import assert from 'node:assert/strict';
import {JSDOM} from 'jsdom';
const dom = new JSDOM('<!doctype html><div id="root"></div>', {url: 'http://localhost:3000'});
Object.assign(globalThis, {window:dom.window, document:dom.window.document, HTMLElement:dom.window.HTMLElement,
  HTMLInputElement:dom.window.HTMLInputElement, Event:dom.window.Event, MouseEvent:dom.window.MouseEvent,
  IS_REACT_ACT_ENVIRONMENT:true});
const React = await import('react');
globalThis.React = React;
const {createRoot} = await import('react-dom/client');
const {default:Home} = await import('../app/SourceInspector.tsx');
const root = createRoot(document.getElementById('root'));
const fetchOriginal = globalThis.fetch;
const base = process.env.FINN_TEST_API || 'http://127.0.0.1:8000';
let calls=[];
globalThis.fetch = async (url,options) => {
  const target = new URL(String(url).replace('http://localhost:8000',base),base).href;
  const response = await fetchOriginal(target, options);
  calls.push({url:target,status:response.status});
  return response;
};
const check=[];
async function inspect(symbol) {
  await React.act(async () => {
    const input=document.querySelector('#ticker');
    Object.getOwnPropertyDescriptor(dom.window.HTMLInputElement.prototype,'value').set.call(input,symbol);
    input.dispatchEvent(new dom.window.Event('input',{bubbles:true}));
  });
  await React.act(async () => {
    document.querySelector('#source-form').dispatchEvent(new dom.window.Event('submit',{bubbles:true,cancelable:true}));
  });
  for(let i=0;i<100 && document.querySelector('#source-form button').disabled;i++) {
    await React.act(async () => {await new Promise(resolve=>setTimeout(resolve,30));});
  }
  assert.equal(document.querySelector('#source-form button').disabled,false,'request must finish');
  return document.body.textContent;
}
try {
  await React.act(async()=>root.render(React.createElement(Home)));
  for(const [symbol,name] of [['TCS','Tata Consultancy Services'],['ASTRAL','Astral'],['LAURUSLABS','Laurus']]) {
    const text=await inspect(symbol);
    assert.ok(text.includes(name),symbol+' should render from actual API');
    assert.ok(text.includes('6 staging tables'));
    assert.ok(text.includes('not yet verified'));
    assert.ok(text.includes('Market data: unavailable') || text.includes('Market data: rejected_older') || text.includes('Market data: saved'));
    check.push(symbol+' actual API data renders');
  }
  const failed=await inspect('HDFCBANK');
  assert.ok(failed.includes('HDFC Bank'));
  assert.ok(failed.includes('Latest refresh did not succeed'));
  assert.ok(failed.includes('diagnostic source outage'));
  check.push('failed refresh shows last-good real company plus diagnostic error');
  const missing=await inspect('ZZZZNOTREAL');
  assert.ok(missing.includes('has not been ingested'));
  assert.equal(document.querySelector('#company-snapshot'),null);
  check.push('404 clears prior result and explains missing cache');
  const invalid=await inspect('TATAMOTORS');
  assert.ok(invalid.includes('TMPV') && invalid.includes('TMCV'));
  check.push('422 displays actionable instrument error');
  globalThis.fetch=async()=>{throw new TypeError('diagnostic network disconnect');};
  const disconnected=await inspect('TCS');
  assert.ok(disconnected.includes('Cannot reach the ingestion API'));
  check.push('network failure renders recoverable error');
  globalThis.fetch=async(url,options)=>fetchOriginal(String(url).replace('http://localhost:8000',base),options);
  assert.ok((await inspect('TCS')).includes('Tata Consultancy Services'));
  check.push('successful retry restores company result');
  async function loadDigest(window) {
    if (window) await React.act(async () => document.querySelector(`[data-window="${window}"]`).click());
    await React.act(async () => document.querySelector('#digest-form').dispatchEvent(new dom.window.Event('submit',{bubbles:true,cancelable:true})));
    for(let i=0;i<100 && document.querySelector('#load-digest').disabled;i++) {
      await React.act(async () => {await new Promise(resolve=>setTimeout(resolve,30));});
    }
    assert.equal(document.querySelector('#load-digest').disabled,false);
    return document.querySelector('[aria-labelledby="digest-heading"]').textContent;
  }
  const expected=await (await fetchOriginal(base+'/api/push/digest?window=7d')).json();
  const digestText=await loadDigest('7d');
  assert.ok(digestText.includes(`${expected.counts.scanned} scanned · ${expected.counts.surfaced} surfaced · ${expected.counts.buried} buried`));
  assert.ok(digestText.includes('not a live feed') && digestText.includes('Source coverage'));
  assert.ok(digestText.includes('Nearby filings do not establish causation'));
  check.push('seven-day digest renders real API counts, coverage and noncausal EOD alerts');
  const monthText=await loadDigest('30d');
  assert.ok(monthText.includes('73188') && monthText.includes('13934') && monthText.includes('1.26%'));
  assert.ok(monthText.includes('Prashant Verma') && monthText.includes('2027-02-01'));
  assert.ok(document.querySelector('.citation-pill') && monthText.includes('not independently verified'));
  check.push('real TCS results and Bajaj management evidence render with calculated changes');
  globalThis.fetch=async()=>{throw new TypeError('diagnostic digest disconnect');};
  assert.ok((await loadDigest()).includes('Cannot reach the digest API'));
  assert.equal(document.querySelector('[data-testid="digest-result"]'),null);
  check.push('digest outage clears previous results and displays retry guidance');
  globalThis.fetch=async(url,options)=>fetchOriginal(String(url).replace('http://localhost:8000',base),options);
  assert.ok((await loadDigest('7d')).includes('scanned'));
  check.push('digest retry restores actual API data');
  console.log(JSON.stringify({passed:true,checks:check,requests:calls,scope:'React component in jsdom using real HTTP API; not a real browser or mobile test'},null,2));
} finally {
  await React.act(async()=>root.unmount());
  dom.window.close();
}
