> Historical checkpoint. Current status: [final pack status](../../final-pack-status.md). Current setup: [final pack setup](../../final-pack-setup.md).

# FINN Day 1 — run it and verify it yourself

> Historical pre-repair report. For the current code, schema 2, updated test counts, fixed behavior and remaining limitations, use [day1-reliability-report.md](day1-reliability-report.md). The original issues described below were the inputs to that repair. The preserved original database is now `data/baselines/day1_original.sqlite3`.

Verification date: **28 October 2026 (IST)**. Day 2 is paused. This report supersedes the older checkpoint's statement that real HTTP had not been tested.

**Verdict: the saved ingestion checkpoint is inspectable and internally consistent, but the live refresh pipeline is not yet reliable enough to approve the Day 1 gate.** The application code is unchanged in this verification pass. Added verification scripts, captured responses, diagnostics and these instructions. The original `data/finn.sqlite3` is preserved; fresh requests went into `data/verification_live.sqlite3`.

## 1. What actually ran

| Check | Observed result | Scope / limit |
|---|---|---|
| Clean Python installation from lockfile and editable package | Passed | Python 3.12.14, Linux; Windows installation not executed here |
| Clean frontend installation (`npm ci`) | Passed | Node 24.22.1 |
| Existing backend tests | **42 passed in 1.43s**, one deprecation warning | Fixtures and unit/integration tests; not a provider-completeness guarantee |
| Production Next.js build and TypeScript | Passed | Compilation does not establish browser interaction |
| Saved database + real HTTP audit | **153 checks passed** | Includes 22 route cases, 20 warm reads, source-byte and arithmetic checks |
| Fresh database consistency audit | **35 checks passed** | Checks consistency, not freshness or transcript suitability |
| SQLite / source integrity | `ok`; all **68 saved raw objects** hash correctly | A hash proves preservation, not factual accuracy |
| Saved coverage | **19 companies**, 30 EOD sessions each, **227 filings**, four PDFs / **93 pages** | 18 holdings plus unseen ASTRAL; saved latest session 27 October |
| Warm ASTRAL API, actual local HTTP | **4.67 ms median; 6.68 ms maximum**, 20 reads | Server and client in one execution session; not phone/internet latency |
| Cold fresh ingestion of four companies | **79.43 seconds total** | Three workers; includes master, EOD, filings and PDF discovery |
| Fresh Screener requests | **7.10–8.42 seconds each** | The <3s cold goal fails |
| Frontend HTML over HTTP | HTTP 200, Day 1 shell present | JavaScript form interaction not verified in this environment |
| Browser preview | **Blocked: connection refused** | Browser cannot reach these execution-session servers; no working public preview is claimed |

The server/client HTTP test succeeded when both were launched in the same execution session. Separately launched clients and the cloud browser could not reach the servers. The exact environment cause remains unproven. Use the local instructions below to exercise the full browser flow.

## 2. Set up locally without changing the saved checkpoint

Download and extract `finn_day1_verification_kit.zip`. Open a terminal in the extracted **`finn` directory**, which contains `backend`, `frontend`, `data`, `scripts` and `docs`. Use Python **3.12** and Node **24** to match the tested major versions. Installation requires internet; viewing the saved cache does not require new provider requests. No model/API key is needed.

Windows PowerShell, terminal A:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e backend
.\.venv\Scripts\python.exe -m pytest backend/tests -q
.\.venv\Scripts\python.exe scripts/verify_day1.py --out verification/my-offline-check
$env:FINN_DB = (Resolve-Path data/finn.sqlite3).Path
.\.venv\Scripts\python.exe -m uvicorn finn.main:app --host 127.0.0.1 --port 8000
```

Keep terminal A running. Expected server line: `Uvicorn running on http://127.0.0.1:8000`. These commands invoke the environment's Python directly, so PowerShell script activation is unnecessary.

Windows PowerShell, terminal B, starting in the same `finn` directory:

```powershell
cd frontend
npm ci
$env:NEXT_PUBLIC_API_BASE = "http://localhost:8000"
npm run build
npm run typecheck
npm run start
```

Keep terminal B running. Open **http://localhost:3000**, using `localhost`, because the API's default CORS origin is `http://localhost:3000`. Open **http://localhost:8000/docs** for interactive Swagger requests. `NEXT_PUBLIC_API_BASE` is compiled into the frontend; rebuild after changing it.

