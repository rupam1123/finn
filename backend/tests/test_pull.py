import hashlib
import json
from datetime import date
import pytest
from finn.storage import Store
from finn.pull import build_research, verified_document, research
from finn.pull_jobs import initialize, enqueue, get_job, run_one
from finn.narrative_auditor import ledger
from finn.transcript_rag import chunks, retrieve


def document():
    return {'url':'https://nsearchives.nseindia.com/a.pdf','sha256':hashlib.sha256(b'%PDF fixture').hexdigest(),
            'fetched_at':'2026-01-01T00:00:00+00:00','status':'text_extracted','page_count':1,'kind':'transcript',
            'pages':[{'page':1,'text':'Moderator: Welcome.\nJane Smith: We expect revenue growth. Working capital is a risk.'}]}


def test_missing_is_explicit():
    r=build_research('KPIL',[],[])
    assert r['status']=='unavailable'
    assert len(r['modules'])==8
    assert r['say_do']['missing_quarters']==4
    assert not r['claims_verified']


def test_no_four_pdf_four_quarter_equivalence():
    r=build_research('INFY',[document()]*4,[])
    assert r['say_do']['observed_periods']==0
    assert r['modules']['forward_guidance']['excerpts']
    assert not r['modules']['forward_guidance']['claims_verified']


def test_hash_failure_closed(tmp_path):
    store=Store(tmp_path/'test.db')
    with pytest.raises(ValueError): verified_document(store,document())
    store.raw(document()['url'],b'%PDF fixture')
    assert verified_document(store,document())['sha256']==document()['sha256']


def test_speaker_topics():
    index=chunks(document())
    assert index[-1]['speaker']=='Jane Smith'
    assert 'guidance' in index[-1]['topics']
    assert index[-1]['speaker_verified'] is False
    with pytest.raises(ValueError): retrieve(index,'growth',0)


def test_jobs_deduplicate_and_recoverable(tmp_path,monkeypatch):
    store=Store(tmp_path/'test.db');initialize(store)
    first=enqueue(store,'KPIL'); second=enqueue(store,'kpil')
    assert first['id']==second['id']
    monkeypatch.setattr('finn.pull_jobs.research',lambda *args:{'status':'partial'})
    assert run_one(store)
    assert get_job(store,first['id'])['status']=='partial'
    assert not run_one(store)
    assert enqueue(store,'KPIL')['id']!=first['id']


def test_job_failure_persisted(tmp_path,monkeypatch):
    store=Store(tmp_path/'test.db');initialize(store);job=enqueue(store,'INFY')
    def fail(*args): raise ValueError('test failure')
    monkeypatch.setattr('finn.pull_jobs.research',fail)
    run_one(store)
    assert get_job(store,job['id'])['status']=='failed'
    assert get_job(store,'absent') is None


def test_four_period_ledger_missing_guidance():
    r=ledger([],[],['2025-03-31','2025-06-30','2025-09-30','2025-12-31','2024-12-31'],'2026-01-01')
    assert len(r['ledger'])==4
    assert all(x['status']=='no_comparable_guidance' for x in r['ledger'])


def test_api_queue_and_read(tmp_path):
    from finn.main import create_app
    from fastapi.testclient import TestClient
    with TestClient(create_app(tmp_path/'test.db')) as client:
        assert client.get('/api/pull/KPIL').status_code==404
        queued=client.post('/api/pull/KPIL/jobs')
        assert queued.status_code==202
        assert client.get('/api/pull-jobs/'+queued.json()['id']).json()['status']=='queued'
        assert client.post('/api/pull/bad%20symbol/jobs').status_code==422


def test_model_quote_rejection():
    from finn.pull_reasoning import reason
    class Model:
        def generate(self,*args):
            return {'proposals':[{'module':'guidance','claim':'Invented claim','page':1,'quote':'This quote is not in the primary document.'}]},{}
    with pytest.raises(ValueError): reason(document(),Model())


def test_model_quote_presence_is_not_claim_verification():
    from finn.pull_reasoning import reason
    class Model:
        def generate(self,*args):
            return {'proposals':[{'module':'guidance','claim':'Candidate statement','page':1,'quote':'We expect revenue growth.'}]},{'model':'test fixture'}
    result=reason(document(),Model())
    assert result['proposals'][0]['status']=='semantic_review_required'
    assert not result['proposals'][0]['claims_verified']


