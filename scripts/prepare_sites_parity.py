"""Build private local D1-shaped data and capture original API responses for comparison."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import sqlite3
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--export',type=Path,required=True)
parser.add_argument('--reuse-db',action='store_true')
args=parser.parse_args()
manifest=json.loads((args.export/'manifest.json').read_text())
target=args.export/'ported.sqlite3'
if target.exists() and not args.reuse_db:raise SystemExit('Preserving existing parity database; select --reuse-db after checking this export')
if not target.exists():
    with sqlite3.connect(target) as db:
        db.executescript((ROOT/'hosting/drizzle/0000_finn.sql').read_text().replace('--> statement-breakpoint',''))
        for table,cols in manifest['columns'].items():
            sql='INSERT INTO "'+table+'"('+','.join('"'+c+'"' for c in cols)+') VALUES('+','.join('?' for _ in cols)+')'
            with (args.export/(table+'.jsonl')).open(encoding='utf-8') as f:
                db.executemany(sql,(json.loads(line) for line in f))
        db.execute("INSERT INTO read_meta(key,value) VALUES('ready','true')")
else:
    with sqlite3.connect(target) as db:
        assert json.loads(db.execute("SELECT value FROM read_meta WHERE key='exported_at'").fetchone()[0])==manifest['exported_at']
os.environ['FINN_DB']=manifest['source_backup']
os.environ['FINN_PUBLIC_REVIEW']='1'
from finn.main import create_app
from fastapi.testclient import TestClient
clock=datetime.fromisoformat(manifest['exported_at'])
class Frozen(datetime):
    @classmethod
    def now(cls,tz=None):return clock.astimezone(tz) if tz else clock.replace(tzinfo=None)
paths=['/api/capabilities','/api/universe']
with sqlite3.connect(target) as db:
    paths += [r[0] for r in db.execute('SELECT path FROM read_documents ORDER BY path')]
    for r in db.execute('SELECT id FROM read_cards GROUP BY id LIMIT 12'):
        paths.append('/api/push/filing/'+r[0])
    for r in db.execute("SELECT id FROM read_sessions WHERE json_extract(payload,'$.core') IS NOT NULL ORDER BY cutoff DESC LIMIT 12"):
        paths.append('/api/push/alert/'+r[0]+'?price_threshold=0.5&vol_threshold=1.2')
    for r in db.execute('SELECT sha256,page,quote_id FROM read_quotes LIMIT 12'):
        paths.append(f'/api/evidence/{r[0]}/metadata?page={r[1]}&quote_id={r[2]}')
    for r in db.execute('SELECT sha256 FROM raw_objects WHERE is_pdf=1 LIMIT 3'):
        paths.append('/api/evidence/'+r[0]+'.pdf')
for q in ['TCS','TATA','hdfc','infosis','ZOMATO','A','ZZZZZZ','RELIANCE']:
    paths.append('/api/universe?q='+q)
for window in ['1d','3d','7d','30d','latest']:
    for p,v in [(3,2),(.5,1.2),(10,5)]:
        for watch in ['', '&watch_categories=']:
            paths.append(f'/api/push/digest?window={window}&price_threshold={p}&vol_threshold={v}'+watch)
for s in manifest['symbols']:
    paths.append('/api/push/company/'+s+'?window=30d')
for past in ['2026-10-28T15:00:00+00:00','2026-10-30T15:00:00+00:00','2026-11-02T15:00:00+00:00']:
    from urllib.parse import quote
    paths.append('/api/push/digest?window=30d&as_of='+quote(past))
paths += ['/api/filings/TCS?days=30','/api/company/ZOMATO','/api/market/TATAMOTORS','/api/push/digest?price_threshold=NaN','/api/push/digest?watch_categories=bad','/api/evidence/bad.pdf']
cases=[]
app=create_app(manifest['source_backup'])
with patch('finn.main.datetime',Frozen),patch('finn.storage.datetime',Frozen),patch('finn.push.datetime',Frozen),patch('finn.workspace_api.datetime',Frozen):
    client=TestClient(app)
    for path in paths:
        r=client.get(path)
        if path.endswith('.pdf') and r.status_code==200:
            import hashlib
            body={'sha256':hashlib.sha256(r.content).hexdigest(),'size':len(r.content)}
        else:body=r.json()
        cases.append({'path':path,'status':r.status_code,'body':body})
(args.export/'parity-cases.json').write_text(json.dumps({'clock':manifest['exported_at'],'cases':cases},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print(json.dumps({'cases':len(cases),'database':str(target),'scope':'Original saved Python API; no provider/model requests'}))
