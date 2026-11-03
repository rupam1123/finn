"""Speaker/topic retrieval retaining exact page text and bounded offsets."""
import re
from .evidence import citation
from .transcript_context import turns

TOPICS = {'guidance':r'guidance|outlook|expect|target', 'cash':r'cash|receivable|inventory|working capital',
          'governance':r'related party|contingent|auditor', 'performance':r'revenue|profit|margin|growth'}


def chunks(document, max_chars=1800):
    if max_chars < 100:
        raise ValueError('Chunk budget too small')
    result=[]
    for turn in turns(document):
        for start in range(0,len(turn['text']),max_chars):
            quote=turn['text'][start:start+max_chars].strip()
            if not quote:continue
            result.append({'speaker':turn['speaker'],'speaker_verified':turn['speaker_verified'],
                'speaker_evidence':turn['speaker_evidence'],
                'topics':[k for k,p in TOPICS.items() if re.search(p,quote,re.I)],
                'requires_visual_review':turn['requires_visual_review'],
                'citation':citation(document,turn['page'],quote)})
    return result


def retrieve(index,query,limit=8):
    if not 1 <= limit <= 100:
        raise ValueError('Retrieval limit must be 1–100')
    terms=set(re.findall(r'\w+',query.lower()))
    ranked=[(len(terms & set(re.findall(r'\w+',item['citation']['quote'].lower()))),i,item)
            for i,item in enumerate(index)]
    return [item for score,_,item in sorted(ranked,key=lambda x:(-x[0],x[1]))[:limit] if score]


def reported_quarter(document):
    """Explicit cover/title period only; no dates inferred from fiscal-year labels."""
    text='\n'.join(p['text'] for p in document.get('pages',[])[:3])
    pattern=r'\bQ([1-4])\s*(?:&\s*(?:H1|9M|Full\s+Year)?\s*)?FY\s*[\'’]?(20\d{2}|\d{2})\b'
    found=re.search(pattern,text,re.I)
    if found:
        year=int(found[2]);year=year+2000 if year<100 else year
        return {'label':f'Q{found[1]} FY{year}','order':year*4+int(found[1]),
                'period_end':None,'method':'reported_fiscal_label'}
    found=re.search(r'quarter(?:\s+and\s+[\w-]+)?\s+ended\s+(March|June|September|December)\s+(\d{1,2}),?\s+(20\d{2})',text,re.I)
    if found:
        from datetime import date
        month={'march':3,'june':6,'september':9,'december':12}[found[1].lower()]
        end=date(int(found[3]),month,int(found[2])).isoformat()
        return {'label':end,'order':int(found[3])*12+month,'period_end':end,'method':'reported_date'}
    found=re.search(r'quarterly-results/(20\d{2})-(20\d{2})/q([1-4])',text,re.I)
    if found:
        return {'label':f'Q{found[3]} FY{found[2]}','order':int(found[2])*4+int(found[3]),
                'period_end':None,'method':'issuer_report_path'}
    return None


def quarter_evidence(documents):
    grouped={}
    for document in documents:
        if document.get('kind')!='transcript':continue
        period=reported_quarter(document)
        if not period:continue
        grouped.setdefault(period['label'],[]).append((period,document))
    # Separate date-labelled and fiscal-labelled groups to avoid pretending a fiscal calendar is known.
    methods={pair[0]['period_end'] is not None for group in grouped.values() for pair in group}
    omitted = []
    if len(methods)>1:
        date_groups = {k:v for k,v in grouped.items() if v[0][0]['period_end'] is not None}
        fiscal_groups = {k:v for k,v in grouped.items() if v[0][0]['period_end'] is None}
        selected = date_groups if len(date_groups)>=len(fiscal_groups) else fiscal_groups
        omitted = [k for k in grouped if k not in selected]
        grouped = selected
    ordered=sorted(grouped.values(),key=lambda group:group[0][0]['order'],reverse=True)
    rows=[]
    by_order={group[0][0]['order']:group for group in ordered}
    expected=[]
    if ordered:
        from datetime import date
        from calendar import monthrange
        latest=ordered[0][0][0]
        gap=3 if latest['period_end'] else 1
        for offset in range(4):
            order=latest['order']-offset*gap
            group=by_order.get(order)
            if group: period=group[0][0]
            elif latest['period_end']:
                year,month=divmod(order-1,12);month+=1
                end=date(year,month,monthrange(year,month)[1]).isoformat()
                period={'label':end,'order':order,'period_end':end,'method':'expected_consecutive_date'}
            else:
                year,quarter=divmod(order-1,4);quarter+=1
                period={'label':f'Q{quarter} FY{year}','order':order,'period_end':None,'method':'expected_consecutive_fiscal_label'}
            expected.append((period,group,by_order.get(order-gap)))
    for period,group,prior_group in expected:
        doc=group[0][1] if group else None
        prior=prior_group[0][1] if prior_group else None
        rows.append({'period_end':period['label'],'status':'review_required' if group else 'missing_transcript',
            'coverage_status':'observed' if group else 'missing_transcript',
            'reason':'Target horizon, speaker and actuals require reconciliation' if group else 'No transcript for this expected consecutive period.',
            'reported_period':period,'revisions':len(group or []),
            'said':retrieve(chunks(prior),'guidance expect target outlook') if prior else [],
            'delivered':retrieve(chunks(doc),'revenue profit growth margin cash') if doc else [],
            'claims_verified':False})
    observed=sum(r['coverage_status']=='observed' for r in rows)
    return {'requested_quarters':4,'observed_periods':observed,'missing_quarters':4-observed,
            'coverage_policy':'Four consecutive periods anchored to latest labelled transcript; fiscal and date labels are not mixed.',
            'ledger':rows,'status':'review_required','unreconciled_period_labels':omitted}
