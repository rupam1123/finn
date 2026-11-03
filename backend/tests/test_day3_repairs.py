"""Synthetic boundaries and captured-primary regressions for the Day 3 repair."""
import json
from pathlib import Path
import pytest
from finn.storage import Store
from finn.pull import research
from finn.classifier import classify
from finn.source_review import apply_source_review
from finn.say_do import analyze, evaluate, observations
from finn.results_enricher import enrich_results
from finn.transcript_context import management_roster


def transcript(label, text='', uri='a.pdf'):
    return {'kind':'transcript','url':'https://nsearchives.nseindia.com/'+uri,
            'sha256':'a'*64,'fetched_at':'2026-10-01T00:00:00+00:00','page_count':2,'status':'text_extracted',
            'pages':[{'page':1,'text':label+'\nMANAGEMENT: MR. JANE SMITH – CHIEF FINANCIAL OFFICER\nMODERATOR: MR. JOHN DOE – ANALYST', 'requires_visual_review':False},
                     {'page':2,'text':'Jane Smith:\n'+text,'requires_visual_review':False}]}


def stored(store, label, uri):
    d=transcript(label,uri=uri)
    d['sha256']=store.raw(d['url'],('%PDF synthetic fixture '+uri).encode())
    store.put('pull_document','INFY:'+d['sha256'],d)
    return d


def test_refresh_discovers_new_quarter_after_five_cached(tmp_path,monkeypatch):
    store=Store(tmp_path/'db.sqlite3')
    for i,label in enumerate(['Q1 FY2026','Q2 FY2026','Q3 FY2026','Q4 FY2026','Q1 FY2027']):stored(store,label,str(i)+'.pdf')
    new=transcript('Q2 FY2027',uri='new.pdf');new['sha256']=store.raw(new['url'],b'%PDF new synthetic fixture')
    monkeypatch.setattr('finn.pull.fetch_screener',lambda *a:{'documents':[{'kind':'transcript','url':new['url']}]})
    monkeypatch.setattr('finn.pull.fetch_nse',lambda *a:{'filings':[]})
    monkeypatch.setattr('finn.pull.fetch_annual_reports',lambda *a:[])
    called=[]
    monkeypatch.setattr('finn.pull.resolve_transcript',lambda url,*a:called.append(url) or new)
    monkeypatch.setattr('finn.pull.transcript_quality',lambda d:{'status':'transcript_candidate'})
    r=research('INFY',store,force=True)
    assert called==[new['url']]
    assert r['say_do']['ledger'][0]['period_end']=='Q2 FY2027'
    assert len(r['sources'])==6


def test_forced_refresh_revalidates_same_url(tmp_path,monkeypatch):
    store=Store(tmp_path/'db.sqlite3');old=stored(store,'Q1 FY2027','same.pdf')
    changed={**old,'sha256':store.raw(old['url'],b'%PDF changed synthetic fixture')}
    monkeypatch.setattr('finn.pull.fetch_screener',lambda *a:{'documents':[{'kind':'transcript','url':old['url']}]})
    monkeypatch.setattr('finn.pull.fetch_nse',lambda *a:{'filings':[]})
    monkeypatch.setattr('finn.pull.fetch_annual_reports',lambda *a:[])
    calls=[];monkeypatch.setattr('finn.pull.resolve_transcript',lambda url,*a:calls.append(url) or changed)
    monkeypatch.setattr('finn.pull.transcript_quality',lambda d:{'status':'transcript_candidate'})
    result=research('INFY',store,force=True)
    assert calls==[old['url']]
    assert {d['sha256'] for d in result['sources']}=={old['sha256'],changed['sha256']}


def test_category_review_preserves_independent_routine_gate():
    d=transcript('Routine','Dematerialization certificate confirms the routine processing of equity shares. '*3)
    d['pages']=d['pages'][1:];d['page_count']=1
    f={'title':'Dematerialization','description':'Routine certificate','content_hash':'revision'}
    decision=classify(f,d);assert decision['buried']
    review={'filing_content_hash':'revision','document_sha256':d['sha256'],'category':'unclassified',
            'scope':'primary_event_category','page':2,'quote':'Dematerialization certificate',
            'reason':'Confirmed event category','reviewed_at':'2026-10-02T00:00:00+00:00'}
    result=apply_source_review(decision,f,d,review)
    assert result['buried'] and not result['review_required']
    review['category']='results'
    assert not apply_source_review(decision,f,d,review)['buried']


