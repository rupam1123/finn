"""Conservative presentation of old cached ledgers, without model calls or writes."""
import re
from calendar import monthrange
from datetime import date


def consecutive_ledger(value):
    if value.get('coverage_policy'):return value
    rows=value.get('ledger',[])
    if not rows:return value
    def order(label):
        fiscal=re.fullmatch(r'Q([1-4]) FY(\d{4})',label)
        if fiscal:return ('fiscal',int(fiscal[2])*4+int(fiscal[1]))
        try:
            d=date.fromisoformat(label);return ('date',d.year*12+d.month)
        except ValueError:return None
    parsed=[(order(r.get('period_end','')),r) for r in rows]
    parsed=[(o,r) for o,r in parsed if o]
    if not parsed:return value
    mode=parsed[0][0][0];parsed=[(o,r) for o,r in parsed if o[0]==mode]
    latest=max(o[1] for o,r in parsed);by={o[1]:r for o,r in parsed};result=[]
    for i in range(4):
        index=latest-i*(1 if mode=='fiscal' else 3)
        if index in by:result.append({**by[index],'coverage_status':'observed'});continue
        if mode=='fiscal':year,q=divmod(index-1,4);label=f'Q{q+1} FY{year}'
        else:year,m=divmod(index-1,12);label=date(year,m+1,monthrange(year,m+1)[1]).isoformat()
        result.append({'period_end':label,'coverage_status':'missing_transcript','status':'missing_transcript','reason':'No retained transcript for this expected consecutive period.','said':[],'delivered':[],'comparisons':[],'claims_verified':False})
    observed=sum(r['coverage_status']=='observed' for r in result)
    return {**value,'ledger':result,'requested_quarters':4,'observed_periods':observed,'missing_quarters':4-observed,
            'resolved_comparisons':sum(c.get('status') in ('within_target','above_target','below_target') for r in result for c in r.get('comparisons',[])),
            'coverage_policy':'Consecutive periods projected from retained labels; no new source or model validation.'}
