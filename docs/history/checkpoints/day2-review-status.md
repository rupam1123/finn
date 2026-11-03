> Historical checkpoint. Current status: [final pack status](../../final-pack-status.md). Current setup: [final pack setup](../../final-pack-setup.md).

# Day 2 source review — 30 October 2026 (IST)

The backup is intact, the recovered working database is healthy, and processing/review results are saved in the existing FINN project. **Day 3 has not started. Day 2 is not fully accepted:** source access, OCR, broader extraction and independent accuracy evaluation remain open.

## Coverage and review

The fixed cohort is the 30-day window ending **29 October 2026, 04:51:36 UTC** (10:21:36 IST). Keeping this cutoff avoids moving the target while processing.

| Measure | Final result |
|---|---:|
| Original database filings / versions | 232 / 232, all preserved |
| Filings in the frozen review cohort | 224 |
| Analysis records in that cohort | 224 / 224 |
| Documents with at least some usable extracted text | 219 / 224 (97.8%) |
| Originally pending filings attempted | 123 / 123 |
| Originally pending with usable source text | 120 / 123 |
| Originally pending still source-blocked | 3 |
| Original uncertain queue triaged | 210 / 210 |
| Reviewed named category in that queue | 160 |
| Retained as unclassified in that queue | 42 |
| Source/classification follow-up in that queue | 8 (5 source problems + 3 further reviews) |
| Source-bound corrections beyond classifier-v4 rules | 27 |
| Categories changed versus existing Windows analyses | 32 |
| Hidden/buried filings in this reviewed cohort | 0 |

“Processed” means the pipeline handled the document and found usable text. It does **not** certify every page, number, accounting basis or event. Image-only pages can coexist with a readable cover. The review ledger records exact filing revisions, PDF hashes, pages and cover/event quotes.

All 224 general review flags remain set deliberately: this was a primary-event category review, not certification of whole-document materiality and extraction. The UI therefore does not claim that 210 entire filings have been fully verified. The 42 unclassified records are not silently discarded; some, such as guarantees and fire-related disclosures, can be important.

**Accuracy:** no defensible overall classification accuracy percentage is available. There is no independent labeled evaluation set. Source-backed corrections and passing regression/citation tests are evidence of improvement, not a 100% accuracy claim. Gemini was not called in this run because no API key was configured; previous Gemini outputs remain preserved in the database.

## What changed

- Classifier-v4 prioritizes specific primary subjects, including repeated subject headers. Earnings calls, presentations, employee stock allotments, ESG ratings and statutory insider-trading references are handled more carefully. Historical meeting references no longer masquerade as the current event.
- Saved category decisions are bound to both the filing content hash and PDF hash. A changed source invalidates the review; a category decision cannot authorize burial. Updated review records invalidate cached analyses.
- Zero-page PDFs now fail extraction. Entirely unreadable PDFs have an explicit state. A failed or unreadable refresh retains the previous readable source and analysis without advancing their source timestamps; the failed attempt remains visible.
- Two previously unusable saved PDF responses were replaced by readable fresh primary downloads. Their old response bytes remain preserved. The recovered TCS results release and HDFC Bank results document are categorized as results; extraction remains conservative where bases or image tables are ambiguous.
- Management-v3 extracts Persistent's explicit Rajesh Gharpure resignation sentence, including role and effective date. Tests reject missing dates, impossible dates and tentative actions. No external biography was invented.
- UTF-8 subprocess output and explicit SQLite handle closure retain the Windows fixes. Locale tests simulate CP1252/ASCII here; this is not a new native Windows test run.
- Reproducible frozen-cohort processing, review, preservation audit and finalization scripts were added. The finalization workflow owns an isolated staging database and publishes it only after integrity checks.

## Integrity and preservation

The uploaded backup passes SQLite integrity and foreign-key checks. All **187 original raw objects** match their saved SHA-256 values. The original file is unchanged:

`eb7f829c35a90c6a93dcc822e206ba55f16d8361226d8e650a299fa7b99ca63c`

