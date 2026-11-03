"""Primary-bound management guidance and actuals with explicit abstention states."""
import re
from decimal import Decimal
from .evidence import citation, compact
from .transcript_rag import reported_quarter, quarter_evidence
from .transcript_context import turns, accounting_basis

METRIC = r'(operating margin|EBITDA margin|PBT margin|PAT margin|net interest margin|revenue (?:growth|grew))'
PERIOD = r'(Q[1-4]\s*FY\s*[\'’]?(?:20)?\d{2}|(?:financial year|full year|FY)\s*[\'’]?(?:20)?\d{2})'
BAND = r'(-?\d+(?:\.\d+)?)\s*%?\s*(?:to|and|–|-)\s*(-?\d+(?:\.\d+)?)\s*%'
METRIC_RE = re.compile(METRIC, re.I)
GUIDANCE_WORDS = re.compile(r'guidance|\bexpect\w*\b|\btarget\w*\b|outlook|\banticipat\w*\b', re.I)
VALUE = re.compile(r'(?:was|is|stood at|stands at|came in at|reported at|reached|of|at|by)\s*(?:around\s+)?(-?\d+(?:\.\d+)?)\s*%', re.I)


def period(value):
    value = value.replace('’', "'")
    year = re.search(r'(\d{2,4})\s*$', value)
    if not year: raise ValueError('Unrecognized fiscal period')
    year = int(year[1]); year += 2000 if year < 100 else 0
    q = re.search(r'Q([1-4])', value, re.I)
    return f'Q{q[1]} FY{year}' if q else f'FY{year}'


def next_quarter(label):
    match = re.fullmatch(r'Q([1-4]) FY(\d{4})', label)
    if not match: return None
    q, y = map(int, match.groups())
    return f'Q{q+1} FY{y}' if q < 4 else f'Q1 FY{y+1}'


