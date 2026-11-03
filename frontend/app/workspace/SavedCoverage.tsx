import {date} from '../terminal/data';
export function savedCoverage(coverage:Record<string,any>={},kind:'filings'|'market'='filings'){
 const rows=Object.values(coverage),dates=rows.map(r=>kind==='market'?r.market?.freshness?.actual_session:r.filings?.fetched_at).filter((d):d is string=>typeof d==='string'&&Number.isFinite(Date.parse(d))).sort();
 return {oldest:dates[0],newest:dates.at(-1),available:dates.length,total:rows.length};
}
export default function SavedCoverage({coverage,kind='filings'}:{coverage?:Record<string,any>;kind?:'filings'|'market'}){
 const saved=savedCoverage(coverage,kind);if(!saved.total)return null;
 return <p className="saved-coverage">{kind==='market'?'Saved market sessions':'Filing checks saved'}: {saved.oldest?<>{date(saved.oldest)}{saved.oldest?.slice(0,10)!==saved.newest?.slice(0,10)&&` – ${date(saved.newest)}`}</>:'unavailable'}{saved.available<saved.total&&` · ${saved.total-saved.available} companies missing coverage`}</p>
}
