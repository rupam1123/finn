# FINN release review — 1 November 2026

This is a scoped engineering and public-source review of the existing assessment prototype, not a legal opinion, accessibility certification or financial-data accuracy certification. No deployment or source-license decision was made. The user's newer visual reference was applied during this review: compact DM Sans typography, soft grey canvas, white cards and light glass navigation. Existing icon vectors are unchanged.

## Changes and scope

| Area | Applied measures |
|---|---|
| Financial presentation | Always-available research notice; assessment watchlist distinguished from actual investments/recommended allocation; no personalised advice or guaranteed-return claim; review-priority score distinguished from investment rating. AI-assisted classifications and analyses remain labelled. A citation/hash is not described as an independent audit. |
| Source attribution and freshness | Yahoo Finance/yfinance named beside saved market observations; primary URLs, pages, hashes, publication and observation times retained; Screener remains staging. Individual session dates and freshness state remain visible. Indian sessions and observation timestamps now use explicit IST, including the year, independent of visitor timezone. The display-details toggle no longer hides the filing-window cutoff. |
| Privacy | Added a linked factual data-flow notice. No login, account, ads, browser analytics or application cookies. FINN local-storage preferences/bookmark IDs can be reset without touching other site data or SQLite. Source-detail telemetry is explicitly a display setting. Next CLI usage telemetry and launcher URL access logs are disabled. Hosting/tunnel logs and provider processing are disclosed without unsupported zero-logging/retention promises. |
| Public operation | `--public-review` / `FINN_PUBLIC_REVIEW=1` prevents new research-job POSTs server-side and starts no worker. UI reflects this capability and keeps saved-data browsing. Local owner mode retains discovery/refresh. Cross-site/unconfigured-origin POSTs are rejected; wildcard CORS is not accepted. These checks are not authentication. |
| Abuse and errors | HTTP queue capped at six active jobs, 12 new jobs per hour and 48 per rolling day, atomically in SQLite; existing active jobs deduplicate without spending budget. Counts are global, with timestamps only and no IP/visitor IDs. Old budget timestamps are pruned at startup and accepted queue activity. Generic worker errors avoid publishing exception paths/secrets. Owner CLI runs are outside the HTTP queue budget. |
| Browser security | nosniff, no-referrer, SAMEORIGIN framing, capability restrictions and a same-origin CSP with bounded PDF/blob support. API JSON is no-store; existing hash-verified PDF semantics remain intact. CSV cells neutralise spreadsheet formulas including whitespace/control prefixes. React escaping and safe HTTPS source links are retained. |
| Licenses | Public third-party notices and pinned dependency inventory; existing OFL/ISC font/icon notices retained; PyMuPDF COPYING added. No proprietary reference-font/photo asset or third-party logo is introduced. This does not grant financial-data redistribution rights or license the user's application code. |
| Accessibility | Stronger text contrast, labelled/focusable wide tables and header scopes, native modal focus return, route title/main-focus updates, combobox Escape behaviour, visible input focus, reduced motion and non-colour state indicators. Explicit limitations are published. No claim of complete WCAG conformance. |
| Responsiveness and latency | Visited research/portfolio workspaces stay mounted; memoised views and compact charts avoid unrelated re-renders. The overview API uses one DB connection and skips decoding large Pull results. Per-card blur/entrance animations removed; restrained glass stays on navigation/sheets. |

## Applicability decisions

Financial research in India may bring SEBI Research Analyst requirements into scope depending on actual operation, audience and content. Calling something a prototype or adding a disclaimer does not settle that question. No SEBI number, registration status, client agreement, investor charter, complaints statistics or regulatory seal was invented. Registration/conflict-of-interest obligations must be resolved for the real operator before public research publication.

India's DPDP commencement notification stages provisions over time. As of this review date the main 18-month tranche has not yet commenced. This build is deliberately data-minimal, but is not labelled DPDP/GDPR-compliant. The actual operator, hosting arrangement, source-personal-data processing and intended audience still matter. Cookie-consent tooling, identity verification, subscription, payment, signup and account deletion flows were not added because this app has none of those product functions.

Gemini inputs are selected public issuer text/page images, not visitor bookmarks or private account documents. Public filings can still contain names and contact details. The operator must check model-provider terms and permitted input processing, including unpaid versus paid treatment and audience/region requirements. Public review runs no model jobs. No confidential user input is needed or requested.

## Verification

