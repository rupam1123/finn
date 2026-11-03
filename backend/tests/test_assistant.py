"""Synthetic safety/behavior checks; no provider calls or acceptance claims."""
import json

import pytest
from fastapi.testclient import TestClient

from finn.assistant import Ask, generate, passages
from finn.main import create_app
from finn.storage import Store


def sample():
    citation = {'sha256': 'a' * 64, 'url': 'https://issuer.example/report.pdf',
                'page': 2, 'quote': 'Management reported revenue of INR 100 crore for FY2026 on a consolidated basis.',
                'observed_at': '2026-11-01T12:00:00+00:00'}
    return {'symbol': 'TCS', 'fetched_at': '2026-11-01T12:00:00+00:00',
            'sources': [{'sha256': citation['sha256'], 'url': citation['url'], 'page_count': 3}],
            'modules': {'business_snapshot': {'excerpts': [{'citation': citation}]}}}


class Model:
    model = 'test-model'
    def __init__(self, output=None):
        self.output = output or {'points': [{'text': 'The source reports INR 100 crore for FY2026 on a consolidated basis.', 'source_indices': [0]}]}
        self.calls = 0
    def generate(self, task, source, schema):
        self.calls += 1
        assert 'untrusted data' in task and 'Do not calculate' in task
        assert source['sources'][0]['quote'] == sample()['modules']['business_snapshot']['excerpts'][0]['citation']['quote']
        return self.output, {}


def test_summary_retains_citations_and_review_state():
    result = generate(sample(), Ask(), Model())
    assert result['mode'] == 'ai_draft' and result['claims_verified'] is False
    assert result['points'][0]['citations'][0]['page'] == 2
    assert result['source_saved_at'] == sample()['fetched_at']


@pytest.mark.parametrize('change', ['hash', 'url', 'protocol', 'page', 'page_max', 'visual', 'image'])
def test_reject_unbound_or_visual_passages(change):
    data = sample(); item = data['modules']['business_snapshot']['excerpts'][0]; c = item['citation']
    if change == 'hash': c['sha256'] = 'b' * 64
    if change == 'url': c['url'] = 'https://different.example/report.pdf'
    if change == 'protocol': c['url'] = data['sources'][0]['url'] = 'javascript:alert(1)'
    if change == 'page': c['page'] = True
    if change == 'page_max': c['page'] = 4
    if change == 'visual': item['requires_visual_review'] = True
    if change == 'image': c['evidence_type'] = 'page_image'
    assert passages(data) == []


def test_search_abstains_and_deduplicates_without_inventing_an_answer():
    data = sample(); data['modules']['business_snapshot']['excerpts'] *= 3
    assert len(passages(data, question='revenue')) == 1
    assert passages(data, question='dividend') == []
    model = Model(); assert generate(data, Ask(question='dividend'), model)['mode'] == 'unavailable'
    assert model.calls == 0


@pytest.mark.parametrize('point', [
    {'text': 'The source reports INR 101 crore.', 'source_indices': [0]},
    {'text': 'The source reports INR 100 crore.', 'source_indices': [-1]},
    {'text': 'The source reports INR 100 crore.', 'source_indices': [1]},
])
def test_model_output_cannot_add_numbers_or_unknown_citations(point):
    with pytest.raises(ValueError): generate(sample(), Ask(), Model({'points': [point]}))


def owner(tmp_path, monkeypatch):
    monkeypatch.setenv('FINN_PUBLIC_REVIEW', '0')
    monkeypatch.setenv('FINN_ASSISTANT_USE_MODEL', '1')
    monkeypatch.setenv('GEMINI_API_KEY', 'test-key-not-real')
    path = tmp_path / 'assistant.sqlite3'; app = create_app(path)
    Store(path).put('pull', 'TCS', sample())
    return path, app


def test_read_only_blocks_generation_even_with_key_and_flag(tmp_path, monkeypatch):
    monkeypatch.setenv('FINN_PUBLIC_REVIEW', '1')
    monkeypatch.setenv('FINN_ASSISTANT_USE_MODEL', '1')
    monkeypatch.setenv('GEMINI_API_KEY', 'test-key-not-real')
    def forbidden(*a, **kw): raise AssertionError('Read invoked a model')
    monkeypatch.setattr('finn.model.Flash.generate', forbidden)
    with TestClient(create_app(tmp_path / 'readonly.sqlite3')) as c:
        assert c.get('/api/assistant/capabilities').json() == {'generation_enabled': False, 'saved_source_guide': True}
        assert c.get('/api/portfolio/overview').status_code == 200
        assert c.post('/api/assistant/TCS', json={}).status_code == 403


def test_key_alone_does_not_enable_generation(tmp_path, monkeypatch):
    monkeypatch.setenv('FINN_PUBLIC_REVIEW', '0'); monkeypatch.setenv('GEMINI_API_KEY', 'test-key-not-real')
    monkeypatch.delenv('FINN_ASSISTANT_USE_MODEL', raising=False)
    with TestClient(create_app(tmp_path / 'off.sqlite3')) as c:
        assert c.get('/api/assistant/capabilities').json()['generation_enabled'] is False


def test_origins_bounds_budget_and_no_saved_questions(tmp_path, monkeypatch):
    path, app = owner(tmp_path, monkeypatch); model = Model()
    monkeypatch.setattr('finn.model.Flash', lambda: model)
    with TestClient(app) as c:
        assert c.post('/api/assistant/TCS', json={}, headers={'origin': 'https://attacker.example'}).status_code == 403
        assert c.post('/api/assistant/TCS', json={}, headers={'sec-fetch-site': 'cross-site'}).status_code == 403
        assert c.post('/api/assistant/TCS', json={'question': 'x' * 401}).status_code == 422
        assert c.post('/api/assistant/TCS', json={'topic': 'trade'}).status_code == 422
        assert c.post('/api/assistant/TCS', json={'question': 'dividend'}).json()['mode'] == 'unavailable'
        for _ in range(6):
            assert c.post('/api/assistant/TCS', json={'question': 'revenue'}, headers={'origin': 'http://localhost:3000'}).status_code == 200
        response = c.post('/api/assistant/TCS', json={})
        assert response.status_code == 429 and response.headers['retry-after'] == '3600'
    assert model.calls == 6
    with Store(path).connect() as db:
        assert [r['name'] for r in db.execute('PRAGMA table_info(assistant_usage)')] == ['created_at']
        assert db.execute('SELECT count(*) FROM assistant_usage').fetchone()[0] == 6
    # The persisted quota also applies to a newly constructed API process.
    with TestClient(create_app(path)) as c:
        assert c.post('/api/assistant/TCS', json={}).status_code == 429


def test_provider_errors_are_redacted_and_gate_releases(tmp_path, monkeypatch):
    _path, app = owner(tmp_path, monkeypatch)
    def fail(*a, **kw): raise RuntimeError('SECRET /private/key.env')
    monkeypatch.setattr('finn.model.Flash.generate', fail)
    with TestClient(app) as c:
        for _ in range(2):
            r = c.post('/api/assistant/TCS', json={})
            assert r.status_code == 503 and 'SECRET' not in json.dumps(r.json())
