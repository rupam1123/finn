# Reviewed execution baseline — revision 1

Reviewed 27 October 2026 against both official PDFs. The official main brief remains authoritative. The corrections in the final section and plan-review.md override conflicting wording in the original plan below. Work remains in the five-phase sequence; the six calendar dates include a two-day final phase. Day 1 is local implementation and verification; deployment follows later.

---

# FINN: Financial Investment Agent — Master Architecture & Execution Plan

**Challenge:** ENAM Holdings AI Engineer Build Challenge  
**Timeline:** Tuesday, October 27, 2026 – Sunday, November 1, 2026 (5 Calendar Days)  
**Submission Target:** `assessment@enam.com` | **Subject:** `ENAM - IIT screening - 2027`  
**Core Deliverable:** Mobile-First Working Prototype + GitHub Repository + AI Build History + Covering Writeup

---

## 1. Executive Summary & Core Product Philosophy

An institutional public-markets investor does not suffer from a lack of information; they suffer from **signal dilution**. Every day across a 20-stock portfolio, exchanges publish dozens of routine compliance certificates, postal ballots, and ESOP notices alongside a handful of thesis-altering disclosures (earnings surprises, sudden CFO resignations, capital allocation shifts, or unexplained volume spikes).

> **The North Star:** *"The scarce skill is not aggregating information. It's filtering it: surfacing the few things that actually matter and burying everything else, beautifully."*

### Our Product Point of View (Why FINN Wins)
Because every candidate has access to frontier LLMs, a generic "Chat with PDF" or standard stock dashboard will blend into the crowd. We position **FINN** as an **Evidence-First Mobile Investment Terminal & Forensic Accountability Agent** built around three strict principles:
1. **Zero AI Slop, High Financial Density:** Investors read structured tables, basis-point deltas ($\Delta\text{ bps}$), $\text{QoQ}/\text{YoY}$ percentages, and verbatim management quotes—never walls of generic chatbot prose.
2. **Deterministic Math, Probabilistic Synthesis:** LLMs never perform mental arithmetic. Python computes every financial growth rate, margin, cash-conversion ratio, and volume anomaly deterministically; LLMs are strictly routed to classify unstructured filings, extract schema-constrained tables, and audit management promises against delivered numbers.
3. **Traceable Primary-Source Discipline:** Every analytical claim in Pull Mode is anchored to an interactive citation pill (`[Q2 FY26 Concall, p. 7]` or `[FY25 AR, p. 114]`) that opens a bottom sheet displaying the exact verbatim excerpt from the primary filing.

---

## 2. Strategic Synthesis: Combining the Best of Both Strategies

| Architectural Layer | Foundational Strategy (ChatGPT) | High-Saliency Upgrade (Our Combined Master Plan) |
| :--- | :--- | :--- |
| **Product Structure** | Split into two focused workflows: **FINN Signal Inbox (Push)** and **FINN Research Workspace (Pull)**. | Add a **Cross-Signal Attribution Engine** that links Push price/volume anomalies with Push filings, plus a **Scoped Primary-Source Copilot & 60s Audio Brief** for mobile commute ergonomics. |
| **Mathematical Accuracy** | Never trust LLMs with arithmetic; compute all $\text{QoQ}\%$, $\text{YoY}\%$, and ratios in Python. | Add **Indian Financial Normalization Guards**: automatic $\text{₹ Lakhs} \rightarrow \text{₹ Crores}$ conversion, Consolidated-first statement locking, Loss-to-Profit turnaround handling, and a **Banking/NBFC Schema Switcher**. |
| **Push Mode Intelligence** | Rank corporate filings by materiality and collapse routine noise; trigger EOD price/volume alerts. | Add a visible **Noise Burial Telemetry Counter** (`47 Scanned -> 4 Material · 43 Buried`) and **Market-Session-Aware Windowing** so Sunday/Monday evaluation never lands on an empty weekend feed. |
| **Pull Mode Intelligence** | Focus heavily on **Narrative vs. Numbers** (management guidance vs. actual delivery) using primary sources. | Build the **4-Quarter "Say-Do" Credibility Ledger** (Promised Quote vs. Actual Metric vs. Beat/Miss Verdict + Subsequent Concall Explanation) alongside a **Forensic Cash Quality Check** ($\text{CFO}/\text{PAT}$). |
| **Cost & Latency Efficiency** | Cache outputs and route tasks between fast extraction models and heavier reasoning models. | Expose a toggleable **"Engine Telemetry Badge"** in the UI displaying exact tier routing (`Tier-0 Python` $\rightarrow$ `Tier-1 Flash` $\rightarrow$ `Tier-2 Pro`), latency, cache status, and token cost per query. |

---

## 3. The Saliency Strategy: 5 Signature Differentiators

### Differentiator 1: Cross-Signal Attribution ("Explained vs. Unexplained Moves")
When a portfolio stock crosses an End-of-Day (EOD) threshold—such as daily volume $> 2.0\times$ its 20-day moving average or price change $> \pm 3.0\%$—FINN does not just fire an isolated price alert. It automatically cross-references NSE/BSE filings within a $\pm 48\text{-hour}$ window:
* **🟢 Attributed Move:** Links the price/volume spike directly to the catalyst filing (e.g., `Volume 3.4x | Price +6.2% — Linked to Q2 FY27 Results Beat filed Oct 24`).
* **🔴 Unexplained Anomaly:** Flags when a stock experiences heavy institutional volume with **zero material exchange filings** in the last 48 hours (`Volume 2.8x | Price -4.1% — No Material Filing Found. Watch for pending disclosure`).

### Differentiator 2: Visible "Noise Burial" Telemetry
At the top of the Mobile Signal Inbox, FINN quantifies how much time it saved the investor:
* **Header Pill:** `52 Filings Ingested · 5 Material Surfaced · 47 Routine Buried (90.4% Noise Filtered)`
* **The Buried Drawer:** All `unclassified` disclosures (Reg 74(5) demat certificates, ESOP allotments, duplicate newspaper ads, routine trading window closures) are collapsed into a single muted bottom accordion. The investor can inspect them in one tap, proving nothing was lost while keeping the primary viewport surgical.