The updated database contains **303 raw objects**. Every original raw response, filing, filing version, attempt and run is preserved exactly. All original analysis, market, fundamentals, filing-coverage, primary-sample and universe snapshots are retained. Current document snapshots and new versioned analyses add the corrected results.

An interrupted working copy failed integrity checks and was preserved for diagnosis. It was not used as a recovery source. The final database was rebuilt from the immutable upload and passed integrity checks before and after publication. The exact cause of the interrupted-copy corruption is not established; durable deployment storage remains a later acceptance requirement.

Database integrity does not prove exchange-wide completeness. This verifies the supplied records and frozen cohort, not that NSE/BSE returned every possible disclosure.

## Verification results

| Check | Result |
|---|---|
| Full backend suite | **199 passed**, one non-failing Starlette/httpx deprecation warning |
| Frozen 224-filing revision/source audit | **444 checks passed** |
| Saved-data Push audit | **790 checks passed** |
| Real local HTTP Push audit | **795 checks passed** |
| Day 1 data / HTTP integration | **153 checks passed** |
| React/jsdom integration using real HTTP | **12 scenarios passed** |
| Frontend production build | Passed |
| TypeScript check | Passed |
| Preservation / final SQLite integrity | Passed |
| Four primary APIs | TCS 29, HDFCBANK 17, LAURUSLABS 18, ASTRAL 29 transcript pages |
| Warm 7-day digest HTTP benchmark | 20 requests; **44.04 ms median**, **54.19 ms maximum** |

The React checks cover actual TCS results, Bajaj management evidence, counts, coverage, errors, retries and stale-response clearing. The outage used in integration is explicitly synthetic and confined to a temporary database; company and market data are real saved records. Browser/mobile QA and live Gemini validation were not performed in this run.

The HTTP audit used the rolling window at execution time: **212 filings**, versus the frozen 224. The difference is older records rolling out of the window, not data loss. Benchmark timings are local warm-cache measurements, not cold provider or mobile-network latency. Initial source processing took **358.51 seconds** with verified-byte reuse and missing-source fetches; subsequent saved-byte review processing took **19.56 seconds**. These are different workloads.

## Remaining source/classification issues

| Issuer | Issue | Current handling |
|---|---|---|
| HDFCBANK | Earnings-presentation attachment did not yield a validated readable PDF, including a fresh retry | Visible, source unavailable |
| TMPV | Filing metadata has no attachment | Visible, source unavailable |
| SUNPHARMA | Resignation attachment is ZIP | Visible; PDF pipeline does not unpack it |
| TRENT | Resignation attachment is ZIP | Visible; PDF pipeline does not unpack it |
| PERSISTENT | Resignation attachment is ZIP | Visible; PDF pipeline does not unpack it |
| INFY | Results-release notice also schedules an earnings call | Multi-event categorization review remains |
| ETERNAL | Visual inspection identifies Q2FY27 shareholder letter/results, but page text is incomplete | OCR and financial-table validation remain |
| DEEPAKNTR | Internal preference-share funding with OCR errors | Taxonomy and numeric validation remain; no external-funding claim |

The three source-blocked items from the original 123 are **TMPV, SUNPHARMA and PERSISTENT**. The remaining two source problems were already in the analyzed portion of the backup.

Enrichment status across the cohort is **3 source-extracted management records, 2 partial results records, 30 requiring extraction review, and 189 without an enrichment payload**. Broader bank/NBFC tables, image-heavy financial statements and multi-person management disclosures remain incomplete. Existing BSE fallback, cold-latency and real-phone validation gates also remain open.

## Reproduce locally

Run from the existing `finn` root, with the backend environment active and dependencies installed:

```powershell
$env:PYTHONUTF8 = "1"
python -m pytest backend/tests -q
python scripts/run_integration.py --out verification/manual-integration
```

The integration runner expects an existing frontend production build. If this is a fresh checkout, run `npm ci` and `npm run build` inside `frontend` once first. Stop existing processes on ports 8000 and 3000 before running the integration script.

To reproduce the preserved-source audit:

```powershell
python scripts/verify_day2.py --db data/finn.sqlite3 --out verification/manual-day2-audit.json
python scripts/audit_backup_preservation.py --backup "PATH_TO_UNCHANGED_WINDOWS_BACKUP.sqlite3" --db data/finn.sqlite3
```

