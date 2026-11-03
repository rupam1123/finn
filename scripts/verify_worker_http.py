"""Local real-HTTP cold-job check; launches API + worker in the same process tree."""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import httpx


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--symbol',default='HAVELLS');p.add_argument('--port',type=int,default=8017)
    p.add_argument('--timeout',type=int,default=360);p.add_argument('--out',default='verification/day3-cold-http.json')
    a=p.parse_args();report={'symbol':a.symbol,'passed':False,'scope':'Real HTTP, empty temporary DB, real source discovery; no live model call'}
    root=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='finn-http-') as temp:
        env=dict(os.environ,FINN_DB=str(Path(temp)/'cold.sqlite3'))
        with open(Path(temp)/'server.log','w') as log:
            process=subprocess.Popen([sys.executable,'-m','finn.dev','--db',env['FINN_DB'],'--port',str(a.port)],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
            try:
                with httpx.Client(base_url=f'http://127.0.0.1:{a.port}',timeout=15,trust_env=False) as client:
                    for _ in range(100):
                        if process.poll() is not None:raise RuntimeError('API/worker launcher exited')
                        try:
                            health=client.get('/health')
                            if health.status_code==200:break
                        except httpx.HTTPError:pass
                        time.sleep(.2)
                    else:raise RuntimeError('Local HTTP startup unavailable')
                    report['health']=health.json()
                    queued=client.post('/api/pull/'+a.symbol+'/jobs?refresh=true')
                    report['enqueue_status']=queued.status_code
                    if queued.status_code!=202:raise RuntimeError('Job was not accepted')
                    job=queued.json();start=time.perf_counter();last=None
                    while time.perf_counter()-start<a.timeout:
                        value=client.get('/api/pull-jobs/'+job['id']).json()
                        if value['status']!=last:print(value['status'],flush=True);last=value['status']
                        if value['status'] not in ('queued','running'):
                            research=client.get('/api/pull/'+a.symbol)
                            report.update(job=value,research_http_status=research.status_code,elapsed_seconds=round(time.perf_counter()-start,2))
                            if research.status_code==200:
                                data=research.json()['data'];report.update(source_count=len(data['sources']),source_errors=data['source_errors'],quarter_periods=data['say_do']['observed_periods'])
                            report['passed']=research.status_code==200 and value['status'] in ('partial','complete')
                            break
                        time.sleep(2)
                    else:report['error']='Research exceeded the explicit smoke-test deadline'
            except Exception as exc:report['error']=str(exc)
            finally:
                if process.poll() is None:
                    if os.name=='nt':subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True)
                    else:process.terminate()
                    try:process.wait(timeout=15)
                    except subprocess.TimeoutExpired:process.kill();process.wait()
        report['server_log']=Path(temp,'server.log').read_text(errors='replace')[-3000:]
    target=Path(a.out);target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ('server_log','source_errors')},indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__=='__main__':main()
