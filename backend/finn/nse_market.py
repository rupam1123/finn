"""Reconcile a missing final Yahoo session using the exchange's official bhavcopy.

Only the last session may be repaired. Prior adjusted history must be valid, the
exchange previous close must agree, and the corporate-action feed must exclude
an action between the two sessions. All source bytes and derivation are retained.
"""
import csv
import io
import json
import math
import hashlib
import zipfile
from datetime import datetime,timedelta
from datetime import time
from zoneinfo import ZoneInfo
from decimal import Decimal
from urllib.parse import urlencode
from .calendar import expected_session
from .storage import now_iso
from .transport import Fetcher


def parse_bhavcopy(body,session):
    with zipfile.ZipFile(io.BytesIO(body)) as z:
        candidates=[i for i in z.infolist() if i.filename.lower().endswith('.csv')]
        if len(candidates)!=1 or candidates[0].file_size>25_000_000:raise ValueError('Invalid bhavcopy archive')
        text=z.read(candidates[0]).decode('utf-8-sig')
    rows={}
    for row in csv.DictReader(io.StringIO(text)):
        if row.get('TradDt')!=session or row.get('SctySrs')!='EQ' or row.get('Sgmt')!='CM':continue
        ticker=row['TckrSymb']
        if ticker in rows:raise ValueError('Duplicate exchange equity row')
        values={name:float(row[key]) for name,key in [('open','OpnPric'),('high','HghPric'),('low','LwPric'),('close','ClsPric'),('volume','TtlTradgVol'),('previous_close','PrvsClsgPric')]}
        if any(not math.isfinite(v) or v<0 for v in values.values()):raise ValueError('Invalid exchange numeric field')
        if not 0<values['low']<=min(values['open'],values['close'])<=max(values['open'],values['close'])<=values['high']:raise ValueError('Invalid exchange OHLC range')
        rows[ticker]={'date':session,**values,'isin':row.get('ISIN')}
    if not rows:raise ValueError('No exchange EQ rows for requested session')
    return rows


def reconcile(bars,ticker,session,exchange,actions):
    bars=sorted(bars,key=lambda b:b['date'])
    if not bars or bars[-1]['date']!=session or len(bars)<22:raise ValueError('Fallback requires existing final-session stub and at least 21 previous sessions')
    prior=bars[-2]
    previous_session=expected_session(datetime.combine(datetime.fromisoformat(session).date(),time(17),ZoneInfo('Asia/Kolkata')))
    if prior['date']!=previous_session:raise ValueError('Previous session is missing; cannot label a multi-day move as a daily return')
    # Never use this path to hide an older corrupt bar or unexplained adjustment.
    for b in bars[:-1]:
        if any(not math.isfinite(b[k]) or b[k]<=0 for k in ('close','adjusted_close')):raise ValueError('Earlier price history invalid')
        if any(not math.isfinite(b[k]) or b[k]<0 for k in ('open','high','low','volume')):raise ValueError('Earlier OHLCV history invalid')
        if not 0<b['low']<=min(b['open'],b['close'])<=max(b['open'],b['close'])<=b['high']:raise ValueError('Earlier OHLC range invalid')
    if abs(Decimal(str(prior['close']))-Decimal(str(exchange['previous_close'])))>Decimal('.02'):
        raise ValueError('Exchange previous close differs from saved history; corporate action or data revision requires review')
    factor=Decimal(str(prior['adjusted_close']))/Decimal(str(prior['close']))
    if abs(factor-1)>Decimal('.0000001'):raise ValueError('Previous adjustment factor is not unity; cannot infer current adjusted price')
    for row in actions:
        if row.get('symbol')!=ticker:continue
        try:ex=datetime.strptime(row['exDate'],'%d-%b-%Y').date().isoformat()
        except (ValueError,KeyError,TypeError):raise ValueError('Unrecognized corporate-action date')
        if prior['date']<ex<=session:raise ValueError('Corporate action crosses fallback boundary; adjustment requires review')
    bar={k:exchange[k] for k in ('date','open','high','low','close','volume')}
    bar.update(adjusted_close=exchange['close'],dividend=0.0,split=0.0,
               adjustment_method='identity_after_exchange_previous_close_and_no_action_checks')
    return bars[:-1]+[bar]


