"""Final local Day 1–3 validation. Credentials and DB backups stay private."""
import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from contextlib import closing
from datetime import datetime,timezone
from pathlib import Path


def main():
    root=Path(__file__).resolve().parents[1]
    from finn.settings import load_local_settings
    from finn.validation import REVIEW_FILES,create_review_bundle
    load_local_settings(root/'.env')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',default=os.getenv('FINN_DB','data/finn.sqlite3'))
    parser.add_argument('--use-model',action='store_true')
    parser.add_argument('--out',default='verification/day3-final-local')
    parser.add_argument('--skip-build',action='store_true')
    args=parser.parse_args();out=(root/args.out).resolve();out.mkdir(parents=True,exist_ok=True)
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    previous=[out/name for name in REVIEW_FILES+('day3_verification.zip',) if (out/name).is_file()]
    for path in previous:
        saved=out/'previous-runs'/run_id/path.relative_to(out);saved.parent.mkdir(parents=True,exist_ok=True);shutil.move(path,saved)
    db=(root/args.db).resolve();env=dict(os.environ,FINN_DB=str(db));checks=[];use_model=False

    def finish():
        result={'run_id':run_id,'finished_at':datetime.now(timezone.utc).isoformat(),'checks':checks,
                'model_requested':args.use_model,'model_preflight_passed':use_model if args.use_model else None,
                'frontend_checks_skipped':args.skip_build,'passed':bool(checks) and all(c['exit_code']==0 for c in checks),
                'note':'Review acceptance and primary claims. Mechanical checks are not independent semantic certification.'}
        (out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
        print('Share '+str(create_review_bundle(out))+'; credentials and database backups are excluded.')
        raise SystemExit(0 if result['passed'] else 1)

    if not db.is_file():
        checks.append({'name':'existing-database','exit_code':1,'error':'Database not found. Check --db; no empty replacement was created.'});finish()
    use_model=args.use_model and bool(env.get('GEMINI_API_KEY'))
    if args.use_model and not use_model:
        report={'passed':False,'error':'No private local GEMINI_API_KEY configured. Keep the key local; no model calls were made.'}
        (out/'model-preflight.json').write_text(json.dumps(report,indent=2));checks.append({'name':'model-preflight','exit_code':1})
    if use_model:
        from finn.model import Flash,Reasoner
        from finn.validation import model_preflight
        try:report=model_preflight([Flash(),Reasoner()])
        except Exception as exc:report={'passed':False,'error':str(exc)}
        use_model=report['passed']
        (out/'model-preflight.json').write_text(json.dumps(report,indent=2))
        checks.append({'name':'model-preflight','exit_code':0 if use_model else 1})
    if args.use_model and not use_model:
        print('Model preflight failed. Stopped before database backup, builds, ingestion or model-free reprocessing.',flush=True)
        finish()
    try:
        backup=out/('database-before-validation-'+run_id+'.sqlite3')
        with closing(sqlite3.connect(db.as_uri()+'?mode=ro',uri=True)) as src,closing(sqlite3.connect(backup)) as dst:
            if src.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('Database integrity check failed')
            src.backup(dst)
        checks.append({'name':'database-backup','exit_code':0})
    except (sqlite3.Error,OSError,ValueError) as exc:
        checks.append({'name':'database-backup','exit_code':1,'error':str(exc)});finish()

    def run(name,command,cwd=root):
        print(name,flush=True)
        with (out/(name+'.log')).open('w',encoding='utf-8') as log:
            try:
                shell=os.name=='nt' and Path(command[0]).suffix.lower() in {'.cmd','.bat'}
                if name in {'warm-primary-cache','primary-research'}:
                    with subprocess.Popen(command,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                                          text=True,encoding='utf-8',errors='replace',shell=shell) as process:
                        for line in process.stdout:
                            log.write(line);log.flush();print(line.rstrip(),flush=True)
                        code=process.wait()
                else:
                    code=subprocess.run(command,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,check=False,shell=shell).returncode
            except OSError as exc:log.write(str(exc));code=127
        checks.append({'name':name,'exit_code':code});return code

    run('backend-tests',[sys.executable,'-m','pytest','backend/tests','-q'])
    npm=shutil.which('npm')
    if not args.skip_build:
        if not npm:checks.append({'name':'frontend-tools','exit_code':127})
        else:
            if not (root/'frontend/node_modules').exists():run('frontend-install',[npm,'ci'],root/'frontend')
            run('frontend-build',[npm,'run','build','--','--webpack'],root/'frontend')
            run('frontend-typecheck',[npm,'run','typecheck'],root/'frontend')
            run('frontend-races',[npm,'run','test:pull-races'],root/'frontend')
    if any(c['exit_code'] for c in checks if c['name']!='model-preflight'):finish()
    run('portfolio-ingestion',[sys.executable,'-m','finn.cli','--portfolio','--db',str(db),'--workers','3','--force-refresh','--output',str(out/'portfolio.json')])
    run('day1-source-audit',[sys.executable,'scripts/verify_day1.py','--db',str(db),'--out',str(out/'day1-audit')])
    push=[sys.executable,'-m','finn.push_ingest','--db',str(db),'--days','30','--workers','1' if use_model else '3']
    if use_model:push.append('--use-model')
    run('push-processing',push)
    if use_model:
        from finn.storage import Store
        from finn.classifier import classify
        from finn.push import analysis_key
        from finn.validation import push_model_check
        from datetime import timedelta
        from finn.universe import PORTFOLIO
        store=Store(db);end=datetime.now(timezone.utc)
        candidates=[f for ticker in PORTFOLIO for f in store.filings(ticker,end-timedelta(days=30),end)]
        selected=[]
        for category in ('results','management_change','M&A','litigation'):
            selected.extend(sorted((f for f in candidates if classify(f)['category']==category),key=lambda f:f['published_at'],reverse=True)[:2])
        diagnostics=[]
        for filing in {f['id']:f for f in selected}.values():
            saved=store.get('push_analysis',analysis_key(filing))
            diagnostics.append({'id':filing['id'],'symbol':filing['symbol'],**push_model_check(saved['data'] if saved else None),
                                'analysis':saved['data'] if saved else None})
        (out/'live-model-push.json').write_text(json.dumps({'scope':'Review sample from full-corpus model processing','validation':diagnostics},indent=2))
        checks.append({'name':'live-model-push','exit_code':0 if diagnostics and all(r['passed'] for r in diagnostics) else 1})
    run('warm-primary-cache',[sys.executable,'-m','finn.pull','--db',str(db),'--warm','--output',str(out/'warm.json')])
    pull=[sys.executable,'-m','finn.pull','--db',str(db),'--symbols','INFY','DEEPAKNTR','HDFCBANK','KPIL','--output',str(out/'research.json')]
    if use_model:pull.append('--use-model')
    run('primary-research',pull)
    run('cold-http-worker',[sys.executable,'scripts/verify_worker_http.py','--symbol','HAVELLS','--out',str(out/'cold-http.json')])
    run('source-audit',[sys.executable,'scripts/verify_pull_sources.py','--db',str(db),'--out',str(out/'source-audit.json')])
    run('push-audit',[sys.executable,'scripts/verify_day2.py','--db',str(db),'--out',str(out/'push-audit.json')])
    run('acceptance',[sys.executable,'scripts/verify_day3.py','--db',str(db),'--out',str(out/'acceptance.json')])
    finish()


if __name__=='__main__':main()

