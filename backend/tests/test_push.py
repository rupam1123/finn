"""Real primary-document fixtures; synthetic cases explicitly test faults/boundaries."""
import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import httpx
import pytest
from fastapi.testclient import TestClient
from finn.classifier import classify
from finn.cross_signal import alert_cutoff, signals
from finn.evidence import citation
from finn.main import create_app
from finn.management_enricher import enrich_management
from finn.model import Flash, ModelUnavailable
from finn.push import analysis_key, digest
from finn.push_ingest import process_filing
from finn.results_enricher import enrich_results, parse_statement
from finn.storage import Store
from finn.universe import CATEGORIES

FIXTURES = Path(__file__).parent / 'fixtures' / 'day2'
UTC = timezone.utc
NOW = datetime(2026, 10, 28, 8, tzinfo=UTC)

def real(symbol): return json.loads((FIXTURES/(symbol.lower()+'.json')).read_text(encoding='utf-8'))
def filing(**extra):
    return {'id':'f1','symbol':'TCS','title':'General Updates','description':'','source':'NSE',
            'published_at':(NOW-timedelta(hours=3)).isoformat(),'observed_at':(NOW-timedelta(hours=2)).isoformat(),
            'document_url':'https://nsearchives.nseindia.com/test.pdf','industry':'IT',**extra}
def synthetic_doc(text):
    return {'url':'https://nsearchives.nseindia.com/test.pdf','sha256':'a'*64,'fetched_at':NOW.isoformat(),
            'page_count':1,'status':'text_extracted','pages':[{'page':1,'text':text,'requires_visual_review':False}]}

def test_all_seventeen_categories_and_unknown_visible():
    assert len(CATEGORIES)==17
    r=classify(filing())
    assert r['category']=='unclassified' and r['review_required'] and not r['buried']

@pytest.mark.parametrize('critical',['auditor resignation','qualified opinion','fraud','default','financial results','appointment of Chief Executive','insolvency'])
def test_critical_content_overrides_routine(critical):
    r=classify(filing(title='Certificate under SEBI (Depositories and Participants) Regulations, 2018'),synthetic_doc('Certificate regarding securities. '*5+critical))
    assert r['critical_override'] and not r['buried'] and r['materiality']>=85

def test_routine_requires_complete_document():
    f=filing(title='Certificate under SEBI (Depositories and Participants) Regulations, 2018')
    d=synthetic_doc('The registrar confirms that securities received for dematerialisation were duly processed. '*2)
    assert classify(f,d)['buried'] and not classify(f)['buried']
    d['page_count']=2
    assert not classify(f,d)['buried']
    d['page_count']=1; d['pages'][0]['requires_visual_review']=True
    assert not classify(f,d)['buried']
    d['page_count']=1;d['status']='ocr_required'
    assert not classify(f,d)['buried']

class FakeModel:
    configured=True
    model='test-only'
    def __init__(self,value):self.value=value
    def generate(self,*args):return self.value,{'live':False}

@pytest.mark.parametrize('changes',[{'category':'invented'},{'materiality':101},{'materiality':True},{'confidence':1.2},{'page':77},{'quote':'Invented evidence absent from the source.'}])
def test_invalid_model_output_cannot_hide_filing(changes):
    quote='The company has disclosed material litigation involving a tax demand.'
    value={'category':'litigation','materiality':80,'confidence':.95,'reason':'Tax dispute','page':1,'quote':quote,**changes}
    r=classify(filing(),synthetic_doc(quote+' Please review the source.'),FakeModel(value))
    assert r['model_status']=='unavailable_or_invalid' and not r['buried']

def test_valid_model_low_score_stays_visible_and_critical_score_preserved():
    quote='The company reports a default under its credit agreement and requests review.'
    value={'category':'unclassified','materiality':1,'confidence':.4,'reason':'Uncertain','page':1,'quote':quote}
    r=classify(filing(),synthetic_doc(quote+' Additional source information.'),FakeModel(value))
    assert r['model_status']=='validated_output' and r['materiality']==85 and r['review_required'] and not r['buried']

