"""Image-backed result extraction with deterministic statement reconciliation."""
import re
from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field
from .finance import delta,to_crores
from .documents import primary_page_image

class ImageRow(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    metric: Literal['revenue','ebitda','pbt','pat','other_income','total_income','total_expenses','pbt_before_exception','exceptional_items','tax','current_tax','deferred_tax','provisions','interest_income','net_interest_income']
    label: str=Field(min_length=2,max_length=200)
    cells:list[str|None]=Field(min_length=3,max_length=3)

class ImageStatement(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    is_statement: bool
    basis: Literal['consolidated','standalone','unknown']
    currency: Literal['INR','USD','other','unknown']
    unit: Literal['rupees','lakhs','crores','millions','billions','unknown']
    periods:list[str]=Field(min_length=3,max_length=3)
    header_transcription:str=Field(max_length=1800)
    rows:list[ImageRow]=Field(max_length=14)

def money(value):
    if value is None:return None
    value=value.strip()
    if value in {'-','—','–'}:return Decimal(0)
    if not re.fullmatch(r'\(?-?(?:\d+|\d{1,3}(?:,\d{3})+|\d{1,2}(?:,\d{2})*,\d{3})(?:\.\d+)?\)?',value):raise ValueError('Ambiguous source amount')
    if value.startswith('(') and value.endswith(')'):value='-'+value[1:-1]
    n=Decimal(value.replace(',',''))
    if not n.is_finite():raise ValueError('Invalid source amount')
    return n


def period_date(value):
    """Normalize fully specified dates; never infer a missing day/year or locale."""
    try:return date.fromisoformat(value)
    except ValueError:
        match=re.fullmatch(r'(\d{1,2})([./-])(\d{1,2})\2(\d{4})',value.strip())
        if not match or int(match[1])<=12:raise ValueError('Image period must be an explicit unambiguous date') from None
        return date(int(match[4]),int(match[3]),int(match[1]))

def validate(document,image,output,profile):
    parsed=ImageStatement.model_validate(output)
    if not parsed.is_statement or parsed.basis=='unknown' or parsed.currency!='INR' or parsed.unit=='unknown':raise ValueError('Image statement context is not explicit')
    dates=[period_date(x) for x in parsed.periods]
    if not (85<=(dates[0]-dates[1]).days<=95 and 364<=(dates[0]-dates[2]).days<=366):raise ValueError('Image periods are not comparable quarters')
    if re.search(r'year.to.date|nine.month|six.month',parsed.header_transcription,re.I) and not re.search(r'quarter|three.month',parsed.header_transcription,re.I):raise ValueError('YTD-only table cannot supply quarterly cells')
    rows={}
    for r in parsed.rows:
        if r.metric in rows:raise ValueError('Duplicate image metric')
        if r.metric=='ebitda' and not re.search(r'\bEBITDA\b|earnings before interest.{0,50}depreciation',r.label,re.I):raise ValueError('Operating profit cannot be relabelled EBITDA')
        if r.metric=='pat' and re.search(r'attributable|owners|non.controlling|per.share',r.label,re.I):raise ValueError('PAT attribution differs from total group profit')
        if r.metric=='pbt' and re.search(r'exceptional',r.label,re.I):raise ValueError('PBT before exceptional items is a different metric')
        rows[r.metric]=(r,[money(x) for x in r.cells])
    if 'tax' in rows and ('current_tax' in rows or 'deferred_tax' in rows):raise ValueError('Ambiguous total and component tax rows')
    tax_keys=['tax'] if 'tax' in rows else ['current_tax','deferred_tax']
    needed={'pbt','pat','total_income','total_expenses',*tax_keys}
    needed|={'revenue','other_income','pbt_before_exception'} if profile=='nonfinancial' else {'provisions'}
    missing=needed-rows.keys()
    illegible={k for k in needed&rows.keys() if any(v is None for v in rows[k][1])}
    if missing or illegible:raise ValueError('Independent reconciliation rows unavailable: '+', '.join(sorted(missing|illegible)))
    exceptional_sign=-1
    if profile=='nonfinancial' and 'exceptional_items' in rows and any(v is not None and v!=0 for v in rows['exceptional_items'][1]):
        formula=re.search(r'\(\s*\d+\s*([+-])\s*\d+\s*\)',rows['pbt'][0].label)
        if not formula:raise ValueError('Exceptional-item sign needs an explicit printed PBT formula')
        exceptional_sign=1 if formula[1]=='+' else -1
    for i in range(3):
        value=lambda k:rows[k][1][i]
        def equal(a,b,keys):
            tolerance=sum((Decimal(0) if rows[k][0].cells[i].strip() in {'-','—','–'} else Decimal(10)**rows[k][1][i].as_tuple().exponent/2 for k in keys),Decimal(0))
            return abs(a-b)<=tolerance
        tax=sum((value(k) for k in tax_keys),Decimal(0))
        if not equal(value('pbt')-tax,value('pat'),['pbt',*tax_keys,'pat']):raise ValueError('PAT/tax reconciliation failed')
        if profile=='nonfinancial':
            if not equal(value('revenue')+value('other_income'),value('total_income'),['revenue','other_income','total_income']):raise ValueError('Revenue reconciliation failed')
            if not equal(value('total_income')-value('total_expenses'),value('pbt_before_exception'),['total_income','total_expenses','pbt_before_exception']):raise ValueError('Income/expense reconciliation failed')
            exceptional=value('exceptional_items') if 'exceptional_items' in rows else None
            if exceptional is None:
                # Do not turn an unprinted adjustment into zero. Instead require
                # the independently printed before/after PBT rows to agree, in
                # addition to the income/expense and tax/PAT checks above.
                if not equal(value('pbt_before_exception'),value('pbt'),['pbt_before_exception','pbt']):
                    raise ValueError('Unextracted exceptional items prevent PBT reconciliation')
            elif not equal(value('pbt_before_exception')+exceptional_sign*exceptional,value('pbt'),['pbt_before_exception','exceptional_items','pbt']):raise ValueError('Exceptional-item reconciliation failed')
        elif not equal(value('total_income')-value('total_expenses')-value('provisions'),value('pbt'),['total_income','total_expenses','provisions','pbt']):raise ValueError('Lender reconciliation failed')
    def evidence(quote):
        return {'url':document['url'],'sha256':document['sha256'],'page':image['page'],'observed_at':document['fetched_at'],
                'evidence_type':'page_image','image_sha256':image['image_sha256'],'quote':quote,'transcription':True}
    wanted=['revenue','ebitda','pbt','pat'] if profile=='nonfinancial' else ['interest_income','total_income','net_interest_income','pbt','pat']
    final=[]
    for metric in wanted:
        if metric not in rows:
            final.append({'metric':metric,'status':'not_reported_or_unavailable','values':None,'qoq':delta(None,None),'yoy':delta(None,None),'evidence':None});continue
        raw,values=rows[metric];values=[to_crores(str(v),parsed.unit) if v is not None else None for v in values]
        final.append({'metric':metric,'reported_label':raw.label,'status':'source_extracted',
                      'values':dict(zip(['current','previous_quarter','year_ago'],[str(v) if v is not None else None for v in values])),
                      'raw_values':raw.cells,'source_unit':parsed.unit,'qoq':delta(values[0],values[1]),'yoy':delta(values[0],values[2]),
                      'evidence':evidence(raw.label+': '+', '.join(x if x is not None else 'unavailable' for x in raw.cells))})
    return {'status':'extracted' if all(r['values'] for r in final) else 'partial','rows':final,'basis':parsed.basis,
            'currency':'INR','unit':'crores','periods':dict(zip(['current','previous_quarter','year_ago'],[d.isoformat() for d in dates])),
            'duration_months':3,'method':'primary_image_reconciled','model_status':'image_rows_reconciled',
            'context_evidence':evidence(parsed.header_transcription),'requires_visual_review':True,
            'reconciliation_inputs':[r.model_dump() for r in parsed.rows],
            'reconciliation_method':{'tax':'printed_total' if tax_keys==['tax'] else 'sum_of_printed_current_and_deferred_tax',
                                     'exceptional_items_sign':exceptional_sign if profile=='nonfinancial' else None,
                                     'unextracted_exceptional_cells':'require_equal_printed_before_and_after_pbt; no adjustment value inferred'},
            'warnings':['Image transcription: statement arithmetic reconciled; inspect the original page. Missing EBITDA is never inferred.']}

def extract(document,profile,model,store,pages,require_consolidated=False):
    failures=[];standalone=None
    for page in list(dict.fromkeys(pages))[:3]:
        try:
            image=primary_page_image(document,page,store)
            output,usage=model.generate_vision('Read ONLY this primary result-statement image. Return explicit consolidated figures where present, otherwise standalone. '
                'Select current quarter, previous quarter, and same quarter last year; never select YTD columns. '
                'Return exactly three fully printed quarter dates in YYYY-MM-DD format; do not infer missing dates or years. '
                'Transcribe labels, explicit units/currency and reconciliation rows; use null when illegible. '
                'Include revenue, other income, total income, total expenses, PBT before exceptional items, exceptional items, PBT, tax, PAT. '
                'Copy the full PBT label including any printed row-number formula such as (5+6). '
                'A section heading with blank cells is not a data row. If the exceptional-item section has exactly one named item, '
                'transcribe that item label and its printed cells for exceptional_items, rather than the empty section heading. '
                'Never replace a blank or missing cell with a dash or zero. '
                'If total tax is not printed, transcribe current_tax and deferred_tax separately; never calculate a total. '
                'If total tax is printed use tax and omit its component rows. '
                'For lenders include provisions and explicitly reported interest/NII. EBITDA only if separately reported. '
                'Printed accounting dash is "-"; a missing cell is null. Do not estimate, derive or repair cells. '
                'Return is_statement=false for a non-statement/ambiguous page.',
                {'primary_pdf_sha256':document['sha256'],'page':page},ImageStatement.model_json_schema(),[image])
            result=validate(document,image,output,profile)
            if require_consolidated and result['basis']!='consolidated':
                raise ValueError('Consolidated statement cannot be replaced by standalone')
            result['usage']=usage
            # A fully scanned document cannot reveal consolidated headings to
            # the native-text detector. Inspect the remaining bounded candidates
            # before falling back to an otherwise valid standalone statement.
            if result['basis']=='standalone':
                standalone=standalone or result
                continue
            return result
        except (ValueError,RuntimeError,KeyError,TypeError) as exc:failures.append({'page':page,'error':str(exc)})
    if standalone is not None:return standalone
    raise ValueError('No image statement passed checks: '+str(failures))
