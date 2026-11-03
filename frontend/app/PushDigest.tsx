"use client";

import DisclosureSummary from './DisclosureSummary';
import {useEffect, useRef, useState} from "react";
import EvidenceButton, {sourceLink} from "./EvidenceButton";
import Sheet from "./Sheet";

type Evidence = {url: string; page: number; quote: string; sha256: string; evidence_type?:string};
type Change = {percent: number | null; state: string};
type Row = {metric: string; values: {current: string | null; previous_quarter: string | null; year_ago: string | null} | null;
  qoq: Change; yoy: Change; evidence: Evidence | null};
type Enrichment = {kind: string; status: string; basis?: string; unit?: string; currency?: string;
  periods?: {current: string; previous_quarter: string; year_ago: string}; rows?: Row[]; warnings: string[];
  events?: {name: string; role: string; action: string; effective_date: string; evidence: Evidence;
    profile: {text: string; source_type: string; independently_verified: boolean; evidence: Evidence} | null}[]};
type Card = {id: string; symbol: string; title: string; published_at: string; observed_at: string; document_url: string | null;
  classification: {category: string; materiality: number; reason: string; review_required: boolean; method: string; model_status: string};
  analysis_status: string; analyzed_at: string | null; enrichment: Enrichment | null;
  document: {fetched_at: string; sha256: string} | null; last_attempt: {status: string} | null};
type Source = {available: boolean; status: string; fetched_at?: string; cache_expired?: boolean;
  last_attempt?: {status: string} | null; freshness?: {status: string; actual_session: string}};
type Digest = {window: string; since: string; as_of: string; status: string; warnings: string[];
  counts: {scanned: number; surfaced: number; buried: number; review_required: number; processed: number; unprocessed: number; market_alerts: number};
  cards: Card[]; buried: Card[]; coverage: Record<string, {filings: Source; market: Source}>;
  market_alerts: {id: string; symbol: string; session: string; context: string; observation_mode: string;
    indicators: {return_1d_pct: number | null; volume_ratio_20d: number | null};
    nearby_filings: {id: string; title: string}[]; retrospective_filings: {id: string; title: string; reason: string}[];
    last_attempt: {status: string} | null}[]};

function percent(value: Change) {return value.percent === null ? value.state.replaceAll("_", " ") : `${value.percent.toFixed(2)}%`;}
function EvidenceLink({e}: {e: Evidence}) {return <EvidenceButton citation={e}/>;}
const categories = ["results","M&A","fund_raise","management_change","litigation","insider_trading","earnings_call","investor_meetings","credit_rating","dividend","bonus_split","capex","press_release","postal_ballot","agm_egm","pledging","unclassified"];
const windows = [["1d","24 hours"],["latest","Latest session"],["3d","3 days"],["7d","7 days"],["30d","30 days"]];
function FilingCard({card}: {card: Card}) {
  const c = card.classification, e = card.enrichment;
  return <article className="rounded-xl border border-white/15 p-4" data-testid="filing-card">
    <p className="text-xs text-emerald-200">{card.symbol} · {c.category.replaceAll("_", " ")} · score {c.materiality}/100</p>
    <h3 className="mt-2 font-medium">{card.title}</h3>
    <p className="mt-2 text-xs text-white/50">Published {new Date(card.published_at).toLocaleString()} · observed {new Date(card.observed_at).toLocaleString()}</p>
    {card.document && <p className="mt-1 text-xs text-white/50">PDF observed {new Date(card.document.fetched_at).toLocaleString()}{card.analyzed_at && ` · analysis generated ${new Date(card.analyzed_at).toLocaleString()}`}</p>}
    <p className="mt-2 text-sm text-amber-100">{c.review_required ? "Review required. " : ""}{c.reason}</p>
    <p className="mt-2 text-xs text-white/50">{c.method.replaceAll("_", " ")} · AI: {c.model_status.replaceAll("_", " ")} · analysis: {card.analysis_status.replaceAll("_", " ")}</p>
    {card.last_attempt && !["processed", "cached"].includes(card.last_attempt.status) && <p className="mt-2 text-xs text-amber-100">Latest analysis attempt: {card.last_attempt.status}. {card.document ? "Showing previously saved evidence." : "Primary evidence is unavailable."}</p>}
    {sourceLink(card.document_url) && <a className="mt-3 inline-block text-sm underline decoration-white/30" href={card.document_url!} target="_blank" rel="noopener noreferrer">Open filing</a>}
    {e && <div className="mt-4 border-t border-white/10 pt-3">
      <p className="text-xs text-white/70">Enrichment: {e.status.replaceAll("_", " ")}</p>
      {e.periods && <p className="mt-2 text-xs text-white/60">{e.basis} · {e.currency} {e.unit} · quarters ending {e.periods.current}, {e.periods.previous_quarter}, {e.periods.year_ago}</p>}
      {!!e.rows?.length && <div className="mt-3 financial-table" tabIndex={0} role="region" aria-label="Quarterly results; scroll horizontally"><table className="w-full text-left text-xs"><thead><tr>{["Metric", "Current", "Previous", "Year ago", "QoQ", "YoY"].map(h => <th scope="col" className="p-2" key={h}>{h}</th>)}</tr></thead><tbody>{e.rows.map(row => <tr key={row.metric} className="border-t border-white/10">
        <td className="p-2 uppercase">{row.metric}</td><td className="p-2">{row.values?.current ?? "—"}</td><td className="p-2">{row.values?.previous_quarter ?? "—"}</td><td className="p-2">{row.values?.year_ago ?? "—"}</td><td className="p-2">{percent(row.qoq)}</td><td className="p-2">{percent(row.yoy)}</td>
      </tr>)}</tbody></table>{e.rows.filter(r => r.evidence).map(r => <EvidenceLink key={r.metric} e={r.evidence!}/>)}</div>}
      {e.events?.map(event => <div className="mt-3" key={event.name+event.action}><p className="font-medium">{event.name}</p><p className="text-sm text-white/70">{event.role} · {event.action} · effective {event.effective_date}</p><EvidenceLink e={event.evidence}/>
        {event.profile && <details className="mt-2 text-sm text-white/70"><DisclosureSummary>Issuer-provided profile · not independently verified</DisclosureSummary><p className="mt-2">{event.profile.text}</p><EvidenceLink e={event.profile.evidence}/></details>}</div>)}
      {e.warnings.map(w => <p key={w} className="mt-2 text-xs text-amber-100/80">{w}</p>)}
    </div>}
  </article>;
}

