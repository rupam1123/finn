import {ChevronRight,FileText,MessagesSquare} from 'lucide-react';
import type {ReactNode} from 'react';
import {label} from '../terminal/data';
import {Status} from '../terminal/ui';

/** A compact native disclosure; source gaps stay visible before expansion. */
export default function QuarterCard({row,children}:{row:any;children:ReactNode}){
 const matched=(row.comparisons||[]).filter((c:any)=>['within_target','above_target','below_target'].includes(c.status)).length;
 return <details className="quarter-card compact-quarter"><summary className="quarter-toggle"><span className="quarter-summary"><span className="quarter-heading"><strong>{row.period_end}</strong><Status>{label(row.status)}</Status></span><span className="quarter-preview">{matched?`${matched} matched numerical ${matched===1?'comparison':'comparisons'}`:'No matched numerical comparison'}</span></span><ChevronRight className="quarter-chevron" size={19} strokeWidth={1.8} aria-hidden="true"/></summary><div className="quarter-body">{children}</div></details>
}

export function QuarterEvidence({kind,count,children}:{kind:'said'|'delivered';count:number;children:ReactNode}){
 const Icon=kind==='said'?MessagesSquare:FileText,title=kind==='said'?'Management commentary':'Delivered-period evidence';
 return <details className="quarter-evidence"><summary><Icon size={15} strokeWidth={1.6} aria-hidden="true"/><span>{title}</span><span className="quarter-evidence-count">{count}</span><ChevronRight className="quarter-evidence-chevron" size={16} strokeWidth={1.8} aria-hidden="true"/></summary><div className="quarter-evidence-body">{children}</div></details>
}
