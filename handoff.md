# FINN — AI continuation handoff

Prepared 1 November 2026. This document describes the consolidated source pack. Read it before older checkpoints. The user's existing Windows project is usually `X:\finn_day1_verification_kit\finn`.

**Local verification update — 3 November 2026:** the actual Windows database now passes **58/58** engineering acceptance checks, 391 backend tests, 60 frontend checks and the production build. The historical 52/58 references below describe the delivered pack. Read [current brief coverage and remaining limits](docs/assessment-coverage-2026-11-03.md) and the [repair evidence](verification/acceptance-repair-2026-11-03/README.md) before continuing. Semantic/source-depth, actual-device and release gates remain separate.

## What the user wants

A nearly finished, mobile-first financial research product for the ENAM assessment, preserving the existing FastAPI/SQLite and Next.js structure. Day 4 implementation and visual polish are present. The next work is local source/model acceptance and Day 5 release/submission preparation, not another frontend redesign. The user values concise updates, independent decisions, compact information density and working interactions.

The source pack is complete and dependency-locked; **the project is not certified as fully accepted or ready for unrestricted public deployment**. Missing provider/evidence/model results remain explicit. Do not convert passing tests into a claim of financial accuracy, universal ticker coverage or legal compliance.

Read in order:

1. `AGENTS.md`, `README.md`, `docs/final-pack-setup.md`, `docs/final-pack-status.md`.
2. `docs/master-execution-plan.md` and `docs/plan-review.md`. Official `docs/source-main.pdf` > `docs/source-reference.pdf` > reviewed plan/corrections.
3. `docs/frontend-architecture.md` and `docs/release-review.md`.
4. The relevant dated report under `docs/history/checkpoints` only when needed. The old 229-test handoff is retained under `docs/history/handoff-2026-10-31.md` and is historical.

## What is implemented

| Phase | Implementation present | Acceptance limit |
| --- | --- | --- |
| Day 1 | Exact assessment universe, EOD/source ingestion, immutable raw/PDF bytes and hashes, SQLite snapshots/history, market arithmetic and freshness guards | Provider/calendar/source coverage must still be inspected on the user's local data. |
| Day 2 | 24h default plus explicit windows, all 17 categories, critical-content overrides, routine inspection/burial, market alerts, results/executive enrichments, uncertainty states | OCR/nonstandard financial layouts can abstain. Surfaced/review items are not all confirmed material events. |
| Day 3 | Primary-source company workspace, durable research jobs/SSE/polling, four-period Say–Do structures, reported financials/annual forensics, evidence links and accounting/period guards | General source discovery remains bounded by reviewed document hosts. Several results require source/model or semantic review; earlier live acceptance was 52/58. |
| Day 4 | Routed mobile app, real saved-data API integration, search/filtering/sliders/pagination, interactive charts/tables, evidence dialogs, settings/themes, minimal toasts and offline shell | Captured-source browser QA is not a fresh model run or physical iOS/Android/Safari/screen-reader certification. |
| Day 5 | Source packaging, setup/cleanup instructions and this handoff | Deployment, licensing/permissions decisions, actual build-history export and submission remain. |

Do not hardcode a claim that every Day 1–3 gate is accepted. A partial record can be the correct result when primary facts, speaker roles, basis or target horizon are unsupported. Never force a numerical Say–Do verdict to make a demo look complete.

## Architecture and files

