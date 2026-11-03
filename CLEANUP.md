# What to keep, regenerate or archive

The downloadable `finn/` folder is already cleaned. The updater's `--cleanup` removes only known obsolete/generated items from an existing active tree by **moving** them to `finn-release-backups/<run>/quarantine` beside that tree. It performs no permanent deletion. Stop all FINN processes first.

| Item in your existing folder | Action |
| --- | --- |
| `.env`, `.env.local`, frontend/backend private env files | Keep. Never overwrite with `.env.example`. |
| `data/`, every `.sqlite3`/`.sqlite`/`.db` and WAL/SHM/journal companion | Keep. No automatic cleanup targets these files. A sidecar must not be removed while SQLite is active. |
| `.git/`, unknown edits, editor settings | Keep. The pack contains no Git history and never replaces yours. |
| `.venv/` | Keep if it uses Python 3.12. If it uses 3.15, rename it for rollback and create a 3.12 environment as explained in setup. |
| `frontend/node_modules/` | Keep when working; generated dependency output is excluded from the ZIP. `npm ci` recreates it from the lockfile when needed. |
| `frontend/.next/`, `frontend/tsconfig.tsbuildinfo` | Rebuildable output. `--cleanup` quarantines it; the next production launch rebuilds it. |
| `__pycache__/`, `.pyc`, pytest caches, backend `*.egg-info` | Rebuildable metadata. Recognised items are quarantined. Reinstall editable backend after cleanup. |
| `frontend/.preview-qa.json` | Local-only preview override. Quarantined if present; it must not control your real workspace. |
| `.qa/` and `frontend/.qa/` | Excluded from the release. If present locally, inspect and archive them manually only after confirming they are disposable QA captures. The automated tool leaves these directories and their databases intact. |
| Old root `export-manifest.json`, `export-verification.json`, `day3-delivery-manifest.json` | Known originals are quarantined; preserved copies live under `docs/history/manifests`. Unknown variants stay untouched. |
| Old Day 1–4 setup/status/design documents | Known originals move out of the active locations; retained history is consolidated under `docs/history/checkpoints`. Current instructions are in `docs/final-pack-setup.md`. |
| Duplicate official PDFs under `docs/original-inputs` | Known byte-identical duplicates are quarantined. Canonical originals remain `docs/source-main.pdf` and `docs/source-reference.pdf`. |
| `backups/`, `update-backups/`, prior verification runs or old ZIPs | Keep outside the app after review if desired. The updater never deletes them; they may contain the only rollback copy or private data. |
| Backend fixtures, frontend tests, legacy components imported by tests, `scripts`, lockfiles, notices/licenses | Keep. They are needed for reproducible verification or attribution. |

If you want a fresh folder instead of updating in place, keep the original project as your backup and work from the supplied complete `finn/` source tree. Copy private configuration/data only while the old app is stopped; do not selectively copy or delete a database WAL file. Existing-folder updates avoid copying your large SQLite database entirely.

After successful local review, you may remove confirmed generated caches or the dated quarantine yourself to reclaim space. Keep the source-before backup and receipt until the release is accepted. Do not run a blanket recursive deletion over the project or all ZIP/SQLite files.

Unknown source conflicts: the entire update stops before writing. Preserve your edit and deliberately merge the matching file from the supplied `finn/` tree. There is no force switch.