macOS/Linux equivalent, terminal A from `finn`:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.lock.txt
.venv/bin/python -m pip install --no-deps -e backend
.venv/bin/python -m pytest backend/tests -q
.venv/bin/python scripts/verify_day1.py --out verification/my-offline-check
export FINN_DB="$PWD/data/finn.sqlite3"
.venv/bin/python -m uvicorn finn.main:app --host 127.0.0.1 --port 8000
```

Terminal B:

```sh
cd frontend
npm ci
export NEXT_PUBLIC_API_BASE=http://localhost:8000
npm run build
npm run typecheck
npm run start
```

Do not copy a virtual environment between computers. If a command fails, stop at that command and inspect the error before proceeding. If port 8000/3000 is occupied, stop your own existing application using that port or change both the server port and corresponding API/CORS configuration.

## 3. Verify the browser component

1. At `http://localhost:3000`, confirm “Day 1 · Foundation”, “Start with the source”, the NSE symbol field, and Inspect button.
2. Enter **TCS** and click **Inspect**. Expect **Tata Consultancy Services Ltd**, **consolidated**, **6 staging tables**, document links, fetched time, and the warning that Screener values are not verified primary evidence.
3. Repeat for **HDFCBANK**, **LAURUSLABS**, and **ASTRAL**. All four have cached data. ASTRAL demonstrates a symbol outside the 18-stock portfolio.
4. Enter **ZZZZNOTREAL**. Expect “This company has not been ingested yet”. This is a missing-cache response, not a claim that the symbol is valid.
5. Enter **TATAMOTORS**. The API correctly rejects the ambiguous legacy symbol with 422, but the UI currently shows only a generic source error. More helpful error detail remains to be implemented.
6. Stop terminal A with Ctrl+C, then Inspect TCS again. Expect “Cannot reach the ingestion API”. Restart terminal A before continuing.
7. Test a narrow browser window (about 390px), keyboard entry and focus. This is your manual browser checklist; it was **not** executed successfully in the cloud browser.

The UI currently shows table counts and document links, not financial tables, charts, alerts, rankings or a Say–Do ledger. Inspect reads cached data; it does not launch ingestion. Some original BSE document links can fail. Do not infer that all displayed links have been downloaded.

## 4. Verify each API route

In Swagger, expand each GET, choose **Try it out**, enter parameters, then **Execute**. Alternatively paste the full route into a browser, or run `Invoke-RestMethod` in PowerShell.

| Route | Expected result for the included checkpoint |
|---|---|
| `/health` | 200; `status: ok`, `phase: day1_ingestion`, `schema_version: 1` |
| `/api/portfolio` | 200; 18 holdings and five showcase symbols |
| `/api/universe?q=ASTRAL` | 200; total 2,364; ASTRAL appears in matches |
| `/api/company/TCS` | 200; fetched time, cache age, consolidated basis, six tables, discovery links |
| `/api/market/TCS` | 200; 30 saved bars and deterministic indicators |
| `/api/filings/TCS?days=30` | 200; filings plus source coverage, requested range and errors |
| `/api/company/ASTRAL` | 200; unseen-portfolio symbol is supported when ingested |
| `/api/company/ZOMATO` | 200; resolves to ETERNAL |
| `/api/company/TCS.NS` | 200; resolves to TCS |
| `/api/company/ZZZZNOTREAL` | 404; `not_ingested` |
| `/api/company/TATAMOTORS` | 422; ambiguous legacy instrument |
| `/api/filings/TCS?days=0` or `days=31` | 422; valid range is 1–30 |
| `/api/push/digest` | 404; Day 2 endpoint does not exist yet |

Actual captured `/health` response:

```json
{"status":"ok","phase":"day1_ingestion","schema_version":1}
```

Actual `/api/market/TCS` response excerpt from the saved checkpoint:

```json
{
  "as_of": "2026-10-27",
  "return_1d_pct": -1.5029624321992063,
  "return_5d_pct": 1.4628794924049338,
  "volume_ratio_20d": 0.7221538676949888,
  "warnings": [],
  "return_basis": "adjusted_close",
  "volume_basis": "provider_raw_volume"
}
```

