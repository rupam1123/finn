"use client";
import { useEffect, useRef, useState } from "react";
import EvidenceButton, {sourceLink} from "./EvidenceButton";
import CompanySearch from "./CompanySearch";
type Evidence = {
  citation: {
    url: string;
    sha256: string;
    page: number;
    quote: string;
    observed_at: string;
    evidence_type?: string;
  };
  requires_visual_review: boolean;
};
type PrimaryFact = {metric: string; value: string; unit: string; period_end: string; basis: string;
  requires_visual_review?: boolean; citations: Evidence["citation"][]};
type Target = {metric: string; target_period: string; lower: string; upper: string|null; comparison_operator?:string; basis: string;
  speaker_verified: boolean; horizon_verified: boolean; citation: Evidence["citation"]};
type Research = {
  symbol: string;
  status: string;
  source_mode: string;
  modules: Record<string, { status: string; excerpts: Evidence[]; facts?: PrimaryFact[];
    targets?: Target[]; bull?: {claim:string;citations:Evidence["citation"][]}[];
    bear?: {claim:string;citations:Evidence["citation"][]}[];
    analysis?: {claim:string;status:string;citation:Evidence["citation"];citations?:Evidence["citation"][]}[] }>;
  say_do: {
    observed_periods: number;
    requested_quarters: number;
    ledger: {
      period_end: string;
      status: string;
      reason: string;
      comparisons?: {status:string;reason:string;metric?:string;target?:{lower:string;upper:string|null;operator?:string};actual?:string;citations:Evidence["citation"][]}[];
      extracted_guidance?: Target[];
      model_assessments?: {assessment:string;status:string;citations:Evidence["citation"][]}[];
      said?: Evidence[];
      delivered?: Evidence[];
    }[];
  };
  annual_forensics?: {
    source_url: string;
    status: string;
    periods: {
      period_end: string;
      cash_conversion: {
        status: string;
        value?: string | null;
        citations?: Evidence["citation"][];
      };
    }[];
    leverage: {
      period_end: string;
      debt_to_equity: string | null;
      definition: string;
      citations: Evidence["citation"][];
    }[];
  }[];
  source_errors: { stage: string; error: string }[];
};
type JobResponse = {id:string; symbol:string; status:string; payload:{stage?:string}};
type SavedResearch = {data:Research; fetched_at:string; cache_expired:boolean};
const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
export default function PullWorkspace() {
  const [ticker, setTicker] = useState("INFY"),
    [data, setData] = useState<Research | null>(null),
    [status, setStatus] = useState("");
  const [job, setJob] = useState<string | null>(null);
  const generation = useRef(0), pending = useRef<AbortController | null>(null);
  const [requesting, setRequesting] = useState(false);
  useEffect(() => () => {generation.current++; pending.current?.abort();}, []);
  useEffect(() => {
    if (!job) return;
    const request = generation.current;
    const controller = new AbortController();
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const current = () => active && request === generation.current;
    async function poll() {
      let terminal = false;
      try {
        const response = await fetch(`${base}/api/pull-jobs/${job}`, {
          signal: AbortSignal.any([controller.signal, AbortSignal.timeout(10000)]),
        });
        if (!response.ok) throw Error();
        const value = await response.json() as JobResponse;
        if (!current()) return;
        setStatus(
          `${value.status}: ${value.payload.stage || "waiting for research"}`,
        );
        if (!["queued", "running"].includes(value.status)) {
          terminal = true;
          if (["failed", "unavailable"].includes(value.status)) {
            setStatus("Research could not finish. Retry or inspect source availability.");
            setJob(null);
            return;
          }
          const result = await fetch(
            `${base}/api/pull/${encodeURIComponent(value.symbol)}`,
            {signal: AbortSignal.any([controller.signal, AbortSignal.timeout(10000)])},
          );
          if (!result.ok) throw Error();
          const saved = await result.json() as SavedResearch;
          if (!current()) return;
          setData(saved.data);
          setJob(null);
        }
      } catch {
        if (current()) {
          setStatus("Could not check research progress. Retry shortly.");
          if (terminal) setJob(null);
        }
      } finally {
        // Schedule after completion: slow responses cannot create overlapping polls.
        if (current() && !terminal) timer = setTimeout(poll, 2000);
      }
    }
    timer = setTimeout(poll, 2000);
    return () => { active = false; controller.abort(); clearTimeout(timer); };
  }, [job]);
  async function research(refresh = false, selected = ticker) {
    const request = ++generation.current;
    pending.current?.abort(); const controller = new AbortController(); pending.current = controller;
    setRequesting(true);
    setData(null);
    setJob(null);
    setStatus("Checking saved research…");
    try {
      const url = `${base}/api/pull/${encodeURIComponent(selected.trim())}`;
      const response = await fetch(url, { signal: AbortSignal.any([controller.signal, AbortSignal.timeout(10000)]) });
      if (request !== generation.current) return;
      if (response.ok && !refresh) {
        const saved = await response.json() as SavedResearch;
        if (request !== generation.current) return;
        setData(saved.data);
        setStatus(
          `Saved research · generated ${saved.fetched_at}${saved.cache_expired ? " · refresh due" : ""}`,
        );
        return;
      }
      if (!response.ok && response.status !== 404) throw Error();
      const queued = await fetch(`${url}/jobs?refresh=${refresh}`, {
        method: "POST",
        signal: AbortSignal.any([controller.signal, AbortSignal.timeout(10000)]),
      });
      if (!queued.ok) throw Error();
      const value = await queued.json() as JobResponse;
      if (request !== generation.current) return;
      setJob(value.id);
      setStatus("Research queued. Progress will appear here.");
    } catch {
      if (request === generation.current)
        setStatus(
          "Research unavailable. Check the symbol and backend connection.",
        );
    } finally {if (request === generation.current) setRequesting(false);}
  }
  return (
    <section className="mt-12 border-t border-white/15 pt-8">
      <h2 className="text-2xl">Forensic Workspace</h2>
      <p className="mt-3 text-sm text-white/60">
        Primary evidence with explicit coverage gaps. Excerpts require review
        before supporting an investment conclusion.
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void research();
        }}
        className="mt-4 flex gap-2"
      >
        <CompanySearch value={ticker} onChange={setTicker} onSelect={symbol => void research(false, symbol)}/>
        <button className="primary-action" disabled={requesting}>{requesting ? "Checking…" : "Research"}</button>
      </form>
      <div className="showcase-pills" aria-label="Showcase companies">{["TITAN","COFORGE","SYNGENE","SONACOMS","CAMS"].map(symbol =>
        <button type="button" key={symbol} onClick={() => {setTicker(symbol); void research(false, symbol);}}>{symbol}</button>)}</div>
      <p role="status" className="mt-3 text-sm text-amber-100">
        {status}
      </p>
      {data && (
        <>
          <button disabled={requesting || !!job} onClick={() => void research(true)} className="mt-3 rounded border border-emerald-200/50 px-4 py-2 text-sm">Refresh sources</button>
          <p className="mt-3">
            {data.symbol} · {data.status} ·{" "}
            {data.source_mode.replaceAll("_", " ")}
          </p>
          <div className="research-grid">
          <section className="research-card ledger-card" aria-labelledby="ledger-heading"><h3 id="ledger-heading" className="font-semibold">Four-quarter Say–Do coverage</h3>
          <p>
            {data.say_do.observed_periods} / {data.say_do.requested_quarters}{" "}
            periods observed
          </p>
          {data.say_do.ledger.map((row) => (
            <details
              key={row.period_end}
              className="mt-3 rounded border border-white/15 p-3"
            >
              <summary>
                {row.period_end} · {row.status}
              </summary>
              <p className="mt-2 text-sm text-amber-100">{row.reason}</p>
              {row.comparisons?.map((comparison,i)=><div key={i} className="mt-3"><strong>{comparison.status.replaceAll("_"," ")}</strong><p>{comparison.reason}</p>{comparison.target && <p>{comparison.metric?.replaceAll("_"," ")} · Target {comparison.target.operator==='at_least'?'≥ ':''}{comparison.target.lower}{comparison.target.upper!==null?'–'+comparison.target.upper:''}% · Reported {comparison.actual}%</p>}<EvidenceList items={comparison.citations.map(citation=>({citation,requires_visual_review:false}))}/></div>)}
              {row.model_assessments?.map((item,i)=><div key={i} className="mt-3"><strong>AI assessment · {item.status.replaceAll("_"," ")}</strong><p>{item.assessment}</p><EvidenceList items={item.citations.map(citation=>({citation,requires_visual_review:false}))}/></div>)}
              <h4 className="mt-3">Earlier commentary candidates</h4>
              <EvidenceList items={row.said || []} />
              <h4 className="mt-3">Delivered-period evidence candidates</h4>
              <EvidenceList items={row.delivered || []} />
            </details>
          ))}
          {renderModules(data, ["narrative_vs_numbers", "forward_guidance"])}
          </section>
          <section className="research-card" aria-labelledby="snapshot-heading"><h3 id="snapshot-heading">Snapshot &amp; trajectory</h3>{renderModules(data, ["business_snapshot", "financial_snapshot", "trajectory"])}</section>
          <section className="research-card" aria-labelledby="cash-heading"><h3 id="cash-heading">Cash quality &amp; balance sheet</h3>
          {data.annual_forensics?.map((annual, i) => (
            <details
              key={i}
              className="mt-4 rounded border border-white/15 p-3"
            >
              <summary>Annual cash and leverage · {annual.status}</summary>
              <a
                href={sourceLink(annual.source_url)}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs underline"
              >
                Source annual report
              </a>
              <p className="mt-2 text-xs text-amber-100">
                Figures remain specific to this report. Comparative values may
                differ between reports. Cash conversion uses total consolidated
                profit; borrowing-to-equity excludes leases.
              </p>
              {annual.periods.map((row) => (
                <div key={row.period_end} className="mt-3">
                  <p>
                    {row.period_end} · CFO / PAT:{" "}
                    {row.cash_conversion.value != null
                      ? Number(row.cash_conversion.value).toFixed(3) + "×"
                      : row.cash_conversion.status}
                  </p>
                  <EvidenceList
                    items={(row.cash_conversion.citations || [])
                      .slice(0, 1)
                      .map((citation) => ({
                        citation,
                        requires_visual_review: false,
                      }))}
                  />
                </div>
              ))}
              {annual.leverage.map((row) => (
                <div key={row.period_end} className="mt-2">
                  {row.period_end} · Borrowings / equity:{" "}
                  {row.debt_to_equity != null
                    ? Number(row.debt_to_equity).toFixed(3) + "×"
                    : "undefined"}{" "}
                  <EvidenceList items={row.citations.map(citation => ({citation, requires_visual_review: false}))}/>

                </div>
              ))}
            </details>
          ))}
          {renderModules(data, ["cash_quality", "balance_sheet_governance"])}
          </section>
          <section className="research-card" aria-labelledby="cases-heading"><h3 id="cases-heading">Evidence for growth &amp; caution</h3>{renderModules(data, ["bull_bear"])}</section>
          </div>
          {data.source_errors.length > 0 && (
            <details className="mt-4">
              <summary>Source failures ({data.source_errors.length})</summary>
              {data.source_errors.map((error, i) => (
                <p className="mt-2 text-xs" key={i}>
                  {error.stage}: {error.error}
                </p>
              ))}
            </details>
          )}
        </>
      )}
    </section>
  );
}

