# Assessment coverage and live repair — 3 November 2026

The actual Windows installation now passes **58/58** checks in `scripts/verify_day3.py`, using the existing database. The final report was generated **3 November 2026, 16:48:55 IST**. This supersedes the historical 52/58 live engineering result for the checks covered by that script. It does not certify financial accuracy, every source, physical-device accessibility or deployment.

Evidence: [repair report](../verification/acceptance-repair-2026-11-03/README.md), [58-check result](../verification/acceptance-repair-2026-11-03/acceptance-after.json), [final company data](../verification/acceptance-repair-2026-11-03/research-final-state.json).

## Brief interpretation

The supplied desktop PDFs were extracted and all seven pages visually reviewed. Their SHA-256 hashes match the canonical [main brief](source-main.pdf) and [companion reference](source-reference.pdf) in [source-manifest.json](source-manifest.json). The main brief takes precedence over the reference and reviewed plan.

The main brief calls the frontend examples “illustrations, not a checklist” (page 2) and the eight research outputs a menu (page 3). It requires a working mobile-first prototype with Push and Pull, three source families, a 15–20-company mock portfolio, a handful of ad-hoc companies, and an engine that generalises where primary data is available. Chat, voice and other interaction examples are optional. QR/copilot/audio remain disclosed stretch placeholders. The PDF's submission instructions are requirements for the eventual submission, not authorization to publish or email from this repair task.

## Requirement traceability

