> Historical checkpoint. Current status: [final pack status](../../final-pack-status.md). Current setup: [final pack setup](../../final-pack-setup.md).

# FINN — navigation, scroll motion and adaptive glass

Current source update after the compact glass revision. Apply using `frontend-restructure-setup.md`; keep the existing folder structure, `.env` and SQLite files. Earlier status reports are historical checkpoints.

## Delivered behavior

- Inbox, holding, quarter, research and session-map tiles rise and scale from 96.5% to 100% as they enter the viewport. The reveal runs once per mounted tile, lasts 360ms, and has at most 72ms of stagger. Newly paginated cards register with the same observer. Content is readable without JavaScript animation support; no scroll position is hijacked or financial value tweened.
- Chart traces draw over 650ms; saved volume and financial bars grow over 480ms from their real zero baseline. Negative financial bars retain the correct origin and sign. Donut segments and guidance marks fade in. Range/mode changes can reveal the newly rendered plot. Charts retain their tables, saved-session slider, units, bases and citations.
- Light and dark themes now change the bottom dock, selected destination, search circle and search field. Translucent tinted surfaces, backdrop blur, fine highlight edges and underlying content provide the glass effect. Existing FINN mark, navigation glyphs, Lucide icons and self-hosted DM Sans are retained.
- Workspace pages no longer render a global footer. About and Workspace settings hold the financial/AI notice, privacy, licenses, accessibility and source-health links. Per-source age, missing coverage, review flags and evidence warnings remain in context.

## Changes that reduce avoidable work

The previous build flashed skeletons on warm return visits, recomputed chart geometry while inspecting pointer positions, animated the whole route in addition to chart entrances, and used a fixed page background plus several large blur surfaces. The dock colors were fixed rather than theme-derived, and filing cards were absent from the reveal observer.

Saved JSON now remains in bounded page memory for up to five minutes; the freshness interval stays 30 seconds. A fresh return view uses its snapshot synchronously without an extra request. An older retained view remains visible while revalidation runs. Failure remains an error and does not update the saved observation time. Explicit retry invalidates that request; an older in-flight result cannot overwrite a newer refresh. This is a UI cache, not live market data or persistent browser financial storage.

The shared workspace context and holding counts are memoized. The 18-company ribbon no longer eagerly prefetches every company route. Main navigation retains Next navigation/prefetch behavior. Chart geometry is memoized and pointer movement coalesces to one update per animation frame. Compact sparklines do not process pointer hover. The duplicate blurred SVG trace is removed. Scroll reveals use one IntersectionObserver and one insertion observer per route; observers and animation frames are cleaned up. The page background scrolls normally, and costly blur is concentrated on small/sticky glass controls rather than every tile. There is no continuous scroll listener or persistent layer promotion per card.

Reduced motion bypasses observer animation and cancels running effects. Reduced transparency and forced colors use readable solid surfaces. Native scrolling, keyboard controls and focus management remain.

## Verification

- 50 frontend checks passed, including ten new cache/motion/pointer regressions. A burst of 100 pointer events schedules one frame and chooses the correct saved session; fresh and stale return views, failed refresh, invalidation races, expiry, new-page observation and cleanup are covered.
- TypeScript and the production Next build passed. Test and build logs accompany the package.
- Captured-public-source FastAPI replay: 14 JSON routes passed, saved PDF SHA-256 integrity passed, public-review job POST remained forbidden. No upstream/model execution was used.
- Chromium production review: populated Inbox; Universe and Radar navigation; mobile search to TCS; chart volume mode; Settings notice links; About destination; light/dark dock and search rendering; native keyboard scrolling; zero horizontal overflow at a 390px document width; no global footer. Screenshots show the saved replay explicitly, not a live acceptance run. Browser-extension metadata errors were observed separately from FINN; no app runtime error was observed in this review.
- Backend source is unchanged from the prior 348-test checkpoint. Those backend tests were not rerun solely for this frontend revision. Installer checks cover original and four prior update baselines, private-file preservation, idempotency and refusal of unknown local edits.

## Review locally

Stop the existing app before applying the installer. From the FINN root after applying:

```powershell
.\.venv\Scripts\python.exe scripts\run_local.py --build --production --db data\finn.sqlite3
```

Use the production build when judging speed. No new dependency is required for these animations; keep the pinned setup from the cumulative update. Open Inbox with a populated window, scroll through filings, change pages, inspect a chart, toggle appearance and open Settings → About FINN. OS reduced-motion preferences should disable reveals. The full model finalizer is not needed to review these UI changes.

## Limits before deployment

These changes remove measured/reproducible sources of unnecessary work; they do not establish a phone frame-rate, universal latency or public-network speed guarantee. Physical iOS/Android, Safari glass rendering, touch scrolling and screen-reader checks remain. Blur support and device performance vary. A slow source/model job is separate from route animation, and missing evidence remains missing. The prior local model/source acceptance result (52/58) is not re-certified by this frontend update. Live acceptance, data/AGPL licensing decisions, deployment and submission remain open as documented in the pre-final reports.
