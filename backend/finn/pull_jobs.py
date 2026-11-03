"""Durable queue with explicit single-worker CLI and restart recovery."""
import argparse
import json
import uuid
import time
from datetime import datetime,timedelta,timezone
from .storage import Store, now_iso
from .pull import research
from .universe import symbol


def initialize(store):
    with store.connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS pull_jobs(id TEXT PRIMARY KEY,symbol TEXT,status TEXT,updated_at TEXT,payload TEXT)')
        db.execute('CREATE TABLE IF NOT EXISTS api_job_budget(requested_at TEXT NOT NULL)')
        db.execute('DELETE FROM api_job_budget WHERE requested_at<?',((datetime.now(timezone.utc)-timedelta(days=1)).isoformat(),))


class QueueLimit(ValueError):
    pass


def enqueue(store,ticker,refresh=False,api_budget=False):
    ticker=symbol(ticker)
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute("SELECT * FROM pull_jobs WHERE symbol=? AND status IN ('queued','running')",(ticker,)).fetchone()
        if row:
            return dict(row)
        if api_budget:
            now=datetime.now(timezone.utc)
            day=(now-timedelta(days=1)).isoformat();hour=(now-timedelta(hours=1)).isoformat()
            db.execute('DELETE FROM api_job_budget WHERE requested_at<?',(day,))
            active=db.execute("SELECT count(*) FROM pull_jobs WHERE status IN ('queued','running')").fetchone()[0]
            daily=db.execute('SELECT count(*) FROM api_job_budget').fetchone()[0]
            hourly=db.execute('SELECT count(*) FROM api_job_budget WHERE requested_at>=?',(hour,)).fetchone()[0]
            if active>=6 or hourly>=12 or daily>=48:
                raise QueueLimit('Research queue budget reached. Reuse saved research and try again later.')
            # Global counts only. No IP, browser identifier or visitor query log.
            db.execute('INSERT INTO api_job_budget VALUES(?)',(now.isoformat(),))
        job={'id':uuid.uuid4().hex,'symbol':ticker,'status':'queued','updated_at':now_iso(),
             'payload':json.dumps({'refresh':refresh,'stage':'queued'})}
        db.execute('INSERT INTO pull_jobs VALUES(:id,:symbol,:status,:updated_at,:payload)',job)
        return job


def get_job(store,job_id):
    with store.connect() as db:
        row=db.execute('SELECT * FROM pull_jobs WHERE id=?',(job_id,)).fetchone()
    if not row:
        return None
    result=dict(row); result['payload']=json.loads(result['payload'])
    return result


def run_one(store,model=None):
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute("SELECT * FROM pull_jobs WHERE status='queued' ORDER BY updated_at LIMIT 1").fetchone()
        if not row:
            return False
        db.execute("UPDATE pull_jobs SET status='running',updated_at=? WHERE id=?",(now_iso(),row['id']))
    options=json.loads(row['payload'])
    def emit(event):
        with store.connect() as db:
            db.execute('UPDATE pull_jobs SET updated_at=?,payload=? WHERE id=?',(now_iso(),json.dumps(event),row['id']))
    try:
        kwargs = {}
        if options.get('refresh'): kwargs['force'] = True
        if model is not None: kwargs['model'] = model
        result=research(row['symbol'],store,emit,**kwargs)
        status=result['status']
        emit({'stage':'finished','research_status':status})
    except Exception:
        status='failed'; emit({'error':'Research failed. Check source availability and the local worker diagnostics.'})
    with store.connect() as db:
        db.execute('UPDATE pull_jobs SET status=?,updated_at=? WHERE id=?',(status,now_iso(),row['id']))
    return True


def main():
    from .settings import load_local_settings
    load_local_settings()
    p=argparse.ArgumentParser(); p.add_argument('--db',default='data/finn.sqlite3'); p.add_argument('--recover',action='store_true'); p.add_argument('--watch',action='store_true')
    p.add_argument('--use-model',action='store_true',help='Use server-side Gemini credentials; never expose them in the browser')
    args=p.parse_args(); store=Store(args.db); initialize(store)
    from .model import Flash
    model=Flash() if args.use_model else None
    if model is not None and not model.configured: p.error('--use-model requires GEMINI_API_KEY in the worker environment')
    if args.recover:
        with store.connect() as db:
            db.execute("UPDATE pull_jobs SET status='queued',payload=? WHERE status='running'",(json.dumps({'refresh':True,'stage':'recovered'}),))
    while True:
        if not run_one(store,model):
            if not args.watch: break
            time.sleep(2)

if __name__=='__main__': main()
