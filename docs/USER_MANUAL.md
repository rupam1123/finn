# FINN user manual

## Start here

Open `/` for the FINN welcome page. Use the sun/moon control to choose light or dark. **Open workspace** goes to Inbox; **Explore company research** opens company search. No login or signup is required in the local assessment app. Hosted access is controlled separately by the hosting platform.

Use the **Home** icon beside Workspace settings to return to the welcome page. In Research, the company ribbon and company header shrink as you scroll, keeping tickers, saved prices and research tabs in reach. Scroll to the top to restore the full details.

## Page-by-page controls

| Page | What to do | What to check |
| --- | --- | --- |
| Inbox | Choose 24 hours, 3/7/30 days or Latest session. Open a filing. Expand find/filter/sort; bookmark or export filtered CSV. | Selected window and saved filing-check dates differ. Routine filings and all 17 categories remain inspectable. A priority score is review priority. |
| Radar | Set price move and volume multiple, then choose a time window. Use Reload Radar to read the saved data again or Inspect timeline to open an alert. | Returns use adjusted EOD prices; volume is raw shares against the prior 20 sessions. Known-at-cutoff and later filings differ. Timing is not causation. |
| Research | Search a company name or NSE ticker, or swipe the centred watchlist picker and choose Research for the selected company. | ZOMATO resolves to ETERNAL. Historical TATAMOTORS requires choosing TMPV or TMCV; histories are not spliced. |
| Company Overview | Explore business/market context, open Ask FINN, or use the Say–Do, Forensics and Vault tabs. | Saved source dates and incomplete states. The price is a saved close. |
| Say–Do audit | Expand a compact quarter row, then open management commentary or delivered-period evidence. The period and evidence status remain visible while closed. | Source coverage and matched numerical comparisons have separate counts. Missing, qualitative and not-comparable records are not beat/miss verdicts. |
| Financials | Expand a statement to inspect tables/charts. Explore annual cash/debt and governance evidence. | Period, units, currency and consolidated/standalone basis. Lender schemas differ from industrial companies. Visual-review flags remain explicit. |
| Sources | Filter documents and open View saved PDF or Open original. | Page, quotation, observed time, URL and document hash. A PDF iframe may be blank in some browsers; use the saved/original link. |
| Universe | Pick one of the 18 assessment companies. Search, sort or switch to table view. Expand Market overview if needed. | Chart colour compares plotted endpoints; the 1D badge describes one session. These can differ. |
| Source health | Inspect retained source coverage and failures. | This is saved status, not a new connection test. |
| Settings / About | Change appearance, display technical details or reset FINN bookmarks/preferences. | Reset affects this browser's FINN settings; it does not delete server data. |

## Ask FINN

1. Open a company and choose the green **Ask FINN** button.
2. Choose Overview, Promises, Cash & debt or Watch points; or enter a short question.
3. The **saved-source guide** returns relevant, shortened primary excerpts. Open a citation for the complete quote/page. This mode makes no model call and does not invent an answer when no passage matches.
4. In an explicitly model-enabled owner session, **Summarise with AI** requests up to three cited draft points. It may consume the configured provider's quota. Questions and answers are not persisted by FINN; explicit AI requests send the question and selected excerpts to the configured provider.

Public review and the hosted saved-data port keep new generation disabled. A source match or numeric-support check does not prove semantic correctness; verify the original passage.

## Touch and keyboard

- Tap a destination in the flat bottom bar. Search is at the right of the same bar.
- Use ordinary taps/clicks for filters and actions. The rolling company picker retains its own native scrolling and mouse dragging.
- Use Tab/Shift+Tab, Enter/Space and Escape. Dialogs retain focus and restore it on close. Charts have native saved-session controls and text tables.
- The Research watchlist picker supports native horizontal swiping, mouse dragging and Left/Right/Home/End keys. Only the selected card is in the Tab sequence; the explicit Research action opens its page. All 18 companies remain available.
- Long tables scroll horizontally. Reduced-motion preferences suppress decorative animation.

## Install and run

Use Python 3.12 and the tested Node 24 family. From a clone of the GitHub repository:

```powershell
git clone --recurse-submodules https://github.com/rupam1123/finn.git
cd finn
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e backend
npm --prefix frontend ci
```

Keep an existing private `.env` and SQLite database. A fresh clone deliberately includes neither. If configuration is absent, use `.env.example` as a template without overwriting existing settings. Never put keys in `NEXT_PUBLIC_*` or Git.

With saved data:

```powershell
.\.venv\Scripts\python.exe scripts\run_local.py --build --production --public-review --db data\finn.sqlite3
```

Visit http://localhost:3000. Keep the terminal running; Ctrl+C stops the local session. Ports 3000 and 8000 must be free. Public review starts no research worker and rejects research/AI generation POSTs.

### If starting without saved data

The app can show empty states; it cannot recreate the operator's saved research from Git. Deliberate source ingestion makes network requests and can encounter provider failures:

```powershell
.\.venv\Scripts\python.exe -m finn.cli --portfolio --db data\finn.sqlite3
.\.venv\Scripts\python.exe -m finn.push_ingest --days 30 --db data\finn.sqlite3
```

Then run the launcher without `--public-review` for an owner session and explicitly choose Discover primary sources / Refresh sources in a company workspace. The durable worker handles the queued job. Do not run a second worker against the same database. No model executes unless explicitly enabled.

For owner AI, configure the accessible model IDs/key locally, stop the review session, and launch with `--use-model` instead of `--public-review`. Provider access/quota is required; a configured model name is not a successful generation result. The assistant request budget is six per hour and 24 per day. Do not enable model use simply to browse saved research.

## Common questions

| Symptom | Action |
| --- | --- |
| Empty 24-hour view | Check the saved coverage date shown in the notice. **View saved 7 days** explicitly widens the window. Reload rereads saved data; it does not fetch exchange filings. Empty coverage is not proof that no disclosure exists. |
| No research / unavailable statement | Inspect Sources and retained gaps. In an owner session, explicitly queue discovery. Missing primary evidence remains a gap. |
| AI summary button absent | Expected in read-only mode or when model execution/key is not enabled. Use the saved-source guide. |
| PDF preview blank | Use Saved PDF or Original source. Keep the quotation/page controls as an alternative. |
| Service unavailable | Confirm the launcher and API are running; inspect the terminal. Do not reset/delete the database. |
| Port already in use | Stop the previous FINN session before restarting; do not launch duplicate workers. |
| Old hosted UI | GitHub source updates and deployment are separate. Deploy the tested Sites version from the owning account. Automatic publication remains paused. |

## Validation and release

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
npm --prefix frontend run test:workspace
npm --prefix frontend run test:touch
npm --prefix frontend run test:assistant
npm --prefix frontend run test:welcome
npm --prefix frontend run test:details
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

See [release readiness](release-readiness-2026-11-04.md). Tests and builds do not certify every financial interpretation, licensing choice or physical device. Actual AI chat/build-history export remains a separate submission artifact.

Typography follows the verified Swiftz SF Pro Display roles and spacing. Devices with the local Apple font use it; this Windows installation uses bundled DM Sans. No proprietary Apple font file is distributed. See [final UI checks](brand-detail-polish-2026-11-04.md).
