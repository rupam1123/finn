"""Conservative primary-table extraction with exact Decimal math.

Only an unambiguous row-major statement with explicit quarter columns is accepted.
Flash can locate a statement page; it cannot supply financial values or fix damaged
OCR. Unsupported layouts remain reviewable with their source links.
"""
import calendar
import re
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from .evidence import citation, compact, model_pages
from .finance import delta, number, to_crores
from .model import ModelUnavailable

VERSION = 'results-v6'
MONTHS = '|'.join(calendar.month_name[1:])
NUM = r'(?:\(?-?\d[\d,]*(?:\.\d+)?\)?|[—–-])'
METRICS = {
    'revenue': r'Revenue from operations',
    'ebitda': r'(?:Reported\s+)?EBITDA',
    'pbt': r'(?:PROFIT BEFORE TAX|Profit from ordinary activities before tax)(?:\s*\([\d+.\s-]+\))?',
    'pat': r'(?:PROFIT FOR THE PERIOD|Net Profit for the period)(?:\s*\([\d+.\s-]+\))?',
    'interest_income': r'Interest earned(?:\s*\([^\n]*\))?',
    'total_income': r'Total Income(?:\s*\([^\n]*\))?',
    'net_interest_income': r'Net interest income',
}


class PageChoice(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    page: int = Field(ge=1)
    reason: str = Field(min_length=1, max_length=500)


class LocatedRow(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    metric: str
    label: str = Field(min_length=2, max_length=200)
    quote: str = Field(min_length=5, max_length=3000)


class TableChoice(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    page: int = Field(ge=1)
    rows: list[LocatedRow] = Field(min_length=2, max_length=7)


def quarter_dates(text):
    """Three explicit comparable quarter columns, optionally annual/YTD columns."""
    header = re.split(r'Revenue from operations|Interest earned|Total income', text, maxsplit=1, flags=re.I)[0]
    # TCS-style PDF reading order separates the month/day row from the year row.
    month_days = list(re.finditer(rf'({MONTHS})\s+(\d{{1,2}}),', header, re.I))
    years = re.findall(r'\b(20\d{2})\b', header)
    dates = []
    if len(month_days) in (3,4,5,6) and len(years) == len(month_days):
        for match, year in zip(month_days, years):
            month = next(i for i in range(1, 13) if calendar.month_name[i].lower() == match[1].lower())
            dates.append(date(int(year), month, int(match[2])))
    else:
        numeric = re.findall(r'\b(\d{2})[./-](\d{2})[./-](20\d{2})\b', header)
        if len(numeric) in (3,4,5,6):
            dates = [date(int(y), int(m), int(d)) for d, m, y in numeric]
        else:
            short = re.findall(r'\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{2})\b', header, re.I)
            anchors = set(re.findall(r'\b(20\d{2})\b', header))
            if len(short) in (3,4,5,6) and len(anchors) == 1:
                anchor = int(next(iter(anchors)))
                for day, month, year in short:
                    full_year = anchor//100*100+int(year)
                    if full_year not in {anchor, anchor-1}:
                        raise ValueError('Short year cannot be aligned to the explicit statement year')
                    month_no = next(i for i in range(1,13) if calendar.month_abbr[i].lower() == month.lower())
                    dates.append(date(full_year, month_no, int(day)))
    if len(dates) not in (3,4,5,6) or not re.search(r'three months ended|quarter ended', text, re.I):
        raise ValueError('Quarter columns cannot be unambiguously reconstructed')
    current, prior, year_ago = dates[:3]
    if not (85 <= (current-prior).days <= 95 and 364 <= (current-year_ago).days <= 366):
        raise ValueError('Quarter dates are missing, duplicated or not comparable')
    # The trailing columns must explicitly correspond to YTD and annual values.
    if len(dates)>=5 and (dates[3] != current or dates[4] != year_ago or not re.search(r'(?:six|nine) months ended|half.year ended', text, re.I)):
        raise ValueError('Unexpected table column structure')
    return [d.isoformat() for d in dates]


def _row(text, label, columns=6):
    # Match the label once, then tokenize cells without a repeated numeric
    # regex. The previous (whitespace* NUMBER whitespace*){columns} could
    # partition one damaged long number exponentially while holding the GIL.
    prefix = r'(?:\(?[a-z0-9]{1,2}\)\s*)?'
    labels = re.finditer(r'(?im)^\s*' + prefix + '(' + label + r')\s*\n', text)
    token = re.compile(r'\S+')
    whitespace = re.compile(r'\s*')
    numeric = re.compile(NUM)
    next_label = re.compile(prefix + r'[A-Za-z]', re.I)
    found = []
    for match in labels:
        values = []
        cursor = match.end()
        end = cursor
        while len(values) < columns:
            cursor = whitespace.match(text, cursor).end()
            cell = token.match(text, cursor)
            if not cell or not numeric.fullmatch(cell[0]):
                break
            values.append(cell[0])
            end = cursor = cell.end()
        if len(values) != columns:
            continue
        cursor = whitespace.match(text, end).end()
        # Require a new labelled row, not a seventh value, note or damaged tail.
        if '\n' not in text[end:cursor] or not next_label.match(text, cursor):
            continue
        valid = True
        for value in values:
            raw = value.strip('()-')
            if ',' in raw and not re.fullmatch(r'(?:\d{1,3}(?:,\d{3})+|\d{1,2}(?:,\d{2})*,\d{3})(?:\.\d+)?', raw):
                valid = False
                break
        if valid:
            found.append((match[1], values, text[match.start():end].strip()))
    return found[0] if len(found) == 1 else None


def parse_statement(document, page, profile='nonfinancial', located_rows=None):
    text = page['text']
    if located_rows and page.get('requires_visual_review'):
        raise ValueError('Statement page requires visual review')
    bases = set(re.findall(r'\b(consolidated|standalone)\b', text, re.I))
    bases = {b.lower() for b in bases}
    if len(bases) != 1:
        raise ValueError('Accounting basis is missing or ambiguous')
    if not re.search(r'financial results|statement of.*results', compact(text), re.I):
        raise ValueError('Not a financial results statement')
    unit_matches = set(u.lower().rstrip('s') for u in re.findall(r'\b(crores?|lakhs?|millions?|billions?)\b', text, re.I))
    if len(unit_matches) != 1 or not re.search(r'₹|`|\bINR\b|\bRs\.?|rupees', text, re.I):
        raise ValueError('Currency or monetary unit is missing/ambiguous')
    if re.search(r'US\s*\$|\bUSD\b|\bEUR\b', text):
        raise ValueError('Mixed currencies on source page')
    unit = next(iter(unit_matches)) + 's'
    periods = quarter_dates(text)
    metrics = ['revenue', 'ebitda', 'pbt', 'pat'] if profile == 'nonfinancial' else ['interest_income', 'total_income', 'net_interest_income', 'pbt', 'pat']
    rows = []
    for metric in metrics:
        found = _row(text, METRICS[metric], len(periods))
        if found is None and located_rows:
            located = [r for r in located_rows if r.metric == metric]
            if len(located)==1:
                choice = located[0]
                citation(document,page['page'],choice.quote)
                # The model locates a row, never assigns cells. Verify its label
                # and numeric-only run independently, then read source order.
                if re.fullmatch(METRICS[metric],choice.label,re.I):
                    tail = compact(choice.quote)
                    if tail.lower().startswith(choice.label.lower()):
                        tail = tail[len(choice.label):].strip()
                        values = tail.split()
                        if len(values)==len(periods) and all(re.fullmatch(NUM,value) for value in values):
                            # Reuse grouping validation; inline PDF reading order
                            # is represented as a single validated row for parsing.
                            synthetic = choice.label+'\n'+'\n'.join(values)+'\nEnd of row'
                            parsed = _row(synthetic,METRICS[metric],len(periods))
                            if parsed: found=(choice.label,values,choice.quote)
        if found is None:
            rows.append({'metric': metric, 'status': 'not_reliably_extracted', 'values': None,
                         'qoq': delta(None, None), 'yoy': delta(None, None), 'evidence': None})
            continue
        label, raw, quote = found
        first, second = (number(raw[i]) for i in [0,1])
        half = number(raw[3]) if len(periods)>=5 and re.search(r'six months ended|half.year ended',text,re.I) else None
        if all(v is not None for v in [first, second, half]):
            # Six-month subtotal independently checks both quarter cells. Allow
            # only the maximum rounding error implied by the reported precision.
            precision = min(-v.as_tuple().exponent for v in [first, second, half])
            tolerance = Decimal('1.5') * Decimal(10) ** -precision
            if abs(first+second-half) > tolerance:
                rows.append({'metric': metric, 'status': 'reconciliation_failed', 'values': None,
                             'qoq': delta(None, None), 'yoy': delta(None, None),
                             'evidence': citation(document, page['page'], quote)})
                continue
        normalized = [to_crores(v, unit) for v in raw[:3]]
        values = {key: str(v) if v is not None else None for key, v in zip(['current', 'previous_quarter', 'year_ago'], normalized)}
        rows.append({'metric': metric, 'reported_label': label.strip(), 'status': 'source_extracted',
                     'values': values, 'raw_values': raw[:3], 'source_unit': unit,
                     'half_year_reconciliation': 'passed' if all(v is not None for v in [first, second, half]) else 'not_available',
                     'normalization_factor':str(to_crores('1',unit)),
                     'reconciliation_proof':{'current_raw':str(first),'previous_quarter_raw':str(second),
                         'half_year_raw':str(half),'calculated_half_year_raw':str(first+second),
                         'tolerance_raw':str(tolerance),'source_unit':unit}
                         if all(v is not None for v in [first,second,half]) else None,
                     'qoq': delta(normalized[0], normalized[1]), 'yoy': delta(normalized[0], normalized[2]),
                     'evidence': citation(document, page['page'], quote)})
    if sum(r['status'] == 'source_extracted' for r in rows) < 2:
        raise ValueError('Insufficient reliable rows')
    return {'status': 'partial' if any(r['status'] != 'source_extracted' for r in rows) else 'extracted',
            'basis': next(iter(bases)), 'currency': 'INR', 'unit': 'crores', 'profile': profile,
            'periods': dict(zip(['current', 'previous_quarter', 'year_ago'], periods[:3])),
            'duration_months': 3, 'pat_scope': 'total_profit_for_period_including_NCI_if_consolidated',
            'method': 'strict_primary_table_parser', 'rows': rows,
            'requires_visual_review': page.get('requires_visual_review', False),
            'context_evidence': citation(document, page['page'], text),
            'warnings': ['EBITDA is never inferred from operating profit; missing means not reliably extracted.',
                         'PAT uses total profit for the period, not profit attributable to owners.'] if profile == 'nonfinancial' else
                        ['Lender schema: no industrial EBITDA or working-capital judgment.']}


def image_statement_pages(document,failures):
    rejected={f['page'] for f in failures if f.get('page') is not None and f['reason'] not in
              {'Not a financial results statement','Accounting basis is missing or ambiguous'}}
    def score(page):
        text=compact(page['text'])
        labels=sum(bool(re.search(pattern,text,re.I)) for pattern in
                   [r'revenue|interest earned|total income',r'profit before tax|\bPBT\b',
                    r'profit for the period|profit after tax|\bPAT\b',r'total expenses|provisions|tax expense'])
        return (120 if page['page'] in rejected else 0)+labels*25+(100 if page.get('requires_visual_review') else 0)+(
            30 if re.search(r'quarter|three months',text,re.I) else 0)+(20 if re.search(r'consolidated',text,re.I) else 0)
    return [p['page'] for p in sorted(document['pages'],key=lambda p:(-score(p),p['page']))]


def enrich_results(document, profile='nonfinancial', model=None, store=None):
    if profile not in {'nonfinancial', 'bank', 'nbfc'}:
        raise ValueError('Unsupported financial profile')
    base = {'version': VERSION, 'profile': profile, 'status': 'review_required', 'rows': [],
            'model_status': 'not_configured' if model is None or not model.configured else 'not_needed',
            'warnings': [], 'source_url': document.get('url') if document else None}
    if not document or document.get('status') not in {'text_extracted','ocr_required'}:
        return {**base, 'warnings': ['Primary PDF text unavailable; no financial values inferred.']}
    candidates, failures = [], []
    for page in document['pages']:
        if not re.search(r'Revenue from operations|Interest earned|Total income', page['text'], re.I):
            continue
        try:
            candidates.append(parse_statement(document, page, profile))
        except ValueError as exc:
            failures.append({'page': page['page'], 'reason': str(exc)})
    consolidated = [r for r in candidates if r['basis'] == 'consolidated']
    # Do not silently pick standalone when a consolidated statement exists but failed parsing.
    has_consolidated = any(re.search(r'consolidated.{0,80}(?:financial|audited|results)|statement of consolidated', compact(p['text']), re.I)
                           for p in document['pages'])
    selection = consolidated or ([] if has_consolidated else candidates)
    if len(selection) == 1:
        return {**base, **selection[0], 'parser_rejections': failures}
    # Saved exchange attachments can include notices and ordinary releases.
    # Do not spend locator/vision requests searching those for nonexistent
    # quarterly statements. Unreadable pages still get the image fallback.
    native_candidate=any(
        re.search(r'\b(?:revenue|sales|income)\b',p['text'],re.I)
        and re.search(r'profit|loss|expenses|\bEBITDA\b|\bPAT\b',p['text'],re.I)
        and re.search(r'quarter|three months|statement of.{0,50}(?:profit|income|results)',compact(p['text']),re.I)
        for p in document['pages'])
    image_candidate=(document.get('status')=='ocr_required' or any(
        p.get('requires_visual_review') for p in document['pages']))
    try_model=model is not None and model.configured and (native_candidate or image_candidate)
    if try_model:
        try:
            choice, usage = model.generate('Locate the consolidated quarterly INR financial results table page; '
                'if genuinely standalone-only, locate that page. Do not supply or infer any numerical values.',
                {'pages': model_pages(document)}, PageChoice.model_json_schema())
            choice = PageChoice.model_validate(choice)
            page = next(p for p in document['pages'] if p['page'] == choice.page)
            result = parse_statement(document, page, profile)
            if has_consolidated and result['basis'] != 'consolidated':
                raise ValueError('Consolidated statement cannot be replaced by standalone')
            return {**base, **result, 'model_status': 'page_locator_validated', 'usage': usage}
        except (ModelUnavailable, ValueError, TypeError, KeyError, StopIteration):
            base['model_status'] = 'unavailable_or_invalid'
        try:
            output, usage = model.generate(
                'Locate the consolidated quarterly INR results table (standalone only if genuinely absent). '
                'For each requested metric return its exact complete source row quote, including the label and '
                'ALL numeric columns in their printed order. Do not supply computed values or reorder cells. '
                'Metrics: '+', '.join(METRICS)+'. Do not substitute operating profit for EBITDA. '
                'Unsupported/ambiguous/scanned tables must not be guessed.',
                {'pages':model_pages(document)},TableChoice.model_json_schema())
            located = TableChoice.model_validate(output)
            page = next(p for p in document['pages'] if p['page']==located.page)
            result = parse_statement(document,page,profile,located.rows)
            if has_consolidated and result['basis']!='consolidated':
                raise ValueError('Consolidated statement cannot be replaced by standalone')
            return {**base,**result,'method':'model_located_source_rows_deterministic_cells',
                    'model_status':'source_rows_validated','usage':usage,'parser_rejections':failures}
        except (ModelUnavailable, ValueError, TypeError, KeyError, StopIteration):
            base['model_status'] = 'unavailable_or_invalid'
    if try_model and store is not None and hasattr(model,'generate_vision'):
        from .vision_results import extract
        images=image_statement_pages(document,failures)
        try:return {**base,**extract(document,profile,model,store,images,require_consolidated=has_consolidated),'parser_rejections':failures}
        except ValueError as exc:
            base['model_status']='image_extraction_unavailable_or_invalid'
            failures.append({'page':None,'reason':str(exc)})
    warning=('Ambiguous layout, periods, units or basis. Review the primary PDF; no financial values inferred.'
             if native_candidate or image_candidate else
             'No quarterly financial statement candidate found in this attachment; no financial values inferred.')
    return {**base, 'parser_rejections': failures, 'warnings': [warning]}
