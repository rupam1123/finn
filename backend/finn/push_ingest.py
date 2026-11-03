"""Resumable, bounded Day 2 processing. API reads never fetch PDFs or call AI."""
import argparse
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from .classifier import classify
from .documents import document_url, extract_document, fetch_document, fetch_filing_document, container_matches
from .evidence import fingerprint
from .management_enricher import enrich_management
from .model import Flash
from .push import PIPELINE_VERSION, analysis_key
from .results_enricher import enrich_results
from .storage import Store, now_iso
from .source_review import apply_source_review
from .transport import Fetcher
from .universe import PORTFOLIO, symbol


def saved_document(store, filing):
    """Re-extract verified saved primary bytes without refreshing the source time."""
    snapshot = store.get('filing_document', filing['id'])
    if not snapshot:
        raise ValueError('No saved primary document')
    previous = snapshot['data']
    if previous['url'] != document_url(filing['document_url']):
        raise ValueError('Saved document belongs to a different attachment')
    with store.connect() as db:
        raw = db.execute('SELECT body FROM raw_responses WHERE sha256=?', (previous['sha256'],)).fetchone()
    if raw is None or hashlib.sha256(raw['body']).hexdigest() != previous['sha256']:
        raise ValueError('Saved primary bytes missing or hash mismatch')
    if previous.get('source_container'):
        with store.connect() as db:archive=db.execute('SELECT body FROM raw_responses WHERE sha256=?',(previous['source_container']['sha256'],)).fetchone()
        if not archive or not container_matches(previous,archive['body']):raise ValueError('Saved primary archive chain is invalid')
    document = extract_document(raw['body'], previous['url'])
    document.update({k: previous[k] for k in ('url', 'sha256', 'fetched_at')})
    for key in ('source_container','retained_previous'):
        if previous.get(key):document[key]=previous[key]
    document.update(cache_hit=True, source_mode='saved_verified_bytes')
    return document


def retained_document(store,filing):
    """Reparse prior verified bytes without pretending a failed refresh succeeded."""
    try:
        doc=saved_document(store,filing)
        if doc.get('status')=='text_extracted':return {**doc,'retained_previous':True,'source_mode':'retained_verified_bytes'}
    except (ValueError,KeyError):pass
    url=document_url(filing['document_url'])
    if not urlparse(url).path.lower().endswith('.pdf'):return None
    with store.connect() as db:rows=db.execute('SELECT sha256,fetched_at FROM raw_responses WHERE url=? ORDER BY fetched_at DESC LIMIT 3',(url,)).fetchall()
    for row in rows:
        with store.connect() as db:raw=db.execute('SELECT body FROM raw_responses WHERE sha256=?',(row['sha256'],)).fetchone()
        if not raw or hashlib.sha256(raw['body']).hexdigest()!=row['sha256']:continue
        try:doc=extract_document(raw['body'],url)
        except (ValueError,TypeError):continue
        if doc.get('status')=='text_extracted':
            return {**doc,'sha256':row['sha256'],'fetched_at':row['fetched_at'],'cache_hit':True,
                    'retained_previous':True,'source_mode':'retained_verified_bytes'}
    return None


