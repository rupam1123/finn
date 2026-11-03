"""Run real HTTP and React/jsdom integration checks in one local process session.
Uses a temporary copy of the selected DB; the diagnostic outage never enters it.
"""
import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from contextlib import closing
from pathlib import Path
from urllib.request import ProxyHandler, build_opener

from finn.storage import Store


def copy_database(source_path, destination_path):
    source_uri = Path(source_path).resolve(strict=True).as_uri() + '?mode=ro'
    with closing(sqlite3.connect(source_uri, uri=True)) as source:
        with closing(sqlite3.connect(destination_path)) as destination:
            source.backup(destination)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--db',default='data/finn.sqlite3')
    parser.add_argument('--out',default='verification/reliability/integration')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True)
    report={'scope':'Real HTTP plus React component in jsdom; synthetic outage metadata only in a temporary DB','checks':[]}
    processes=[];logs=[]
    with tempfile.TemporaryDirectory() as temp:
        db=Path(temp)/'integration.sqlite3'
        copy_database(args.db, db)
        store=Store(db)
        attempt=store.start_attempt('fundamentals','HDFCBANK')
        store.finish_attempt(attempt,'unavailable',error='diagnostic source outage')
        env={**os.environ,'FINN_DB':str(db),'FINN_ALLOWED_ORIGINS':'http://localhost:3000','FINN_TEST_API':'http://127.0.0.1:8000'}
        npm=shutil.which('npm.cmd' if os.name=='nt' else 'npm')
        if not npm:raise RuntimeError('npm is required')
        opener=build_opener(ProxyHandler({}))
        try:
            for name,cmd,cwd,url in [
                ('backend',[sys.executable,'-m','uvicorn','finn.main:app','--host','127.0.0.1','--port','8000'],root,'http://127.0.0.1:8000/health'),
                ('frontend',[npm,'run','start','--','--hostname','127.0.0.1'],root/'frontend','http://127.0.0.1:3000')]:
                log=open(out/(name+'.txt'),'w',encoding='utf-8');logs.append(log)
                process=subprocess.Popen(cmd,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT);processes.append(process)
                for _ in range(80):
                    if process.poll() is not None:raise RuntimeError(name+' exited before startup; check log or port conflict')
                    try:
                        with opener.open(url,timeout=1) as response:
                            if response.status==200:break
                    except Exception:time.sleep(.25)
                else:raise RuntimeError(name+' startup timeout')
                time.sleep(.1)
                if process.poll() is not None:raise RuntimeError(name+' port may already be in use')
            commands=[('data-http',[sys.executable,'scripts/verify_day1.py','--db',str(db),'--out',str(out/'http'),'--base-url','http://127.0.0.1:8000','--frontend-url','http://127.0.0.1:3000'],root),
                      ('react',[npm,'run','test:integration'],root/'frontend'),
                      ('pull-react',[shutil.which('node'),'--import','tsx','tests/pull-integration.mjs'],root/'frontend'),
                      ('push-http',[sys.executable,'scripts/verify_day2.py','--db',str(db),'--base-url','http://127.0.0.1:8000','--out',str(out/'day2-audit.json')],root)]
            for name,cmd,cwd in commands:
                result=subprocess.run(cmd,cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
                (out/(name+'.txt')).write_text(result.stdout+result.stderr,encoding='utf-8')
                report['checks'].append({'name':name,'passed':result.returncode==0,'exit_code':result.returncode})
            for symbol in ['TCS','HDFCBANK','LAURUSLABS','ASTRAL']:
                with opener.open('http://127.0.0.1:8000/api/primary/'+symbol,timeout=10) as response:
                    primary=json.load(response)
                report['checks'].append({'name':symbol+' primary API','passed':primary['data']['quality']['status']=='transcript_candidate',
                                         'pages':primary['data']['page_count']})
            with opener.open('http://127.0.0.1:8000/api/market/TCS',timeout=10) as response:
                market=json.load(response)
            (out/'market-api.json').write_text(json.dumps(market,indent=2))
            report['checks'].append({'name':'market last refresh visible','passed':market['last_attempt'] is not None})
        finally:
            for process in processes:
                process.terminate()
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.kill();process.wait()
            for log in logs:log.close()
    report['passed']=all(check['passed'] for check in report['checks'])
    (out/'summary.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__=='__main__':main()
