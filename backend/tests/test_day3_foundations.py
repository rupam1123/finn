from finn.transcript_rag import chunks, retrieve
from finn.narrative_auditor import compare
from finn.forensic_analyzer import ratio
import pytest


def test_page_bound_chunks():
    doc = {'url':'https://example.test/a.pdf','sha256':'a'*64,'fetched_at':'2026-01-01',
           'pages':[{'page':2,'text':'Revenue guidance increased. '*100}]}
    index = chunks(doc)
    assert len(index) > 1
    assert all(x['citation']['quote'] in doc['pages'][0]['text'] for x in index)
    assert retrieve(index, 'guidance')[0]['citation']['page'] == 2
    assert not retrieve(index, 'absent')


def observation(value):
    return dict(value=value, metric='revenue',period_start='2025-01-01',period_end='2025-03-31',
                basis='consolidated',currency='INR',unit='crore',definition='reported revenue',
                reviewed_primary=True,citations=[{'quote':'review fixture'}])


def test_comparison_guards():
    actual = observation('11')
    guidance = dict(observation('0'), lower='10',upper='12',statement_date='2024-12-01',direction='higher')
    assert compare(guidance, actual, '2025-04-01')['status'] == 'within_target'
    assert compare(guidance, actual, '2025-02-01')['status'] == 'not_yet_due'
    assert compare(guidance, dict(actual,basis='standalone'), '2025-04-01')['status'] == 'not_comparable'
    assert compare(guidance, dict(actual,reviewed_primary=False), '2025-04-01')['status'] == 'review_required'


def test_ratio_guards():
    assert ratio(observation('20'),observation('10'))['value'] == '2'
    assert ratio(observation('20'),observation('0'))['status'] == 'undefined'
    assert ratio(None,None)['status'] == 'missing'
    assert ratio(None,None,profile='bank')['status'] == 'not_applicable'
    with pytest.raises(ValueError):
        ratio(observation('NaN'),observation('10'))
