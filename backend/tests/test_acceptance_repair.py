"""Regressions for rejected provider grammars, bounded audits and retry provenance."""
import json

import httpx
import pytest
from pydantic import ValidationError

from finn.model import Flash, ModelUnavailable, model_failure
from finn.pull_reasoning import audit_four_quarters, ComparisonProposals
from finn.say_do_model import Facts
from finn.storage import Store, now_iso
from finn.validation import has_live_usage


def test_provider_grammar_omits_array_bounds_but_local_validation_keeps_them():
    def inspect(request):
        schema=json.loads(request.content)['generationConfig']['responseFormat']['text']['schema']
        assert schema['properties']['facts']['items']=={'$ref':'#/$defs/Fact'}
        assert 'maxItems' not in schema['properties']['facts']
        assert 'no more than 32 items' in schema['properties']['facts']['description']
        assert schema['$defs']['Fact']['properties']['source_index']['minimum']==0
        assert 'at least 15 characters' in schema['$defs']['Fact']['properties']['quote']['description']
        return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'{"facts": []}'}]}}]})
    with httpx.Client(transport=httpx.MockTransport(inspect)) as client:
        value,usage=Flash(client=client,key='unit-test-key').generate('Schema regression',{},Facts.model_json_schema())
    assert Facts.model_validate(value).facts==[] and usage['live'] is False
    fact={'kind':'actual','metric':'operating_margin','target_period':'Q1 FY2026','operator':'actual',
          'value':'20','basis':'consolidated','source_index':0,'quote':'Operating margin was 20%.',
          'context_index':0,'context_quote':'Consolidated Q1 FY2026 results'}
    with pytest.raises(ValidationError):Facts.model_validate({'facts':[fact]*33})
    with pytest.raises(ValidationError):Facts.model_validate({'facts':[{**fact,'source_index':-1}]})


def test_one_malformed_fact_cannot_discard_other_source_validated_observations(monkeypatch):
    from finn.say_do_model import extract,FactCandidates
    import finn.transcript_rag as rag
    quote='Our operating margin for Q1 FY2026 was 21% on a consolidated basis.'
    doc={'kind':'transcript','sha256':'a'*64,'url':'https://example.test/transcript.pdf',
         'pages':[{'page':1,'text':quote}]}
    item={'citation':{'sha256':doc['sha256'],'url':doc['url'],'page':1,'quote':quote},
          'speaker':'Jane Smith','speaker_verified':True}
    monkeypatch.setattr(rag,'reported_quarter',lambda d:{'label':'Q1 FY2026'})
    monkeypatch.setattr(rag,'chunks',lambda d:[item])
    monkeypatch.setattr(rag,'retrieve',lambda index,*args:index)
    valid={'kind':'actual','metric':'operating_margin','target_period':'Q1 FY2026','operator':'actual',
           'value':'21','basis':'consolidated','source_index':0,'quote':quote,'context_index':0,'context_quote':quote}
    class Model:
        def generate(self,*args):
            return {'facts':[{**valid,'target_period':'an unsupported year'},{**valid,'value':'21%'},valid]},{'live':False}
    facts,metadata=extract([doc],Model())
    assert len(facts)==1 and facts[0]['value']=='21' and facts[0]['citation']['quote']==quote
    assert metadata['accepted_observations']==1 and metadata['rejected_observations']==2
    assert metadata['rejection_reasons']==['Observation schema did not match the required fields','Percentage is absent or ambiguous']
    assert metadata['schema_rejections']==[{'field':'target_period','type':'string_pattern_mismatch'}]
    assert not has_live_usage(metadata)
    with pytest.raises(ValidationError):FactCandidates.model_validate({'facts':[valid]*33})


def excerpt(period,field):
    quote=period+' '+field+' '+('Literal primary evidence. '*65)
    source={'url':'https://example.test/'+period.replace(' ','-')+'.pdf','sha256':period+field,
            'page':1,'quote':quote}
    return {'citation':source,'speaker':'Jane Smith','speaker_verified':True,
            'speaker_evidence':{**source,'quote':'Jane Smith Chief Financial Officer '+('Roster evidence. '*40)}}


