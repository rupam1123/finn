> Historical checkpoint. Current status: [final pack status](../../final-pack-status.md). Current setup: [final pack setup](../../final-pack-setup.md).

# Current Day 2 checkpoint — 30 October 2026 (IST)

See [day2-review-status.md](day2-review-status.md) for the current verified report. The Windows backup has been restored successfully; 219/224 frozen-cohort filings have usable primary text, all 123 pending records were attempted, and all 210 uncertain records were triaged. Full review flags remain, with 8 source/classification follow-ups and broader extraction still open. 199 backend tests and full local HTTP/React integration pass. Day 3 has not started.

The following notes are historical and are superseded by the report above.

# Day 2 progress — 28 October 2026 IST

**29 October update:** The resumed workspace's `data/finn.sqlite3` is malformed and appears truncated. The latest changes pass 168 backend tests using isolated test databases, but full integration and batch completion are blocked. The historical measurements below are not current acceptance results. See [day2-review-status.md](day2-review-status.md) for the current report. Day 3 has not started.

**The core Push workflow runs in the existing project. The Day 2 acceptance gate remains open.** Changes, source bytes, tests and progress remain in the same repository/database. No replacement project folder or ZIP was created. The final complete build/package remains Day 5; the frontend production build here was a validation check.

## Implemented and verified

| Component | Working behavior | Current limit |
| --- | --- | --- |
| Classification | All 17 categories; separate materiality; critical overrides; unknown/review visibility; conservative routine burial | Rule classifications are provisional. Live Flash accuracy is unverified. All 215 surfaced records currently retain review flags. |
| Flash adapter | Fixed Gemini endpoint, bounded requests, strict JSON validation, quote/page checks, redacted failures and usage metadata | No API key was configured. Mock HTTP tests do not establish live model behavior. |
| Results | Real TCS and Polycab consolidated tables; exact units, aligned periods, Python QoQ/YoY and half-year reconciliation | Two partial tables; nine other results records need review. Missing EBITDA remains blank. |
| Management | Bajaj Finance reappointment and issuer profile; Trent resignation with role/effective date | Two extracted events; 27 provisional management-category records need review. Complex multi-person tables remain unsupported. |
| EOD alerts | Adjusted returns, prior-20-session volume, exact threshold comparisons, split suppression and temporal cutoffs | Cached source data. Earlier sessions may lack enough history for volume evaluation. No causal attribution. |
| Digest | Ranked cards, reconciled counts, exact 24h/3d/7d/30d windows, source times/failures and coverage | Reads saved data. Refresh is an explicit CLI action. |
| Frontend | Existing company inspection plus Day 2 windows/thresholds, results, management evidence, routine drawer and alerts | Functional verification screen. Full mobile design remains Day 4; real-browser/mobile revalidation is open. |
| Evidence | Original URL, page, quote, SHA-256 and immutable saved PDF endpoint | Quote presence alone does not validate every semantic inference. Ambiguous extraction remains reviewable. |

The Flash-assisted enrichment path currently locates source pages; deterministic code accepts or rejects financial rows. **Broad structured extraction envisaged in the complete Day 2 plan is not yet implemented/validated.** This is an open gate, not a passed feature. No external executive career history was invented.

## Real-data coverage

The recorded 30-day audit contains **224 filings: 215 surfaced + 9 buried**, with **47 EOD alerts counted separately**. All 224 have analysis records; 220 have PDF evidence and four have explicit source-unavailable states. There are 208 distinct document hashes because several filings share PDFs. Source bytes are deduplicated by hash.

The four unavailable attachments are TRENT, SUNPHARMA and PERSISTENT resignation ZIPs, and a TMPV news-verification record without an attachment. They stay visible. A separate Trent resignation PDF was successfully processed. The CLI correctly exits **1** for partial source coverage, even when every selected record has been handled.

Window counts change as records cross the rolling cutoff. See `verification/day2-integration/day2-digest-*.json` for the exact API timestamps and counts. An accepted exchange response does not establish complete exchange-wide coverage.

### Financial values checked against actual PDFs

Comparison periods: 30 September 2026, 30 June 2026 and 30 September 2025; consolidated three-month periods. PAT is total profit including non-controlling interests, not owners' PAT.

