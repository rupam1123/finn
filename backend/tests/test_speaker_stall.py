"""Exact-source regressions for PDF spacing and source-bound row locators."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from finn.transcript_context import management_roster

FIXTURE=Path(__file__).parent/'fixtures/day3/polycab-court-filing.json'


def run_bounded(code):
    return subprocess.run([sys.executable,'-c',code],capture_output=True,timeout=8,env=os.environ.copy())


def test_exact_stalled_polycab_source_completes_native_research():
    document=json.loads(FIXTURE.read_text(encoding='utf-8'))
    assert len(document['pages'])==60
    assert document['sha256']=='a3a1264b2c68a37d607233586365a031fa2d3caf1c064dc73e15bed3713743ae'
    assert hashlib.sha256(FIXTURE.with_suffix('.pdf').read_bytes()).hexdigest()==document['sha256']
    code='''import json
from pathlib import Path
from finn.pull import build_research
from finn.transcript_rag import chunks
p=Path(FIXTURE_PATH)
d=json.loads(p.read_text(encoding='utf-8'))
items=chunks(d)
assert items and all(item['citation']['quote'] in next(page['text'] for page in d['pages'] if page['page']==item['citation']['page']) for item in items)
r=build_research('POLYCAB',[d],[])
assert r['sources'][0]['sha256']==d['sha256']
assert r['say_do']['observed_periods']==0
assert not r['claims_verified']
'''.replace('FIXTURE_PATH',repr(str(FIXTURE.resolve())))
    result=run_bounded(code)
    assert result.returncode==0,result.stderr.decode(errors='replace')


@pytest.mark.parametrize('spaces',[2,24,64])
def test_pdf_name_spacing_keeps_management_role_source_bound(spaces):
    name='Jane'+' '*spaces+'Smith'
    d={'url':'https://example.test/transcript.pdf','sha256':'a'*64,'fetched_at':'2026-10-31T00:00:00+00:00',
       'kind':'transcript','pages':[{'page':1,'text':name+'\nChief Financial Officer\n'+name+':\nWe report our results.'}]}
    roster=management_roster(d)
    assert roster['janesmith']['name']==name
    assert 'Chief Financial Officer' in roster['janesmith']['citation']['quote']


def test_model_located_numeric_tail_cannot_trigger_repeated_number_backtracking():
    fixture=Path(__file__).parent/'fixtures/day2/tcs.json'
    code='''import json
from pathlib import Path
import finn.results_enricher as results
from finn.results_enricher import LocatedRow
p=Path(FIXTURE_PATH)
d=json.loads(p.read_text(encoding='utf-8'));page=d['pages'][7]
quote='Revenue from operations '+'9'*200+' %'
page['text']+='\\n'+quote+'\\n'
results._row=lambda *args:None
try:results.parse_statement(d,page,located_rows=[LocatedRow(metric='revenue',label='Revenue from operations',quote=quote)])
except ValueError as exc:assert str(exc)=='Insufficient reliable rows'
else:raise AssertionError('Malformed source must abstain')
'''.replace('FIXTURE_PATH',repr(str(fixture.resolve())))
    result=run_bounded(code)
    assert result.returncode==0,result.stderr.decode(errors='replace')
