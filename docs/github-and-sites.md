# GitHub and ChatGPT Sites

The source repository is private: https://github.com/rupam1123/finn.

- `main` retains the original Python FastAPI/SQLite + Next.js application and the migration/synchronization tools.
- `sites` contains the Sites-compatible read-only port. `hosting` is a submodule pointing to that branch in the same private repository.
- Private database backups, exports, keys, installed dependencies and generated builds stay outside Git.

The hosted app is https://finn-research-rupam1123-20261103.quaintmoon4.chatgpt.site. It uses owner-private platform access. The initial private server deployment succeeded on 3 November 2026. Data import and hosted readback must be verified before declaring the migration complete.

## Updates

Commit and push application edits to `main`. Its GitHub Actions workflow runs the original backend/frontend checks and production build. After success it safely syncs Git-tracked interface files into the `sites` branch, preserving independent hosted edits, and dispatches the hosted checks. Direct edits to the port belong on `sites`.

A linked Sites task is configured to check that branch hourly in Asia/Calcutta and publish newly validated source using native Sites credentials. This is scheduled polling, not instant deployment on every push. A saved schedule does not prove its first unattended run succeeded; that verification remains separate. Unchanged source stays quiet. The task preserves the live version when checks, access or conflict checks fail.

Local edits are not uploaded until committed and pushed. Source synchronization covers the interface and retained calendar. Python financial/backend behavior changes require a corresponding tested port; new saved financial evidence requires a separate private import. Code updates never silently run provider/model research.

## Migration and verification

The original database is opened read-only to create a consistent private SQLite backup. The export retains structured tables and file identities, plus Python-calculated read models. D1 stores structured records and R2 stores the original response bytes. Uploads enforce SHA-256; readiness is withheld until every table count and evidence-object size matches.

The port passed 240 comparisons against the original saved Python API and nine regression checks for decimal thresholds, aliases, microsecond cutoffs, calendar abstention, immutable historical diagnostics and blocked writes/imports. Both original and hosted TypeScript checks pass; the Sites build passes. The original 391 backend tests and 60 frontend checks also passed locally, and the initial GitHub Actions run passed its production build.

New research jobs remain disabled, matching public-review mode. Saved evidence gaps and source/model limitations remain visible. This port does not implement the original owner's live Python worker on Sites.

After the private import, remove `FINN_MIGRATION_KEY` from hosted environment values and redeploy. The import endpoints then refuse writes. Retain the local import receipt; never commit its private inputs.

## Local source commands

```powershell
git status
git add -- frontend/app frontend/public
git commit -m "Update FINN interface"
git push origin main
```

For a fresh complete checkout, clone with `--recurse-submodules`. The source and hosted branches have separate histories; do not merge them into each other or force-push either branch.

Source, licensing, semantic and physical-device review gates in the handoff are not resolved by deployment checks.