def test_comparison_accepts_explicit_fiscal_year_but_not_a_different_year_or_amount():
    from finn.pull_reasoning import comparison_packet,validate_comparisons
    row={'period_end':'Q3 FY2026','said':[excerpt('Q3 FY2026','guidance')],
         'delivered':[excerpt('Q3 FY2026','actual')]}
    packet=comparison_packet([row])
    item={'period':'Q3 FY2026','metric':'revenue','status':'not_comparable',
          'guidance_source':0,'actual_source':1,
          'assessment':'The supplied fiscal 2026 excerpts do not establish comparable revenue guidance.'}
    accepted,rejected=validate_comparisons({'comparisons':[item]},packet)
    assert len(accepted)==1 and not rejected
    for invented in ('2025','99%'):
        accepted,rejected=validate_comparisons({'comparisons':[{**item,'assessment':item['assessment'].replace('2026',invented)}]},packet)
        assert not accepted and len(rejected)==1


def test_large_four_period_audit_batches_without_dropping_or_reassigning_evidence():
    rows=[{'period_end':f'Q{i} FY2026','said':[excerpt(f'Q{i} FY2026','guidance') for _ in range(8)],
           'delivered':[excerpt(f'Q{i} FY2026','actual') for _ in range(8)]} for i in range(1,5)]
    packets=[]
    class Model:
        def generate(self,task,source,schema):
            assert len(json.dumps({'task':task,'source_data':source},ensure_ascii=False))<=100_000
            assert all(c['management_verified'] for c in source['source_context'])
            assert len(source['periods'])==1
            period=source['periods'][0];props=schema['$defs']['ComparisonProposal']['properties']
            assert props['period']['enum']==[period['period']]
            assert props['guidance_source']['enum']==period['guidance']
            assert props['actual_source']['enum']==period['actuals']
            assert [s['index'] for s in source['sources']]==list(range(len(source['sources'])))
            packets.append(source)
            return {'comparisons':[{'period':p['period'],'metric':'reported commentary',
                'assessment':'The supplied excerpts do not establish comparable targets.',
                'status':'not_comparable','guidance_source':p['guidance'][0],
                'actual_source':p['actuals'][0]} for p in source['periods']]},{'live':False}
    result=audit_four_quarters({'ledger':rows},Model())
    assert result['batch_count']>1 and not has_live_usage(result)
    assert [p['period'] for packet in packets for p in packet['periods']]==[r['period_end'] for r in rows]
    assert sum(len(packet['sources']) for packet in packets)==64
    for comparison,row in zip(result['comparisons'],rows):
        assert comparison['period']==row['period_end']
        assert comparison['citations']==[row['said'][0]['citation'],row['delivered'][0]['citation']]
        assert comparison['validation_status']=='semantic_review_required'


def test_single_oversized_period_abstains_before_provider_request():
    row={'period_end':'Q1 FY2026','said':[excerpt('Q1 FY2026','guidance')],
         'delivered':[excerpt('Q1 FY2026','actual')]}
    row['said'][0]['citation']['quote']='x'*110_000
    class Model:
        def generate(self,*args):raise AssertionError('Oversized evidence cannot reach the provider')
    with pytest.raises(ModelUnavailable,match='input budget'):audit_four_quarters({'ledger':[row]},Model())


def test_one_failed_period_keeps_other_validated_periods_and_reports_the_gap():
    rows=[{'period_end':f'Q{i} FY2026','said':[excerpt(f'Q{i} FY2026','guidance')],
           'delivered':[excerpt(f'Q{i} FY2026','actual')]} for i in range(1,4)]
    class Model:
        def generate(self,task,source,schema):
            period=source['periods'][0]
            if period['period']=='Q2 FY2026':raise ModelUnavailable('Model response unavailable or invalid')
            return {'comparisons':[{'period':period['period'],'metric':'reported commentary',
                'assessment':'The supplied excerpts do not establish comparable targets.','status':'not_comparable',
                'guidance_source':period['guidance'][0],'actual_source':period['actuals'][0]}]},{'live':False}
    result=audit_four_quarters({'ledger':rows},Model())
    assert result['status']=='partial'
    assert [c['period'] for c in result['comparisons']]==['Q1 FY2026','Q3 FY2026']
    assert result['errors']==[{'period':'Q2 FY2026','error':'ModelUnavailable: Model response unavailable or invalid'}]
    assert not has_live_usage(result)