def test_roles_and_basis_bound_to_primary_text():
    d=transcript('Q4 FY2026','All financial figures are on a consolidated basis. Our operating margin guidance for Q1 FY2027 is 20% to 22%.')
    facts=observations(d)
    assert facts[0]['speaker_verified'] and facts[0]['basis']=='consolidated'
    assert facts[0]['horizon_verified'] and len(facts[0]['context_citations'])==2
    assert 'janesmith' in management_roster(d)


def test_analyst_questions_cannot_become_management_actuals():
    g=observations(transcript('Q4 FY2026','Our consolidated operating margin guidance for Q1 FY2027 is 20% to 22%.'))[0]
    d=transcript('Q1 FY2027','Our consolidated operating margin for Q1 FY2027 was 21%.')
    d['pages'][1]['text']=d['pages'][1]['text'].replace('Jane Smith:','John Doe:')
    a=observations(d)[0]
    assert not a['speaker_verified']
    assert evaluate(g,a)['status']=='review_required'


@pytest.mark.parametrize('fault',[{'requires_visual_review':True},{'basis':'not_explicit'},{'horizon_verified':False},{'scope_verified':False}])
def test_comparison_abstains_on_either_side(fault):
    g=observations(transcript('Q4 FY2026','Our consolidated operating margin guidance for Q1 FY2027 is 20% to 22%.'))[0]
    a=observations(transcript('Q1 FY2027','Our consolidated operating margin for Q1 FY2027 was 21%.'))[0]
    assert evaluate(g,a)['status']=='within_target'
    assert evaluate(g,{**a,**fault})['status']=='review_required'
    assert evaluate({**g,**fault},a)['status']=='review_required'


def test_four_period_end_to_end_deterministic_ledger():
    labels=['Q4 FY2025','Q1 FY2026','Q2 FY2026','Q3 FY2026','Q4 FY2026']
    docs=[]
    for i,label in enumerate(labels):
        text=f'Our consolidated operating margin for {label} was 21%. '
        if i<4:text+=f'Our consolidated operating margin guidance for {labels[i+1]} is 20% to 22%.'
        docs.append(transcript(label,text,uri=str(i)+'.pdf'))
    result=analyze(docs)
    assert result['observed_periods']==4
    assert result['resolved_comparisons']==4
    assert all(r['comparisons'][0]['status']=='within_target' for r in result['ledger'])


def test_annual_guidance_does_not_become_quarterly_verdict():
    g=observations(transcript('Q4 FY2026','Our consolidated operating margin guidance for financial year 2027 is 20% to 22%.'))[0]
    a=observations(transcript('Q1 FY2027','Our consolidated operating margin for Q1 FY2027 was 21%.'))[0]
    assert evaluate(g,a)['status']=='not_comparable'


def test_three_column_statement_and_model_row_fallback():
    header='Consolidated financial results\nINR in crores\nThree months ended\n30.09.2026 30.06.2026 30.09.2025\n'
    rows=[('revenue','Revenue from operations','100 90 80'),('ebitda','EBITDA','20 18 16'),('pbt','PROFIT BEFORE TAX','15 13 12'),('pat','PROFIT FOR THE PERIOD','10 9 8')]
    text=header+'\n'.join(label+' '+values for _,label,values in rows)+'\nEPS\n1 1 1'
    d=transcript('irrelevant');d.update(page_count=1,pages=[{'page':1,'text':text,'requires_visual_review':False}])
    class Model:
        configured=True
        def generate(self,task,source,schema):
            if 'rows' not in schema['properties']:return {'page':1,'reason':'Located table'},{}
            return {'page':1,'rows':[{'metric':metric,'label':label,'quote':label+' '+values} for metric,label,values in rows]},{}
    result=enrich_results(d,model=Model())
    assert result['model_status']=='source_rows_validated'
    assert result['periods']['current']=='2026-09-30'
    assert result['rows'][0]['values']['current']=='100'
    assert result['rows'][0]['qoq']['percent']==pytest.approx(100/9)


