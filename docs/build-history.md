# AI-assisted build decision log

## 2026-10-27 — Review and Day 1

User instruction: read the three source files carefully, review the master plan for mistakes/improvements, follow the plan, prioritize placement-shortlisting quality, and begin Day 1 step by step with proper tests.

1. Read all source text and visually inspected the seven PDF pages. Recorded source precedence and 24 corrections before implementation.
2. Retained FastAPI/SQLite and Next.js/TypeScript/Tailwind. Kept deployment for the roadmap's later phase.
3. Verified instrument aliases against NSE material and retrieved the real NSE equity security master. Corrected ETERNAL/TMPV portfolio entries without joining unrelated demerged entities.
4. Captured actual Screener and NSE responses to design parsers; preserved reduced regression fixtures with their source URLs.
5. Built pure deterministic financial utilities, EOD calculation guards, ingestion/storage/API modules and a mobile development shell.
6. First live acceptance run fetched all three data families for TCS/HDFCBANK/LAURUSLABS/ASTRAL. Observed cold fetch times above the plan's 3-second target; recorded failure rather than changing the measurement.
7. Corrected SOCKS dependency support. Removed redundant local DNS resolution for fixed reviewed PDF hosts because the environment resolves through a proxy; HTTPS host allowlisting and same-host redirects remain enforced.
8. BSE PDFs/API returned HTTP 403. Changed transcript selection to prefer matching NSE filings over BSE discovery links.
9. Concurrent work exposed SQLite corruption with the initial WAL store. Quarantined that generated database, changed to rollback journaling, serialized/closed connections, added concurrent-write integrity regression, and rebuilt from live sources. Root cause is not conclusively proven; deployment storage behavior still needs verification.
10. Ran offline financial/parser/storage/API tests, production frontend compilation and TypeScript checking; recorded subsequent live results in day1-status.md and machine-readable run reports.

This document summarizes decisions; it does not recreate the original agent conversation. Export/share this actual ChatGPT build conversation before submission, alongside other coding-agent sessions. Do not claim this summary alone satisfies ENAM's AI build-history requirement.

## 2026-10-28 IST — User-requested Day 1 self-verification

1. Paused Day 2 and recreated the Python environment from lockfiles; installed the backend package and frontend dependencies cleanly. Reran the existing 42 tests, production build and TypeScript check successfully.
2. Launched both servers. Cross-session HTTP/browser requests were refused; same-session real HTTP succeeded. Captured 22 route cases, CORS responses, warm HTTP timings and frontend HTML. Browser JavaScript interaction remains unverified.
3. Added a separate, read-only verification script: raw SHA-256, snapshot references, 570 saved bars, independent Decimal indicators, 227 filing timestamp conversions, selected TCS staging rows and all four preserved PDFs. Together with HTTP checks, 153 checks passed.
4. Ran four-company real-source ingestion into a separate database. All returned market frames ended on 26 October, older than the preserved 27 October checkpoint. Overlapping bars agreed. Astral discovery returned a one-page notice instead of the full transcript. Both demonstrate gaps not caught by the existing suite or CLI success status.
5. Added temporary-database reproductions of ignored same-ID amendments, future-window leakage and hidden failed refreshes. No production behavior was changed or failure represented as fixed.
6. Packaged exact Windows/macOS/Linux setup, manual UI checklist, actual API responses, source PDFs, fresh-versus-saved evidence and explicit remaining issues. The live reliability acceptance gate remains open; Day 2 stays paused.

## 2026-10-28 IST — Six-issue reliability repair

1. User confirmed local backend/frontend startup, then requested all six fixes before Day 2. Preserved the original checkpoint and implemented/tested repairs on a separate copy.
2. Added schema-2 migration, independent refresh attempts, stable NSE filing identities, revision history and observation-aware bounded date queries. Last-good source data and refresh failure metadata now coexist in the API and UI.
3. Added atomic monotonic market replacement, full OHLCV validation, the source-backed 2026 NSE calendar and explicit special-session/year abstention. Fresh Yahoo frames exposed missing latest-session close values; retained the saved newer complete data and returned a failed refresh status.
4. Added conservative transcript content checks and bounded approved PDF-link traversal. Real Astral discovery now records the one-page notice then retrieves the full 29-page issuer transcript.
5. Added durable source TTL reuse, forced refresh, failed-market retry cooldown, byte/hash checks and cache bypass after failed refreshes. Scheduled independent jobs through the same maximum-three-worker pool. Observed four-company cold run 34.79s; cache reuse 0.95–1.17s. All those runs correctly remain exit 1 because market responses are incomplete.
6. Reran 81 backend tests, production build/type checking, 153 data/HTTP checks and eight React/jsdom interaction scenarios. Preserved captured real fixtures and clearly labelled diagnostic mutations separately.
7. Promoted the repaired real-data database to the default path, retained the original baseline, and prepared current repair/migration documentation and updated files. Day 2 remains unstarted. No external deployment, GitHub publication or email dispatch occurred.

## 2026-10-28 IST — Day 2 in the existing project

