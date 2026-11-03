> Historical checkpoint. Current status: [final pack status](../../final-pack-status.md). Current setup: [final pack setup](../../final-pack-setup.md).

# Warm-up repair, revision 2: exact Polycab reproduction

The first repair fixed one reproduced financial-row regex defect but missed a second defect in management speaker matching. The new company/document progress identified the exact remaining stall: POLYCAB document 4, POLYCAB_08102026190117_Intimation_to_Stock_Exchange.pdf. The official 60-page filing was downloaded again; its raw SHA-256 matches the earlier captured source exactly: a3a1264b2c68a37d607233586365a031fa2d3caf1c064dc73e15bed3713743ae.

An isolated replay exceeded a 13-second deadline, with repeated stack dumps in transcript_context.management_roster at pattern.finditer. Speaker candidates can retain many spaces between words from PDF columns. Replacing every individual space with an independent \\s+ produced adjacent unbounded repetitions. The repair builds one whitespace matcher per word boundary. The original name text, source quotes, role checks and evidence remain intact.

The exact full document now completes source chunking in approximately 0.03 seconds and full native build_research in approximately 0.077 seconds here. These are measurements of this single filing, not a promise for the whole portfolio or a semantic certification. Its legal pages do not become a four-quarter transcript ledger or verified financial claims.

A related repeated-number regex in the model-located row fallback is also replaced by explicit numeric-cell tokenization. The source-bound tests reject malformed rows and keep existing financial reconciliation guards. No model or API key was used for these regressions.

Current full suite: 318 passed, one non-failing Starlette/httpx deprecation warning. Tests include the exact 60-page PDF/text/hash, complete native research, 2/24/64-space speaker names, malformed model-located numeric text, all earlier financial/parser regressions and real KPIL accountability fixtures. See verification/speaker-stall-fix.

## Stop the old frozen process

Try Ctrl+C in the original PowerShell window. If it cannot return to the prompt, the old regex may be holding the interpreter. From a second PowerShell window in the actual FINN root, the following stops only verification/research Python processes using that project's virtual environment:

```powershell
$pythonPath = (Resolve-Path .\.venv\Scripts\python.exe).Path
$stalled = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
    Where-Object {
        $_.ExecutablePath -eq $pythonPath -and
        $_.CommandLine -match 'scripts[\\/]finalize_day3\.py|-m\s+finn\.pull(?:\s|$)'
    }
$stalled | Select-Object ProcessId, ParentProcessId
$stalled | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

Do not delete the database, transaction journal or backups. Stop the old process before applying the repair or launching another verifier. An interrupted SQLite transaction can be recovered on the next open; completed caches were committed separately.

## Apply the cumulative repair

This revision includes the entire previous warm-up repair. It supports the latest Day 3 source with or without revision 1 and with or without the separate Day 4 frontend update. Unknown source edits stop the installer before writes. No frontend, private settings, dependency pins or database is overwritten. Existing cache versions remain unchanged so eligible completed companies are reusable.

From this extracted folder:

```powershell
python apply_update.py --project "X:\finn_day1_verification_kit\finn"
```

From the actual FINN root, first run just Polycab so that a remaining problem can be identified without another whole-portfolio run:

```powershell
$env:PYTHONUTF8 = "1"
.\.venv\Scripts\python.exe -u -m finn.pull --db data/finn.sqlite3 --symbols POLYCAB --output verification/polycab-recheck.json
```

This standalone check is model-free and keeps the existing database. Let it reach its terminal result; an explicit failed/unavailable result is a failure to inspect, not a passed gate. The command still does real source discovery and may encounter provider limits; it is not equivalent to the fast single-filing replay measured above.

After Polycab completes successfully, rerun the finalizer:

```powershell
.\.venv\Scripts\python.exe scripts/finalize_day3.py --db data/finn.sqlite3 --use-model
```

Keep both model settings on gemini-3.5-flash-lite. Eligible caches are reused; missing, expired or failed sources can need work. The finalizer streams warm-up/research progress, with company/timestamp/document labels, 30-second heartbeats and completed-company report checkpoints. Heartbeats are liveness signals, not fabricated progress. They are not a hard execution deadline for all possible malformed sources.

Send verification/day3-final-local/day3_verification.zip when the final run finishes. Source/model/semantic acceptance and real-phone Day 4 checks remain pending; this repair is not a blanket error-free guarantee or Day 5 deployment. This note is an engineering record, not the original AI conversation export.