- `backend/finn/main.py`: FastAPI routes, capabilities, security and read-only review controls.
- `storage.py`: raw/snapshot/history persistence; keep source identity and observation time intact.
- `finance.py`, `market_data.py`, `nse_market.py`, `calendar.py`: deterministic financial/market calculations, completed-session and freshness handling. Keep adjusted returns separate from raw OHLC/volume. The prior-20 volume baseline excludes the trigger session.
- `push.py`, `classifier.py`, `push_ingest.py`, `results_enricher.py`, `management_enricher.py`: Inbox classification and enrichment; uncertain/critical filings must stay inspectable.
- `pull.py`, `documents.py`, `transport.py`, `transcript_rag.py`, `transcript_context.py`: source discovery/download/text/evidence. HTTPS reviewed hosts, bounded downloads/parsing and same-host redirects remain enforced. Screener is discovery/staging, not primary analytical evidence.
- `say_do.py`, `say_do_model.py`, `annual_forensics.py`, `forensic_analyzer.py`, `pull_reasoning.py`: guidance/actual matching and conservative financial interpretation. Units, currency, accounting basis, metric definition, duration, fiscal calendar and source support must align. Source quote presence is not semantic entailment.
- `pull_jobs.py` and `dev.py`: durable single-worker lifecycle. `scripts/run_local.py` starts the local API/worker/frontend; avoid running a second worker or a concurrent finalizer on the same DB.
- `research_views.py`, `workspace_api.py`, `workspace_projection.py`: saved-data workspace/detail projections.
- `frontend/app/workspace/Workspace.tsx`: persistent shell, four main navigation items, ribbon, settings and source capability state.
- `workspace/cache.ts`: shared request coalescing and bounded page-memory snapshots. 30s freshness; retained snapshot up to 5min while revalidating. Failures stay visible and cannot be overwritten by an invalidated older response. Financial API data is not persisted to localStorage.
- `terminal/Inbox.tsx`, `workspace/Radar.tsx`, `terminal/Portfolio.tsx`, `workspace/CompanyHub.tsx`, `terminal/Research.tsx`: main saved-data interactions. Keep legacy components used by tests; their presence does not mean they are safe to delete.
- `terminal/Chart.tsx`, `workspace/FinancialVisuals.tsx`, `workspace/market-style.ts`: charts plot returned values. Universe green/red/gray follows first/last displayed adjusted close; separate 1D badges may have the opposite sign. Native sliders/tables provide accessible alternatives. Missing values are not zero.
- `Sheet.tsx`: bounded native dialog, scrolling body, retained header, optional pinned actions and visible-viewport handling.
- `Toasts.tsx`: one ephemeral, dismissible notification, placed inside the active modal when necessary. No history/telemetry is collected.
- `workspace/EvidenceLayer.tsx`, `EvidenceButton.tsx`, `SourceInspector.tsx`: primary citations, URL state, quotation/PDF controls, integrity metadata and original links.
- `workspace/ResearchTelemetry.tsx`: grouped saved source/model gaps, original records and suggested next actions. It makes no provider request and does not clear failures.

## Routes and API boundaries

Main views: `/inbox`, `/radar`, `/research`, `/universe`, `/sources`, `/about`.

Company views: `/research/{ticker}`, `/say-do`, `/forensics`, `/filings` beneath that company. Detail routes include `/inbox/{filingId}` and `/radar/{alertId}`. Existing `/portfolio` and older symbol links redirect; preserve aliases. Use `backend/finn/universe.py` as the universe authority. ZOMATO maps to ETERNAL; ambiguous historical TATAMOTORS requires an explicit TMPV/TMCV choice and must not splice histories.

Key reads include `/api/portfolio/overview`, `/api/capabilities`, `/api/universe`, `/api/market/{ticker}`, `/api/push/digest`, `/api/push/filing/{id}`, `/api/push/alert/{id}`, `/api/push/company/{ticker}`, `/api/pull/{ticker}`, job lookup/status/events and `/api/evidence/{sha256}` PDF/metadata endpoints. Use the actual routes in `main.py` for exact schemas. Archived OpenAPI JSON is a historical contract, not guaranteed current.

Research runs require explicit `POST /api/pull/{ticker}/jobs`. `--public-review` disables job POSTs and starts no worker; UI reflects capabilities. Owner operation uses the durable worker and explicit model flag. GET views must not trigger model jobs. Do not introduce login, payments, subscriptions or browser push subscriptions; “Push” here refers to the intelligence Inbox.

## Setup and private data

Use Python **3.12** for the Windows environment; the user's earlier Python 3.15 setup failed building PyYAML. Use the tested Node 24 family and `npm ci`. Exact dependency locks are included. No installed environment or dependencies are shipped.

The pack deliberately contains **no API key, .env, SQLite database, generated research cache or local QA override**. The user retains a large `data/finn.sqlite3` and may have other databases. Do not request/upload secrets. Do not delete databases or their WAL/SHM/journal companions. Do not replace a populated database with an empty one.

The recommended existing-folder update uses outer `manage_existing.py --check --cleanup`, then `--apply --cleanup`. It checks every payload before writing, refuses unknown source edits/symlinks, keeps private/Git/dependency paths, backs up changed source and moves recognised caches/history to a dated sibling archive. Review its receipt. Unknown local material stays untouched. There is no force option. Do not apply old incremental ZIPs after this pack.