@pytest.mark.parametrize('kind',['valid','financial_number','uncited_reference'])
def test_source_index_labels_cannot_mask_unsupported_financial_numbers(kind):
    row={'period_end':'Q1 FY2026','said':[excerpt('Q1 FY2026','guidance')],
         'delivered':[excerpt('Q1 FY2026','actual')]}
    assessment='Source 0 and Source 1 contain commentary, but the supplied excerpts do not establish a comparable target.'
    if kind=='financial_number':assessment+=' The company reported an unsupported 99% margin.'
    if kind=='uncited_reference':assessment=assessment.replace('Source 1','Source 9')
    class Model:
        def generate(self,*args):
            return {'comparisons':[{'period':'Q1 FY2026','metric':'commentary','assessment':assessment,
                'status':'not_comparable','guidance_source':0,'actual_source':1}]},{'live':False}
    if kind=='valid':
        result=audit_four_quarters({'ledger':[row]},Model())
        assert 'Source 0' not in result['comparisons'][0]['assessment']
        assert result['comparisons'][0]['raw_assessment']==assessment
    else:
        with pytest.raises(ValueError,match='numbers absent' if kind=='financial_number' else 'uncited source'):
            audit_four_quarters({'ledger':[row]},Model())


def test_rejected_comparison_does_not_discard_a_supported_candidate_for_the_same_period():
    row={'period_end':'Q1 FY2026','said':[excerpt('Q1 FY2026','guidance')],
         'delivered':[excerpt('Q1 FY2026','actual')]}
    good={'period':'Q1 FY2026','metric':'commentary','assessment':'The supplied primary excerpts do not establish an aligned target for a numerical comparison.',
          'status':'not_comparable','guidance_source':0,'actual_source':1}
    class Model:
        def generate(self,*args):return {'comparisons':[{**good,'assessment':good['assessment']+' An unsupported 99% was reported.'},good]},{'live':False}
    result=audit_four_quarters({'ledger':[row]},Model())
    assert len(result['comparisons'])==1 and len(result['rejected_proposals'])==1
    assert '99%' not in result['comparisons'][0]['assessment']


def test_bare_status_is_not_a_completed_research_assessment():
    from finn.pull_reasoning import ComparisonProposal
    with pytest.raises(ValidationError):ComparisonProposal.model_validate({'period':'Q1 FY2026','metric':'commentary',
        'assessment':'not_comparable','status':'not_comparable','guidance_source':0,'actual_source':1})


def test_image_page_ranking_prefers_financial_tables_to_cover_letters():
    from finn.results_enricher import image_statement_pages
    table='Quarter ended. Revenue from operations. Profit before tax. Profit for the period. Total expenses.'
    doc={'pages':[{'page':1,'text':'Consolidated financial results for the quarter. Covering letter.'},
                  {'page':2,'text':'Independent auditor report on consolidated financial results.'},
                  {'page':7,'text':'Standalone '+table},
                  {'page':13,'text':'Consolidated '+table},
                  {'page':8,'text':'','requires_visual_review':True}]}
    pages=image_statement_pages(doc,[{'page':7,'reason':'Insufficient reliable rows'},{'page':13,'reason':'Insufficient reliable rows'}])
    assert pages[:3]==[13,7,8]


def test_safe_model_diagnostic_preserves_actionable_cause_without_arbitrary_text():
    assert model_failure(ModelUnavailable('Model input budget exceeded'))=='ModelUnavailable: Model input budget exceeded'
    assert model_failure(ModelUnavailable('Gemini returned HTTP 429 (GenerateRequestsPerDay); daily request quota exhausted')).endswith('HTTP 429; daily request quota exhausted')
    assert model_failure(ModelUnavailable('Gemini returned HTTP 400 SECRET'))=='ModelUnavailable: Gemini returned HTTP 400'
    assert model_failure(ModelUnavailable('SECRET private provider body'))=='ModelUnavailable'
    assert model_failure(ValueError('SECRET bad model text'))=='ValueError'


