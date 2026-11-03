"""Reproducible review cohort; source times and historical analyses are preserved."""
import argparse
import hashlib
import json
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

from finn.push import analysis_key
from finn.push_ingest import process_filing
from finn.documents import document_url, extract_document
from finn.storage import Store
from finn.universe import PORTFOLIO


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default='data/finn.sqlite3')
    parser.add_argument('--as-of', default='2026-10-29T04:51:36.974427+00:00')
    parser.add_argument('--out', default='verification/day2-backup-review')
    parser.add_argument('--saved-documents', action='store_true')
    parser.add_argument('--prefer-saved', action='store_true', help='Reuse verified primary bytes when present; HTTP only for missing documents')
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    store = Store(args.db)
    end = datetime.fromisoformat(args.as_of)
    if end.tzinfo is None:
        parser.error('--as-of requires a timezone')
    rows = [f for ticker in PORTFOLIO for f in store.filings(ticker, end-timedelta(days=30), end)]
    baseline = out / 'baseline.json'
    if not baseline.exists():
        with store.connect() as db:
            old = [json.loads(r[0]) for r in db.execute("SELECT payload FROM snapshots WHERE kind='push_analysis'")]
        by_id = {a['filing_id']: a for a in old}
        baseline.write_text(json.dumps({'as_of': end.isoformat(), 'filings': rows,
            'previous_analyses': old,
            'pending_ids': [f['id'] for f in rows if f['id'] not in by_id],
            'uncertain_ids': [f['id'] for f in rows if f['id'] not in by_id or by_id[f['id']]['classification']['review_required']]}, indent=2), encoding='utf-8')
    else:
        saved = json.loads(baseline.read_text(encoding='utf-8'))
        if saved['as_of'] != end.isoformat() or saved['filings'] != rows:
            raise ValueError('Frozen cohort changed; do not overwrite the existing review baseline')
    started = time.perf_counter()
    available = set()
    if args.prefer_saved:
        for filing in rows:
            if not filing.get('document_url'):
                continue
            try:
                url = document_url(filing['document_url'])
                with store.connect() as db:
                    raw = db.execute('SELECT * FROM raw_responses WHERE url=? ORDER BY fetched_at DESC LIMIT 1', (url,)).fetchone()
                if raw and hashlib.sha256(raw['body']).hexdigest() == raw['sha256']:
                    document = extract_document(raw['body'], url)
                    document.update(sha256=raw['sha256'], fetched_at=raw['fetched_at'], source_mode='saved_verified_bytes')
                    store.put('filing_document', filing['id'], document)
                    available.add(filing['id'])
            except ValueError:
                continue
        print(json.dumps({'verified_saved_sources':len(available)}), flush=True)
    with (out/'processing.jsonl').open('w', encoding='utf-8') as log, ThreadPoolExecutor(max_workers=3) as pool:
        results = []
        for result in pool.map(lambda f: process_filing(store, f, saved_documents=args.saved_documents or f['id'] in available), rows):
            results.append(result)
            log.write(json.dumps(result)+'\n'); log.flush()
            print(json.dumps(result), flush=True)
    analyses = [store.get('push_analysis', analysis_key(f)) for f in rows]
    summary = {'cohort_as_of': end.isoformat(), 'selected': len(rows), 'model': 'disabled',
               'elapsed_seconds': round(time.perf_counter()-started, 2),
               'outcomes': dict(Counter(r['status'] for r in results)),
               'stored_statuses': dict(Counter(a['data']['status'] if a else 'missing' for a in analyses)),
               'classification_accuracy': None,
               'accuracy_note': 'Source review and targeted regressions are not an independent labeled accuracy benchmark.'}
    (out/'processing-summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary), flush=True)
    raise SystemExit(0 if all(a and a['data']['status']=='processed' for a in analyses) else 1)


if __name__ == '__main__':
    main()
