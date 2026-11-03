> Historical checkpoint. Current status: [final pack status](../../final-pack-status.md). Current setup: [final pack setup](../../final-pack-setup.md).

# Latest repair: revision 2

See [exact Polycab speaker-stall repair](speaker-stall-fix.md). The section below records revision 1; it did not resolve the later exact-source speaker regex stall. Current validation is 318 passing tests.

---

# Warm-cache parser repair — 31 October 2026

The uploaded warm log contains 17 company discovery events, 212 document events, 16 analysis events and 15 company completions. It has no traceback. Old concurrent events omit the company identity, so the last displayed completion cannot identify which of the two in-flight companies was still executing.

A local reproduction exposed a financial-table regex with exponential backtracking: a long damaged numeric line followed by an unsupported tail can monopolize the Python interpreter. The old parser exceeded a three-second subprocess deadline on an 80-digit example. This is a concrete defect consistent with the observed frozen log, not proof of the exact live row in the user's database.

The repair tokenizes numeric cells sequentially, preserves exact source quotes and grouping checks, and abstains on malformed/extra cells. Eight regressions cover the hang, exact cells/quotes, damaged tails, company-labelled progress and partial-batch checkpoints. The full backend suite now has 313 passing tests; see verification/warm-stall-fix/backend-tests.log. The non-failing Starlette/httpx warning is unchanged.

Warm-up now labels every event with company and timestamp, reports analysis per document, emits a 30-second heartbeat showing each active stage and idle duration, and atomically checkpoints every completed company into the output report without waiting for earlier submissions. The finalizer streams warm-up and four-company research progress to PowerShell as well as their log files. A heartbeat shows that the runner is alive; an increasing idle duration is not presented as completed work.

Windows test fixtures are explicitly read as UTF-8. This repair does not change the model settings, frontend, database or existing cache version. Eligible processed filings and company caches can be reused; failed, changed or expired sources may still require network/model work. No cache entry is marked accepted just to make verification pass.

## Apply

Stop the old verification before applying. Try Ctrl+C in its original PowerShell window. Wait for that process to stop; do not start a competing run. If the interpreter will not stop, use Task Manager to end the Python processes belonging to this FINN verification. Keep other applications/processes intact. SQLite may recover its transaction journal on the next open; do not delete the database, journal, WAL files or backups.

From this extracted repair folder:

```powershell
python apply_update.py --project "X:\finn_day1_verification_kit\finn"
```

The installer accepts the latest Day 3 source, with or without the separate Day 4 frontend update. It checks every baseline before writing, backs up changed files and rejects unknown source edits. No dependency reinstall is required.

From the actual project root:

```powershell
$env:PYTHONUTF8 = "1"
.\.venv\Scripts\python.exe scripts/finalize_day3.py --db data/finn.sqlite3 --use-model
```

Keep both model tiers on the working gemini-3.5-flash-lite. The finalizer still runs the checks needed for an honest final report. It reuses eligible caches rather than deliberately discarding prior work. During warm-up the console now prints company/document progress and 30-second heartbeats. It may still take time to complete missing companies and paid research; no completion-time guarantee is made.

Return verification/day3-final-local/day3_verification.zip. If progress stalls again, send the company-labelled final log lines, including the heartbeat idle time. Native browser/phone Day 4 checks and Day 5 deployment/submission remain separate. This note is an engineering decision record, not the original AI conversation export.