def observations(document):
    q = reported_quarter(document)
    if not q or document.get('kind') != 'transcript': return []
    output = []
    for turn in turns(document):
        text = compact(turn['text'])
        # Decimal points are not sentence boundaries. Every resulting quote still
        # has to occur on one exact original page.
        for sentence in re.split(r'(?<=[.!?])\s+(?=[A-Z])|,\s+(?=while\b|whereas\b)', text):
            original_sentence=sentence
            sentence=re.split(r'compared (?:to|with) our earlier|versus (?:our )?(?:earlier|previous)',sentence,maxsplit=1,flags=re.I)[0].strip()
            first_person=re.search(r'\bour\b|\bwe\b',sentence,re.I)
            if first_person: sentence=sentence[first_person.start():]
            matches = list(METRIC_RE.finditer(sentence))
            if len(matches) != 1 or not re.search(r'\bour\b|\bwe\b', sentence, re.I): continue
            match = matches[0]
            metric = match[1].lower().replace(' ', '_')
            if metric=='revenue_grew':metric='revenue_growth'
            tail = sentence[match.end():]
            kind = 'guidance' if GUIDANCE_WORDS.search(sentence) else 'actual'
            band = re.search(BAND, tail) if kind == 'guidance' else None
            actual = VALUE.search(tail) if kind == 'actual' else None
            minimum=re.search(r'(?:at least|minimum of|minimum)\s*(\d+(?:\.\d+)?)\s*%|(\d+(?:\.\d+)?)\s*%\s*(?:plus|\+)',tail,re.I) if kind=='guidance' else None
            if not (band or actual or minimum): continue
            if metric == 'revenue_growth':
                cc = bool(re.search(r'constant.currency', sentence, re.I))
                reported = bool(re.search(r'reported (?:currency|terms)', sentence, re.I))
                yoy = bool(re.search(r'year.on.year|\by[- ]?o(?:n)?[- ]?y\b|\byoy\b', sentence, re.I))
                qoq = bool(re.search(r'quarter.on.quarter|sequential|\bq[- ]?o(?:n)?[- ]?q\b|\bqoq\b', sentence, re.I))
                annual=bool(re.search(r'full year|financial year|\bFY\s*[\'’]?(?:20)?\d{2}',original_sentence,re.I)) and not re.search(r'Q[1-4]\s*FY',original_sentence,re.I)
                annual_context=None
                if kind=='guidance' and not annual:
                    before=text[:text.find(original_sentence)]
                    contexts=list(re.finditer(r'[^.!?]*\b(?:full year|financial year)\s*[\'’]?(?:20)?\d{2}[^.!?]*[.!?]',before[-1000:],re.I))
                    if contexts:annual=True;annual_context=contexts[-1][0].strip()
                if not yoy and not qoq and annual:yoy=True
                if (cc and reported) or yoy == qoq: continue
                definition = ('constant_currency_' if cc else 'reported_currency_') + ('yoy' if yoy else 'qoq')
            else:
                definition = 'reported_' + metric
            explicit = re.search(PERIOD, tail, re.I)
            if not explicit:
                prefix=re.search(r'\b(?:in|for|during)\s+'+PERIOD,original_sentence[:first_person.start()] if first_person else '',re.I)
                if prefix:explicit=re.search(PERIOD,prefix[0],re.I)
            target = period(explicit[0]) if explicit else None
            if not target and metric=='revenue_growth' and annual_context:
                context_period=re.search(PERIOD,annual_context,re.I)
                if context_period:target=period(context_period[0])
            if not target and re.search(r'full year|financial year|for the year',sentence,re.I):
                year=re.search(r'FY(\d{4})',q['label'])
                if year:target='FY'+year[1]
            if not target and re.search(r'next quarter', sentence, re.I): target = next_quarter(q['label'])
            if not target and re.search(r'this quarter|for the quarter|quarterly', sentence, re.I): target = q['label']
            basis, context = accounting_basis(document, sentence)
            if metric=='revenue_growth' and annual_context:context.append(citation(document,turn['page'],annual_context))
            # Compare only whole-company metrics. Segment-specific values need a
            # separate schema and must not be mixed with group actuals.
            scope_verified = not re.search(r'\b(?:segment|vertical|division|business|9m|6m|h1|h2|ytd)\b|'
                                           r'half.year|nine.month|six.month|year.to.date|adjusted|normalised|normalized|excluding', sentence, re.I)
            item = {'kind': kind, 'metric': metric, 'target_period': target or q['label'],
                    'horizon_verified': target is not None, 'statement_period': q['label'],
                    'unit': 'percent', 'definition': definition, 'basis': basis,
                    'scope': 'company', 'scope_verified': scope_verified,
                    'requires_visual_review': turn['requires_visual_review'],
                    'speaker': turn['speaker'], 'speaker_verified': turn['speaker_verified'],
                    'speaker_status': 'management_role_bound' if turn['speaker_verified'] else 'management_role_unverified',
                    'context_citations': context + ([turn['speaker_evidence']] if turn['speaker_evidence'] else []),
                    'citation': citation(document, turn['page'], original_sentence)}
            if band:
                item.update(lower=band[1], upper=band[2])
                if Decimal(item['lower']) > Decimal(item['upper']): continue
            elif minimum:item.update(lower=minimum[1] or minimum[2],upper=None,comparison_operator='at_least')
            else: item['value'] = actual[1]
            # A single stated target explicitly applying to BOTH scopes is two
            # targets. Never copy an actual with two different reported values.
            if kind=='guidance' and re.search(r'\bboth\b.{0,35}(?:stand[ -]?alone.{0,15}consol|consol.{0,20}stand[ -]?alone)',sentence,re.I):
                output.extend([{**item,'basis':basis} for basis in ('consolidated','standalone')])
            else:output.append(item)
    unique = {}
    for item in output:
        key = tuple(item.get(k) for k in ('kind','metric','target_period','statement_period','lower','upper','value','definition','basis','speaker','scope'))
        unique.setdefault(key, item)
    return list(unique.values())


def evaluate(guidance, actual):
    citations = [guidance['citation']] + ([actual['citation']] if actual else [])
    citations += guidance.get('context_citations', []) + (actual.get('context_citations', []) if actual else [])
    if guidance.get('withdrawn'): return {'status':'withdrawn','citations':citations,'reason':'Target explicitly withdrawn.'}
    if actual is None: return {'status':'actual_unavailable','reason':'No supported primary actual extracted for this target.','citations':citations}
    keys = ('metric','target_period','unit','definition')
    if any(guidance[k] != actual[k] for k in keys):
        return {'status':'not_comparable','reason':'Metric, target horizon or definition differs. Annual guidance is not a quarterly promise.','citations':citations}
    if (guidance.get('basis') not in ('consolidated','standalone') or guidance['basis'] != actual.get('basis')
            or any(not x.get('speaker_verified') or x.get('requires_visual_review')
                   or x.get('horizon_verified') is False or x.get('scope_verified') is False for x in (guidance,actual))
            or guidance.get('scope', 'company') != actual.get('scope', 'company')):
        return {'status':'review_required','reason':'Accounting basis, speaker, target horizon, scope or visual evidence is not explicitly verified.','citations':citations}
    if guidance.get('comparison_operator')=='at_least':
        lo,value=map(Decimal,(guidance['lower'],actual['value']))
        if not lo.is_finite() or not value.is_finite():raise ValueError('Invalid values')
        return {'status':'within_target' if value>=lo else 'below_target','metric':guidance['metric'],'period':guidance['target_period'],
                'reason':'Compared with the explicitly stated minimum target; this is not an upper-band beat.',
                'target':{'lower':str(lo),'upper':None,'operator':'at_least'},'actual':str(value),'citations':citations}
    lo, hi, value = map(Decimal, (guidance['lower'],guidance['upper'],actual['value']))
    if not all(v.is_finite() for v in (lo,hi,value)) or lo > hi: raise ValueError('Invalid values')
    return {'status':'within_target' if lo <= value <= hi else 'above_target' if value > hi else 'below_target',
            'reason':'Aligned reported percentage compared with the explicit target band; no causal claim.',
            'metric':guidance['metric'], 'period':guidance['target_period'],
            'target':{'lower':str(lo),'upper':str(hi)},'actual':str(value),'citations':citations}


