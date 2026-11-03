# FINN plan review — 27 October 2026

Reviewed all four pages of the official main brief, all three pages of the companion reference, and the full master plan. The main brief takes precedence, then the companion definitions, then the master plan with this correction record. The product remains Signal Inbox + Forensic Workspace, with deterministic Python calculations and inspectable primary evidence.

## Corrections locked before Day 1

| Area | Finding | Implementation decision |
| --- | --- | --- |
| Calendar | Oct 27–Nov 1 spans six calendar dates, not five. | Five work phases; Oct 31 and Nov 1 are validation/submission buffer. No exact submission hour is stated in the brief. |
| Scope | The brief's Pull modules are a menu. Eight modules plus audio, chat, OCR and governance analysis risk missing a working demo. | Prioritize Inbox and four-quarter Say–Do ledger with citations; cash quality next. Audio/copilot/QR/deep governance are stretch work after acceptance gates. |
| Categories | Reference page 1 lists **17**, not 16, categories. | Preserve all 17, including unclassified. Category and materiality are separate; unknown is not synonymous with routine. |
| Instruments | ZOMATO is now ETERNAL. TATAMOTORS became TMPV; the demerged commercial-vehicle entity is TMCV. | Use ETERNAL and TMPV for these portfolio slots. Preserve the historical ZOMATO alias; reject ambiguous Tata Motors name queries. Never splice demerged company financial histories. Refresh the NSE security master. |
| Portfolio claims | Market-cap tiers and demo stories in the plan are unverified hypotheses. | Keep the 18-company/5-showcase structure; never display a prewritten beat/miss, scandal, or size classification as a finding. |
| Primary sources | Screener's normalized tables and company summaries are secondary compilation. | Screener is document discovery and separately labelled unverified staging data. Pull claims/ratios and Say–Do actuals require original reports, transcripts or company/exchange filings, with field-level provenance. |
| Cross-signal | A filing within ±48 hours does not establish cause. Future filings introduce look-ahead. Volume alone does not identify institutional buyers. | Label “nearby filing” or “no matching filing in available coverage”; cutoff at alert time. Subsequent filings are clearly retrospective. No causal or institutional-flow claim. |
| Guidance alignment | Latest four transcripts may describe future years or require a fifth earlier transcript for the oldest outcome quarter. | Collect enough historical statements to cover four delivered periods. Store statement date, target horizon, metric, unit, currency, scope, revisions and source. Not-yet-due, withdrawn, qualitative and not-comparable are explicit states. |
| Verdicts | A lower number can be good (debt/cost), and qualitative remarks are not numerical promises. | Metric-specific direction and target bands; no beat/miss unless horizon and definition align. A company explanation is labelled management's explanation, not verified causality. |
| Basis | Missing consolidated page does not prove no subsidiaries. | Fallback only on genuine absence/redirect with explicit observed basis; never fallback for 403/429/timeouts. Never mix bases, fiscal calendars, currencies, quarter/YTD/full-year or restated/original values. |
| Periods | Not every issuer uses an April–March FY. Q4 may be derived from annual less 9M. | Preserve reported dates and duration first. Indian FY labels only where confirmed. Derived Q4 requires aligned annual/9M basis and a visible derived flag. |
| Units/metrics | Global crores conversion would corrupt EPS, percentages or share counts. Operating profit is not automatically EBITDA. | Typed monetary/per-share/percent/count values, exact Decimal conversion, unknown-unit abstention; do not invent EBITDA or double-count other income. |
| Banks/NBFCs | Bank NIM and Screener financing margin are not interchangeable; CFO/PAT is not a generic bank cash-quality test. | Separate bank, NBFC and nonfinancial profiles. Only reported NII/NIM/asset quality; no generic industrial EBITDA, working-capital or cash-conversion judgement for lenders. |
| Cash quality | CFO/PAT thresholds are heuristics, especially with zero/negative profit or mismatched PAT attribution. | Align cumulative periods/scope; undefined for nonpositive cumulative PAT. Capex is cash purchase of fixed/intangible assets, not total investing cash flow; record sign convention. |
| EOD | Thirty calendar days may contain fewer than 21 trading observations. Today's bar may be intraday. Corporate actions can distort returns/volume. | Fetch wider history, retain 30 completed sessions. Baseline uses prior 20 sessions excluding today. Reject invalid bars; flag corporate-action windows; label adjusted price return and raw volume separately. |
| Digest | Weekend convenience should not silently change a user's selected period. | Keep 24h default and offer explicit latest-session/weekend view with shown range and as-of date. Never present cached historical material as live. |
| Materiality | Auditor resignation/qualification and some ballots can matter despite a routine category. | Critical-content overrides before routine burial; unknown/low-confidence documents remain visible for review. Counts use deduplicated records with surfaced+buried total reconciliation. |
| Ingestion | Header rotation is not a guaranteed solution to exchange blocks; empty data is not proof of no filings. | Bounded requests, stable identification, polite backoff, provider status and completeness. Preserve raw responses, source URLs, observed times and hashes. No empty success on schema failure. |
| Citations | Substring match proves presence, not support or speaker identity. | Validate exact page and document hash, metric support, speaker, target period and primary provenance. Treat document text as untrusted data. OCR failures abstain. |
| Performance/cost | Hard-coded call costs and universal <3s/<8s cold starts are unsupported. | Measure cold vs warm latency, coverage and cache age. Record actual provider/model usage; estimate cost only with dated pricing. Current model choice stays configurable. |
| Reliability | SQLite on ephemeral cloud storage loses cached evidence; in-process jobs can vanish on restart. | Durable volume or managed DB, unique ingestion keys, schema versioning and resumable jobs. Verify deployment early, well before submission. |
| Security | Arbitrary PDF URLs and model output create fetch/render risks. | Validate ticker input; use a fixed, reviewed HTTPS document-host allowlist (no arbitrary hosts/IPs), reject credentials, alternate ports and cross-host redirects, and bound size/pages/time; do not render raw model HTML. Further deployment-specific DNS protections remain a hosting check. |
| History/submission | A build log is not the requested original AI conversation export. | Maintain decisions/tests now; include actual exported/shared conversations in final package. Draft final email at submission stage; do not send during Day 1. |

