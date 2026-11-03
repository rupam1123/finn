export const API = (process.env.NEXT_PUBLIC_API_BASE || '').replace(/\/$/, '');
export const categories=['results','M&A','fund_raise','management_change','litigation','insider_trading','earnings_call','investor_meetings','credit_rating','dividend','bonus_split','capex','press_release','postal_ballot','agm_egm','pledging','unclassified'];
export async function request<T>(path:string, options:RequestInit={}) : Promise<T> {
  const response=await fetch(`${API}${path}`,{...options,signal:options.signal || AbortSignal.timeout(20000)});
  if(!response.ok){const body=await response.json().catch(()=>null) as {detail?:string|{message?:string}}|null;const detail=typeof body?.detail==='string'?body.detail:body?.detail?.message;
    throw new Error(detail || (response.status===404?'No saved data available.':`Source service returned ${response.status}. Please retry.`));}
  return response.json() as Promise<T>;
}
export function label(value:string|undefined|null){return (value||'unavailable').replaceAll('_',' ');}
export function amount(value:unknown,digits=2){if(value===null||value===undefined||value==='')return '—';const n=Number(value);return Number.isFinite(n)?n.toLocaleString('en-IN',{maximumFractionDigits:digits}):String(value);}
export function date(value:string|undefined|null){if(!value)return 'Not recorded';const d=new Date(value);return Number.isNaN(+d)?value:d.toLocaleDateString('en-IN',{day:'2-digit',month:'short',year:'numeric',timeZone:'Asia/Kolkata'});}
export function time(value:string|undefined|null){if(!value)return 'Not recorded';const d=new Date(value);return Number.isNaN(+d)?value:d.toLocaleString('en-IN',{day:'numeric',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',timeZone:'Asia/Kolkata'})+' IST';}
export type Citation={url:string;sha256:string;page:number;quote:string;quote_id?:string;observed_at?:string;evidence_type?:string};
export type Bar={date:string;adjusted_close:number;close:number;open?:number;high?:number;low?:number;volume:number};
export type Market={symbol:string;fetched_at:string;indicators:{as_of:string;return_1d_pct:number|null;return_5d_pct:number|null;volume_ratio_20d:number|null;warnings:string[]};freshness?:{status:string;expected_session?:string};bars:Bar[];indicator_history?:Bar[]};
export type Holding={symbol:string;name:string;market:Market|null;research_available:boolean;observed_at:string|null;filing_count:number;surfaced_24h_count?:number|null;latest_attempt?:string|null};
export type Filing={id:string;symbol:string;title:string;published_at:string;observed_at:string;document_url:string|null;classification:{category:string;materiality:number;reason:string;review_required:boolean;model_status:string;evidence?:Citation[]};analysis_status:string;enrichment:any;document:any;last_attempt:any};
export type Digest={window:string;since:string;as_of:string;warnings:string[];counts:{scanned:number;surfaced:number;buried:number;review_required:number;market_alerts:number};cards:Filing[];buried:Filing[];coverage:Record<string,any>;market_alerts:any[]};
export type Research={symbol:string;status:string;fetched_at:string;source_mode:string;sources:any[];modules:Record<string,any>;say_do:any;source_errors:any[];annual_forensics:any[];financial_statements?:any[];governance?:Record<string,any>;reasoning_model_name?:string;elapsed_ms?:number;generated_at?:string;reasoning?:any[];model_name?:string|null};
