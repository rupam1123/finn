# FINN: Multi-Route Mobile-First Frontend Architecture & Micro-Interaction Blueprint

**Design Philosophy:** Zero AI Slop · Progressive Disclosure · Thumb-Zone Ergonomics · Instant Byte-Level Provenance

**Target Viewport:** Mobile-First (`390px–430px` primary frame, expanding cleanly on desktop with a live mobile QR companion)

## 1. Core UX Paradigm: Calm Default & Progressive Expansion

Most financial apps fail on mobile because they dump 50 tables, unparsed JSON, or giant search dropdowns onto the screen at load time. FINN uses **Calm Default & Progressive Micro-States**:

### 1.1 The Morphing Top Search & Action Bar

* **Default State (Idle / Calm):**

  * At the top of the screen (`48px` height), the header is ultra-clean:

    * **Left:** Minimal `FINN` monogram + a 6px live status dot (`🟢 EOD Synced`)

    * **Right:** A compact, pill-shaped **Search Trigger Button** (`🔍 Search 2,364 NSE Tickers` or `⌘K`) styled with a subtle glassmorphic border (`border-zinc-800 bg-zinc-900/80`).

  * **Crucial Rule:** By default, **zero search dropdowns or noisy lists are rendered**.

* **Active State (When User Taps Search):**

  * The Search Trigger Button **minimizes and morphs** into a sleek `[ESC / ✕]` icon pill on the right while the input bar smoothly expands across the header (`transition-all duration-200 ease-out`).

  * **While Input is Empty (`""`):** Nothing bulky appears—only a tiny 1-line hint pill: *"Type any NSE symbol (e.g., INFY, TITAN, ZOMATO → ETERNAL)..."*

  * **As Soon as 1+ Characters Are Typed:**

    * An instant, floating glassmorphic **Search Results Sheet** materializes directly below the input (`max-h-[280px] overflow-y-auto`):

      * Each row is `44px` tall (ideal tap target): **`[TICKER]`** (monospace bold) · **Company Name** (truncated) · **Sector Tag** (`IT` / `BANK` / `IND`) · **Status Dot** (`⚡ Warm` for pre-cached or `🌐 Live Pull` for unseen NSE tickers).

      * **Smart Alias Micro-Chip:** If the user types `ZOMATO`, a sleek amber micro-chip appears inline: `Legacy Alias → Tap to open ETERNAL`. If they type `TATAMOTORS`, two split micro-buttons appear inline: `[🚗 TMPV (Passenger)]` | `[🚛 TMCV (Commercial)]`.

  * **On Selection (Tap):**

    * The search bar immediately collapses back to its minimized pill state, and the user is routed directly to `/research/[ticker]` (Company Landing Terminal).

### 1.2 The Minimal Horizontal Portfolio Ribbon (Top of Main Body)

Right below the top header—occupying **only `68px` of vertical height**—sits a **Horizontal Snap-Scroll Company Ribbon** (`overflow-x-auto snap-x no-scrollbar flex gap-2 px-3 py-1.5`):

* **Why It Works:** It takes almost zero vertical space, gives immediate situational awareness across all 18 portfolio companies, and acts as a 1-tap teleporter into any company's dedicated workspace.

* **Micro-Card Anatomy (`132px` wide × `56px` tall per chip):**

  ```
  ┌──────────────────────────┐
  │ INFY          ▲ +1.42%   │ ← Row 1: Monospace Ticker (12px bold) + Color-Coded 1D Return
  │ ₹1,842 · Vol 1.8x · 2📄 │ ← Row 2: Close Price · 20D Vol Ratio · Unread Material Filings Badge
  └──────────────────────────┘
  
  ```