def test_real_tcs_values_periods_basis_and_exact_math():
    d=real('tcs');r=enrich_results(d)
    assert r['status']=='partial' and r['basis']=='consolidated'
    assert r['periods']=={'current':'2026-09-30','previous_quarter':'2026-06-30','year_ago':'2025-09-30'}
    rows={x['metric']:x for x in r['rows']}
    assert rows['revenue']['values']=={'current':'73188','previous_quarter':'72275','year_ago':'65799'}
    assert rows['pbt']['values']['current']=='18638' and rows['pat']['values']['current']=='13934'
    assert rows['revenue']['qoq']['percent']==pytest.approx(913/72275*100)
    assert rows['revenue']['yoy']['percent']==pytest.approx(7389/65799*100)
    assert rows['ebitda']['values'] is None
    for row in r['rows']:
        if row['evidence']:
            e=row['evidence'];assert citation(d,e['page'],e['quote'])==e

@pytest.mark.parametrize('symbol,profile',[('hdfcbank','bank'),('infy','nonfinancial')])
def test_real_ambiguous_tables_abstain(symbol,profile):
    r=enrich_results(real(symbol),profile)
    assert r['status']=='review_required' and r['rows']==[] and r['parser_rejections']

@pytest.mark.parametrize('change',['unknown_unit','mixed_basis','mixed_currency','duplicate_year','ytd_only'])
def test_results_context_guards(change):
    d=real('tcs');p=copy.deepcopy(d['pages'][7])
    changes={'unknown_unit':('crore','units'),'mixed_basis':('TATA CONSULTANCY','Standalone TATA CONSULTANCY'),
             'mixed_currency':('(` crore)','(USD millions)'),'duplicate_year':('2025','2026'),
             'ytd_only':('Three months ended','Six months ended')}
    old,new=changes[change];p['text']=p['text'].replace(old,new)
    with pytest.raises(ValueError):parse_statement(d,p)

def test_results_malformed_grouping_and_lender_schema():
    d=real('tcs');p=d['pages'][7];p['text']=p['text'].replace('73,188','7318,8')
    assert parse_statement(d,p)['rows'][0]['values'] is None
    assert not {'revenue','ebitda'} & {r['metric'] for r in parse_statement(d,p,'bank')['rows']}

def test_real_management_event_and_issuer_profile():
    d=real('bajfinance');r=enrich_management(d);e,=r['events']
    assert r['status']=='source_extracted'
    assert (e['name'],e['role'],e['action'],e['effective_date'])==('Prashant Verma','Chief Information Security Officer (CISO)','reappointment','2027-02-01')
    assert e['profile']['source_type']=='issuer_statutory_brief_profile' and '21 years' in e['profile']['text']
    assert not e['profile']['independently_verified'] and citation(d,e['evidence']['page'],e['evidence']['quote'])==e['evidence']

def test_management_boilerplate_does_not_create_resignation():
    r=enrich_management(real('lt'));assert r['status']=='review_required' and not r['events']

def snapshot():
    bars=[{'date':(NOW.date()-timedelta(days=21-i)).isoformat(),'close':100.,'adjusted_close':100.,'volume':100.,'split':0} for i in range(21)]
    bars[-1].update(adjusted_close=104.,close=104.,volume=300)
    return {'fetched_at':NOW.isoformat(),'last_attempt':{'status':'unavailable'},'data':{'symbol':'TCS','fetched_at':NOW.isoformat(),'bars':bars,'source_url':'https://finance.yahoo.com/quote/TCS.NS/history/','sha256':'b'*64}}

