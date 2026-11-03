> Historical checkpoint. Current status: [final pack status](../../final-pack-status.md). Current setup: [final pack setup](../../final-pack-setup.md).

# Day 4 functional frontend handoff — 31 October 2026

The reviewed master plan remains authoritative. This update implements the mobile interaction foundation while the user's Day 3 live-data verification runs separately. It does not sign off Day 3, deploy the application, or complete the user's final visual design.

## Implemented

- Two keyboard-accessible, thumb-reachable Inbox and Research tabs. Switching tabs preserves each workspace's state. Mobile safe areas, 44px primary controls, 16px text entry and contained financial-table scrolling are supported.
- Exact 24-hour Inbox default and explicit latest-session/3d/7d/30d controls. A native modal sheet contains price/volume sliders, precise number inputs and all 17 category watches. Applying settings reloads saved data; it does not refresh exchanges or create notification subscriptions.
- Existing scanned/surfaced/buried telemetry, routine drawer, results tables, issuer profiles, source refresh failures and noncausal EOD alerts remain visible.
- Company-name/symbol suggestions from the saved NSE security master, keyboard selection and the five actual showcase symbols. Suggestions are substring matching provided by the API, not typo-tolerant fuzzy search. Exact-symbol entry remains available if the security master is unavailable.
- Four research panels: Say–Do and forward guidance; snapshot and trajectory; cash and balance sheet; evidence for growth and caution. Panels display only backend-supported figures and evidence. Missing data and review states remain explicit. The UI does not derive new financial metrics or generate sparklines from incomplete data.
- Shared native evidence bottom sheet for Inbox and Research. It shows the exact supplied source excerpt, page, observation time when present, saved PDF, original HTTPS link and document hash. Image transcriptions retain a visual-review warning. React escapes source text. Missing/invalid hashes do not produce saved-PDF links. This highlights the supplied excerpt in the sheet, not text inside an external PDF viewer.
- Sequential, cancellable Pull job polling is preserved. Additional request/response guards protect company search, initial research reads, Inbox loads and source inspection against late responses.
- PWA manifest, PNG icons, Apple metadata, install prompt when supported, online/offline status and a static offline fallback. The service worker never caches API responses, financial research, downloaded evidence or private keys. It runs only in production and needs HTTPS or localhost. Full offline research is not included.
- Source inspection is available in a secondary disclosure instead of occupying the main product screen.

## Verification

Production build, TypeScript, existing Pull race tests, new interaction checks and service-worker checks are recorded in verification/day4. Interaction tests use React/jsdom with mocked transport and a real TCS source fixture; they are mechanical checks, not live-data or semantic certification. The production HTML/assets are checked separately if recorded in production-http.json.

Native dialog modality, focus restoration, phone overflow, real installation and offline navigation still need real-browser/phone verification. A Chromium download in this environment failed because the browser archive was truncated; no browser or screenshot pass is claimed. iOS Safari/Android Chrome and hosted HTTPS checks remain open.

The user's local report confirms 305 backend tests and a live gemini-3.5-flash-lite preflight. The full Day 3 acceptance result has not yet been received. No backend source, scripts, database, private .env or model configuration is changed by this update.

## Apply and run

Let the current Day 3 verification finish before applying this update, so its build and source results refer to one version. Keep its report ZIP.

From the extracted update folder:

```powershell
python apply_update.py --project "X:\finn_day1_verification_kit\finn"
```

The installer checks all baselines before writing, backs up changed files and stops on unknown local edits. It only updates frontend source/tests, these docs and recorded validation. It does not require deleting node_modules or creating another database.

From the project root, open the backend in one PowerShell window, after verification has finished:

```powershell
$env:PYTHONUTF8 = "1"
.\.venv\Scripts\python.exe -m finn.dev --db data/finn.sqlite3 --use-model
```

Keep both model settings on the working gemini-3.5-flash-lite in the private root .env. Starting the worker makes explicit research jobs able to call that model; saved read endpoints do not call it.

In another PowerShell window:

```powershell
npm --prefix frontend run typecheck
npm --prefix frontend run test:day4
npm --prefix frontend run test:pull-races
npm --prefix frontend run build -- --webpack
npm --prefix frontend run start
```

Open http://localhost:3000. No new npm dependency is introduced. In development use npm --prefix frontend run dev; the service worker is intentionally not registered in development.

## Short manual acceptance check

1. Select each tab using touch and arrow keys. Confirm the previous search/digest survives tab switching.
2. Load 24 hours, then explicitly choose a wider window. Check source range/as-of and scanned = surfaced + buried. Open routine filings.
3. Change alert settings, apply and confirm displayed filters. Select a company suggestion using keyboard, then a showcase button. Check missing-source and invalid-symbol states.
4. Open an Inbox result and Say–Do citation. Check the exact quote, page and original PDF, then close using Escape/Close. Confirm focus returns to the citation button and the page cannot be operated behind the open modal.
5. At 320/375/390/768px and with enlarged text, confirm the page does not scroll sideways and results tables scroll inside their own region. Check a bank displays no invented industrial EBITDA/cash judgments.
6. In a production browser over localhost/HTTPS, load once, then switch offline and reload. Confirm the offline page explains that research is not stored offline. Reconnect and retry.

For phone testing on a trusted local Wi-Fi network, the phone cannot use the laptop's localhost. Configure frontend/.env.local NEXT_PUBLIC_API_BASE with the laptop's LAN address, set backend FINN_ALLOWED_ORIGINS to the corresponding frontend origin, and start finn.dev with --host 0.0.0.0. Restart/rebuild after changing the public API base. Plain LAN HTTP is useful for layout testing but does not certify PWA installation; use hosted HTTPS in Day 5. Do not expose the unauthenticated development server to the public internet.

## Remaining scope

The user will finish visual styling. Real phone/browser acceptance, deployment/HTTPS and final submission remain open. Audio briefing, scoped copilot, QR handoff, typo-tolerant search, new charting and deeper governance are not implemented or represented as completed. The reviewed plan identifies audio/copilot/QR/deeper governance as stretch work after core gates. Final AI history must use actual conversation exports; this engineering note is not that export.
