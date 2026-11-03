"""Concise source-bound views assembled from deterministic financial facts."""
from decimal import Decimal
from .finance import delta


def assemble(modules, financials, annual, say_do):
    # Do not choose between conflicting restatements or accounting bases.
    facts={}
    for statement in financials:
        if statement.get('basis') not in ('consolidated','standalone'):continue
        for row in statement.get('rows',[]):
            if row.get('status')!='source_extracted' or not row.get('values'):continue
            for slot,date in statement.get('periods',{}).items():
                value=row['values'].get(slot)
                if value is None:continue
                key=(statement['basis'],date,row['metric'])
                fact={'basis':key[0],'period_end':date,'metric':key[2],'value':value,
                      'unit':'INR_crore','citations':[row['evidence'],statement['context_evidence']],
                      'requires_visual_review':statement.get('requires_visual_review',False)}
                facts.setdefault(key,{})[value]=fact
    consolidated=any(k[0]=='consolidated' for k in facts)
    series=[];conflicts=[]
    for key,values in sorted(facts.items()):
        if consolidated and key[0]!='consolidated':continue
        if len(values)!=1:
            conflicts.append({'basis':key[0],'period_end':key[1],'metric':key[2],
                              'status':'conflicting_primary_values','alternatives':list(values.values())})
        else:series.append(next(iter(values.values())))
    latest=max((x['period_end'] for x in series),default=None)
    snapshot=[x for x in series if x['period_end']==latest]
    modules['financial_snapshot'].update(status='primary_values' if snapshot else 'unavailable',
        facts=snapshot,conflicts=conflicts,claims_verified=False)
    modules['trajectory'].update(status='primary_series' if series else 'unavailable',
        facts=series,conflicts=conflicts,claims_verified=False)
    modules['forward_guidance'].update(status='primary_targets' if say_do['forward_guidance'] else 'unavailable',
        targets=say_do['forward_guidance'],claims_verified=False)
    modules['narrative_vs_numbers'].update(status=say_do['status'],ledger=say_do['ledger'],claims_verified=False)
    cash=[];leverage=[]
    for report in annual:
        cash.extend(report.get('periods',[]));leverage.extend(report.get('leverage',[]))
    modules['cash_quality'].update(status='primary_ratios' if any(x['cash_conversion']['status']=='computed' for x in cash) else 'unavailable',facts=cash)
    modules['balance_sheet_governance'].update(leverage=leverage)
    bull=[];bear=[]
    # These are factual evidence for each side, not a model's investment verdict.
    for metric in ('revenue','ebitda','pbt','pat'):
        points=sorted((x for x in series if x['metric']==metric),key=lambda x:x['period_end'])
        if len(points)<2:continue
        previous,current=points[-2:]
        if previous['requires_visual_review'] or current['requires_visual_review']:continue
        from datetime import date
        if not 85 <= (date.fromisoformat(current['period_end'])-date.fromisoformat(previous['period_end'])).days <= 95:continue
        a,b=Decimal(previous['value']),Decimal(current['value'])
        if a<=0 or b<0:continue
        change=delta(b,a)
        item={'claim':f"Reported {metric.upper()} {'rose' if b>a else 'fell' if b<a else 'was unchanged'} from INR {a} crore to INR {b} crore between {previous['period_end']} and {current['period_end']}.",
              'citations':previous['citations']+current['citations'],'change':change,
              'status':'deterministic_primary_comparison','causality_established':False}
        if b>a:bull.append(item)
        elif b<a:bear.append(item)
    modules['bull_bear'].update(status='primary_financial_evidence' if bull or bear else 'unavailable',
        bull=bull[:3],bear=bear[:3],limitations=['Financial changes are evidence for consideration, not a complete investment thesis.'],claims_verified=False)
    return modules
