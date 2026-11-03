# FINN usability and source assistant — 4 November 2026

Local implementation only. Publication remains paused at the user's request.

## What changed

- Company overview starts with a short primary-source brief and links to promises and financials. Charts, detailed analysis, accounting schema and run diagnostics expand on demand. All original sections and evidence controls remain available.
- Research labels use plain language. Watchlist prices, market overview, Radar thresholds, source diagnostics and historical-symbol help are nested. Both themes have clearer table headers, row separation, borders and focus states.
- Inbox identifies the selected window separately from the actual saved filing-check range. Radar shows the saved market-session range. Missing company coverage stays visible.
- Say–Do displays the number of matched numerical comparisons separately from quarters with sources. No additional comparison or performance verdict has been manufactured.
- Ask FINN opens in each company workspace. Its free source guide searches existing primary excerpts and offers Overview, Promises, Cash & debt and Watch points. It links to the original page-bound evidence and abstains on missing matches. Short excerpts are labelled as excerpts, not AI summaries.
- Explicit owner-only AI generation is available through `POST /api/assistant/{ticker}`. GET reads never run models. Public review and the hosted copy disable generation. Owner mode requires both a configured key and explicit model enablement. The original `--use-model` launcher flag enables it; merely having a key does not.
- AI input is bounded to eight saved passages and a 400-character question. Output has up to three points, bound source indices and a numeric-support check. Every generated result remains a review-required draft. Exact source presence is not proof of semantic support.
- Summary generation has a persisted six-per-hour / 24-per-day request budget, per-process concurrency guard, origin checks and redacted failures. FINN stores no assistant question/answer history. An explicit AI request transmits the question and selected excerpts to the configured Gemini provider.
- Existing release-to-select navigation remains; the assistant's topic buttons also support it. No new UI dependency or paid service was added.

## Verification

- Backend: **407 passed**, one existing Starlette/httpx deprecation warning; includes 16 assistant cases. Synthetic fixtures and mocked model adapter; no new live provider call.
- Frontend: **60 existing workspace checks**, **9 pointer-selection checks**, **8 assistant/coverage checks** passed. TypeScript and Next production build passed.
- Hosted copy: TypeScript, **10 read-model tests**, production Vinext build and router namespace check passed. Source is synchronized locally; no remote push or publication was performed.
- Local production HTTP check: **11 routes returned 200**, including all four company tabs and disabled AI/read-only capabilities.
- [Actual saved-data source selection](usability-saved-guide-audit-2026-11-04.json): 25 companies and 100 topic views checked without upstream/model calls. All had selectable text; this is source-selection coverage, not summary accuracy or a resolved financial comparison.
- Browser control reports disabled in Work settings. This pass does not establish rendered-layout, real touch, Safari, screen-reader or model-output quality acceptance. jsdom tests and successful builds do not substitute for those checks.

## How to review

Run the existing production read-only launcher and visit `/research/TCS`. Open **Ask FINN**, choose a topic, then inspect its citation. Other companies retain their own evidence and gaps.

```powershell
.\.venv\Scripts\python.exe scripts\run_local.py --public-review --production --db data\finn.sqlite3
```

For deliberately enabled owner AI use, stop the read-only session first and use the existing `--use-model` owner command with the operator's configured accessible model/key. This may consume provider quota; it was not run for this upgrade. Never expose keys through `NEXT_PUBLIC_*`.

## Research gates still open

This improves the interface and review workflow. It does not resolve unsupported annual layouts, missing comparable quarterly guidance/actuals, source connection gaps, semantic validation, model availability, licensing or actual-device acceptance. The saved INFY/DEEPAKNTR/HDFCBANK/KPIL audit still has only one resolved numerical comparison across sixteen quarter slots; period coverage is not comparison success. Do not force missing comparisons or invent values to fill the interface.
