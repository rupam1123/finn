> Historical checkpoint. Current status: [final pack status](../../final-pack-status.md). Current setup: [final pack setup](../../final-pack-setup.md).

> Latest frontend update: [restructuring report](frontend-restructure-report.md), [corrected blueprint](../../frontend-architecture.md), and [setup](frontend-restructure-setup.md). Earlier checkpoint details below remain historical.

# FINN pre-final status — 1 November 2026

The Day 4 product interface is implemented against the existing FastAPI/SQLite contracts. This is a functional local product build, not a mock data prototype. It is **not a certification that all Day 2–3 live model gates are complete**, and an overall 90% acceptance claim would be misleading while those gates remain open.

## Delivered product

| Area | Implemented behavior |
|---|---|
| App shell | Direct Inbox, Research, Portfolio and Source health routes; browser history; responsive sidebar/bottom navigation; global keyboard search; persistent settings; error boundary and 404 recovery |
| Push | 24-hour default, explicit 3/7/30-day and latest-session windows, scanned/surfaced/buried telemetry, inspectable routine bucket, 17 announcement watches, threshold sliders/number inputs, text/company/category filters, priority/date sorting |
| Inbox cards | Backend classification and review state, source-bound results tables, backend-computed QoQ/YoY, management event/profile details, observation timestamps, source links, local bookmarks, saved filter, pagination, CSV export |
| Market signals | Saved adjusted returns and raw-volume multiples, related/retrospective filing context with no causal attribution; company/text filtering and pagination |
| Pull | Arbitrary NSE symbol submission, saved security-master name/typo suggestions, core/showcase shortcuts, cached research reads, explicit discovery/refresh, durable job progress, retryable requests and active-job recovery across reload/navigation |
| Research | Overview, four-period Say–Do ledger, guidance, primary financial statements, cash/leverage output, investment case, governance excerpts, source/engine telemetry, preserved review/abstention states |
| Charts | Saved adjusted EOD price, separate raw OHLC candles and raw-volume modes; 10/30/60 sessions; pointer and keyboard/session slider; accessible data table; portfolio sparklines |
| Evidence | Exact quote drawer, visual-transcription warning, safe original link, observation time/hash, immutable saved-PDF loading, native PDF viewer and page control, missing-PDF/transport failure states, quote copy feedback |
| Source library | Type/search filtering, pagination, saved PDF and original links, module excerpts |
| Portfolio | All 18 fixed holdings, real return breadth and a tappable saved-session map, search, sorting, card/table switch, accepted session/prices, company research navigation; no invented aggregate portfolio return |
| Source health | Cache/provider freshness, connection/coverage metrics, compiled Screener tables and linked sources explicitly marked staging, partial-snapshot empty states |
| PWA | Manifest/icons, install prompt when browser-supported, explicit offline status; static fallback only; no financial/API data silently cached by the service worker |
| Deliberate placeholders | Only QR handoff, audio and copilot are Planned, as authorized |

## Design and licensing

The latest reference revision uses compact self-hosted DM Sans typography, a soft grey canvas, white rounded cards and restrained glass on navigation/sheets. Existing icon vectors and the FINN monogram are unchanged. Card blur and entrance effects were removed to reduce navigation work. Newsreader remains a licensed dependency; OFL/ISC notices and a pinned dependency inventory are included. No proprietary Apple, Tiempos or Söhne font or reference-photo asset was introduced. The exact font in the supplied screenshots could not be identified from the images. See `docs/release-review.md` for this revision's privacy, security, accessibility and licensing review.

Visited Research and Portfolio views retain state. The saved-only portfolio API avoids decoding large research snapshots just to check availability. Public-review mode is read-only, with no worker; owner-local discovery remains available. A linked `/about` page explains research limitations, sources, privacy, licenses and accessibility. These changes do not grant financial-data rights, settle SEBI applicability or resolve the PyMuPDF source-license decision.

## Verification scope

