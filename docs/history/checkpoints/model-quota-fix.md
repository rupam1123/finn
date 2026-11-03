> Historical checkpoint. Current status: [final pack status](../../final-pack-status.md). Current setup: [final pack setup](../../final-pack-setup.md).

# Gemini quota handling — 1 November 2026

The user's AI Studio screenshot displays Gemini 3.5 Flash-Lite at 0/15 requests per minute, 0/250K input tokens per minute and 0/500 requests per day. It does not demonstrate which limit caused the earlier HTTP 429. The dashboard must be for the project associated with the actual key loaded by FINN; delayed dashboard data, other clients and different quota windows can matter. A new API key in the same project shares that project's quota.

## Changes

- Live default-client requests are spaced by FINN_MODEL_RPM, default 12. That is one request start every five seconds, with a shared process-local model gate covering Flash, Reasoner and retries. Injected/mock clients do not sleep for this gate.
- Google RetryInfo and Retry-After delays are respected, including HTTP dates. A requested wait above 120 seconds is reported rather than retried earlier than requested. Daily quota IDs cause an immediate explicit stop for that model. Exhausted quota retries block additional calls to that model for the remainder of the process, avoiding a retry storm.
- Only HTTP status and allowlisted quota identifiers are exposed. Provider messages, project identifiers, response bodies, headers and credentials are not persisted or printed. The key is redacted from constructed quota errors.
- A --use-model finalizer now stops after failed preflight, before backup/build/ingestion/model-free reprocessing. It still writes a failure report ZIP. It no longer continues the full requested model verification with model-free analyses after that failed check.
- FINN_MODEL_RPM is accepted from the private root .env and documented in .env.example. Actual private settings, the database, frontend, existing financial math and citation gates are unchanged.

This pacing is per process. It cannot coordinate other applications or separately running workers using the same project, or guarantee token/day/spend quotas. Keep one verifier running. A 250K token limit can still be reached by large contexts, and a 500-request daily allowance may be insufficient for the full corpus plus enrichments/retries. The live-model run can require hundreds of calls and tens of minutes; the earlier six-minute run was model-free after preflight failed. No claim is made that another key/account automatically increases quota.

## Apply

Use this after the latest warm-up repair revision 2. Stop other verification/API workers first.

From this extracted folder:

```powershell
python apply_update.py --project "X:\finn_day1_verification_kit\finn"
```

No dependency reinstall is needed. The installer checks baselines and backs up changed source files. It preserves your frontend, database and private .env.

## Confirm the correct key/project, then run one preflight

1. In AI Studio API Keys, check the project attached to your key. Select that same project in Rate Limit. Never share the key in chat.
2. If switching to another authorized project, privately replace GEMINI_API_KEY in the actual root .env. Keep both model tiers on gemini-3.5-flash-lite. A different key in the same project does not reset quota.
3. From your actual FINN root, clear an old shell-exported key so the private .env can provide the replacement, and explicitly use the shown pacing:

```powershell
Remove-Item Env:GEMINI_API_KEY -ErrorAction SilentlyContinue
$env:FINN_MODEL_RPM = "12"
$env:PYTHONUTF8 = "1"
.\.venv\Scripts\python.exe -c "import json; from finn.settings import load_local_settings; from finn.model import Flash,Reasoner; from finn.validation import model_preflight; load_local_settings(); print(json.dumps(model_preflight([Flash(),Reasoner()]),indent=2))"
```

This makes one connection check when both tiers use the same model, with bounded retries if Google requests them. A successful single request does not guarantee enough quota for the whole corpus. If it fails, send only this redacted output; quota IDs can now distinguish a per-minute versus daily request limit. Do not repeatedly launch full finalizers to test the key.

After successful preflight and checking the available daily allowance, run:

```powershell
.\.venv\Scripts\python.exe scripts/finalize_day3.py --db data/finn.sqlite3 --use-model
```

Return verification/day3-final-local/day3_verification.zip. Before final acceptance, the actual source-linked model outputs and four-period comparisons still require review. No live Gemini call was made here; test transports cannot pass that acceptance gate. This engineering note is not the original AI build-history export.

Official quota reference checked on 1 November 2026: https://ai.google.dev/gemini-api/docs/rate-limits . Dashboard limits are project-specific and may change.
