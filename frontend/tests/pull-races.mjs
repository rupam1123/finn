import assert from 'node:assert/strict';
import {JSDOM} from 'jsdom';
const dom=new JSDOM('<div id="root"></div>',{url:'http://localhost:3000'});
Object.assign(globalThis,{window:dom.window,document:dom.window.document,HTMLElement:dom.window.HTMLElement,HTMLInputElement:dom.window.HTMLInputElement,Event:dom.window.Event,IS_REACT_ACT_ENVIRONMENT:true});
const React=await import('react');globalThis.React=React;
const {createRoot}=await import('react-dom/client');
const imported=await import('../app/PullWorkspace.tsx');
const Pull=typeof imported.default==='function'?imported.default:imported.default.default;
const response=(data,status=200)=>({ok:status<400,status,json:async()=>data});
const data=symbol=>({symbol,status:'partial',source_mode:'transcripts',modules:{},say_do:{observed_periods:0,requested_quarters:4,ledger:[]},source_errors:[]});
let scheduled=[],finishOld,firstInfy=true,refreshRequested=false;
const realTimeout=globalThis.setTimeout,realClear=globalThis.clearTimeout,originalFetch=globalThis.fetch;
globalThis.setTimeout=(callback,ms,...args)=>{if(ms===2000){scheduled.push(callback);return {unref(){}};}return realTimeout(callback,ms,...args);};
globalThis.clearTimeout=id=>{if(typeof id?.unref==='function'&&!('_onTimeout' in id))return;realClear(id);};
globalThis.fetch=async url=>{
 url=String(url);
 if(url.includes('/api/pull-jobs/'))return new Promise(resolve=>{finishOld=resolve;});
 if(url.includes('/jobs')){refreshRequested=url.includes('refresh=true');return response({id:'test-job'});}
 if(url.endsWith('/INFY')&&firstInfy){firstInfy=false;return response({},404);}
 return response({data:data(url.endsWith('/TCS')?'TCS':'INFY'),fetched_at:'2026-10-30T00:00:00Z'});
};
const root=createRoot(document.getElementById('root'));
async function submit(symbol){
 await React.act(async()=>{const input=document.getElementById('pull-symbol');Object.getOwnPropertyDescriptor(dom.window.HTMLInputElement.prototype,'value').set.call(input,symbol);input.dispatchEvent(new Event('input',{bubbles:true}));});
 await React.act(async()=>document.querySelector('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
}
try{
 await React.act(async()=>root.render(React.createElement(Pull)));
 await submit('INFY');
 let pending;
 await React.act(async()=>{pending=scheduled.shift()();await Promise.resolve();});
 assert.equal(scheduled.length,0,'A pending poll must not schedule overlapping requests');
 await submit('TCS');
 assert.ok(document.body.textContent.includes('TCS · partial'));
 await React.act(async()=>{finishOld(response({status:'partial',symbol:'INFY',payload:{stage:'finished'}}));await pending;});
 assert.ok(document.body.textContent.includes('TCS · partial'),'Old job must not overwrite the new company');
 await React.act(async()=>{const button=[...document.querySelectorAll('button')].find(x=>x.textContent==='Refresh sources');button.click();});
 assert.ok(refreshRequested,'Refresh must enqueue a forced research job');
 console.log('3 Pull UI checks passed: stale responses, sequential polling, forced refresh.');
}finally{
 await React.act(async()=>root.unmount());dom.window.close();globalThis.setTimeout=realTimeout;globalThis.clearTimeout=realClear;globalThis.fetch=originalFetch;
}
