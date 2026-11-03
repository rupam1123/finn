"""Saved real source regressions and explicitly synthetic fault/boundary tests."""
import hashlib
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path

import pytest

from finn.classifier import classify
from finn.documents import extract_document
from finn.push import analysis_key
from finn.push_ingest import process_filing, saved_document
from finn.storage import Store

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / 'fixtures' / 'day2'


def source(name):
    return json.loads((FIXTURES / (name + '.json')).read_text(encoding='utf-8'))


def filing(title='General Updates', description=''):
    return {'id': 'test', 'symbol': 'TCS', 'content_hash': 'test-revision',
            'title': title, 'description': description, 'document_url': source('tcs')['url']}


def synthetic(text):
    return {'url': source('tcs')['url'], 'sha256': 'a'*64, 'fetched_at': '2026-10-28T00:00:00+00:00',
            'status': 'text_extracted', 'page_count': 1,
            'pages': [{'page': 1, 'text': text, 'requires_visual_review': False}]}


@pytest.mark.parametrize('name,category', [('tcs', 'results'), ('hdfcbank', 'results'),
    ('infy', 'results'), ('bajfinance', 'management_change'), ('trent', 'management_change'),
    ('lt', 'management_change')])
def test_saved_real_cover_subjects(name, category):
    doc = source(name)
    result = classify(filing(), doc)
    assert result['category'] == category
    assert result['review_required'] and not result['buried']
    assert result['evidence'][0]['sha256'] == doc['sha256']


def test_real_polycab_metadata_and_ambiguous_cover():
    # This cover has a generic subject; metadata identifies the actual results event.
    result = classify(filing('Financial Results'), source('polycab'))
    assert result['category'] == 'results' and not result['buried']


@pytest.mark.parametrize('subject,category', [
    ('Schedule of Analyst/Institutional Investor Meeting', 'investor_meetings'),
    ('Q2 FY27 Earnings Conference Call', 'earnings_call'),
    ('Investor Presentation', 'results'),
    ('Intimation of investor/analyst call', 'earnings_call')])
def test_generic_exchange_meeting_title_uses_actual_subject(subject, category):
    result = classify(filing('Analysts/Institutional Investor Meet/Con. Call Updates', 'Schedule of meet'),
                      synthetic('Sub: '+subject+' Dear Sir, '+ 'Disclosure for the stock exchange. '*4))
    assert result['category'] == category and result['review_required'] and not result['buried']


def test_historical_annexure_words_do_not_create_events():
    doc = synthetic('Sub: Press release Dear Sir, We delivered a new software platform. '+
                    'Our historical risk factors include acquisition and management appointment. '*3)
    assert classify(filing('Press Release'), doc)['category'] == 'press_release'
    doc['pages'][0]['text'] = 'General reconciliation certificate. '*5+'Appointment of common agency for share registry.'
    result = classify(filing('Certificate under SEBI (Depositories and Participants) Regulations, 2018'), doc)
    assert result['category'] == 'unclassified' and not result['buried']


@pytest.mark.parametrize('event,category', [('Press Release on NCLAT Order','litigation'),
    ('Initial Public Offer of a subsidiary','fund_raise'),
    ('Voluntary Public Takeover Offer','M&A'), ('Bagging/Receiving of orders/contracts','press_release')])
def test_important_disclosures_not_lost(event, category):
    result = classify(filing(description=event), synthetic('Sub: '+event+' Dear Sir, '+'Details enclosed. '*8))
    assert result['category'] == category and not result['buried']


def test_existing_joint_venture_is_not_a_new_deal():
    result = classify(filing(description='License agreement by our existing subsidiary / joint venture'))
    assert result['category'] == 'unclassified' and result['review_required'] and not result['buried']


class WrongCategoryModel:
    configured = True
    model = 'synthetic-test-model'

    def generate(self, *args):
        return {'category': 'press_release', 'materiality': 5, 'confidence': .99,
                'reason': 'Synthetic conflicting decision', 'page': 1,
                'quote': 'Sub: Financial results'}, {}


