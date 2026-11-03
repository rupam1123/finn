import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .documents import resolve_transcript, transcript_quality
from .filings_ingest import fetch_nse
from .market_data import fetch_market
from .screener_scraper import fetch_screener
from .storage import Store
from .transport import Fetcher
from .universe import PORTFOLIO, MASTER_URL, parse_master, symbol


def failed_previous_attempt(store, kind, ticker):
    attempt = store.last_attempt(kind, ticker)
    return bool(attempt and attempt['status'] not in {'ok', 'cached', 'text_extracted'})


def ingest_company(s, store, now, market=None, primary_sample=False, force=False):
    fetcher = Fetcher(store)
    fetcher.force = force
    started = time.perf_counter()
    result, data, filings = {}, None, None
    if market is not None:
        result['market'] = {k: v for k, v in market.items() if k != 'bars'}
    try:
        fetcher.force = force or failed_previous_attempt(store, 'fundamentals', s)
        attempt = store.start_attempt('fundamentals', s) if force or not store.reusable('fundamentals', s) else None
        try:
            cached = store.reusable('fundamentals', s) if attempt is None else None
            if cached:
                data = cached['data']
            else:
                data = fetch_screener(s, fetcher)
                if data['warnings']:
                    if data.get('source_url'):
                        store.invalidate_http(data['source_url'])
                    raise ValueError('Incomplete staging tables: ' + '; '.join(data['warnings']))
                store.put('fundamentals', s, data)
                store.finish_attempt(attempt, 'ok', source_observed_at=data.get('fetched_at'))
            result['fundamentals'] = {'status': 'cached' if cached else 'ok', 'basis': data['basis'],
                'tables': len(data['tables']), 'documents': len(data['documents']),
                'latency_ms': 0 if cached else data['latency_ms'], 'warnings': data['warnings'],
                'cache_hit': bool(cached) or data.get('cache_hit', False), 'fetched_at': data.get('fetched_at')}
        except Exception as exc:
            data = None
            result['fundamentals'] = {'status': 'unavailable', 'error': str(exc)}
            if attempt is not None:
                store.finish_attempt(attempt, 'unavailable', error=str(exc))
        fetcher.force = force or failed_previous_attempt(store, 'filings_coverage', s)
        attempt = store.start_attempt('filings_coverage', s)
        try:
            filings = fetch_nse(s, now-timedelta(days=30), now, fetcher)
            store.add_filings(filings['filings'], observed_at=filings.get('fetched_at'))
            coverage = {k: v for k, v in filings.items() if k != 'filings'}
            coverage['status'] = 'partial' if filings['errors'] else 'ok'
            store.put('filings_coverage', s, coverage)
            store.finish_attempt(attempt, coverage['status'], source_observed_at=filings.get('fetched_at'),
                                 cache_hit=filings.get('cache_hit', False), errors=filings['errors'])
            result['filings'] = {**coverage, 'count': len(filings['filings'])}
        except Exception as exc:
            result['filings'] = {'status': 'unavailable', 'error': str(exc)}
            store.finish_attempt(attempt, 'unavailable', error=str(exc))
        if primary_sample:
            cached = None if force else store.reusable('primary_sample', s)
            if cached and transcript_quality(cached['data'])['status'] == 'transcript_candidate':
                result['primary_sample'] = {k: v for k, v in cached['data'].items() if k != 'pages'}
                result['primary_sample']['cache_hit'] = True
            else:
                fetcher.force = force or failed_previous_attempt(store, 'primary_sample', s)
                attempt = store.start_attempt('primary_sample', s)
                candidates = []
                if filings:
                    candidates.extend(r['document_url'] for r in filings['filings']
                                      if r['document_url'] and 'transcript' in (r['title']+r['description']).lower())
                if not candidates:
                    try:
                        history = fetch_nse(s, now-timedelta(days=180), now, fetcher)
                        candidates.extend(r['document_url'] for r in history['filings']
                                          if r['document_url'] and 'transcript' in (r['title']+r['description']).lower())
                        result['primary_discovery_lookback_days'] = 180
                    except Exception as exc:
                        result['primary_discovery_warning'] = str(exc)
                if data:
                    candidates.extend(d['url'] for d in data['documents'] if d['kind'] == 'transcript')
                errors = []
                for url in list(dict.fromkeys(candidates))[:3]:
                    try:
                        primary = resolve_transcript(url, fetcher)
                        store.put('primary_sample', s, primary)
                        store.finish_attempt(attempt, 'text_extracted', source_observed_at=primary['fetched_at'],
                                             url=primary['url'], quality=primary['quality'])
                        result['primary_sample'] = {k: v for k, v in primary.items() if k != 'pages'}
                        break
                    except Exception as exc:
                        errors.append(str(exc))
                if 'primary_sample' not in result:
                    result['primary_sample'] = {'status': 'unavailable', 'errors': errors}
                    store.finish_attempt(attempt, 'unavailable', errors=errors, error='No suitable full transcript found')
    finally:
        fetcher.close()
    result['source_fetch_ms'] = round((time.perf_counter()-started)*1000, 1)
    return s, result


