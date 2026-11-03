"""Read-only detail routes. Opening a page never fetches a provider or invokes a model."""
import hashlib
import json
import re
from datetime import datetime,timedelta,timezone
from fastapi import HTTPException,Query
from urllib.parse import unquote
from .push import digest,filing_card
from .cross_signal import signals,alert_cutoff


def annotate_quotes(value):
    if isinstance(value,dict):
        if isinstance(value.get('quote'),str) and value.get('sha256') and value.get('page'):
            value['quote_id']=hashlib.sha256(value['quote'].encode()).hexdigest()
        for child in list(value.values()):annotate_quotes(child)
    elif isinstance(value,list):
        for child in value:annotate_quotes(child)
    return value


def install(app,store,checked):
    @app.get('/api/push/company/{ticker}')
    def company_digest(ticker:str,window:str='30d'):
        try:return annotate_quotes(digest(store,window,symbols=[checked(ticker)]))
        except ValueError as exc:raise HTTPException(422,str(exc)) from exc

    @app.get('/api/push/filing/{filing_id}')
    def filing_detail(filing_id:str,as_of:datetime|None=None):
        if not re.fullmatch(r'[0-9a-f]{64}',filing_id):raise HTTPException(422,'Invalid filing ID')
        end=as_of or datetime.now(timezone.utc)
        if end.tzinfo is None or end>datetime.now(timezone.utc):raise HTTPException(422,'Invalid observation cutoff')
        end=end.astimezone(timezone.utc)
        with store.connect() as db:
            row=db.execute('SELECT payload,revision,observed_at,content_hash FROM filing_versions WHERE id=? AND observed_at<=? AND published_at<=? ORDER BY revision DESC LIMIT 1',
                (filing_id,end.isoformat(),end.isoformat())).fetchone()
        if not row:raise HTTPException(404,'Filing not available by the selected observation cutoff')
        record={**json.loads(row['payload']),**{k:row[k] for k in ('revision','observed_at','content_hash')}}
        return {'card':annotate_quotes(filing_card(store,record,end)[0]),'as_of':end.isoformat()}

    @app.get('/api/push/alert/{alert_id}')
    def alert_detail(alert_id:str,price_threshold:float=Query(3,gt=0,le=100,allow_inf_nan=False),vol_threshold:float=Query(2,gt=0,le=100,allow_inf_nan=False)):
        alert_id=unquote(alert_id)
        match=re.fullmatch(r'([A-Z0-9&-]{1,30}):(\d{4}-\d{2}-\d{2})',alert_id)
        if not match:raise HTTPException(422,'Invalid alert ID')
        ticker=checked(match[1])
        try:cutoff=alert_cutoff(match[2])
        except ValueError as exc:raise HTTPException(422,'Invalid session') from exc
        now=datetime.now(timezone.utc)
        context=store.filings(ticker,cutoff-timedelta(hours=48),min(now,cutoff+timedelta(hours=48)))
        snapshot=store.get('market',ticker)
        alerts=signals(snapshot,context,cutoff,now,price_threshold,vol_threshold) if cutoff<=now else []
        alert=next((a for a in alerts if a['id']==alert_id),None)
        if not alert:raise HTTPException(404,'No saved alert matches this session and these thresholds. Coverage or the saved snapshot may have changed.')
        bars=sorted(snapshot['data'].get('indicator_history') or snapshot['data'].get('bars',[]),key=lambda b:b['date'])
        end=next(i for i,b in enumerate(bars) if b['date']==match[2])
        return {'alert':alert,'bars':bars[max(0,end-29):end+1], 'volume_baseline':bars[max(0,end-20):end+1],
                'baseline_policy':'20 prior completed sessions, excluding the trigger session',
                'thresholds':{'price_threshold':price_threshold,'vol_threshold':vol_threshold}}

    @app.get('/api/evidence/{sha256}/metadata')
    def evidence_metadata(sha256:str,page:int=Query(1,ge=1,le=1500),quote_id:str|None=None):
        if not re.fullmatch(r'[0-9a-f]{64}',sha256) or quote_id and not re.fullmatch(r'[0-9a-f]{64}',quote_id):raise HTTPException(422,'Invalid evidence identity')
        # Metadata only; never read all PDF blobs. Bound extraction snapshot work.
        with store.connect() as db:
            raw=db.execute('SELECT url,fetched_at FROM raw_responses WHERE sha256=?',(sha256,)).fetchone()
            rows=db.execute("SELECT payload FROM snapshots WHERE kind IN ('pull','push_analysis') AND instr(payload,?)>0 ORDER BY fetched_at DESC LIMIT 40",(sha256,)).fetchall() if quote_id else []
        found=None
        def walk(value):
            nonlocal found
            if found:return
            if isinstance(value,dict):
                quote=value.get('quote')
                if value.get('sha256')==sha256 and value.get('page')==page and isinstance(quote,str) and hashlib.sha256(quote.encode()).hexdigest()==quote_id:
                    found=value;return
                for child in value.values():walk(child)
            elif isinstance(value,list):
                for child in value:walk(child)
        for row in rows:walk(json.loads(row['payload']))
        if quote_id and not found:raise HTTPException(404,'This excerpt is not in the retained analysis snapshots. The saved PDF can still be inspected.')
        if not found and not raw:raise HTTPException(404,'Document metadata unavailable')
        return {'citation':found or {'sha256':sha256,'page':page,'quote':'','url':raw['url'],'observed_at':raw['fetched_at']},
                'integrity_status':'Checked when saved PDF bytes are requested; a hash alone is not certification.'}
