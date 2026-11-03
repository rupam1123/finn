// Catch the production-only missing namespace that made every Link inert.
import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
import path from 'node:path';
import {init,parse} from 'es-module-lexer';
await init;
const dir=path.resolve('dist/client/_next/static/chunks');
const files=readdirSync(dir).filter(f=>f.endsWith('.js'));
const workspace=files.find(f=>f.startsWith('Workspace-'));
assert.ok(workspace,'Built workspace chunk is present');
let checked=false;
// Shared Link code can move into any common client chunk as routes evolve.
for(const file of files){
const text=readFileSync(path.join(dir,file),'utf8');
const [imports]=parse(text);

for(const item of imports){
 const literal=text.slice(item.s,item.e),specifier=item.n??(/^`\.\/[^`$]+`$/.test(literal)?literal.slice(1,-1):null);
 if(item.d<0||!specifier?.startsWith('./'))continue;
 const after=text.slice(item.se,item.se+180);
 const namespace=after.match(/\.then\(\w+=>\w+\.([A-Za-z_$][\w$]*)\)/)?.[1];
 if(!namespace?.includes('navigation'))continue;
 const source=readFileSync(path.resolve(dir,specifier),'utf8');
 const [,exports]=parse(source);
 assert.ok(exports.some(e=>e.n===namespace),'Router dynamic import selects an exported namespace');
 for(const method of ['navigateClientSide','getPrefetchInterceptionContext','getMountedSlotsHeader','createAppPrefetchRequestHeaders'])assert.ok(new RegExp('\\b'+method+'\\s*:').test(source),'Router namespace retains '+method);
 checked=true;
}
}
assert.ok(checked,'Navigation dynamic-entry namespace contract was checked across the client graph');
console.log('Production router namespace: navigation and prefetch functions retained.');