def process_filing(store, filing, model=None, force=False, saved_documents=False):
    key = analysis_key(filing)
    old = store.get('push_analysis', key)
    review = store.get('source_review', filing['id'])
    review_version = fingerprint(review['data']) if review else None
    model_name = model.model if model and model.configured else None
    source_mode = 'saved_verified_bytes' if saved_documents else 'http'
    if (not force and old and old['data'].get('model_name') == model_name
            and old['data'].get('review_version') == review_version
            and old['data'].get('source_mode', 'http') == source_mode):
        # Content-addressed analyses don't expire as facts, but documents need periodic
        # revalidation: an exchange can replace PDF bytes at the same URL.
        age = (datetime.now(timezone.utc)-datetime.fromisoformat(old['fetched_at'])).total_seconds()
        if (0 <= age < 86400 and old['data']['status'] == 'processed'
                and (not old['last_attempt'] or old['last_attempt']['status'] == 'processed')
                and (not model_name or old['data']['classification']['model_status'] in {'validated_output', 'not_needed'})):
            return {'id': filing['id'], 'status': 'cached', 'symbol': filing['symbol']}
    attempt = store.start_attempt('push_analysis', key)
    document, doc_error = None, None
    url = filing.get('document_url')
    fetcher = Fetcher(store, force=force)
    try:
        if url and urlparse(url).path.lower().endswith(('.pdf','.zip')):
            try:
                document = (saved_document(store,filing) if saved_documents else
                            fetch_filing_document(url,fetcher) if urlparse(url).path.lower().endswith('.zip') else fetch_document(url,fetcher))
                previous_document = store.get('filing_document', filing['id'])
                if (document.get('status') != 'text_extracted' and previous_document
                        and previous_document['data'].get('status') == 'text_extracted'):
                    doc_error = 'New primary text is unreadable; previous readable source retained'
                    document = None
                else:
                    store.put('filing_document', filing['id'], document)
            except Exception as exc:
                doc_error = f'{type(exc).__name__}: '+str(exc)[:300]
        else:
            doc_error = 'Missing or unsupported attachment (PDF or single-PDF official NSE ZIP required)'
        if doc_error and old and old['data'].get('document') and old['data'].get('model_name')==model_name:
            store.finish_attempt(attempt,'unavailable',error=doc_error)
            return {'id':filing['id'],'symbol':filing['symbol'],'status':'retained_previous','error':doc_error}
        if document is None and doc_error and url and not saved_documents:
            try:document=retained_document(store,filing)
            except (ValueError,KeyError):document=None
            if document:store.put('filing_document',filing['id'],document)
        classification = classify(filing, document, model)
        classification = apply_source_review(classification, filing, document, review['data'] if review else None)
        retained=bool(document and document.get('retained_previous'))
        if retained:
            classification.update(buried=False,review_required=True)
            classification.setdefault('review_reasons',[]).append('Latest source refresh failed; prior verified bytes retained with their original observation time.')
        enrichment = None
        if classification['category'] == 'results':
            industry = (filing.get('industry') or '').lower()
            profile = 'bank' if 'bank' in industry else 'nbfc' if any(
                word in industry for word in ['finance', 'financial services']) else 'nonfinancial'
            # These two verified portfolio identities prevent a missing exchange industry
            # field from incorrectly applying an industrial EBITDA schema to a lender.
            profile = {'HDFCBANK': 'bank', 'BAJFINANCE': 'nbfc'}.get(filing['symbol'], profile)
            if not industry and filing['symbol'] not in PORTFOLIO:
                enrichment = {'kind': 'results', 'status': 'review_required', 'profile': 'unknown', 'rows': [],
                              'warnings': ['Issuer industry/profile is unavailable. Verify bank/NBFC/nonfinancial scope before extracting metrics.']}
            else:
                enrichment = {'kind': 'results', **enrich_results(document, profile, model, store)}
        elif classification['category'] == 'management_change':
            enrichment = {'kind': 'management_change', **enrich_management(document, model)}
        analysis = {'fetched_at': now_iso(), 'filing_content_hash': filing['content_hash'],
                    'filing_id': filing['id'], 'pipeline_version': PIPELINE_VERSION, 'model_name': model_name,
                    'source_mode': source_mode,
                    'review_version': review_version,
                    'classification': classification, 'enrichment': enrichment,
                    'status': ('processed' if document.get('status') == 'text_extracted' else 'source_unreadable') if document else 'source_unavailable',
                    'document': {k: document[k] for k in ['url', 'sha256', 'fetched_at', 'page_count', 'status']} if document else None,
                    'document_error': doc_error}
        if document:
            for field in ('source_container','source_mode','retained_previous'):
                if field in document:analysis['document'][field]=document[field]
        analysis['latest_source_refresh_ok']=False if retained else None if saved_documents else doc_error is None
        if not document and old and old['data'].get('document'):
            # Preserve last-good analytical data and its original timestamp on failure.
            store.finish_attempt(attempt, 'unavailable', error=doc_error)
            return {'id': filing['id'], 'symbol': filing['symbol'], 'status': 'retained_previous', 'error': doc_error}
        store.put('push_analysis', key, analysis)
        store.finish_attempt(attempt, 'unavailable' if retained else analysis['status'], document_error=doc_error)
        return {'id': filing['id'], 'symbol': filing['symbol'], 'status': 'retained_previous' if retained else analysis['status'],
                'category': classification['category'], 'buried': classification['buried'],
                'enrichment_status': enrichment['status'] if enrichment else None}
    except Exception as exc:
        store.finish_attempt(attempt, 'unavailable', error=f'{type(exc).__name__}: processing failed')
        return {'id': filing['id'], 'symbol': filing['symbol'], 'status': 'unavailable'}
    finally:
        fetcher.close()


def main():
    from .settings import load_local_settings
    load_local_settings()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default='data/finn.sqlite3')
    parser.add_argument('--symbols', nargs='+')
    parser.add_argument('--days', type=int, choices=[1, 3, 7, 30], default=30)
    parser.add_argument('--workers', type=int, choices=[1, 2, 3], default=3)
    parser.add_argument('--limit', type=int, help='Optional explicit document budget; unprocessed filings stay visible')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--use-model', action='store_true', help='Opt in to Gemini; requires GEMINI_API_KEY')
    parser.add_argument('--saved-documents', action='store_true',
                        help='Re-extract hash-verified saved PDFs without fetching; preserve original source timestamps')
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error('--limit must be positive')
    store = Store(args.db)
    model = Flash() if args.use_model else None
    if args.use_model and not model.configured:
        parser.error('--use-model requires GEMINI_API_KEY; do not put the key in command-line arguments')
    end = datetime.now(timezone.utc)
    tickers = [symbol(s) for s in args.symbols] if args.symbols else PORTFOLIO
    rows = [f for ticker in dict.fromkeys(tickers) for f in store.filings(ticker, end-timedelta(days=args.days), end)]
    rows.sort(key=lambda f: f['published_at'], reverse=True)
    selected = rows[:args.limit] if args.limit else rows
    started = time.perf_counter()
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for result in pool.map(lambda f: process_filing(store, f, model, args.force, args.saved_documents), selected):
            results.append(result)
            print(json.dumps(result), flush=True)
    report = {'pipeline_version': PIPELINE_VERSION, 'finished_at': now_iso(), 'selected': len(selected),
              'available_filings': len(rows), 'unselected': len(rows)-len(selected),
              'model': model.model if model else 'disabled', 'source_mode': 'saved_verified_bytes' if args.saved_documents else 'http',
              'elapsed_seconds': round(time.perf_counter()-started, 2),
              'results': results}
    store.run(report)
    print(json.dumps({k: v for k, v in report.items() if k != 'results'}), flush=True)
    raise SystemExit(1 if any(r['status'] in {'source_unavailable', 'source_unreadable', 'unavailable', 'retained_previous'} for r in results) else 0)


if __name__ == '__main__':
    main()