1. User directed all future work into the existing workspace, with the final complete build/package on Day 5. Kept the same repository/database and did not produce a new project folder or ZIP.
2. Retained the reviewed 17-category taxonomy and noncausal, observation-aware signal rules. Built a bounded Flash REST adapter with strict output validation, explicit missing-key status, redacted errors and provider usage metadata. No live Gemini invocation occurred because no key was configured.
3. Added conservative routine burial with critical-content overrides, unknown/review visibility, large-image exclusion and resurrection after failed document refresh. Versioned analysis keys include filing content and parser/classifier versions; failed refreshes retain old evidence and observation times.
4. Added strict source-table parsing, exact Decimal currency/unit conversion, comparable quarter date checks, total-PAT attribution and half-year reconciliation. Verified TCS and Polycab against rendered source pages. HDFC Bank/Infosys ambiguous cells remain blank; EBITDA is not fabricated from operating profit. Flash currently locates candidate pages, while deterministic parsing validates figures. Broader structured extraction remains an open Day 2 gate.
5. Added explicit single-event appointment/reappointment/resignation extraction and issuer brief profiles. Verified Bajaj Finance and Trent. Complex multi-person tables and unverified external biographies remain review states.
6. Added exact Decimal alert-threshold comparisons, prior-20-session volume, corporate-action suppression and historical observation cutoffs. Retrospective context is separate from information available at alert time; no causal attribution.
7. Added a read-only digest, immutable PDF-by-hash endpoint, an accessible frontend verification panel and real-HTTP/React integration checks. Preserved the existing company inspection workflow.
8. Automatic review twice stopped an unrelated Microsoft telemetry request during initial PDF runs. Disabling ONNX telemetry was insufficient. Removed the ML/ONNX extras, pinned the basic PyMuPDF 1.x runtime and isolated each PDF in a bounded child process. The resumed real-source run completed without that blocked destination. No exception/permission to send telemetry was sought.
9. A full real-data run exposed nullable exchange industry metadata for Polycab. Fixed it, added a regression and abstention for an unseen issuer with unknown profile. Processed 224 current-window records; unsupported ZIP/missing attachments remain surfaced. The final verification results and remaining gates are recorded in day2-status.md.

This remains a decision/validation log. Preserve the actual conversation export/share link for the Day 5 AI build-history submission.

## 2026-10-29 IST — Remaining filing review, blocked by workspace database

1. Continued the requested 123-filings/210-uncertain review in the same project. Those numbers describe the user's Windows audit, not a newly verified run here. No Gemini key is configured in this workspace.
2. Found the resumed default database malformed: its header declares 377,815,040 bytes but the file has 185,797,632. Even the schema cannot be read. The cause is unconfirmed. Read-only checks found intact Day 1 backups, but these lack Day 2 analysis records. Did not overwrite the default database with an older backup; its SHA-256 was unchanged through verification.
3. Restored the previously verified Windows fixes in the resumed source files: explicit UTF-8 PDF subprocess output and explicit closure of read-only SQLite backup handles. Added locale and backup lifecycle regressions.
4. Changed classification to use the exchange description and primary cover subject instead of scanning annexure boilerplate for the first category keyword. Generic combined investor-meeting/call titles no longer force earnings-call classification. Expanded event recognition; added conservative model/subject conflict review. Unknowns and source failures remain surfaced. Rules remain provisional and do not clear analyst review merely to reduce the queue.
5. Added optional hash-verified saved-PDF re-extraction. It checks attachment identity and raw SHA-256, reparses bytes rather than trusting saved text, preserves original source time, and does not fetch. This mode was tested on synthetic fault cases; the unavailable production corpus could not be reprocessed.
6. Added explicit analysis/document/review coverage to the Day 2 audit. A passing mechanical audit is no longer the only headline; semantic accuracy is explicitly unknown. An intact Day 1 backup control correctly reported zero Day 2 analyses and fully_reviewed=false despite passing its mechanical checks.
7. Validation: 168 backend tests passed; frontend typecheck passed; eight re-extractions of four saved real primary PDFs (cp1252 and ASCII) matched original page count, page numbers and text and verified source hashes. Full default-database integration failed at SQLite backup before servers started. No live Gemini calls, new batch coverage, whole-corpus accuracy or Day 2 sign-off are claimed.
8. Updated the existing source, tests and documentation. No new project folder, ZIP or frontend rebuild. Current Windows database/source evidence is required to complete the requested corpus review.


## 30 October 2026 — Windows backup recovery and source review

Restored the supplied immutable backup after the interrupted working database failed integrity. Preserved all original records; isolated database ownership during processing and published only after verification. Processed all 123 pending records (120 with usable text, 3 source-blocked), triaged 210 uncertain classifications, and retained full-review flags. Added source-bound category reviews, zero-page/unreadable-refresh guards and explicit Persistent resignation extraction. Fresh primary downloads recovered two unusable PDFs. Final checks: 199 backend tests, 444 frozen-cohort checks, 153 data/HTTP checks, 795 Push/HTTP checks and 12 React/jsdom scenarios; build/typecheck pass. No new Gemini call, mobile QA, independent accuracy percentage or Day 3 completion is claimed. This log is an engineering record, not the original AI conversation export.