def test_real_market_recalculation():
    d=json.loads((FIXTURES.parent/'reliability/tcs-market-newer.json').read_text())
    s={'data':d,'fetched_at':d['fetched_at'],'last_attempt':None}
    alerts=signals(s,[],NOW-timedelta(days=7),max(NOW,datetime.fromisoformat(d['fetched_at'])),.01,.01)
    assert alerts and alerts[-1]['source_url']==d['source_url']

def test_cross_signal_cutoffs_thresholds_retrospective_links():
    s=snapshot();cutoff=alert_cutoff(s['data']['bars'][-1]['date'])
    a=filing(id='before',published_at=(cutoff-timedelta(hours=1)).isoformat(),observed_at=(cutoff-timedelta(minutes=30)).isoformat())
    b=filing(id='after',published_at=(cutoff+timedelta(hours=1)).isoformat())
    c=filing(id='late_observed',published_at=(cutoff-timedelta(hours=1)).isoformat())
    future=filing(id='future',published_at=(NOW+timedelta(hours=1)).isoformat())
    r,=signals(s,[a,b,c,future],NOW-timedelta(days=1),NOW,4.,3.)
    assert r['price_triggered'] and not r['volume_triggered']
    assert [f['id'] for f in r['nearby_filings']]==['before']
    assert {f['id'] for f in r['retrospective_filings']}=={'after','late_observed'} and r['observation_mode']=='retrospective'
    s['data']['bars'][-1]['split']=2
    r,=signals(s,[],NOW-timedelta(days=1),NOW,3,2)
    assert not r['volume_triggered'] and r['indicators']['volume_ratio_20d'] is None

@pytest.mark.parametrize('price,volume',[(0,2),(-1,2),(float('nan'),2),(3,float('inf')),(3,0)])
def test_threshold_edge_cases(price,volume):
    with pytest.raises(ValueError):signals(snapshot(),[],NOW-timedelta(days=1),NOW,price,volume)

def test_cross_signal_unknown_snapshot_and_zero_volume():
    s=snapshot();assert signals(s,[],NOW-timedelta(days=2),NOW-timedelta(seconds=1))==[]
    for b in s['data']['bars']:b['volume']=0
    r,=signals(s,[],NOW-timedelta(days=1),NOW)
    assert r['indicators']['volume_ratio_20d'] is None and not r['volume_triggered']

def test_digest_counts_ranking_amendments_and_history(tmp_path):
    store=Store(tmp_path/'test.db');end=datetime.now(UTC)-timedelta(seconds=2)
    rows=[filing(id=str(i),published_at=(end-timedelta(hours=i+1)).isoformat()) for i in range(3)]
    store.add_filings(rows,end-timedelta(seconds=1));saved=store.filings('TCS',end-timedelta(days=1),end)
    for i,f in enumerate(saved):
        c=classify(f);c.update(buried=i==0,materiality=i*20)
        store.put('push_analysis',analysis_key(f),{'fetched_at':(end-timedelta(seconds=.5)).isoformat(),'filing_content_hash':f['content_hash'],'classification':c,'status':'processed'})
    r=digest(store,as_of=end,symbols=['TCS'])
    assert r['counts']['scanned']==3==r['counts']['surfaced']+r['counts']['buried'] and r['counts']['processed']==3
    assert [c['classification']['materiality'] for c in r['cards']]==[40,20]
    store.add_filings([{**rows[0],'description':'Auditor resignation'}],end+timedelta(seconds=.2))
    newer=digest(store,as_of=end+timedelta(seconds=.5),symbols=['TCS'])
    assert newer['counts']['scanned']==3 and newer['counts']['unprocessed']==1
    assert not next(c for c in newer['cards'] if c['id']=='0')['classification']['buried']
    assert digest(store,as_of=end,symbols=['TCS'])['counts']['buried']==1

@pytest.mark.parametrize('query',['window=2d','price_threshold=0','price_threshold=nan','vol_threshold=inf','as_of=2026-01-01','as_of=2999-01-01T00:00:00Z'])
def test_digest_api_rejects_invalid_inputs(tmp_path,query):
    with TestClient(create_app(tmp_path/'api.db')) as c:assert c.get('/api/push/digest?'+query).status_code==422

