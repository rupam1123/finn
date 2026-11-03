'use client';
import {useEffect,useRef,useState} from 'react';
import {createPortal} from 'react-dom';
import {Check,Info,AlertTriangle,X} from 'lucide-react';
export type ToastTone='success'|'info'|'warning'|'error';
type Notice={message:string;tone:ToastTone;id:number};
// UI feedback only. No history, persistence, telemetry or network request.
export function toast(message:string,tone:ToastTone='info'){
 if(typeof document==='undefined'||!document.querySelector('[data-finn-toast-root]'))return false;
 window.dispatchEvent(new CustomEvent('finn:toast',{detail:{message,tone}}));return true;
}
export default function Toasts(){
 const [notice,setNotice]=useState<Notice|null>(null),[host,setHost]=useState<HTMLElement|null>(null);
 const timer=useRef<ReturnType<typeof setTimeout>|null>(null),serial=useRef(0);
 const clear=()=>{if(timer.current!==null){clearTimeout(timer.current);timer.current=null}};
 const dismiss=()=>{clear();setNotice(null)};
 const arm=()=>{clear();timer.current=setTimeout(()=>setNotice(null),5000)};
 useEffect(()=>{
  const sync=()=>setHost(document.querySelector<HTMLElement>('dialog[open] .sheet-toast-host')||document.body);
  const receive=(event:Event)=>{const detail=(event as CustomEvent).detail;if(typeof detail?.message!=='string'||!detail.message.trim())return;sync();setNotice({message:detail.message.slice(0,220),tone:['success','info','warning','error'].includes(detail.tone)?detail.tone:'info',id:++serial.current});arm()};
  sync();window.addEventListener('finn:toast',receive);window.addEventListener('finn:dialog-change',sync);
  return()=>{clear();window.removeEventListener('finn:toast',receive);window.removeEventListener('finn:dialog-change',sync)};
 },[]);
 const Icon=notice?.tone==='success'?Check:notice?.tone==='info'?Info:AlertTriangle;
 return <><span data-finn-toast-root hidden/>{notice&&host&&createPortal(<div className={`app-toast toast-${notice.tone}`} key={notice.id} onMouseEnter={clear} onMouseLeave={arm} onFocus={clear} onBlur={e=>{if(!e.currentTarget.contains(e.relatedTarget as Node))arm()}}><Icon size={18} aria-hidden="true"/><span role="status" aria-live="polite" aria-atomic="true">{notice.message}</span><button type="button" aria-label="Dismiss notification" onClick={dismiss}><X size={16}/></button></div>,host)}</>;
}