* **Minute Visual Details on Each Ribbon Chip:**

  * **Left Border Accent (`2px`):**

    * `Emerald-500`: Material positive results or beat in window.

    * `Amber-500`: Material filing or volume anomaly (`>2.0x`) in last 48h.

    * `Zinc-700`: Quiet / routine session (all noise buried).

  * **Tap Interaction:** Tapping any chip (`TCS`, `DEEPAKNTR`, `HDFCBANK`, `POLYCAB`, etc.) triggers a tactile scale-down (`active:scale-95`) and lands the user directly on **`/research/[ticker]`** (that company's dedicated multi-tab page).

## 2. Multi-Page Nested Route Architecture (No Single-Page Scroll Fatigue)

Instead of a single endless page, FINN is organized into **4 Primary Routes** (accessible via a `56px` thumb-zone Bottom Navigation Bar) and **7 Nested Drill-Down Pages**:

```
/ (Root) ──► Redirects to /inbox
│
├── /inbox                                 [TAB 1: PUSH — SIGNAL INBOX]
│   └── /inbox/[filingId]                  [NESTED: Filing Deep-Dive & QoQ/YoY Table]
│
├── /radar                                 [TAB 2: PUSH — ANOMALY RADAR]
│   └── /radar/[alertId]                   [NESTED: ±48h Coincident Timeline & OHLCV]
│
├── /research                              [TAB 3: PULL — FORENSIC LAUNCHPAD]
│   └── /research/[ticker]                 [NESTED LEVEL 1: Company Hub & Snapshot]
│       ├── /research/[ticker]/say-do      [NESTED LEVEL 2: ★ 4-Quarter Say-Do Matrix]
│       ├── /research/[ticker]/forensics   [NESTED LEVEL 2: Cash (CFO/PAT), Debt & RPTs]
│       └── /research/[ticker]/filings     [NESTED LEVEL 2: Company-Specific Push Feed & Vault]
│
└── /universe                              [TAB 4: PORTFOLIO MATRIX & ENGINE TELEMETRY]

```

* **Global Bottom Sheet Drawer (`?cite={sha256}&page={n}&q={quote}`):**

  * Lives at the root `layout.tsx` level. Tapping **any** citation pill (`[p.29 · Q1 Transcript]`) on **any** page smoothly slides up a native-feeling bottom sheet displaying the verbatim quote, the SHA-256 cryptographic fingerprint, and the embedded `/api/evidence/{sha256}.pdf#page={n}` document viewer without losing the user's scroll position.

## 3. Page-by-Page Structural Blueprint & Saliency Features

### PAGE 1: `/inbox` — The Proactive Signal Inbox (Default Landing)

**Goal:** Prove in 3 seconds that FINN surfaces the 3–5 filings that move capital and buries the 40+ routine compliance notices.

1. **Top Strip: The Minimal Portfolio Ribbon (`68px` height)**

   * Horizontal scroll of the 18 portfolio stocks with live 1D return %, volume multiple, and filing dot.

2. **Saliency Telemetry Bar (`44px` compact Bento bar)**

   * **Left:** Segmented Window Pill: **`24H`** (default) | `3D` | `7D` | `30D`.

     * *Smart Quiet-Day Pill:* If `24H` has `0` surfaced filings (e.g., Sunday/holiday), a compact 1-line amber pill appears: `0 Filings in 24H (Weekend) · [Tap for 7D Active Feed (48) →]`.

   * **Right:** **Signal-to-Noise Mini Meter:** Visual 3-segment micro-bar showing `12 Surfaced` vs `212 Buried (94% Noise Removed)`.

3. **Horizontal Category Filter Pills (`36px` height)**

   * `All Material` · `📊 Results` · `👔 Mgmt Change` · `🤝 M&A / Orders` · `⚖️ Auditor / Legal` · `🏗️ Capex`

4. **Main Feed: High-Density Signal Tiles (Max 3 data points per card before tap)**

   * **Card Type A — Quarterly Results Tile (`TCS`, `POLYCAB`):**

     * **Top Row:** Ticker Pill (`TCS`) + Category Tag (`FINANCIAL RESULTS`) + Basis Pill (`Consolidated · ₹ Cr`) + Time (`14m ago`).

     * **Center Visual (Inline Micro-Grid):**

       | Metric | Reported (`Q2`) | QoQ $\Delta$ | YoY $\Delta$ | 
       | ----- | ----- | ----- | ----- | 
       | **Revenue** | `₹64,259 Cr` | `🟢 +2.6%` | `🟢 +7.8%` | 
       | **PBT** | `₹16,032 Cr` | `🔴 -1.1%` | `🟢 +5.4%` | 
       | **PAT** | `₹11,909 Cr` | `🔴 -1.1%` | `🟢 +5.0%` | 

     * **Bottom Action Bar:** `[Open Full Reconciliation →]` (routes to `/inbox/[filingId]`) · `[📄 PDF p.8]`.

   * **Card Type B — Executive Change Tile (`BAJFINANCE`, `TRENT`, `PERSISTENT`):**

     * **Top Row:** Ticker + Action Pill (`APPOINTMENT` in Emerald / `RESIGNATION` in Rose) + Effective Date.

     * **Center:** Executive Name + Role (`Harish Bhat · Non-Executive Director`) + 1-line statutory summary preview.

     * **Bottom Action Bar:** `[Read Statutory Dossier →]` (routes to `/inbox/[filingId]`) · `[📄 PDF p.2]`.

5. **Bottom Vault: The "Buried Routine Noise" Pill (`40px` collapsed bar)**

   * Sits quietly at the bottom of the feed:
     `🛡️ 203 Routine Filings Auto-Buried (Reg 74(5), Trading Window, ESOPs) — [Tap to Audit]`

   * Tapping opens a clean modal/accordion showing *why* each routine filing was buried (deterministic rule match + PDF link).

#### Nested Page 1.1: `/inbox/[filingId]` (Dedicated Filing Inspector)

* **Header:** `← Back to Inbox` · Ticker Badge (`TCS`) · `SHA-256 Verified`.

* **Visual Chart:** **3-Quarter Grouped SVG Bar Chart** comparing `Current Quarter`, `Previous Quarter`, and `Year-Ago Quarter` across Revenue, PBT, and PAT.

* **Mathematical Audit Box:** Shows `Half-Year (6M) Reconciliation Check` + `Unit Normalization Factor (₹ Lakh → ₹ Cr via Decimal)` so evaluators see zero-hallucination math.

* **Statutory Text & Direct PDF Drawer Trigger.**

### PAGE 2: `/radar` — Configurable Anomaly Radar & $\pm 48\text{h}$ Attribution

**Goal:** Showcase configurable EOD price/volume triggers and our unique **Point-in-Time Temporal Attribution** (distinguishing explained moves from unexplained spikes).

1. **Minimized Threshold Scrubber Bar (Compact 2-Slider Tile)**

   * **Price Move (**$\pm X\%$**):** Compact range slider (`0.5%` – `10%`, currently `3.0%`).

   * **Volume Spike (**$Y\times$ **20D Avg):** Compact range slider (`1.2x` – `5.0x`, currently `2.0x`).

   * Updating either slider smoothly re-filters the anomaly grid in real time via `/api/push/digest?price_threshold_pct=...&volume_ratio_threshold=...`.

2. **2-Tile Attribution Summary Split**

   * **Tile 1 (`🟢 Filing-Coincident Spikes`):** Spikes with an exchange filing observed within $\pm 48\text{h}$ of the 18:00 IST cutoff.

   * **Tile 2 (`🟠 Unexplained Anomalies`):** High-volume/price breakouts with **zero** exchange disclosures in the $\pm 48\text{h}$ window.

3. **Anomaly Bento Cards**

   * Each card displays:

     * **Left:** Ticker + Date + `1D Return Badge` (`+4.8%`) + `Volume Multiple Badge` (`3.4x 20D Avg`).

     * **Right (Inline SVG Spark-Bars):** A 20-bar mini volume histogram where the 19 baseline days are muted zinc and the trigger day is a glowing emerald/rose bar crossing a dashed horizontal threshold line.

     * **Bottom Attribution Strip:** Either links directly to the coincident filing (`🔗 Coincident: Q2 Results Filing (-6.2h)`) or displays `⚪ No Primary Filing in ±48h Window`.

   * Tapping the card routes to **`/radar/[alertId]`**, which renders the full 30-day Price + Volume chart with vertical pins for every NSE filing timestamp (explicitly marking **Contemporaneous** vs. **Retrospective** post-cutoff filings).

### PAGE 3: `/research/[ticker]` — The Company Hub (Landing Page When Any Company Is Clicked)

Whether the user clicks a company chip in the **Top Horizontal Ribbon** or selects a ticker from the **Minimized Search Bar**, they land here.

#### Sticky Company Context Header (`84px` total height)

* **Row 1:** `← Back` · **Ticker & Company Name** (`INFY · Infosys Ltd`) · **Price & 1D** $\Delta$ (`₹1,842.50 ▲ +1.4%`) · **Profile Badge** (`NON-FINANCIAL` or `BANK / LENDER SCHEMA`).

* **Row 2 (4 Nested Sub-Page Navigation Pills):**

  * **`[ ① Overview ]`** (`/research/[ticker]`)

  * **`[ ② Say–Do Audit ★ ]`** (`/research/[ticker]/say-do`)

  * **`[ ③ Forensics ]`** (`/research/[ticker]/forensics`)

  * **`[ ④ Vault (24) ]`** (`/research/[ticker]/filings`)

#### Sub-Page 3.1: `/research/[ticker]` (Overview Bento Grid)

Designed to give a complete, zero-fluff institutional snapshot in 4 clean tiles:

1. **Tile 1: Primary Business & Segment Mix**

   * Concise breakdown of revenue streams, core verticals, and geographic split (e.g., North America `54.6%`, Europe `32.5%`) with 1-tap `[AR p.188]` citation pills.

2. **Tile 2: Sector-Adaptive Financial Snapshot + Trend Visual**

   * **Dynamic Schema Switcher (Our Unique Domain Instinct):**

     * If `profile === "nonfinancial"`: Shows **Revenue, Operating Profit/EBITDA, PBT, PAT, Operating Margin %, EPS**.

     * If `profile === "bank"` (`HDFCBANK`, `ICICIBANK`, `KOTAKBANK`, `SBIN`, `AXISBANK`): Automatically switches to **Interest Earned, Net Interest Income (NII), Total Income, Operating Profit, Provisions, PAT** with an explicit `🏦 Lender Schema Active` badge.

3. **Tile 3: Grounded Bull vs. Bear Tension Matrix (2-Column Split)**

   * **🟢 Bull Case (Primary Evidence):** e.g., *"\$5.2B Large Deal TCV (62% Net New) + 29% QoQ AI growth"* `[Q2 Call p.25]`.

   * **🔴 Bear Case (Primary Evidence):** e.g., *"FY27 CC revenue guidance narrowed to 1%–2% amid discretionary softness & H2 wage hikes"* `[Q2 Call p.6]`.

4. **Tile 4: Quick-Jump Preview to Say–Do & Forensics**

   * Two high-contrast interactive summary banners that lead into Sub-Pages 3.2 and 3.3.

#### Sub-Page 3.2: `/research/[ticker]/say-do` — ★ The Signature 4-Quarter Say–Do Credibility Matrix

This dedicated route is our **#1 competitive differentiator** for the ENAM evaluation.

1. **Visual 1: The 4-Quarter Guidance Evolution & Delivery Chart (Custom Inline SVG)**

   * **Left Chart (Revenue Growth CC %):** Plots the management guidance band across the last 4 quarters (`Q3 FY26: 3.0–3.5%` $\rightarrow$ `Q4 FY26: 1.5–3.5%` $\rightarrow$ `Q1 FY27: 1.5–3.0%` $\rightarrow$ `Q2 FY27: 1.0–2.0%`) as a shaded channel, overlaid with the actual delivered YoY CC growth points (`3.1%`, `2.4%`, `1.5%`).

   * **Right Chart (Operating Margin %):** Plots the `20.0%–22.0%` guided corridor as a horizontal green band with actual delivered quarterly margin dots (`21.2%`, `20.9%`, `21.1%`, `21.0%`) sitting squarely inside the band.

2. **Visual 2: The Credibility Scorecard Strip**

   * `Quarters Audited: 4` · `Margin Guidance Adherence: 4/4 Within 20–22% Band` · `Revenue Guidance Revisions: 2 Downward Narrowings Tracked`.

3. **The 4 Quarter-by-Quarter Accountability Cards (`Q2 FY27`, `Q1 FY27`, `Q4 FY26`, `Q3 FY26`)**

   * Each card is structured as a strict **Left-vs-Right Comparison Tile**:

     * **Left Column (`🗣️ SAID / PROMISED`):**

       * Exact guidance range or qualitative target stated in the prior call + Speaker Role badge (`Salil Parekh, CEO` / `Jayesh Sanghrajka, CFO`) + `[📄 p.4 Quote]`.

     * **Right Column (`📊 DELIVERED / ACTUAL`):**

       * Exact primary reported figure in the target period + `[📄 p.29 Quote]`.

     * **Bottom Verdict Bar:**

       * Color-coded status pill (`✅ DELIVERED IN-BAND`, `⚠️ REVISED DOWNWARD`, or `🛡️ HORIZON CHECK: Annual Guidance vs. Quarterly Run-Rate`) + collapsible **"Management Variance Attribution"** drawer quoting management's exact explanation (e.g., Project Maximus tailwinds vs. EURS client termination).

#### Sub-Page 3.3: `/research/[ticker]/forensics` — Cash Quality, Leverage & Governance

Built specifically to highlight `annual_forensics.py` and `forensic_analyzer.py`:

1. **Visual 1: Accounting PAT vs. Operating Cash Flow (CFO) Dual-Bar SVG Chart**

   * Side-by-side bars for FY25 & FY26 comparing **Net Profit (PAT)** against **Net Cash from Operating Activities (CFO)** in `₹ Crores` (or `$ Millions`).

   * **Cash Conversion Badge:** e.g., `DEEPAKNTR FY26: CFO ₹538.95 Cr / PAT ₹550.66 Cr = 0.98x (98% Conversion) ✅` or `INFY H1 FY27: FCF 113.5% of Net Profit ✅`.

   * **Deterministic Math Proof Pill:** Shows the exact subtotal verification (`Cash Generated from Operations - Income Taxes Paid = Net CFO`).

2. **Visual 2: Balance Sheet Leverage & Identity Gauge**

   * Displays **Non-Current Borrowings + Current Borrowings = Total Debt** vs. **Total Equity** $\rightarrow$ **Debt-to-Equity (**$D/E$**) Ratio** (`0.26x` for Deepak Nitrite; `0.00x Debt-Free (Ex-Lease)` for Infosys).

   * Displays `✅ Accounting Identity Verified: Assets = Equity + Liabilities`.

3. **Governance & Footnote Radar (3 Segmented Sub-Pills)**

   * **`[ Related Party (RPT) ]`** · **`[ Contingent Liabilities ]`** · **`[ Auditor Opinion ]`**

   * Renders extracted primary footnote tables and auditor opinion paragraphs (`Deloitte Haskins & Sells LLP — Unqualified Ind AS 34 Opinion`) with 1-tap page-level PDF verification.

#### Sub-Page 3.4: `/research/[ticker]/filings` — Primary Source Vault & Live Job Runner

1. **Live On-Demand Ingestion Trigger (For Unseen NSE Tickers):**

   * If the user searched an unseen ticker (e.g., `TITAN`, `COFORGE`, `TRENT`), a sleek **"Run Live Primary Pull"** button triggers `POST /api/pull/{ticker}/jobs` and renders a real-time 3-step SSE progress bar (`Discovering Links` $\rightarrow$ `Fetching & SHA-256 Hashing PDFs` $\rightarrow$ `Running Forensic & Say-Do Extractors`).

2. **Cryptographic Primary Document Table:**

   * Lists all primary PDFs indexed for this company (`Transcript`, `Annual Report`, `Quarterly Results`, `Presentation`) with their page count, observation timestamp, short SHA-256 badge (`b8e9a931...`), and direct `[Open PDF]` button.

3. **Epistemic Guardrail Footer:**

   * Explicitly badges that secondary staging (`Screener.in`) is isolated to discovery (`eligible_for_pull_claims: false`).

### PAGE 4: `/universe` — 18-Stock Heatmap & 3-Tier Cost/Model Architecture

**Goal:** Give evaluators a 1-screen overview of the entire 18-stock portfolio and visually prove the **Cost/Efficiency Bonus Criteria**.

1. **18-Stock Interactive Bento Heatmap (3 Columns × 6 Rows on Mobile)**

   * Every stock in the portfolio (`RELIANCE`, `TCS`, `HDFCBANK`, `INFY`, `ICICIBANK`, `LT`, `SUNPHARMA`, `ETERNAL`, `TMPV`, `BAJFINANCE`, `TITAN`, `POLYCAB`, `DIXON`, `TRENT`, `KPIL`, `DEEPAKNTR`, `LAURUSLABS`, `SUZLON`) is rendered as a color-coded heatmap tile showing **Ticker**, **1D %**, **Vol Multiple**, and **Surfaced Signal Count**. Tapping any tile jumps to `/research/[ticker]`.

2. **Visual Diagram: The 3-Tier Smart Model Routing Funnel (Bonus Points Showcase)**

   * A clean SVG flow diagram showing how FINN eliminates token waste:

     * **Tier 0 (`Deterministic Python + PyMuPDF + Decimal` — `₹0 / $0.00`):** Handles 100% of EOD anomaly math, Reg 74(5) noise burial, SHA-256 deduplication, and 6-column/2-column accounting reconciliations.

     * **Tier 1 (`Gemini 2.5 Flash` — Page-Targeted):** Only invoked on candidate pages (`<15%` of total PDF pages) for ambiguous layouts.

     * **Tier 2 (`Say-Do & Forensic Synthesis` — Content-Addressed Cache):** Keyed by `(sha256, extractor_version)` in SQLite so repeated views cost **0 tokens**.

## 4. Micro-Interaction & Visual Polish Checklist (What Makes FINN Stand Out)

| Micro-Detail | How FINN Implements It | Why Evaluators Notice It | 
| ----- | ----- | ----- | 
| **Minimized Morphing Search** | Compact `🔍 Ticker` pill at top-right; expands on tap, shows instant results only when typing, auto-collapses on selection. | Keeps the top viewport 100% clutter-free by default. | 
| **68px Portfolio Ribbon** | Ultra-compact horizontal snap-scroll strip at the top of the body with 1D %, Vol ratio, and unread filing dot. | 1-tap navigation to any company without leaving the current flow. | 
| **Monospace Tabular Numbers** | Every price, percentage, crore value, and SHA-256 hash uses `font-mono tabular-nums`. | Columns align to the pixel; looks like a Bloomberg/Koyfin mobile terminal. | 
| **1-Tap Citation Pills** | Every number or claim has a mini pill `[📄 p.29]` that opens the bottom-sheet PDF/quote drawer in `<50ms`. | Proves zero hallucination on every single screen. | 
| **Epistemic Humility Badges** | Explicit pills for `Consolidated vs Standalone`, `Contemporaneous vs Retrospective`, and `Lender vs Industrial Schema`. | Shows genuine public-markets domain instinct rather than generic AI summaries. | 
