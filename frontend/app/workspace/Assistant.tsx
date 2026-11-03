'use client';
import {useEffect,useRef,useState} from 'react';
import {MessageCircle,ArrowUpRight,ArrowRight,Sparkles} from 'lucide-react';
import Link from 'next/link';
import Sheet from '../Sheet';import EvidenceButton from '../EvidenceButton';
import {request,time} from '../terminal/data';import {Failure,Skeleton} from '../terminal/ui';
import {useRead} from './cache';import {auditCoverage,excerpt,savedPassages,Topic,BriefPoint} from './assistant-core';

const choices:[Topic,string][]=[['summary','Overview'],['guidance','Promises'],['cash','Cash & debt'],['risks','Watch points']];

export function CompanyBrief({ticker,data,onAsk}:{ticker:string;data:any;onAsk:()=>void}){
 const passage=savedPassages(data)[0],coverage=auditCoverage(data);
 return <section className="company-brief" aria-label="Company brief"><div className="brief-heading"><div><span className="section-label">START HERE</span><h2>Your company brief</h2></div><button className="primary-action" onClick={onAsk}><MessageCircle size={16}/>Ask FINN</button></div>
 <p className="brief-coverage">{data.sources?.length||0} saved documents · {coverage.matched} matched {coverage.matched===1?'comparison':'comparisons'}</p>
 {passage?<div className="brief-excerpt"><small>FROM A PRIMARY SOURCE</small><p>“{excerpt(passage.citation.quote,250)}”</p><EvidenceButton citation={passage.citation}/></div>:<p>No readable primary excerpt is available yet. Open Sources to inspect the saved documents.</p>}
 <div className="brief-next"><Link href={`/research/${encodeURIComponent(ticker)}/say-do`}>Check promises<ArrowUpRight size={14}/></Link><Link href={`/research/${encodeURIComponent(ticker)}/forensics`}>Explore financials<ArrowUpRight size={14}/></Link></div>
 <p className="caption">{coverage.periods}/{coverage.requested} quarters have source coverage. Unmatched promises remain open.</p>
 </section>
}

export default function Assistant({ticker,onClose}:{ticker:string;onClose:()=>void}){
 const saved=useRead<any>(`/api/pull/${encodeURIComponent(ticker)}`),capabilities=useRead<any>('/api/assistant/capabilities');
 const [topic,setTopic]=useState<Topic>('summary'),[input,setInput]=useState(''),[question,setQuestion]=useState(''),[draft,setDraft]=useState<BriefPoint[]|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[model,setModel]=useState('');
 const controller=useRef<AbortController|null>(null);
 useEffect(()=>()=>controller.current?.abort(),[]);
 const data=saved.data?.data,passages=savedPassages(data,topic,question),coverage=auditCoverage(data);
 function reset(next:Topic,q=''){controller.current?.abort();setBusy(false);setError('');setDraft(null);setModel('');setTopic(next);setQuestion(q)}
 async function generate(){if(busy||!capabilities.data?.generation_enabled)return;const active=new AbortController();controller.current=active;setBusy(true);setError('');setDraft(null);
  try{const result=await request<any>(`/api/assistant/${encodeURIComponent(ticker)}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topic,question}),signal:AbortSignal.any([active.signal,AbortSignal.timeout(150000)])});if(!active.signal.aborted){setDraft(result.points||[]);setModel(result.model||'');if(!result.points?.length)setError(result.message||'No supported summary was returned.')}}catch(e){if(!active.signal.aborted)setError(e instanceof Error?e.message:'Summary unavailable.')}finally{if(!active.signal.aborted)setBusy(false)}
 }
 return <Sheet title={`Ask FINN · ${ticker}`} onClose={onClose}>
 <div className="assistant"><p className="assistant-intro">Find the important passages. Open a source whenever you want to check it.</p>
 <div className="assistant-topics" role="group" aria-label="Research questions">{choices.map(([id,title])=><button key={id} aria-pressed={topic===id&&!question} onClick={()=>{setInput('');reset(id)}}>{title}</button>)}</div>
 <form className="assistant-question" onSubmit={e=>{e.preventDefault();reset(topic,input.trim())}}><label className="sr-only" htmlFor="assistant-question">Ask about saved company sources</label><input id="assistant-question" value={input} maxLength={400} onChange={e=>setInput(e.target.value)} placeholder="Ask about growth, guidance, cash…"/><button className="icon-button" aria-label="Find supporting passages" type="submit"><ArrowRight size={18}/></button></form>
 {saved.error&&<Failure message={saved.error} retry={saved.retry}/>}{saved.loading?<Skeleton count={2}/>:data&&<>
 <div className="assistant-answer" aria-live="polite" aria-busy={busy}>
 <div className="section-heading"><h3>{question?`“${excerpt(question,100)}”`:choices.find(([id])=>id===topic)?.[1]}</h3><span className="assistant-mode">{draft?'AI draft · review required':'Saved-source guide'}</span></div>
 {busy&&<p role="status">Reading the selected passages…</p>}{error&&<p role="alert" className="notice">{error}</p>}
 {draft?.length?<><p className="caption">AI summary · verify the cited passages.</p>{draft.map((point,i)=><article className="assistant-point" key={i}><p>{point.text}</p><div className="evidence-list">{point.citations.map((c,j)=><EvidenceButton key={j} citation={c}/>)}</div></article>)}</>:passages.length?<><p className="caption">Source excerpts, shortened for reading. These are not a generated AI answer.</p>{passages.slice(0,3).map((p,i)=><article className="assistant-point" key={`${p.citation.sha256}-${p.citation.page}-${i}`}><p>“{excerpt(p.citation.quote)}”</p><EvidenceButton citation={p.citation}/></article>)}</>:<p>No matching readable passage in the saved sources. Try a broader question or open Sources.</p>}
 </div>
 {capabilities.data?.generation_enabled&&passages.length>0&&<div className="assistant-generate"><button className="primary-action" onClick={generate} disabled={busy}><Sparkles size={16}/>{busy?'Summarising…':'Summarise with AI'}</button><small>Uses your configured model and API quota.</small></div>}
 <details className="quiet-disclosure"><summary>Coverage & limitations</summary><p>Research saved {time(saved.data.fetched_at)}. {data.sources?.length||0} primary documents. {coverage.periods}/{coverage.requested} quarters with sources; {coverage.matched} matched numerical comparisons. Source dates may differ.</p><p>{capabilities.data?.generation_enabled?'AI uses only the supplied saved passages. Responses are drafts, not independently verified conclusions.':'AI generation is off in this session. The source guide searches existing primary excerpts without a model request.'} Missing evidence is not a verdict. No investment advice.</p>{model&&<p>Model: {model}</p>}<p>Your questions and answers are not saved by FINN. An explicit AI request sends the question and selected excerpts to the configured provider.</p></details>
 <Link className="text-button" href={`/research/${encodeURIComponent(ticker)}/filings`} onClick={onClose}>Open all sources<ArrowUpRight size={14}/></Link>
 </>}
 </div></Sheet>
}
