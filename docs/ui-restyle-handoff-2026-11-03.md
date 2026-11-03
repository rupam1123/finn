# FINN UI restyle handoff — 3 November 2026

**Completion update:** The linked Figma Home/Market frames were read in both themes, and the presentation restyle is implemented. See [the verification report](ui-restyle-verification-2026-11-03.md) for verified properties, source backups, passing checks, screenshot scope and remaining font/device limitations. The access state and “no application files changed” statement below describe the start of this work.

**Follow-up refinement:** Selected navigation now uses green, range controls/sidebar are restrained, light-theme cards/tables have clearer separation and the Research entry explicitly describes AI-assisted company analysis. See [the follow-up verification report](ui-refinement-verification-2026-11-03.md), including the final browser-verification limitation.

Continue in `X:\finn_day1_verification_kit\finn`. Read `AGENTS.md` and its required handoff/status/plan documents first.

## User's authorized request

Restyle the existing FINN app using both themes in this Swiftz community file:

https://www.figma.com/design/MCzGH0Vey4okYFpBcr7itx/Swiftz-App-by-Galuh--Community-?node-id=0-1

Match its verified light/dark colors, font family and weights, typography widths, spacing, tile and button treatment. Mix in the attached liquid-glass reference: translucent surfaces, fine glass edges, soft blur and inner highlights. Keep the result readable and compact.

**Preserve the app's structure:** routes, page positions, navigation destinations, section order, existing content/data, component responsibilities and all interactions. This is a presentation change. Do not replace the app with the Swiftz app or add its onboarding/trading flows. Existing financial, primary-source, read-only and accessibility safeguards remain.

The user explicitly requested the Figma font, overriding the older instruction to preserve the current font for this UI task. Retain current icons unless a presentation change actually requires otherwise; do not replace content with demo fixtures.

## Reference and access state

- The public Figma canvas opened successfully and visibly contains light and dark versions. Its exact typography and dimension properties were not verified.
- The Figma plugin is installed and enabled. Its design-reading tools were absent from the previous chat's exposed tool list. This does not establish that the user's account is disconnected.
- First check the new chat's tools and perform one real Figma read before proposing configuration changes or editing. Use the Figma design-to-code skill when its reader is available. Inspect relevant Home/Market/control frames in both themes rather than relying on the root canvas alone.
- The user already approved using browser inspection and the visible canvas as a fallback if the design-reading tools remain unavailable. Do not ask for that approval again. Flag any font/dimension/color that cannot be verified; do not claim an exact match from guessed values.
- Windows browser control stopped because it could not reliably identify the current URL. Avoid repeating that failed Windows-controller route. The in-app Figma canvas was accessible.

Glass reference: `C:/Users/dasr3/AppData/Local/Temp/codex-clipboard-95ae6bcb-92a5-420f-bcae-5dd10d4d5231.png`. Inspect it with the image viewer before styling. This is a visual reference, not an application background asset. If the temporary file has expired, ask for that image again rather than inventing its contents.

## Existing frontend

- `frontend/app/layout.tsx`: stylesheet/font imports.
- `frontend/app/workspace/glass.css`: current theme tokens and final presentation overrides.
- `frontend/app/workspace/workspace.css`: shared route presentation.
- `frontend/app/workspace/ThemeToggle.tsx`: persisted light/dark behavior and browser theme color.
- `frontend/app/workspace/Workspace.tsx`: current shell and navigation; preserve its structure.
- Existing UI regression commands are in `frontend/package.json` (`test:workspace`, `typecheck`, `build`).

No application files have been changed for this restyle request. `verification/ui-reference-2026-11-03/reference-access.json` records the earlier access check and original file hashes. Back up source before applying changes, since this checkout has no Git metadata. Preserve private settings, SQLite/WAL files and unknown edits.

The earlier backend repair is complete within its documented engineering scope: the 3 November report records 58/58 acceptance, 391 backend tests and 60 frontend checks. Those are historical measured results, not a fresh test of this new UI change. Do not rerun paid model research or refresh the database for styling.

## Completion checks

Apply theme/type/control styling through existing components and CSS. Verify the requested views in both themes at desktop and mobile widths, including settings, source/evidence dialogs, financial tables, search and the fixed navigation. Preserve touch targets, focus, reduced motion/transparency, and readable contrast. Run appropriate existing frontend checks, TypeScript and the production build. Save actual before/after screenshots and report verification scope honestly. No deployment or submission is authorized by this restyle task.
