> Historical checkpoint. Current status: [final pack status](../../final-pack-status.md). Current setup: [final pack setup](../../final-pack-setup.md).

# Day 3 delivery — 30 October 2026

## Acceptance status

**Day 3 is not fully accepted.** This delivery adds a working primary-document research and evidence workspace, durable jobs, four-period evidence ledgers, conservative financial parsers and validation reports. It does not claim a fully automated, semantically verified four-quarter Say–Do analyst. Numerical verdicts, broad financial layouts, working-capital extraction and verified bull/bear synthesis remain incomplete. The user explicitly chose to continue without a live model test.

## Implemented

- General symbol-based Pull ingestion using Screener for discovery only, NSE history and approved primary PDF hosts. No demo-symbol gate. KPIL was retrieved from its official issuer host after NSE attachments proved to be notices rather than transcripts.
- Speaker-labelled, topic-tagged, page-bound excerpts; reported-period detection; deduplicated quarterly coverage; explicit annual-report fallback and unavailable states. Speaker labels and target alignment are not automatically certified.
- Four-period source-evidence ledger with preceding-period commentary and delivered-period excerpts. Comparison helpers reject mismatched definitions, basis, units, currency, horizons, revisions and missing evidence. They do not promote arbitrary model output into verified verdicts.
- Strict annual CFO/PAT and borrowing-to-equity extraction for supported two-column primary statements, with subtotal/balance-sheet reconciliation, exact Decimal arithmetic and explicit missing/unsupported states. Deepak Nitrite real statement pages were visually checked. Reports remain separate where comparative figures differ. Industrial cash conversion is excluded when the lender profile is detected.
- Working-capital arithmetic guards and governance evidence retrieval. Automated working-capital fact extraction remains open; governance keyword hits are not adverse findings.
- Optional bounded model proposal and four-quarter reasoning adapters with quote/source-index validation. Results remain semantic-review-required. No live model call was made.
- Cached Pull API, durable SQLite job queue, progress polling and SSE, single-worker CLI, restart recovery, and additive React workspace with source-PDF links and cash/leverage figures.
- Cached partial research for all 18 portfolio and 5 showcase symbols, plus KPIL and ASTRAL. Cached availability is not analytical completeness.

## Validation

- **225 backend tests passed**, six non-failing warnings.
- **80.38% backend statement coverage** (1,680 / 2,090 statements). Coverage is not accuracy.
- Production frontend build and TypeScript check passed. Final build used `npm run build -- --webpack` after this environment denied Turbopack's helper port binding.
- Real local HTTP integration, existing React/jsdom scenarios and five new Pull UI scenarios passed. New checks include KPIL source evidence, Deepak Nitrite financial ratios, invalid input, disconnect handling and durable cold-job submission. Not real phone/browser QA.
- Final source audit: **25 cached companies, 1,300 citations, zero page/quote mismatches** after re-extracting original PDF bytes. Raw hashes checked. This is mechanical provenance, not semantic accuracy.
- INFY, DEEPAKNTR, HDFCBANK and unseen KPIL each have four reported quarterly transcript periods in the final cache. Numerical promised-versus-delivered judgments are still review-required.
- Original 303 raw response rows, 232 filings, 232 filing revisions, 325 Push analyses and 216 source reviews are unchanged and retained. Original Desktop project is unchanged.
- Test environment: Python 3.13.9, with exact versions recorded in `verification/day3-environment.json`. The original full Python 3.12 lock environment was not reproduced; lockfiles were preserved.

## Remaining issues

1. No end-to-end promotion of extracted guidance and actuals into semantically verified numerical Say–Do judgments. Four-quarter evidence coverage does not satisfy that requirement alone.
2. Broad annual/quarterly layouts, general working-capital cycle extraction, lender-specific financial extraction, OCR and ZIP disclosures remain incomplete. Cash/leverage automation currently proves only the supported real statement layouts; most companies abstain.
3. Bull/bear and narrative modules expose primary excerpts and optional review-required proposals, not fully verified synthesis. Model credential was absent; live model testing was explicitly waived.
4. Annual-report fallback uses page/topic retrieval, not a fully validated MD&A/directors-report section classifier. Ambiguous fiscal labels and revisions remain explicit.
5. Source hosts can return errors, and some latest reports exceed the 500-page limit. Provider completeness and latest-document completeness are not guaranteed. Existing Day 2 limitations remain.
6. The worker is deliberately single-writer. Queue recovery requires stopping other workers before `--recover`. Deployment security, rate limits, multi-process production behavior and real mobile QA remain later work.
7. Cold retrieval can take minutes; no <3-second cold performance claim. Full independent semantic/classification accuracy evaluation remains open.

## Run from project root

Install the existing backend lockfile and editable backend package, and run `npm ci` in frontend. Set `FINN_DB=data/finn.sqlite3` and `PYTHONPATH=backend` where needed.

```sh
python -m uvicorn finn.main:app --host 127.0.0.1 --port 8000
python -m finn.pull_jobs --db data/finn.sqlite3 --watch
# separate frontend terminal
cd frontend
npm run dev
```

Direct research (serialized writer; stop the worker first):

```sh
python -m finn.pull --db data/finn.sqlite3 --symbols INFY DEEPAKNTR HDFCBANK KPIL
python -m finn.pull --db data/finn.sqlite3 --warm
python -m finn.pull --db data/finn.sqlite3 --symbols KPIL --saved-only --force
```

Use `--use-model` only with a locally configured `GEMINI_API_KEY`. Never put credentials into frontend variables. API routes: GET `/api/pull/{symbol}`, POST `/api/pull/{symbol}/jobs`, GET `/api/pull-jobs/{id}`, GET `/api/pull-jobs/{id}/events`. Reads never scrape or call a model.

Validation:

```sh
python -m pytest backend/tests -q --cov=finn
python scripts/verify_pull_sources.py --db data/finn.sqlite3
python scripts/run_integration.py --db data/finn.sqlite3 --out verification/local-integration
```

Historical export manifests and handoff describe the imported baseline; this report and `day3-delivery-manifest.json` describe the updated delivery. Actual chat export remains separate from the build decision log.
