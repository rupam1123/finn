# Publish source updates from GitHub

The canonical hosted source is the private repository `rupam1123/finn`, branch `sites`. The original Python application, data-export tools and frontend source remain on `main`, which links this checkout as the `hosting` submodule. Never upload private SQLite exports, keys or runtime state to either branch.

The linked Sites task checks the `sites` branch for new commits. This is scheduled publication, not an immediate GitHub webhook. A task that sees no source change must stay quiet.

1. Read the current Sites skill and this Site's metadata. Preserve its owner-private audience and its existing D1/R2 data. Reuse the exact project ID in `.openai/hosting.json`.
2. Obtain fresh native source-repository write access and open the Site in a new empty checkout with the supported source helper. Keep all credentials in memory and send them only through hidden stdin. Never generate a new bypass token without an explicit user request.
3. Use the user's connected GitHub account to inspect and fetch `refs/heads/sites` from `https://github.com/rupam1123/finn.git`. Verify that the revision has a successful `FINN Sites checks` run. If authenticated Git access is unavailable, or checks failed, leave the live version unchanged and report the concrete blocker. Do not use a personal token in an Actions secret or invent a deployment endpoint.
4. Compare the fetched source with the current Site source, excluding only `.openai/upstream.json`. If the trees match, stop without publishing. Check for independent Site changes since the last recorded upstream revision; preserve both sides and report a conflict instead of overwriting them.
5. In this fresh checkout, apply the GitHub revision's tracked source with `git restore --source FETCH_HEAD --staged --worktree -- .`. Preserve Git history, ignored dependencies and local tool state. Record the selected GitHub SHA in `.openai/upstream.json` as `{ "repository": "rupam1123/finn", "branch": "sites", "commit": "<verified SHA>" }`.
6. Install dependencies only when required. Run TypeScript, `node --test tests/read-model.test.mjs`, and the supported Sites build. Use the source helper to commit/push the exact tested source and package it; then publish that saved version with the native private Sites operation. Never force-push or publish a failed build.
7. Confirm native deployment success and use existing Site service access for bounded health/capability readback, sending credentials only to the exact Site origin without following redirects. Preserve read-only mode. Do not invoke upstream data providers or models, reseed the database, rotate tokens, change access, or create another Site.

Report a newly completed deployment, failure or required action briefly. Stay quiet for unchanged source. A schedule being saved does not prove that an unattended deployment has succeeded; verify its first run separately.

For edits made to the original `main` frontend, run `scripts/sync_sites_source.py`, validate the hosted source, and push the resulting `hosting` commit to GitHub's `sites` branch. The sync tool preserves independent hosted edits. Data refreshes require a separate verified private import; code publication does not fabricate refreshed financial evidence.
