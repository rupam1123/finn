'use client';
import {useEffect,useState} from 'react';

// Separate collapse/expand thresholds prevent header resizing from flickering.
export const compactAfterScroll=(y:number,wasCompact:boolean)=>y>120?true:y<40?false:wasCompact;
export default function useCompactChrome(enabled:boolean,route:string){
 const [compact,setCompact]=useState(false);
 useEffect(()=>{
  if(!enabled){setCompact(false);return}
  let frame=0;
  const update=()=>{frame=0;setCompact(was=>compactAfterScroll(window.scrollY,was))};
  const scroll=()=>{if(!frame)frame=requestAnimationFrame(update)};
  update();window.addEventListener('scroll',scroll,{passive:true});
  return()=>{window.removeEventListener('scroll',scroll);if(frame)cancelAnimationFrame(frame)};
 },[enabled,route]);
 return enabled&&compact;
}
