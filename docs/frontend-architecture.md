> Latest appearance update: [compact glass, light/dark themes and motion](history/checkpoints/glass-motion-update.md). Earlier design/checkpoint details below remain historical.

# FINN frontend execution specification — corrected and implemented

1 November 2026. Official ENAM brief > companion definitions > reviewed master plan > this specification. The original supplied design blueprint is retained at `docs/reference/frontend-blueprint-original.md`; this document corrects its illustrative numbers and incompatible requirements.

## Product and design

Keep the established neutral grey/white surfaces, DM Sans typography, existing FINN mark and navigation glyphs. Glass is restricted to the navigation/dialog surfaces. Financial content is structured and readable, with reduced-motion support. No sign-in, trading, subscriptions, payments or analytics are added.

Primary routes are `/inbox`, `/radar`, `/research` and `/universe`. `/` redirects to Inbox. `/portfolio` redirects to Universe; `/sources` remains a separate diagnostics page; old `/research?symbol=INFY` links redirect to the company hub.

| Route | Implemented behavior |
| --- | --- |
| `/inbox` | 24h default, explicit 3/7/30-day and latest-session choices, all 17 categories, quick filters, bookmarks, CSV export, pagination, compact result previews and inspectable routine filings. Unknown/review candidates remain visible. |
| `/inbox/[filingId]` | Independent read-only lookup, retained revision, source times, full results/dossier where available, source-backed grouped comparison and backend normalization/reconciliation proof. |
| `/radar` | Separate EOD workflow, debounced price/volume sliders, coincidence/unmatched filters, pagination, actual volume histograms and signal coverage. |
| `/radar/[alertId]` | Saved price/raw-OHLC/volume chart, daily filing pins, exact timestamp timeline, 20 prior volume bars plus trigger, contemporaneous versus retrospective disclosure context. |
| `/research` | Company launchpad and the approved five showcase companies. Compact top search opens any valid NSE symbol without starting a job. |
| `/research/[ticker]` | Persistent company context, saved market chart, primary business excerpt preview, financial snapshot/trajectory, supported growth/caution comparisons and navigation to audit/forensics. |
| `…/say-do` | Four consecutive delivered-period slots, explicit missing transcripts, comparison states/citations, quarterly guidance bands only when target/actual are resolved for the same quarter. Historical guidance is labelled extracted targets. |
| `…/forensics` | Primary result tables, grouped bars where review status permits, annual CFO/PAT bars, borrowings/equity, retained backend proof and governance excerpts. Unsupported documents are summarized in a separate disclosure. |
| `…/filings` | Filterable/paginated primary document Vault, saved/original PDF controls, company-scoped 30-day filing feed, explicit source refresh. Active durable jobs recover with SSE, then polling fallback. |
| `/universe` | Exact 18-company heatmap, unweighted breadth, saved session/volume and 24h surfaced counts, card/table/search/sort views, truthful engine architecture and diagnostics link. |

## Mandatory corrections to the supplied blueprint

