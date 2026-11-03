"""Continuation regressions. Synthetic providers never count as live validation."""
import copy
import hashlib
import importlib.util
import io
import json
import sqlite3
import sys
import threading
import zipfile
from pathlib import Path
from types import SimpleNamespace
import pytest
from finn.storage import Store
from test_final_day3 import image_doc,image_statement,transcript,bars


def load_script(name):
    path=Path(__file__).resolve().parents[2]/'scripts'/name
    spec=importlib.util.spec_from_file_location('finn_test_'+name.replace('.','_'),path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def zipped(entries):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,body in entries:archive.writestr(name,body)
    return stream.getvalue()


def primary_pdf(text='Synthetic primary statement for source retention. '):
    from finn.pdf_runtime import pymupdf
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((72,72),text*3)
        return pdf.tobytes()


def test_configured_model_and_processing_success_are_not_live_usage():
    from finn.validation import push_model_check,has_live_usage
    analysis={'status':'processed','model_name':'gemini-test','classification':{'category':'results','model_status':'not_configured'},'enrichment':{'status':'extracted'}}
    assert not push_model_check(analysis)['passed']
    analysis['classification']['usage']={'live':False}
    assert not has_live_usage(analysis)
    analysis['classification']['usage']['live']=True
    assert push_model_check(analysis)['passed']


def test_live_classifier_cannot_hide_failed_results_extraction():
    from finn.validation import push_model_check
    analysis={'status':'processed','classification':{'category':'results','model_status':'validated_output','usage':{'live':True}},'enrichment':{'status':'review_required','model_status':'image_extraction_unavailable_or_invalid'}}
    assert not push_model_check(analysis)['passed']
    analysis['enrichment']={'status':'partial','model_status':'image_rows_reconciled','usage':{'live':True}}
    assert push_model_check(analysis)['passed']


def test_preflight_deduplicates_shared_model_and_checks_both_tiers():
    from finn.validation import model_preflight
    calls=[]
    class Model:
        def __init__(self,name):self.model=name
        def generate(self,*args):calls.append(self.model);return {'ready':True},{'live':True}
    assert model_preflight([Model('gemini-flash-test'),Model('gemini-flash-test'),Model('gemini-reasoning-test')])['passed']
    assert calls==['gemini-flash-test','gemini-reasoning-test']


def test_preflight_rejects_mock_usage_and_inaccessible_reasoning():
    from finn.validation import model_preflight
    class Mock:
        model='gemini-test'
        def generate(self,*args):return {'ready':True},{'live':False}
    assert not model_preflight([Mock()])['passed']
    class Unavailable:
        model='gemini-reasoning-test'
        def generate(self,*args):raise RuntimeError('Synthetic HTTP 403')
    report=model_preflight([Unavailable()])
    assert not report['passed'] and '403' in report['models'][0]['error']


def test_current_default_preserves_explicit_model_settings(monkeypatch):
    from finn.model import Flash,Reasoner
    monkeypatch.delenv('FINN_FLASH_MODEL',raising=False);monkeypatch.delenv('FINN_REASONING_MODEL',raising=False)
    assert Flash().model==Reasoner().model=='gemini-3.8-flash'
    monkeypatch.setenv('FINN_FLASH_MODEL','gemini-legacy-test')
    assert Flash().model==Reasoner().model=='gemini-legacy-test'
    monkeypatch.setenv('FINN_REASONING_MODEL','gemini-reasoning-test')
    assert Reasoner().model=='gemini-reasoning-test'


def test_finalizer_missing_path_never_creates_empty_replacement(tmp_path,monkeypatch):
    db=tmp_path/'misspelled.sqlite3';out=tmp_path/'report'
    monkeypatch.setattr(sys,'argv',['finalize_day3.py','--db',str(db),'--out',str(out)])
    with pytest.raises(SystemExit) as stopped:load_script('finalize_day3.py').main()
    result=json.loads((out/'result.json').read_text())
    assert stopped.value.code==1 and not result['passed'] and not db.exists()
    assert result['checks'][0]['name']=='existing-database'


def test_finalizer_preserves_corrupt_database_and_reports_backup_failure(tmp_path,monkeypatch):
    db=tmp_path/'corrupt.sqlite3';db.write_bytes(b'not a database');out=tmp_path/'report'
    monkeypatch.setattr(sys,'argv',['finalize_day3.py','--db',str(db),'--out',str(out)])
    with pytest.raises(SystemExit):load_script('finalize_day3.py').main()
    assert db.read_bytes()==b'not a database'
    assert json.loads((out/'result.json').read_text())['checks'][0]['name']=='database-backup'


def test_build_failure_stops_before_ingestion_or_paid_extraction(tmp_path,monkeypatch):
    db=tmp_path/'existing.sqlite3';Store(db);out=tmp_path/'report';module=load_script('finalize_day3.py');calls=[]
    def run(command,**kwargs):calls.append(command);return SimpleNamespace(returncode=1)
    monkeypatch.setattr(module.subprocess,'run',run);monkeypatch.setattr(module.shutil,'which',lambda _:None)
    monkeypatch.setattr(sys,'argv',['finalize_day3.py','--db',str(db),'--out',str(out)])
    with pytest.raises(SystemExit):module.main()
    assert calls and all('finn.cli' not in cmd and 'finn.pull' not in cmd for cmd in calls)
    assert list(out.glob('database-before-validation-*.sqlite3'))


def test_model_opt_in_processes_full_push_without_repaying_for_sample(tmp_path,monkeypatch):
    import finn.validation
    db=tmp_path/'db.sqlite3';Store(db);out=tmp_path/'report';module=load_script('finalize_day3.py');calls=[]
    monkeypatch.setenv('GEMINI_API_KEY','private-test-key')
    monkeypatch.setattr(finn.validation,'model_preflight',lambda _: {'passed':True,'models':[]})
    monkeypatch.setattr(module.shutil,'which',lambda _:None)
    def run(command,**kwargs):calls.append(command);return SimpleNamespace(returncode=0)
    monkeypatch.setattr(module.subprocess,'run',run)
    class StreamedProcess:
        stdout=()
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def wait(self):return 0
    def popen(command,**kwargs):calls.append(command);return StreamedProcess()
    monkeypatch.setattr(module.subprocess,'Popen',popen)
    monkeypatch.setattr(sys,'argv',['finalize_day3.py','--db',str(db),'--out',str(out),'--skip-build','--use-model'])
    with pytest.raises(SystemExit):module.main()
    cmd=next(c for c in calls if 'finn.push_ingest' in c)
    assert '--use-model' in cmd and cmd[cmd.index('--workers')+1]=='1'


def test_review_zip_excludes_credentials_and_databases(tmp_path):
    from finn.validation import create_review_bundle
    (tmp_path/'result.json').write_text('{"passed":false}')
    (tmp_path/'.env').write_text('GEMINI_API_KEY=private-test-key')
    (tmp_path/'backup.sqlite3').write_bytes(b'private database')
    (tmp_path/'unrelated.json').write_text('{"private":true}')
    with zipfile.ZipFile(create_review_bundle(tmp_path)) as archive:assert set(archive.namelist())=={'result.json'}


def test_failed_rerun_archives_stale_success_and_old_review_zip(tmp_path,monkeypatch):
    out=tmp_path/'report';out.mkdir();(out/'acceptance.json').write_text('{"passed":true}')
    (out/'day3_verification.zip').write_bytes(b'old report')
    monkeypatch.setattr(sys,'argv',['finalize_day3.py','--db',str(tmp_path/'missing.sqlite3'),'--out',str(out)])
    with pytest.raises(SystemExit):load_script('finalize_day3.py').main()
    assert not (out/'acceptance.json').exists() and list((out/'previous-runs').glob('*/acceptance.json'))
    assert list((out/'previous-runs').glob('*/day3_verification.zip'))
    with zipfile.ZipFile(out/'day3_verification.zip') as archive:assert set(archive.namelist())=={'result.json'}


@pytest.mark.parametrize('entries',[
    [('a.pdf',b'%PDF-test'),('b.pdf',b'%PDF-test')],[('../a.pdf',b'%PDF-test')],
    [('a.pdf',b'not a PDF')],[('a.pdf',b'%PDF-'+b'0'*500000)],
    [(str(i)+'.pdf',b'%PDF-test') for i in range(11)]])
def test_malformed_or_ambiguous_archives_are_rejected(entries):
    from finn.documents import archive_pdf
    with pytest.raises(ValueError):archive_pdf(zipped(entries))


def test_archive_preserves_container_hash_and_immutable_pdf(tmp_path):
    import httpx
    from fastapi.testclient import TestClient
    from finn.documents import fetch_filing_document,container_matches
    from finn.transport import Fetcher
    from finn.push_ingest import saved_document
    from finn.main import create_app
    body=primary_pdf();archive=zipped([('filings/primary.pdf',body)])
    url='https://nsearchives.nseindia.com/corporate/synthetic-test.zip';store=Store(tmp_path/'archive.sqlite3')
    fetcher=Fetcher(store,client=httpx.Client(transport=httpx.MockTransport(lambda _:httpx.Response(200,content=archive))))
    try:doc=fetch_filing_document(url,fetcher)
    finally:fetcher.close()
    assert doc['sha256']==hashlib.sha256(body).hexdigest() and container_matches(doc,archive)
    assert doc['source_container']['sha256']==hashlib.sha256(archive).hexdigest()
    filing={'id':'synthetic-archive','document_url':url};store.put('filing_document',filing['id'],doc)
    assert saved_document(store,filing)['sha256']==doc['sha256']
    with TestClient(create_app(store.path)) as client:assert client.get('/api/evidence/'+doc['sha256']+'.pdf').content==body
    with store.connect() as db:db.execute('UPDATE raw_responses SET body=? WHERE sha256=?',(b'tampered archive',doc['source_container']['sha256']))
    with pytest.raises(ValueError,match='archive chain'):saved_document(store,filing)


def test_scanned_statement_rounding_uses_each_printed_cell():
    from finn.vision_results import validate
    statement=image_statement()
    for row in statement['rows']:row['cells']=[c if c=='-' else format(float(c),'.2f') for c in row['cells']]
    pat=next(r for r in statement['rows'] if r['metric']=='pat');pat['cells'][0]='25.01'
    validate(image_doc(),{'page':3,'image_sha256':'b'*64},statement,'nonfinancial')
    pat['cells'][0]='25.02'
    with pytest.raises(ValueError,match='PAT/tax reconciliation'):validate(image_doc(),{'page':3,'image_sha256':'b'*64},statement,'nonfinancial')


def test_quarter_and_annual_guidance_are_independent_revision_groups():
    from finn.say_do import analyze
    q=transcript('Q2 FY2026','Our consolidated operating margin guidance for Q4 FY2026 is 20% to 22%.')
    y=transcript('Q3 FY2026','Our consolidated operating margin guidance for FY2026 is 21% to 23%.')
    a=transcript('Q4 FY2026','Our consolidated operating margin for Q4 FY2026 was 21%. Our consolidated operating margin for FY2026 was 22%.')
    result=analyze([q,y,a])
    assert result['resolved_comparisons']==2
    assert {c['period'] for c in result['ledger'][0]['comparisons']}=={'Q4 FY2026','FY2026'}


def test_one_live_company_does_not_pass_four_company_gate(tmp_path):
    from finn.pull import VERSION
    module=load_script('verify_day3.py');store=Store(tmp_path/'acceptance.sqlite3')
    payload={'version':VERSION,'sources':[],'say_do':{'ledger':[]},'reasoning':[{'usage':{'live':True}}]}
    store.put('pull','INFY',payload);report=module.audit(store.path)
    assert not next(c for c in report['checks'] if c['name']=='Actual live model run recorded')['passed']
    for ticker in ('DEEPAKNTR','HDFCBANK','KPIL'):store.put('pull',ticker,payload)
    report=module.audit(store.path)
    assert next(c for c in report['checks'] if c['name']=='Actual live model run recorded')['passed']
    assert not report['passed']


def test_warm_cli_runs_all_23_with_bounded_workers_and_preserves_failures(tmp_path,monkeypatch):
    import finn.pull as pull
    from finn.universe import PORTFOLIO,SHOWCASE
    barrier=threading.Barrier(3,timeout=5);guard=threading.Lock();active=0;peak=0
    def research(ticker,store,emit,*args,**kwargs):
        nonlocal active,peak
        with guard:active+=1;peak=max(peak,active)
        try:
            if ticker in PORTFOLIO[:3]:barrier.wait()
            if ticker==SHOWCASE[-1]:raise ValueError('Synthetic single-company failure')
            value={'status':'partial','symbol':ticker,'sources':[]};store.put('pull',ticker,value);return value
        finally:
            with guard:active-=1
    monkeypatch.setattr(pull,'research',research);db=tmp_path/'warm.sqlite3';out=tmp_path/'warm.json'
    monkeypatch.setattr(sys,'argv',['pull','--warm','--db',str(db),'--output',str(out)])
    with pytest.raises(SystemExit) as stopped:pull.main()
    assert stopped.value.code==1 and len(json.loads(out.read_text()))==23 and peak==3
    with Store(db).connect() as connection:assert connection.execute("SELECT count(*) FROM snapshots WHERE kind='pull'").fetchone()[0]==22


def test_large_classifier_packet_is_literal_bounded_and_keeps_critical_scan():
    from finn.classifier import classify
    quote='The Board approved the quarterly financial results for September 2026.'
    pages=[{'page':i+1,'text':(quote+'\n' if i==0 else '')+'\n"quoted disclosure"\\text\n'*2500,'requires_visual_review':False} for i in range(5)]
    pages[-1]['text']+='\nThe auditor resignation requires disclosure.'
    doc={'url':'https://example.test/a.pdf','sha256':'a'*64,'fetched_at':'2026-10-31','status':'text_extracted','page_count':5,'pages':pages}
    class Model:
        configured=True
        def generate(self,task,source,schema):
            assert source['scope']=='selected_literal_spans' and len(json.dumps(source,ensure_ascii=False))<105000
            assert all(p['text'] in pages[p['page']-1]['text'] for p in source['pages'])
            return {'category':'results','materiality':40,'confidence':.99,'reason':'Synthetic classification','page':1,'quote':quote},{'live':False}
    result=classify({'title':'Financial Results','description':''},doc,Model())
    assert result['model_status']=='validated_output' and result['review_required'] and result['critical_override'] and result['materiality']>=85


def test_say_do_model_receives_roles_and_rejects_invented_numbers():
    from finn.pull_reasoning import audit_four_quarters
    g={'citation':{'url':'https://example.test/a.pdf','sha256':'a'*64,'page':1,'quote':'Our operating margin guidance is 20% to 22%.'},'speaker':'Jane Smith','speaker_verified':True}
    a={'citation':{'url':'https://example.test/b.pdf','sha256':'b'*64,'page':1,'quote':'Our operating margin for this quarter was 21%.'},'speaker':'Jane Smith','speaker_verified':True}
    ledger={'ledger':[{'period_end':'Q4 FY2026','said':[g],'delivered':[a]}]}
    class Model:
        assessment='The reported quarterly operating margin is 99%, which requires checking against its primary source.'
        def generate(self,task,source,schema):
            assert all(x['management_verified'] for x in source['source_context'])
            return {'comparisons':[{'period':'Q4 FY2026','metric':'operating_margin','assessment':self.assessment,'status':'numerical_candidate','guidance_source':0,'actual_source':1}]},{'live':False}
    model=Model()
    with pytest.raises(ValueError,match='numbers absent'):audit_four_quarters(ledger,model)
    model.assessment='The target is 20% to 22%; reported margin is 21%. Horizon alignment needs review.'
    assert audit_four_quarters(ledger,model)['comparisons'][0]['validation_status']=='semantic_review_required'


def test_previous_good_pdf_recovered_across_parser_versions_without_false_refresh(tmp_path,monkeypatch):
    from finn.push_ingest import process_filing
    from finn.push import analysis_key
    store=Store(tmp_path/'retained.sqlite3');url='https://nsearchives.nseindia.com/corporate/synthetic-previous.pdf'
    body=primary_pdf();digest=store.raw(url,body);observed='2026-10-20T00:00:00+00:00'
    with store.connect() as db:db.execute('UPDATE raw_responses SET fetched_at=? WHERE sha256=?',(observed,digest))
    store.raw(url,b'%PDF-truncated synthetic replacement')
    f={'id':'a'*64,'content_hash':'b'*64,'symbol':'HDFCBANK','title':'Financial Results','description':'','document_url':url}
    def broken(*args):raise ValueError('Synthetic truncated current download')
    monkeypatch.setattr('finn.push_ingest.fetch_document',broken)
    result=process_filing(store,f,force=True);saved=store.get('push_analysis',analysis_key(f))
    assert result['status']=='retained_previous' and saved['data']['document']['sha256']==digest
    assert saved['data']['document']['fetched_at']==observed and saved['data']['latest_source_refresh_ok'] is False
    assert saved['last_attempt']['status']=='unavailable' and not saved['data']['classification']['buried']
    before=saved['data']
    assert process_filing(store,f,force=True)['status']=='retained_previous'
    assert store.get('push_analysis',analysis_key(f))['data']==before


def test_prior_bytes_from_unapproved_host_are_not_accepted(tmp_path):
    from finn.push_ingest import retained_document
    store=Store(tmp_path/'unsafe.sqlite3');url='https://127.0.0.1/private.pdf';store.raw(url,primary_pdf())
    with pytest.raises(ValueError):retained_document(store,{'id':'unsafe','document_url':url})


def test_raw_cache_audit_reads_objects_lazily_from_read_only_sqlite(tmp_path):
    module=load_script('verify_day1.py');dbpath=tmp_path/'raw.sqlite3';store=Store(dbpath);digest=store.raw('https://example.test',b'primary bytes')
    connection=sqlite3.connect(dbpath.as_uri()+'?mode=ro',uri=True)
    try:
        raw=module.RawSources(connection);assert len(raw)==1 and digest in raw and raw[digest]==b'primary bytes'
        assert list(raw.items())==[(digest,b'primary bytes')]
        with pytest.raises(KeyError):raw['missing']
    finally:connection.close()


def test_exchange_repair_uses_exact_current_yahoo_hash_not_newest_url_row(tmp_path,monkeypatch):
    import pandas as pd
    import yfinance
    from finn.market_data import fetch_market
    data=bars();frame=pd.DataFrame({
        'Open':[b['open'] for b in data],'High':[b['high'] for b in data],'Low':[b['low'] for b in data],
        'Close':[b['close'] for b in data],'Adj Close':[b['adjusted_close'] for b in data],
        'Volume':[b['volume'] for b in data],'Dividends':[0.]*len(data),'Stock Splits':[0.]*len(data)},
        index=pd.DatetimeIndex([b['date'] for b in data],name='Date'))
    frame.iloc[-1,frame.columns.get_loc('Close')]=float('nan');frame.iloc[-1,frame.columns.get_loc('Adj Close')]=float('nan')
    store=Store(tmp_path/'market.sqlite3');url='https://finance.yahoo.com/quote/TCS.NS/history/'
    expected=store.raw(url,frame.to_json(orient='table').encode());misleading=store.raw(url,b'different later Yahoo response')
    monkeypatch.setattr(yfinance,'download',lambda *a,**kw:pd.concat({'TCS.NS':frame},axis=1))
    csv_text='TckrSymb,TradDt,SctySrs,Sgmt,OpnPric,HghPric,LwPric,ClsPric,TtlTradgVol,PrvsClsgPric\nTCS,2026-10-30,EQ,CM,101,104,100,103,1500,100\n'
    class Fetcher:
        def __init__(self,store):self.store=store
        def get(self,url,**kwargs):
            body=zipped([('market.csv',csv_text.encode())]) if 'BhavCopy' in url else b'[]'
            return {'url':url,'body':body,'sha256':self.store.raw(url,body),'fetched_at':'2026-10-30T20:00:00+00:00'}
        def close(self):pass
    monkeypatch.setattr('finn.nse_market.Fetcher',Fetcher)
    result=fetch_market(['TCS'],__import__('datetime').datetime(2026,10,30,20,tzinfo=__import__('datetime').timezone.utc),store,force=True,exchange_fallback=True)['TCS']
    assert result['status']=='ok' and result['input_provenance'][0]['sha256']==expected!=misleading


def test_source_audit_does_not_accept_self_consistent_but_forged_derived_history():
    module=load_script('verify_day1.py');raw={}
    def save(body):
        digest=hashlib.sha256(body).hexdigest();raw[digest]=body;return digest
    base={'open':100.,'high':104.,'low':99.,'close':100.,'adjusted_close':100.,'volume':1000.,'dividend':0.,'split':0.}
    history=[{'date':'2026-10-29',**base},{'date':'2026-10-30',**base,'close':103.,'adjusted_close':103.,'volume':1500.}]
    fields={'open':'Open','high':'High','low':'Low','close':'Close','adjusted_close':'Adj Close','volume':'Volume','dividend':'Dividends','split':'Stock Splits'}
    yahoo=save(json.dumps({'data':[{'Date':b['date'],**{v:b[k] for k,v in fields.items()}} for b in history[:-1]]}).encode())
    csv_text='TckrSymb,TradDt,SctySrs,Sgmt,OpnPric,HghPric,LwPric,ClsPric,TtlTradgVol,PrvsClsgPric\nTCS,2026-10-30,EQ,CM,100,104,99,103,1500,100\n'
    bhav=save(zipped([('market.csv',csv_text.encode())]));actions=save(b'[]')
    data={'symbol':'TCS','bars':copy.deepcopy(history),'indicator_history':copy.deepcopy(history),'input_provenance':[
        {'url':'https://finance.yahoo.com/quote/TCS.NS/history/','sha256':yahoo},
        {'url':'https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_test.csv.zip','sha256':bhav},
        {'url':'https://www.nseindia.com/api/corporates-corporateActions?index=equities','sha256':actions}]}
    def seal():data['sha256']=save(json.dumps({'bars':data['indicator_history'],'inputs':[bhav,data['input_provenance'][2]['sha256']]}).encode())
    seal();assert module.source_alignment(data,raw)
    data['bars'][0]['open']=101.;data['indicator_history'][0]['open']=101.;seal()
    assert not module.source_alignment(data,raw)


@pytest.mark.parametrize('ticker',['TRENT','SUNPHARMA','PERSISTENT'])
def test_real_captured_archives_replay_with_hash_and_ocr_status(ticker):
    from finn.documents import archive_pdf,extract_document,container_matches
    folder=Path(__file__).parent/'fixtures/day3/archives';source=json.loads((folder/'sources.json').read_text())[ticker]
    archive=(folder/(ticker.lower()+'.zip')).read_bytes();entry,body=archive_pdf(archive)
    assert hashlib.sha256(archive).hexdigest()==source['source_container']['sha256']
    doc=extract_document(body,source['source_container']['url']);doc.update(sha256=hashlib.sha256(body).hexdigest(),source_container=source['source_container'])
    assert container_matches(doc,archive) and entry==source['source_container']['entry']
    assert doc['status']==source['status'] and doc['page_count']==source['pages']
    if ticker=='SUNPHARMA':assert doc['status']=='ocr_required'


@pytest.mark.parametrize('marker',['Analyst:','Analyst'])
def test_anonymous_analyst_turn_cannot_inherit_management_identity(marker):
    from finn.say_do import observations,analyze
    guide=transcript('Q2 FY2026','We will take questions.\nModerator:\nNext question.\n'+marker+'\nOur consolidated operating margin guidance for Q4 FY2026 is 20% to 22%.')
    actual=transcript('Q4 FY2026','Our consolidated operating margin for Q4 FY2026 was 21%.')
    facts=observations(guide)
    assert facts and all(not x['speaker_verified'] for x in facts)
    assert analyze([guide,actual])['resolved_comparisons']==0

