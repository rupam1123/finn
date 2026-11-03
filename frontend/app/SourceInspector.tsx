"use client";

import {useEffect, useRef, useState} from "react";
import {time} from "./terminal/data";
import {sourceLink} from "./EvidenceButton";

type Attempt = {status: string; finished_at: string | null; started_at: string; details: {error?: string}};
type Snapshot = {fetched_at: string; cache_age_seconds: number; cache_expired?: boolean;
  last_attempt?: Attempt | null;
  source_status?: Record<string, {available: boolean; fetched_at: string | null; cache_expired: boolean; last_attempt: Attempt | null;
    freshness?: {status: string; actual_session: string | null}}>;
  data: {
  symbol: string; company_name: string; basis: string; source_url: string;
  tables: Record<string, unknown>; documents: {kind: string; url: string; context: string}[];
  warnings: string[];
}};

export default function SourceInspector() {
  const [ticker, setTicker] = useState("TCS");
  const [data, setData] = useState<Snapshot | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const generation = useRef(0), pending = useRef<AbortController | null>(null);
  useEffect(() => () => {generation.current++; pending.current?.abort();}, []);
  async function inspect(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const request = ++generation.current; pending.current?.abort();
    const controller = new AbortController(); pending.current = controller;
    setLoading(true); setError(""); setData(null);
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE || "";
      const response = await fetch(`${base}/api/company/${encodeURIComponent(ticker.trim())}`, {signal: AbortSignal.any([controller.signal, AbortSignal.timeout(10000)])});
      if (!response.ok) {
        const body = await response.json().catch(() => null) as {detail?: unknown} | null;
        if (request !== generation.current) return;
        setError(response.status === 404 ? "This company has not been ingested yet. Use the Research tab to request primary research for its NSE symbol." :
          response.status === 422 && typeof body?.detail === "string" ? body.detail :
          "Source data is unavailable. Check the backend and try again.");
        return;
      }
      const saved = await response.json() as Snapshot;
      if (request === generation.current) setData(saved);
    } catch {
      if (request === generation.current) setError("Cannot reach the ingestion API. Start the backend to inspect saved source data.");
    } finally { if (request === generation.current) setLoading(false); }
  }

  return <section aria-label="Saved source inspection">
    <form id="source-form" onSubmit={inspect} className="mt-9">
      <label htmlFor="ticker" className="text-sm text-white/70">NSE symbol</label>
      <div className="mt-2 flex gap-2"><input id="ticker" value={ticker} onChange={e => setTicker(e.target.value)} maxLength={30} required autoCapitalize="characters" spellCheck={false} className="min-w-0 flex-1 rounded-lg border border-white/20 bg-white/5 px-4 py-3 uppercase"/><button disabled={loading} className="rounded-lg bg-emerald-200 px-5 py-3 font-semibold text-emerald-950 disabled:opacity-50">{loading ? "Loading…" : "Inspect"}</button></div>
      <p className="mt-3 text-xs text-white/40">Inspect cache age and provider status separately from primary research.</p>
    </form>
    <div aria-live="polite">
      {error && <p role="alert" className="mt-6 rounded-lg border border-amber-200/30 p-4 text-sm text-amber-100">{error}</p>}
      {data && <section id="company-snapshot" className="mt-8 rounded-xl border border-white/15 p-5">
        <p className="text-xs uppercase tracking-widest text-emerald-200">{data.data.symbol} · {data.data.basis}</p>
        <h2 className="mt-2 text-xl">{data.data.company_name}</h2>
        <p className="mt-4 text-sm text-white/60">{Object.keys(data.data.tables||{}).length} staging tables · {(data.data.documents||[]).length} document links</p>
        <p className="mt-2 text-xs leading-relaxed text-amber-100/80">Screener is a discovery source. These tables are not yet verified against primary filings and do not support research conclusions.</p>
        <p className="mt-3 text-xs text-white/40">Fetched {time(data.fetched_at)} · cached snapshot</p>
        <p className="mt-2 text-xs text-white/60">Source age: {Math.floor(data.cache_age_seconds / 60)} minutes{data.cache_expired ? " · refresh due" : " · within cache lifetime"}</p>
        {data.cache_expired && <p role="status" className="mt-3 text-sm text-amber-100">This saved snapshot is past its refresh interval. Run ingestion to check the source again.</p>}
        {data.last_attempt && !["ok", "cached", "text_extracted"].includes(data.last_attempt.status) &&
          <p role="alert" className="mt-3 text-sm text-amber-100">{data.last_attempt.status === "refreshing" ? "Refresh started; completion has not been recorded." : "Latest refresh did not succeed. Showing the last successful snapshot."}
            {data.last_attempt.details?.error && <> {data.last_attempt.details?.error}</>}
            <> Attempt: {time(data.last_attempt.finished_at || data.last_attempt.started_at)}.</>
          </p>}
        {Object.entries(data.source_status || {}).map(([kind, source]) => {
          const label = kind === "market" ? "Market data" : kind === "filings_coverage" ? "Filings" : "Primary transcript";
          const status = source.last_attempt?.status;
          const failed = status && !["ok", "cached", "text_extracted"].includes(status);
          return <p key={kind} className="mt-3 text-xs text-white/60">
            {label}: {failed ? status : source.available ? "saved" : "not ingested"}
            {source.freshness && <> · session {source.freshness.actual_session || "unknown"} · {source.freshness.status}</>}
            {source.fetched_at && <> · observed {time(source.fetched_at)}</>}
            {source.cache_expired && source.available && <> · refresh due</>}
            {failed && source.available && <> · retaining previous data</>}
            {failed && source.last_attempt?.details?.error && <>. {source.last_attempt.details.error}</>}
          </p>;
        })}
        {(data.data.warnings||[]).map(w=><p className="caption" key={w}>{w}</p>)}
        {!Object.keys(data.data.tables||{}).length&&<p className="caption">No compiled financial tables are included in this snapshot.</p>}
        {Object.entries(data.data.tables||{}).map(([key,table])=><StagingTable key={key} name={key} value={table}/>)}
        {sourceLink(data.data.source_url)&&<p><a className="text-button" href={data.data.source_url} target="_blank" rel="noopener noreferrer">Open staging source</a></p>}
        <ul className="mt-5 space-y-4">{(data.data.documents||[]).filter(d => ["annual_report", "transcript"].includes(d.kind) && sourceLink(d.url)).slice(0,5).map(d => <li key={d.url}><a className="text-sm underline decoration-white/30" href={d.url} target="_blank" rel="noopener noreferrer">{d.kind.replaceAll("_", " ")} — {d.context}</a></li>)}</ul>
      </section>}
    </div>
  </section>;
}

