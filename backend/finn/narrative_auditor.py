"""Conservative comparison of explicitly reviewed, primary-grounded observations."""
from datetime import date
from decimal import Decimal

ALIGN = ('metric', 'period_start', 'period_end', 'unit', 'currency', 'basis', 'definition')


def compare(guidance, actual, as_of):
    if guidance.get('withdrawn'):
        return {'status': 'withdrawn'}
    end = date.fromisoformat(guidance['period_end'])
    if end > date.fromisoformat(as_of):
        return {'status': 'not_yet_due'}
    if guidance.get('lower') is None or guidance.get('upper') is None:
        return {'status': 'qualitative', 'reason': 'No explicit numerical target band'}
    if not actual or any(not guidance.get(k) or guidance.get(k) != actual.get(k) for k in ALIGN):
        return {'status': 'not_comparable'}
    if any(not item.get('reviewed_primary') or not item.get('citations') for item in (guidance, actual)):
        return {'status': 'review_required'}
    if date.fromisoformat(guidance['statement_date']) > date.fromisoformat(guidance['period_start']):
        return {'status': 'not_comparable', 'reason': 'In-period or retrospective target requires review'}
    lower, upper, value = map(Decimal, (str(guidance['lower']), str(guidance['upper']), str(actual['value'])))
    if not all(x.is_finite() for x in (lower, upper, value)) or lower > upper:
        raise ValueError('Invalid financial values or band')
    direction = guidance.get('direction')
    if direction not in ('higher', 'lower'):
        return {'status': 'not_comparable'}
    status = 'within_target' if lower <= value <= upper else 'above_target' if value > upper else 'below_target'
    return {'status': status, 'citations': guidance['citations'] + actual['citations'],
            'direction': direction, 'causality_established': False}


def ledger(guidance, actuals, periods, as_of):
    """Four delivered periods; absence and multiple revisions are explicit."""
    cutoff=date.fromisoformat(as_of)
    selected=sorted({p for p in periods if date.fromisoformat(p)<=cutoff},reverse=True)[:4]
    rows=[]
    for period in selected:
        statements=[g for g in guidance if g['period_end']==period]
        if not statements:
            rows.append({'period_end':period,'status':'no_comparable_guidance','comparisons':[]})
            continue
        comparisons=[]
        for g in statements:
            matches=[a for a in actuals if all(a.get(k)==g.get(k) for k in ALIGN)]
            peers=[x for x in statements if all(x.get(k)==g.get(k) for k in ALIGN)]
            if len(matches)>1 or len(peers)>1:
                result={'status':'review_required','reason':'Multiple revisions or actuals require explicit selection'}
            else:
                result=compare(g,matches[0] if matches else None,as_of)
            comparisons.append(result)
        rows.append({'period_end':period,'status':'evaluated','comparisons':comparisons})
    return {'requested_quarters':4,'observed_periods':len(selected),'missing_quarters':4-len(selected),'ledger':rows}