| Original suggestion | Correct implementation |
| --- | --- |
| ICICIBANK, TITAN, KPIL in the assessment portfolio | Exact list: RELIANCE, TCS, HDFCBANK, INFY, TMPV, SUNPHARMA, LT, BAJFINANCE, TRENT, ETERNAL, PERSISTENT, DIXON, POLYCAB, DEEPAKNTR, LAURUSLABS, KPITTECH, SUZLON, JYOTHYLAB. Showcase: TITAN, COFORGE, SYNGENE, SONACOMS, CAMS. |
| Fixed 2,364-company count and sector badges | Search the saved official security master. Total and sector are not invented; cache availability comes from actual stored workspaces. |
| `price_threshold_pct`, `volume_ratio_threshold` | Actual REST parameters are `price_threshold` and `vol_threshold`. |
| Nineteen baseline days plus trigger | Twenty **prior completed sessions**, excluding trigger; volume hit is strictly above threshold, adjusted price hit inclusive. |
| Unread material counts | No unread tracking exists. Ribbon/heatmap show **surfaced /24H**, including review candidates, independently of the currently selected Inbox window. Missing count is a dash. |
| Attributed/explained institutional buying | “Nearby filing” and “no matching filing in available point-in-time coverage.” Both publication and observation matter. No causal or institutional-flow claim. |
| Four available transcripts = four audited quarters | Four consecutive slots anchored to latest reported label/date. Missing quarters remain missing; dates and fiscal labels are not silently merged. Old snapshots are projected read-only into consecutive slots. |
| Annual guidance against quarterly actual; FCF against CFO | Only backend-resolved same-horizon comparisons. CFO/PAT uses aligned annual consolidated INR facts, not FCF, H1, or owners-only PAT. |
| Operating profit implies EBITDA; every issuer uses industrial ratios | Only explicitly extracted metrics. Lender statement schemas remain distinct; industrial cash judgments are withheld for lender profiles. Schema identification is not an independently verified sector classification. |
| `?q={verbatim quote}` | `?cite={sha256}&page={n}&quote_id={sha256-of-excerpt}`. No quote text in URLs. Server resolves retained citations; browser Back closes a newly opened drawer; reload resolves a shared link. |
| Always show “SHA verified”, “zero hallucination”, 4/4 success | Hash identifies saved bytes; integrity is checked on PDF delivery. Source presence does not certify claim support. Missing/unsupported/review states remain visible. |
| Universal <50ms, <15% pages, fixed model cost | No such claim. In-memory GET cache: 30 seconds, bounded 24 entries, concurrent reads coalesce. It does not persist financial payloads or imply a model cache hit. Actual recorded model/time telemetry remains per company. |

## Implementation contracts

- Next.js App Router root shell persists through route changes. Company layout retains the research state across its nested pages. Existing icons and source/privacy notices survive.
- Financial arithmetic stays in Python `Decimal`. The browser plots returned values; it does not decide financial beat/miss or certify reconciliation. New parser output retains normalization factor, raw quarter/half-year values and rounding tolerance. Older snapshots explicitly say proof was not retained.
- Read-only endpoints: `/api/push/filing/{id}`, `/api/push/alert/{ticker:session}`, `/api/push/company/{ticker}`, `/api/evidence/{sha}/metadata`. They do not call upstream providers, models or job enqueueing.
- Research jobs require an explicit POST. Public-review mode rejects POST server-side. SSE has a watchdog and falls back to sequential polling; a terminal job reloads saved research. Active job lookup restores a job after navigation.
- Saved JSON remains no-store at HTTP level. PDFs retain hash-checked immutable delivery. Browser financial data stays in session memory; only existing settings/bookmark IDs use localStorage.
- Citation dialogs are rendered outside financial table cells. Native modal focus/scroll locking and return-to-trigger remain. Charts have readable alternatives or adjacent full numeric cards/tables, and do not silently replace missing observations with zero.
- Original model/page extraction limits and provider guards remain. No extra API keys, host allowlist relaxation, paid live run or deployment is part of this change.

## Scope that remains evidence-dependent

The interface is implemented; accepted evidence is not guaranteed for every issuer. Missing segment mix, comparable guidance, footnotes or supported annual tables must remain missing. Existing cached annual reports may require re-extraction for the newly retained proof fields. A read-only view never performs that refresh automatically.

Document/model extraction has several versioned caches, but the supplied blueprint's universal `(hash, extractor version)` zero-token claim is not established for every synthesis stage. The UI makes no such guarantee. No fixed tier price or universal performance gate is claimed.

This restructuring does not convert the previous live/model acceptance result of 52/58 into a pass. Final local source/model validation, deployment checks, licensing/redistribution review and submission materials remain explicit release work.

## Navigation and motion revision

Read `fluid-motion-update.md` for the current performance and motion behavior. The shared memory cache retains snapshots for at most five minutes and checks freshness at 30 seconds. Warm route returns render the saved observation while refreshing; errors and source timestamps remain visible. Tile/plot animations are bounded once per mounted surface, use one route observer, and cancel on cleanup or reduced-motion changes. Settings and About carry the research/privacy/licensing notices; workspace pages have no global footer.
