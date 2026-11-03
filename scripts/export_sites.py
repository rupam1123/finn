"""Export a consistent private SQLite backup and exact Python read models for Sites.

No provider/model calls. The original database is opened read-only and never modified.
Generated data is private, ignored by Git, and separate from schema migrations.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import sys
from datetime import datetime, timezone
from decimal import Decimal

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))


def encoded(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':'))


def export(source, output):
    output.mkdir(parents=True, exist_ok=False)
    backup = output / 'snapshot.sqlite3'
    with sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True) as original:
        with sqlite3.connect(backup) as target:
            original.backup(target)
    os.environ['FINN_DB'] = str(backup)
    os.environ['FINN_PUBLIC_REVIEW'] = '1'
    from finn.main import create_app
    from finn.storage import Store
    from finn.push import filing_card, analysis_key, digest, coverage
    from finn.workspace_api import annotate_quotes
    from finn.cross_signal import signals, alert_cutoff, finite
    from finn.market_data import indicators
    from finn.universe import PORTFOLIO, SHOWCASE, CATEGORIES
    from finn.calendar import CALENDAR
    from fastapi.testclient import TestClient

    store = Store(backup)
    now = datetime.now(timezone.utc)
    counts = {}
    handles = {}

    def row(table, values):
        if table not in handles:
            handles[table] = (output / (table + '.jsonl')).open('w', encoding='utf-8', newline='\n')
        handles[table].write(encoded(values) + '\n')
        counts[table] = counts.get(table, 0) + 1

    with store.connect() as db:
        tables = db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
        schema = [r['sql'] + ';' for r in tables]
        schema += [r['sql'] + ';' for r in db.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")]
        columns = {}
        for t in tables:
            name = t['name']
            counts[name] = 0
            handles[name] = (output / (name + '.jsonl')).open('w', encoding='utf-8', newline='\n')
            cols = [r['name'] for r in db.execute('PRAGMA table_info("' + name + '")')]
            columns[name] = cols
            if name == 'raw_responses':
                for r in db.execute('SELECT sha256,url,fetched_at FROM raw_responses ORDER BY sha256'):
                    row(name, [r['sha256'], r['url'], r['fetched_at'], None])
            else:
                for r in db.execute('SELECT * FROM "' + name + '"'):
                    row(name, [r[c] for c in cols])
        symbols = sorted(set(PORTFOLIO + SHOWCASE + [r[0] for r in db.execute("SELECT DISTINCT symbol FROM snapshots WHERE kind IN ('pull','market','fundamentals','primary_sample')")]))
        versions = [{**json.loads(r['payload']), **{k:r[k] for k in ('revision','observed_at','content_hash')}} for r in db.execute('SELECT * FROM filing_versions')]

    extra = {
        'read_documents': (['path','status','body'], 'path TEXT PRIMARY KEY,status INTEGER NOT NULL,body TEXT NOT NULL'),
        'read_cards': (['id','revision','symbol','published_at','observed_at','state_at','processed','payload'], 'id TEXT,revision INTEGER,symbol TEXT,published_at TEXT,observed_at TEXT,state_at TEXT,processed INTEGER,payload TEXT,PRIMARY KEY(id,revision,state_at)'),
        'read_sessions': (['id','symbol','cutoff','snapshot_at','payload','detail'], 'id TEXT PRIMARY KEY,symbol TEXT,cutoff TEXT,snapshot_at TEXT,payload TEXT,detail TEXT'),
        'read_quotes': (['sha256','page','quote_id','payload'], 'sha256 TEXT,page INTEGER,quote_id TEXT,payload TEXT,PRIMARY KEY(sha256,page,quote_id)'),
        'raw_objects': (['sha256','size','is_pdf'], 'sha256 TEXT PRIMARY KEY,size INTEGER,is_pdf INTEGER'),
        'read_meta': (['key','value'], 'key TEXT PRIMARY KEY,value TEXT NOT NULL'),
    }
    for name, (cols, definition) in extra.items():
        columns[name] = cols
        schema.append('CREATE TABLE IF NOT EXISTS ' + name + '(' + definition + ');')
    schema.append('CREATE TABLE IF NOT EXISTS imported_objects(sha256 TEXT PRIMARY KEY,size INTEGER NOT NULL);')

    client = TestClient(create_app(backup))
    for path in ['/api/portfolio', '/api/portfolio/overview'] + [f'/api/{kind}/{s}' for s in symbols for kind in ['company','market','primary','pull']] + [f'/api/pull/{s}/jobs' for s in symbols]:
        response = client.get(path)
        row('read_documents', [path, response.status_code, encoded(response.json())])

    # Retain card states at every visibility boundary, including older revisions.
    for filing in versions:
        saved = store.get('push_analysis', analysis_key(filing))
        attempt = store.last_attempt('push_analysis', analysis_key(filing))
        points = {filing['observed_at']}
        if saved: points.add(saved['fetched_at'])
        if attempt: points.add(attempt['finished_at'] or attempt['started_at'])
        for point in sorted(points):
            end = datetime.fromisoformat(point)
            if end < datetime.fromisoformat(filing['observed_at']) or end > now:
                continue
            card, processed = filing_card(store, filing, end)
            row('read_cards', [filing['id'],filing['revision'],filing['symbol'],filing['published_at'],filing['observed_at'],point,int(processed),encoded(annotate_quotes(card))])

    for symbol in symbols:
        snapshot = store.get('market', symbol)
        if not snapshot: continue
        bars = sorted(snapshot['data'].get('indicator_history') or snapshot['data'].get('bars', []), key=lambda b:b['date'])
        for i, bar in enumerate(bars):
            cutoff = alert_cutoff(bar['date'])
            if cutoff > now: continue
            stats = indicators(bars[:i+1])
            candidates = signals(snapshot, [], cutoff, now, 1e-100, 1e-100)
            core = next((a for a in candidates if a['session'] == bar['date']), None)
            item = {
                'indicators':stats,'core':core,
                'price_evaluable':finite(stats['return_1d_pct']),
                'volume_evaluable':finite(stats['volume_ratio_20d']),
                'current':str(bar.get('adjusted_close',0)),
                'previous':str(bars[i-1].get('adjusted_close',0)) if i else '0',
                'volume':str(bar.get('volume',0)),
                'prior_volume_sum':str(sum(Decimal(str(b['volume'])) for b in bars[max(0,i-20):i])),
            }
            detail = {'bars':bars[max(0,i-29):i+1], 'volume_baseline':bars[max(0,i-20):i+1], 'baseline_policy':'20 prior completed sessions, excluding the trigger session'}
            row('read_sessions', [symbol+':'+bar['date'],symbol,cutoff.isoformat(),snapshot['fetched_at'],encoded(item),encoded(detail)])

    seen = set()
    def quotes(value):
        if isinstance(value, dict):
            quote, sha, page = value.get('quote'), value.get('sha256'), value.get('page')
            if isinstance(quote,str) and sha and page:
                qid = hashlib.sha256(quote.encode()).hexdigest()
                key = (sha,page,qid)
                if key not in seen:
                    seen.add(key)
                    row('read_quotes',[sha,page,qid,encoded(value)])
            for child in value.values(): quotes(child)
        elif isinstance(value,list):
            for child in value: quotes(child)
    with store.connect() as db:
        for r in db.execute("SELECT payload FROM snapshots WHERE kind IN ('pull','push_analysis') ORDER BY fetched_at DESC"):
            quotes(json.loads(r['payload']))
        raw_count = 0
        raw_bytes = 0
        for r in db.execute('SELECT sha256,length(body) AS size,substr(body,1,4) AS magic FROM raw_responses ORDER BY sha256'):
            row('raw_objects', [r['sha256'],r['size'],int(r['magic'] == b'%PDF')])
            raw_count += 1; raw_bytes += r['size']

    base = digest(store,'1d',as_of=now)
    for key in ['cards','buried','market_alerts','coverage','announcement_alerts','counts']:
        base.pop(key, None)
    sources = {s:{kind:{'coverage':coverage(store,kind,s,now),'snapshot_at':(store.get(kind,s) or {}).get('fetched_at'),'ttl':(store.get(kind,s) or {}).get('ttl_seconds'), 'actual_session':((store.get(kind,s) or {}).get('data') or {}).get('indicators',{}).get('as_of')} for kind in ['market','filings_coverage']} for s in symbols}
    for key, val in {'exported_at':now.isoformat(),'calendar':CALENDAR,'portfolio':PORTFOLIO,'showcase':SHOWCASE,'categories':CATEGORIES,'digest_template':base,'sources':sources}.items():
        row('read_meta',[key,encoded(val)])
    for handle in handles.values(): handle.close()
    migration = ROOT/'hosting/drizzle/0000_finn.sql'
    migration.write_text('\n--> statement-breakpoint\n'.join(schema)+'\n', encoding='utf-8')
    (ROOT/'hosting/drizzle/meta/_journal.json').write_text(encoded({'version':'7','dialect':'sqlite','entries':[{'idx':0,'version':'6','when':int(now.timestamp()*1000),'tag':'0000_finn','breakpoints':True}]})+'\n')
    (ROOT/'hosting/backend').mkdir(exist_ok=True)
    (ROOT/'hosting/backend/import-schema.json').write_text(encoded(columns)+'\n')
    manifest = {'exported_at':now.isoformat(),'source_backup':str(backup),'tables':counts,'columns':columns,'raw_objects':raw_count,'raw_bytes':raw_bytes,'symbols':symbols,'quote_count':len(seen)}
    (output/'manifest.json').write_text(encoded(manifest)+'\n',encoding='utf-8')
    print(encoded({k:v for k,v in manifest.items() if k not in ['columns','source_backup']}), flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',type=Path,default=ROOT/'data/finn.sqlite3')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    export(args.db,args.output)