- **340 backend tests passed**, including exact/prefix/typo security search, saved-only portfolio overview, and symbol-scoped resumable jobs. No network/model call is needed by the new read-only endpoints. The suite reports one upstream FastAPI/Starlette deprecation warning.
- TypeScript check and optimized Next.js production build passed. All six app URLs (`/`, `/inbox`, `/research`, `/portfolio`, `/sources`, `/about`) build, with 404 handling.
- React/jsdom behavior checks cover pagination, bookmark/company filters, all 17 settings and threshold/window query values, routes, unique search labels, Escape modal dismissal, offline status, evidence escaping/link safety, stale suggestion responses, completed-job reread and partial-source rendering. Four static-only service-worker checks pass. Three existing Pull race/polling/refresh regressions pass. Six new market-visual checks cover adjusted/raw chart modes, missing OHLC, flat/zero-volume input, real category counting, breadth with missing returns, exact holding navigation and motion/dock declarations.
- Production browser QA used the **real backend**, a scratch SQLite cache imported from the user's captured public verification reports, three older actual Screener snapshots, and hash-matched real PDF fixtures. It did not call Gemini or invent prices, filings, figures, model success or verdicts. A visible replay banner identifies this mode; it is not shipped as a demo database.
- Browser checks cover applied thresholds, ticker/category filters and actual Polycab financial values/citations; exact evidence drawer; CSV download; chart range; four-period ledger; source search and empty results; refresh confirmation; portfolio cards/table/search; narrow-screen navigation and dialogs; actual saved 60-page PDF rendering.
- Narrow-screen QA uses the real app in a browser iframe with **375 CSS pixels of usable width**, not an iPhone/iOS emulator. The screenshots include the frame context. Inbox, Research and Portfolio had no document-level horizontal overflow; financial tables intentionally scroll within their container. Desktop QA uses the available Chromium viewport. Physical Android, iOS Safari, PWA installation and touch-device PDF behavior remain local review items.
- Build/test logs and the final browser checklist are in the package's `verification` folder. Screenshots are in `screenshots`. Older project verification files are historical, not new acceptance results.

## Backend integration changes

A saved-only `/api/portfolio/overview` endpoint supplies all holdings without source/model calls. `/api/universe` ranks exact symbols, prefixes, word matches and close spellings. `GET /api/pull/{ticker}/jobs` exposes the active durable job so the UI can resume observation. Existing POST enqueue and single-worker processing remain intact. The frontend uses same-origin `/api` rewrites; the local launcher starts API, worker and Next together and handles the old localhost frontend API setting for that process.

## Remaining work by day

| Phase | Remaining / qualification |
|---|---|
| Day 1 | Existing local ingestion/storage regressions pass. Keep and reuse the user's actual database; this package excludes private settings/databases. Refresh public sources only when needed. |
| Day 2 | The user's latest captured full run still had five failing live enrichment samples, incomplete model review for some readable filings, and two unavailable sources. UI support is implemented; a passing UI/build does not fix those source/model outcomes. |
| Day 3 | Four-period workspaces and primary citations display, but many numerical comparisons still abstain for missing actuals/basis/speaker verification. The captured core model stage failed when daily quota was exhausted. Cached issuer/profile consistency for annual cash outputs also needs review (including a lender-style abstention in a non-lender workspace). Verify affected source identity/profile and regenerate the affected snapshots before relying on the cash analysis. |
| Day 4 | Implemented and locally tested as described. Final acceptance requires the user's actual populated DB, supported Gemini configuration/quota for new model work, and physical phone review. Unsupported extraction remains explicit. |
| Day 5 | Resolve/re-run the targeted Day 2–3 acceptance gaps, final phone/PWA review, deployment configuration/HTTPS, repository cleanup, actual AI history export, submission write-up and email. No deployment, repository publish or email was performed. |

The most recent user-supplied acceptance report was **52/58**, not 58/58. This build improves the product and integration but does not relabel those six live gates as passed. No second-account key rotation or fabricated comparisons are part of the solution.

## Run and review

Follow `docs/day4-local-review.md`. Start with the existing database in production mode using `scripts/run_local.py --build --production`; review saved behavior before starting paid model refreshes. Report any local error with the URL/ticker, action, browser console error and backend traceback, without sharing API keys. Deployment and submission stay separate from this local source update.
