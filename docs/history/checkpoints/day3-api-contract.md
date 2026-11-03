> Historical checkpoint. Current status: [final pack status](../../final-pack-status.md). Current setup: [final pack setup](../../final-pack-setup.md).

# Day 3 backend handoff for frontend work

The backend source is frozen for frontend integration. Live Gemini/data acceptance remains a local verification step; do not label it independently certified. The exact generated route/parameter schema is in day3-openapi.json.

## Start backend and worker together

```powershell
python -m finn.dev --db data/finn.sqlite3 --use-model
```

Keep GEMINI_API_KEY on the server in the root .env or shell. Omit --use-model for deterministic operation. Do not start a second ingestion/worker process against the same database. Frontend API base is http://localhost:8000 for local development; configure NEXT_PUBLIC_API_BASE separately in frontend/.env.local. Never put the model key in a NEXT_PUBLIC variable.

## Main endpoints

| Method and path | Frontend purpose |
| --- | --- |
| GET /health | API availability |
| GET /api/portfolio | Portfolio symbols |
| GET /api/universe?q=TEXT | Company/symbol discovery |
| GET /api/push/digest?window=1d | Saved Inbox; default exact 24 hours |
| GET /api/company/{ticker} | Saved company/source bundle |
| GET /api/market/{ticker} | Saved completed-session market data |
| GET /api/filings/{ticker}?days=30 | Observed filings |
| GET /api/pull/{ticker} | Saved primary research snapshot |
| POST /api/pull/{ticker}/jobs?refresh=false | Queue research; response 202 includes job ID |
| GET /api/pull-jobs/{job_id} | Progress/status |
| GET /api/pull-jobs/{job_id}/events | Optional progress stream |
| GET /api/evidence/{sha256}.pdf | Immutable source PDF; add #page=N in browser links |

Read endpoints do not scrape or call a model. Research requires the durable worker started by finn.dev. On absent research, enqueue a job, poll while queued/running, and then read research again. Treat partial, unavailable and failed states explicitly. Abort polling and discard old responses when the selected company changes. Refresh sources is an explicit refresh=true job.

## Preserve these data rules in the UI

- Show source observation time/cache age and latest failed refresh. Previously saved evidence remains useful, but cannot be labelled freshly downloaded after a failure.
- Inbox windows are 1d, 3d, 7d, 30d and explicit latest-session. Do not silently expand a 24-hour selection on weekends. Category watches use the 17 backend categories.
- Display financial values, units, dates, accounting basis and backend-computed deltas. Do not recompute ratios or turn missing values into zero. Lenders do not get industrial EBITDA/CFO/PAT assumptions.
- Numerical comparison badges come from deterministic comparisons. Model numerical_candidate/semantic_review_required output is reviewable analysis, not a verified beat/miss.
- Annual and quarterly targets remain distinct, even in the same Q4 ledger row. Not-yet-due, unavailable and not-comparable outcomes are legitimate states.
- Citation buttons show the source quote, page, original URL and saved PDF. Image-backed evidence is a transcription requiring visual review, not native verbatim text.
- Scanned/unknown/failed-source filings remain surfaced. The buried drawer is inspectable; surfaced + buried must equal scanned.
- Primary research facts use company/exchange originals. Screener staging is labelled separately and is not primary evidence.

No frontend redesign is included in this handoff. Mobile styling and presentation can now be built around these stable endpoints.
