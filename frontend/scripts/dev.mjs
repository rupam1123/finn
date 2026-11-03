// Standard Next development; optional report-backed sidecar exists only for local QA.
import {spawn} from 'node:child_process';
import {existsSync,readFileSync} from 'node:fs';
process.env.NEXT_TELEMETRY_DISABLED='1';
const children=[];
let production=false;
const args=process.argv.slice(2).filter(a=>a!=='--strictPort').map(a=>a==='--host'?'--hostname':a);
if(existsSync('.preview-qa.json')){
 const qa=JSON.parse(readFileSync('.preview-qa.json','utf8')); production=!!qa.production;
 children.push(spawn(qa.python,['-m','uvicorn','finn.main:app','--host','127.0.0.1','--port','8000','--no-access-log'],{stdio:'inherit',env:{...process.env,PYTHONPATH:qa.pythonpath,FINN_DB:qa.db,FINN_QA_REPLAY:'1',FINN_PUBLIC_REVIEW:qa.public_review?'1':'0'}}));
}
children.push(spawn(process.execPath,['node_modules/next/dist/bin/next',...(production?['start']:['dev','--webpack']),...args],{stdio:'inherit'}));
for(const sig of ['SIGINT','SIGTERM'])process.on(sig,()=>{for(const child of children)child.kill('SIGTERM');process.exit(0)});
for(const child of children)child.on('exit',code=>{for(const other of children)if(other!==child)other.kill('SIGTERM');process.exit(code||0)});