| Brief point | App implementation and evidence | Current boundary |
| --- | --- | --- |
| 15–20 diverse mock holdings; 3–5 extra demo companies | Exact existing 18-company portfolio and five showcase companies in `backend/finn/universe.py`; Universe, Research search and security-master aliases retained. | These are mock assessment holdings. |
| Generalise outside the demo set | Security-master ticker resolution, bounded primary discovery, durable research jobs; KPIL is outside both sets and passes the unseen-company gates with ten saved primary documents and four delivered periods. | One unseen company is demonstrated, not universal ticker coverage. Primary availability and reviewed source hosts constrain discovery. |
| EOD prices and volume | Actual refresh accepted all 18 holdings through **2 November 2026**, the latest completed session at verification time. Adjusted returns, raw OHLC/volume, previous-20-session volume baseline and freshness guards retained. | EOD alerts are evaluated after completed observations; no intraday-feed claim. Later sessions require a deliberate refresh. |
| NSE/BSE announcements and prioritisation | Inbox windows, 24h default, all 17 reference categories, critical-content overrides, collapsible routine filings, filters/bookmarks/export. All 246 current-window filings have versioned analyses; 244 readable filings have live or routine classifications. | Two unavailable/scanned attachments remain coverage gaps. 204 items retain review flags; coverage is not classification accuracy. |
| Configurable unusual-move/category alerts | Radar price/volume thresholds and category watches; actual mobile settings controls inspected. Five alert cards were present in the 24h saved-data check. | “Push” is the in-app Inbox/Radar, not an OS notification subscription. |
| Management-change background | Management enrichment, source-bound identity/event validation, evidence and uncertainty presentation remain implemented and regression-tested. | Missing or ambiguous public professional background remains a gap; no invented biography. |
| Quarterly Revenue/EBITDA/PBT/PAT, QoQ/YoY | Results and research tables use deterministic Decimal changes with explicit periods, basis, INR units and primary evidence. TCS Push table inspected. Consolidated statements restored for INFY, DEEPAKNTR, HDFCBANK and KPIL; 36 cells checked visually against primary pages. | EBITDA is not substituted with operating profit or manufactured when absent. Lenders use income/PBT/PAT rather than industrial EBITDA. Image-derived rows retain visual-review flags. |
| Annual reports and earnings transcripts | Saved original PDF bytes/hashes, URLs, page quotes and observation/publication times; Screener remains staging/discovery. Fresh full saved-source audit covers 25 company caches with SQLite integrity `ok` and zero citation errors. | Some IR URLs still fail TLS, redirect or return HTML/406; existing source-error records remain inspectable. No TLS verification was disabled. |
| Business/financial snapshot and trajectory | Company overview, source-linked model proposals, actual quarterly facts/series, charts, citations and missing-data states. | Multi-year facts depend on reliable extraction; a quarterly series is not presented as a complete multi-year history. |
| Balance sheet and cash quality | Annual forensics, leverage/cash reconciliation and governance evidence viewers, with lender exclusions and accounting-scope guards. | Several annual layouts remain unsupported or partial. HDFC industrial cash/PAT analysis is deliberately not applicable. Keyword evidence is not a governance verdict. |
| Four-quarter promised versus delivered | All four acceptance companies have four delivered source periods, each with a meaningful source-linked assessment or supported deterministic comparison. Period-by-period model packets preserve speaker and original citations. Annual versus quarterly, basis, metric and revised-target guards remain. | Model assessments require semantic review. Unsupported numerical comparisons remain unresolved; completed audit coverage does not mean four numerical beat/miss verdicts. INFY's latest 16 numerical extraction proposals were rejected, not promoted to facts. |
| Explicit forward guidance; bull/bear menu | Separate explicit guidance targets, primary excerpts, bounded attributed claims and guarded deterministic financial evidence. KPIL's supported annual minimum/outcome comparison remains distinct from quarterly evidence. | No investment recommendation, invented target or causal price explanation. Unsupported modules abstain. |
| Primary-only Pull | Source-bound quotes/pages/hash identity; bounded public issuer/exchange passages for reasoning; no broker/news/model-memory research evidence. | Exact quote presence is not independent entailment evaluation. |
| Mobile-first, concise and interactive | Existing Inbox/Radar/Research/Universe routes, responsive charts, accessible table regions, native dialogs, source controls, search and settings preserved. Actual 390×844 browser checks include repaired tables, evidence, audit and settings; dark-table label contrast fixed. | Physical Android/iPhone, Safari, soft keyboard and screen-reader certification remains open. The embedded browser's PDF iframe was blank; excerpt and Saved PDF/Original source links work, and a fallback caption now explains this. |
| Efficient model use and architecture | Cached saved-only research refreshes; routine Tier-0 filtering; separate configurable Flash/Reasoner adapters; bounded inputs, per-period audits, retry of missing stages only, usage receipts and pacing. Actual approved runs used the locally configured `gemini-3.5-flash-lite`. | No monetary cost estimate or guaranteed free-tier capacity is claimed. No new subscription/provider configuration. |
| Submission prototype link, repository, actual AI history and covering note | Working production build and local run command verified; source and historical decision log retained. | Public hosting/storage/licensing/operator choices, GitHub publication, authentic AI chat export and email submission remain separate release work. This checkout has no Git metadata. No conversation transcript was fabricated. |

## Verification on this installation

| Check | Result |
| --- | --- |
| Full backend regression suite | **391 passed**, one existing Starlette/httpx deprecation warning |
| Frontend workspace checks | **60 passed** |
| TypeScript | Passed |
| Final Next.js production build | Passed |
| Day 1–3 live engineering acceptance | **58/58**, no open gates in that audit |
| Saved Push + production API/source/arithmetic audit | **985 checks passed** |
| Full saved Pull source audit | 25 companies; integrity `ok`; zero citation errors |
| Final production HTTP verification | 28 requests; four source PDFs hash-verified; job POST rejected with 403; saved snapshots unchanged by reads |
| Financial page spot check | 36/36 displayed cells match the four saved primary pages |

The database was backed up before deliberate changes. Previous Pull/Push analyses remain in history and the original source timestamps were preserved. Private settings, unknown files and Git metadata were not replaced; no cleanup tool, runtime migration, deployment or email submission was performed.

The remaining work is evidence/semantic depth and release acceptance, not the old six failing engineering gates. Keep the source gaps and review labels visible when demonstrating the app.