def test_empty_digest_coverage_not_false_no_events(tmp_path):
    with TestClient(create_app(tmp_path/'api.db')) as c:
        response=c.get('/api/push/digest');assert response.status_code==200;r=response.json()
        assert r['counts']['scanned']==0 and r['window']=='1d' and r['coverage']['TCS']['filings']['status']=='unavailable'
        assert r['status']=='cached_partial_coverage'

def test_pipeline_failure_keeps_last_good_and_timestamp(tmp_path,monkeypatch):
    store=Store(tmp_path/'pipeline.db');f=filing(content_hash='original',title='Financial results');doc=real('tcs')
    monkeypatch.setattr('finn.push_ingest.fetch_document',lambda *a:doc)
    assert process_filing(store,f)['status']=='processed'
    key=analysis_key(f);before=store.get('push_analysis',key);assert process_filing(store,f)['status']=='cached'
    def failure(*a):raise TimeoutError('synthetic upstream failure')
    monkeypatch.setattr('finn.push_ingest.fetch_document',failure)
    assert process_filing(store,f,force=True)['status']=='retained_previous'
    after=store.get('push_analysis',key)
    assert before['data']==after['data'] and before['fetched_at']==after['fetched_at'] and after['last_attempt']['status']=='unavailable'
    assert process_filing(store,f)['status']=='retained_previous'

def test_model_adapter_no_key_and_mock_transport_validation():
    with pytest.raises(ModelUnavailable):Flash(key='').generate('task',{}, {})
    requests=[]
    def handler(request):
        requests.append(request)
        return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'{"page":8}'}]}}],'usageMetadata':{'promptTokenCount':120}})
    with httpx.Client(transport=httpx.MockTransport(handler)) as c:r,u=Flash(c,key='test-only').generate('task',{}, {'type':'object'})
    assert r=={'page':8} and u['usage']['promptTokenCount']==120 and not u['live']
    assert 'test-only' not in str(requests[0].url) and requests[0].headers['x-goog-api-key']=='test-only'

@pytest.mark.parametrize('response',[httpx.Response(429),httpx.Response(200,text='not JSON'),httpx.Response(200,json={'candidates':[{'finishReason':'MAX_TOKENS'}]})])
def test_model_failure_explicit_redacted(response):
    with httpx.Client(transport=httpx.MockTransport(lambda r:response)) as c:
        with pytest.raises(ModelUnavailable) as exc:Flash(c,key='never-expose-me').generate('task',{}, {})
    assert 'never-expose-me' not in str(exc.value)

def test_real_resignation_links_name_role_and_effective_date():
    result=enrich_management(real('trent'));e,=result['events']
    assert (e['name'],e['role'],e['action'],e['effective_date'])==('Harish Bhat','Non-Executive Non-Independent Director','resignation','2026-10-17')
    assert e['profile'] is None

def test_failed_refresh_resurfaces_previously_buried_filing(tmp_path):
    store=Store(tmp_path/'review.db');end=datetime.now(UTC)-timedelta(seconds=2)
    f=filing(published_at=(end-timedelta(hours=1)).isoformat())
    store.add_filings([f],end-timedelta(seconds=1));f=store.filings('TCS',end-timedelta(days=1),end)[0]
    key=analysis_key(f);decision=classify(f);decision.update(buried=True,review_required=False)
    store.put('push_analysis',key,{'fetched_at':(end-timedelta(seconds=.5)).isoformat(),'filing_content_hash':f['content_hash'],'classification':decision,'status':'processed'})
    attempt=store.start_attempt('push_analysis',key);store.finish_attempt(attempt,'unavailable',error='synthetic failed refresh')
    result=digest(store,symbols=['TCS'])
    assert result['counts']['buried']==0 and result['counts']['surfaced']==1
    assert result['cards'][0]['classification']['review_required']