def analyze(documents,extra_facts=None):
    result = quarter_evidence(documents)
    facts = [x for d in documents for x in observations(d)]
    # Equivalent model/deterministic observations are one fact with one value,
    # not conflicting revisions merely because both extractors found them.
    for fact in extra_facts or []:
        keys=('kind','metric','target_period','statement_period','lower','upper','value','definition','basis','scope')
        if not any(all(x.get(k)==fact.get(k) for k in keys) for x in facts):facts.append(fact)
    for row in result['ledger']:
        label = row['period_end']
        annual_label='FY'+label.split('FY')[-1] if label.startswith('Q4 FY') else None
        current = [x for x in facts if x['kind']=='actual' and x['statement_period']==label
                   and x['target_period'] in {label,annual_label}]
        # A target can originate more than one quarter earlier, provided it
        # explicitly targets this delivered period and predates its call.
        def order(value):
            m = re.fullmatch(r'Q([1-4]) FY(\d{4})',value)
            return int(m[2])*4+int(m[1]) if m else None
        current_order = order(label)
        targets = [x for x in facts if x['kind']=='guidance' and (x['target_period'] in {label,annual_label} or x['target_period']=='FY'+label.split('FY')[-1])
                   and current_order is not None and order(x['statement_period']) is not None
                   and order(x['statement_period']) < current_order]
        comparisons = []
        for g in targets:
            if not g.get('speaker_verified'):
                comparisons.append({'status':'review_required','reason':'The target speaker is not verified as management.','citations':[g['citation']]})
                continue
            if g['target_period'].startswith('FY') and not annual_label:
                comparisons.append({'status':'not_yet_due','reason':'Annual guidance remains pending; a quarterly result is not the annual outcome.','citations':[g['citation']]})
                continue
            alignment=('metric','target_period','definition','basis','scope')
            matches = [a for a in current if all(a.get(k)==g.get(k) for k in alignment)]
            peers = [x for x in targets if all(x.get(k)==g.get(k) for k in alignment)]
            # Most recent earlier statement selects the dated revision. A
            # conflicting same-period revision still requires explicit review.
            latest=max((order(x['statement_period']) for x in peers),default=None)
            peers=[x for x in peers if order(x['statement_period'])==latest]
            if order(g['statement_period'])!=latest:continue
            if len(matches)>1 or len(peers)>1:
                comparisons.append({'status':'review_required','reason':'Conflicting values or target revisions require dated selection.','citations':[x['citation'] for x in peers]})
            else:
                comparison=evaluate(g,matches[0] if matches else None)
                comparison['target_statement_period']=g['statement_period']
                comparison['comparison_scope']='latest_comparable_extracted_target'
                comparisons.append(comparison)
        resolved = [x for x in comparisons if x['status'] in ('within_target','above_target','below_target')]
        row.update(comparisons=comparisons, extracted_actuals=current, extracted_guidance=targets,
                   status='compared' if resolved else 'missing_transcript' if row.get('coverage_status')=='missing_transcript' else 'review_required' if comparisons else 'insufficient_comparable_evidence',
                   reason='Explicit comparable primary targets and actuals.' if resolved else
                          'No verified numerical comparison. Review the sources; absence of an extracted pair is not proof that no guidance was given.')
    result.update(version='say-do-v4', observations=facts, status='analyzed_with_abstentions',
                  resolved_comparisons=sum(x['status'] in ('within_target','above_target','below_target') for r in result['ledger'] for x in r['comparisons']),
                  forward_guidance=[x for x in facts if x['kind']=='guidance'],
                  extraction_scope='Primary management percentage targets with explicit accounting and reporting context')
    return result