@pytest.mark.parametrize('corrected,correction_live',[(True,True),(False,True),(True,False)])
def test_classification_quote_retry_keeps_exact_source_validation_and_review(corrected,correction_live):
    from finn.classifier import classify
    quote='The company has disclosed material litigation involving a tax demand. Please inspect the original filing.'
    doc={'url':'https://example.test/filing.pdf','sha256':'a'*64,'fetched_at':'2026-10-31T00:00:00+00:00',
         'status':'text_extracted','page_count':1,'pages':[{'page':1,'text':quote,'requires_visual_review':False}]}
    calls=[]
    class Model:
        configured=True
        def generate(self,task,source,schema):
            calls.append(task)
            if len(calls)==2:assert 'contiguous verbatim quote' in task and source['prior_quote']=='This quotation is absent.'
            text=quote if len(calls)==2 and corrected else 'This quotation is absent.'
            return {'category':'litigation','materiality':10,'confidence':.99,'reason':'Tax dispute',
                    'page':1,'quote':text},{'provider':'isolated unit mock','live':True if len(calls)==1 else correction_live}
    result=classify({'title':'Litigation disclosure','description':''},doc,Model())
    assert len(calls)==(3 if not corrected else 2) and not result['buried'] and result['review_required']
    if corrected and correction_live:
        assert result['model_status']=='validated_output' and result['evidence'][0]['quote']==quote
        assert result['materiality']>=85 and result['usage']['validation_retry_usage']['usage']['live'] is True
    else:
        assert result['model_status']=='unavailable_or_invalid' and not result['evidence']


@pytest.mark.parametrize('index,live',[(0,True),(999,True),(0,False)])
def test_last_classification_fallback_selects_only_supplied_literal_evidence(index,live):
    from finn.classifier import classify
    quote='The company has disclosed material litigation involving a tax demand. Please inspect the original filing.'
    doc={'url':'https://example.test/filing.pdf','sha256':'a'*64,'fetched_at':'2026-10-31T00:00:00+00:00',
         'status':'text_extracted','page_count':1,'pages':[{'page':1,'text':quote,'requires_visual_review':False}]}
    calls=[]
    class Model:
        configured=True
        def generate(self,task,source,schema):
            calls.append(task)
            base={'category':'litigation','materiality':10,'confidence':.99,'reason':'Tax dispute'}
            if len(calls)<3:return {**base,'page':1,'quote':'This quotation is absent.'},{'provider':'isolated unit mock','live':True}
            assert source['source_spans']==[{'index':0,'page':1,'quote':quote}]
            assert schema['properties']['span_index']['enum']==[0]
            return {**base,'span_index':index},{'provider':'isolated unit mock','live':live}
    result=classify({'title':'Litigation disclosure','description':''},doc,Model())
    assert len(calls)==3 and result['review_required'] and not result['buried']
    if index==0 and live:
        assert result['model_status']=='validated_output' and result['evidence'][0]['quote']==quote
        assert result['evidence'][0]['page']==1 and result['materiality']>=85
    else:assert result['model_status']=='unavailable_or_invalid' and not result['evidence']


@pytest.mark.parametrize('ambiguous',[False,True])
def test_printed_page_offset_uses_only_unique_literal_evidence_matches(ambiguous):
    from finn.classifier import classify
    quote='The company disclosed a material tax demand and litigation requiring review of this filing.'
    pages=[{'page':1,'text':'This is a cover page. '*6,'requires_visual_review':False},
           {'page':2,'text':quote,'requires_visual_review':False}]
    if ambiguous:pages.append({'page':3,'text':quote,'requires_visual_review':False})
    doc={'url':'https://example.test/filing.pdf','sha256':'a'*64,'fetched_at':'2026-10-31T00:00:00+00:00',
         'status':'text_extracted','page_count':len(pages),'pages':pages}
    class Model:
        configured=True
        def generate(self,*args):
            return {'category':'litigation','materiality':10,'confidence':.99,'reason':'Tax dispute',
                    'page':1,'quote':quote},{'live':False}
    result=classify({'title':'Litigation disclosure','description':''},doc,Model())
    assert not result['buried'] and result['review_required']
    if ambiguous:assert result['model_status']=='unavailable_or_invalid'
    else:
        assert result['model_status']=='validated_output' and result['evidence'][0]['page']==2
        assert result['evidence'][0]['quote']==quote and not has_live_usage(result)


def test_ordinary_release_does_not_spend_financial_extraction_requests():
    from finn.results_enricher import enrich_results
    class Model:
        configured=True
        def generate(self,*args):raise AssertionError('An ordinary release has no statement to locate')
    doc={'url':'https://example.test/release.pdf','status':'text_extracted',
         'pages':[{'page':1,'text':'We announce a new technology partnership and an upcoming investor meeting.',
                   'requires_visual_review':False}]}
    result=enrich_results(doc,model=Model())
    assert result['rows']==[] and result['status']=='review_required'
    assert result['model_status']=='not_needed' and 'No quarterly financial statement' in result['warnings'][0]


