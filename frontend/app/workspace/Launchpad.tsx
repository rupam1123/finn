'use client';
import CompanyPicker from './CompanyPicker';import Link from 'next/link';import ResearchMotion from './ResearchMotion';import {Search,ArrowUpRight} from 'lucide-react';import {useWorkspace} from './Workspace';
export default function Launchpad(){
 const {holdings,loading,search,jobsEnabled}=useWorkspace();
 return <section>
  <div className="eyebrow">PRIMARY EVIDENCE / PULL</div>
  <div className="page-heading"><div><h1>AI-assisted research</h1><p>Company analysis grounded in primary sources.</p></div></div>
  <div className="research-launch">
   <ResearchMotion/>
   <span className="section-label">RESEARCH A COMPANY</span>
   <h2>Read the business.<br/>Question the numbers.</h2>
   <p>Explore AI-assisted analysis where available, the Say–Do audit, reported financials and source documents.</p>
   <button className="primary-action" onClick={search}><Search size={17}/>Research a company</button>
  </div>
  <div className="alias-choices"><span className="caption">Historical Tata Motors symbol?</span><Link className="outline-button" href="/research/TMPV">TMPV · Passenger</Link><Link className="outline-button" href="/research/TMCV">TMCV · Commercial</Link></div>
  <div className="section-heading"><h2>Beyond the portfolio</h2></div>
  <div className="launch-companies">{['TITAN','COFORGE','SYNGENE','SONACOMS','CAMS'].map(s=><Link href={`/research/${s}`} key={s}><strong>{s}</strong><ArrowUpRight size={18}/><small>Open saved research or discover sources</small></Link>)}</div>
  <CompanyPicker holdings={holdings} loading={loading}/>
  <p className="caption">{jobsEnabled?'Opening a company reads saved data. Start new source discovery explicitly from its research workspace.':'Read-only preview · choose a company to review saved research. New research runs are available in the local owner session.'} AI-assisted analysis may be incomplete; verify the cited primary sources.</p>
 </section>;
}
