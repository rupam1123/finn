import type {Citation} from '../terminal/data';

export type Topic='summary'|'guidance'|'cash'|'risks';
export type Passage={module:string;citation:Citation};
export type BriefPoint={text:string;citations:Citation[]};
const topics:Record<Topic,string[]>={summary:['business_snapshot','financial_snapshot','trajectory'],guidance:['forward_guidance','narrative_vs_numbers'],cash:['cash_quality','balance_sheet_governance'],risks:['bull_bear','balance_sheet_governance']};
const stop=new Set('the and for what how why this that with company about tell does are can you please summarise summarize'.split(' '));

/** Extract source text, never reinterpret model candidates as verified facts. */
export function savedPassages(data:any,topic:Topic='summary',question=''):Passage[]{
 const sources=new Map<string,any>((data?.sources||[]).map((s:any)=>[s.sha256,s]));
 const seen=new Set<string>(),items:Passage[]=[];
 for(const module of [...new Set([...topics[topic],...Object.keys(data?.modules||{})])]){
  for(const item of data?.modules?.[module]?.excerpts||[]){
   const c=item.citation,source=sources.get(c?.sha256);if(!source)continue;
   let url:URL;try{url=new URL(c.url)}catch{continue}
   if(!/^[a-f0-9]{64}$/.test(c.sha256)||source.url!==c.url||url.protocol!=='https:'||url.username||url.password||!Number.isInteger(c.page)||c.page<1||(source.page_count&&c.page>source.page_count)||typeof c.quote!=='string'||c.quote.trim().length<20||item.requires_visual_review||c.evidence_type==='page_image')continue;
   const key=JSON.stringify([c.sha256,c.page,c.quote]);if(seen.has(key))continue;seen.add(key);items.push({module,citation:c});if(items.length>=160)break;
  }if(items.length>=160)break;
 }
 const words=[...new Set((question.toLowerCase().match(/[a-z]{3,}/g)||[]).filter(w=>!stop.has(w)))];
 if(words.length){const score=(p:Passage)=>words.filter(w=>new RegExp(`\\b${w}\\b`,'i').test(p.citation.quote)).length;return items.filter(p=>score(p)>0).sort((a,b)=>score(b)-score(a)).slice(0,8)}
 // First show one excerpt per topic so a long transcript cannot fill the brief.
 const preferred=items.filter(p=>topics[topic].includes(p.module));
 const distinct=preferred.filter((p,i)=>preferred.findIndex(s=>s.module===p.module)===i);
 return [...distinct,...preferred.filter(p=>!distinct.includes(p))].slice(0,8);
}

export function excerpt(text:string,max=310){const clean=text.replace(/\s+/g,' ').trim();if(clean.length<=max)return clean;const end=clean.lastIndexOf(' ',max);return clean.slice(0,end>max/2?end:max)+'…'}
export function auditCoverage(data:any){const ledger=data?.say_do?.ledger||[];return {periods:data?.say_do?.observed_periods||0,requested:data?.say_do?.requested_quarters||4,matched:ledger.flatMap((r:any)=>r.comparisons||[]).filter((c:any)=>['within_target','above_target','below_target'].includes(c.status)).length}}
