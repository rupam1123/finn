import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta,timezone

from fastapi.testclient import TestClient
from finn.main import create_app
from finn.storage import Store
from finn.pull_jobs import enqueue,initialize,get_job,run_one


def test_public_review_blocks_work_and_keeps_reads(tmp_path,monkeypatch):
    monkeypatch.setenv('FINN_PUBLIC_REVIEW','1')
    path=tmp_path/'review.sqlite3'
    with TestClient(create_app(path)) as client:
        assert client.get('/api/capabilities').json()=={'public_review':True,'research_jobs_enabled':False}
        assert client.get('/api/portfolio/overview').status_code==200
        for headers in [{},{'origin':'http://localhost:3000'},{'origin':'https://attacker.example'}]:
            assert client.post('/api/pull/INFY/jobs?refresh=true',headers=headers).status_code==403
        assert client.get('/api/pull/INFY/jobs').json()=={'active':None}
        assert client.get('/api/portfolio/overview').headers['cache-control']=='no-store'


def test_cross_site_job_request_and_wildcard_cors_rejected(tmp_path,monkeypatch):
    monkeypatch.setenv('FINN_PUBLIC_REVIEW','0');monkeypatch.setenv('FINN_ALLOWED_ORIGINS','*')
    with TestClient(create_app(tmp_path/'jobs.sqlite3')) as client:
        for headers in [{'origin':'https://attacker.example'},{'sec-fetch-site':'cross-site'}]:
            assert client.post('/api/pull/TCS/jobs',headers=headers).status_code==403
        response=client.post('/api/pull/TCS/jobs',headers={'origin':'http://localhost:3000'})
        assert response.status_code==202
        assert client.get('/api/portfolio',headers={'origin':'https://attacker.example'}).headers.get('access-control-allow-origin') is None


def test_job_budget_atomic_deduplicated_and_no_visitor_identifiers(tmp_path,monkeypatch):
    monkeypatch.setenv('FINN_PUBLIC_REVIEW','0')
    path=tmp_path/'budget.sqlite3'
    with TestClient(create_app(path)) as client:
        tickers=['TCS','INFY','RELIANCE','HDFCBANK','LT','TRENT','TITAN','CAMS','DIXON','POLYCAB']
        with ThreadPoolExecutor(max_workers=5) as pool:
            responses=list(pool.map(lambda ticker:client.post(f'/api/pull/{ticker}/jobs'),tickers))
        assert sum(r.status_code==202 for r in responses)==6
        assert all(r.status_code in {202,429} for r in responses)
        accepted=next(r.json() for r in responses if r.status_code==202)
        same=client.post(f'/api/pull/{accepted["symbol"]}/jobs?refresh=true')
        assert same.status_code==202 and same.json()['id']==accepted['id']
    with Store(path).connect() as db:
        assert db.execute('SELECT count(*) FROM api_job_budget').fetchone()[0]==6
        assert [r['name'] for r in db.execute('PRAGMA table_info(api_job_budget)')]==['requested_at']


def test_hour_budget_and_expiry(tmp_path,monkeypatch):
    monkeypatch.setenv('FINN_PUBLIC_REVIEW','0')
    path=tmp_path/'hour.sqlite3';app=create_app(path);store=Store(path)
    now=datetime.now(timezone.utc)
    with store.connect() as db:db.executemany('INSERT INTO api_job_budget VALUES(?)',[(now.isoformat(),)]*12)
    with TestClient(app) as client:
        assert client.post('/api/pull/TCS/jobs').status_code==429
        with store.connect() as db:db.execute('UPDATE api_job_budget SET requested_at=?',((now-timedelta(days=2)).isoformat(),))
        assert client.post('/api/pull/TCS/jobs').status_code==202
    with store.connect() as db:assert db.execute('SELECT count(*) FROM api_job_budget').fetchone()[0]==1


def test_worker_error_does_not_publish_exception_details(tmp_path,monkeypatch):
    store=Store(tmp_path/'error.sqlite3');initialize(store);job=enqueue(store,'TCS')
    def fail(*a,**kw):raise RuntimeError('DO-NOT-LEAK C:/private/key.env')
    monkeypatch.setattr('finn.pull_jobs.research',fail)
    run_one(store)
    result=get_job(store,job['id'])
    assert result['status']=='failed'
    assert 'DO-NOT-LEAK' not in json.dumps(result) and 'private' not in json.dumps(result)


def test_overview_uses_single_connection_and_never_decodes_pull(tmp_path,monkeypatch):
    path=tmp_path/'overview.sqlite3';app=create_app(path);store=Store(path)
    store.put('fundamentals','TCS',{'company_name':'Tata Consultancy Services'})
    # Availability must not require parsing a large/invalid research payload.
    with store.connect() as db:
        db.execute('INSERT INTO snapshots VALUES(?,?,?,?)',('pull','TCS',datetime.now(timezone.utc).isoformat(),'not JSON'))
    monkeypatch.setattr(Store,'get',lambda *a:(_ for _ in ()).throw(AssertionError('Snapshot decode is unnecessary here')))
    calls=[];connect=Store.connect
    def measured(self):calls.append(True);return connect(self)
    monkeypatch.setattr(Store,'connect',measured)
    with TestClient(app) as client:
        response=client.get('/api/portfolio/overview');assert response.status_code==200
        row=next(h for h in response.json()['holdings'] if h['symbol']=='TCS')
        assert row['name']=='Tata Consultancy Services' and row['research_available'] is True
        assert len(calls)==1
