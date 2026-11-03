import copy
import io
import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pandas as pd
from finn.pdf_runtime import pymupdf
import pytest
from fastapi.testclient import TestClient

from finn import cli
from finn.calendar import expected_session, freshness
from finn.documents import extract_document, resolve_transcript, transcript_quality
from finn.filings_ingest import parse_nse
from finn.main import create_app
from finn.market_data import accept_market, fetch_market
from finn.storage import SCHEMA_VERSION, Store
from finn.transport import Fetcher, FetchError

FIX = Path(__file__).parent / 'fixtures' / 'reliability'
NOW = datetime(2026, 10, 28, 3, tzinfo=timezone.utc)


def captured(name):
    return json.loads((FIX / (name + '.json')).read_text())


def test_real_older_market_response_never_replaces_newer(tmp_path):
    store = Store(tmp_path/'test.db')
    newer, older = captured('tcs-market-newer'), captured('tcs-market-older')
    store.put('market', 'TCS', newer)
    before = store.get('market', 'TCS')
    attempt = store.start_attempt('market', 'TCS')
    result = accept_market(store, 'TCS', older, NOW, attempt)
    after = store.get('market', 'TCS')
    assert result['status'] == 'rejected_older'
    assert before['data'] == after['data'] and before['fetched_at'] == after['fetched_at']
    assert after['last_attempt']['status'] == 'rejected_older'
    assert after['last_attempt']['details']['received_as_of'] == '2026-10-26'


def test_stale_first_response_is_explicit_and_not_reused(tmp_path):
    store = Store(tmp_path/'test.db')
    older = captured('tcs-market-older')
    result = accept_market(store, 'TCS', older, NOW, store.start_attempt('market', 'TCS'))
    assert result['status'] == 'stale'
    assert result['freshness']['expected_session'] == '2026-10-27'
    assert store.reusable('market', 'TCS') is None


def test_equal_session_provider_correction_is_accepted(tmp_path):
    store = Store(tmp_path/'test.db')
    data = captured('tcs-market-newer')
    store.put('market', 'TCS', data)
    data['provider_correction'] = 'explicit diagnostic metadata'
    assert store.put('market', 'TCS', data)
    assert store.get('market', 'TCS')['data']['provider_correction']


def test_older_observation_cannot_undo_same_session_correction(tmp_path):
    store=Store(tmp_path/'test.db');data=captured('tcs-market-newer')
    store.put('market','TCS',data)
    data['fetched_at']='2026-10-26T00:00:00+00:00'
    assert store.put('market','TCS',data) is False


@pytest.mark.parametrize('stamp,expected', [
    ('2026-10-28T05:00:00+05:30', '2026-10-27'),
    ('2026-10-28T17:59:00+05:30', '2026-10-27'),
    ('2026-10-28T18:00:00+05:30', '2026-10-28'),
    ('2026-10-25T20:00:00+05:30', '2026-10-23'),
    ('2026-10-20T20:00:00+05:30', '2026-10-19'),
    ('2026-01-15T20:00:00+05:30', '2026-01-14'),
    ('2026-11-08T22:00:00+05:30', None),
    ('2027-01-05T20:00:00+05:30', None),
])
def test_expected_session_ist_weekend_holiday_and_unknown(stamp, expected):
    assert expected_session(datetime.fromisoformat(stamp)) == expected


def test_calendar_unknown_abstains():
    assert freshness('2027-01-04', datetime(2027,1,5,tzinfo=timezone.utc))['status'] == 'calendar_unknown'
    with pytest.raises(ValueError): expected_session(datetime(2026,10,28))


def test_provider_failure_records_attempt_without_destroying_cache(tmp_path, monkeypatch):
    import yfinance
    store = Store(tmp_path/'test.db')
    newer = captured('tcs-market-newer')
    store.put('market', 'TCS', newer)
    def fail(*args, **kwargs): raise RuntimeError('diagnostic provider outage')
    monkeypatch.setattr(yfinance, 'download', fail)
    result = fetch_market(['TCS'], NOW, store, force=True)
    assert result['TCS']['status'] == 'unavailable'
    assert store.get('market', 'TCS')['data'] == newer
    assert store.last_attempt('market', 'TCS')['details']['error'] == 'diagnostic provider outage'