### Differentiator 3: The 4-Quarter "Say-Do" Credibility Ledger (Pull Centerpiece)
Instead of summarizing what management said on an earnings call, FINN audits management's track record across the last 4 quarters:
1. **Guidance Extraction:** Extracts explicit forward-looking targets from historical concall transcripts (revenue growth $\%$, $\text{EBITDA}$ margin bands, capex outlay, debt reduction, or order-book conversion).
2. **Deterministic Audit:** Compares those targets against the actual reported numbers in subsequent quarterly filings.
3. **Structured Output Card:**
   * **Quarter & Source:** `Q4 FY25 Concall (May 2025, p. 9)`
   * **What Was Promised:** *"We are confident of achieving $18\%\text{–}20\%$ EBITDA margins in FY26 driven by operating leverage."*
   * **What Was Delivered:** `Actual FY26 EBITDA Margin: 15.6% (-240 bps below lower band)`
   * **Verdict Badge:** `❌ MISSED TARGET`
   * **Management's Follow-Up Explanation:** Extracted from Q3/Q4 FY26 concall explaining the variance (e.g., raw material spike vs. delayed plant commissioning).

### Differentiator 4: Forensic Cash Quality & Balance Sheet Reality Check
Institutional investors at firms like ENAM care deeply about capital allocation and accounting integrity. FINN automatically computes and flags:
* **Cash Conversion Efficiency:** Cumulative 3-Year and 5-Year $\frac{\text{Cash Flow from Operations (CFO)}}{\text{Net Profit (PAT)}}$. If $\frac{\text{CFO}}{\text{PAT}} < 70\%$ persistently, FINN triggers a **⚠️ Low Cash Conversion Warning** and inspects receivables/inventory buildup.
* **Working Capital Cycle Trajectory:** Tracks Debtor Days $+$ Inventory Days $-$ Creditor Days across 3–5 years.
* **Balance Sheet & Governance Red Flags:** Scans Annual Report notes for Contingent Liabilities ($\%$ of Net Worth), Related-Party Transactions (RPTs), Promoter Pledging deltas, and Auditor Qualifications.

### Differentiator 5: Live AI Engineering & Cost Telemetry ("Bonus Points Mode")
A subtle header toggle (`⚙️ Telemetry`) reveals the exact engineering mechanics behind every card:
* `Pipeline: Tier-0 (Pandas Math) + Tier-1 (Gemini 2.5 Flash) | Latency: 340ms (Warm Cache) | Est. Cost: $0.0002 | Primary Sources Verified: 4/4`

---

## 4. Curated Portfolio & Generalizable Ticker Universe

### A. The 18-Stock Mock Portfolio (Push Mode)
Selected across market caps (Large, Mid, Small) and sectors (IT, Banking/NBFC, Pharma, Auto, Capital Goods, Consumer, Chemicals, Telecom) to guarantee diverse real-world filings (`results`, `M&A`, `management_change`, `capex`, `dividend`, `litigation`, `credit_rating`, `unclassified`) and EOD volume movements:

| # | NSE Symbol | Yahoo Ticker | Company Name | Sector | Market Cap Tier | Primary Signal Role in Demo |
| :- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `RELIANCE` | `RELIANCE.NS` | Reliance Industries Ltd. | Conglomerate / Energy | Mega Cap | Q2 Results, Capex & Subsidiary M&A filings |
| 2 | `TCS` | `TCS.NS` | Tata Consultancy Services Ltd. | IT Services | Mega Cap | Quarterly Results ($\text{QoQ}/\text{YoY}$), Dividend, Concall |
| 3 | `HDFCBANK` | `HDFCBANK.NS` | HDFC Bank Ltd. | Banking | Mega Cap | Tests Banking Schema ($\text{NII}/\text{NIM}/\text{GNPA}$ vs $\text{EBITDA}$) |
| 4 | `INFY` | `INFY.NS` | Infosys Ltd. | IT Services | Large Cap | Explicit Revenue & Margin Guidance Revisions |
| 5 | `TATAMOTORS` | `TATAMOTORS.NS` | Tata Motors Ltd. | Automobiles | Large Cap | Demerger / M&A corporate action, JLR volume updates |
| 6 | `SUNPHARMA` | `SUNPHARMA.NS` | Sun Pharmaceutical Industries | Pharmaceuticals | Large Cap | USFDA regulatory/litigation updates & R&D guidance |
| 7 | `LT` | `LT.NS` | Larsen & Toubro Ltd. | Capital Goods / EPC | Large Cap | Frequent Order Win (`press_release`) & guidance tracking |
| 8 | `BAJFINANCE` | `BAJFINANCE.NS` | Bajaj Finance Ltd. | NBFC | Large Cap | Fundraise / credit rating / AUM & credit cost guidance |
| 9 | `TRENT` | `TRENT.NS` | Trent Ltd. | Retail / Consumer | Large Cap | High-growth trajectory, store expansion capex, volume spikes |
| 10 | `ZOMATO` | `ZOMATO.NS` | Eternal Ltd. (Zomato) | Consumer Tech | Large Cap | QIP `fund_raise`, Blinkit capex, loss-to-profit turnaround |
| 11 | `PERSISTENT` | `PERSISTENT.NS` | Persistent Systems Ltd. | Mid-Cap IT | Mid Cap | High-signal concall transcripts, M&A tuck-ins, CXO changes |
| 12 | `DIXON` | `DIXON.NS` | Dixon Technologies (India) | EMS / Manufacturing | Mid Cap | Joint ventures (`M&A`), PLI `capex`, working capital efficiency |
| 13 | `POLYCAB` | `POLYCAB.NS` | Polycab India Ltd. | Cables & Wires | Mid Cap | Tax/regulatory `litigation` history, strong cash conversion |
| 14 | `DEEPAKNTR` | `DEEPAKNTR.NS` | Deepak Nitrite Ltd. | Specialty Chemicals | Mid Cap | Margin compression trajectory, capex commissioning delays |
| 15 | `LAURUSLABS` | `LAURUSLABS.NS` | Laurus Labs Ltd. | Pharma / CDMO | Mid Cap | Classic "Narrative vs. Numbers" guidance miss & recovery |
| 16 | `KPITTECH` | `KPITTECH.NS` | KPIT Technologies Ltd. | Auto ER&D Software | Mid Cap | Consistent guidance beat, high $\text{ROCE}$, acquisition filings |
| 17 | `SUZLON` | `SUZLON.NS` | Suzlon Energy Ltd. | Renewables / Capital Goods | Mid Cap | Balance sheet turnaround, promoter `pledging` history, order wins |
| 18 | `JYOTHYLAB` | `JYOTHYLAB.NS` | Jyothy Labs Ltd. | FMCG | Small/Mid Cap | Clean balance sheet, margin vs. volume commentary |

