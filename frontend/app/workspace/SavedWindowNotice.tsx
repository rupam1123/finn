import {time} from '../terminal/data';
export function savedCoverageState(data:any){
 const checks=Object.values(data?.coverage||{}).map((v:any)=>v.filings?.fetched_at).filter((v):v is string=>typeof v==='string'&&Number.isFinite(Date.parse(v)));
 const latest=checks.sort((a,b)=>Date.parse(b)-Date.parse(a))[0]||null;
 const since=Date.parse(data?.since),stale=!!latest&&Number.isFinite(since)&&Date.parse(latest)<since;
 return {latest,stale,missing:checks.length===0};
}
export default function SavedWindowNotice({data,window,onWindow}:{data:any;window:string;onWindow:(v:string)=>void}){
 if(!data||window!=='1d'||data.counts?.scanned!==0)return null;
 const coverage=savedCoverageState(data);
 return <div className="saved-window-notice" role="status"><div><strong>No saved filings in the last 24 hours</strong><p>{coverage.stale?`Saved filing coverage was last checked ${time(coverage.latest)}. It does not cover this 24-hour window.`:coverage.missing?'Filing coverage is unavailable for this window.':'No filings were retained for this window; source coverage may be incomplete.'} Reload reads saved data; it does not refresh exchanges.</p></div><button className="text-button" onClick={()=>onWindow('7d')}>View saved 7 days</button></div>;
}
