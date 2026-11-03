> Historical checkpoint. Current status: [final pack status](../../final-pack-status.md). Current setup: [final pack setup](../../final-pack-setup.md).

> Latest frontend update: [restructuring report](frontend-restructure-report.md), [corrected blueprint](../../frontend-architecture.md), and [setup](frontend-restructure-setup.md). Earlier checkpoint details below remain historical.

# FINN pre-final local review

The Day 4 interface runs against your existing FastAPI and SQLite data. It does not create sample prices, refresh exchanges on page load, or spend model quota while you browse. Keep your real `.env` and `data/finn.sqlite3`. Do not delete SQLite files to install this update.

## Install the source update

Stop the frontend, API, worker and any Day 3 finalizer before changing source files. Extract the pre-final ZIP outside the existing `finn` folder. From the extracted `finn_prefinal` folder, check the destination and then apply:

```powershell
py -3.12 install_update.py --project "X:\finn_day1_verification_kit\finn" --check
py -3.12 install_update.py --project "X:\finn_day1_verification_kit\finn" --apply
```

The installer backs up changed source files. It leaves your environment files, databases, uploads, verification reports and locally added files untouched. Unknown edits cause a conflict report before any change; keep that report and merge deliberately. There is no blanket force option. An already applied file is skipped. To review a separate copy, first copy your existing project to a new folder, then apply this source update there and use a separate copy of your database. `changes` is a cumulative patch, not a standalone project.

## Fresh dependencies on Windows

Use Python **3.12**, which avoids the Python 3.15 source-wheel failures from the earlier installation. You do not need to reinstall Python dependencies if your existing 3.12 environment still works. If the virtual environment was deleted:

```powershell
cd X:\finn_day1_verification_kit\finn
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e backend
cd frontend
npm ci
cd ..
```

Use Node 24 LTS. `npm ci` recreates `node_modules` from the supplied lockfile. Your backend `.env` contains your own Gemini settings; no key is shipped in this package. Keep the model ID that passes your account's preflight. This update does not require changing it.

## Start the whole product

For the closest review to a final submission:

```powershell
.\.venv\Scripts\python.exe scripts\run_local.py --build --production --db data\finn.sqlite3
```

Open **http://localhost:3000**. The launcher starts the API, durable Pull worker and frontend; Ctrl+C stops that session. Saved research, evidence and EOD data work without a Gemini call. New discovery can still contact public sources. The default worker runs deterministic extraction; add `--use-model` only when your key has available quota and you intend to run model stages. Existing model-assisted saved results still display without that flag.

For frontend development:

```powershell
.\.venv\Scripts\python.exe scripts\run_local.py --db data\finn.sqlite3
```

For phone review on your trusted Wi-Fi, add `--lan` and open `http://<your-PC-LAN-IP>:3000`. The frontend proxies `/api` to the backend, so the phone does not contact its own localhost. Allow the frontend port through your Windows firewall only on the intended private network. PWA installation/service-worker functionality needs HTTPS or localhost; a phone LAN HTTP URL tests the responsive app but may not offer installation.

The launcher supplies an empty `NEXT_PUBLIC_API_BASE` and `FINN_BACKEND_URL=http://127.0.0.1:8000`. This overrides an old frontend localhost API setting for that process. If running npm manually, set `$env:NEXT_PUBLIC_API_BASE = ""` before **both build and start**, and use the default backend URL or set `FINN_BACKEND_URL` before building. Never put secrets in variables prefixed `NEXT_PUBLIC_`.

Do not run a second worker or finalizer concurrently just to view the frontend. If an earlier worker crashed, stop other workers and use the documented `finn.dev --recover` workflow; the launcher does not silently requeue another worker's jobs.

## Review flow

1. Inbox: verify the default 24-hour window. Select 3/7/30 days or Latest session explicitly for older saved data. Empty weekends are valid. Check scanned/surfaced/buried; inspect Routine.
2. Apply price/volume thresholds and announcement watches. These filter saved observations; they do not subscribe to browser notifications or trigger exchange ingestion.
3. Search/filter/sort filings, save a card, switch Saved, paginate and export CSV. Card symbols open the matching research workspace.
4. Research: search by saved NSE name, symbol or close spelling. All four core examples and five showcase shortcuts work. A symbol without a snapshot offers source discovery; the durable worker processes it and the UI polls progress. Return/reload resumes any active job.
5. Inspect adjusted EOD charts with the session slider and accessible data table. Open the four-quarter Say–Do ledger and source citations. Review labels and missing comparisons remain explicit.
6. Financials: expand a primary statement to inspect Revenue/EBITDA/PBT/PAT, backend-computed QoQ/YoY, units and period. Values are never filled in by the UI. Bank and unsupported-layout abstentions remain visible.
7. Source library: search/type-filter/paginate sources; open a saved PDF or an original. Citation drawers show exact quoted text, page, original URL, observation time and hash. A missing local PDF offers the original source and explains the gap.
8. Portfolio: inspect all 18 prescribed holdings, search, sort, switch cards/table, and open a company. No portfolio return is invented without weights.
9. Source health: inspect company cache/provider status. Screener remains staging. Workspace settings reduce telemetry; warnings remain visible. QR, audio and copilot are visibly Planned.
10. Check browser Back, a direct `/research?symbol=POLYCAB` reload, keyboard search (Ctrl/Cmd+K), Escape/Tab in dialogs, offline messaging and narrow-screen bottom navigation.

## Verification commands

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
cd frontend
npm run typecheck
npm run test:day4
npm run test:pull-races
npm run build
cd ..
```

`test:day4` is a deterministic React/jsdom behavior suite plus service-worker checks. It is not a live Gemini acceptance test. Legacy `test:integration` / `scripts/run_integration.py` require the original fully populated verification DB (including its original company fixtures); the Day 4 read-only API/browser replay tests are documented separately in `docs/day4-prefinal-status.md`.

A production build and unit tests do not certify financial extraction or model reasoning. Re-run the targeted pending Day 3 acceptance checks with quota; avoid re-running all ingestion solely to inspect the UI.


## Shared read-only review

Read `release-review.md` before public deployment or tunnel sharing. Use `scripts/run_local.py --build --production --public-review --db data/finn.sqlite3` for saved-data review; this starts no worker and disables job POSTs. Do not add `--use-model` in that mode. For local owner discovery, stop public sharing and set `FINN_PUBLIC_REVIEW=0` before starting the normal authorised owner session. Data rights and software/regulatory release obligations still require resolution. Stop running processes before updating or rebuilding a production frontend.
