import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import httpx
import pytest
from finn.model import Flash,ModelUnavailable
from finn.model_limits import RequestPacer,QuotaUnavailable,retry_metadata
from finn.storage import Store


def test_shared_model_pacer_reserves_five_second_slots_at_twelve_rpm():
    now=[0.0];waits=[]
    def sleep(seconds):waits.append(seconds);now[0]+=seconds
    gate=RequestPacer(clock=lambda:now[0],sleep=sleep)
    for _ in range(4):gate.wait('same-model',12)
    assert waits==[5,5,5]
    gate.wait('different-model',12)
    assert waits==[5,5,5]
    gate.block('same-model','quota exhausted')
    with pytest.raises(QuotaUnavailable,match='quota exhausted'):gate.wait('same-model',12)


@pytest.mark.parametrize('value',['0','-1','nan','inf','not-a-number'])
def test_invalid_pacing_never_starts_provider_request(value,monkeypatch):
    monkeypatch.setenv('FINN_MODEL_RPM',value)
    with pytest.raises(ValueError):Flash(key='synthetic-test-key')


def test_retry_metadata_keeps_only_allowlisted_quota_fields():
    value={'error':{'message':'SECRET MUST NOT LEAK','details':[
        {'@type':'type.googleapis.com/google.rpc.RetryInfo','retryDelay':'61.5s'},
        {'@type':'type.googleapis.com/google.rpc.QuotaFailure','violations':[
            {'quotaId':'GenerateRequestsPerMinutePerProjectPerModel','subject':'SECRET PROJECT'},
            {'quotaId':'ARBITRARY SECRET'}]}]}}
    result=retry_metadata(json.dumps(value),default=2)
    assert result=={'delay':61.5,'daily':False,'quota_ids':['GenerateRequestsPerMinutePerProjectPerModel']}
    assert 'SECRET' not in str(result)


def test_retry_after_http_date_is_honored():
    from datetime import datetime,timedelta,timezone
    from email.utils import format_datetime
    header=format_datetime(datetime.now(timezone.utc)+timedelta(seconds=90),usegmt=True)
    assert 88 <= retry_metadata(b'',header)['delay'] <= 90


def test_daily_quota_is_explicit_without_retries_or_key_disclosure(monkeypatch):
    calls=[];waits=[];monkeypatch.setattr('finn.model.time.sleep',waits.append)
    def handler(request):
        calls.append(request)
        return httpx.Response(429,json={'error':{'message':'synthetic-private-key','details':[
            {'@type':'type.googleapis.com/google.rpc.QuotaFailure','violations':[
                {'quotaId':'GenerateRequestsPerDayPerProjectPerModel-FreeTier'}]}]}})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ModelUnavailable,match='daily request quota exhausted') as stopped:
            Flash(client,key='synthetic-private-key').generate('ready',{}, {'type':'object'})
    assert len(calls)==1 and waits==[] and 'synthetic-private-key' not in str(stopped.value)


def test_provider_retry_delay_then_success(monkeypatch):
    calls=[];waits=[];monkeypatch.setattr('finn.model.time.sleep',waits.append)
    def handler(request):
        calls.append(request)
        if len(calls)==1:return httpx.Response(429,json={'error':{'details':[
            {'@type':'type.googleapis.com/google.rpc.RetryInfo','retryDelay':'62s'}]}})
        return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'{"ready":true}'}]}}]})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        value,_=Flash(client,key='synthetic-test-key').generate('ready',{}, {'type':'object'})
    assert value=={'ready':True} and waits==[62.0] and len(calls)==2


def test_failed_opt_in_preflight_stops_before_database_or_subprocess_work(tmp_path,monkeypatch):
    import finn.validation
    path=Path(__file__).resolve().parents[2]/'scripts/finalize_day3.py'
    spec=importlib.util.spec_from_file_location('quota_finalizer_test',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    db=tmp_path/'existing.sqlite3';Store(db);before=db.read_bytes();out=tmp_path/'out'
    monkeypatch.setenv('GEMINI_API_KEY','synthetic-test-key')
    monkeypatch.setattr(finn.validation,'model_preflight',lambda models:{'passed':False,'models':[{'error':'Gemini returned HTTP 429'}]})
    def forbidden(*args,**kwargs):raise AssertionError('Failed preflight must not run ingestion, tests, build or model-free replacement')
    monkeypatch.setattr(module.subprocess,'run',forbidden);monkeypatch.setattr(module.subprocess,'Popen',forbidden)
    monkeypatch.setattr(sys,'argv',['finalize_day3.py','--db',str(db),'--out',str(out),'--use-model'])
    with pytest.raises(SystemExit) as stopped:module.main()
    assert stopped.value.code==1 and db.read_bytes()==before and not list(out.glob('*.sqlite3'))
    report=json.loads((out/'result.json').read_text())
    assert report['checks']==[{'name':'model-preflight','exit_code':1}]
    assert report['passed'] is False


def test_live_default_flash_and_reasoner_share_the_same_request_gate(monkeypatch):
    import finn.model as module
    now=[0.0];waits=[]
    def sleep(seconds):waits.append(seconds);now[0]+=seconds
    gate=RequestPacer(clock=lambda:now[0],sleep=sleep)
    original_client=httpx.Client
    def client_factory(**kwargs):
        return original_client(transport=httpx.MockTransport(lambda request:httpx.Response(200,json={
            'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'{"ready":true}'}]}}]})))
    monkeypatch.setenv('FINN_FLASH_MODEL','gemini-3.5-flash-lite');monkeypatch.setenv('FINN_REASONING_MODEL','gemini-3.5-flash-lite');monkeypatch.setenv('FINN_MODEL_RPM','12')
    monkeypatch.setattr(module,'PACER',gate);monkeypatch.setattr(module.httpx,'Client',client_factory)
    for model in [module.Flash(key='synthetic-test-key'),module.Reasoner(key='synthetic-test-key')]:
        assert model.generate('ready',{}, {'type':'object'})[0]=={'ready':True}
    assert waits==[5]


def test_provider_delay_above_budget_does_not_retry_early(monkeypatch):
    waits=[];calls=[];monkeypatch.setattr('finn.model.time.sleep',waits.append)
    def handler(request):calls.append(request);return httpx.Response(429,headers={'retry-after':'1200'})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ModelUnavailable,match='exceeds automatic wait budget'):
            Flash(client,key='synthetic-test-key').generate('ready',{}, {'type':'object'})
    assert waits==[] and len(calls)==1