def test_pdf_engine_has_no_ml_runtime_import():
    import subprocess,sys
    r=subprocess.run([sys.executable,'-c','from finn.pdf_runtime import pymupdf; import sys; assert "onnxruntime" not in sys.modules; print(pymupdf.VersionBind)'],capture_output=True,text=True,check=True)
    assert r.stdout.strip().startswith('1.')

def test_real_exchange_null_industry_does_not_crash_pipeline(tmp_path,monkeypatch):
    store=Store(tmp_path/'nullable.db');f=filing(content_hash='null-industry',title='Financial results',industry=None)
    monkeypatch.setattr('finn.push_ingest.fetch_document',lambda *a:real('tcs'))
    assert process_filing(store,f)['status']=='processed'
    f.update(symbol='UNKNOWNISSUER',id='unseen',content_hash='unseen-industry')
    assert process_filing(store,f)['status']=='processed'
    e=store.get('push_analysis',analysis_key(f))['data']['enrichment']
    assert e['profile']=='unknown' and e['rows']==[]

def test_real_polycab_millions_convert_exactly_and_periods_align():
    r=enrich_results(real('polycab'));rows={x['metric']:x for x in r['rows']}
    assert r['basis']=='consolidated' and r['periods']['current']=='2026-09-30'
    assert rows['revenue']['source_unit']=='millions' and rows['revenue']['values']['current']=='9898.901'
    assert rows['pbt']['values']['current']=='1306.220' and rows['pat']['values']['current']=='989.997'
    assert rows['revenue']['qoq']['percent']==pytest.approx((98989.01-82097.32)/82097.32*100)
    assert rows['revenue']['half_year_reconciliation']=='passed'

def test_changed_numeric_cell_fails_independent_half_year_check():
    d=real('polycab');p=d['pages'][3];p['text']=p['text'].replace('98,989.01','98,989.91')
    r=parse_statement(d,p);row=r['rows'][0]
    assert row['status']=='reconciliation_failed' and row['values'] is None and row['qoq']['percent'] is None

def test_price_boundary_uses_decimal_inputs_not_float_roundoff():
    s=snapshot();s['data']['bars'][-1].update(adjusted_close=116.,close=116.,volume=200.)
    r,=signals(s,[],NOW-timedelta(days=1),NOW,16,2)
    assert r['price_triggered'] and not r['volume_triggered']
    assert signals(s,[],NOW-timedelta(days=1),NOW,16.000001,2)==[]

def test_evidence_route_serves_exact_immutable_pdf_not_other_raw_data(tmp_path):
    import hashlib
    store=Store(tmp_path/'evidence.db');body=(FIXTURES.parent/'reliability/astral-notice.pdf').read_bytes()
    digest_value=store.raw('https://nsearchives.nseindia.com/evidence.pdf',body)
    html_hash=store.raw('https://example.org/other',b'<html>not a PDF</html>')
    with TestClient(create_app(store.path)) as c:
        r=c.get('/api/evidence/'+digest_value+'.pdf')
        assert r.status_code==200 and r.content==body and hashlib.sha256(r.content).hexdigest()==digest_value
        assert 'immutable' in r.headers['cache-control'] and r.headers['x-content-type-options']=='nosniff'
        assert c.get('/api/evidence/'+html_hash+'.pdf').status_code==404
        assert c.get('/api/evidence/invalid.pdf').status_code==422
        with store.connect() as db:db.execute('UPDATE raw_responses SET body=? WHERE sha256=?',(b'%PDFcorrupt',digest_value))
        assert c.get('/api/evidence/'+digest_value+'.pdf').status_code==503

def test_historical_volume_coverage_is_explicit():
    from finn.cross_signal import signal_coverage
    c=signal_coverage(snapshot(),NOW-timedelta(days=30),NOW)
    assert c=={'saved_sessions_in_window':21,'price_evaluable_sessions':20,'volume_evaluable_sessions':1}
