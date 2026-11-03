> Historical checkpoint. Current status: [final pack status](../../final-pack-status.md). Current setup: [final pack setup](../../final-pack-setup.md).

> Historical repair checkpoint. Superseded for current status by [day3-final-status.md](day3-final-status.md). Retained figures below describe the earlier run.

# Day 1–3 repair status — 31 October 2026

This update repairs confirmed defects in the supplied project. **Day 3 is not fully accepted.** The official brief and `docs/plan-review.md` remain authoritative. No unsupported financial verdict, synthetic live data, deployment or email submission is claimed.

## Implemented changes

- New report discovery is no longer blocked by older cached-document quotas. Forced refresh revalidates the same URL, preserves previous source versions, prefers explicitly dated recent filings, and does not charge failed downloads to the successful-document quota.
- Earnings-call discovery follows bounded approved links. AGM transcripts are excluded. Annual-report filenames can identify discovery candidates, and NSE's dedicated annual-report feed supplies additional primary URLs. Added the Deepak Nitrite issuer host found in its primary filing; arbitrary hosts remain blocked.
- Large annual reports can use explicitly labelled section extraction, retaining original page numbers, original PDF bytes and omitted-page counts. Full-document/routine checks cannot mistake selected sections for complete coverage.
- Literal Say–Do extraction now binds management roles to primary document context, supports colon and name-only speaker turns, carries speaker turns across pages, recognizes more percentage-band wording, and records explicit basis/period/scope uncertainty. Both guidance and actual must pass speaker, visual, basis, horizon and scope checks. Annual targets never become quarterly comparisons. Conflicting revisions remain review-required.
- Results extraction supports explicit three-, four-, five- and six-column layouts. Nine-month totals are not incorrectly reconciled as the sum of two quarters. An optional model can locate exact source rows; deterministic checks read the cells and validate labels, periods, units and source quotes. Damaged OCR and unsupported layouts still abstain.
- A category-only source review preserves an already valid independent routine-burial decision when categories agree. Added guarded Regulation 74(5)/ESOP routine patterns; critical-content scans still take precedence.
- Pull jobs support explicit forced refresh and optional server-side model use. `python -m finn.dev` starts API and durable worker together. Reads remain free of scraping/model calls.
- Pull polling is sequential, abortable and protected against old-job responses overwriting a newly selected company. Added a Refresh sources button and rendered primary facts, targets, numerical comparisons and optional cited model analysis.
- Financial snapshot/trajectory views assemble only primary parsed values, expose conflicting figures, and provide deterministic financial evidence for growth/caution. Bounded multi-document model synthesis uses source indices and rejects numerical claims absent from cited excerpts. It remains labelled AI analysis requiring verification. A separately configurable reasoning model is supported.
- Partial Screener refreshes retain the previous accepted staging snapshot. Original source files, fixtures, stored analyses and historical logs are preserved.

## Actual validation performed

- Full backend suite: **254 tests passed**, one non-failing Starlette/httpx deprecation warning. Exact command and result are in `verification/day3-repair/backend-tests.txt`.
- Frontend production build, TypeScript check and three new Pull race/refresh checks passed. See the matching frontend logs.
- Real cold HAVELLS research through HTTP + durable worker from an empty temporary database: HTTP 202 submission, completed job, HTTP 200 research, seven primary sources, four transcript periods, about 86 seconds. It remained partial and explicitly reported source-size/availability failures.
- Refreshed discovery across all 18 holdings: 18/18 Screener staging sources and 18/18 NSE announcement responses accepted; 259 dated filings. Provider completeness remains unverified.
- Yahoo returned invalid latest-session prices for all 18 holdings. They were rejected, not replaced with invented or stale-as-current prices. This live EOD gate remains open.
- Rebuilt INFY, DEEPAKNTR, HDFCBANK and KPIL research from downloaded primary evidence. Each has four transcript periods. Latest annual reports were retrieved, including HDFCBANK reports exceeding 500 pages, through explicitly selected sections.
- Independent raw-hash and exact-page quote audit: **1,269 citations, zero mismatches** across those four companies. This is mechanical provenance, not proof of semantic correctness.
- No live Gemini call was made. No credentials were extracted from the uploaded `.env`. Model adapter tests use labelled synthetic responses.
- Runtime versions and measured coverage are recorded in the repair verification directory. Earlier historical coverage percentages were not rerun and are not current claims.

## Open acceptance gates

1. Valid current EOD data from a functioning provider is still required.
2. The real four-company corpus produced **zero resolved numerical Say–Do comparisons**. Broader guidance/actual extraction, reliable reporting context and source review are still needed; the four-period synthetic end-to-end regression does not satisfy the real-source gate.
3. Several real results pages contain damaged/missing native text or unsupported financial layouts. The new source-row fallback was tested with synthetic model responses, not validated with a live model. Lender extraction remains limited; industrial ratios are not applied indiscriminately.
4. All portfolio Push analyses must be recomputed against the repaired classifier/results versions in the user's existing complete cache. The new 18-stock discovery cache did not contain those historical analyses.
5. A live model run and independent semantic review remain outstanding. The remaining eight-module breadth in the original master plan is not claimed complete. The reviewed plan prioritizes the two core workflows; additional polish remains Day 4.
6. Production/mobile validation and deployment remain later phases. Source hosts can return errors and documents can exceed explicit size limits. These are visible partial states, not empty successful research.

The read-only `scripts/verify_day3.py` report deliberately exits 1 while acceptance gates are open. The audit here recorded 32/56 checks passing and 24 open checks, mostly the 18 current-EOD failures. An unavailable check is not a passed check.

## Apply and verify locally

The supplied update package changes source/tests/docs only. Its installer checks baseline hashes before changing anything and makes backups of changed existing files. It never replaces `data/finn.sqlite3`, other databases, `.env`, downloaded evidence or unrelated files. If you have edited the project since the uploaded ZIP, a conflict stops the update before writes.

From the unpacked update folder:

```powershell
python apply_update.py --project "C:\path\to\finn"
```

From your existing project root, with its existing virtual environment activated:

```powershell
python -m pip install -r backend/requirements.lock.txt
python -m pip install --no-deps -e backend
python -m pytest backend/tests -q
python -m finn.dev --db data/finn.sqlite3
```

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Optional model use: privately set `GEMINI_API_KEY` in the backend/worker terminal, then start `python -m finn.dev --db data/finn.sqlite3 --use-model`. The backend does not automatically load `.env`. `FINN_FLASH_MODEL` selects extraction; `FINN_REASONING_MODEL` selects reasoning. Do not paste keys into chat, frontend variables or command-line arguments.

For the final data acceptance run, stop the worker first so ingestion remains serialized. Preserve a backup of your existing database. These commands update that same cache and record partial failures honestly:

```powershell
python -m finn.cli --portfolio --db data/finn.sqlite3 --workers 3 --output verification/day1-current.json
python -m finn.push_ingest --db data/finn.sqlite3 --days 30 --workers 3 --force --use-model
python -m finn.pull --db data/finn.sqlite3 --symbols INFY DEEPAKNTR HDFCBANK KPIL --force --use-model --output verification/day3-current.json
python scripts/verify_day3.py --db data/finn.sqlite3 --unseen KPIL --out verification/day3-acceptance-current.json
python scripts/verify_pull_sources.py --db data/finn.sqlite3 --out verification/day3-source-audit-current.json
```

Omit `--use-model` for a deterministic-only run, but that cannot pass the live-model gate. Send back the acceptance report and relevant source-error summaries; no huge database or credentials are required. A live model response must still be assessed against the cited primary evidence before calling the workflow fully accepted.