@pytest.mark.parametrize('field,value', [('Open', float('nan')), ('High', 1), ('Volume', -1)])
def test_invalid_ohlcv_does_not_replace_cache(tmp_path, monkeypatch, field, value):
    import yfinance
    store = Store(tmp_path/'test.db')
    newer = captured('tcs-market-newer')
    store.put('market', 'TCS', newer)
    values = {'Open': [100.], 'High': [110.], 'Low': [90.], 'Close': [100.], 'Adj Close': [100.],
              'Volume': [1000.], 'Dividends': [0.], 'Stock Splits': [0.]}
    values[field] = [value]
    frame = pd.concat({'TCS.NS': pd.DataFrame(values, index=pd.to_datetime(['2026-10-27']))}, axis=1)
    monkeypatch.setattr(yfinance, 'download', lambda *a, **k: frame)
    assert fetch_market(['TCS'], NOW, store, force=True)['TCS']['status'] == 'unavailable'
    assert store.get('market', 'TCS')['data'] == newer


def test_real_notice_resolves_to_real_issuer_transcript(tmp_path):
    notice, transcript = captured('astral-notice'), captured('astral-transcript')
    requests = []
    bodies = {notice['url']: (FIX/'astral-notice.pdf').read_bytes(), transcript['url']: (FIX/'astral-transcript.pdf').read_bytes()}
    def respond(req):
        requests.append(str(req.url))
        return httpx.Response(200, content=bodies[str(req.url)])
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        fetcher = Fetcher(Store(tmp_path/'test.db'), client)
        result = resolve_transcript(notice['url'], fetcher)
    assert result['url'] == transcript['url'] and result['page_count'] == 29
    assert result['sha256'] == transcript['sha256'] and not result['claims_verified']
    assert len(result['discovery_chain']) == 2 and len(requests) == 2
    assert result['discovery_chain'][0]['quality']['status'] == 'not_full_transcript'


@pytest.mark.parametrize('name,expected', [('astral-notice','not_full_transcript'), ('astral-transcript','transcript_candidate'), ('tcs-transcript','transcript_candidate')])
def test_quality_gate_on_real_pdfs(name, expected):
    doc = extract_document((FIX/(name+'.pdf')).read_bytes(), captured(name)['url'])
    assert transcript_quality(doc)['status'] == expected


def test_notice_without_allowed_links_is_not_accepted(tmp_path):
    pdf = pymupdf.open(); page = pdf.new_page()
    page.insert_text((30,40), 'Transcript is available on our website. This is a synthetic notice.')
    page.insert_link({'kind': pymupdf.LINK_URI, 'from': pymupdf.Rect(30,40,90,60), 'uri':'https://evil.test/document.pdf'})
    calls=[]
    def respond(req): calls.append(str(req.url)); return httpx.Response(200,content=pdf.tobytes())
    fetcher=Fetcher(Store(tmp_path/'test.db'),httpx.Client(transport=httpx.MockTransport(respond)))
    with pytest.raises(ValueError,match='No suitable full transcript'): resolve_transcript('https://www.tcs.com/notice.pdf',fetcher)
    assert len(calls)==1
    fetcher.close();pdf.close()


def test_scan_cannot_be_transcript():
    pdf=pymupdf.open();pdf.new_page()
    doc=extract_document(pdf.tobytes(),'https://www.tcs.com/scan.pdf')
    assert doc['status']=='ocr_required' and transcript_quality(doc)['status']=='not_full_transcript'
    pdf.close()


def real_row():
    raw=json.loads((FIX.parent/'nse.json').read_text())[0]
    return parse_nse([raw], 'TCS', datetime(2026,1,1,tzinfo=timezone.utc), datetime(2026,12,31,tzinfo=timezone.utc))['filings'][0]