### B. Ad-Hoc Showcase Companies (Pull Mode Quick-Pills)
In addition to the 18 portfolio companies, the Pull Workspace features 5 one-tap showcase tickers outside the portfolio:
1. `TITAN.NS` (Titan Company — Margin trajectory & jewelry guidance)
2. `COFORGE.NS` (Coforge — QIP, Cigniti acquisition & order intake vs. guidance)
3. `SYNGENE.NS` (Syngene International — Capex vs. revenue guidance revisions)
4. `SONACOMS.NS` (Sona BLW Precision — EV order book narrative vs. numbers)
5. `CAMS.NS` (Computer Age Management Services — High $\text{ROE}$ / cash conversion benchmark)

### C. Universal NSE Generalization ("Any Ticker" Guarantee)
* The frontend bundles a lightweight, instant-search JSON dictionary of **all ~2,200 active NSE-listed companies** (`symbol`, `company_name`, `isin`, `sector`).
* When an evaluator searches **any unseen NSE ticker** (e.g., `HAVELLS`, `ASTRAL`, `NAVINFLUOR`, `IRCTC`), the backend dynamically executes the live ingestion pipeline against `screener.in/company/{SYMBOL}/` and NSE APIs without any hard-coded dependencies.

---

## 5. System Architecture & 3-Tier Model Routing

### High-Level Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                   FRONTEND: Mobile-First PWA (Next.js + Tailwind)                 |
|  [Tab 1: Signal Inbox (Push)]   [Tab 2: Forensic Workspace (Pull)]   [Copilot]    |
+-----------------------------------------+-----------------------------------------+
                                          | REST + Server-Sent Events (SSE Streaming)
+-----------------------------------------v-----------------------------------------+
|                        BACKEND: Python FastAPI Orchestrator                       |
|                                                                                   |
|  +-----------------------------+               +-------------------------------+  |
|  |     PUSH ENGINE MODULE      |               |      PULL ENGINE MODULE       |  |
|  | - EOD Anomaly Detector      |               | - Dynamic Screener Scraper    |  |
|  | - 16-Category Classifier    |               | - Concall & AR PDF Chunker    |  |
|  | - Materiality Scorer        |               | - Sector Schema Switcher      |  |
|  | - Results Table Extractor   |               | - Say-Do Credibility Auditor  |  |
|  | - CXO Bio Enricher          |               | - Citation Substring Verifier |  |
|  +--------------+--------------+               +---------------+---------------+  |
|                 |                                              |                  |
|  +--------------v----------------------------------------------v---------------+  |
|  |                    3-TIER SMART MODEL ROUTING & CACHE LAYER                 |  |
|  |  [Tier 0: Python/Pandas/Regex] -> [Tier 1: Gemini Flash] -> [Tier 2: Pro]   |  |
|  |  [SQLite / Postgres Persistent Cache: Filings, Parsed Tables, Embeddings]   |  |
|  +--------------+----------------------------------------------+---------------+  |
+-----------------|----------------------------------------------|------------------+
                  |                                              |
    +-------------v--------------+                 +-------------v--------------+
    |     PUSH DATA SOURCES      |                 |     PULL DATA SOURCES      |
    | - Yahoo Finance (yfinance) |                 | - Screener.in (Tables/IR)  |
    | - NSE / BSE Filings Feed   |                 | - Concall Transcripts PDF  |
    | - Web Search (CXO Bio only)|                 | - Annual Reports & Decks   |
    +----------------------------+                 +----------------------------+