def test_changed_model_quote_is_rejected():
    d=transcript('not a statement')
    class Model:
        configured=True
        def generate(self,*args):return {'page':2,'rows':[{'metric':'revenue','label':'Revenue from operations','quote':'Revenue from operations 900 800 700'}]*2},{}
    assert enrich_results(d,model=Model())['status']=='review_required'


def test_worker_forwards_explicit_refresh_and_model(tmp_path,monkeypatch):
    from finn.pull_jobs import initialize,enqueue,run_one,get_job
    store=Store(tmp_path/'queue.db');initialize(store)
    job=enqueue(store,'INFY',refresh=True);seen={};model=object()
    def execute(ticker,db,emit,**kwargs):
        seen.update(kwargs);return {'status':'partial'}
    monkeypatch.setattr('finn.pull_jobs.research',execute)
    assert run_one(store,model=model)
    assert seen=={'force':True,'model':model}
    assert get_job(store,job['id'])['status']=='partial'


def test_api_can_request_refresh_without_fetching(tmp_path,monkeypatch):
    from finn.main import create_app
    from fastapi.testclient import TestClient
    def forbidden(*a,**kw):pytest.fail('Enqueuing must not make a network request')
    monkeypatch.setattr('finn.pull_jobs.research',forbidden)
    path=tmp_path/'api.db'
    with TestClient(create_app(path)) as client:
        response=client.post('/api/pull/KPIL/jobs?refresh=true')
        assert response.status_code==202
        saved=client.get('/api/pull-jobs/'+response.json()['id']).json()
        assert saved['payload']['refresh'] is True


def test_missing_quarter_never_uses_an_older_call_as_adjacent():
    from finn.transcript_rag import quarter_evidence
    result=quarter_evidence([transcript('Q1 FY2026','We expect growth.'),transcript('Q3 FY2026','Our growth improved.')])
    assert result['ledger'][0]['said']==[]


def test_recent_exchange_candidate_precedes_old_issuer_archive():
    from finn.pull import candidate_date
    newer={'url':'https://nsearchives.nseindia.com/current.pdf','published_at':'2026-09-01T00:00:00+00:00'}
    older={'url':'https://www.infosys.com/2021/old.pdf','context':'Jan 2021 Transcript'}
    assert candidate_date(newer)>candidate_date(older)


def test_exchange_annual_report_discovery_retains_provenance():
    from finn.filings_ingest import fetch_annual_reports
    class Fetcher:
        def get(self,url,ttl):
            return {'body':json.dumps({'data':[
                {'toYr':'2026','fromYr':'2025','fileName':'https://nsearchives.nseindia.com/annual_reports/new.pdf','disseminationDateTime':'14-JUL-2026 21:22:39'},
                {'toYr':'2025','fromYr':'2024','fileName':'https://nsearchives.nseindia.com/annual_reports/old.zip'},
                {'toYr':'2024','fromYr':'2023','fileName':'https://127.0.0.1/unsafe.pdf'}]}).encode()}
    reports=fetch_annual_reports('INFY',Fetcher())
    assert len(reports)==1
    assert reports[0]['published_at']=='2026-07-14T15:52:39+00:00'
    assert reports[0]['discovery_url'].startswith('https://www.nseindia.com/api/annual-reports?')


def test_agm_transcript_is_not_an_earnings_call():
    from finn.pull import filing_document_kind
    assert filing_document_kind({'title':'Updates','description':'Transcript of Annual General Meeting','document_url':'https://nsearchives.nseindia.com/agm.pdf'}) is None
    assert filing_document_kind({'title':'Shareholders meeting','description':'Notice of Annual General Meeting','document_url':'https://nsearchives.nseindia.com/Integrated_Annual_Report_2026.pdf'})=='annual_report'


