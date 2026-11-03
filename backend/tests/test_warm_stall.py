"""Regressions for malformed financial rows and observable warm-cache progress."""
import json
import os
import subprocess
import sys
import threading
import time

import pytest
from finn.results_enricher import _row


def test_malformed_numeric_row_cannot_block_the_python_interpreter():
    # Isolate the regression: the previous regex held the GIL on this input.
    # A subprocess deadline makes a regression fail instead of hanging pytest.
    code = "from finn.results_enricher import _row; assert _row('Revenue from operations\\n'+'9'*200+'\\n%', 'Revenue from operations') is None"
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, timeout=8, env=os.environ.copy())
    assert result.returncode == 0, result.stderr.decode(errors='replace')


@pytest.mark.parametrize('separator', ['\n', ' '])
def test_numeric_row_preserves_cells_and_exact_source_quote(separator):
    cells = ['1,000.00','(90.00)','80','—','60','50']
    source = 'Revenue from operations\n' + separator.join(cells) + '\n(ii) Next row'
    label, values, quote = _row(source, 'Revenue from operations')
    assert label == 'Revenue from operations'
    assert values == cells
    assert quote == source.split('\n(ii)')[0]


@pytest.mark.parametrize('tail', ['\n70\nNext row', '\n%', '\n123 broken'])
def test_numeric_row_rejects_extra_cell_or_damaged_following_row(tail):
    source = 'Revenue from operations\n1\n2\n3\n4\n5\n6'+tail
    assert _row(source, 'Revenue from operations') is None


def test_finished_companies_are_checkpointed_without_waiting_for_first_submission(tmp_path, monkeypatch):
    from finn import pull
    release = threading.Event()
    output = tmp_path/'warm.json'
    monkeypatch.setattr(pull, 'PORTFOLIO', ['SLOW','FAST'])
    monkeypatch.setattr(pull, 'SHOWCASE', [])
    def research(ticker, store, emit, *args, **kwargs):
        emit({'stage':'analysis','symbol':ticker})
        if ticker == 'SLOW':
            assert release.wait(8)
        return {'symbol':ticker,'status':'partial'}
    monkeypatch.setattr(pull, 'research', research)
    monkeypatch.setattr(sys, 'argv', ['pull','--warm','--db',str(tmp_path/'cache.sqlite3'),'--output',str(output)])
    exited = []
    def run():
        try:pull.main()
        except SystemExit as exc:exited.append(exc.code)
    thread = threading.Thread(target=run)
    thread.start()
    try:
        deadline=time.monotonic()+5
        while not output.exists() and time.monotonic()<deadline:
            time.sleep(.02)
        assert output.exists(), 'FAST result must be written while SLOW is still pending'
        assert set(json.loads(output.read_text(encoding='utf-8'))) == {'FAST'}
        assert thread.is_alive()
    finally:
        release.set()
        thread.join(timeout=8)
    assert exited == [0]
    assert set(json.loads(output.read_text(encoding='utf-8'))) == {'SLOW','FAST'}


def test_research_progress_events_include_company_and_timestamp(tmp_path):
    from finn.pull import research
    from finn.storage import Store
    events=[]
    research('INFY',Store(tmp_path/'empty.sqlite3'),events.append,saved_only=True)
    assert events and all(event['symbol']=='INFY' and event['at'] for event in events)
    assert any(event['stage']=='analysis_ledger' for event in events)
