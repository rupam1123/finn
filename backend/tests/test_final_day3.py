"""Final Day 1–3 boundaries; synthetic fixtures never count as live evidence."""
import copy,csv,io,json,zipfile
from datetime import datetime,timezone
from pathlib import Path
import pytest
from finn.nse_market import parse_bhavcopy,reconcile
from finn.vision_results import validate
from finn.say_do import observations,evaluate,analyze
from finn.management_enricher import EventCandidate,validate_event
from finn.storage import Store
from finn.push import digest


def bars():
    from datetime import date,timedelta
    end=date(2026,10,30)
    return [{'date':(end-timedelta(days=30-i)).isoformat(),'open':100.,'high':102.,'low':99.,'close':100.,'adjusted_close':100.,'volume':1000,'split':0} for i in range(31)]


def test_exchange_reconciliation_checks_all_boundaries():
    data=bars();data[-1]['close']=float('nan');data[-1]['adjusted_close']=float('nan')
    ex={'date':'2026-10-30','open':101.,'high':104.,'low':100.,'close':103.,'volume':1500,'previous_close':100.}
    result=reconcile(data,'TCS','2026-10-30',ex,[])
    assert result[-1]['close']==result[-1]['adjusted_close']==103.
    assert data[-1]['close']!=data[-1]['close']
    with pytest.raises(ValueError):reconcile(data,'TCS','2026-10-30',{**ex,'previous_close':98.},[])
    with pytest.raises(ValueError):reconcile(data,'TCS','2026-10-30',ex,[{'symbol':'TCS','exDate':'30-Oct-2026'}])
    data[-2]['adjusted_close']=98.
    with pytest.raises(ValueError):reconcile(data,'TCS','2026-10-30',ex,[])


def image_statement():
    values={'revenue':['100','90','80'],'other_income':['5','4','3'],'total_income':['105','94','83'],
            'total_expenses':['70','65','60'],'pbt_before_exception':['35','29','23'],
            'exceptional_items':['-','-','-'],'pbt':['35','29','23'],'tax':['10','9','8'],'pat':['25','20','15']}
    return {'is_statement':True,'basis':'consolidated','currency':'INR','unit':'crores',
            'periods':['2026-09-30','2026-06-30','2025-09-30'],'header_transcription':'Consolidated INR crores: quarter ended',
            'rows':[{'metric':k,'label':k.replace('_',' '),'cells':v} for k,v in values.items()]}


def image_doc():return {'url':'https://example.test/results.pdf','sha256':'a'*64,'fetched_at':'2026-10-30T00:00:00+00:00'}


def test_image_results_have_explicit_image_evidence_and_reconcile():
    result=validate(image_doc(),{'page':3,'image_sha256':'b'*64},image_statement(),'nonfinancial')
    assert result['rows'][0]['values']['current']=='100'
    assert result['rows'][0]['evidence']['evidence_type']=='page_image'
    assert result['rows'][1]['values'] is None # EBITDA is not invented.
    changed=image_statement();changed['rows'][0]['cells'][0]='200'
    with pytest.raises(ValueError):validate(image_doc(),{'page':3,'image_sha256':'b'*64},changed,'nonfinancial')


def test_image_tax_components_are_summed_only_when_both_are_printed():
    item=image_statement();item['rows']=[r for r in item['rows'] if r['metric']!='tax']
    item['rows'] += [{'metric':'current_tax','label':'Current tax','cells':['12','11','10']},
                     {'metric':'deferred_tax','label':'Deferred tax','cells':['(2)','(2)','(2)']}]
    result=validate(image_doc(),{'page':3,'image_sha256':'b'*64},item,'nonfinancial')
    assert result['reconciliation_method']['tax']=='sum_of_printed_current_and_deferred_tax'
    assert result['reconciliation_inputs'][-1]['cells']==['(2)','(2)','(2)']
    item['rows'].pop()
    with pytest.raises(ValueError,match='reconciliation rows'):validate(image_doc(),{'page':3,'image_sha256':'b'*64},item,'nonfinancial')


