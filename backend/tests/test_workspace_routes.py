"""Read-only detail, temporal coverage and accounting proof regressions."""
import hashlib
from datetime import datetime,timezone
from fastapi.testclient import TestClient
from finn.main import create_app
from finn.storage import Store
from finn.transcript_rag import quarter_evidence
from finn.workspace_projection import consecutive_ledger
from test_day3_repairs import transcript


def test_consecutive_coverage_does_not_count_older_transcripts():
    value=quarter_evidence([transcript(p) for p in ['Q2 FY2027','Q4 FY2026','Q3 FY2026','Q2 FY2026']])
    assert value['observed_periods']==3 and value['missing_quarters']==1
    assert [r['period_end'] for r in value['ledger']]==['Q2 FY2027','Q1 FY2027','Q4 FY2026','Q3 FY2026']
    assert value['ledger'][1]['coverage_status']=='missing_transcript'
    assert not value['ledger'][0]['said']


def test_legacy_projection_keeps_gap_and_verdicts():
    value=consecutive_ledger({'ledger':[{'period_end':p,'comparisons':[]} for p in ['Q2 FY2027','Q4 FY2026','Q3 FY2026','Q2 FY2026']]})
    assert value['observed_periods']==3
    assert value['ledger'][1]['status']=='missing_transcript'
    assert value['resolved_comparisons']==0


def test_calendar_coverage_rolls_year_without_fiscal_assumption():
    docs=[{**transcript('Quarter ended March 31, 2026')},{**transcript('Quarter ended September 30, 2025')}]
    value=quarter_evidence(docs)
    assert [r['period_end'] for r in value['ledger']]==['2026-03-31','2025-12-31','2025-09-30','2025-06-30']
    assert value['observed_periods']==2


def test_metadata_resolves_quote_identity_without_exposing_raw_input(tmp_path,monkeypatch):
    monkeypatch.setenv('FINN_PUBLIC_REVIEW','1');store=Store(tmp_path/'db');body=b'%PDF synthetic isolated fixture';digest=store.raw('https://www.tcs.com/a.pdf',body)
    quote='Exact source excerpt with private query characters ? & #.';qid=hashlib.sha256(quote.encode()).hexdigest()
    citation={'sha256':digest,'url':'https://www.tcs.com/a.pdf','page':7,'quote':quote}
    store.put('pull','TCS',{'say_do':{},'sources':[],'modules':{'test':{'citation':citation}}})
    with TestClient(create_app(tmp_path/'db')) as client:
        response=client.get(f'/api/evidence/{digest}/metadata',params={'page':7,'quote_id':qid})
        assert response.status_code==200 and all(response.json()['citation'][k]==v for k,v in citation.items())
        assert client.get(f'/api/evidence/{digest}/metadata',params={'page':8,'quote_id':qid}).status_code==404
        assert client.get('/api/evidence/not-a-hash/metadata').status_code==422
        assert client.post('/api/pull/TCS/jobs').status_code==403
        assert client.get(f'/api/evidence/{digest}.pdf').content==body
    with store.connect() as db:assert db.execute('SELECT count(*) FROM pull_jobs').fetchone()[0]==0


def test_filing_detail_latest_revision_by_observation(tmp_path):
    store=Store(tmp_path/'db')
    filing={'id':'a'*64,'symbol':'TCS','title':'Financial results','description':'Results','published_at':'2026-10-01T10:00:00+00:00','document_url':'https://www.tcs.com/a.pdf'}
    store.add_filings([filing],observed_at='2026-10-02T10:00:00+00:00')
    store.add_filings([{**filing,'title':'Corrected financial results'}],observed_at='2026-10-03T10:00:00+00:00')
    with TestClient(create_app(tmp_path/'db')) as client:
        historical=client.get('/api/push/filing/'+'a'*64,params={'as_of':'2026-10-02T12:00:00+00:00'})
        assert historical.status_code==200 and historical.json()['card']['title']=='Financial results'
        assert client.get('/api/push/filing/'+'a'*64).json()['card']['title']=='Corrected financial results'
        assert client.get('/api/push/filing/invalid').status_code==422
        assert client.get('/api/push/filing/'+'b'*64).status_code==404
        assert client.get('/api/push/alert/TCS:2026-99-01').status_code==422


def test_returned_quote_id_is_stable_and_not_quote_text():
    from finn.workspace_api import annotate_quotes
    citation={'sha256':'a'*64,'page':3,'quote':'Verbatim primary text.'}
    value=annotate_quotes({'nested':[citation]})
    assert value['nested'][0]['quote_id']==hashlib.sha256(citation['quote'].encode()).hexdigest()



def test_encoded_alert_id_and_prior_twenty_baseline(tmp_path):
    from datetime import date,timedelta
    store=Store(tmp_path/'db');bars=[]
    for i in range(30):
        bars.append({'date':(date(2026,9,1)+timedelta(days=i)).isoformat(),'adjusted_close':100 if i<29 else 110,'close':100 if i<29 else 110,'volume':100 if i<29 else 1000})
    store.put('market','TCS',{'symbol':'TCS','bars':bars,'fetched_at':'2026-10-01T00:00:00+00:00','source_url':'https://finance.yahoo.com/quote/TCS.NS/','sha256':'a'*64})
    with TestClient(create_app(tmp_path/'db')) as client:
        response=client.get('/api/push/alert/TCS%253A2026-09-30')
        assert response.status_code==200
        result=response.json()
        assert len(result['volume_baseline'])==21
        assert [b['volume'] for b in result['volume_baseline'][:-1]]==[100]*20
        assert result['alert']['indicators']['volume_ratio_20d']==10
        assert result['alert']['observation_mode']=='retrospective'


def test_captured_primary_results_retains_reconciliation_proof():
    from test_push import real
    from finn.results_enricher import enrich_results
    from decimal import Decimal
    result=enrich_results(real('tcs'))
    rows=[r for r in result['rows'] if r.get('values')]
    assert rows
    for row in rows:
        assert Decimal(row['normalization_factor'])>0
        proof=row['reconciliation_proof']
        if proof:
            assert Decimal(proof['current_raw'])+Decimal(proof['previous_quarter_raw'])==Decimal(proof['calculated_half_year_raw'])
            assert abs(Decimal(proof['calculated_half_year_raw'])-Decimal(proof['half_year_raw']))<=Decimal(proof['tolerance_raw'])