function EvidenceList({items}: {items: Evidence[]}) {
  return <div className="evidence-list">{items.length === 0 && <p className="text-sm text-white/50">Comparable evidence unavailable.</p>}
    {items.slice(0, 3).map((item, i) => <EvidenceButton key={i} citation={item.citation} requiresVisualReview={item.requires_visual_review}/>) }
    {items.length > 3 && <details className="mt-2 text-sm"><summary>{items.length - 3} more sources</summary>
      {items.slice(3).map((item, i) => <EvidenceButton key={i} citation={item.citation} requiresVisualReview={item.requires_visual_review}/>)}</details>}
  </div>;
}

function renderModules(data: Research, names: string[]) {
  if (!names.some(name => data.modules[name])) return <p className="mt-3 text-sm text-white/60">No supported source data available for this view.</p>;
  return <>          {Object.entries(data.modules).filter(([name]) => names.includes(name)).map(([name, module]) => (
            <details
              key={name}
              className="mt-4 rounded border border-white/15 p-4"
            >
              <summary>
                {name.replaceAll("_", " ")} · {module.status}
              </summary>
              {module.facts?.filter((fact): fact is PrimaryFact => typeof fact.metric === "string").map((fact,i)=><div key={i} className="mt-3 text-sm">
                <p>{fact.metric.replaceAll("_"," ")} · {fact.value} {fact.unit} · {fact.period_end} · {fact.basis}</p>
                {fact.requires_visual_review && <p className="text-amber-100">Visual review required</p>}
                <EvidenceList items={fact.citations.map(citation=>({citation,requires_visual_review:!!fact.requires_visual_review}))}/>
              </div>)}
              {module.targets?.map((target,i)=><div key={i} className="mt-3 text-sm">
                <p>{target.metric.replaceAll("_"," ")} · {target.comparison_operator==='at_least'?'≥ ':''}{target.lower}{target.upper!==null?'–'+target.upper:''}% · {target.target_period} · {target.basis.replaceAll("_"," ")}</p>
                {(!target.speaker_verified || !target.horizon_verified) && <p className="text-amber-100">Speaker or target period needs review</p>}
                <EvidenceList items={[{citation:target.citation,requires_visual_review:false}]}/>
              </div>)}
              {([['Evidence for growth',module.bull],['Evidence for caution',module.bear]] as const).map(([title,items])=>items && <div key={title} className="mt-3"><h4>{title}</h4>{items.length===0 && <p className="text-sm text-white/50">No supported comparison available.</p>}{items.map((item,i)=><div key={i} className="mt-2"><p>{item.claim}</p><EvidenceList items={item.citations.map(citation=>({citation,requires_visual_review:false}))}/></div>)}</div>)}
              {module.analysis?.map((item,i)=><div key={i} className="mt-3 text-sm"><p>{item.claim}</p><p className="text-xs text-amber-100">AI analysis · verify the supporting evidence</p><EvidenceList items={(item.citations || [item.citation]).map(citation=>({citation,requires_visual_review:false}))}/></div>)}
              <EvidenceList items={module.excerpts || []}/>
            </details>
          ))}
</>;
}
