'use client';
import {useEffect,useRef,useState} from 'react';

// Separate collapse/expand thresholds prevent header resizing from flickering.
export const compactAfterScroll=(y:number,wasCompact:boolean)=>y>120?true:y<40?false:wasCompact;
export default function useCompactChrome(enabled:boolean,route:string){
 const [compact,setCompact]=useState(false);
 const current=useRef(false);
 useEffect(()=>{
  if(!enabled){
   current.current=false;
   setCompact(false);
   return;
  }
  let frame=0;
  const update=()=>{
   frame=0;
   const next=compactAfterScroll(window.scrollY,current.current);
   if(next===current.current)return;
   current.current=next;
   setCompact(next);
  };
  const scroll=()=>{if(!frame)frame=requestAnimationFrame(update)};
  update();window.addEventListener('scroll',scroll,{passive:true});
  return()=>{window.removeEventListener('scroll',scroll);if(frame)cancelAnimationFrame(frame)};
 },[enabled,route]);
 return enabled&&compact;
}
