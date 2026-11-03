from fastapi.testclient import TestClient
from finn.main import create_app
from finn.storage import Store
from finn.universe import PORTFOLIO


def test_universe_exact_prefix_typo_and_empty(tmp_path):
    store = Store(tmp_path / 'cache.sqlite3')
    store.put('universe', 'NSE', {'companies': [
        {'symbol': 'INFY', 'company_name': 'Infosys Limited'},
        {'symbol': 'HCL-INSYS', 'company_name': 'HCL Infosystems Limited'},
        {'symbol': 'TCS', 'company_name': 'Tata Consultancy Services Limited'},
        {'symbol': 'TITAN', 'company_name': 'Titan Company Limited'}]})
    api = TestClient(create_app(store.path))
    assert api.get('/api/universe?q=infy').json()['matches'][0]['symbol'] == 'INFY'
    assert api.get('/api/universe?q=infosys').json()['matches'][0]['symbol'] == 'INFY'
    assert api.get('/api/universe?q=infosy').json()['matches'][0]['symbol'] == 'INFY'
    assert not api.get('/api/universe?q=zzzzzzzzzzzz').json()['matches']
    assert api.get('/api/universe?q=').json()['total'] == 4
    assert api.get('/api/universe?q='+'a'*61).status_code == 422


def test_overview_uses_saved_snapshots_only(tmp_path, monkeypatch):
    import httpx
    def forbidden(*args, **kwargs):
        raise AssertionError('A read-only overview must not fetch sources')
    monkeypatch.setattr(httpx.HTTPTransport, 'handle_request', forbidden)
    store = Store(tmp_path / 'cache.sqlite3')
    ticker = PORTFOLIO[0]
    market = {'symbol': ticker, 'indicators': {'as_of': '2026-10-30', 'return_1d_pct': None}}
    store.put('market', ticker, market)
    store.put('fundamentals', ticker, {'company_name': 'Issuer from saved staging'})
    store.put('pull', ticker, {'status': 'partial'})
    api = TestClient(create_app(store.path))
    response = api.get('/api/portfolio/overview')
    assert response.status_code == 200
    result = response.json()
    assert [row['symbol'] for row in result['holdings']] == PORTFOLIO
    row = result['holdings'][0]
    assert {k:v for k,v in row['market'].items() if k!='freshness'} == market and row['research_available']
    assert row['market']['freshness']['actual_session'] == market['indicators']['as_of']
    assert row['name'] == 'Issuer from saved staging'
    assert row['filing_count'] == 0
    assert result['holdings'][1]['market'] is None
    assert not result['holdings'][1]['research_available']
    assert result['mode'] == 'saved_snapshots'


def test_active_job_is_resumable_and_symbol_scoped(tmp_path):
    api = TestClient(create_app(tmp_path / 'jobs.sqlite3'))
    assert api.get('/api/pull/INFY/jobs').json() == {'active': None}
    job = api.post('/api/pull/INFY/jobs').json()
    assert api.get('/api/pull/INFY/jobs').json()['active']['id'] == job['id']
    assert api.get('/api/pull/TCS/jobs').json()['active'] is None
    assert api.post('/api/pull/INFY/jobs').json()['id'] == job['id']
