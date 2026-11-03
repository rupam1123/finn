"""Bounded owner-private hosted readback; access arrives through hidden stdin."""
import argparse
import concurrent.futures
import getpass
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import urllib.request
import urllib.error

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--export',type=Path,required=True)
args=parser.parse_args()
print('Ready for private Site verification JSON on hidden stdin.',flush=True)
auth=json.loads(getpass.getpass('') if sys.stdin.isatty() else sys.stdin.readline())
origin=auth['url'].rstrip('/')
if not origin.startswith('https://') or '/' in origin.removeprefix('https://') or not origin.endswith('.chatgpt.site'):raise SystemExit('Invalid Site origin')
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*a,**kw):return None
opener=urllib.request.build_opener(NoRedirect)
def get(path,method='GET',body=None,anonymous=False,extra=None):
    headers={} if anonymous else {'OAI-Sites-Authorization':'Bearer '+auth['bypass_token']}
    headers.update(extra or {})
    if body is not None:body=json.dumps(body).encode();headers['Content-Type']='application/json'
    try:
        with opener.open(urllib.request.Request(origin+path,data=body,headers=headers,method=method),timeout=60) as r:return r.status,r.headers.get('Content-Type',''),r.read()
    except urllib.error.HTTPError as e:return e.code,e.headers.get('Content-Type',''),e.read()
pages=['/inbox','/radar','/research','/universe','/sources','/about','/research/TCS','/research/TCS/say-do','/research/TCS/forensics','/research/TCS/filings']
api=['/health','/api/capabilities','/api/portfolio/overview','/api/universe?q=TCS','/api/push/digest?window=30d','/api/push/company/TCS?window=30d','/api/company/TCS','/api/pull/TCS','/api/pull/TCS/jobs']
report=[]
def check(path):
    status,ctype,body=get(path)
    if status!=200:raise RuntimeError('Live read failed: '+path+' HTTP '+str(status))
    if path in pages:
        if 'text/html' not in ctype or b'FINN' not in body:raise RuntimeError('Unexpected page response')
    else:
        data=json.loads(body)
        if path=='/api/capabilities' and data!={'public_review':True,'research_jobs_enabled':False}:raise RuntimeError('Read-only mode changed')
        if path=='/api/portfolio/overview' and len(data['holdings'])!=18:raise RuntimeError('Assessment universe changed')
        if path=='/api/universe?q=TCS' and data['matches'][0]['symbol']!='TCS':raise RuntimeError('Company search changed')
        if path=='/api/push/digest?window=30d' and data['counts']['scanned']!=len(data['cards'])+len(data['buried']):raise RuntimeError('Digest counts do not reconcile')
    return {'path':path,'status':status,'bytes':len(body)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    for result in pool.map(check,pages+api):report.append(result)
status,_,_=get('/api/pull/TCS/jobs','POST',{})
if status!=403:raise RuntimeError('Hosted research writes not blocked')
report.append({'path':'POST /api/pull/TCS/jobs','status':status})
status,_,_=get('/__migration/rows','POST',{'table':'read_meta','rows':[]},extra={'X-FINN-Migration-Key':auth.get('old_migration_key','')})
if status!=403:raise RuntimeError('Temporary import seal returned HTTP '+str(status))
report.append({'path':'POST /__migration/rows after secret removal','status':status})
status,ctype,body=get('/api/portfolio/overview',anonymous=True)
if status==200 and 'application/json' in ctype and 'holdings' in json.loads(body):raise RuntimeError('Private data is readable anonymously')
report.append({'path':'Anonymous portfolio read','status':status,'private_data_blocked':True})
manifest=json.loads((args.export/'manifest.json').read_text())
with sqlite3.connect(manifest['source_backup']) as db:
    pdfs=db.execute('SELECT sha256,length(body) FROM raw_responses WHERE substr(body,1,4)=? ORDER BY length(body) DESC LIMIT 1',(b'%PDF',)).fetchall()
    pdfs+=db.execute('SELECT sha256,length(body) FROM raw_responses WHERE substr(body,1,4)=? ORDER BY length(body) LIMIT 1',(b'%PDF',)).fetchall()
for sha,size in pdfs:
    req=urllib.request.Request(origin+'/api/evidence/'+sha+'.pdf',headers={'OAI-Sites-Authorization':'Bearer '+auth['bypass_token']})
    digest=hashlib.sha256();length=0
    with opener.open(req,timeout=180) as response:
        if response.status!=200:raise RuntimeError('Saved PDF readback failed')
        while chunk:=response.read(128*1024):digest.update(chunk);length+=len(chunk)
    if digest.hexdigest()!=sha or length!=size:raise RuntimeError('Saved PDF hash/size mismatch')
    report.append({'path':'Saved PDF readback','sha256':sha,'bytes':length,'verified':True})
summary={'url':origin,'passed':True,'checks':report,'scope':'Hosted HTTP/API/auth and streamed evidence readback; no physical-device or browser-layout certification'}
(args.export/'live-checks.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary),flush=True)