| Source | Metric | Current INR crore | Previous quarter | Year ago | QoQ | YoY |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| TCS, PDF page 8 | Revenue | 73,188 | 72,275 | 65,799 | 1.26% | 11.23% |
| TCS, PDF page 8 | PBT | 18,638 | 17,944 | 16,068 | 3.87% | 15.99% |
| TCS, PDF page 8 | PAT | 13,934 | 13,420 | 12,131 | 3.83% | 14.86% |
| Polycab, PDF page 4 | Revenue | 9,898.901 | 8,209.732 | 6,477.211 | 20.58% | 52.83% |
| Polycab, PDF page 4 | PBT | 1,306.220 | 1,058.223 | 921.001 | 23.44% | 41.83% |
| Polycab, PDF page 4 | PAT | 989.997 | 796.654 | 692.959 | 24.27% | 42.87% |

Polycab reports INR millions; normalization is exactly ×0.1. Stored money values are not rounded. TCS owners' PAT of 13,884 is deliberately not substituted for total PAT of 13,934. No EBITDA was fabricated. Both pages were rendered and visually checked; extracted rows also reconcile the two quarters to the reported half year within source precision.

Bajaj Finance supports **Prashant Verma, Chief Information Security Officer, reappointment effective 1 February 2027**. Its profile is labelled an issuer statement, not independent verification. Trent supports **Harish Bhat, Non-Executive Non-Independent Director, resignation effective 17 October 2026**. Publication and effective dates remain separate.

HDFC Bank and Infosys have ambiguous/damaged text and mixed layouts. The pipeline abstains instead of repairing digits or guessing periods. Lenders have separate schemas; unseen issuers with unknown industry/profile metadata are held for review.

## Additional reliability fixes

- Nullable exchange industry metadata no longer crashes Polycab processing; unseen unknown profiles abstain.
- Failed refreshes retain the previous analysis and original timestamps. Previously buried items reappear for review after failed/incomplete refreshes.
- Analysis keys include filing content and component versions. Amendments and parser changes invalidate old reuse.
- Large raster regions or incomplete text prevent routine burial. Unsupported attachments are not silently dropped.
- PDF parsing runs in isolated child processes: 30 MB, 500 pages, two million extracted characters and a 60-second parse timeout. Network work remains bounded to three workers.
- Exact decimal comparisons prevent floating-point errors at alert thresholds: price is inclusive; volume is strictly greater-than.
- Contemporaneous links must have been published and observed by the alert cutoff. Later observations/publications are separately retrospective. Nothing beyond the requested as-of is included.
- Evidence downloads verify stored PDF bytes against their hash. Saved evidence remains accessible if an exchange later changes the URL content.

Automatic approval review initially blocked unrelated Microsoft telemetry during PDF processing. An opt-out was insufficient. The ML layout/ONNX extras were removed, the basic PyMuPDF 1.28.2 runtime was pinned, and PDF parsing was isolated. The resumed real-source run completed without that blocked request. No telemetry exception was requested. A regression checks that the PDF runtime does not import ONNX.

## Test results

| Verification | Result |
| --- | --- |
| Backend suite | **138 passed**, 4.86 seconds; includes 57 additional Day 2 cases |
| Existing Day 1 source-data/real-HTTP audit | **153 checks passed** |
| Day 2 source-byte, arithmetic, temporal and HTTP audit | **628 checks passed**, zero failures |
| React/jsdom with actual local HTTP | **12 scenarios passed**, including existing inspection, failures/recovery, digest counts, results and management evidence |
| Next.js production validation build | Passed |
| TypeScript and dependency compatibility | Passed |
| SQLite integrity | `ok` |
| Live Gemini | **Not run: key unavailable** |
| Real browser/mobile QA | **Not verified here** |

Synthetic values are confined to explicit fault/boundary tests and temporary test databases. UI/API examples use real saved sources. One non-failing Starlette/httpx deprecation warning remains.

Twenty real local seven-day digest requests measured **41.89 ms median, 48.11 ms maximum**. Re-analysis using cached PDFs took **20.29 seconds**; the subsequent warm CLI pass took **0.12 seconds** and correctly retained exit 1 for missing/unsupported attachments. A resumed live-source batch took 398.54 seconds and reused earlier work: this is not a complete cold-run benchmark. Cold-start and real-mobile targets remain open.

## Verify in the existing project