The full source-review workflow is tied to this exact backup and cohort. Its `--resume` option retries only unavailable PDFs before reapplying the recorded reviews. Source-processing exit code **1** means incomplete source coverage; it is intentionally not converted into a successful-completeness claim.

These changes are in the shared project workspace. They do not automatically modify the separate Windows installation. Stop the Windows backend and retain its current database backup before copying an updated database there. No API key is included in any deliverable.

## Updated files and evidence

- [data/finn.sqlite3](sandbox:/workspace/scratch/75cc33983803/finn/data/finn.sqlite3)
- [backend/finn/classifier.py](sandbox:/workspace/scratch/75cc33983803/finn/backend/finn/classifier.py)
- [backend/finn/documents.py](sandbox:/workspace/scratch/75cc33983803/finn/backend/finn/documents.py)
- [backend/finn/management_enricher.py](sandbox:/workspace/scratch/75cc33983803/finn/backend/finn/management_enricher.py)
- [backend/finn/pdf_worker.py](sandbox:/workspace/scratch/75cc33983803/finn/backend/finn/pdf_worker.py)
- [backend/finn/push_ingest.py](sandbox:/workspace/scratch/75cc33983803/finn/backend/finn/push_ingest.py)
- [backend/finn/source_review.py](sandbox:/workspace/scratch/75cc33983803/finn/backend/finn/source_review.py)
- [scripts/run_integration.py](sandbox:/workspace/scratch/75cc33983803/finn/scripts/run_integration.py)
- [scripts/verify_day2.py](sandbox:/workspace/scratch/75cc33983803/finn/scripts/verify_day2.py)
- [scripts/review_day2_batch.py](sandbox:/workspace/scratch/75cc33983803/finn/scripts/review_day2_batch.py)
- [scripts/apply_day2_source_review.py](sandbox:/workspace/scratch/75cc33983803/finn/scripts/apply_day2_source_review.py)
- [scripts/audit_backup_preservation.py](sandbox:/workspace/scratch/75cc33983803/finn/scripts/audit_backup_preservation.py)
- [scripts/finalize_day2_review.py](sandbox:/workspace/scratch/75cc33983803/finn/scripts/finalize_day2_review.py)
- [backend/tests/test_review_reliability.py](sandbox:/workspace/scratch/75cc33983803/finn/backend/tests/test_review_reliability.py)
- [backend/tests/fixtures/day2/cover-regressions.json](sandbox:/workspace/scratch/75cc33983803/finn/backend/tests/fixtures/day2/cover-regressions.json)
- [backend/tests/fixtures/day2/persistent-resignation.json](sandbox:/workspace/scratch/75cc33983803/finn/backend/tests/fixtures/day2/persistent-resignation.json)
- [backend/tests/fixtures/day2/zero-page-source.pdf](sandbox:/workspace/scratch/75cc33983803/finn/backend/tests/fixtures/day2/zero-page-source.pdf)
- [verification/day2-backup-review/final-coverage.json](sandbox:/workspace/scratch/75cc33983803/finn/verification/day2-backup-review/final-coverage.json)
- [verification/day2-backup-review/source-review-ledger.json](sandbox:/workspace/scratch/75cc33983803/finn/verification/day2-backup-review/source-review-ledger.json)
- [verification/day2-backup-review/preservation.json](sandbox:/workspace/scratch/75cc33983803/finn/verification/day2-backup-review/preservation.json)
- [verification/day2-backup-review/tests-final.txt](sandbox:/workspace/scratch/75cc33983803/finn/verification/day2-backup-review/tests-final.txt)
- [verification/day2-backup-review/integration/summary.json](sandbox:/workspace/scratch/75cc33983803/finn/verification/day2-backup-review/integration/summary.json)
- [verification/day2-backup-review/integration/day2-audit.json](sandbox:/workspace/scratch/75cc33983803/finn/verification/day2-backup-review/integration/day2-audit.json)

No replacement project folder or new ZIP was created. Final packaging remains Day 5.
