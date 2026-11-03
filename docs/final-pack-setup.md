# Final pack: update, setup and run

The ZIP contains an outer `finn_final` folder with a complete `finn` source tree, this guide, an existing-project manager and payload manifest. It is a full source pack, not another incremental patch. It contains no private database or environment.

## 1. Update the project you already have

Close FINN's frontend/backend/worker/finalizer and the Cloudflare tunnel first. Extract this pack **outside** `X:\finn_day1_verification_kit\finn`; for example into Downloads. Open Windows PowerShell in the extracted outer `finn_final` folder, where `manage_existing.py` and the supplied `finn` folder sit beside each other.

```powershell
py -3.12 .\manage_existing.py --project "X:\finn_day1_verification_kit\finn" --check --cleanup
py -3.12 .\manage_existing.py --project "X:\finn_day1_verification_kit\finn" --apply --cleanup
```

The check lists each file to update/quarantine. It writes nothing. Apply backs up source before replacing it; generated caches and known outdated copies move to `X:\finn_day1_verification_kit\finn-release-backups\<run>`. The receipt is there. Your `.env`, all SQLite data, `.git`, `.venv`, installed dependencies, old backups and unknown files remain untouched. The large database is not copied, uploaded or reset.

If there are conflicts, the whole update stops before changing anything. Keep the message and your edit; merge the matching file from the supplied `finn/` folder deliberately. Do not force-copy the entire folder over private files or apply older ZIPs afterward. For another project location, change only the `--project` path.

Read [CLEANUP.md](../CLEANUP.md) for exact cleanup decisions. The manager never permanently deletes anything. It deliberately leaves `.qa` directories and their databases alone; only their frontend preview override is quarantined. Existing old backup directories/ZIPs can be archived outside the active app after review.

## 2. Restore dependencies

From your actual FINN root:

```powershell
cd X:\finn_day1_verification_kit\finn
.\.venv\Scripts\python.exe --version
```

Keep a working Python 3.12 environment. If `.venv` is absent, create it:

```powershell
py -3.12 -m venv .venv
```

If it is Python 3.15, stop all processes, rename that directory for rollback, then create 3.12:

```powershell
Rename-Item -LiteralPath .\.venv -NewName .venv-py315-old
py -3.12 -m venv .venv
```

Install the locked dependencies and recreate editable package metadata after cleanup:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e backend
cd frontend
npm ci
cd ..
```

Use the tested Node 24 family. `npm ci` restores `node_modules` from the included lockfile; it does not reset FINN's database. No new animation package is required. Do not copy the example environment over an existing private `.env`.

## 3. Configuration and data

For an existing project, retain your private `.env` and data. If `.env` is missing, copy `.env.example` to `.env` and supply only the settings you need. Saved-data review needs no model key. Keep any real `GEMINI_API_KEY` local and out of Git/`NEXT_PUBLIC_*`. Model execution requires explicit accessible model IDs and current quota in that provider project; the example does not assume one.

The source ZIP's `data/` contains only a README. A fresh folder without your populated database will show empty saved-data states. The recommended in-place update preserves your original populated `data/finn.sqlite3` without copying it. Never delete a database or its WAL/journal companions to make a test pass.

## 4. Build and run

```powershell
.\.venv\Scripts\python.exe scripts\run_local.py --build --production --db data\finn.sqlite3
```

Open http://localhost:3000. Ctrl+C stops the local session. Avoid `npm run dev` when judging production navigation speed. If a port is already occupied, stop the older FINN session rather than starting a second worker. Reload the browser after the new build.

For sharing saved evidence in a read-only assessment session:

```powershell
.\.venv\Scripts\python.exe scripts\run_local.py --build --production --public-review --db data\finn.sqlite3
```

For an explicitly intended owner model session, use `--use-model` instead of `--public-review` after local model preflight/configuration succeeds. That operation can consume provider quota. No full finalizer or model call is needed to inspect the frontend.

## 5. Validate locally

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
cd frontend
npm run test:workspace
npm run typecheck
npm run build
cd ..
```

Review Inbox with 24h and a populated explicit window; Routine, filters, pagination, bookmark/export feedback; Radar sliders and a filing timeline; Universe plot colors/scrubbers/table view; company Overview/Say–Do/Forensics/Vault; quote/PDF evidence and Back/direct links; both themes; short-window Settings scrolling/Done; reset cancellation/focus; About/source notices. Missing/review states must stay visible.

A source/model acceptance run is separate and may be slow or quota-limited. Read the handoff and current status first. Do not rerun the full model finalizer to check packaging, colors or navigation. The earlier 52/58 result is not converted to a pass by these offline checks.

## 6. Share with another AI

Give it the complete clean source pack and root `handoff.md`. Start with: “Read handoff.md and AGENTS.md first. Preserve the current design, private data and safeguards. Verify the open local acceptance gates and prepare Day 5 without claiming unsupported success.”

The pack is suitable for source review because keys, databases, dependency output and local QA captures are excluded. Do not additionally upload `.env`, a database containing private material, old backups or raw logs without reviewing them. Actual AI build-history export remains a separate submission deliverable.