function StagingTable({name,value}:{name:string;value:unknown}){const t=value as {basis?:string;periods?:{label:string}[];rows?:{label:string;unit:string;values:unknown[]}[]};if(!t||!Array.isArray(t.rows)||!Array.isArray(t.periods))return null;return <details className="staging-table"><summary>{name.replaceAll('_',' ')} · compiled staging</summary><p className="caption">{t.basis||'Basis unavailable'} · Screener compilation, not primary verified. Each row retains its reported unit.</p><div className="table-scroll" tabIndex={0} role="region" aria-label={`${name.replaceAll('_',' ')} compiled staging, scroll horizontally`}><table aria-label={`${name.replaceAll('_',' ')} compiled staging`}><thead><tr><th scope="col">Metric / unit</th>{t.periods.map((p,i)=><th scope="col" key={i}>{p.label}</th>)}</tr></thead><tbody>{t.rows.map((r,i)=><tr key={i}><th scope="row">{r.label}<small>{r.unit?.replaceAll('_',' ')}</small></th>{(r.values||[]).map((v,j)=><td key={j}>{v==null?'—':typeof v==='object'?String((v as {raw?:string;value?:unknown}).raw??(v as {value?:unknown}).value??'—'):String(v)}</td>)}</tr>)}</tbody></table></div></details>}
