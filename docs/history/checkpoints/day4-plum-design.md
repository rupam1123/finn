> Historical checkpoint. Current status: [final pack status](../../final-pack-status.md). Current setup: [final pack setup](../../final-pack-setup.md).

# Plum glass product revision

This revision follows the supplied six-colour palette and floating navigation reference while keeping the existing Next.js/FastAPI/SQLite product.

| Surface | Behaviour |
|---|---|
| Mobile dock | Four original SVG glyphs; only the current destination shows text; separate circular Search opens the existing company search dialog; safe-area spacing |
| Typography and identity | Self-hosted DM Sans and Newsreader under OFL; own unboxed FINN mark; matching manifest and app icons |
| Market chart | Adjusted closing price, separate raw OHLC candle mode, raw volume; 10/30/60 saved sessions; crosshair, accessible session slider and table |
| Inbox composition | Category counts from the current returned surfaced filings, before local filtering; each legend button applies its category filter |
| Portfolio map | Saved per-holding adjusted 1D return and source session; unweighted advance/decline/flat counts; missing observations stay missing; click opens the exact ticker |
| Motion | Short page/card entrance, chart-line drawing, volume rise, spring-like dock expansion and sliding evidence sheets; disabled for reduced-motion preference |

There is no fabricated portfolio return, price series or model verdict. Raw candles and adjusted prices remain separate because corporate actions can make their bases differ. Candle mode is disabled when raw OHLC is absent. Review-required/unsupported backend outputs remain explicit.

The Instagram reel URL was inaccessible through the available retrieval service. Its exact motion was not observed or reproduced. An uploaded short screen recording can guide a subsequent motion refinement.

## Review locally

Apply the cumulative update using START-HERE.md and keep the existing SQLite and environment files. Rebuild the frontend. On a phone-width browser, switch each dock destination and use the separate Search circle. In Research, change chart mode and session window, drag the session slider, expand its data table and open a source citation. Inspect the portfolio map and category legend. With reduced motion enabled in the device accessibility settings, transitions should become immediate.

Checks: `npm run typecheck`, `npm run test:day4`, `npm run test:visuals`, `npm run test:pull-races`, `npm run build`. Backend: `python -m pytest backend/tests -q`. These local automated checks do not replace the still-open live model/data acceptance gates in day4-prefinal-status.md.
