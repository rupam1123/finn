"""Import a private Sites export. Credentials arrive only through hidden stdin.

Usage: python scripts/import_sites.py --export <directory>
Input JSON: {url, bypass_token, migration_key}; never put tokens in CLI arguments.
"""
import argparse
import concurrent.futures
import hashlib
import getpass
import json
from pathlib import Path
import sqlite3
import sys
import time
import urllib.request
import urllib.error


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export',type=Path,required=True)
    parser.add_argument('--workers',type=int,default=8)
    args=parser.parse_args()
    print('Ready for private Site import JSON on stdin (input must be hidden).',flush=True)
    auth=json.loads(getpass.getpass('') if sys.stdin.isatty() else sys.stdin.readline())
    url=auth['url'].rstrip('/')
    if not url.startswith('https://') or '/' in url.removeprefix('https://') or not url.endswith('.chatgpt.site'):
        raise SystemExit('Use the exact HTTPS ChatGPT Site origin')
    headers={'OAI-Sites-Authorization':'Bearer '+auth['bypass_token'],'X-FINN-Migration-Key':auth['migration_key']}
    manifest=json.loads((args.export/'manifest.json').read_text(encoding='utf-8'))
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,req,fp,code,msg,headers,newurl):return None
    opener=urllib.request.build_opener(NoRedirect)

    def request(path,data=None,method=None,content_type='application/json'):
        payload=data if isinstance(data,bytes) else None if data is None else json.dumps(data,separators=(',',':'),ensure_ascii=False).encode()
        h={**headers,'Content-Type':content_type}
        if payload is not None:h['Content-Length']=str(len(payload))
        for attempt in range(4):
            req=urllib.request.Request(url+path,data=payload,headers=h,method=method or ('GET' if data is None else 'POST'))
            try:
                with opener.open(req,timeout=180) as res:
                    return json.load(res)
            except urllib.error.HTTPError as e:
                if e.code not in (429,500,502,503,504) or attempt==3:
                    # Do not print redirects, credentials, or the entire server response.
                    raise RuntimeError('Private import HTTP '+str(e.code)+' at '+path.split('/')[2]) from None
            except (OSError,TimeoutError):
                if attempt==3:raise RuntimeError('Private import connection failed') from None
            time.sleep(min(2**attempt,8))

    done={x['sha256']:x['size'] for x in request('/__migration/status')['objects']}
    print('Resuming with '+str(len(done))+' checksum-verified evidence objects.',flush=True)
    def upload(identity):
        sha,size=identity
        if done.get(sha)==size:return size,False
        with sqlite3.connect(manifest['source_backup']) as db:
            body=db.execute('SELECT body FROM raw_responses WHERE sha256=?',(sha,)).fetchone()[0]
        if hashlib.sha256(body).hexdigest()!=sha:raise RuntimeError('Original saved response failed SHA-256 verification')
        result=request('/__migration/object/'+sha,body,'PUT','application/pdf' if body.startswith(b'%PDF') else 'application/octet-stream')
        if result.get('sha256')!=sha or result.get('size')!=size or result.get('verified') is not True:raise RuntimeError('Evidence upload receipt mismatch')
        return size,True
    with sqlite3.connect(manifest['source_backup']) as db:
        identities=db.execute('SELECT sha256,length(body) FROM raw_responses ORDER BY sha256').fetchall()
    if not 1<=args.workers<=12:raise SystemExit('Use 1 to 12 evidence upload workers')
    def upload_objects():
        count=0; size=0
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            for future in concurrent.futures.as_completed([pool.submit(upload,x) for x in identities]):
                length,_=future.result();count+=1;size+=length
                if count%20==0 or count==len(identities):print(f'Evidence verified {count}/{len(identities)}; {size/1e6:.1f} MB',flush=True)
    def import_table(table,expected):
        batch=[];batch_bytes=0;count=0
        with (args.export/(table+'.jsonl')).open(encoding='utf-8') as rows:
            for line in rows:
                if batch and (len(batch)>=40 or batch_bytes+len(line.encode())>1800000):
                    request('/__migration/rows',{'table':table,'rows':batch});count+=len(batch);batch=[];batch_bytes=0
                batch.append(json.loads(line));batch_bytes+=len(line.encode())
            if batch:request('/__migration/rows',{'table':table,'rows':batch});count+=len(batch)
        if count!=expected:raise RuntimeError('Local export row count mismatch')
        print(f'Records imported: {table} ({count})',flush=True)
    def import_records():
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            for future in concurrent.futures.as_completed([pool.submit(import_table,t,n) for t,n in manifest['tables'].items()]):future.result()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as stages:
        objects=stages.submit(upload_objects)
        records=stages.submit(import_records)
        records.result();objects.result()
    summary=request('/__migration/finish',{k:manifest[k] for k in ['tables','raw_objects','raw_bytes','exported_at']})
    (args.export/'import-receipt.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