export default function PushDigest() {
  const [window, setWindow] = useState("1d"), [price, setPrice] = useState("3"), [volume, setVolume] = useState("2");
  const [watched,setWatched]=useState(["results","M&A","management_change","litigation","fund_raise","capex","pledging"]);
  const [data, setData] = useState<Digest | null>(null), [error, setError] = useState(""), [loading, setLoading] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const generation = useRef(0), pending = useRef<AbortController | null>(null);
  useEffect(() => () => {generation.current++; pending.current?.abort();}, []);
  async function load(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); const request = ++generation.current; pending.current?.abort();
    const controller = new AbortController(); pending.current = controller;
    setLoading(true); setData(null); setError("");
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
      const query = new URLSearchParams({window, price_threshold: price, vol_threshold: volume,watch_categories:watched.join(',')});
      const response = await fetch(`${base}/api/push/digest?${query}`, {signal: AbortSignal.any([controller.signal, AbortSignal.timeout(10000)])});
      if (!response.ok) throw new Error(response.status === 422 ? "Choose valid alert thresholds and a supported window." : "Digest API is unavailable. Try again after checking the backend.");
      const result = await response.json() as Digest;
      if (!result.counts || !Array.isArray(result.cards) || !Array.isArray(result.market_alerts)) throw new Error("Digest response is incomplete.");
      if (request === generation.current) setData(result);
    } catch (err) {if (request === generation.current) setError(err instanceof Error && err.message.includes("Digest") || err instanceof Error && err.message.includes("Choose") ? err.message : "Cannot reach the digest API. Check the backend and retry.");}
    finally {if (request === generation.current) setLoading(false);}
  }
  return <section className="mt-12 border-t border-white/15 pt-8" aria-labelledby="digest-heading">
    <h2 id="digest-heading" className="text-2xl">Signal Inbox</h2>
    <p className="mt-3 text-sm text-white/60">Inspect cached filings and EOD alerts. This loads saved analysis; it does not refresh the exchanges.</p>
    <form id="digest-form" onSubmit={load} className="mt-5 space-y-4">
      <fieldset className="window-pills"><legend className="sr-only">Saved filing window</legend>{windows.map(([value,label]) =>
        <button type="button" key={value} data-window={value} aria-pressed={window === value} onClick={() => setWindow(value)}>{label}</button>)}</fieldset>
      <div className="flex flex-wrap items-center gap-3"><button type="button" className="action-link" aria-haspopup="dialog" onClick={() => setFiltersOpen(true)}>Alert settings</button>
        <p className="text-xs text-white/60">Price ±{price}% · volume &gt;{volume}× · {watched.length} watched categories</p></div>
      <button id="load-digest" disabled={loading} className="primary-action w-full">{loading ? "Loading digest…" : "Load saved digest"}</button>
    </form>
    {filtersOpen && <Sheet title="Alert settings" onClose={() => setFiltersOpen(false)}>
      <form onSubmit={event => {setFiltersOpen(false); void load(event);}} className="space-y-5">
        <p className="text-sm text-white/60">Settings filter saved observations. They do not refresh sources or subscribe to notifications.</p>
        <label className="block">Adjusted price move ±{price}%
          <input aria-label="Price threshold slider" type="range" min="0.5" max="100" step="0.5" value={price} onChange={e => setPrice(e.target.value)} className="mt-3 w-full"/>
          <input aria-label="Price threshold" type="number" min="0.01" max="100" step="0.01" required value={price} onChange={e => setPrice(e.target.value)} className="setting-number"/>
        </label>
        <label className="block">Volume above {volume}× prior 20 sessions
          <input aria-label="Volume threshold slider" type="range" min="0.5" max="100" step="0.5" value={volume} onChange={e => setVolume(e.target.value)} className="mt-3 w-full"/>
          <input aria-label="Volume threshold" type="number" min="0.01" max="100" step="0.01" required value={volume} onChange={e => setVolume(e.target.value)} className="setting-number"/>
        </label>
        <fieldset className="category-watches"><legend>Announcement alert categories</legend>{categories.map(category =>
          <label key={category}><input type="checkbox" checked={watched.includes(category)} onChange={e => setWatched(e.target.checked ? [...watched,category] : watched.filter(c => c !== category))}/>{category.replaceAll("_"," ")}</label>)}</fieldset>
        <p className="text-xs text-white/60">Materiality and review rules remain active. Unknown documents are not hidden merely because a category is unwatched.</p>
        <button className="primary-action w-full">Apply and load digest</button>
      </form>
    </Sheet>}
    <div aria-live="polite">{error && <p role="alert" className="mt-4 text-sm text-amber-100">{error}</p>}
      {data && <div className="mt-6" data-testid="digest-result">
        <p className="font-medium">{data.counts.scanned} scanned · {data.counts.surfaced} surfaced · {data.counts.buried} buried</p>
        <p className="mt-2 text-xs text-white/60">{data.counts.review_required} need review · {data.counts.unprocessed} not processed · {data.counts.market_alerts} market alerts</p>
        <p className="mt-2 text-xs text-white/50">{new Date(data.since).toLocaleString()} – {new Date(data.as_of).toLocaleString()} · {data.window}</p>
        {data.warnings.map(w => <p className="mt-2 text-xs text-amber-100/80" key={w}>{w}</p>)}
        <details className="my-5 text-xs text-white/60"><DisclosureSummary className="cursor-pointer">Source coverage and refresh status · {Object.keys(data.coverage).length} holdings</DisclosureSummary>{Object.entries(data.coverage).map(([symbol,s]) => <p key={symbol} className="mt-3">{symbol}: filings {s.filings.last_attempt?.status || s.filings.status}{s.filings.fetched_at && ` · observed ${new Date(s.filings.fetched_at).toLocaleString()}`}{s.filings.cache_expired && " · refresh due"}; market {s.market.freshness?.status || s.market.status}{s.market.freshness && ` · session ${s.market.freshness.actual_session}`}{s.market.last_attempt && ` · last refresh ${s.market.last_attempt.status}`}</p>)}</details>
        {data.counts.scanned === 0 && <p className="my-4 text-sm text-amber-100">No filings in the selected saved window. Check coverage before interpreting this as no events.</p>}
        <div className="space-y-4">{data.cards.map(c => <FilingCard key={c.id} card={c}/>)}</div>
        <details className="mt-5 text-sm text-white/60"><DisclosureSummary className="cursor-pointer">Routine filings ({data.buried.length})</DisclosureSummary><div className="mt-4 space-y-3">{data.buried.map(c => <FilingCard key={c.id} card={c}/>)}</div></details>
        {data.market_alerts.length > 0 && <div className="mt-8 space-y-4"><h3 className="text-lg">EOD market alerts</h3>{data.market_alerts.map(a => <article key={a.id} className="rounded-xl border border-white/15 p-4 text-sm"><p>{a.symbol} · session {a.session}</p><p className="mt-2 text-white/70">Adjusted 1D return {a.indicators.return_1d_pct?.toFixed(2) ?? "unavailable"}% · volume {a.indicators.volume_ratio_20d?.toFixed(2) ?? "unavailable"}× prior 20 sessions</p><p className="mt-2 text-xs text-amber-100">{a.context.replaceAll("_", " ")} · {a.observation_mode}. Nearby filings do not establish causation.</p><p className="mt-2 text-xs text-white/60">{a.nearby_filings.length} known by cutoff · {a.retrospective_filings.length} retrospective links{a.last_attempt && ` · latest source refresh: ${a.last_attempt.status}`}</p><details className="mt-2 text-xs"><DisclosureSummary>Related filing titles</DisclosureSummary>{a.nearby_filings.map(f => <p key={f.id}>{f.title} · known by cutoff</p>)}{a.retrospective_filings.map(f => <p key={f.id}>{f.title} · {f.reason.replaceAll("_", " ")}</p>)}</details></article>)}</div>}
      </div>}
    </div>
  </section>;
}