- 340 backend tests, including public read-only enforcement, cross-site/CORS checks, concurrent queue caps, budget expiry, generic failure output and single-connection saved-only overview.
- Existing eight frontend behaviour groups, four service-worker checks, three Pull race checks and six market-visual checks. New safeguard checks cover timezone-stable dates, CSV neutralisation, scoped local reset, cached navigation/focus/title, public read-only controls and security headers. TypeScript and production build include `/about` plus every existing route.
- `npm audit --omit=dev` reports zero known vulnerabilities. `pip-audit` against all 50 pinned Python requirements reports zero known vulnerabilities and no skipped requirements. These checks are time-bound advisory-database checks, not a penetration test or a guarantee of absence of vulnerabilities.
- Same captured-source SQLite replay, 20 warm local calls per version: portfolio overview median **51.89 ms before / 3.98 ms after**. This measures the direct API handler, not a Windows/Cloudflare/phone latency guarantee. React tests verify no additional research GET when returning to a visited workspace.
- Chromium review uses actual FastAPI + public captured sources with a visible replay banner. It verifies original source/evidence actions, public-mode controls, browser preference reset, linked privacy/license information, routing, responsive rendering and contrast of inspected text. The screenshot replay is not shipped as financial/demo data. Physical phones, assistive technology and browser-specific PDF behaviour remain review items.

## Blockers and residual risks before public deployment

1. **Data rights:** Screener's published terms restrict public display/copying, and yfinance's documentation distinguishes its open-source code from Yahoo data rights/personal-use limitations. Obtain necessary permission or replace affected data with an authorised source. Check NSE/BSE/issuer document storage, quotation and redistribution permissions too, including the real primary-document regression fixtures before publishing the repository. Their fixture NOTICE preserves this distinction. A public tunnel is still public display; read-only mode does not resolve licensing.
2. **PyMuPDF/MuPDF:** resolve AGPL-compatible complete-source/distribution obligations or an appropriate commercial license. A patch ZIP, copyright notice, or unrelated open-source dependency license is not an automatic resolution. FINN's source license and a real source-offer URL must be decided by its owner; none was fabricated.
3. **Research regulation:** confirm whether this operator's public securities analysis and any financial interests require SEBI registration/disclosures or an applicable exemption. The software does not establish those legal facts.
4. **Hosting/privacy:** publish a real operator contact, confirm hosting/provider log retention and access, keep keys/SQLite off the public filesystem, use HTTPS and configure edge request-rate/size controls. Public review must be read-only; local origin validation is not a login or server authentication. If private investor data is introduced later, a separate privacy/security design is needed.
5. **Extraction acceptance:** the last user-supplied live run was 52/58, with unresolved Day 2 enrichment and Day 3 comparison/profile consistency outcomes. These were not reclassified as passing by this review. Verify issuer identity/accounting basis and affected cash-analysis snapshots before financial reliance.
6. **Testing boundary:** no full WCAG conformance claim, legal compliance guarantee, external penetration test, paid-model acceptance rerun, physical Android/iOS or live user-DB performance claim is made. The static Next CSP still permits framework inline scripts; moving to a nonce/hash-only policy would require a separate rendering/security design. Native third-party PDFs may lack accessible text structure.

## Local and shared review

Apply the safe cumulative updater with FINN processes stopped. Keep the existing `.env`, SQLite cache and verification files. Install frontend dependencies with `npm ci` and rebuild.

For a shared review, from the FINN project root:

```powershell
.\.venv\Scripts\python.exe scripts\run_local.py --build --production --public-review --db data\finn.sqlite3
```

Do not add `--use-model` in this mode. The app can browse existing saved evidence; discovery/refresh is disabled. Use the local owner session, with the tunnel stopped, for authorised model/source work. Confirm data/software/regulatory rights before public publication. See `day4-local-review.md` for normal local setup.

## Sources checked

- SEBI RA FAQs, registration, public-media and disclosure scope: https://www.sebi.gov.in/sebi_data/faqfiles/jul-2025/1753269723942.pdf
- SEBI RA regulations, November 2025 amendment listing: https://www.sebi.gov.in/legal/regulations/nov-2025/securities-and-exchange-board-of-india-research-analysts-regulations-2014-last-amended-on-november-25-2025-_98248.html
- MeitY DPDP commencement notification G.S.R. 843(E): https://www.meity.gov.in/static/uploads/2025/11/c56ceae6c383460ca69577428d36828b.pdf
- W3C WCAG 2.2: https://www.w3.org/TR/WCAG22/
- Screener terms: https://www.screener.in/guides/terms/
- yfinance documentation/data-rights notice: https://ranaroussi.github.io/yfinance/
- PyMuPDF licensing and installed 1.28.2 COPYING: https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright
- Gemini API terms: https://ai.google.dev/gemini-api/terms
