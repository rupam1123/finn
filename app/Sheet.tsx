"use client";

import {useEffect, useId, useRef} from "react";

export default function Sheet({title, onClose, children,footer}: {
  title: string; onClose: () => void; children: React.ReactNode; footer?:React.ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => {
    const dialog = ref.current!;
    const trigger = document.activeElement as HTMLElement | null;
    const overflow = document.body.style.overflow;
    const viewport=window.visualViewport;
    const resize=()=>{dialog.style.setProperty('--sheet-available-height',`${viewport?.height||window.innerHeight}px`);dialog.style.setProperty('--sheet-keyboard-inset',`${viewport?Math.max(0,window.innerHeight-viewport.height-viewport.offsetTop):0}px`)};
    resize();viewport?.addEventListener('resize',resize);viewport?.addEventListener('scroll',resize);
    dialog.showModal();window.dispatchEvent(new Event('finn:dialog-change'));
    document.body.style.overflow = "hidden";
    return () => {viewport?.removeEventListener('resize',resize);viewport?.removeEventListener('scroll',resize);dialog.close();window.dispatchEvent(new Event('finn:dialog-change')); document.body.style.overflow = overflow;if(trigger?.isConnected)trigger.focus({preventScroll:true});};
  }, []);
  return <dialog ref={ref} aria-labelledby={titleId} className="evidence-sheet"
    onCancel={event => {event.preventDefault(); onClose();}}
    onClose={() => {if (!ref.current?.open) onClose();}}
    onClick={event => {if (event.target === event.currentTarget) onClose();}}>
    <div className="sheet-header"><h2 id={titleId}>{title}</h2>
      <button type="button" onClick={onClose} aria-label={`Close ${title}`}>Close</button></div>
    <div className="sheet-toast-host"/><div className="sheet-body" tabIndex={0} role="region" aria-label={`${title} content`}>{children}</div>{footer&&<div className="sheet-footer">{footer}</div>}
  </dialog>;
}
