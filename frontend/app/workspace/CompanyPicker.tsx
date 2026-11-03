'use client';
import {useCallback,useEffect,useId,useRef,useState} from 'react';
import Link from 'next/link';import {ArrowUpRight,ChevronLeft,ChevronRight} from 'lucide-react';
import type {Holding} from '../terminal/data';import CompanyLogo from './CompanyLogo';

export function closestCompany(centres:number[],target:number){return centres.reduce((best,x,i)=>Math.abs(x-target)<Math.abs(centres[best]-target)?i:best,0)}

export default function CompanyPicker({holdings,loading=false}:{holdings:Holding[];loading?:boolean}){
 const [selected,setSelected]=useState(1),track=useRef<HTMLDivElement>(null),frame=useRef<number|null>(null),positions=useRef<number[]>([]),drag=useRef<{id:number;x:number;left:number;moved:boolean}|null>(null),suppressClick=useRef(false),hint=useId(),selectedRef=useRef(0);
 const active=Math.min(selected,Math.max(0,holdings.length-1)),company=holdings[active];selectedRef.current=active;
 const measure=useCallback(()=>{const el=track.current;if(el)positions.current=Array.from(el.querySelectorAll<HTMLElement>('.company-picker-card')).map(card=>card.offsetLeft+card.offsetWidth/2)},[]);
 const choose=useCallback((index:number,focus=false,instant=false)=>{const el=track.current;if(!el||!holdings.length)return;const next=Math.max(0,Math.min(holdings.length-1,index));measure();setSelected(next);const reduced=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;el.scrollTo({left:Math.max(0,positions.current[next]-el.clientWidth/2),behavior:instant||reduced?'auto':'smooth'});if(focus)el.querySelectorAll<HTMLButtonElement>('.company-picker-card')[next]?.focus({preventScroll:true})},[holdings.length,measure]);
 useEffect(()=>{measure();const el=track.current;if(!el)return;choose(selectedRef.current,false,true);const resize=()=>choose(selectedRef.current,false,true);const observer=typeof ResizeObserver==='function'?new ResizeObserver(resize):null;observer?.observe(el);window.addEventListener('resize',resize);return()=>{observer?.disconnect();window.removeEventListener('resize',resize)}},[measure,choose,holdings.length]);
 useEffect(()=>()=>{if(frame.current!==null)cancelAnimationFrame(frame.current)},[]);
 function scroll(){if(frame.current!==null)return;frame.current=requestAnimationFrame(()=>{frame.current=null;const el=track.current;if(el&&positions.current.length)setSelected(closestCompany(positions.current,el.scrollLeft+el.clientWidth/2))})}
 return <section className="company-picker" aria-label="Assessment watchlist" aria-roledescription="carousel">
  <div className="picker-heading"><div><h2>Assessment watchlist</h2><p id={hint}>Swipe to explore. Open a company when you’re ready.</p></div><span className="picker-count">{company?String(active+1).padStart(2,'0'):'—'} <span>/ {holdings.length}</span></span></div>
  {!company?<p className="caption" role="status">{loading?'Loading your watchlist…':'Watchlist unavailable. Check the saved sources or retry the workspace.'}</p>:<>
  <div className="picker-stage"><div className="picker-track" ref={track} onScroll={scroll} aria-describedby={hint} onKeyDown={e=>{const next=e.key==='ArrowRight'?active+1:e.key==='ArrowLeft'?active-1:e.key==='Home'?0:e.key==='End'?holdings.length-1:null;if(next!==null){e.preventDefault();choose(next,true)}}}
   onPointerDown={e=>{suppressClick.current=false;if(e.pointerType!=='mouse'||e.button!==0)return;drag.current={id:e.pointerId,x:e.clientX,left:e.currentTarget.scrollLeft,moved:false}}}
   onPointerMove={e=>{const d=drag.current;if(!d||d.id!==e.pointerId)return;const dx=e.clientX-d.x;if(Math.abs(dx)>5&&!d.moved){d.moved=true;e.currentTarget.setPointerCapture?.(e.pointerId);e.currentTarget.dataset.dragging='true'}if(d.moved){e.preventDefault();e.currentTarget.scrollLeft=d.left-dx}}}
   onPointerUp={e=>{const d=drag.current;if(!d)return;suppressClick.current=d.moved;drag.current=null;delete e.currentTarget.dataset.dragging;if(e.currentTarget.hasPointerCapture?.(e.pointerId))e.currentTarget.releasePointerCapture(e.pointerId)}}
   onPointerCancel={e=>{drag.current=null;suppressClick.current=false;delete e.currentTarget.dataset.dragging}}
   onLostPointerCapture={e=>{drag.current=null;delete e.currentTarget.dataset.dragging}}
   onPointerLeave={()=>{if(drag.current&&!drag.current.moved)drag.current=null}}
   onDragStart={e=>e.preventDefault()}
   onClickCapture={e=>{if(suppressClick.current){suppressClick.current=false;if(e.detail>0){e.preventDefault();e.stopPropagation()}}}}>
   {holdings.map((h,i)=><button type="button" key={h.symbol} className={`company-picker-card ${i===active?'is-current':''}`} tabIndex={i===active?0:-1} aria-pressed={i===active} aria-label={`${h.symbol}, ${h.name}, ${h.research_available?'saved research':'research not saved'}`} onClick={()=>choose(i)}><CompanyLogo symbol={h.symbol}/><strong>{h.symbol}</strong><span className="picker-company-name">{h.name}</span><span className="picker-availability"><i/>{h.research_available?'Saved research':'Explore sources'}</span></button>)}
  </div></div>
  <div className="picker-footer"><button className="picker-step" type="button" aria-label="Previous company" disabled={active===0} onClick={()=>choose(active-1)}><ChevronLeft size={20}/></button><Link className="picker-open" href={`/research/${encodeURIComponent(company.symbol)}`} prefetch={false}>Research {company.symbol}<ArrowUpRight size={16}/></Link><button className="picker-step" type="button" aria-label="Next company" disabled={active===holdings.length-1} onClick={()=>choose(active+1)}><ChevronRight size={20}/></button></div>
  <span className="sr-only" role="status" aria-live="polite">{company.symbol}, company {active+1} of {holdings.length}</span>
  </>}
 </section>
}