def test_amended_real_filing_retains_history_and_stable_identity(tmp_path):
    store=Store(tmp_path/'test.db'); row=real_row()
    t1='2026-10-27T15:00:00+00:00';t2='2026-10-27T16:00:00+00:00'
    store.add_filings([row],t1)
    changed=copy.deepcopy(row);changed['description']='DIAGNOSTIC amendment to a captured real row';changed['document_url']='https://nsearchives.nseindia.com/revised.pdf'
    store.add_filings([changed],t2);store.add_filings([changed],t2)
    before=store.filings('TCS','2026-01-01',t1);after=store.filings('TCS','2026-01-01',t2)
    assert before[0]['description']==row['description'] and before[0]['revision']==1
    assert len(after)==1 and after[0]['description']==changed['description'] and after[0]['revision']==2
    assert before[0]['id']==after[0]['id']
    with store.connect() as db: assert db.execute('SELECT count(*) FROM filing_versions').fetchone()[0]==2
    store.add_filings([row],t1)
    assert store.filings('TCS','2026-01-01',t2)[0]['revision']==2


def test_parser_identity_survives_changed_attachment():
    raw=json.loads((FIX.parent/'nse.json').read_text())[0];changed={**raw,'attchmntFile':'https://nsearchives.nseindia.com/revised.pdf'}
    start=datetime(2026,1,1,tzinfo=timezone.utc);end=datetime(2026,12,31,tzinfo=timezone.utc)
    a=parse_nse([raw],'TCS',start,end)['filings'][0];b=parse_nse([changed],'TCS',start,end)['filings'][0]
    assert a['id']==b['id']


def test_migration_keeps_legacy_records_and_is_idempotent(tmp_path):
    path=tmp_path/'old.db';row=real_row();row['id']='legacy-id'
    db=sqlite3.connect(path)
    db.executescript('CREATE TABLE schema_version(version INTEGER PRIMARY KEY); INSERT INTO schema_version VALUES(1); CREATE TABLE filings(id TEXT PRIMARY KEY,symbol TEXT,published_at TEXT,payload TEXT);')
    db.execute('INSERT INTO filings VALUES(?,?,?,?)',(row['id'],row['symbol'],row['published_at'],json.dumps(row)));db.commit();db.close()
    store=Store(path);store=Store(path)
    rows=store.filings('TCS','2026-01-01')
    assert len(rows)==1 and rows[0]['id']!='legacy-id'
    with store.connect() as db:
        assert db.execute('SELECT version FROM schema_version').fetchone()[0]==SCHEMA_VERSION
        assert db.execute('SELECT count(*) FROM filing_versions').fetchone()[0]==1
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'


def test_closed_window_boundaries_and_timezones(tmp_path):
    store=Store(tmp_path/'test.db')
    start='2026-10-26T12:00:00+00:00';end='2026-10-27T12:00:00+00:00'
    for i,stamp in enumerate(['2026-10-26T11:59:59+00:00',start,end,'2026-10-27T12:00:00.000001+00:00']):
        store.add_filings([{'id':str(i),'symbol':'TCS','published_at':stamp}], '2026-10-25T00:00:00+00:00')
    rows=store.filings('TCS',start,'2026-10-27T17:30:00+05:30')
    assert {r['id'] for r in rows}=={'1','2'}
    with pytest.raises(ValueError): store.filings('TCS',end,start)


def test_api_failed_refresh_last_good_and_no_cache_states(tmp_path, monkeypatch):
    path=tmp_path/'test.db';store=Store(path)
    store.put('fundamentals','TCS',{'symbol':'TCS','fetched_at':'2026-10-27T00:00:00+00:00'})
    def fail(*a,**k): raise RuntimeError('diagnostic blocked provider')
    monkeypatch.setattr(cli,'fetch_screener',fail);monkeypatch.setattr(cli,'fetch_nse',fail)
    cli.ingest_company('TCS',store,NOW,force=True)
    cli.ingest_company('ASTRAL',store,NOW,force=True)
    with TestClient(create_app(path)) as client:
        result=client.get('/api/company/TCS')
        assert result.status_code==200
        d=result.json();assert d['data']['symbol']=='TCS' and d['last_attempt']['status']=='unavailable'
        assert d['fetched_at']=='2026-10-27T00:00:00+00:00' and d['cache_expired']
        assert client.get('/api/company/ASTRAL').status_code==503
        assert client.get('/api/company/ZZZZNOTREAL').status_code==404
        assert client.get('/api/filings/TCS?as_of=2099-01-01T00:00:00Z').status_code==422
        assert client.get('/api/filings/TCS?as_of=2026-10-27T00:00:00').status_code==422