1. Activate the existing Python environment. If it previously installed PyMuPDF 2, run `python -m pip uninstall -y pymupdf_layout pymupdf4llm onnxruntime`, then `python -m pip install -r backend/requirements.lock.txt` and `python -m pip install --no-deps -e backend`.
2. From the repository root, start/restart `python -m uvicorn finn.main:app --host 127.0.0.1 --port 8000`. In the frontend terminal run `npm run dev` from `frontend`. Frontend dependencies are unchanged; reinstall only if missing locally.
3. Open `http://localhost:3000`. Inspect TCS, HDFCBANK, LAURUSLABS and ASTRAL as before. Source failures and age must remain visible beside retained snapshots.
4. Load **Signal Inbox · Day 2** for 24 hours and 7 days. Confirm the displayed range and `scanned = surfaced + buried`. Compare with `http://localhost:8000/api/push/digest?window=7d&price_threshold=3.0&vol_threshold=2.0`.
5. Select **30 days** for TCS/Polycab tables. Compare the values above, expand evidence, and choose **Open saved PDF** to inspect the cited page. EBITDA must remain blank. Inspect Bajaj Finance/Trent names, roles, dates and profile labels. Ambiguous results and unsupported attachments must retain review/unavailable states.
6. Change thresholds and reload. Price uses `abs(return) >= threshold`; volume uses `ratio > threshold`. An absent historical volume alert may reflect missing baseline history; the API exposes per-holding evaluable-session counts.
7. Stop the backend and reload the digest: previous results should clear and a recoverable error should appear. Restart and retry. This does not alter source evidence.
8. Run `python -m pytest backend/tests -q` and `python scripts/verify_day2.py --db data/finn.sqlite3 --base-url http://localhost:8000`. For automated integration, stop your servers first, build the frontend once, then run `python scripts/run_integration.py --out verification/day2-integration`. Test outages affect only a temporary database.

To regenerate analysis on your existing database, run `python -m finn.push_ingest --db data/finn.sqlite3 --days 30 --workers 3`. It reuses valid work. Set `GEMINI_API_KEY` privately in your local shell and add `--use-model` for live adapter validation; do not commit or paste credentials into reports. The backend does not auto-load `.env`. A separate Windows download is not automatically synced by this workspace update.

## Remaining gates

1. Live Flash behavior, usage/cost, confidence calibration and classification accuracy need validation with a configured key.
2. Broader structured extraction remains Day 2 work: complex layouts, damaged OCR and multi-person events need supported extraction or explicit manual review. Two successful table examples do not close this gate.
3. Three ZIPs, one missing attachment, BSE fallback and exchange completeness remain unresolved. Unknown/failed items stay visible.
4. Earlier live Yahoo refreshes had invalid latest-session fields. The newer complete saved snapshot remains protected and refresh failure metadata stays visible. Cold-start targets and durable deployed storage remain open.
5. Full mobile UI, real-browser QA, deployment, repository publication, actual AI conversation export and final submission packaging remain later phases. No production deployment or email dispatch occurred.

## Updated files

- Backend: `classifier.py`, `model.py`, `evidence.py`, `results_enricher.py`, `management_enricher.py`, `cross_signal.py`, `push.py`, `push_ingest.py`, `pdf_runtime.py`, `pdf_worker.py`, `documents.py` and `main.py` under `backend/finn/`.
- Frontend: `frontend/app/PushDigest.tsx`, `frontend/app/page.tsx`, `frontend/tests/integration.mjs`.
- Tests: `backend/tests/test_push.py`, real `backend/tests/fixtures/day2/` documents and existing PDF-test imports.
- Reproduction: `scripts/verify_day2.py`, `scripts/verify_day1.py`, `scripts/run_integration.py`.
- Setup/progress: backend dependency files, `.env.example`, `README.md`, `docs/build-history.md`, `docs/day1-status.md` and this report.
- Logs/API responses: `verification/day2-tests.txt`, `verification/day2-pytest.xml`, frontend validation logs and `verification/day2-integration/`.
- Source persistence: the existing `data/finn.sqlite3`, with source bytes deduplicated by SHA-256. No new database copy was promoted.

Implementation references: [PyMuPDF process guidance](https://pymupdf.readthedocs.io/en/latest/recipes-multiprocessing.html), [Gemini structured output](https://ai.google.dev/gemini-api/docs/generate-content/structured-output) and [GenerateContent API](https://ai.google.dev/api/generate-content). The official brief and reviewed master plan remain the baseline.