def test_unprinted_exceptional_cells_remain_null_and_need_direct_pbt_identity():
    item=image_statement();by_metric={r['metric']:r for r in item['rows']}
    by_metric['exceptional_items']['cells']=[None,None,None]
    result=validate(image_doc(),{'page':3,'image_sha256':'b'*64},item,'nonfinancial')
    raw=next(r for r in result['reconciliation_inputs'] if r['metric']=='exceptional_items')
    assert raw['cells']==[None,None,None]
    by_metric['pbt']['cells'][0]='37';by_metric['pat']['cells'][0]='27'
    with pytest.raises(ValueError,match='Unextracted exceptional items'):validate(image_doc(),{'page':3,'image_sha256':'b'*64},item,'nonfinancial')


@pytest.mark.parametrize('sign',['+','-'])
def test_image_exceptional_items_follow_explicit_printed_pbt_formula(sign):
    item=image_statement();by_metric={r['metric']:r for r in item['rows']}
    by_metric['exceptional_items']['cells']=['2','2','2']
    by_metric['pbt']['label']='Profit before tax (5'+sign+'6)'
    by_metric['pbt']['cells']=['37','31','25'] if sign=='+' else ['33','27','21']
    by_metric['pat']['cells']=['27','22','17'] if sign=='+' else ['23','18','13']
    result=validate(image_doc(),{'page':3,'image_sha256':'b'*64},item,'nonfinancial')
    assert result['reconciliation_method']['exceptional_items_sign']==(1 if sign=='+' else -1)
    by_metric['pbt']['label']='Profit before tax'
    with pytest.raises(ValueError,match='explicit printed PBT formula'):validate(image_doc(),{'page':3,'image_sha256':'b'*64},item,'nonfinancial')


@pytest.mark.parametrize('field,value',[('currency','USD'),('unit','unknown'),('basis','unknown')])
def test_image_context_cannot_be_guessed(field,value):
    item=image_statement();item[field]=value
    with pytest.raises(ValueError):validate(image_doc(),{'page':3,'image_sha256':'b'*64},item,'nonfinancial')


def test_image_duplicate_rows_and_operating_profit_as_ebitda_rejected():
    item=image_statement();item['rows'].append(copy.deepcopy(item['rows'][0]))
    with pytest.raises(ValueError):validate(image_doc(),{'page':3,'image_sha256':'b'*64},item,'nonfinancial')
    item=image_statement();item['rows'].append({'metric':'ebitda','label':'Operating profit','cells':['20','19','18']})
    with pytest.raises(ValueError):validate(image_doc(),{'page':3,'image_sha256':'b'*64},item,'nonfinancial')


def transcript(label,text):
    return {'url':'https://example.test/a.pdf','sha256':'a'*64,'fetched_at':'2026-10-30','kind':'transcript',
            'pages':[{'page':1,'text':label+'\nMR. JANE SMITH – CHIEF FINANCIAL OFFICER\nMODERATOR: JOHN DOE','requires_visual_review':False},
                     {'page':2,'text':'Jane Smith:\n'+text,'requires_visual_review':False}]}


def test_annual_minimum_is_not_replaced_by_earlier_band():
    doc=transcript('Q2 FY2026',"We maintain guidance for the full year '26. On guidance, we target revenue growth of 25% plus at both standalone and consol level, compared to our earlier guidance of 20% to 25%.")
    facts=observations(doc)
    assert len(facts)==2 and {x['basis'] for x in facts}=={'consolidated','standalone'}
    assert all(x['lower']=='25' and x['upper'] is None and x['target_period']=='FY2026' for x in facts)
    actual=transcript('Q4 FY2026','In FY26, our consol revenue grew by 22% Y-o-Y to INR 100 crores.')
    result=analyze([doc,actual])
    assert result['resolved_comparisons']==1
    assert result['ledger'][0]['comparisons'][0]['status']=='below_target'


def test_current_year_guidance_stays_pending_before_q4():
    g=transcript('Q1 FY2026','Our consolidated operating margin guidance for FY2026 is 20% to 22%.')
    a=transcript('Q2 FY2026','Our consolidated operating margin for Q2 FY2026 was 21%.')
    assert analyze([g,a])['ledger'][0]['comparisons'][0]['status']=='not_yet_due'