def repair_latest(tickers,frames,as_of,store,yahoo_hashes):
    from .market_data import indicators,accept_market
    session=expected_session(as_of)
    if session is None:return {t:{'status':'calendar_unknown','symbol':t} for t in tickers}
    fetcher=Fetcher(store)
    results={}
    try:
        date=datetime.fromisoformat(session)
        url=f'https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{date:%Y%m%d}_F_0000.csv.zip'
        bhav=fetcher.get(url,max_bytes=5_000_000,ttl=86400)
        rows=parse_bhavcopy(bhav['body'],session)
        start=min((b[-2]['date'] for b in frames.values() if len(b)>=2),default=session)
        action_url='https://www.nseindia.com/api/corporates-corporateActions?'+urlencode({'index':'equities','from_date':datetime.fromisoformat(start).strftime('%d-%m-%Y'),'to_date':date.strftime('%d-%m-%Y')})
        action_response=fetcher.get(action_url,ttl=3600)
        actions=json.loads(action_response['body'])
        if not isinstance(actions,list) or any(not isinstance(x,dict) for x in actions):raise ValueError('Corporate-action feed schema invalid')
        for ticker in tickers:
            attempt=store.start_attempt('market',ticker)
            try:
                bars=reconcile(frames[ticker],ticker,session,rows[ticker],actions)
                series_bytes=json.dumps({'bars':bars,'inputs':[bhav['sha256'],action_response['sha256']]},sort_keys=True,allow_nan=False).encode()
                series_hash=store.raw('derived:exchange-reconciled-eod:'+ticker+':'+session,series_bytes)
                payload={'symbol':ticker,'source':'Yahoo historical bars + NSE final-session bhavcopy',
                         'source_url':url,'fetched_at':now_iso(),'bars':bars[-30:],'indicator_history':bars,'sha256':series_hash,'indicators':indicators(bars),
                         'cache_hit':False,'calendar_days_since_last_bar':(as_of.astimezone(ZoneInfo('Asia/Kolkata')).date()-date.date()).days,
                         'input_provenance':[{'url':bhav['url'],'sha256':bhav['sha256'],'fetched_at':bhav['fetched_at']},
                                             {'url':action_response['url'],'sha256':action_response['sha256'],'fetched_at':action_response['fetched_at']}],
                         'derivation':'Only the missing final-session row is replaced from NSE; previous-close agreement, unity adjustment and no intervening action are required.'}
                # Include the exact Yahoo response hash rather than implying its
                # history came from the exchange's one-session CSV.
                with store.connect() as db:
                    raw=db.execute('SELECT sha256,url,fetched_at,body FROM raw_responses WHERE sha256=? AND url=?',
                                   (yahoo_hashes[ticker],f'https://finance.yahoo.com/quote/{ticker}.NS/history/')).fetchone()
                if not raw or hashlib.sha256(raw['body']).hexdigest()!=yahoo_hashes[ticker]:raise ValueError('Original Yahoo frame bytes are unavailable or corrupt')
                payload['input_provenance'].insert(0,{k:raw[k] for k in ('sha256','url','fetched_at')})
                results[ticker]=accept_market(store,ticker,payload,as_of,attempt)
            except Exception as exc:
                store.finish_attempt(attempt,'unavailable',error=str(exc));results[ticker]={'status':'unavailable','symbol':ticker,'error':str(exc)}
    except Exception as exc:
        results={ticker:{'status':'unavailable','symbol':ticker,'error':'Exchange fallback: '+str(exc)} for ticker in tickers}
        for ticker in tickers:
            attempt=store.start_attempt('market',ticker)
            store.finish_attempt(attempt,'unavailable',error=results[ticker]['error'])
    finally:fetcher.close()
    return results