def test_reported_quarter_and_event_abstention():
    from finn.transcript_rag import reported_quarter,quarter_evidence
    d=document()
    assert reported_quarter(d) is None
    docs=[]
    for q in (1,2,3,4):
        item=document();item['pages'][0]['text']=f'Q{q} & FY 2026\nJane Smith: We expect revenue growth.';docs.append(item)
    result=quarter_evidence(docs)
    assert result['observed_periods']==4
    assert all(not row['claims_verified'] for row in result['ledger'])
    assert result['ledger'][0]['said']


def test_working_capital_guards():
    from finn.forensic_analyzer import working_capital_cycle
    def fact(value):
        return dict(value=value,unit='days',period_start='2025-04-01',period_end='2026-03-31',basis='consolidated',definition='annual_average',reviewed_primary=True,citations=[{'quote':'synthetic test'}])
    assert working_capital_cycle(fact(30),fact(40),fact(20))['value']=='50'
    assert working_capital_cycle(None,None,None)['status']=='missing'
    assert working_capital_cycle(None,None,None,'bank')['status']=='not_applicable'
    assert working_capital_cycle(fact(30),dict(fact(40),basis='standalone'),fact(20))['status']=='not_comparable'


def test_saved_pipeline_and_cache(tmp_path):
    store=Store(tmp_path/'test.db');doc=document()
    store.raw(doc['url'],b'%PDF fixture');store.put('primary_sample','KPIL',doc)
    events=[];result=research('KPIL',store,events.append,saved_only=True)
    assert result['status']=='partial'
    assert events[-1]['stage']=='finished'
    assert research('KPIL',store,events.append,saved_only=True)==result
    assert events[-1]['stage']=='cached'


def test_completed_job_stream(tmp_path):
    from finn.main import create_app
    from fastapi.testclient import TestClient
    store=Store(tmp_path/'test.db');initialize(store);job=enqueue(store,'KPIL')
    with store.connect() as db: db.execute("UPDATE pull_jobs SET status='partial' WHERE id=?",(job['id'],))
    with TestClient(create_app(tmp_path/'test.db')) as client:
        response=client.get('/api/pull-jobs/'+job['id']+'/events')
        assert response.status_code==200
        assert response.headers['content-type'].startswith('text/event-stream')
        assert 'partial' in response.text


@pytest.mark.parametrize('ticker',['deepakntr','kpil','infy','hdfcbank'])
def test_real_primary_period_excerpts(ticker):
    from pathlib import Path
    from finn.transcript_rag import reported_quarter
    doc=json.loads((Path(__file__).parent/'fixtures/day3'/f'{ticker}.json').read_text())
    assert reported_quarter(doc) is not None
    index=chunks(doc)
    assert index
    for item in index:
        c=item['citation']
        assert c['quote'] in next(p['text'] for p in doc['pages'] if p['page']==c['page'])


def test_live_refresh_with_saved_quarter_and_unavailable_providers(tmp_path,monkeypatch):
    store=Store(tmp_path/'test.db');doc=document();doc['pages'][0]['text']='Q1 FY2026\n'+doc['pages'][0]['text']
    store.raw(doc['url'],b'%PDF fixture');store.put('primary_sample','KPIL',doc)
    def unavailable(*args):raise ValueError('synthetic source outage')
    monkeypatch.setattr('finn.pull.fetch_screener',unavailable)
    monkeypatch.setattr('finn.pull.fetch_nse',unavailable)
    result=research('KPIL',store,force=True)
    assert result['sources']
    assert len(result['source_errors'])==2
    assert result['status']=='partial'


def test_delivered_ledger_excludes_future_periods():
    result=ledger([],[],['2026-12-31','2026-09-30'],'2026-10-31')
    assert result['observed_periods']==1
    assert result['ledger'][0]['period_end']=='2026-09-30'


def test_working_capital_unknown_profile_rejected():
    from finn.forensic_analyzer import working_capital_cycle
    with pytest.raises(ValueError):working_capital_cycle(None,None,None,'unknown')