def test_successful_retry_clears_failure_and_preserves_observed_timestamp(tmp_path,monkeypatch):
    store=Store(tmp_path/'test.db');attempt=store.start_attempt('fundamentals','TCS');store.finish_attempt(attempt,'unavailable',error='old failure')
    stamp=datetime.now(timezone.utc).isoformat()
    data={'symbol':'TCS','warnings':[],'tables':{},'documents':[],'basis':'consolidated','latency_ms':1,'fetched_at':stamp}
    monkeypatch.setattr(cli,'fetch_screener',lambda *a:data)
    monkeypatch.setattr(cli,'fetch_nse',lambda *a:{'filings':[],'errors':[],'fetched_at':stamp})
    cli.ingest_company('TCS',store,NOW,force=True)
    snapshot=store.reusable('fundamentals','TCS')
    assert snapshot['last_attempt']['status']=='ok' and snapshot['fetched_at']==stamp


def test_ttl_force_expiry_and_no_failed_response_cache(tmp_path):
    store=Store(tmp_path/'test.db');calls=[]
    def respond(req): calls.append(str(req.url));return httpx.Response(200,content=b'realistically mutable source')
    fetcher=Fetcher(store,httpx.Client(transport=httpx.MockTransport(respond)))
    url='https://example.com/source';first=fetcher.get(url,ttl=60);second=fetcher.get(url,ttl=60)
    assert len(calls)==1 and second['cache_hit'] and second['fetched_at']==first['fetched_at']
    fetcher.force=True;fetcher.get(url,ttl=60);assert len(calls)==2
    fetcher.force=False
    with store.connect() as db:
        cached=json.loads(db.execute('SELECT payload FROM http_cache').fetchone()[0]);cached['fetched_at']='2000-01-01T00:00:00+00:00'
        db.execute('UPDATE http_cache SET payload=?',(json.dumps(cached),))
    fetcher.get(url,ttl=60);assert len(calls)==3
    with pytest.raises(FetchError): fetcher.get(url,max_bytes=2,ttl=60)
    assert len(calls)==4
    fetcher.close()
    bad=Fetcher(store,httpx.Client(transport=httpx.MockTransport(lambda req:httpx.Response(403))))
    with pytest.raises(FetchError):bad.get('https://example.com/blocked',ttl=60)
    assert store.cached_http('https://example.com/blocked',60,100) is None
    bad.close()


def test_corrupt_cache_not_served(tmp_path):
    store=Store(tmp_path/'test.db');url='https://example.com/pdf'
    digest=store.raw(url,b'original');store.cache_http(url,{'url':url,'fetched_at':datetime.now(timezone.utc).isoformat(),'sha256':digest})
    with store.connect() as db:db.execute('UPDATE raw_responses SET body=?',(b'corrupted',))
    assert store.cached_http(url,60,1000) is None


def test_real_market_ttl_skips_network(tmp_path,monkeypatch):
    import yfinance
    store=Store(tmp_path/'test.db');data=captured('tcs-market-newer');data['fetched_at']=datetime.now(timezone.utc).isoformat();store.put('market','TCS',data)
    def fail(*a,**k):raise AssertionError('network must not be used for a current unexpired snapshot')
    monkeypatch.setattr(yfinance,'download',fail)
    assert fetch_market(['TCS'],NOW,store)['TCS']['cache_hit']


def test_real_partial_provider_frame_is_rejected_and_archived(tmp_path,monkeypatch):
    import yfinance
    store=Store(tmp_path/'test.db');newer=captured('tcs-market-newer');store.put('market','TCS',newer)
    frame=pd.read_json(io.StringIO((FIX/'tcs-provider-partial.json').read_text()),orient='table')
    monkeypatch.setattr(yfinance,'download',lambda *a,**k:pd.concat({'TCS.NS':frame},axis=1))
    result=fetch_market(['TCS'],NOW,store,force=True)['TCS']
    assert result['status']=='unavailable' and 'close' in result['error']
    assert store.get('market','TCS')['data']==newer
    digest=store.last_attempt('market','TCS')['details']['response_sha256']
    with store.connect() as db:assert db.execute('SELECT 1 FROM raw_responses WHERE sha256=?',(digest,)).fetchone()