def test_high_confidence_model_conflict_still_needs_review():
    doc = synthetic('Sub: Financial results Dear Sir, '+'Details enclosed. '*8)
    result = classify(filing(), doc, WrongCategoryModel())
    assert result['model_status'] == 'validated_output'
    assert result['review_required'] and result['review_reasons'] and not result['buried']


@pytest.mark.parametrize('document', [None, {'pages': []}, {'pages': [{'page': 1, 'text': ''}]}])
def test_missing_source_does_not_spend_model_tokens(document):
    class NeverCalled:
        configured = True

        def generate(self, *args):
            pytest.fail('A missing source must not invoke Gemini')

    result = classify(filing(), document, NeverCalled())
    assert result['model_status'] == 'source_unavailable'
    assert result['review_required'] and not result['buried']


def saved_setup(tmp_path):
    from finn.pdf_runtime import pymupdf
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((72, 72), 'Synthetic boundary fixture: primary bytes, not a market disclosure.')
        body = pdf.tobytes()
    store = Store(tmp_path / 'test.sqlite3')
    f = filing()
    digest = store.raw(f['document_url'], body)
    document = extract_document(body, f['document_url'])
    document.update(sha256=digest, fetched_at='2026-10-01T00:00:00+00:00')
    store.put('filing_document', f['id'], document)
    return store, f, body, document


def test_saved_reextract_uses_bytes_and_preserves_observation(tmp_path, monkeypatch):
    store, f, body, document = saved_setup(tmp_path)
    document['pages'][0]['text'] = 'Tampered saved text must not be trusted'
    store.put('filing_document', f['id'], document)
    def no_network(*args, **kwargs):
        pytest.fail('Saved mode must not fetch')
    monkeypatch.setattr('finn.push_ingest.fetch_document', no_network)
    result = process_filing(store, f, saved_documents=True)
    assert result['status'] == 'processed'
    analysis = store.get('push_analysis', analysis_key(f))['data']
    assert analysis['source_mode'] == 'saved_verified_bytes'
    assert analysis['document']['fetched_at'] == document['fetched_at']
    assert store.get('filing_document', f['id'])['data']['pages'][0]['text'].startswith('Synthetic boundary fixture')


@pytest.mark.parametrize('fault', ['missing_snapshot', 'missing_bytes', 'corrupt_bytes', 'changed_attachment'])
def test_saved_bytes_fail_closed(tmp_path, fault):
    store, f, body, document = saved_setup(tmp_path)
    with store.connect() as db:
        if fault == 'missing_snapshot': db.execute("DELETE FROM snapshots WHERE kind='filing_document'")
        if fault == 'missing_bytes': db.execute('DELETE FROM raw_responses')
        if fault == 'corrupt_bytes': db.execute('UPDATE raw_responses SET body=?', (body+b'corruption',))
    if fault == 'changed_attachment': f['document_url'] = f['document_url'].replace('.pdf', '-replacement.pdf')
    with pytest.raises(ValueError): saved_document(store, f)
    result = process_filing(store, f, saved_documents=True)
    analysis = store.get('push_analysis', analysis_key(f))['data']
    assert result['status'] == 'source_unavailable'
    assert analysis['classification']['review_required'] and not analysis['classification']['buried']


@pytest.mark.parametrize('encoding', ['cp1252', 'ascii'])
def test_pdf_worker_uses_utf8_under_windows_locale(tmp_path, encoding):
    from finn.pdf_runtime import pymupdf
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((72, 72), 'Synthetic currency: £100; café.')
        body = pdf.tobytes()
    env = {**os.environ, 'PYTHONUTF8': '0', 'PYTHONIOENCODING': encoding}
    result = subprocess.run([sys.executable, '-m', 'finn.pdf_worker', source('tcs')['url'], '500'],
                            input=body, capture_output=True, env=env, timeout=30)
    assert result.returncode == 0, result.stderr
    assert '£100' in json.loads(result.stdout.decode('utf-8'))['pages'][0]['text']