Full actual HTTP bodies, status codes and timings are in **`verification/current/api-responses.json`**. These responses contain stored real-source data, not a new provider fetch on each request. Cache age grows with time. Filing counts were TCS 19, HDFCBANK 19, LAURUSLABS 5 and ASTRAL 1 at this check; the endpoint's rolling date window means counts can shrink on later dates without deleting data.

Run all HTTP and stored-data checks locally in terminal C from `finn`, while A and B are running:

```powershell
.\.venv\Scripts\python.exe scripts/verify_day1.py --base-url http://127.0.0.1:8000 --frontend-url http://localhost:3000 --out verification/my-http-check
```

On macOS/Linux use `.venv/bin/python` instead. Expected output against the unchanged checkpoint: `"passed": true`, `"checks": 153`. The script exits nonzero on failed assertions and saves full evidence. It bypasses HTTP proxy settings only for your explicitly supplied local URLs. It checks frontend HTML delivery, not JavaScript interaction.

## 5. Verify data accuracy and provenance yourself

**Market math:** load `/api/market/TCS`, inspect `data.bars`, and compare with `data.indicators`. For the saved 27 October snapshot:

- Latest adjusted close: **2496.89990234375**.
- Previous adjusted close: **2535.0**.
- Five sessions earlier: **2460.89990234375**.
- Latest volume: **4,336,510**.
- 1D return = `(latest / previous - 1) × 100` = **−1.5029624322%**.
- 5D return = `(latest / five-sessions-earlier - 1) × 100` = **1.4628794924%**.
- Volume ratio = `latest volume / mean of preceding 20 volumes`, excluding the current session = **0.7221538677×**.

`verification/current/market-recalculation.json` contains independent Decimal calculations for all 19 companies, including the denominator values. All 570 stored bars match their preserved Yahoo/yfinance frame within floating-point serialization tolerance. This is provider consistency, not comparison with an independent official exchange price feed. Yahoo's stored “raw” object is the downloaded pandas frame serialized to JSON, not the original wire response. Adjusted returns can differ from simple close-to-close returns around dividends.

**Financial staging:** open `/api/company/TCS`, inspect `data.tables.quarters`. The Sep 2026 column has Sales **73,188 INR crore**, Net Profit **13,934 INR crore**, EPS **38.37 INR per share**. All columns of these three rows match the saved source HTML in the spot-check. See `verification/current/tcs-table-spotcheck.json` and the `data.source_url` returned by the API. The live website may change. These figures have **not** been reconciled to primary financial statements and must not be presented as verified research findings. EPS must not be converted to crores.

**Filings:** inspect each record's `published_at`, `raw.exchdisstime`, `document_url`, and source coverage. The audit independently rechecks all 227 IST-to-UTC dissemination conversions. Example: RELIANCE's `27-Oct-2026 19:17:11` IST is `2026-10-27T13:47:11+00:00`. A missing attachment remains null; a successful NSE response is explicitly labelled `provider_response_unverified_completeness`.

**Primary documents:** open the exported originals in `verification/current/`: TCS 29 pages, HDFCBANK 17, LAURUSLABS 18, ASTRAL 29. Corresponding JSON contains source URL, SHA-256 and numbered text. All saved pages were extracted again from preserved PDF bytes and matched. For TCS, physical PDF page 2 is the transcript's printed “Page 1 of 28”, dated 8 October 2026. Citation page numbering must distinguish physical and printed pages. `claims_verified` remains false. Successful extraction does not establish speaker attribution, metric support or four-quarter coverage.

## 6. Run a fresh real-source ingestion separately

From `finn` in terminal C:

```powershell
.\.venv\Scripts\python.exe -m finn.cli --symbols TCS HDFCBANK LAURUSLABS ASTRAL --workers 3 --primary-sample --db data/my_live_check.sqlite3 --output verification/my-live-ingestion.json
```

On macOS/Linux substitute `.venv/bin/python`. Inspect every source status, date, error and document before using the new database. A zero CLI exit code is **not enough** to approve freshness or document suitability: the current implementation misses both defects below. Do not overwrite `data/finn.sqlite3` during this comparison.

The fresh run captured on **28 October, 02:30–02:31 IST** returned:

