"""Start the local API and durable Pull worker together; no production deployment."""
import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def main():
    from .settings import load_local_settings
    load_local_settings()
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',default=os.getenv('FINN_DB','data/finn.sqlite3'))
    p.add_argument('--host',default='127.0.0.1')
    p.add_argument('--port',type=int,default=8000)
    p.add_argument('--use-model',action='store_true')
    p.add_argument('--recover',action='store_true',help='Requeue interrupted jobs; stop any other worker first')
    args=p.parse_args()
    if args.use_model and os.getenv('FINN_PUBLIC_REVIEW')=='1':p.error('Public review is read-only; model execution is disabled.')
    if args.use_model and not os.getenv('GEMINI_API_KEY'):p.error('--use-model requires GEMINI_API_KEY in your environment')
    env=dict(os.environ,FINN_DB=str(Path(args.db).resolve()))
    worker=[sys.executable,'-m','finn.pull_jobs','--db',env['FINN_DB'],'--watch']
    if args.use_model:worker.append('--use-model')
    if args.recover:worker.append('--recover')
    children=[]
    def stop(*_):raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,stop)
    try:
        if os.getenv('FINN_PUBLIC_REVIEW') != '1':
            children.append(subprocess.Popen(worker,env=env))
        children.append(subprocess.Popen([sys.executable,'-m','uvicorn','finn.main:app','--host',args.host,'--port',str(args.port),'--no-access-log'],env=env))
        while all(child.poll() is None for child in children):time.sleep(.5)
        raise SystemExit(next((child.returncode or 1 for child in children if child.poll() is not None),1))
    except KeyboardInterrupt:
        pass
    finally:
        for child in children:
            if child.poll() is None:child.terminate()
        for child in children:
            try:child.wait(timeout=10)
            except subprocess.TimeoutExpired:child.kill();child.wait()


if __name__=='__main__':main()