def test_segment_and_ytd_values_cannot_resolve_annual_company_targets():
    guidance=transcript('Q2 FY2026','Our consolidated operating margin guidance for FY2026 is 20% to 22%.')
    nine_month=transcript('Q3 FY2026','Our consolidated operating margin for 9M FY2026 was 21%.')
    annual=transcript('Q4 FY2026','Our consolidated business operating margin for FY2026 was 21%.')
    assert observations(nine_month)[0]['scope_verified'] is False
    assert observations(annual)[0]['scope_verified'] is False
    result=analyze([guidance,nine_month,annual])
    assert result['resolved_comparisons']==0
    assert all(a['statement_period']==row['period_end'] for row in result['ledger'] for a in row['extracted_actuals'])


def test_event_model_validates_linked_fields_and_real_date():
    text='The Board approved appointment of Jane Smith as Chief Financial Officer effective 1 November 2026.'
    doc={'url':'https://example.test/a.pdf','sha256':'a'*64,'fetched_at':'2026-10-30','pages':[{'page':1,'text':text}]}
    event=EventCandidate(name='Jane Smith',role='Chief Financial Officer',action='appointment',effective_date='2026-11-01',date_text='1 November 2026',page=1,quote=text)
    assert validate_event(doc,event)['effective_date']=='2026-11-01'
    event.effective_date='2026-12-01'
    with pytest.raises(ValueError):validate_event(doc,event)


def test_latest_session_window_and_unknown_watch_category(tmp_path,monkeypatch):
    store=Store(tmp_path/'db.sqlite3');at=datetime(2026,10,31,1,tzinfo=timezone.utc)
    class Clock(datetime):
        @classmethod
        def now(cls,tz=None):return at
    monkeypatch.setattr('finn.push.datetime',Clock)
    result=digest(store,window='latest',as_of=at,symbols=[])
    assert result['since']=='2026-10-29T18:30:00+00:00'
    with pytest.raises(ValueError):digest(store,watch_categories=['invented'],symbols=[])


def test_local_settings_are_not_executed_or_allowed_to_override_exports(tmp_path,monkeypatch):
    from finn.settings import load_local_settings
    f=tmp_path/'local.env';f.write_text('GEMINI_API_KEY="private-test-key"\nHOME=/unsafe\nFINN_FLASH_MODEL=gemini-test\n')
    monkeypatch.delenv('GEMINI_API_KEY',raising=False);monkeypatch.setenv('FINN_FLASH_MODEL','gemini-exported')
    import os
    prior=os.environ.get('HOME');load_local_settings(f)
    assert os.environ['GEMINI_API_KEY']=='private-test-key'
    assert os.environ['FINN_FLASH_MODEL']=='gemini-exported'
    assert os.environ.get('HOME')==prior
    monkeypatch.delenv('GEMINI_API_KEY')


def test_vision_adapter_sends_bounded_images_and_keeps_key_out_of_url():
    import httpx
    from finn.model import Flash
    def handler(request):
        assert 'private-test-key' not in str(request.url)
        body=json.loads(request.content);parts=body['contents'][0]['parts']
        assert parts[1]['inlineData']=={'mimeType':'image/png','data':'dGVzdA=='}
        return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'{"ok":true}'}]}}]})
    client=httpx.Client(transport=httpx.MockTransport(handler))
    model=Flash(client=client,key='private-test-key')
    value,usage=model.generate_vision('Synthetic image transport test',{}, {'type':'object'},[{'mime_type':'image/png','data':'dGVzdA=='}])
    assert value=={'ok':True} and usage['live'] is False
    with pytest.raises(RuntimeError):model.generate_vision('test',{}, {},[{'data':'x'}]*3)


def test_real_primary_image_transcription_reconciles_with_visible_deepak_statement():
    # Human-transcribed regression from the real NSE result page visually
    # inspected during repair. This is NOT a live Gemini response.
    data=image_statement();data['periods']=['2026-06-30','2026-03-31','2025-06-30']
    values={'revenue':['2577.60','2120.33','1889.88'],'other_income':['14.01','6.86','24.56'],
            'total_income':['2591.61','2127.19','1914.44'],'total_expenses':['2123.98','1825.84','1759.70'],
            'pbt_before_exception':['467.63','301.35','154.74'],'exceptional_items':['-','-','-'],
            'pbt':['467.63','301.35','154.74'],'tax':['122.62','81.52','42.49'],'pat':['345.01','219.83','112.25']}
    data['rows']=[{'metric':k,'label':k.replace('_',' '),'cells':v} for k,v in values.items()]
    result=validate(image_doc(),{'page':3,'image_sha256':'b'*64},data,'nonfinancial')
    assert result['rows'][0]['values']['current']=='2577.60'
    assert result['rows'][-1]['values']['current']=='345.01'


