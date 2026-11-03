import assert from 'node:assert/strict';
import {JSDOM} from 'jsdom';
const dom=new JSDOM('<body><nav class="mobile-nav"><a href="/inbox" aria-current="page">Inbox</a><a href="/radar">Radar</a><a href="/research">Research</a><a href="/universe">Universe</a></nav><div class="segmented"><button aria-pressed="true">Price</button><button aria-pressed="false" disabled>Raw candles</button><button aria-pressed="false">Volume</button></div></body>',{url:'http://localhost:3000/inbox'});
Object.assign(globalThis,{window:dom.window,document:dom.window.document,Element:dom.window.Element,Node:dom.window.Node,HTMLElement:dom.window.HTMLElement});
const mod=await import('../app/workspace/slide-selection.ts'),{installSlideSelection}=mod.installSlideSelection?mod:mod.default;
const frames=new Map();let serial=0;window.requestAnimationFrame=fn=>{frames.set(++serial,fn);return serial};window.cancelAnimationFrame=id=>frames.delete(id);
const nav=document.querySelector('nav'),segments=document.querySelector('.segmented'),links=[...nav.children],buttons=[...segments.children];
const rect=(x,y,w,h)=>({x,y,left:x,top:y,right:x+w,bottom:y+h,width:w,height:h,toJSON(){}});
nav.getBoundingClientRect=()=>rect(0,500,400,56);segments.getBoundingClientRect=()=>rect(0,100,300,40);
for(const [i,el] of links.entries())el.getBoundingClientRect=()=>rect(i*100,500,100,56);
for(const [i,el] of buttons.entries())el.getBoundingClientRect=()=>rect(i*100,100,100,40);
let captured=null;nav.setPointerCapture=id=>captured=id;nav.hasPointerCapture=id=>captured===id;nav.releasePointerCapture=()=>captured=null;
const calls=[];for(const el of [...links,...buttons])el.addEventListener('click',e=>{e.preventDefault();calls.push(el.textContent)});
function pointer(target,type,x,y,extra={}){const e=new dom.window.MouseEvent(type,{bubbles:true,cancelable:true,clientX:x,clientY:y,button:0,...extra});Object.defineProperties(e,{pointerId:{value:1},isPrimary:{value:true},pointerType:{value:'touch'}});target.dispatchEvent(e);return e;}
function flush(){for(const [id,fn]of [...frames]){frames.delete(id);fn();}}
const stop=installSlideSelection(document.body,window),checks=[];
pointer(links[0],'pointerdown',50,525);for(let i=0;i<100;i++)pointer(window,'pointermove',51+i*2.8,525);assert.equal(frames.size,1);flush();assert.equal(calls.length,0);assert.equal(links[3].dataset.slidePreview,'true');checks.push('100 drag updates coalesce into one frame with no intermediate navigation');
pointer(window,'pointerup',350,525);assert.deepEqual(calls,['Universe']);assert.equal(nav.dataset.slideActive,undefined);assert.equal(captured,null);assert.equal(frames.size,0);checks.push('Release commits only the final route and clears capture/highlight');
links[3].dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true,cancelable:true,detail:1}));assert.equal(calls.length,1);checks.push('The browser follow-up click cannot navigate twice');
pointer(links[0],'pointerdown',50,525);pointer(window,'pointerup',50,525);links[1].click();assert.equal(calls.at(-1),'Radar');checks.push('Ordinary taps and keyboard-style clicks retain native activation');
pointer(links[0],'pointerdown',50,525);pointer(window,'pointermove',51,560);pointer(window,'pointerup',55,590);assert.equal(calls.length,2);assert.equal(nav.dataset.slideActive,undefined);checks.push('Vertical scroll intent never selects a route');
pointer(links[0],'pointerdown',50,525);pointer(window,'pointermove',250,525);flush();pointer(window,'pointercancel',250,525);assert.equal(calls.length,2);assert.equal(document.querySelector('[data-slide-preview]'),null);checks.push('Cancelled touches clear previews without navigation');
pointer(buttons[0],'pointerdown',40,120);pointer(window,'pointermove',250,120);pointer(window,'pointerup',250,120);assert.equal(calls.at(-1),'Volume');assert.ok(!calls.includes('Raw candles'));checks.push('Segmented controls support release selection and skip disabled options');
pointer(links[0],'pointerdown',50,525);pointer(window,'pointermove',250,525);pointer(window,'pointerup',650,525);assert.equal(calls.length,3);checks.push('Releasing outside the control cancels the action');
pointer(links[0],'pointerdown',50,525);pointer(window,'pointermove',250,525);assert.equal(frames.size,1);stop();assert.equal(frames.size,0);assert.equal(document.querySelector('[data-slide-active]'),null);checks.push('Unmount cancels pending frames and removes all gesture listeners');
dom.window.close();console.log(JSON.stringify({passed:true,checks,scope:'Pointer regression tests; actual browser navigation and touch layout checked separately'},null,2));
