> Historical checkpoint. Current status: [final pack status](../../final-pack-status.md). Current setup: [final pack setup](../../final-pack-setup.md).

# FINN Day 1–3 source candidate — 31 October 2026

This is the current status record. The official brief and reviewed plan corrections remain authoritative. Source fixes are implemented, with regression and source checks below. **Day 1–3 acceptance is not yet signed off:** real Gemini outputs and four-period semantic review still require the private local key. No error-free, universal extraction or independent accuracy guarantee is made.

## Current implementation against the reviewed plan

| Requirement | Implementation | Acceptance boundary |
| --- | --- | --- |
| Day 1 ingestion, 18 holdings and arbitrary symbols | Yahoo EOD, NSE announcements/annual reports, separately labelled Screener staging, immutable raw hashes and last-good retention | Source observations and failures remain visible; provider response acceptance does not certify exchange completeness |
| Day 1 deterministic EOD | Exact current-frame hash binding for the guarded NSE final-row fallback; original inputs audited independently; up to 60 context sessions | Source/date/adjustment failures abstain; no stale-as-current substitution |
| Day 2 Inbox | 17 categories, exact 24-hour default, explicit 3d/7d/30d/latest-session views, category watches and EOD thresholds | Unknown, scanned or failed-source filings remain visible; no causal price attribution |
| Day 2 results and management | Source-bound native/table/image fallbacks, explicit basis/units/periods, per-cell rounding checks, issuer-bound management fields | Missing EBITDA and uncertain scope remain missing; model outputs need source review |
| Day 2 complete-corpus model processing | Local --use-model applies to the full filing corpus, with routine short-circuiting and sequential paid calls | Processing success alone cannot pass the model-usage gate; review sample reports include actual source-linked outputs |
| Day 2 filing archives and recovery | Bounded single-PDF official NSE ZIPs; both archive and PDF hashes retained; prior verified PDF bytes can survive failed refreshes | A retained source keeps its original observation time, remains surfaced for review and records the failed refresh |
| Day 3 research and jobs | General NSE discovery, bounded transcript following, selected annual-report sections, durable worker, safe polling and explicit refresh | Partial sources are visible; use finn.dev to launch API and worker together |
| Day 3 four-period Say–Do | Verified management context, strict horizon/basis/scope matching, separate annual/quarterly revisions, source-linked model commentary | Numerical verdicts require comparable primary facts; no invented assessment numbers or analyst promises |
| Day 3 warm caches | Real discovery for all 18 portfolio plus five showcase symbols, bounded three-worker model-free warm-up | Every required cache is checked; saved-only placeholders do not pass |
| Days 4–5 | Existing functional frontend retained | Mobile/browser polish, deployment, original AI export and submission are later work |

The reviewed brief treats the eight research modules as a menu. The core remains Inbox + primary research/four-period accountability. Supplemental financial/cash/governance views must not be presented as independently verified conclusions when their evidence is incomplete. Banks do not receive generic industrial EBITDA/CFO/PAT judgments.

## Recorded validation

- Current restored backend suite: **305 passed**, one non-failing Starlette/httpx deprecation warning. Includes real KPIL transcript replay, three real official NSE archives, current-input provenance, financial rounding, annual/quarterly revision separation, model-output guards, cache preservation and verification-run safety.
- Frontend production build, typecheck and Pull race checks are recorded under verification/day3-continuation.
- All three previously unsupported NSE archives were retrieved and their archive/PDF chains verified: Trent and Persistent contain readable management filings; Sun Pharma contains a scanned page and remains OCR-required.
- A fresh HDFC Bank result download returns the complete 24-page PDF with SHA-256 1a25f460842bbd8e3632a000cdbc625d7aa1ec2934d3b0d8b60d270bb33e3bdf. An earlier run encountered a truncated response. The new recovery path can reparse prior verified bytes across parser versions without changing source observation times or hiding the failed refresh. Existing valid analyses remain unchanged during failed refreshes.
- The supplied finn_upload.sqlite3 is intact and contains an older snapshot: 232 filings, 40 saved filing documents and no saved Pull research. Work uses a separate copy; the uploaded database is unchanged.
- Full current-cache/23-symbol and live-key verification must now be run on the existing local database. The backend source is ready for that final acceptance run. Earlier complete corpus reports in verification/day3-final and day3-repair remain historical; their 51/56 gate score and earlier source failures are not current-version sign-off.
- The final speaker guard also prevents anonymous analyst/moderator turns, with or without colons, from inheriting the previous management identity. Research is versioned pull-v9 / say-do-v4 so older results are rebuilt.
- No live Gemini call has been made here. Mock responses and human/captured-source regressions cannot pass live-model acceptance. No credentials were extracted from the uploaded environment file.

## Final local verification

Apply the update to the existing project using its installer. It verifies all baselines before changing files, backs up existing changed files, and supports the original upload, previous repair and previous final candidate. Unknown local edits stop the update before writes. Databases and the private environment file are preserved.

From the extracted update directory:

```powershell
python apply_update.py --project "C:\path\to\finn"
```

From the existing project root, with the Python environment activated:

```powershell
python -m pip install -r backend/requirements.lock.txt
python -m pip install --no-deps -e backend
python scripts/finalize_day3.py --db data/finn.sqlite3 --use-model
```

Keep GEMINI_API_KEY in the local shell or root .env. Stop other ingestion/workers first. The finalizer refuses missing database paths, checks integrity and backs up before mutation. Build failures stop ingestion. Both configured model tiers are preflighted (one call when they share a model). With --use-model the readable filing corpus receives model classification/enrichment; this is a paid full-corpus run, not just an eight-filing demonstration. Valid cached analyses and routine filters reduce repeated calls. Model-free discovery uses at most three company workers.

Each stage prints its name and writes its matching log. A cold whole-portfolio run can take substantially longer than a single ticker request. Source failures and incomplete evidence remain failed/partial states; they are not turned into invented success.

Return **verification/day3-final-local/day3_verification.zip**. It contains an explicit list of result, acceptance, source-audit and cited research/model-sample reports. Credentials, database backups and unrelated files are excluded. Prior reports are archived before reruns so stale success cannot be mistaken for a current result. The large database is not needed in chat.

Inspect the reported tables and comparisons against their cited primary pages before semantic sign-off. Day 4 begins after reviewing those results.

## Runtime/model notes

Python 3.12+ and Node 20.9+ are required. The default model is gemini-3.8-flash; explicit FINN_FLASH_MODEL and FINN_REASONING_MODEL settings are preserved. Google limits legacy 2.5 access to prior active users; choose an accessible model if preflight fails. Official references checked on 31 October 2026: https://ai.google.dev/gemini-api/docs/deprecations and https://ai.google.dev/api/generate-content . The documented request shape does not replace the pending live run.

The decision log is not the required original conversation export. No deployment, submission email or Day 4 implementation has been performed.
