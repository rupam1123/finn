"""Aligned financial ratios. Caller must provide reviewed primary field evidence."""
from decimal import Decimal


def ratio(numerator, denominator, profile='nonfinancial', metric='cash_conversion'):
    if profile not in ('nonfinancial', 'bank', 'nbfc'):
        raise ValueError('Unknown sector profile')
    if profile != 'nonfinancial' and metric in ('cash_conversion', 'working_capital'):
        return {'status': 'not_applicable', 'value': None}
    if not numerator or not denominator:
        return {'status': 'missing', 'value': None}
    keys = ('period_start', 'period_end', 'basis', 'currency', 'unit')
    if any(not numerator.get(k) or numerator[k] != denominator.get(k) for k in keys):
        return {'status': 'not_comparable', 'value': None}
    if any(not x.get('reviewed_primary') or not x.get('citations') for x in (numerator, denominator)):
        return {'status': 'review_required', 'value': None}
    a, b = Decimal(str(numerator['value'])), Decimal(str(denominator['value']))
    if not a.is_finite() or not b.is_finite():
        raise ValueError('Nonfinite input')
    if b <= 0:
        return {'status': 'undefined', 'value': None}
    return {'status': 'computed', 'value': str(a/b), 'unit': 'ratio',
            'citations': numerator['citations'] + denominator['citations']}


def analyze(facts, profile):
    """Facts are keyed by metric; missing facts remain missing, never zero."""
    return {
        'cash_conversion': ratio(facts.get('cfo'),facts.get('pat'),profile),
        'debt_to_equity': ratio(facts.get('total_debt'),facts.get('equity'),profile,'leverage'),
        'working_capital': {'status':'not_applicable' if profile!='nonfinancial' else 'review_required',
                           'reason':'Requires comparable reported cycle periods; no invented day counts'},
    }


def working_capital_cycle(inventory_days, receivable_days, payable_days, profile='nonfinancial'):
    if profile not in ('nonfinancial','bank','nbfc'):
        raise ValueError('Unknown sector profile')
    if profile in ('bank','nbfc'):
        return {'status':'not_applicable','value':None}
    items=(inventory_days,receivable_days,payable_days)
    if any(x is None for x in items):
        return {'status':'missing','value':None}
    keys=('period_start','period_end','basis','definition')
    if any(x.get('unit')!='days' or not x.get('reviewed_primary') or not x.get('citations') for x in items):
        return {'status':'review_required','value':None}
    if any(not items[0].get(k) or any(x.get(k)!=items[0][k] for x in items) for k in keys):
        return {'status':'not_comparable','value':None}
    a,b,c=(Decimal(str(x['value'])) for x in items)
    if not all(x.is_finite() and x>=0 for x in (a,b,c)):
        raise ValueError('Invalid day counts')
    return {'status':'computed','value':str(a+b-c),'unit':'days',
            'citations':sum((x['citations'] for x in items),[])}


def governance_excerpts(index):
    from .transcript_rag import retrieve
    return {name:{'status':'evidence_for_review','excerpts':retrieve(index,query,4),
                  'adverse_finding_established':False}
            for name,query in {'related_party':'related party transactions',
                               'contingent_liabilities':'contingent liabilities guarantees',
                               'audit':'qualified opinion auditor qualification'}.items()}
