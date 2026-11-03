"""Reproduce three open reliability defects in a disposable database only."""
import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from finn.cli import ingest_company
from finn.main import create_app
from finn.storage import Store


def main():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'repro.sqlite3'
        store = Store(path)
        now = datetime.now(timezone.utc)
        filing = {'id': 'diagnostic-id', 'symbol': 'TCS', 'published_at': now.isoformat(), 'title': 'original'}
        store.add_filings([filing])
        store.add_filings([{**filing, 'title': 'corrected'}])
        amendment_ignored = store.filings('TCS', (now-timedelta(days=1)).isoformat())[0]['title'] == 'original'
        store.add_filings([{**filing, 'id': 'diagnostic-future', 'published_at': (now+timedelta(days=2)).isoformat()}])
        store.put('fundamentals', 'TCS', {'symbol': 'TCS', 'diagnostic': 'last successful snapshot'})
        with patch('finn.cli.fetch_screener', side_effect=RuntimeError('diagnostic source failure')), patch('finn.cli.fetch_nse', side_effect=RuntimeError('diagnostic source failure')):
            _, result = ingest_company('TCS', store, now)
        with TestClient(create_app(path)) as client:
            rows = client.get('/api/filings/TCS?days=1').json()['filings']
            snapshot = client.get('/api/company/TCS').json()
        report = {
            'data': 'Synthetic diagnostic rows in a temporary DB; never used as live evidence',
            'amendment_same_id_is_ignored': amendment_ignored,
            'future_filing_leaks_into_current_window': any(r['id'] == 'diagnostic-future' for r in rows),
            'failed_refresh_is_absent_from_company_api': result['fundamentals']['status'] == 'unavailable' and snapshot['data'].get('diagnostic') == 'last successful snapshot' and 'last_attempt' not in snapshot,
        }
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
