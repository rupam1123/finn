> Historical checkpoint. Current status: [final pack status](../../final-pack-status.md). Current setup: [final pack setup](../../final-pack-setup.md).

# FINN — compact glass and motion update

This appearance update supersedes the earlier grey/white-only design direction. It retains the restructured routes, existing FINN mark/navigation icons, primary evidence controls and backend data contracts.

## What changed

- **Removed the three boxes below Signal Inbox.** A single compact strip now shows surfaced versus scanned filings, explicitly includes review items, and provides a small routine-audit button. No separate oversized statistic tiles remain in this view.
- Compact filing tiles use subtle category-tinted gradients, narrow accent edges, inset highlights and restrained shadows. Titles/reasons have concise previews; full content remains in the inspector. Multiple executive changes get one preview and an explicit remaining-count link/context.
- The top sun/moon button switches light/dark appearance and saves only the preference in this browser. Initial appearance follows the system when no explicit preference exists. Resetting FINN preferences restores system appearance. The privacy notice includes this preference.
- Blue-tinted translucent headers, context panels, menus, dialogs and a compact dark glass dock. Blur is limited to overlapping surfaces, avoiding a backdrop filter on every financial tile.
- Visible page/ribbon/table/menu scrollbars are hidden while normal scrolling and focusable financial table regions remain. High-contrast mode restores standard scrollbar treatment.
- Native select menus gain rounded tinted pickers, active checkmarks, hover states and short entrance transitions where the browser supports customizable selects. Other browsers retain usable native menus. Company search has a clearer ticker/name/saved-state layout and first Arrow-Up selection was corrected.
- Route transitions, selected navigation feedback, chart entrances and an original animated document stack on the research launch panel. Entrances settle within roughly one second; there is no endless autoplay, scroll hijacking, new animation dependency or remote animation asset. Numbers and stored financial facts are not tweened. Decorative document graphics are hidden from assistive technology.
- Reduced-motion and reduced-transparency preferences, native keyboard/select behavior, focus styling and contrast-specific dark chart colours are retained. Chart observers cancel/disconnect on cleanup.

## References reviewed

The Behance Subly reference supplied by the user was viewable in Chromium:
https://www.behance.net/gallery/254942367/Subly-AI-Subscription-Fintech-Mobile-App-UIUX/modules/1484161505

The Scrolltide Bean Bag Nap public preview was inspected:
https://www.scrolltide.co/#s-bean-bag-nap

The implementation uses original CSS, SVG and existing licensed icons. No template, paid prompt, video, 3D character or proprietary source asset was copied into FINN. The references inform visual depth and motion pacing; FINN retains its financial research workflows.

## Validation

- **40 frontend checks passed:** existing Inbox/navigation, races, privacy, financial/market visuals, service-worker and cache checks; plus 8 theme/preference/motion cleanup checks.
- TypeScript and production build passed with all existing routes.
- Chromium review exercised both themes, persistence on reload, cross-document preference synchronization, compact mobile tiles/dock, the native glass menu, financial chart/table rendering and the research motion panel.
- At the 390px narrow viewport, document width equalled viewport width; hidden ribbon scrollbars retained `overflow-x:auto` and scrollable content.
- Backend code is unchanged from version 3. Its 348-test result and captured-source API checks are retained as the previous backend checkpoint, not a newly performed live/model run.
- Package checks cover original, older pre-final and versions 2/3, preserving sentinel environment/database files and refusing unknown local edits before any write.

## Review locally

Apply with the included conflict-safe installer (`--check`, then `--apply`), rebuild the frontend and restart FINN. Keep `.env` and all SQLite files. See `frontend-restructure-setup.md` for the existing Windows commands. Use the top appearance icon; inspect Inbox, company Forensics and the Research launchpad in both modes.

A screenshot cannot demonstrate animation timing. Browser-specific native picker/PDF behavior and physical-phone/Safari accessibility remain final local review items. Existing provider/source coverage, model quota, live acceptance and deployment/licensing limitations are unchanged; the prior 52/58 live/model result is not recertified by this visual update.
