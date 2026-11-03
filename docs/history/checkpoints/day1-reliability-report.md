> Historical checkpoint. Current status: [final pack status](../../final-pack-status.md). Current setup: [final pack setup](../../final-pack-setup.md).

# FINN Day 1 reliability repair — 28 October 2026 IST

**Five correctness defects are fixed. The sixth issue, performance, is substantially improved, but the original cold <3-second target is not met.** Day 2 has not started. Live market refreshes still receive incomplete provider data; the application now rejects those responses, retains last-good data and reports the failure honestly.

The original Day 1 database is preserved at `data/baselines/day1_original.sqlite3`. The default `data/finn.sqlite3` contains schema 2, preserved real data and actual refresh-attempt records. No synthetic diagnostic company data or injected outage is in that database.

## What changed and how it was verified

| Issue | Implemented repair | Verification and result |
|---|---|---|
| 1. Older market data overwrites newer data | Atomic session-date guard in SQLite; older observations cannot undo a same-session correction. Full OHLCV validation before replacement. Explicit expected-session freshness using the sourced NSE calendar. Invalid refreshes preserve the accepted snapshot and timestamp. | Captured real TCS responses ending 27 Oct and 26 Oct: the older response is rejected. Fresh four-company frames contained missing Close/Adj Close values on 27 Oct: all rejected, newer complete data retained. Edge cases cover NaN, negative volume, inconsistent high/low, holiday/weekend, pre-close, unknown calendar and provider outage. **Fixed.** |
| 2. Notice mistaken for transcript | Conservative content suitability check; follow embedded PDF links only on approved HTTPS hosts, bounded by document count. Record each document's URL, hash, page count and selection result. Scans/notices abstain. | Real Astral NSE notice → approved issuer PDF → **29-page full transcript**. TCS 29, HDFCBANK 17 and Laurus 18 pages also fetched. No claim-verification flag is set. Tests reject notices without safe links, scans and unsafe redirects. **Fixed for the demonstrated cases; heuristic scope remains explicit.** |
| 3. Failed refresh hidden behind cached success | Independent attempt history with started/finished time, status and error. Snapshot keeps last accepted source time, age, TTL and `last_success_at`. Company API includes other source statuses; frontend shows failures and retained data. Retry after failure bypasses old HTTP cache so cached data cannot falsely clear the failure. | Injected failures using captured real company data return the last-good snapshot plus failure metadata; no-cache failure returns 503, never a fake successful empty response. React renders retained HDFCBANK data with an explicit diagnostic warning. Successful retry clears failure. **Fixed.** |
| 4. Amendments ignored | NSE identity uses symbol + exchange sequence ID, independent of attachment/text. Append-only filing revisions preserve payload, content hash and observation time. Schema-1 migration preserves original rows. | Controlled amendment of a captured real NSE row, changed attachment, duplicate replay, older-observation replay and repeated migration all pass. Revision 1 remains available; latest is revision 2, with one current filing. No naturally occurring live amendment is claimed to have been observed. **Fixed where the provider supplies a stable identity.** |
| 5. Future filings enter date window | Both lower and upper publication bounds. Optional timezone-aware `as_of`, rejecting future/naive cutoffs. Only revisions observed by the cutoff are eligible. | Real stored filings served through HTTP; exact endpoints, one-microsecond-outside boundary, timezone equivalents, future-row injection and historical revision visibility tested. Original reproduction now returns false. **Fixed.** |
| 6. Slow ingestion / repeated cold requests | Persistent TTL reuse with original timestamps, hash/byte checks, no cached error responses, forced refresh and explicit failed-market retry cooldown. Independent source work shares a bounded pool of at most three workers. | Application-cache-bypassed four-company run: **34.79s**. Repeat cache runs: **0.95s and 1.17s**. Earlier same-session serial-phase run: 86.31s. Provider timing varies, so these are observations, not a controlled attribution or latency guarantee. **Improved; cold <3s remains open.** |

The real provider frame explains the apparent date regression: the latest completed day's Open/High/Low/Volume existed, but Close and Adj Close were null. The previous adapter dropped those incomplete rows and could silently move the snapshot backwards. The repaired adapter rejects the incomplete frame before saving it. It does not invent prices or splice a partial bar into the saved series.

## Test results

