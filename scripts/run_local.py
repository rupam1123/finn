"""Start the local FINN API, durable worker and frontend together. No data reset."""
import argparse
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default='data/finn.sqlite3')
    parser.add_argument('--production', action='store_true', help='Serve the existing frontend production build')
    parser.add_argument('--build', action='store_true', help='Build the frontend before starting it')
    parser.add_argument('--use-model', action='store_true', help='Enable configured Gemini calls in the research worker')
    parser.add_argument('--lan', action='store_true', help='Listen on the local network for a phone review; use a trusted network')
    parser.add_argument('--public-review', action='store_true', help='Read-only assessment session: disable source jobs and do not start a worker')
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        print('Recommended runtime: Python 3.12. Use the existing .venv created with py -3.12.')
    npm = shutil.which('npm.cmd' if os.name == 'nt' else 'npm')
    if not npm:
        parser.error('Node/npm is missing. Install Node 24 LTS, then run npm ci in frontend.')
    if not (root / 'frontend/node_modules').is_dir():
        parser.error('Frontend dependencies missing. Run npm ci inside frontend first.')
    from finn.settings import load_local_settings
    load_local_settings(root / '.env')
    if args.public_review:
        os.environ['FINN_PUBLIC_REVIEW']='1'
    if args.use_model and os.getenv('FINN_PUBLIC_REVIEW')=='1':
        parser.error('--use-model cannot be combined with public read-only review.')
    if args.use_model and not os.getenv('GEMINI_API_KEY'):
        parser.error('--use-model requires your backend GEMINI_API_KEY in .env; never use NEXT_PUBLIC_ for a key.')
    database = Path(args.db)
    if not database.is_absolute():
        database = root / database
    env = {**os.environ, 'FINN_DB': str(database.resolve()), 'FINN_BACKEND_URL': 'http://127.0.0.1:8000',
           'NEXT_PUBLIC_API_BASE': '', 'PYTHONUTF8': '1', 'NEXT_TELEMETRY_DISABLED': '1'}
    if args.build:
        subprocess.run([npm, 'run', 'build'], cwd=root / 'frontend', env=env, check=True)
    if args.production and not (root / 'frontend/.next/BUILD_ID').is_file():
        parser.error('Production build missing. Add --build or run npm run build in frontend.')
    if (root / 'frontend/.preview-qa.json').exists():
        parser.error('Remove the local-only .preview-qa.json test configuration before starting your real workspace.')
    backend = [sys.executable, '-m', 'finn.dev', '--db', str(database.resolve())]
    if args.use_model:
        backend.append('--use-model')
    frontend = [npm, 'run', 'start' if args.production else 'dev', '--', '--hostname', '0.0.0.0' if args.lan else '127.0.0.1', '--port', '3000']
    for port in (8000, 3000):
        with socket.socket() as probe:
            probe.settimeout(.3)
            if probe.connect_ex(('127.0.0.1', port)) == 0:
                parser.error(f'Port {port} is already in use. Stop the existing FINN session before launching another API/worker.')
    children = []
    def stop(*_):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    try:
        children.append(subprocess.Popen(backend, cwd=root, env=env))
        children.append(subprocess.Popen(frontend, cwd=root / 'frontend', env=env))
        print('FINN: http://localhost:3000 — Ctrl+C stops this local session. Research model calls: '+str(args.use_model), flush=True)
        while all(child.poll() is None for child in children):
            time.sleep(.5)
        return next((child.returncode or 1 for child in children if child.poll() is not None), 1)
    except KeyboardInterrupt:
        return 0
    finally:
        for child in children:
            if child.poll() is None:
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/PID', str(child.pid), '/T', '/F'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                else:
                    child.terminate()
        for child in children:
            try:
                child.wait(timeout=12)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == '__main__':
    raise SystemExit(main())