## Day 1 acceptance gate

1. Reproducible Python FastAPI + SQLite and Next.js/TypeScript/Tailwind monorepo foundation.
2. Exact 18-stock portfolio and five showcase symbols; unseen valid symbol accepted independently of portfolio.
3. EOD adapter, announcement adapter, and generalizable Screener document/table discovery with raw provenance and explicit errors.
4. Deterministic math and parser/storage/API tests, including missing data, invalid input, mixed units, zero denominators, corporate actions and blocked sources.
5. Run TCS, HDFCBANK, LAURUSLABS and unseen ASTRAL; record per-source coverage and timings. Extend ingestion to all 18. A partial or unavailable source is not a passed gate.
6. Retrieve at least one real primary document and preserve page-indexed text/hash to prove discovery reaches source bytes. Analytical extraction remains Day 3.
7. Keep cold <3s as an aspiration, measure it honestly. Finish with a checkpoint and explicit unresolved items; never use synthetic test fixtures as a live demo.

## Source map

- Main brief p1–2: 15–20 holdings, 3–5 research examples, generalizable engine, three source families, mobile-first Push/Pull.
- Main brief p2–3: prioritized digest, configurable alerts, primary-only research and four-quarter management accountability example.
- Main brief p3–4: narrow reliable scope, efficiency, prototype, repository, actual AI history and covering email.
- Companion p1: 17 categories; p2–3: documents and metric definitions.
- Master plan §§4–9: portfolio, stack, workflow and Day 1 filenames retained with the corrections above.
- NSE instrument evidence: https://www.nseindia.com/companies-listing/corporate-filings-announcements?symbol=ETERNAL ; https://nsearchives.nseindia.com/content/circulars/FAOP70882.pdf ; https://www.niftyindices.com/Press_Release/ind_prs13112025.pdf . Retrieved 27 Oct 2026.