## 30 October 2026 — Day 3 continuation

Added Pull discovery, primary excerpts, period coverage, conservative annual cash/leverage parsers, optional review-required model reasoning, durable jobs/SSE and additive workspace. Preserved immutable baseline records. Validated real KPIL/INFY/Deepak Nitrite/HDFC sources and zero mechanical citation mismatches. Full semantic Say–Do acceptance remains open; user waived live model testing. See day3-status.md for exact test counts and limits. This log is not an original AI conversation export.


## 31 October 2026 — Day 1–3 repair continuation

Repaired refresh quotas, job/UI races, routine review behavior, broader source-bound table and Say–Do extraction, dedicated NSE annual-report discovery, bounded annual sections, worker startup, and opt-in multi-document model synthesis. Added regression and real-source validation. See docs/day3-repair-status.md for measured results and open acceptance gates. This is a decision log, not the actual AI conversation export. No model key was used, no deployment occurred and no email was sent.


## 31 October 2026 — Final Day 1–3 source candidate

Added official NSE final-session reconciliation with corporate-action/previous-close guards, expanded annual/minimum Say–Do extraction and period/segment safety, image-backed reconciled result extraction, bound management fallback, explicit latest-session/category watches, private local settings and bounded model retries/current structured output. Reprocessed all 259 portfolio filings; 253 primary PDFs available, 15 buried, 902 mechanical Push checks pass. All 18 current market snapshots accepted. Four-company primary audit: 1,439 exact-page citations, zero mismatches. Real KPIL annual minimum/outcome resolves one comparison. Fresh HAVELLS HTTP/worker: nine sources/four periods in 44.08 sec. 272 backend tests and frontend build/types/races pass. Added a one-command local finalizer with model preflight and database backup. Real model and four-period semantic acceptance remain pending the user's local key/database verification; no independent accuracy score, deployment or email is claimed. See day3-final-status.md. This remains a decision log, not an original AI conversation export.


## 31 October 2026 — Restored continuation and source recovery

Restored the continuation after the workspace reopened at its earlier checkpoint. Added bounded official NSE ZIP handling, exact current-frame provenance, financial precision/horizon guards, bounded classifier input, verified-role/numeric guards for Say–Do analysis, complete-corpus model verification, real 23-symbol discovery and safe review packaging. Added last-good raw-PDF recovery across parser versions while preserving already valid analyses and original source observation times. Reproduced 303 backend passes; all three real archives validate, with Sun Pharma honestly OCR-required. A fresh HDFC Bank request now returns the complete 24-page original PDF after an earlier truncated response. Full-cache live-source checks are separate from the still-pending private-key/model and semantic acceptance. No deployment or email. This is an engineering log, not an original AI conversation export.


## 31 October 2026 — Final backend handoff

Froze Day 1–3 backend scope for frontend integration. Added the final speaker-boundary guard so anonymous analyst/moderator labels cannot inherit management identity, and versioned research pull-v9 / say-do-v4. Added an actual OpenAPI export and frontend API handoff. Current regression suite: 305 passing tests. Live private-key/four-company semantic acceptance remains a local test, not a claimed result. Frontend design remains the user's next phase. This log is not the original AI conversation export.

## 2026-11-01 — Consolidated final source handoff

Prepared a complete clean source tree from the verified app rather than another incremental patch. Replaced the obsolete root handoff, grouped dated reports/manifests under docs/history, retained canonical official PDFs and removed their byte-identical duplicates, and excluded private data/environments/dependency/build/QA output. Added a read-only check plus guarded existing-project apply/quarantine utility; source conflicts refuse the whole update and an injected filesystem failure exercises rollback. Repeated the 356 backend tests, 60 frontend checks, TypeScript/build and captured-source API verification on the clean code. Live semantic/provider acceptance, licensing, actual-device checks, deployment and actual chat export remain open. This entry records work performed; it is not an exported conversation.

## 2026-11-03 — Actual Windows acceptance repair

Read both supplied official briefs and verified their hashes against the canonical copies. Preserved the actual database with a full backup and kept original changed source files. Diagnosed Gemini's rejected bounded-array schema, oversized combined audit packets, partial-candidate loss and literal-citation failures. Following explicit user approval, repaired four-company stages and exactly 38 pending classifications with actual Gemini usage; kept unsupported numbers rejected and primary source times unchanged. Restored four consolidated financial tables with deterministic date, tax, exceptional-item and PBT/PAT guards; an assistant visual spot check matched 36 cells. Fixed lender routing and dark-theme table contrast. The final existing acceptance audit passes 58/58; 391 backend tests, 60 frontend checks, TypeScript/build, 985 saved Push/API checks and 28 production HTTP requests pass. Full saved Pull integrity/citation audit covers 25 companies with zero citation errors. See [current scope and limits](assessment-coverage-2026-11-03.md). Source/semantic and physical-device gaps remain; no deployment, GitHub publication or email. This is a decision log, not the actual AI conversation export.
