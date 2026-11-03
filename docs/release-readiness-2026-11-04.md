# Source readiness · 4 November 2026

Publication remains paused. A GitHub source push is authorised; a Site deployment/access change is not.

## Final design scope

Read the linked Swiftz Figma launch frames 1584:2484 (light), 1585:563 (dark), and home frames 1584:2839 / 1584:4386. Verified SF Pro Display text roles, #96F15B accents, white/black pages, #F5F5F5 / #1A1A1A cards, 430×932 frame, 300×324 welcome illustration and 390×60 primary action. The root route now shows FINN welcome content with an Open workspace action and research link, without authentication. System SF Pro falls back to bundled DM Sans where unavailable. Small muted text uses a darker accessible light-theme variant.

The glass stylesheet is no longer imported. Active Swiftz styles use solid surfaces and disable backdrop filters/shadows. Existing route data, controls, evidence and release-to-select gestures remain. Company logo assets are local with source URLs; missing logos use honest ticker initials. Source identity logos do not confer data licensing or endorsement.

## Cleanup audit

- SHA-256 scan of tracked nonempty files found only four identical company route page wrappers. These are required distinct Next.js route entry points and are retained.
- TypeScript noUnusedLocals/noUnusedParameters identified 17 unused imports across nine components; removed after reviewing their import declarations.
- Legacy components imported by regression tests, fixtures, lockfiles, license notices and historical verification are retained.
- The hosted source is an intentional separate runtime copy managed by the sync manifest, not an accidental duplicate.
- Private env files, SQLite/WAL data, Git metadata, unknown files, environments and backups remain untouched. No blanket cleanup or source-pack apply was run. No file was deleted merely because its name looked old. The outer pack manager was not present in the parent directories checked; no pack cleanup apply was attempted.

## Validation scope

The preceding usability pass passed 407 backend tests, 77 UI checks, Next/Vinext builds, ten hosted read-model tests, 11 local HTTP checks and the router export guard. Final pass results are appended after execution below. No new paid model/provider acceptance run is inferred.

Browser control currently reports disabled in Work settings. Pixel-level visual matching, actual slide gestures, short-screen/soft-keyboard behaviour, Safari and screen-reader checks remain pending. Automated tests and HTTP 200 do not close these gates.

## Before deployment is resumed

Use the Site-owning account; preserve the existing Site ID and audience. Verify the final commit's checks and deploy its exact source. Check the welcome page in both themes, Inbox-to-Radar navigation, drag release, company tabs, evidence dialogs/PDF fallbacks and public read-only enforcement on the actual hosted URL. Preserve saved D1/R2 data and the sealed import API. Resolve source permissions/licensing and actual-device gates. Do not claim that a repository push updates the paused live deployment.

## Final pass results

Compiler-confirmed unused-import checks passed. Existing workspace tests plus pointer/assistant checks and four new welcome/asset checks passed (81 UI checks in total), with the active-theme regression rerun after its update. Twenty local company-logo files passed PNG/dimension checks; TMPV, JYOTHYLAB, SONACOMS and CAMS retain the initials fallback. Both production builds, hosted TypeScript/read-model tests and the router export guard are checked before the source push. Browser verification remains pending, not passed.