```

### The 3-Tier Routing Discipline (Maximizing Speed & Minimizing Cost)

1. **Tier 0 — Deterministic Python, Regex & Pandas (Cost: $\$0.00$ | Latency: $<50\text{ms}$):**
   * **EOD Price & Volume Math:** Calculates 1-day return $\%$, 5-day return $\%$, 20-day average volume, and volume spike ratio:
     $$\text{Volume Ratio} = \frac{\text{Volume}_{t}}{\frac{1}{20}\sum_{i=1}^{20}\text{Volume}_{t-i}}$$
   * **Pre-Classification Regex Filter:** Immediately tags 100% obvious routine disclosures (e.g., `"Regulation 74(5)"`, `"Closure of Trading Window"`, `"Loss of Share Certificate"`, `"Newspaper Advertisement"`) as `unclassified` with materiality score $0.05$—saving 60%+ of LLM calls.
   * **Financial Table Ratios & Deltas:** Computes $\text{QoQ}\%$, $\text{YoY}\%$, $\text{EBITDA Margin}\%$, $\text{PAT Margin}\%$, $\text{CFO}/\text{PAT}\%$, and $\text{D/E}$ deterministically from scraped tables.

2. **Tier 1 — High-Speed Structured Extractor (`Gemini 2.5 Flash` / `GPT-4o-mini` | Cost: $\sim\$0.0002/\text{call}$):**
   * Classifies remaining corporate announcements into the 16 canonical categories and writes a crisp 15-word impact headline.
   * Parses raw Quarterly Result PDF tables into standardized JSON (`Revenue`, `EBITDA`, `PBT`, `PAT` across `Current Q`, `Prev Q`, `Year-Ago Q`) with unit tags (`Lakhs` vs `Crores`).
   * Extracts structured guidance statements and management commentary chunks from earnings call transcripts.

3. **Tier 2 — Frontier Reasoning Auditor (`Gemini 2.5 Pro` / `Claude 3.5 Sonnet` | Cost: $\sim\$0.003/\text{call}$, Cached):**
   * Invoked **only** for multi-document synthesis:
     * Auditing 4 quarters of extracted guidance promises against delivered actuals (**Narrative vs. Numbers**).
     * Synthesizing the **Bull vs. Bear Tension** and **Forensic Cash/Governance Red Flags** strictly from retrieved primary excerpts.
     * Generating the **Incoming Executive Background Dossier** on `management_change` filings.

---

## 6. Step-by-Step Functional Specification: PUSH Mode (`Signal Inbox`)

### Step 1: EOD Market Data & Configurable Threshold Engine
* **Data Fetch:** Uses `yfinance` bulk download for all 18 `.NS` tickers over a 30-trading-day lookback.
* **User-Configurable Threshold Sliders (Interactive UI):**
  * **Price Move Threshold ($\pm X\%$):** Default $\pm 3.0\%$ (adjustable from $1.0\%$ to $10.0\%$ in $0.5\%$ steps).
  * **Volume Spike Threshold ($Y\times$):** Default $2.0\times$ 20-day average volume (adjustable from $1.2\times$ to $5.0\times$).
  * **Category Watchlist Toggles:** Checkboxes for high-priority categories (`results`, `M&A`, `management_change`, `litigation`, `fund_raise`, `capex`, `pledging`).
* **Instant Recalculation:** Moving a slider in the mobile UI recalculates triggered alerts in real time ($<20\text{ms}$) against the cached 30-day EOD series and updates the Cross-Signal Attribution badges.

### Step 2: Corporate Filings Ingestion & 16-Category Classification
Every announcement ingested from NSE/BSE is mapped to the 16 categories defined in the Reference guide and assigned a **Materiality Tier**:

| Materiality Tier | Priority Score | Categories Included | Default UI Treatment |
| :--- | :--- | :--- | :--- |
| **Tier 1: Critical Thesis Event** | $85 - 100$ | `results`, `M&A`, `management_change`, `litigation` (major orders), `pledging` (spikes) | **Expanded Enriched Card** pinned to top of inbox with custom data table or bio dossier. |
| **Tier 2: High-Signal Update** | $60 - 84$ | `fund_raise`, `capex`, `credit_rating`, `earnings_call` (transcripts), `press_release` (order wins) | **Compact Action Card** with 1-line "Why It Matters" synthesis + PDF link. |
| **Tier 3: Corporate Actions & IR** | $30 - 59$ | `dividend`, `bonus_split`, `investor_meetings`, `insider_trading` | **Single-Line Digest Pill** showing key metric (e.g., `₹12/sh Dividend | Ex-Date: Nov 14`). |
| **Tier 4: Routine Noise (Buried)** | $0 - 29$ | `postal_ballot`, `agm_egm` (routine notices), `unclassified` (ESOPs, Reg 74(5), newspaper ads) | **Collapsed into "Buried Routine Drawer"** at bottom of feed; counted in Noise Filter header. |

### Step 3: Signature Push Enrichments
1. **Quarterly Results Auto-Parser (`results` category):**
   * Extracts `Revenue`, `EBITDA`, `PBT`, and `PAT` from the exchange filing PDF.
   * Normalizes units to `₹ Cr` and computes $\text{QoQ}\%$, $\text{YoY}\%$, and $\text{EBITDA Margin}\%$ ($\Delta\text{ bps}$).
   * Renders a clean 4-row mobile comparison table plus a 1-sentence diagnostic (e.g., *"Top-line grew $+11.4\%\text{ YoY}$, but EBITDA margin compressed by $-185\text{ bps}$ due to raw material cost inflation"*).
2. **Management Change Bio Enricher (`management_change` category):**
   * Identifies the person's name, role (`CEO`, `CFO`, `MD`, `Whole-Time Director`), and action (`Appointed` vs. `Resigned` vs. `Retired`).
   * Extracts the statutory "Brief Profile" annexure attached to the NSE filing and enriches it with public career background (prior companies, tenure, domain expertise) to render an instant **Executive Dossier Card**.

---

## 7. Step-by-Step Functional Specification: PULL Mode (`Forensic Workspace`)

### Step 1: Two-Stage Progressive Loading (Solving Mobile Latency)
When a user selects a showcase stock or types any unseen NSE ticker (`ANY.NS`):
* **Stage 1 ($<2.5\text{ seconds}$ — Instant Quantitative Foundation):**
  * Scrapes `screener.in/company/{SYMBOL}/consolidated/` (with automatic fallback to `/company/{SYMBOL}/` if standalone).
  * Parses the company overview, multi-year P&L (10Y), Quarterly Results (last 8–12 quarters), Balance Sheet, Cash Flows, Ratios, and Shareholding Pattern.
  * Immediately renders **Card 1 (Business & Financial Snapshot)**, **Card 2 (Multi-Year Trajectory)**, and **Card 3 (Balance Sheet & Cash Quality)** on the user's screen.
* **Stage 2 ($4\text{–}8\text{ seconds}$ via SSE Streaming — Deep Primary Qualitative Audit):**
  * Extracts the direct PDF/document links for the **latest 4 Concall Transcripts**, **Investor Presentations**, and **latest Annual Report** from Screener's `Documents` section.
  * Downloads and extracts text using `PyMuPDF` (`fitz`), chunks by section/speaker (Management Opening Remarks vs. Analyst Q&A), and runs the **Narrative vs. Numbers ("Say-Do" Ledger)** and **Bull vs. Bear** synthesis.

### Step 2: The 8 Pull Modules (Organized into 4 High-Density Mobile Cards)
To prevent endless vertical scrolling on a phone, the 8 menu items from the brief are structured into 4 interactive, swipeable/tappable Bento views:

1. **View 1: Business & Financial Snapshot + Multi-Year Trajectory**
   * Business model summary, revenue mix/segments, and key ratios ($\text{ROCE}\%$, $\text{ROE}\%$, $\text{D/E}$, $\text{OPM}\%$).
   * 5-Year & 4-Quarter trajectory sparklines showing what is accelerating vs. compressing.
2. **View 2: Narrative vs. Numbers + Forward Guidance (The Star Module)**
   * **The 4-Quarter "Say-Do" Audit Ledger:** Side-by-side table of Management's Stated Guidance/Commentary vs. Actual Delivered Numbers across the last 4 quarters, complete with `✅ Beat`, `⚠️ In-Line`, or `❌ Missed` badges and management's post-hoc explanation.
   * **Current Forward Guidance Tracker:** Explicit forward targets currently active for revenue growth, margins, capex, and order book.
3. **View 3: Cash Quality & Balance Sheet Forensics**
   * **Cash Conversion Check:** Cumulative $\text{CFO}$ vs. Cumulative $\text{PAT}$ bar comparison + Free Cash Flow ($\text{FCF} = \text{CFO} - \text{Capex}$) trend.
   * **Working Capital & Leverage:** Debtor days, Inventory days, Working Capital cycle trend, $\text{D/E}$ ratio, Promoter Pledging $\%$, and Annual Report governance flags (Contingent Liabilities, RPTs).
4. **View 4: Primary-Grounded Bull vs. Bear Case**
   * Tight 3-bullet Bull Case vs. 3-bullet Bear Case where **every single bullet is backed by a primary filing citation pill**.

### Step 3: Strict Primary-Source Verification Guardrails
To guarantee 100% compliance with ENAM's rule (*"No broker notes, no news, no research reports, and don't lean on the model's own outside knowledge"*):
* **System Prompt Lock:** The LLM prompt explicitly forbids external knowledge and requires every analytical statement to reference a specific `chunk_id` from the ingested Annual Report, Concall Transcript, or Exchange Filing.
* **Substring Verification Check:** Each citation returns `{doc_type, period, page_number, verbatim_quote}`. The backend verifies that `verbatim_quote` exists in the extracted primary document text. Tapping the citation pill on mobile opens the **Primary Evidence Drawer** with the highlighted paragraph and a button to open the original PDF.

---

## 8. Comprehensive Edge-Case Matrix & Defensive Engineering

| # | Edge Case Category | Specific Failure Mode | Our Engineered Solution |
| :- | :--- | :--- | :--- |
| **1** | **Financial Domain** | **The Banking / NBFC Trap:** Evaluator enters `HDFCBANK`, `ICICIBANK`, or `BAJFINANCE`. Banks do not have `EBITDA` or `Working Capital Days`. | **Sector-Aware Schema Switcher:** Detect `Banking / Finance` from Screener sector metadata. Automatically replace `EBITDA` & `Working Capital` with `Net Interest Income (NII)`, `Financing Profit`, `Financing Margin %`, and `GNPA / NNPA %`. |
| **2** | **Financial Domain** | **Consolidated vs. Standalone Mismatch:** Mixing standalone quarterly filings with consolidated annual data corrupts $\text{YoY}\%$. | **Consolidated-First Lock:** Always query `/consolidated/` first and tag every table with a visible `[Consolidated]` badge. Fallback to `[Standalone]` only when the company has no subsidiaries. |
| **3** | **Financial Domain** | **Unit Inconsistency ($\text{₹ Lakhs}$ vs. $\text{₹ Crores}$ vs. $\text{₹ Millions}$):** NSE PDFs frequently report in Lakhs while Screener reports in Crores. | **Deterministic Unit Normalizer:** Regex-detect unit headers (`Rs. in Lakhs`, `₹ in Million`, `Rs. Cr`) before extraction and apply exact multipliers ($\div 100$ for Lakhs, $\div 10$ for Millions) so all UI outputs are standardized in `₹ Cr`. |
| **4** | **Financial Domain** | **Loss-to-Profit / Profit-to-Loss Math:** If $\text{PAT}$ moves from $-\text{₹40 Cr}$ to $+\text{₹20 Cr}$, standard formula gives $-150\%$, looking like a drop. | **Sign-Aware Delta Function:** If $\text{Prev} < 0$ and $\text{Curr} > 0$, output `Turnaround (Loss → Profit)`. If $\text{Prev} > 0$ and $\text{Curr} < 0$, output `Swung to Loss`. If both $< 0$, output `Loss Narrowed` or `Loss Widened`. |
| **5** | **Financial Domain** | **Indian Fiscal Year (FY) Labeling:** LLMs confuse `Q2 FY26` (Jul–Sep 2025) with `Q2 2026`. | **Month-End Canonical Labels:** Always anchor periods with explicit month-end strings (`Sep 2025 (Q2 FY26)`, `Dec 2025 (Q3 FY26)`, `Mar 2026 (Q4 FY26)`, `Jun 2026 (Q1 FY27)`). |
| **6** | **Evaluation Timing** | **The Sunday/Weekend Grading Trap:** Deadline is Sunday, Nov 1. Strict "Last 24h" has zero trading volume and almost no filings. | **Market-Session-Aware Windowing:** Default view is **"Latest Trading Session + Weekend Filings"** with 1-tap pills for `24h`, `3 Days`, `7 Days`, and `30 Days` so the feed is always rich and verifiable. |
| **7** | **Scraping Resilience** | **NSE / BSE Anti-Bot 403 Blocks on Cloud IPs:** NSE blocks raw Python `requests` without active session cookies. | **3-Stage Fetcher:** (1) Persistent `httpx.AsyncClient` with homepage cookie warm-up and rotating browser TLS headers; (2) BSE / Screener announcement feed fallback; (3) Pre-seeded SQLite snapshot of the last 30 days of filings for all 18 portfolio stocks. |
| **8** | **Unseen Ticker** | **Small-Cap / PSU Missing Concall Transcripts:** Evaluator enters an NSE company that does not host earnings calls. | **Graceful Primary Fallback:** If zero concall transcripts exist on Screener, automatically pivot the Narrative vs. Numbers engine to audit the **Annual Report "Management Discussion & Analysis (MD&A)" & Director's Report** across the last 2 Annual Reports, and display a transparent badge explaining the source pivot. |
| **9** | **PDF Processing** | **Scanned / Image-Only PDFs or 400-Page Annual Reports:** Downloading and parsing a 400-page AR live times out mobile requests. | **Targeted Section Extraction & Page Cap:** For live unseen tickers, prioritize Concall Transcripts ($15\text{–}25$ pages, pure text) and Investor Presentations first; for Annual Reports, use TOC/keyword indexing to extract only the MD&A and Auditor Report page ranges. |
| **10** | **User Input** | **Ambiguous Ticker Queries:** Evaluator types `"Tata"`, `"Bajaj"`, or `"Zomato"` (recently renamed Eternal). | **Fuzzy NSE Dictionary Autocomplete:** Instant client-side search across symbol, company name, and historical aliases (e.g., mapping both `ZOMATO` and `ETERNAL` cleanly). |
| **11** | **LLM Integrity** | **Hallucinated Numbers or Pre-Trained Memory Bleed:** LLM invents guidance numbers from 2023 training data. | **Schema Lock + Abstention Rule:** Temperature set to $0.0$. Prompt enforces: *"If explicit numerical guidance is not stated in the provided transcript chunks, return `No Explicit Numerical Guidance Stated` and evaluate qualitative directional commentary instead."* |

---

## 9. Detailed 5-Day Execution Roadmap (Oct 27 – Nov 1, 2026)

### Day 1 (Tuesday, Oct 27): Architecture Lock, Portfolio Seed & Core Data Scrapers
* **Goal:** Get all three backend data sources flowing deterministically into SQLite/JSON before building UI.
* **Tasks:**
  1. Initialize monorepo structure (`/backend` with Python FastAPI + `/frontend` with Next.js TypeScript Tailwind PWA).
  2. Build `market_data.py`: Fetch 30-day EOD OHLCV via `yfinance` for the 18 portfolio tickers; compute 1D $\Delta\%$, 5D $\Delta\%$, and 20D Volume Spike Ratio.
  3. Build `filings_ingest.py`: Fetch corporate announcements from NSE/BSE + Screener for the 18 portfolio stocks; store raw metadata and PDF links in SQLite.
  4. Build `screener_scraper.py`: Generalizable scraper that takes **any** NSE symbol, fetches `screener.in/company/{SYMBOL}/consolidated/`, and extracts clean JSON tables for Quarterly Results, Annual P&L, Balance Sheet, Cash Flow, Ratios, and Document Links (Concalls + ARs).
* **Day 1 Verification Check:** Run CLI test script on `TCS` (IT), `HDFCBANK` (Bank), `LAURUSLABS` (Mid-cap Pharma), and an unseen ticker `ASTRAL`—confirm JSON output in $<3\text{s}$.

### Day 2 (Wednesday, Oct 28): The PUSH Intelligence Engine & Enrichment Pipelines
* **Goal:** Turn raw filings and EOD prices into prioritized, enriched Push cards.
* **Tasks:**
  1. Build `classifier.py`: Tier-0 regex pre-filter for routine noise (`unclassified`) + Tier-1 Flash classifier for the 16 categories with materiality scoring ($0\text{–}100$).
  2. Build `results_enricher.py`: PDF parser (`PyMuPDF`) + Tier-1 structured extractor + Python math normalizer that generates the `Revenue / EBITDA / PBT / PAT` table with $\text{QoQ}\%$ and $\text{YoY}\%$ deltas.
  3. Build `management_enricher.py`: Extracts executive appointment/resignation details from filing PDF + enriches incoming executive bio.
  4. Build `cross_signal.py`: Links EOD price/volume anomalies ($\pm X\%$, $>Y\times$ vol) to filings within $\pm 48\text{h}$ to tag **Attributed** vs. **Unexplained** moves.
* **Day 2 Verification Check:** Query `/api/push/digest?window=7d&price_threshold=3.0&vol_threshold=2.0` and verify ranked cards, noise burial count, and enriched tables.

### Day 3 (Thursday, Oct 29): The PULL Primary-Source Engine & "Say-Do" Auditor
* **Goal:** Build the generalizable on-demand research engine grounded strictly in primary documents.
* **Tasks:**
  1. Build `transcript_rag.py`: Downloads latest 4 Concall Transcripts (and MD&A fallback) for any ticker, chunks by speaker/topic, and indexes with page numbers.
  2. Build `narrative_auditor.py`: Tier-2 reasoning pipeline that cross-examines 4 quarters of management guidance/commentary chunks against the deterministic Screener quarterly numbers to generate the **Say-Do Credibility Ledger**.
  3. Build `forensic_analyzer.py`: Computes Cash Conversion ($\text{CFO}/\text{PAT}$), Working Capital cycle trends, Leverage, and scans for RPT / Contingent Liability flags + generates grounded Bull vs. Bear bullets with verbatim quote verification.
  4. Implement warm caching for the 18 portfolio + 5 showcase tickers AND test cold-start streaming for unseen tickers.
* **Day 3 Verification Check:** Run Pull pipeline on `INFY`, `DEEPAKNTR`, `HDFCBANK`, and a random unseen ticker `KPIL`—confirm every claim has a valid verbatim citation quote and zero hallucinated metrics.

### Day 4 (Friday, Oct 30): Mobile-First UI, Interactive Controls & Audio Briefing
* **Goal:** Build an institutional-grade, thumb-friendly mobile experience that feels like a native app.
* **Tasks:**
  1. Build Mobile Viewport Shell (responsive on any phone; centered mobile frame with live QR code when opened on desktop so evaluators can scan and test on their phone in 2 seconds).
  2. Build **Tab 1: FINN Signal Inbox (Push UI)**:
     * Noise Burial Telemetry Header (`X Scanned · Y Material · Z Buried`).
     * Interactive Alert Threshold Drawer (Sliders for Price $\pm X\%$ and Volume $>Y\times$, Window pills for `Latest Session`, `3D`, `7D`, `30D`).
     * Enriched Cards for Results ($\text{QoQ}/\text{YoY}$ table), Management Changes (Bio card), Cross-Signal Volume Alerts, and the Collapsible Routine Drawer.
  3. Build **Tab 2: FINN Forensic Workspace (Pull UI)**:
     * Instant Fuzzy Search Bar (2,200+ NSE tickers) + Showcase Quick-Pills.
     * 4-Card Bento Layout: Snapshot & Trajectory, **4-Quarter Say-Do Credibility Ledger**, **Cash Quality & Balance Sheet Forensics**, and **Bull vs. Bear**.
     * Interactive **Verbatim Evidence Bottom Sheet** (tap any `[Q2 Concall, p. 8]` pill to view highlighted primary text + PDF link).
  4. Build **Scoped Primary-Source Copilot & 60s Audio Morning Brief** + **Telemetry Badge Toggle**.

### Day 5 (Saturday, Oct 31 – Sunday, Nov 1): Stress Testing, Deployment & Submission Package
* **Goal:** Bulletproof deployment, zero broken states, and a standout covering writeup.
* **Tasks:**
  1. **Unseen Ticker Gauntlet:** Test 15 random NSE tickers across Large, Mid, Small, and Banking sectors to ensure graceful handling of missing transcripts, standalone-only accounts, and negative-to-positive turnarounds.
  2. **Deploy Production Build:** Deploy Frontend to Vercel and Backend + SQLite Cache to Render/Railway/Fly.io with HTTPS. Test thoroughly on both iOS Safari and Android Chrome.
  3. **Package Repository & AI Build History:** Clean up README with architecture diagrams, organize prompt/conversation logs showing how we architected and debugged the system.
  4. **Write Covering Email & Submit:** Draft the concise executive covering note (what we built, key trade-offs, what we intentionally cut, and roadmap) and send to `assessment@enam.com` with subject `"ENAM - IIT screening - 2027"`.

---

## 10. Final Submission Checklist

- [ ] **1. Live Mobile-First Prototype URL:** Tested on iOS Safari & Android Chrome; includes desktop QR code wrapper for instant mobile handoff.
- [ ] **2. Public/Accessible GitHub Repository:** Clean code, `.env.example`, architecture documentation, and reproducible setup instructions.
- [ ] **3. AI Build History Exports:** Exported transcripts/links of this architectural design session and coding-agent workflows demonstrating engineering judgment.
- [ ] **4. Executive Covering Note (Email Body):**
  - **What We Built:** Signal Inbox (Push) + Forensic Accountability Workspace (Pull).
  - **Key Engineering & Product Decisions:** Deterministic Python math + 3-tier model routing, Cross-Signal Attribution, Noise Burial counter, and the 4-Quarter Say-Do Credibility Ledger.
  - **What We Deliberately Left Out:** Intraday tick-by-tick charting, secondary news/broker sentiment scraping (to preserve strict primary-data purity), and multi-user auth complexity.
  - **Where We'd Take It Next:** Automated BSE/NSE webhook listener with sub-minute WhatsApp/push delivery, automated table OCR for scanned small-cap filings, and portfolio-level factor exposure correlation.
- [ ] **5. Email Dispatch:** Sent to `assessment@enam.com` with exact subject line `ENAM - IIT screening - 2027` ahead of the Sunday, November 1, 2026 deadline.

---

# Revision 1 — binding corrections and acceptance gate

# FINN plan review — 27 October 2026

Reviewed all four pages of the official main brief, all three pages of the companion reference, and the full master plan. The main brief takes precedence, then the companion definitions, then the master plan with this correction record. The product remains Signal Inbox + Forensic Workspace, with deterministic Python calculations and inspectable primary evidence.

## Corrections locked before Day 1

| Area | Finding | Implementation decision |
| --- | --- | --- |
| Calendar | Oct 27–Nov 1 spans six calendar dates, not five. | Five work phases; Oct 31 and Nov 1 are validation/submission buffer. No exact submission hour is stated in the brief. |
| Scope | The brief's Pull modules are a menu. Eight modules plus audio, chat, OCR and governance analysis risk missing a working demo. | Prioritize Inbox and four-quarter Say–Do ledger with citations; cash quality next. Audio/copilot/QR/deep governance are stretch work after acceptance gates. |
| Categories | Reference page 1 lists **17**, not 16, categories. | Preserve all 17, including unclassified. Category and materiality are separate; unknown is not synonymous with routine. |
| Instruments | ZOMATO is now ETERNAL. TATAMOTORS became TMPV; the demerged commercial-vehicle entity is TMCV. | Use ETERNAL and TMPV for these portfolio slots. Preserve the historical ZOMATO alias; reject ambiguous Tata Motors name queries. Never splice demerged company financial histories. Refresh the NSE security master. |
| Portfolio claims | Market-cap tiers and demo stories in the plan are unverified hypotheses. | Keep the 18-company/5-showcase structure; never display a prewritten beat/miss, scandal, or size classification as a finding. |
| Primary sources | Screener's normalized tables and company summaries are secondary compilation. | Screener is document discovery and separately labelled unverified staging data. Pull claims/ratios and Say–Do actuals require original reports, transcripts or company/exchange filings, with field-level provenance. |
| Cross-signal | A filing within ±48 hours does not establish cause. Future filings introduce look-ahead. Volume alone does not identify institutional buyers. | Label “nearby filing” or “no matching filing in available coverage”; cutoff at alert time. Subsequent filings are clearly retrospective. No causal or institutional-flow claim. |
| Guidance alignment | Latest four transcripts may describe future years or require a fifth earlier transcript for the oldest outcome quarter. | Collect enough historical statements to cover four delivered periods. Store statement date, target horizon, metric, unit, currency, scope, revisions and source. Not-yet-due, withdrawn, qualitative and not-comparable are explicit states. |
| Verdicts | A lower number can be good (debt/cost), and qualitative remarks are not numerical promises. | Metric-specific direction and target bands; no beat/miss unless horizon and definition align. A company explanation is labelled management's explanation, not verified causality. |
| Basis | Missing consolidated page does not prove no subsidiaries. | Fallback only on genuine absence/redirect with explicit observed basis; never fallback for 403/429/timeouts. Never mix bases, fiscal calendars, currencies, quarter/YTD/full-year or restated/original values. |
| Periods | Not every issuer uses an April–March FY. Q4 may be derived from annual less 9M. | Preserve reported dates and duration first. Indian FY labels only where confirmed. Derived Q4 requires aligned annual/9M basis and a visible derived flag. |
| Units/metrics | Global crores conversion would corrupt EPS, percentages or share counts. Operating profit is not automatically EBITDA. | Typed monetary/per-share/percent/count values, exact Decimal conversion, unknown-unit abstention; do not invent EBITDA or double-count other income. |
| Banks/NBFCs | Bank NIM and Screener financing margin are not interchangeable; CFO/PAT is not a generic bank cash-quality test. | Separate bank, NBFC and nonfinancial profiles. Only reported NII/NIM/asset quality; no generic industrial EBITDA, working-capital or cash-conversion judgement for lenders. |
| Cash quality | CFO/PAT thresholds are heuristics, especially with zero/negative profit or mismatched PAT attribution. | Align cumulative periods/scope; undefined for nonpositive cumulative PAT. Capex is cash purchase of fixed/intangible assets, not total investing cash flow; record sign convention. |
| EOD | Thirty calendar days may contain fewer than 21 trading observations. Today's bar may be intraday. Corporate actions can distort returns/volume. | Fetch wider history, retain 30 completed sessions. Baseline uses prior 20 sessions excluding today. Reject invalid bars; flag corporate-action windows; label adjusted price return and raw volume separately. |
| Digest | Weekend convenience should not silently change a user's selected period. | Keep 24h default and offer explicit latest-session/weekend view with shown range and as-of date. Never present cached historical material as live. |
| Materiality | Auditor resignation/qualification and some ballots can matter despite a routine category. | Critical-content overrides before routine burial; unknown/low-confidence documents remain visible for review. Counts use deduplicated records with surfaced+buried total reconciliation. |
| Ingestion | Header rotation is not a guaranteed solution to exchange blocks; empty data is not proof of no filings. | Bounded requests, stable identification, polite backoff, provider status and completeness. Preserve raw responses, source URLs, observed times and hashes. No empty success on schema failure. |
| Citations | Substring match proves presence, not support or speaker identity. | Validate exact page and document hash, metric support, speaker, target period and primary provenance. Treat document text as untrusted data. OCR failures abstain. |
| Performance/cost | Hard-coded call costs and universal <3s/<8s cold starts are unsupported. | Measure cold vs warm latency, coverage and cache age. Record actual provider/model usage; estimate cost only with dated pricing. Current model choice stays configurable. |
| Reliability | SQLite on ephemeral cloud storage loses cached evidence; in-process jobs can vanish on restart. | Durable volume or managed DB, unique ingestion keys, schema versioning and resumable jobs. Verify deployment early, well before submission. |
| Security | Arbitrary PDF URLs and model output create fetch/render risks. | Validate ticker input; use a fixed, reviewed HTTPS document-host allowlist (no arbitrary hosts/IPs), reject credentials, alternate ports and cross-host redirects, and bound size/pages/time; do not render raw model HTML. Further deployment-specific DNS protections remain a hosting check. |
| History/submission | A build log is not the requested original AI conversation export. | Maintain decisions/tests now; include actual exported/shared conversations in final package. Draft final email at submission stage; do not send during Day 1. |

## Day 1 acceptance gate

1. Reproducible Python FastAPI + SQLite and Next.js/TypeScript/Tailwind monorepo foundation.
2. Exact 18-stock portfolio and five showcase symbols; unseen valid symbol accepted independently of portfolio.
3. EOD adapter, announcement adapter, and generalizable Screener document/table discovery with raw provenance and explicit errors.
4. Deterministic math and parser/storage/API tests, including missing data, invalid input, mixed units, zero denominators, corporate actions and blocked sources.
5. Run TCS, HDFCBANK, LAURUSLABS and unseen ASTRAL; record per-source coverage and timings. Extend ingestion to all 18. A partial or unavailable source is not a passed gate.
6. Retrieve at least one real primary document and preserve page-indexed text/hash to prove discovery reaches source bytes. Analytical extraction remains Day 3.
7. Keep cold <3s as an aspiration, measure it honestly. Finish with a checkpoint and explicit unresolved items; never use synthetic test fixtures as a live demo.

## Source map

- Main brief p1–2: 15–20 holdings, 3–5 research examples, generalizable engine, three source families, mobile-first Push/Pull.
- Main brief p2–3: prioritized digest, configurable alerts, primary-only research and four-quarter management accountability example.
- Main brief p3–4: narrow reliable scope, efficiency, prototype, repository, actual AI history and covering email.
- Companion p1: 17 categories; p2–3: documents and metric definitions.
- Master plan §§4–9: portfolio, stack, workflow and Day 1 filenames retained with the corrections above.
- NSE instrument evidence: https://www.nseindia.com/companies-listing/corporate-filings-announcements?symbol=ETERNAL ; https://nsearchives.nseindia.com/content/circulars/FAOP70882.pdf ; https://www.niftyindices.com/Press_Release/ind_prs13112025.pdf . Retrieved 27 Oct 2026.