def test_retry_backoff_remains_failed_and_force_bypasses_it(tmp_path,monkeypatch):
    import yfinance
    store=Store(tmp_path/'test.db');store.put('market','TCS',captured('tcs-market-newer'))
    calls=[]
    def fail(*a,**k):calls.append(1);raise RuntimeError('diagnostic outage')
    monkeypatch.setattr(yfinance,'download',fail)
    fetch_market(['TCS'],NOW,store,force=True)
    result=fetch_market(['TCS'],NOW,store)['TCS']
    assert result['status']=='unavailable' and result['cache_hit'] and len(calls)==1
    assert result['retry_after_seconds']>0
    fetch_market(['TCS'],NOW,store,force=True)
    assert len(calls)==2


def test_expired_snapshot_and_failed_refresh_are_not_reusable(tmp_path):
    store=Store(tmp_path/'test.db')
    store.put('fundamentals','TCS',{'fetched_at':'2000-01-01T00:00:00+00:00'})
    assert store.reusable('fundamentals','TCS') is None
    store.put('fundamentals','TCS',{})
    assert store.reusable('fundamentals','TCS') is not None
    attempt=store.start_attempt('fundamentals','TCS');store.finish_attempt(attempt,'unavailable',error='diagnostic')
    assert store.reusable('fundamentals','TCS') is None


def test_api_refuses_legacy_notice(tmp_path):
    path=tmp_path/'test.db';store=Store(path)
    doc=extract_document((FIX/'astral-notice.pdf').read_bytes(),captured('astral-notice')['url'])
    store.put('primary_sample','ASTRAL',doc)
    with TestClient(create_app(path)) as client:
        assert client.get('/api/primary/ASTRAL').status_code==503


def test_changed_cache_key_does_not_reuse_other_window(tmp_path):
    calls=[]
    def respond(req):calls.append(str(req.url));return httpx.Response(200,content=str(req.url).encode())
    fetcher=Fetcher(Store(tmp_path/'test.db'),httpx.Client(transport=httpx.MockTransport(respond)))
    a=fetcher.get('https://example.com/feed?days=1',ttl=60)
    b=fetcher.get('https://example.com/feed?days=30',ttl=60)
    assert len(calls)==2 and a['body']!=b['body']
    fetcher.close()


def test_same_host_redirect_cannot_add_credentials_or_port(tmp_path):
    for url in ['https://user:pass@example.com/pdf','https://example.com:8443/pdf']:
        fetcher=Fetcher(Store(tmp_path/'test.db'),httpx.Client(transport=httpx.MockTransport(lambda req:httpx.Response(302,headers={'location':url}))))
        with pytest.raises(FetchError):fetcher.get('https://example.com/pdf')
        fetcher.close()


def test_retry_after_failed_forced_refresh_cannot_hide_behind_http_cache(tmp_path,monkeypatch):
    store=Store(tmp_path/'test.db')
    for kind in ['fundamentals','filings_coverage','primary_sample']:
        attempt=store.start_attempt(kind,'TCS');store.finish_attempt(attempt,'unavailable',error='diagnostic previous outage')
    forced=[]
    def company(s,fetcher):
        forced.append(('fundamentals',fetcher.force))
        raise RuntimeError('diagnostic still unavailable')
    def filings(s,start,end,fetcher):
        forced.append(('filings',fetcher.force))
        return {'filings':[{'document_url':'https://www.tcs.com/transcript.pdf','title':'Transcript','description':''}], 'errors':[]}
    def document(url,fetcher):
        forced.append(('primary',fetcher.force))
        raise RuntimeError('diagnostic still unavailable')
    monkeypatch.setattr(cli,'fetch_screener',company)
    monkeypatch.setattr(cli,'fetch_nse',filings)
    monkeypatch.setattr(cli,'resolve_transcript',document)
    cli.ingest_company('TCS',store,NOW,primary_sample=True)
    assert forced==[('fundamentals',True),('filings',True),('primary',True)]
    assert store.last_attempt('fundamentals','TCS')['status']=='unavailable'
