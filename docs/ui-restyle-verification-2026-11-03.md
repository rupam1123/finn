# FINN UI restyle verification — 3 November 2026

Applied the verified Swiftz theme/type/control treatment and the supplied liquid-glass reference to the existing FINN frontend. Routes, content, navigation destinations, section order, icons, component responsibilities and financial behavior are retained.

## Design evidence

Read the linked [Swiftz Figma file](https://www.figma.com/design/MCzGH0Vey4okYFpBcr7itx/Swiftz-App-by-Galuh--Community-?node-id=0-1) with the Figma connector before editing. Root design context required a concrete frame; metadata identified the relevant frames, then high-fidelity design context and screenshots were returned for light Home `1584:2839`, dark Home `1584:4386`, light Market `1584:3177` and dark Market `1586:4375`. Variable definitions also confirmed Black and Light Green.

| Property | Verified reference |
| --- | --- |
| Font | SF Pro Display; regular 400, medium 500, semibold 600; approximately −1% tracking |
| Light | White background, black text, `#F5F5F5` tiles, `#777777`/`#888888` secondary text |
| Dark | Black background, white text, `#1A1A1A` tiles, `#BBBBBB` secondary text |
| Accent | `#96F15B`; reference chart green `#53D300`, negative red `#DC1616` |
| Frame | 430 × 932 |
| Home controls | 191 × 90 summary tile, 25px radius; 390 × 60 action, 20px radius; 390 × 330 portfolio tile, 30px radius; 20px outer inset |
| Market tiles | 195 × 210, 25px radius, 10px gap |

The liquid-glass image named in the handoff was available and inspected. Its fine edges, inner highlights, neutral translucent material and soft blur informed the presentation. It was not used as an app background. No Swiftz images, icons, sample financial values or flows were added.

Reference measurements were verified, then adapted to FINN's existing compact geometry. The new stylesheet adds no positioning, grid, dimensions, margin or padding declarations. One mobile Inbox subtitle uses 11px text with its existing 20.4px line height to preserve the baseline wrap. Small text and semantic colors use contrast-adjusted variants where the reference's brighter colors would impair readability.

SF Pro Display is configured as a local/system font. It is not installed in the inspected Windows font directory, so an exact Windows font match is not claimed. The existing bundled DM Sans remains the fallback; no proprietary font or new font-service request was added. Product copy, including historical About attribution wording, remains unchanged as requested.

## Changes and preservation

- Added `frontend/app/workspace/swiftz.css`, imported after existing presentation styles.
- Updated browser theme colors to white/black in the existing viewport and theme toggle; updated the existing theme-test expectations.
- Kept original `Workspace.tsx`, `workspace.css` and `glass.css` byte-identical to the source backup. No backend application, dependency, lockfile, fixture, icon or financial/parser/storage logic was changed.
- Original source copies and hashes are under `verification/ui-restyle-2026-11-03/before/source`. Private settings and SQLite evidence were not replaced or reset. The preview used `--public-review`, without a worker or model execution.

## Measured verification

| Check | Result |
| --- | --- |
| Existing frontend workspace suite | 60 checks passed; mocked/synthetic regression fixtures, not source/model acceptance |
| TypeScript | Passed |
| Final production build | Passed |
| Baseline comparison | 24 samples: Inbox, Radar, research launchpad, Universe, Source health and TCS Forensics; both themes at actual 390 × 844 and 1440 × 1000 viewports |
| Sampled geometry | No changes to recorded page headings, main content grids, company context, sidebar, topbar or dock rectangles; no horizontal page overflow |
| Additional rendered views | TCS Say–Do, document Vault and About in both themes at mobile/desktop sizes; populated 7-day Inbox and a retained filing inspector |
| Interactions | Company search keyboard selection opened TCS; 7-day filter showed retained disclosures; financial table scrolled within its labelled region and retained missing values; citation retained quote/page/source links; closing evidence restored citation focus |
| Short settings dialog | Both themes at 390 × 520: dialog top 12px/bottom 508px, scrollable body, visible pinned Done action |
| Read-only API | `public_review: true`, `research_jobs_enabled: false`; source refresh controls disabled |

The browser reports reduced transparency enabled, reduced motion disabled and forced colors disabled. Solid-surface rendering was checked, including a final production check that evidence backdrop blur is `none` in both themes. Standard/WebKit declaration order was corrected after the production minifier initially retained only the prefixed override. Full glass rendering with reduced transparency off was not independently exercised. Existing reduced-motion regression checks passed; forced-color rules were retained and supplemented, without a forced-color device claim.

Evidence excerpt, dialog bounds and PDF controls were exercised. The embedded PDF view was blank in the in-app browser; the existing Saved PDF and Original source alternatives remain. Successful PDF rendering in this browser, physical phone/Safari, screen-reader performance and financial/source/model acceptance are not inferred from this restyle verification. No provider refresh, paid research, deployment or submission was performed.

Logs, original/updated screenshots, Figma measurements/context, geometry comparison and interaction receipts are under [the verification folder](../verification/ui-restyle-2026-11-03/). [Theme preview](../verification/ui-restyle-2026-11-03/preview-themes.jpg).