| Company | Latest EOD received | Staging tables | Filings received | Primary candidate |
|---|---|---:|---:|---|
| TCS | 26 Oct, older than saved 27 Oct | 6 | 19 | 29-page transcript |
| HDFCBANK | 26 Oct, older than saved 27 Oct | 6 | 19 | 17-page transcript |
| LAURUSLABS | 26 Oct, older than saved 27 Oct | 6 | 5 | 18-page transcript |
| ASTRAL | 26 Oct, older than saved 27 Oct | 6 | 1 | **1-page notice linking to a transcript** |

All 29 overlapping market sessions for each company were unchanged. The fresh provider frames simply lacked the saved 27 October bar. The cause of provider omission is unproven; do not erase the newer snapshot or call the new response current. See `verification/fresh-vs-saved.json`, `verification/live-ingestion.json` and the separate `data/verification_live.sqlite3`.

The fresh Astral PDF says the transcript is on the issuer's website; it is not the transcript itself. The previously preserved full 29-page Astral transcript remains available in `verification/current/ASTRAL-primary.pdf`. The one-page notice is in `verification/fresh-consistency/ASTRAL-primary.pdf` so you can inspect the difference.

## 7. What still needs fixing before Day 2

| Priority | Issue | Evidence / required correction |
|---|---|---|
| Critical | A refresh can replace newer market data with an older response | Fresh run regressed 27 Oct → 26 Oct. Add expected-session freshness and monotonic as-of guards, preserve last-good data, expose refresh attempt status |
| Critical | Transcript discovery accepts a notice as a full transcript | Fresh ASTRAL 1-page PDF passed `text_extracted`. Resolve approved primary links and check content suitability; abstain when unresolved |
| Critical | Company API hides a failed refresh behind the last-good snapshot | Reproduced with injected failure. Expose last attempt, failure reason and last-success timestamps separately |
| Critical before time-bounded signals | Filing query has no upper cutoff | A synthetic future filing appears in the current window. Enforce `since <= published_at <= as_of` |
| High | Same-ID amendments are ignored | Reproduced: `INSERT OR IGNORE` preserves the original text. Add version-aware updates and revision provenance |
| High | Cold latency misses target; repeated ingestion has no TTL reuse | Screener alone 7.10–8.42s. Add explicit freshness-aware caching/jobs and measure cold/warm separately |
| High | Provider fallback and completeness remain unproven | BSE 403 was observed in the earlier run; not retested here. Successful NSE responses do not certify all filings |
| Open verification | Full browser/mobile integration | HTTP passes, but browser access is blocked here; execute section 3 locally |
| Lower | Generic UI validation errors and dependency deprecations | Improve useful messages; one Starlette/httpx warning, yfinance/pandas warnings |

To reproduce the three persistence/API defects without touching your checkpoint:

```powershell
.\.venv\Scripts\python.exe scripts/reproduce_known_issues.py
```

The three `true` values mean **defects reproduced**, not tests passed. These diagnostic rows are synthetic, explicitly labelled, and confined to a disposable database. They are not mixed into the live source evidence.

Remaining product work: Day 2 classification/materiality/enrichment/digest; Day 3 primary research and evidence ledger; later mobile QA, PWA validation, durable deployment and submission package. Nothing in this report claims those are implemented.

## 8. Evidence and changed files

- `scripts/verify_day1.py`: read-only data audit plus optional real HTTP checks; exports preserved primary PDFs for inspection.
- `scripts/reproduce_known_issues.py`: isolated defect reproductions.
- `verification/pytest.txt` and `pytest.xml`: actual 42-test results.
- `verification/frontend-build.txt`, `frontend-typecheck.txt`: actual frontend checks.
- `verification/current/summary.json`, `api-responses.json`: 153 checks and complete HTTP responses.
- `verification/live-ingestion.json`, `fresh-vs-saved.json`, `fresh-consistency/`: fresh-source evidence and comparison.
- `verification/known-issues.json`: three reproduced defects.
- `README.md`, `docs/day1-status.md`, `docs/build-history.md`: updated pointers and verification status.

Keep this report with the checkpoint. Passing the existing tests establishes only the behavior those tests cover; it does not cancel the failures uncovered by the fresh-source run.