def runner():
    spec = importlib.util.spec_from_file_location('integration_runner', ROOT / 'scripts' / 'run_integration.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_backup_closes_both_handles_and_preserves_source(tmp_path):
    src, dst = tmp_path/'src.sqlite3', tmp_path/'dst.sqlite3'
    with closing(sqlite3.connect(src)) as db:
        db.execute('CREATE TABLE example(value)'); db.execute('INSERT INTO example VALUES(42)'); db.commit()
    before = hashlib.sha256(src.read_bytes()).hexdigest()
    runner().copy_database(src, dst)
    with closing(sqlite3.connect(dst)) as db:
        assert db.execute('SELECT value FROM example').fetchone()[0] == 42
    assert hashlib.sha256(src.read_bytes()).hexdigest() == before
    src.unlink(); dst.unlink()


def test_backup_does_not_create_missing_source(tmp_path):
    src, dst = tmp_path/'missing.sqlite3', tmp_path/'dst.sqlite3'
    with pytest.raises(FileNotFoundError): runner().copy_database(src, dst)
    assert not src.exists() and not dst.exists()


def test_real_zero_page_response_is_not_successful_extraction():
    body = (FIXTURES / 'zero-page-source.pdf').read_bytes()
    assert hashlib.sha256(body).hexdigest() == '47b1bf8e9a49e9a3d15b1a57e3b268b374270eeae4a0f4a69f36b9fbf4b56409'
    with pytest.raises(ValueError):
        extract_document(body, source('tcs')['url'])


def test_image_only_document_stays_visible_and_is_not_processed(tmp_path, monkeypatch):
    doc = synthetic('')
    doc['status'] = 'ocr_required'
    monkeypatch.setattr('finn.push_ingest.fetch_document', lambda *args: doc)
    store = Store(tmp_path/'test.sqlite3')
    result = process_filing(store, filing('Financial Results'))
    assert result['status'] == 'source_unreadable'
    saved = store.get('push_analysis', analysis_key(filing()))['data']
    assert saved['classification']['review_required'] and not saved['classification']['buried']


@pytest.mark.parametrize('subject,expected', [
    ('Allotment of securities under Employee Stock Option Scheme', 'unclassified'),
    ('Allotment of securities under ESOP and Qualified Institutional Placement', 'fund_raise'),
    ('Closure of Trading Window under SEBI Prohibition of Insider Trading Regulations', 'unclassified'),
    ('Disclosure under Regulation 7(2) Insider trading', 'insider_trading'),
    ('Presentation to be made at earnings call', 'results'),
    ('Media Statement', 'press_release'),
    ('Change in Director', 'management_change'),
    ('ESG rating by an analyst agency', 'unclassified'),
    ('Disposal of equity stake in subsidiary', 'M&A'),
    ('Outcome of investor sessions', 'investor_meetings'),
])
def test_specific_subject_semantics(subject, expected):
    result = classify(filing(), synthetic('Sub: '+subject+' Dear Sir, '+'Details enclosed. '*8))
    assert result['category'] == expected and not result['buried']


def test_historical_ref_after_subject_does_not_create_meeting():
    doc = synthetic('Sub: Intimation Ref: Earlier extraordinary general meeting Dear Sir, '+'Details enclosed. '*8)
    assert classify(filing(), doc)['category'] == 'unclassified'


@pytest.mark.parametrize('fault', [None, 'hash', 'revision', 'quote', 'page', 'category'])
def test_source_review_bound_to_exact_revision_and_source(fault):
    from finn.source_review import apply_source_review
    doc = synthetic('Sub: Financial results Dear Sir, '+'Details enclosed. '*8)
    f = filing()
    review = {'filing_content_hash': f['content_hash'], 'document_sha256': doc['sha256'],
              'category': 'results', 'scope': 'primary_event_category', 'page': 1,
              'quote': 'Financial results', 'reason': 'Confirmed primary event',
              'reviewed_at': '2026-10-29T00:00:00+00:00'}
    if fault == 'hash': review['document_sha256'] = 'b'*64
    if fault == 'revision': review['filing_content_hash'] = 'new-revision'
    if fault == 'quote': review['quote'] = 'Unsupported acquisition claim'
    if fault == 'page': review['page'] = 99
    if fault == 'category': review['category'] = 'invented'
    decision = {**classify(f, doc), 'category': 'unclassified', 'buried': True}
    result = apply_source_review(decision, f, doc, review)
    assert not result['buried'] and result['review_required']
    assert result['category'] == ('results' if fault is None else 'unclassified')


def test_failed_refresh_keeps_last_good_analysis_and_timestamp(tmp_path, monkeypatch):
    store, f, body, doc = saved_setup(tmp_path)
    assert process_filing(store, f, saved_documents=True)['status'] == 'processed'
    before = store.get('push_analysis', analysis_key(f))
    def fail(*args): raise ValueError('Synthetic invalid source')
    monkeypatch.setattr('finn.push_ingest.fetch_document', fail)
    assert process_filing(store, f, force=True)['status'] == 'retained_previous'
    after = store.get('push_analysis', analysis_key(f))
    assert after['data'] == before['data'] and after['fetched_at'] == before['fetched_at']
    assert after['last_attempt']['status'] == 'unavailable'


def test_real_persistent_resignation_binds_name_role_and_effective_date():
    from finn.management_enricher import enrich_management
    doc = source('persistent-resignation')
    result = enrich_management(doc)
    event = result['events'][0]
    assert len(result['events']) == 1
    assert (event['name'], event['role'], event['action'], event['effective_date']) == (
        'Rajesh Gharpure', 'Chief Delivery Officer', 'resignation', '2026-10-14')
    assert event['evidence']['sha256'] == doc['sha256'] and event['evidence']['page'] == 1
    assert 'closure of business hours' in event['evidence']['quote']


@pytest.mark.parametrize('change', ['missing_date', 'future_intent', 'invalid_date'])
def test_resignation_does_not_infer_unlinked_dates_or_actions(change):
    from finn.management_enricher import enrich_management
    doc = source('persistent-resignation')
    if change == 'missing_date':
        doc['pages'][0]['text'] = doc['pages'][0]['text'].replace('October 14, 2026', 'a later date')
    if change == 'future_intent':
        doc['pages'][0]['text'] = doc['pages'][0]['text'].replace('has tendered', 'may tender')
    if change == 'invalid_date':
        doc['pages'][0]['text'] = doc['pages'][0]['text'].replace('October 14, 2026', 'October 32, 2026')
    assert enrich_management(doc)['events'] == []


@pytest.mark.parametrize('case', json.loads((FIXTURES/'cover-regressions.json').read_text(encoding='utf-8')),
                         ids=lambda case: str(case['index']))
def test_real_cover_regressions(case):
    result = classify(case['filing'], case['document'])
    assert result['category'] == case['expected_rule_category']
    assert result['review_required'] and not result['buried']


def test_unreadable_refresh_preserves_readable_source_and_analysis(tmp_path, monkeypatch):
    store, f, body, document = saved_setup(tmp_path)
    assert process_filing(store, f, saved_documents=True)['status'] == 'processed'
    before = store.get('push_analysis', analysis_key(f))['data']
    unreadable = {**synthetic(''), 'sha256': 'b'*64, 'status': 'ocr_required'}
    monkeypatch.setattr('finn.push_ingest.fetch_document', lambda *args: unreadable)
    assert process_filing(store, f, force=True)['status'] == 'retained_previous'
    assert store.get('push_analysis', analysis_key(f))['data'] == before
    assert store.get('filing_document', f['id'])['data']['sha256'] == document['sha256']
    assert store.last_attempt('push_analysis', analysis_key(f))['status'] == 'unavailable'