def ingest_universe(store, force=False):
    fetcher = Fetcher(store, force=force or failed_previous_attempt(store, 'universe', 'NSE'))
    attempt = store.start_attempt('universe', 'NSE')
    try:
        res = fetcher.get(MASTER_URL, ttl=86400)
        try:
            companies = parse_master(res['body'].decode())
        except ValueError:
            store.invalidate_http(MASTER_URL)
            raise
        store.put('universe', 'NSE', {'companies': companies, 'sha256': res['sha256'],
                                     'source_url': MASTER_URL, 'fetched_at': res['fetched_at']})
        result = {'status': 'ok', 'companies': len(companies), 'cache_hit': res['cache_hit']}
        store.finish_attempt(attempt, 'ok', source_observed_at=res['fetched_at'], cache_hit=res['cache_hit'])
    except Exception as exc:
        result = {'status': 'unavailable', 'error': str(exc)}
        store.finish_attempt(attempt, 'unavailable', error=str(exc))
    finally:
        fetcher.close()
    return result


def main():
    parser = argparse.ArgumentParser(description='FINN Day 1 ingestion and source audit')
    parser.add_argument('--symbols', nargs='+', default=['TCS', 'HDFCBANK', 'LAURUSLABS', 'ASTRAL'])
    parser.add_argument('--portfolio', action='store_true')
    parser.add_argument('--db', default='data/finn.sqlite3')
    parser.add_argument('--output', default='data/runs/day1.json')
    parser.add_argument('--workers', type=int, choices=[1, 2, 3], default=1)
    parser.add_argument('--skip-market', action='store_true')
    parser.add_argument('--primary-sample', action='store_true')
    parser.add_argument('--force-refresh', action='store_true', help='Bypass TTL reuse; retain last-good snapshots on failure')
    args = parser.parse_args()
    tickers = PORTFOLIO if args.portfolio else list(dict.fromkeys(symbol(s) for s in args.symbols))
    store, now = Store(args.db), datetime.now(timezone.utc)
    report = {'started_at': now.isoformat(), 'symbols': {}, 'phase': 'day1', 'synthetic': False,
              'force_refresh': args.force_refresh}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        universe_future = pool.submit(ingest_universe, store, args.force_refresh)
        market_future = None if args.skip_market else pool.submit(fetch_market, tickers, now, store, args.force_refresh, True)
        futures = [pool.submit(ingest_company, s, store, now, None, args.primary_sample, args.force_refresh) for s in tickers]
        report['universe'] = universe_future.result()
        market = market_future.result() if market_future else {}
        for future in futures:
            s, result = future.result()
            if s in market:
                result['market'] = {k: v for k, v in market[s].items() if k != 'bars'}
            report['symbols'][s] = result
            print(json.dumps({s: result}), flush=True)
    report['finished_at'] = datetime.now(timezone.utc).isoformat()
    with store.connect() as db:
        report['database_integrity'] = db.execute('PRAGMA integrity_check').fetchone()[0]
    success = {'ok', 'cached', 'text_extracted'}
    failed = any(v.get('status') not in success for r in report['symbols'].values()
                 for k, v in r.items() if k in {'market', 'fundamentals', 'filings', 'primary_sample'})
    report['exit_code'] = 1 if failed or report['universe']['status'] != 'ok' or report['database_integrity'] != 'ok' else 0
    store.run(report)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    raise SystemExit(report['exit_code'])


if __name__ == '__main__':
    main()