| Check | Final result |
|---|---|
| Backend regression suite | **81 passed**, one non-failing Starlette/httpx deprecation warning; 2.31s |
| New regression coverage | 39 added cases beyond the original 42; original ingestion mock updated for the validated resolver contract |
| Production Next.js build | Passed |
| TypeScript check | Passed |
| Real HTTP + saved-source audit | **153 checks passed** |
| React/jsdom interaction scenarios against real HTTP API | **8 passed** |
| Four primary-document API cases | Passed: 29 / 17 / 18 / 29 pages |
| Market refresh status exposed in API | Passed |
| Original defect reproduction | All three flags now **false**: amendment ignored, future-window leakage, hidden failed refresh |
| Database integrity | `ok`; 19 companies, 227 current filings, 87 raw source objects |
| Source preservation / arithmetic | All 87 raw-object hashes checked; 570 stored market bars match preserved frames; 19 companies' indicators independently recalculated; 227 filing timestamp conversions checked |
| Warm company API over local HTTP | 20 samples: **4.72ms median, 6.66ms max** |
| Source and patch checks | Python compilation and `git diff --check` passed |

The 153 checks include local HTTP route cases and warm-read assertions; they are not 153 additional independent unit tests. Integrity/hash checks establish byte preservation and consistency, not independent certification of provider values. TCS staging-table spot checks compare selected rows to captured HTML. Primary financial-statement reconciliation remains later work.

The eight UI scenarios cover TCS, ASTRAL and LAURUSLABS rendering; HDFCBANK retained data plus a refresh warning; missing-symbol 404 clearing the prior card; informative ambiguous-symbol 422; network failure; and successful retry. Tests exercise the actual React component in jsdom with actual FastAPI HTTP responses. This is **not a real-browser/mobile rendering test**. Your earlier local startup confirmation is retained, but the new visual states still need a real-browser check on your machine.

## Real-source acceptance run

| Company | Fundamentals | NSE filings received | Primary transcript | Market refresh |
|---|---|---:|---:|---|
| TCS | Six tables, success | 19 | 29 pages | Incomplete latest-session close; rejected |
| HDFCBANK | Six tables, success | 19 | 17 pages | Incomplete latest-session close; rejected |
| LAURUSLABS | Six tables, success | 5 | 18 pages | Incomplete latest-session close; rejected |
| ASTRAL | Six tables, success | 1 | 29 pages, reached through notice | Incomplete latest-session close; rejected |

All cold/warm CLI runs returned **exit code 1**, correctly, because the market source remained unhealthy. The sub-second cached path is **not a successful new market fetch**. It retains the failed status and reports when retry becomes eligible. `--force-refresh` can retry immediately but does not bypass data validation.

## Cache and freshness behavior

| Source / state | Reuse policy |
|---|---|
| Screener staging | 1 hour |
| Complete market snapshot | 15 minutes, only when expected-session freshness and prior attempt allow it |
| NSE announcement response | 5 minutes, keyed by full request URL, parsed again with the requested date bounds |
| Primary PDF / selected transcript | 24 hours; source bytes and suitability still checked |
| NSE security master | 24 hours |
| Failed/stale market attempt | Retry cooldown up to 5 minutes; failure stays visible; force refresh bypasses cooldown |

Cache hits do not become new source observation times. Failed refreshes cannot be cleared by reusing the old HTTP response. Backend GET endpoints remain read-only cache views and do not scrape on page requests.

The calendar is sourced from NSE's capital-market holiday feed, captured for 2026 on 28 October IST. See `backend/finn/nse_calendar_2026.json` and `verification/reliability/nse-holidays.json`. Official reference: https://www.nseindia.com/resources/exchange-communication-holidays . Regular sessions are considered complete after the project's conservative 18:00 IST cutoff. Unknown years and unresolved special-session dates abstain rather than guessing freshness. The calendar must be maintained for future years or exchange schedule changes.

## Update and run on Windows

