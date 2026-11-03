> Historical checkpoint. Current status: [final pack status](../../final-pack-status.md). Current setup: [final pack setup](../../final-pack-setup.md).

> Latest refinement: [Universe/dialogs/telemetry update](universe-dialogs-telemetry-update.md). Apply with the same installer steps and rebuild production.

> Current update: [fluid navigation, scroll and chart motion, adaptive glass dock](fluid-motion-update.md). Run the production build below when assessing speed.

> This update also includes the [compact glass/theme/motion revision](glass-motion-update.md). Apply and rebuild using the same steps below.

# Apply and review the restructured FINN frontend

Stop FINN's backend/frontend and any finalizer before applying an update. Keep your `.env` and all SQLite files. This update contains source changes; it does not contain your private data or model credentials.

From the extracted `finn_prefinal` update directory in Windows PowerShell:

```powershell
py -3.12 install_update.py --project "X:\finn_day1_verification_kit\finn" --check
py -3.12 install_update.py --project "X:\finn_day1_verification_kit\finn" --apply
cd X:\finn_day1_verification_kit\finn
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e backend
cd frontend
npm ci
cd ..
.\.venv\Scripts\python.exe scripts\run_local.py --build --production --db data\finn.sqlite3
```

Use Python 3.12; do not reuse a Python 3.15 virtual environment. If necessary, recreate only `.venv` with `py -3.12 -m venv .venv`, then install the pinned dependencies above. Dependency/model settings remain those of your existing backend. Do not put API keys into `NEXT_PUBLIC_*` variables.

Open http://localhost:3000. For a read-only assessment session use the same command with `--public-review`; the worker and source-job POST are disabled. Existing public tunnel instructions still require frontend and backend to stay running on the computer. A quick tunnel is not durable deployment.

The installer checks all files before writing, backs up changed files, and refuses unknown local source edits. If it reports conflicts, keep that output and your current project; do not force overwrite or delete your database. Source folders and unrelated files are preserved.

## Checks to run on your own data

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
cd frontend
npm run typecheck
npm run test:workspace
npm run build
```

Review Inbox 24h/7d/routine and category filters; Radar sliders and an alert timeline; any company Overview/Say–Do/Forensics/Vault; a quote drawer followed by Back and direct-link reload; and an unseen symbol without automatically starting discovery. The `/portfolio` and old `?symbol=` links should redirect correctly.

A new model/provider run is separate from these offline checks. Refresh only the companies that need newer evidence, with your local API quota available. Existing research remains inspectable while a job runs. Do not rerun the full model finalizer merely to test navigation.

Read `frontend-architecture.md` for the corrected blueprint and `frontend-restructure-report.md` for results and remaining limitations.