@pytest.mark.parametrize('scanned',[False,True,'partial'])
def test_statement_candidate_and_scanned_page_still_allow_model_locator(scanned):
    from finn.results_enricher import enrich_results
    calls=[]
    class Model:
        configured=True
        def generate(self,task,source,schema):
            calls.append(source)
            raise ModelUnavailable('Model response unavailable or invalid')
    text=('Readable cover text. '*10 if scanned=='partial' else '' if scanned else
          'Quarterly statement: revenue and profit for the quarter ended. Layout needs review.')
    doc={'url':'https://example.test/results.pdf','status':'ocr_required' if scanned is True else 'text_extracted',
         'pages':[{'page':1,'text':text,'requires_visual_review':bool(scanned)}]}
    result=enrich_results(doc,model=Model())
    assert len(calls)==2 and result['rows']==[]
    assert all(c['pages'][0]['text']==text for c in calls)


@pytest.mark.parametrize('ticker,profile',[('HDFCBANK','bank'),('BAJFINANCE','nbfc')])
def test_short_lender_document_keeps_issuer_profile_and_excludes_industrial_cash(ticker,profile,monkeypatch):
    import finn.pull as pull
    import finn.annual_forensics as annual
    profiles=[]
    def extract(doc,selected,*args):
        profiles.append(selected)
        return {'profile':selected,'status':'review_required','rows':[]}
    def forbidden(*args):raise AssertionError('Industrial cash ratios cannot run for these lenders')
    monkeypatch.setattr(pull,'enrich_results',extract)
    monkeypatch.setattr(annual,'extract_annual',forbidden)
    monkeypatch.setattr(annual,'extract_leverage',forbidden)
    doc={'url':'https://example.test/annual.pdf','sha256':'a'*64,'fetched_at':'2026-10-31T00:00:00+00:00',
         'kind':'annual_report','pages':[{'page':1,'text':'Annual report. This short page has no industry boilerplate.'}]}
    result=pull.build_research(ticker,[doc],[])
    assert profiles==[profile]
    assert result['annual_forensics'][0]['status']=='not_applicable'
    assert not result['modules']['cash_quality']['facts']


def test_saved_retry_replaces_model_failures_and_preserves_original_snapshot(tmp_path,monkeypatch):
    import finn.pull as pull
    import finn.pull_reasoning as reasoning
    store=Store(tmp_path/'retry.sqlite3');observed='2026-10-31T00:00:00+00:00'
    digest=store.raw('https://example.test/unit.pdf',b'%PDF isolated retry fixture')
    doc={'url':'https://example.test/unit.pdf','sha256':digest,'fetched_at':observed,'kind':'transcript'}
    store.put('pull_document','INFY:'+digest,doc)
    previous={'fetched_at':observed,'version':'old','status':'partial','sources':[doc],
              'source_errors':[{'stage':'document','error':'Original missing attachment'},
                               {'stage':'say_do_extraction','error':'ModelUnavailable'},
                               {'stage':'say_do_reasoning','error':'ModelUnavailable'},
                               {'stage':'reasoning','error':'ModelUnavailable'}]}
    store.put('pull','INFY',previous)
    def build(ticker,documents,errors,*args,**kwargs):
        assert documents==[doc]
        return {'fetched_at':now_iso(),'version':pull.VERSION,'sources':[doc],'status':'partial',
                'source_errors':errors,'say_do':{'ledger':[]},'modules':{}}
    monkeypatch.setattr(pull,'build_research',build)
    monkeypatch.setattr(pull,'chunks',lambda doc:[])
    monkeypatch.setattr(reasoning,'audit_four_quarters',lambda *args:{'comparisons':[]})
    monkeypatch.setattr(reasoning,'synthesize',lambda *args:{'proposals':[]})
    class Model:
        configured=True;model='unit-test-model'
    result=pull.research('INFY',store,saved_only=True,force=True,model=Model())
    assert result['source_errors']==previous['source_errors'][:1]
    assert store.get('pull_history','INFY:'+observed)['data']==previous
    assert store.get('pull_document','INFY:'+digest)['data']['fetched_at']==observed
