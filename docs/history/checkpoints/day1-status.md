> Historical checkpoint. Current status: [final pack status](../../final-pack-status.md). Current setup: [final pack setup](../../final-pack-setup.md).

# Day 1 checkpoint — 27 October 2026

> **Current status: [28 October reliability repair report](day1-reliability-report.md).** 81 backend tests, frontend build/type checking, 153 saved-data/real-HTTP checks and eight React/jsdom scenarios pass. The identified data-loss, notice-selection, refresh-visibility, amendment and date-window defects are repaired. Observed cold ingestion is 34.79s and cache reuse 0.95–1.17s. Live market data remains incomplete and is explicitly rejected; cold <3s and real-browser/mobile revalidation remain open. Day 2 has since started in the same workspace; see [current Day 2 status](day2-status.md). The checkpoint results below are historical.

**Core ingestion foundation implemented and validated; performance and deployment checks remain open.**

The reviewed master plan remains the project baseline. Its revision-1 corrections override conflicts in the original wording. Official brief > companion reference > reviewed plan. No Day 2–4 research/ranking features are claimed complete.

## What is built

- Local Git monorepo: Python FastAPI + SQLite backend; Next.js/TypeScript/Tailwind mobile development shell.
- Exact 18-stock mock portfolio and five showcase symbols; updated ETERNAL/TMPV identity and explicit handling of ambiguous historical TATAMOTORS.
- General NSE security-master ingestion (2,364 EQ records in this fetched snapshot).
- EOD adapter, prior-20-session volume math, adjusted 1D/5D return calculation, completed-session and corporate-action guards.
- NSE announcements ingestion, dissemination timestamps in UTC, deduplication, and preserved raw records/links/hashes.
- Arbitrary-symbol Screener discovery and six secondary staging tables, visibly ineligible for Pull claims until reconciled to primary documents.
- Approved-host PDF fetch and page-indexed source text, with no analytical claim verification implied.
- Read-only cache API; source observation timestamps and cache age. On-demand job orchestration belongs to Day 3.

## Verified results

| Check | Result |
| --- | --- |
| Offline financial/parser/storage/API regressions | 42 passed |
| Production frontend build | Passed |
| TypeScript check | Passed |
| Live EOD + six staging tables + announcements | 18/18 holdings plus unseen ASTRAL |
| EOD history | 30 completed sessions per company; latest 27 Oct 2026 |
| Unique stored announcements | 227, including ASTRAL's one filing |
| Primary transcript fetch/text extraction | 4/4 acceptance companies; 93 PDF pages total |
| Raw source objects preserved | 68 |
| SQLite integrity check after rebuilding | ok |
| API checks against populated database | Nine routes returned 200 through TestClient |
| Warm cached ASTRAL API | 6.06 ms median, 21 ms maximum over 20 in-process requests; not network/mobile latency |

## Required four-company acceptance set

| Company | Role | EOD sessions | Tables | 30-day filings | Transcript pages |
| --- | --- | ---: | ---: | ---: | ---: |
| TCS | IT | 30 | 6 | 19 | 29 |
| HDFCBANK | Bank | 30 | 6 | 19 | 17 |
| LAURUSLABS | Pharma | 30 | 6 | 5 | 18 |
| ASTRAL | Unseen ticker | 30 | 6 | 1 | 29 |

The full 19-company run and later targeted corrections are preserved separately. The original failed/partial runs remain in the checkpoint for auditability; `data/runs/final-validation.json` describes the final verified state.

## Findings fixed during validation

1. SOCKS support was required by this environment's HTTP transport.
2. The first database showed corruption during overlapping WAL-mode jobs. It was quarantined, rebuilt from source, and replaced with serialized transactions, rollback journaling and explicit connection closure. Added a concurrent-write integrity regression. This mitigates the observed problem; the precise underlying filesystem cause was not proven.
3. BSE returned HTTP 403. Transcript discovery now prefers NSE attachments; an older transcript can require 180 days of discovery independently of the 30-day digest. Laurus's July transcript was retrieved this way.
4. NSE uses `-` to indicate no attachment. Such filings remain valid records; the parser now preserves them with a null document URL, with a regression test.
5. Local DNS resolution was unavailable although proxy-mediated HTTPS worked. Document fetching accepts only fixed reviewed public hosts and rejects unsafe URL forms/cross-host redirects; it no longer performs redundant local DNS lookups.

## Explicit limits — do not mark these passed

- **Cold <3-second JSON target did not pass.** Observed individual Screener requests were roughly 5–9 seconds; combined cold ingestion takes longer. Cache/progressive loading is necessary. No real-phone latency target has been measured.
- **BSE fallback is not operationally verified:** API/PDF requests returned 403 here. NSE and the Astral issuer source worked. Expand tested provider fallbacks before calling the data layer resilient.
- **Browser interaction and real-mobile QA are not done.** Build/type checking passed, and servers reported successful startup, but loopback HTTP probes were refused in this execution environment. API checks used TestClient. Verify full frontend/backend interaction locally before the next product milestone.
- **Completeness is not guaranteed:** exchange response accepted and parsed does not prove all exchange disclosures were returned. Coverage is explicitly labelled in the cache.
- No verified financial analysis, classification, signal ranking, Say–Do verdicts, AI synthesis, four-quarter evidence coverage, production deployment or GitHub publication yet.
- Four primary samples prove fetch/extraction, not all-document coverage or claim entailment. Additional issuer domains need review. The web manifest is scaffolding, not a fully validated offline/installable PWA.
- The SQLite deployment volume and multi-process behavior need testing in the eventual host. The current writer is deliberately serialized.
- One non-failing Starlette/httpx deprecation warning appeared in tests, and yfinance emitted pandas deprecation warnings during live ingestion.

## Next execution step

1. Run the included backend and frontend locally and verify the four-company inspection flow in a browser.
2. Begin Day 2: separate 17-category classification from materiality; add critical-content overrides and unknown/review states before noise burial.
3. Add source-grounded results/management enrichment, then time-bounded nearby-filing links without causal claims. Test each module before integrating the digest API.
4. Keep audio/copilot/QR polish behind the two core workflow acceptance gates. Preserve the actual AI conversation export for final submission.

No email has been sent. Production deployment, external repository publication and the submission package remain later phases.