def test_real_kpil_annual_target_and_outcome_are_compared_without_quarter_mix():
    folder=Path(__file__).parent/'fixtures/day3'
    docs=[json.loads((folder/name).read_text()) for name in ('kpil-q2-fy26-complete.json','kpil-q4-fy26-complete.json')]
    result=analyze(docs)
    comparison=next(c for row in result['ledger'] for c in row['comparisons'] if c['status']=='below_target')
    assert comparison['target']=={'lower':'25','upper':None,'operator':'at_least'}
    assert comparison['actual']=='22'
    assert comparison['target_statement_period']=='Q2 FY2026'
    assert comparison['citations'][0]['sha256']==docs[0]['sha256']
    assert comparison['citations'][1]['sha256']==docs[1]['sha256']


def test_model_rate_limit_retry_is_bounded_and_credential_safe(monkeypatch):
    import httpx
    from finn.model import Flash
    waits=[];count=[];monkeypatch.setattr('finn.model.time.sleep',waits.append)
    def handler(request):
        count.append(1)
        if len(count)<3:return httpx.Response(429,headers={'retry-after':'90'})
        return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'{"ok":true}'}]}}]})
    model=Flash(client=httpx.Client(transport=httpx.MockTransport(handler)),key='private-test-key')
    value,_=model.generate('test',{}, {'type':'object'})
    assert value=={'ok':True} and len(count)==3 and waits==[90,90]


def test_exchange_fallback_does_not_hide_older_invalid_ohlc_or_missing_session():
    data=bars();ex={'date':'2026-10-30','open':101.,'high':104.,'low':100.,'close':103.,'volume':1500,'previous_close':100.}
    data[-4]['high']=98.
    with pytest.raises(ValueError):reconcile(data,'TCS','2026-10-30',ex,[])
    data=bars();data[-2]['date']='2026-10-28'
    with pytest.raises(ValueError):reconcile(data,'TCS','2026-10-30',ex,[])


def test_provider_schema_keeps_properties_and_refs_but_local_only_constraints_stay_local():
    from finn.model import provider_schema
    schema={'type':'object','properties':{'name':{'type':'string','minLength':3,'default':'x'},'item':{'$ref':'#/$defs/Item'}},'$defs':{'Item':{'type':'integer','minimum':1}},'required':['name']}
    value=provider_schema(schema)
    assert value['properties']['name']=={'type':'string','description':'Use at least 3 characters.'}
    assert value['properties']['item']['$ref']=='#/$defs/Item'
    assert value['$defs']['Item']['minimum']==1


def test_image_statement_normalizes_only_fully_specified_unambiguous_dates():
    from finn.vision_results import period_date
    data=image_statement();expected=list(data['periods'])
    from datetime import date
    data['periods']=[date.fromisoformat(p).strftime('%d.%m.%Y') for p in expected]
    result=validate(image_doc(),{'page':3,'image_sha256':'b'*64},data,'nonfinancial')
    assert list(result['periods'].values())==expected
    for value in ['03.04.2026','FY2026','Sep 2026','31.02.2026']:
        with pytest.raises(ValueError):period_date(value)


@pytest.mark.parametrize('known_consolidated',[False,True])
def test_image_fallback_prefers_consolidated_even_when_native_headings_are_unreadable(monkeypatch,known_consolidated):
    import finn.vision_results as vision
    calls=[]
    monkeypatch.setattr(vision,'primary_page_image',lambda doc,page,store:{'page':page,'image_sha256':'b'*64})
    class Model:
        def generate_vision(self,task,source,schema,images):
            page=source['page'];calls.append(page);data=image_statement()
            data['basis']='standalone' if page==1 else 'consolidated'
            return data,{'live':False}
    result=vision.extract(image_doc(),'nonfinancial',Model(),None,[1,2],require_consolidated=known_consolidated)
    assert calls==[1,2] and result['basis']=='consolidated' and result['requires_visual_review'] is True
    with pytest.raises(ValueError,match='Consolidated statement cannot be replaced'):
        vision.extract(image_doc(),'nonfinancial',Model(),None,[1],require_consolidated=True)