1. Stop your existing backend/frontend terminals with Ctrl+C.
2. Extract the updated ZIP into a **new folder** and open PowerShell in its `finn` directory. Keep your previous project folder as your own backup. The archive includes the original baseline as well as the updated default database.
3. Install/update dependencies and run tests:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e backend
.\.venv\Scripts\python.exe -m pytest backend/tests -q
cd frontend
npm ci
npm run build
npm run typecheck
cd ..
.\.venv\Scripts\python.exe scripts/run_integration.py
```

Use Node 24 to match the tested major version. The integration runner needs ports 8000 and 3000 free. It starts both servers, uses a temporary database copy, runs the checks, and stops its own servers. It does not write diagnostic failures to your real database. Expected backend test count: **81**. Expected integration summary: `passed: true`.

4. Start the backend in terminal A:

```powershell
$env:FINN_DB = (Resolve-Path data/finn.sqlite3).Path
.\.venv\Scripts\python.exe -m uvicorn finn.main:app --host 127.0.0.1 --port 8000
```

5. Start the frontend in terminal B, from `finn`:

```powershell
cd frontend
npm run start
```

Open http://localhost:3000 and http://localhost:8000/docs. Use `localhost:3000`, matching the default CORS origin. Inspect TCS and ASTRAL. Expect the company, six staging tables, source age, and per-source status. The packaged real market failure should be visible while the saved 27 October market data remains available. No artificial HDFCBANK fundamentals outage was saved; that scenario is test-only.

6. To perform your own fresh requests, use a separate database or a copy of the packaged one:

```powershell
Copy-Item data/finn.sqlite3 data/my_refresh.sqlite3
.\.venv\Scripts\python.exe -m finn.cli --symbols TCS HDFCBANK LAURUSLABS ASTRAL --workers 3 --primary-sample --force-refresh --db data/my_refresh.sqlite3 --output verification/my-refresh.json
```

The copy operation should be done while no writer is using that database. Inspect source statuses and dates, not just the CLI exit code. Providers can change after this report. To inspect your refreshed copy through the API, restart terminal A with `FINN_DB` pointing to that file.

On macOS/Linux replace `py -3.12` with `python3.12`, use `.venv/bin/python`, and set `export FINN_DB="$PWD/data/finn.sqlite3"`. Other commands are the same.

## Database migration and compatibility

- Existing schema-1 databases migrate to schema 2 on first startup. Back up your own database before upgrading; do not run an older writer concurrently.
- Existing routes and snapshot `data`, `fetched_at`, and `cache_age_seconds` remain. New fields are additive. `/health` reports schema version 2.
- `/api/primary/{ticker}` is new and refuses an unsuitable legacy notice with 503.
- `/api/filings/{ticker}` adds the actual cutoff, revision metadata and optional `as_of`.
- NSE filing IDs change to stable provider identity during migration. If you saved IDs externally, refresh those references. No authenticated/user filing annotations exist in this Day 1 build.
- Pre-migration observation history cannot be reconstructed. Migrated records begin observation history at migration time. Historical `as_of` queries before that time may exclude them; this deliberately avoids claiming earlier knowledge.
- Without a stable exchange sequence ID, fallback identity remains conservative. The application does not guess that two different disclosures are amendments of one another.

## Remaining issues and limits

1. **Provider availability:** fresh Yahoo frames are incomplete in this environment. No new valid market refresh is claimed. Retained real data is dated and source failure is visible. BSE fallback was previously blocked and is not newly certified operational.
2. **Cold performance target:** the observed 34.79s application-cache-bypassed run still fails <3s. Warm reuse is fast, but provider downloads and PDF traversal remain slow. Production job orchestration and deployment measurement belong to later phases.
3. **Browser/mobile QA:** React/jsdom + HTTP passes; a real-browser test of the updated UI on Windows/mobile remains. No public deployment is claimed.
4. **Source completeness and research:** NSE response completeness is unverified. Screener remains secondary staging. Transcript suitability is heuristic; speaker/metric entailment, scanned-document OCR and four-quarter evidence coverage are not solved here.
5. **Calendar and hosting:** maintain holidays/special sessions and test durable storage on the eventual host. Multi-host production database behavior is outside this local repair.
6. **Warnings:** one Starlette/httpx deprecation warning and yfinance/pandas warnings remain non-failing.

## Evidence map

- `backend/tests/test_reliability.py` and `backend/tests/fixtures/reliability/`: targeted regressions with captured real fixtures and explicitly labelled diagnostic modifications.
- `verification/reliability/pytest.txt`, `pytest.xml`: final 81-test run.
- `verification/reliability/frontend-build.txt`, `frontend-typecheck.txt`: frontend checks.
- `verification/reliability/integration/summary.json`, `react.txt`: real HTTP + React integration results.
- `verification/reliability/integration/http/api-responses.json`: full actual API responses and timings.
- `verification/reliability/cold-optimized.json`, `warm-optimized.json`, `performance-optimized.json`: source statuses and measured cold/cache behavior.
- `verification/reliability/known-issues-after.json`: all original defect flags false.
- `verification/reliability/database-checkpoint.json`: original/default checkpoint paths and hashes.
- `scripts/verify_day1.py`, `scripts/run_integration.py`, `scripts/reproduce_known_issues.py`: repeatable verification commands.

The earlier `verification/current/` results and self-verification document are retained as historical evidence. This report and `verification/reliability/` describe the repaired build.
