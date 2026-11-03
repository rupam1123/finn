"use client";

import {useEffect, useId, useRef, useState} from "react";
import {ArrowUpRight,CheckCircle2} from 'lucide-react';
type Company = {symbol: string; company_name: string; sector?:string|null; research_available?:boolean};

export default function CompanySearch({value, onChange, onSelect, id = 'pull-symbol'}: {
  value: string; onChange: (value: string) => void; onSelect: (symbol: string) => void; id?: string;
}) {
  const listId = useId();
  const [matches, setMatches] = useState<Company[]>([]), [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1), [message, setMessage] = useState("");
  const sequence = useRef(0);
  useEffect(() => {
    const request = ++sequence.current;
    setMatches([]); setActive(-1); setMessage("");
    if (!open || !value.trim()) return;
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        const base = process.env.NEXT_PUBLIC_API_BASE || "";
        const result = await fetch(`${base}/api/universe?q=${encodeURIComponent(value.trim().slice(0, 60))}`,
          {signal: AbortSignal.any([controller.signal, AbortSignal.timeout(10000)])});
        if (!result.ok) throw Error();
        const data = await result.json() as {matches?: Company[]};
        if (request !== sequence.current || controller.signal.aborted) return;
        const rows = Array.isArray(data.matches) ? data.matches.filter((row: Company) => typeof row.symbol === "string" && typeof row.company_name === "string").slice(0, 8) : [];
        setMatches(rows);
        setMessage(rows.length ? `${rows.length} matching companies` : "No name matches. You can still enter an exact NSE symbol.");
      } catch {
        if (request === sequence.current && !controller.signal.aborted)
          setMessage("Company suggestions unavailable. Enter an exact NSE symbol.");
      }
    }, 250);
    return () => {clearTimeout(timer); controller.abort();};
  }, [value, open]);
  function choose(company: Company) {setOpen(false); onChange(company.symbol); onSelect(company.symbol);}
  return <div className="company-search" onBlur={event => {if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setOpen(false);}}>
    <label htmlFor={id} className="sr-only">Research NSE symbol or company name</label>
    <input id={id} role="combobox" aria-autocomplete="list" aria-expanded={open && matches.length > 0}
      aria-controls={listId} aria-activedescendant={active >= 0 && matches[active] ? `${listId}-${active}` : undefined}
      autoComplete="off" autoCapitalize="characters" spellCheck={false} required maxLength={60} value={value}
      placeholder="Company name or NSE symbol" onFocus={() => setOpen(true)}
      onChange={event => {setOpen(true); onChange(event.target.value);}}
      onKeyDown={event => {
        if (event.key === "Escape" && open) {event.preventDefault();event.stopPropagation();setOpen(false); setActive(-1);}
        else if (event.key === "ArrowDown" || event.key === "ArrowUp") {
          event.preventDefault(); setOpen(true);
          setActive(index => matches.length ? index<0?(event.key === "ArrowDown"?0:matches.length-1):(index + (event.key === "ArrowDown" ? 1 : -1) + matches.length) % matches.length : -1);
        } else if (event.key === "Enter" && open && active >= 0 && matches[active]) {event.preventDefault(); choose(matches[active]);}
      }}/>
    {open && matches.length > 0 && <ul id={listId} role="listbox" aria-label="Matching companies" className="company-options">
      {matches.map((company, index) => <li role="option" id={`${listId}-${index}`} aria-selected={index === active} key={company.symbol}
        onMouseDown={event => event.preventDefault()} onMouseMove={() => setActive(index)} onClick={() => choose(company)}>
        <span className="search-company-mark" aria-hidden="true">{company.symbol.slice(0,2)}</span><span className="search-company-copy"><strong>{company.symbol}</strong><span>{company.company_name}</span></span><span className="search-company-state">{company.research_available?<><CheckCircle2 size={12}/>Saved</>:<ArrowUpRight size={16}/>}</span>
      </li>)}
    </ul>}
    {open && message && <p role="status" className="search-results-status">{message}</p>}
  </div>;
}