def test_new_routine_patterns_still_scan_for_critical_content():
    d=transcript('','This certificate confirms reconciliation of the dematerialization records. '*5)
    d['pages']=d['pages'][1:];d['page_count']=1
    f={'title':'Certificate under Regulation 74(5)','description':''}
    assert classify(f,d)['buried']
    d['pages'][0]['text']+=' A material fraud has been identified.'
    assert not classify(f,d)['buried']


def test_annual_section_cap_preserves_original_page_numbers():
    from finn.pdf_runtime import pymupdf
    from finn.documents import extract_document
    with pymupdf.open() as pdf:
        for i in range(6):pdf.new_page().insert_text((40,60),'Consolidated Cash Flow Statement' if i==5 else 'Cover or ordinary background text')
        body=pdf.tobytes()
    d=extract_document(body,'https://nsearchives.nseindia.com/annual.pdf',max_pages=2,section_mode=True)
    assert d['page_count']==6 and d['omitted_page_count']==4
    assert [p['page'] for p in d['pages']]==[1,6]
    assert d['extraction_scope']=='selected_primary_sections'
    with pytest.raises(ValueError):extract_document(body,d['url'],max_pages=2)


def test_research_refresh_preserves_last_good_staging_on_partial_tables(tmp_path,monkeypatch):
    store=Store(tmp_path/'db.sqlite3')
    store.put('fundamentals','INFY',{'documents':[],'company_name':'Last good'})
    monkeypatch.setattr('finn.pull.fetch_screener',lambda *a:{'documents':[],'company_name':'Partial','warnings':['Missing cash flow']})
    monkeypatch.setattr('finn.pull.fetch_nse',lambda *a:{'filings':[]})
    monkeypatch.setattr('finn.pull.fetch_annual_reports',lambda *a:[])
    result=research('INFY',store,force=True)
    assert store.get('fundamentals','INFY')['data']['company_name']=='Last good'
    assert store.last_attempt('fundamentals','INFY')['status']=='unavailable'
    assert any(e['stage']=='staging_tables' for e in result['source_errors'])


def test_synthesis_uses_primary_indices_and_rejects_invented_numbers():
    from finn.pull_reasoning import synthesize
    from finn.transcript_rag import chunks
    index=chunks(transcript('Q1 FY2027','Our revenue growth for the quarter was 20% year-on-year.'))
    class Model:
        def __init__(self,claim):self.claim=claim
        def generate(self,*args):return {'claims':[{'module':'trajectory','claim':self.claim,'source_indices':[0]}]}, {'live':False}
    result=synthesize(index,Model('Management reported revenue growth during the quarter.'))
    assert result['proposals'][0]['claims_verified'] is False
    with pytest.raises(ValueError):synthesize(index,Model('Management reported revenue growth of 999%.'))


def test_reasoning_model_is_separately_configurable(monkeypatch):
    from finn.model import Reasoner
    monkeypatch.setenv('FINN_REASONING_MODEL','gemini-2.5-pro')
    assert Reasoner(key='synthetic-test-only').model=='gemini-2.5-pro'


def test_nine_month_ytd_is_not_sum_of_two_quarters():
    from finn.results_enricher import parse_statement
    text='Consolidated financial results\nINR in crores\nThree months ended and nine months ended\n31.12.2026 30.09.2026 31.12.2025 31.12.2026 31.12.2025\nRevenue from operations\n100\n90\n80\n270\n230\nEBITDA\n20\n18\n16\n54\n46\nPROFIT BEFORE TAX\n15\n14\n12\n42\n34\nPROFIT FOR THE PERIOD\n10\n9\n8\n27\n23\nEPS\n1 1 1 1 1'
    d=transcript('fixture');d.update(page_count=1,pages=[{'page':1,'text':text,'requires_visual_review':False}])
    result=parse_statement(d,d['pages'][0])
    assert result['periods']['current']=='2026-12-31'
    assert result['rows'][0]['values']['current']=='100'
    assert result['rows'][0]['half_year_reconciliation']=='not_available'
