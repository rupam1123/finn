import {ChevronDown} from 'lucide-react';
import type {ComponentPropsWithoutRef} from 'react';

/** One aligned native disclosure control across research, evidence and settings. */
export default function DisclosureSummary({children,className='',...props}:ComponentPropsWithoutRef<'summary'>){
 return <summary {...props} className={`disclosure-summary ${className}`}><span className="disclosure-text">{children}</span><ChevronDown className="disclosure-chevron" size={18} strokeWidth={1.8} aria-hidden="true"/></summary>
}
