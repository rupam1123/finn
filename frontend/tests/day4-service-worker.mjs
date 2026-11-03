import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const handlers={},stored=[],deleted=[];let network=0,claimed=false;
const context={URL,Promise,self:{location:{origin:'https://finn.example'},addEventListener:(name,fn)=>handlers[name]=fn,clients:{claim:async()=>{claimed=true;}}},
 caches:{open:async()=>({addAll:async paths=>stored.push(...paths)}),keys:async()=>['finn-shell-v0','another-app'],delete:async key=>deleted.push(key),match:async path=>({offline:path})},
 fetch:async()=>{network++;throw Error('offline');}};
vm.runInNewContext(readFileSync(new URL('../public/sw.js',import.meta.url),'utf8'),context);
await new Promise((resolve,reject)=>handlers.install({waitUntil:p=>p.then(resolve,reject)}));
assert.ok(stored.includes('/offline.html'));assert.ok(stored.every(p=>!p.includes('/api/')&&p!=='/'));
await new Promise((resolve,reject)=>handlers.activate({waitUntil:p=>p.then(resolve,reject)}));
assert.deepEqual(deleted,['finn-shell-v0']);assert.equal(claimed,true);
for(const request of [{url:'https://finn.example/api/pull/INFY',method:'GET',mode:'cors'}, {url:'https://api.finn.example/api/evidence/test.pdf',method:'GET',mode:'cors'}, {url:'https://finn.example/api/pull/INFY/jobs',method:'POST',mode:'cors'}]) {
 let intercepted=false;handlers.fetch({request,respondWith:()=>{intercepted=true;}});assert.equal(intercepted,false);
}
let navigation;handlers.fetch({request:{url:'https://finn.example/',method:'GET',mode:'navigate'},respondWith:p=>navigation=p});
assert.equal((await navigation).offline,'/offline.html');assert.equal(network,1);
console.log('4 service worker checks passed: static-only precache, scoped cleanup, no financial/API caching, offline navigation.');
