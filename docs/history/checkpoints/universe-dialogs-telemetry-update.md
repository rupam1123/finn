> Historical checkpoint. Current status: [final pack status](../../final-pack-status.md). Current setup: [final pack setup](../../final-pack-setup.md).

# FINN — Universe charts, dialogs, telemetry and feedback

Current cumulative source update following the fluid-navigation revision. Apply with the safe installer and run the production build described in `frontend-restructure-setup.md`. Preserve the existing Windows project, private environment and all SQLite files.

## What changed

Universe price lines and their area shading now use green for a rising displayed series, red for a falling series, and gray for endpoints with no net change. This compares the first and last displayed adjusted closes, not an invented trend or investment signal. Equal-price series plot at the middle of a correctly padded axis. A net-unchanged series can still fluctuate between its endpoints.

Each compact plot shows the selected saved price/date. Hover inspection is frame-coalesced; a native range control supports touch and keyboard inspection. The direction label describes the plotted saved-session window. The separate 1D badge is explicitly labelled and may legitimately have the opposite sign. Card spacing was tightened to accommodate these controls. Missing data stays missing. Raw volume remains blue, and raw candles use their own open-to-close direction. Return maps, badges and research-return numbers use the same semantic colors in both themes. General monetary values are not turned green merely because they are positive.

All shared native dialogs now have a bounded frame, a focusable internal scroll area and a retained header. Workspace settings has a separate pinned Done button. Visible-viewport height, keyboard inset and safe-area padding are accounted for. Escape, native modal focus, background scroll locking and return-to-trigger remain. Reset confirmation can be cancelled, and completion returns focus to its surviving trigger. Evidence, filter and confirmation windows use this same frame.

Small dismissible toasts confirm bookmarks, applied alert filters, quote/link copying, requested CSV downloads, resets and research queue actions. Only one toast is displayed at a time, with success/info/warning/error colors and polite announcements. It appears above an open dialog rather than behind the native backdrop. It expires after five seconds and pauses while hovered or focused. No toast history is saved or transmitted. Important failures remain visible in context; copying errors retain their accessible inline fallback. Toast feedback does not establish that a browser download completed or that a research job passed.

## Telemetry inspection and one backend fix

The saved records inspected here contain source/extraction gaps. They are not evidence of a rendering bug or of a current provider connection failure. The panel now groups related issues, explains their meaning and next step, retains every original stage/error/source URL, and labels the saved run separately from current navigation speed. A recorded model name does not prove successful execution. Missing metadata reads “Not recorded in this snapshot,” rather than the misleading “Not used.” No-error snapshots are not labelled complete merely because their error list is empty.

The inspection used captured public-source data, not the user's private live Windows database:

| Saved workspace | Observed gaps | Treatment |
| --- | --- | --- |
| INFY | Three `ModelUnavailable` stages and an attachment that was not a full earnings transcript | Retained and grouped. Model unavailability alone does not establish a quota error. The excluded transcript is not silently accepted. |
| POLYCAB | One non-PDF response and two missing BSE attachments | Retained; source links remain inspectable. No unrelated PDF is substituted. |
| DEEPAKNTR | Three certificate failures and three unavailable model stages | Retained. Certificate verification stays enabled. Local trust/provider diagnosis is still required. |
| SUZLON | Three prior document-host rejections | Fixed the current allowlist omission for exact `www.suzlon.com`. Existing recorded failures remain until a new owner refresh. |
| TCS | No saved source errors; model names absent in this snapshot | Unknown model metadata is labelled correctly. Partial evidence is still partial. |

Suzlon's official financial-reports origin was checked against its issuer investor page: https://www.suzlon.com/investors/financial-reports/ . Only that exact reviewed hostname was added. HTTPS, port, credentials, spoofed-host, local-address and cross-host redirect restrictions remain; TLS was not weakened. The new unit tests verify acceptance of the reviewed origin and rejection of unsafe/lookalike URLs. A new live PDF download or model run was not performed.

Opening telemetry makes no provider/model request. Old failure records are not rewritten to make a snapshot look healthy. In an owner session, use an explicit Refresh sources for the affected company after resolving the actual provider condition. Model preflight and source discovery can consume API quota; neither is needed to review these UI changes.

## Verification and limits

- Backend: **356 tests passed**, including the new reviewed-host and URL restriction cases. One test-client deprecation warning remains; it is unrelated to the recorded research gaps.
- Frontend: **60 checks passed**, including plot direction/flat geometry, native scrubbing, dialog visible-viewport behavior, modal toast placement, replacement/dismissal, focus restoration, diagnostic grouping and raw-text rendering. Synthetic unit fixtures are not app data.
- TypeScript and production build passed. Logs are included.
- Captured-public-source API replay: 14 JSON routes, saved PDF byte integrity and read-only job enforcement passed. No upstream or model execution was used.
- Chromium production QA checked green/red shading, saved-session keyboard interaction, a 390px Universe layout, and the shared settings frame in a 390×520 viewport. Settled dialog bounds were top 12px / bottom 508px in the 520px viewport; Done remained inside that frame and the body scrolled independently. Reset confirmation produced a visible toast within the open native dialog. INFY's four saved gaps appeared as two groups while preserving all four originals. Screenshots show the labelled captured replay.

Screenshots and current logs accompany the package. The installer is checked against the original and five earlier update baselines, preserves private/unrelated files, and refuses unknown local edits before writing.

Physical phone/Safari, real soft-keyboard and screen-reader checks remain. Browser support and device blur performance vary. Live provider/model acceptance is not re-certified; the earlier 52/58 acceptance result is still unresolved. Provider quota, source availability, certificate issues and missing evidence require local diagnosis, not a frontend cosmetic change. Existing licensing, deployment and submission gates remain as described in the pre-final reports.