Run from the project root after dependency setup:

```powershell
.\.venv\Scripts\python.exe scripts\run_local.py --build --production --db data\finn.sqlite3
```

Assessment-only: add `--public-review`. An explicit owner `--use-model` session requires the user's locally configured accessible model IDs/key/quota and cannot be combined with read-only mode. The supplied `.env.example` deliberately does not promise a working model ID. One previous local preflight passed with `gemini-3.5-flash-lite`, but that is historical evidence, not a current availability/quota guarantee. Never put keys in `NEXT_PUBLIC_*`.

## Verified checkpoint and remaining gaps

The latest UI/source checkpoint passed 356 backend tests, 60 frontend checks, TypeScript and production build. Captured public-source replay passed 14 JSON routes, saved-PDF SHA-256 integrity and read-only POST enforcement. Chromium checked mobile/desktop views, both themes, chart scrubbing, 390px layout, modal feedback and 390×520 settings bounds. New full-pack verification scope/results are in `docs/final-pack-status.md` and the included logs.

Saved-source examples inspected during the previous UI refinement:

- INFY: three `ModelUnavailable` stages and a document excluded from the full earnings-transcript audit. Do not infer “daily quota exhausted” from `ModelUnavailable` alone.
- POLYCAB: a non-PDF response and two missing BSE attachments.
- DEEPAKNTR: certificate failures plus unavailable model stages. Keep TLS verification enabled; inspect actual trust/provider conditions locally.
- SUZLON: missing exact `www.suzlon.com` host approval was fixed after checking the official issuer origin. Existing stored error records are retained; a future explicit owner refresh is required to build a new snapshot. No live PDF/model refresh was run for that policy change.
- TCS: no saved source errors in the inspected snapshot, but missing model metadata and partial coverage are not proof of completeness.

These examples came from labelled captured public data, not a new inspection of the user's entire private Windows DB. The previous local live/source acceptance result **52/58** remains unresolved. Do not claim 100%, full autonomous forensic accuracy or universally working arbitrary tickers from test counts. The UI must retain unsupported/review-required states.

## Next work, in order

1. Apply/check the clean source pack locally while all FINN processes are stopped; retain the receipt and private data. Restore dependencies, rerun offline checks, launch the production build and inspect the user's saved data.
2. Obtain the actual local acceptance/preflight summaries if needed. Diagnose real provider errors/model configuration and certificate/document availability; do not guess or rotate keys to conceal failures. Refresh only the affected company/stages with authorised quota instead of repeatedly re-running the whole model finalizer.
3. Review remaining semantic acceptance gates against the primary pages: speaker/horizon/basis alignment, supported statements/annual facts and unseen-ticker coverage. Keep numerical verdicts withheld if comparability is absent.
4. Perform physical phone/Safari, soft-keyboard, reduced-motion/transparency and screen-reader checks. Avoid redesigning the established UI. The user's design preference is compact premium institutional fintech with tinted glass, DM Sans, the existing FINN monogram/glyphs, restrained motion and semantic chart colors. Only the selected bottom navigation item shows its text.
5. Resolve data/provider redistribution permissions and PyMuPDF AGPL/commercial licensing decisions before publication. No project-wide open-source license was invented; do not add one on the user's behalf without a deliberate decision. `/about` is a disclosure, not a legal certification. No SEBI registration or ENAM/issuer endorsement is claimed.
6. Choose an explicitly authorised deployment target, persistent/private SQLite storage, read-only assessment mode and operator contact/privacy details. A quick Cloudflare tunnel is temporary and requires the user's machine to stay awake; old tunnel URLs are not durable deployment evidence.
7. Prepare repository/submission materials and **actual** AI build-history export. `docs/build-history.md` is a decision log, not an exported conversation. The brief's covering email destination/subject are in the official plan; do not send email or publish without a specific user instruction.

## Guardrails for continuing work

Do not replace real-data gaps with fake charts, backfill invented statements, hardcode issuer-specific beat/miss conclusions or disable URL/TLS/security guards. Do not add external analytics/font tracking or account/payment flows. Preserve source freshness/disclaimers/evidence access in context; legal/privacy/licensing information belongs in Settings/About rather than a repeated website footer.

Keep changes bounded, test changed behavior, record the exact verification scope and report any remaining release blocker. Separate successful compilation/unit tests from live provider results and independent semantic validation. Preserve the user's workspace and all original data.
