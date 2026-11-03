import assert from 'node:assert/strict';
import {JSDOM} from 'jsdom';
const dom=new JSDOM('<div id="root"></div>',{url:'http://localhost:3000'});
Object.assign(globalThis,{window:dom.window,document:dom.window.document,HTMLElement:dom.window.HTMLElement,HTMLInputElement:dom.window.HTMLInputElement,Event:dom.window.Event,IS_REACT_ACT_ENVIRONMENT:true});
const React=await import('react');globalThis.React=React;
const {createRoot}=await import('react-dom/client');
const {default:Pull}=await import('../app/PullWorkspace.tsx');
const root=createRoot(document.getElementById('root'));const originalFetch=globalThis.fetch;
const base=process.env.FINN_TEST_API || 'http://127.0.0.1:8000';
globalThis.fetch=(url,options)=>originalFetch(String(url).replace('http://localhost:8000',base),options);
async function submit(ticker){
 await React.act(async()=>{const input=document.getElementById('pull-symbol');Object.getOwnPropertyDescriptor(dom.window.HTMLInputElement.prototype,'value').set.call(input,ticker);input.dispatchEvent(new dom.window.Event('input',{bubbles:true}));});
 await React.act(async()=>document.querySelector('form').dispatchEvent(new dom.window.Event('submit',{bubbles:true,cancelable:true})));
 for(let i=0;i<100&&document.querySelector('[role=status]').textContent.includes('Checking');i++)await React.act(async()=>{await new Promise(r=>setTimeout(r,30));});
 return document.body.textContent;
}
const checks=[];
try{
 await React.act(async()=>root.render(React.createElement(Pull)));
 let text=await submit('KPIL');assert.ok(text.includes('4 / 4'));assert.ok(text.includes('review_required'));assert.ok(document.querySelector('.citation-pill'));checks.push('unseen KPIL four-period source evidence renders through real HTTP');
 text=await submit('DEEPAKNTR');assert.ok(text.includes('0.979×'));assert.ok(text.includes('0.260×'));checks.push('primary-reconciled cash and leverage figures render');
 text=await submit('TATAMOTORS');assert.ok(text.includes('Research unavailable'));assert.ok(!text.includes('0.979×'));checks.push('invalid identity clears previous financial results');
 globalThis.fetch=async()=>{throw new TypeError('diagnostic disconnect');};text=await submit('KPIL');assert.ok(text.includes('Research unavailable'));checks.push('network outage is visible');
 globalThis.fetch=(url,options)=>originalFetch(String(url).replace('http://localhost:8000',base),options);
 text=await submit('ZZZZNOTREAL');assert.ok(text.includes('Queued'));checks.push('cold request creates a durable job');
 console.log(JSON.stringify({passed:true,checks,scope:'React/jsdom with real local HTTP; not phone/browser QA'},null,2));
}finally{await React.act(async()=>root.unmount());dom.window.close();}
