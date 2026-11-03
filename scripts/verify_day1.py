"""Audit saved source bytes and arithmetic; optionally exercise a running HTTP API.

Run from the project root. Does not refresh or modify the database.
"""
import argparse
import hashlib
import json
import math
import sqlite3
import statistics
import time
import csv
import io
import zipfile
from collections.abc import Mapping
from contextlib import closing
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener
from zoneinfo import ZoneInfo


class RawSources(Mapping):
    """Read the large raw cache one object at a time."""
    def __init__(self,db):self.db=db
    def __getitem__(self,key):
        row=self.db.execute('SELECT body FROM raw_responses WHERE sha256=?',(key,)).fetchone()
        if row is None:raise KeyError(key)
        return row[0]
    def __iter__(self):return (r[0] for r in self.db.execute('SELECT sha256 FROM raw_responses'))
    def __len__(self):return self.db.execute('SELECT count(*) FROM raw_responses').fetchone()[0]
    def __contains__(self,key):return self.db.execute('SELECT 1 FROM raw_responses WHERE sha256=?',(key,)).fetchone() is not None
    def items(self):return iter(self.db.execute('SELECT sha256,body FROM raw_responses'))


def source_alignment(data,raw):
    """Audit original Yahoo/NSE bytes independently of derived-series JSON."""
    try:
        fields={'open':'Open','high':'High','low':'Low','close':'Close','adjusted_close':'Adj Close','volume':'Volume','dividend':'Dividends','split':'Stock Splits'}
        bars=data['bars'];source=json.loads(raw[data['sha256']]);same=lambda a,b:math.isclose(float(a),float(b),rel_tol=1e-10,abs_tol=1e-8)
        if 'data' in source:
            rows={r['Date'][:10]:r for r in source['data']}
            return all(b['date'] in rows and all(same(b[k],rows[b['date']][v]) for k,v in fields.items()) for b in bars)
        history=data['indicator_history']
        if source.get('bars')!=history or history[-30:]!=bars:return False
        inputs=data['input_provenance'];yahoo=next(x for x in inputs if x['url'].startswith('https://finance.yahoo.com/'))
        bhav=next(x for x in inputs if '/BhavCopy_NSE_CM_' in x['url']);actions=next(x for x in inputs if '/api/corporates-corporateActions?' in x['url'])
        if source.get('inputs')!=[bhav['sha256'],actions['sha256']]:return False
        rows={r['Date'][:10]:r for r in json.loads(raw[yahoo['sha256']])['data']}
        if not all(b['date'] in rows and all(same(b[k],rows[b['date']][v]) for k,v in fields.items()) for b in history[:-1]):return False
        session=bars[-1]['date'];prior=bars[-2]
        with zipfile.ZipFile(io.BytesIO(raw[bhav['sha256']])) as archive:
            names=[i for i in archive.infolist() if i.filename.lower().endswith('.csv')]
            if len(names)!=1 or names[0].file_size>25_000_000:return False
            records=list(csv.DictReader(io.StringIO(archive.read(names[0]).decode('utf-8-sig'))))
        matches=[r for r in records if r['TckrSymb']==data['symbol'] and r['TradDt']==session and r['SctySrs']=='EQ' and r['Sgmt']=='CM']
        if len(matches)!=1:return False
        row=matches[0];exchange={'open':'OpnPric','high':'HghPric','low':'LwPric','close':'ClsPric','volume':'TtlTradgVol'}
        if not all(same(bars[-1][k],row[v]) for k,v in exchange.items()):return False
        if bars[-1].get('split')!=0 or bars[-1].get('dividend')!=0:return False
        if not same(bars[-1]['adjusted_close'],bars[-1]['close']) or not same(prior['adjusted_close'],prior['close']):return False
        if abs(Decimal(str(prior['close']))-Decimal(row['PrvsClsgPric']))>Decimal('.02'):return False
        action_rows=json.loads(raw[actions['sha256']])
        if not isinstance(action_rows,list):return False
        for action in action_rows:
            if action.get('symbol')==data['symbol']:
                ex=datetime.strptime(action['exDate'],'%d-%b-%Y').date().isoformat()
                if prior['date']<ex<=session:return False
        return True
    except (ValueError,KeyError,TypeError,StopIteration,IndexError,zipfile.BadZipFile):return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default='data/finn.sqlite3')
    parser.add_argument('--out', default='verification/local-check')
    parser.add_argument('--base-url')
    parser.add_argument('--frontend-url')
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'checks': [],
              'scope': 'Stored-source consistency, not independent exchange certification'}

    def check(name, ok, detail=None):
        report['checks'].append({'name': name, 'passed': bool(ok), 'detail': detail})

    def save(name, value):
        (out / name).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')

    with closing(sqlite3.connect(Path(args.db).resolve().as_uri() + '?mode=ro', uri=True)) as db:
        integrity = db.execute('PRAGMA integrity_check').fetchone()[0]
        check('SQLite integrity', integrity == 'ok', integrity)
        raw = RawSources(db)
        check('Raw object SHA-256 verification', all(hashlib.sha256(b).hexdigest() == h for h, b in raw.items()), len(raw))
        snapshots = {(k, s): json.loads(p) for k, s, p in db.execute('SELECT kind,symbol,payload FROM snapshots')}
        check('Snapshot references resolve to source bytes', all(d['sha256'] in raw for d in snapshots.values() if 'sha256' in d))
        report['snapshot_counts'] = dict(db.execute('SELECT kind,count(*) FROM snapshots GROUP BY kind'))
        report['filing_count'] = db.execute('SELECT count(*) FROM filings').fetchone()[0]
        computed = {}
        for (kind, symbol), data in snapshots.items():
            if kind != 'market':
                continue
            bars = data['bars']
            dates = [b['date'] for b in bars]
            check(f'{symbol}: 30 ordered unique sessions', len(bars) == 30 and dates == sorted(set(dates)))
            check(f'{symbol}: all stored bars match saved source bytes',source_alignment(data,raw))
            dec = lambda value: Decimal(str(value))
            latest = dec(bars[-1]['adjusted_close'])
            baseline = sum(dec(b['volume']) for b in bars[-21:-1]) / Decimal(20)
            expected = {'return_1d_pct': (latest / dec(bars[-2]['adjusted_close']) - 1) * 100,
                        'return_5d_pct': (latest / dec(bars[-6]['adjusted_close']) - 1) * 100,
                        'volume_ratio_20d': dec(bars[-1]['volume']) / baseline if baseline > 0 and not any(b['split'] for b in bars[-21:]) else None}
            for key, value in expected.items():
                actual = data['indicators'][key]
                check(f'{symbol}: independent {key}', actual is None if value is None else actual is not None and math.isclose(float(value), actual, rel_tol=1e-10, abs_tol=1e-10))
            computed[symbol] = {'as_of': dates[-1], 'last_close': bars[-1]['close'],
                                'last_adjusted_close': str(latest), 'previous_adjusted_close': str(bars[-2]['adjusted_close']),
                                'five_sessions_ago_adjusted_close': str(bars[-6]['adjusted_close']),
                                'volume': bars[-1]['volume'], 'prior20_mean_volume': str(baseline),
                                'independent': {k: str(v) if v is not None else None for k, v in expected.items()},
                                'source_url': data['source_url']}
        save('market-recalculation.json', computed)
        bad_timestamps = []
        for row, in db.execute('SELECT payload FROM filings'):
            filing = json.loads(row)
            published = filing['raw'].get('exchdisstime') or filing['raw'].get('an_dt')
            parsed = datetime.strptime(published, '%d-%b-%Y %H:%M:%S').replace(tzinfo=ZoneInfo('Asia/Kolkata')).astimezone(timezone.utc)
            if parsed != datetime.fromisoformat(filing['published_at']):
                bad_timestamps.append(filing['id'])
        check('Filing dissemination IST to UTC conversion', not bad_timestamps, bad_timestamps)
        from finn.pdf_runtime import pymupdf
        for (kind, symbol), data in snapshots.items():
            if kind != 'primary_sample':
                continue
            body = raw[data['sha256']]
            with pymupdf.open(stream=body, filetype='pdf') as pdf:
                check(f'{symbol}: PDF page count and extracted text match saved bytes',
                      len(pdf) == data['page_count'] == len(data['pages']) and all(
                          p['page'] == i + 1 and p['text'] == pdf[i].get_text() for i, p in enumerate(data['pages'])), data['page_count'])
            check(f'{symbol}: no verified-claim flag', data['claims_verified'] is False)
            (out / f'{symbol}-primary.pdf').write_bytes(body)
            save(f'{symbol}-primary.json', data)
        # An independent HTML read of selected fields, without the application parser.
        from bs4 import BeautifulSoup
        tcs = snapshots[('fundamentals', 'TCS')]
        soup = BeautifulSoup(raw[tcs['sha256']], 'html.parser')
        comparisons = []
        for label in ['Sales', 'Net Profit', 'EPS in Rs']:
            parsed = next(r for r in tcs['tables']['quarters']['rows'] if r['label'] == label)
            tr = next(tr for tr in soup.select('#quarters tbody tr') if tr.find('td') and tr.find('td').get_text(' ', strip=True).rstrip(' +') == label)
            source_values = [td.get_text(' ', strip=True) for td in tr.find_all('td', recursive=False)[1:]]
            check(f'TCS: {label} source HTML alignment', source_values == [v['raw'] for v in parsed['values']])
            comparisons.append({'label': label, 'unit': parsed['unit'], 'last_period': tcs['tables']['quarters']['periods'][-1], 'source_value': source_values[-1], 'stored_value': parsed['values'][-1]['value']})
        save('tcs-table-spotcheck.json', comparisons)

    if args.base_url:
        opener = build_opener(ProxyHandler({}))
        paths = [('/health', 200), ('/api/portfolio', 200), ('/api/universe?q=ASTRAL', 200)]
        paths += [(f'/api/{kind}/{s}' + ('?days=30' if kind == 'filings' else ''), 200)
                  for s in ['TCS', 'HDFCBANK', 'LAURUSLABS', 'ASTRAL'] for kind in ['company', 'market', 'filings']]
        paths += [('/api/company/ZZZZNOTREAL', 404), ('/api/company/TATAMOTORS', 422),
                  ('/api/filings/TCS?days=31', 422), ('/api/filings/TCS?days=0', 422),
                  ('/api/company/ZOMATO', 200), ('/api/company/TCS.NS', 200), ('/api/push/digest', 200)]
        responses = []
        for path, expected in paths:
            started = time.perf_counter()
            try:
                response = opener.open(Request(args.base_url.rstrip('/') + path, headers={'Origin': 'http://localhost:3000'}), timeout=10)
            except HTTPError as exc:
                response = exc
            with response:
                body = json.loads(response.read())
                cors = response.headers.get('Access-Control-Allow-Origin')
                responses.append({'path': path, 'status': response.status, 'cors': cors, 'elapsed_ms': round((time.perf_counter()-started)*1000, 3), 'body': body})
                check(f'HTTP {path}', response.status == expected and cors == 'http://localhost:3000', response.status)
        save('api-responses.json', responses)
        latencies = []
        for _ in range(20):
            started = time.perf_counter()
            with opener.open(args.base_url.rstrip('/') + '/api/company/ASTRAL', timeout=10) as response:
                response.read()
                check('Warm HTTP status', response.status == 200)
            latencies.append((time.perf_counter()-started)*1000)
        report['warm_http_ms'] = {'samples': 20, 'median': statistics.median(latencies), 'max': max(latencies), 'scope': 'local HTTP; no browser, mobile or remote network'}
        if args.frontend_url:
            with opener.open(args.frontend_url, timeout=10) as response:
                html = response.read().decode()
                check('Frontend serves Day 1 shell over HTTP', response.status == 200 and 'Start with' in html and 'NSE symbol' in html)
                (out / 'frontend.html').write_text(html, encoding='utf-8')
        report['api_transport'] = 'real HTTP'
    else:
        report['api_transport'] = 'not tested; supply --base-url to exercise the running API'
    report['passed'] = all(c['passed'] for c in report['checks'])
    save('summary.json', report)
    print(json.dumps({'passed': report['passed'], 'checks': len(report['checks']), 'failures': [c for c in report['checks'] if not c['passed']], 'report': str(out / 'summary.json')}, indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
