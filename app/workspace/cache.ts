'use client';
import {useCallback,useEffect,useState} from 'react';
import {request} from '../terminal/data';
const FRESH_MS=30_000,RETAIN_MS=5*60_000,MAX_ENTRIES=32;
const cache=new Map<string,{at:number;value:any}>();
const inflight=new Map<string,Promise<any>>();
export function clearReadCache(path?:string){
 if(path){cache.delete(path);inflight.delete(path)}else{cache.clear();inflight.clear()}
}
// Memory only. A retained snapshot keeps return visits readable while a fresh read runs.
export function peekRead<T>(path:string):T|null{
 const saved=cache.get(path);if(!saved)return null;
 if(Date.now()-saved.at>=RETAIN_MS){cache.delete(path);return null}return saved.value;
}
export function cachedRead<T>(path:string):Promise<T>{
 const saved=cache.get(path);if(saved&&Date.now()-saved.at<FRESH_MS)return Promise.resolve(saved.value);
 const pending=inflight.get(path);if(pending)return pending;
 const promise=request<T>(path).then(value=>{
  // An invalidated older request cannot overwrite a newer refresh.
  if(inflight.get(path)===promise){cache.delete(path);cache.set(path,{at:Date.now(),value});while(cache.size>MAX_ENTRIES)cache.delete(cache.keys().next().value!)}return value;
 }).finally(()=>{if(inflight.get(path)===promise)inflight.delete(path)});
 inflight.set(path,promise);return promise;
}
type ReadState<T>={path:string;data:T|null;loading:boolean;refreshing:boolean;error:string};
function snapshot<T>(path:string):ReadState<T>{const data=peekRead<T>(path);return {path,data,loading:data===null,refreshing:false,error:''}}
export function useRead<T=any>(path:string){
 const [result,setResult]=useState<ReadState<T>>(()=>snapshot<T>(path)),[rev,bump]=useState(0);
 useEffect(()=>{
  let alive=true;const retained=peekRead<T>(path);
  if(retained!==null&&Date.now()-cache.get(path)!.at<FRESH_MS){setResult({path,data:retained,loading:false,refreshing:false,error:''});return()=>{alive=false}}
  setResult({path,data:retained,loading:retained===null,refreshing:true,error:''});
  cachedRead<T>(path).then(data=>{if(alive)setResult({path,data,loading:false,refreshing:false,error:''})}).catch(e=>{
   if(alive)setResult({path,data:retained,loading:false,refreshing:false,error:e.message||'Saved source unavailable.'});
  });return()=>{alive=false};
 },[path,rev]);
 const retry=useCallback(()=>{clearReadCache(path);bump(n=>n+1)},[path]);
 return {...(result.path===path?result:snapshot<T>(path)),retry};
}
