import {DatabaseSync} from 'node:sqlite';
import {readFileSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {handleApi} from '../backend/router.mjs';
const dir=path.resolve(process.argv[2]),manifest=JSON.parse(readFileSync(path.join(dir,'manifest.json'),'utf8')),cases=JSON.parse(readFileSync(path.join(dir,'parity-cases.json'),'utf8'));
const sql=new DatabaseSync(path.join(dir,'ported.sqlite3'),{readOnly:true}),raw=new DatabaseSync(manifest.source_backup,{readOnly:true});
const db={prepare(query){let args=[];return {bind(...x){args=x;return this;},async first(){return sql.prepare(query).get(...args)||null;},async all(){return {results:sql.prepare(query).all(...args)};}};}};
const bucket={async get(key){const sha=key.split('/').at(-1),row=raw.prepare('SELECT body FROM raw_responses WHERE sha256=?').get(sha);if(!row)return null;return {body:row.body,checksums:{sha256:createHash('sha256').update(row.body).digest()}};}};
function difference(a,b,where=''){if(typeof a!==typeof b)return where+':type';if(a===null||b===null)return a===b?null:where+':null';if(typeof a!=='object'){if(where.endsWith('.cache_age_seconds')&&typeof a==='number'&&Math.abs(a-b)<.02)return null;return a===b?null:where+':value';}if(Array.isArray(a)!==Array.isArray(b))return where+':array';const ak=Object.keys(a).sort(),bk=Object.keys(b).sort();if(JSON.stringify(ak)!==JSON.stringify(bk))return where+':keys';for(const k of ak){const d=difference(a[k],b[k],where+'.'+k);if(d)return d;}return null;}
const failures=[];
for(const c of cases.cases){const response=await handleApi(new Request('https://finn.test'+c.path),{DB:db,BUCKET:bucket},cases.clock);let body;if(c.path.endsWith('.pdf')&&response.status===200){const bytes=Buffer.from(await response.arrayBuffer());body={sha256:createHash('sha256').update(bytes).digest('hex'),size:bytes.length};}else body=await response.json();let diff=response.status!==c.status?'status':difference(c.body,body);if(diff)failures.push({path:c.path,difference:diff,expected_status:c.status,actual_status:response.status,expected:c.body,actual:body});}
const post=await handleApi(new Request('https://finn.test/api/pull/TCS/jobs',{method:'POST'}),{DB:db},cases.clock);if(post.status!==403)failures.push({path:'POST /api/pull/TCS/jobs',difference:'write enabled'});
const blocked=await handleApi(new Request('https://finn.test/__migration/rows',{method:'POST',body:'{}'}),{DB:db},cases.clock);if(blocked.status!==403)failures.push({path:'POST /__migration/rows',difference:'unprotected import'});
writeFileSync(path.join(dir,'parity-failures.json'),JSON.stringify(failures,null,2));
console.log(JSON.stringify({passed:cases.cases.length-failures.length,total:cases.cases.length,read_only_post:post.status,unauthorized_import:blocked.status,failures:failures.map(({path,difference,expected_status,actual_status})=>({path,difference,expected_status,actual_status}))},null,2));
process.exitCode=failures.length?1:0;
