> Historical checkpoint. Current status: [final pack status](../../final-pack-status.md). Current setup: [final pack setup](../../final-pack-setup.md).

> Latest appearance update: [compact glass, light/dark themes and motion](glass-motion-update.md). Earlier design/checkpoint details below remain historical.

# FINN frontend restructuring — review report

**Implemented and tested locally, 1 November 2026.** This is a cumulative source update for the existing FINN project. It preserves the established design, icons, server-side privacy/security controls, private environment and SQLite data. It is not a deployed site or a new live/model acceptance certificate.

## Changes

- Real App Router pages for Inbox, Radar, Research and Universe, plus filing/alert inspection and company Overview, Say–Do, Forensics and Vault pages. Compatibility redirects preserve older portfolio and symbol URLs.
- A persistent application shell and company workspace, bounded 30-second in-memory reads, coalesced requests, explicit retry invalidation, compact inline search with legacy aliases, horizontal portfolio context and selected-label glass dock. Large quote previews and unsupported-layout lists now use progressive disclosure. Advanced Inbox search/filter/sort remains accessible in an expandable section.
- A separate anomaly workflow with debounced thresholds, actual 21-bar volume context, price/candle/volume controls, daily filing pins and exact publication/observation timeline. Historical observations are explicitly retrospective.
- Source-backed quarterly comparison bars, cash/PAT and borrowings/equity visuals, accounting proof fields retained by the backend, and safe absence states for older snapshots or unsupported layouts.
- Global citation dialogs outside tables. URLs carry document/page/excerpt hashes, not quotes. Direct-link reload and Back/close were exercised in Chromium. PDF integrity is checked against saved bytes on delivery.
- Four consecutive ledger slots, including read-only projection of older caches. Missing quarters are no longer hidden by counting an older available transcript. Annual guidance is not plotted as quarterly delivery. The schema detector no longer classifies a report as a bank solely because incidental narrative mentions NII or nonperforming assets.
- New read-only detail endpoints and company-scoped digest. SSE job updates have watchdog/polling fallback and terminal reload. Existing public review restrictions and source-job budgets remain.

## Verification

| Check | Result and scope |
| --- | --- |
| Backend regression suite | **348 passed**, 24.87 seconds. Includes 8 added tests for consecutive coverage, legacy projection, date boundaries, metadata/quote identity, filing revisions, encoded alert IDs, prior-20 baseline and captured-primary reconciliation fields. One existing Starlette/httpx deprecation warning. |
| Frontend checks | **32 checks** across existing UI, stale-response/polling races, privacy/security, market charts, new cache/financial-visual cases and service-worker behavior. These use isolated transport/display fixtures, never app seed data. |
| TypeScript | Passed `npm run typecheck`. |
| Production | Passed `npm run build`; all declared routes compiled. |
| API integration | 14 JSON routes passed against captured real-source replay; a saved PDF passed SHA-256 byte verification; public-review job POST returned 403. Timings in the JSON log are in-process, not network/mobile measurements. |
| Chromium | Root redirect; populated 7-day Inbox; company navigation; citation opening/direct-link reload/close; four-quarter ledger; financial chart; Vault empty filter; alert timeline and filing detail; legacy portfolio redirect. Captured-source replay was labelled throughout. |
| Narrow layout | Real Chromium iframe at 390px outer width (375px content plus scrollbar): Inbox, compact search, ambiguous TMPV/TMCV choice, glass dock and Universe. Document width equalled viewport width; body font was DM Sans. This is responsive browser QA, not physical-phone/Safari certification. |
| Packaging | Source hashes and conflict-safe installer are checked separately in the delivered verification logs. No `.env`, SQLite, dependency tree, build output or QA sidecar is included. |

Screenshots are in the update's `screenshots/` directory; test logs and captured-source API results are in `verification/`.

## Remaining limitations and release work

1. **Your local source/model validation is still required.** The earlier reported live result of **52/58** remains unresolved; this UI update does not change that result into a pass. No Gemini key, quota rotation or paid provider run was used here.
2. Some issuers/layouts have no supported result table, cash series, comparable target or governance finding. Those stay explicit review/missing states. New normalization/identity proof fields appear after re-extraction; older retained evidence is not silently recertified. Statement schema is not an independently verified sector or issuer-identity classification.
3. SSE/fallback behavior has code/race checks; a fresh long-running provider/model job over the eventual public proxy remains a deployment verification task. Public review deliberately cannot start one.
4. Session-memory reuse reduces repeated reads, but this is not a claim that every model stage has a universal content-addressed cache, that every route meets a phone latency target, or that provider responses are complete. Source/model cost and new cold ingestion remain dependent on actual quota and upstream availability.
5. Existing release review still applies: provider/issuer redistribution rights, PyMuPDF AGPL/commercial compatibility, final operator/regulatory positioning, host logging/contact settings, durable database storage, HTTPS/proxy/SSE and backup recovery checks. No production deployment, repository publication, email or submission occurred here.
6. Physical phone/Safari/PWA install, assistive technology and any final host configuration need final acceptance. Native dialogs, labels, focus, reduced motion, numeric alternatives and no-overflow layout were exercised, but no formal accessibility conformance certification is claimed.

The corrected specification is `docs/frontend-architecture.md`; the supplied blueprint is preserved in `docs/reference/frontend-blueprint-original.md`. Apply/review instructions are in `docs/frontend-restructure-setup.md` and the update's `START-HERE.md`. Keep real AI conversation history separate from this decision/test report for Day 5.
