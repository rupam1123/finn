"""Audit Day 2 against saved real primary bytes; optionally exercise real HTTP.
No artificial market/company data is inserted and no external provider is called.
"""
import argparse
import hashlib
import json
import statistics
import time
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import ProxyHandler, build_opener

from finn.evidence import compact
from finn.push import digest
from finn.storage import Store
from finn.universe import PORTFOLIO


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',default='data/finn.sqlite3')
    parser.add_argument('--base-url')
    parser.add_argument('--out',default='verification/day2-audit.json')
    args=parser.parse_args();store=Store(args.db);checks=[];verified_hashes=set()
    opener=build_opener(ProxyHandler({}))
    def check(name,passed):checks.append({'name':name,'passed':bool(passed)})
    def get(path):
        with opener.open(args.base_url.rstrip('/')+path,timeout=15) as response:return json.load(response)
    def evidence(e,doc):
        page=next((p for p in doc['pages'] if p['page']==e['page']),None)
        if e.get('evidence_type')=='page_image':
            if e['sha256']!=doc['sha256'] or e['url']!=doc['url'] or not page:return False
            try:
                from finn.documents import primary_page_image
                image=primary_page_image(doc,e['page'],store)
                return image['image_sha256']==e.get('image_sha256') and e.get('transcription') is True
            except (ValueError,KeyError):return False
        return e['sha256']==doc['sha256'] and e['url']==doc['url'] and page and compact(e['quote']) in compact(page['text'])
    reports={}
    for window in ['1d','3d','7d','30d']:
        data=get('/api/push/digest?window='+window) if args.base_url else digest(store,window)
        reports[window]=data;counts=data['counts']
        check(window+' counts reconcile',counts['scanned']==counts['surfaced']+counts['buried']==len(data['cards'])+len(data['buried']))
        check(window+' ranking', [c['classification']['materiality'] for c in data['cards']]==sorted([c['classification']['materiality'] for c in data['cards']],reverse=True))
        start,end=datetime.fromisoformat(data['since']),datetime.fromisoformat(data['as_of'])
        expected=sum(len(store.filings(s,start,end)) for s in PORTFOLIO)
        check(window+' matches deduplicated observed filing history',expected==counts['scanned'])
        check(window+' timestamp bounds',all(start<=datetime.fromisoformat(c['published_at'])<=end and datetime.fromisoformat(c['observed_at'])<=end for c in data['cards']+data['buried']))
        for alert in data['market_alerts']:
            cutoff=datetime.fromisoformat(alert['alert_cutoff'])
            check(window+' '+alert['id']+' known links use alert cutoff',all(max(datetime.fromisoformat(f['published_at']),datetime.fromisoformat(f['observed_at']))<=cutoff for f in alert['nearby_filings']))
            check(window+' '+alert['id']+' no future context',all(max(datetime.fromisoformat(f['published_at']),datetime.fromisoformat(f['observed_at']))<=end for f in alert['retrospective_filings']))
    data=reports['30d']
    for card in data['cards']+data['buried']:
        doc_info=card.get('document')
        if not doc_info:continue
        doc=store.get('filing_document',card['id'])['data']
        check(card['id']+' analyzed document identity',doc['sha256']==doc_info['sha256'])
        for claim in card['classification'].get('evidence', []):
            check(card['id']+' classification citation', evidence(claim, doc))
        if doc['sha256'] not in verified_hashes:
            with store.connect() as db:raw=db.execute('SELECT body FROM raw_responses WHERE sha256=?',(doc['sha256'],)).fetchone()
            check(doc['sha256']+' preserved source bytes',raw is not None and hashlib.sha256(raw['body']).hexdigest()==doc['sha256'])
            if doc.get('source_container'):
                from finn.documents import container_matches
                with store.connect() as db:archive=db.execute('SELECT body FROM raw_responses WHERE sha256=?',(doc['source_container']['sha256'],)).fetchone()
                check(doc['sha256']+' original archive and PDF chain',archive is not None and container_matches(doc,archive['body']))
            verified_hashes.add(doc['sha256'])
        if card['classification']['buried']:
            check(card['id']+' burial has full text and no large raster region',len(doc['pages'])==doc['page_count'] and all(p.get('requires_visual_review') is False and len(p['text'].strip())>=80 for p in doc['pages']) and not card['classification']['critical_override'])
        enrichment=card.get('enrichment') or {}
        if enrichment.get('context_evidence'):check(card['id']+' statement context evidence',evidence(enrichment['context_evidence'],doc))
        for row in enrichment.get('rows',[]):
            if row['evidence']:check(card['id']+row['metric']+' citation',evidence(row['evidence'],doc))
            if not row.get('values'):continue
            factor={'crores':Decimal(1),'millions':Decimal('.1'),'lakhs':Decimal('.01'),'billions':Decimal(100),'rupees':Decimal('.0000001')}[row['source_unit']]
            for key,raw in zip(['current','previous_quarter','year_ago'],row['raw_values']):
                if row['values'][key] is None:continue
                from finn.vision_results import money
                check(card['id']+row['metric']+key+' exact unit conversion',Decimal(row['values'][key])==money(raw)*factor)
            for label,key in [('qoq','previous_quarter'),('yoy','year_ago')]:
                current,previous=row['values']['current'],row['values'][key]
                if current is not None and previous is not None and Decimal(previous)>0 and Decimal(current)>=0:
                    expected=(Decimal(current)-Decimal(previous))/Decimal(previous)*100
                    check(card['id']+row['metric']+label+' independent Decimal delta',row[label]['percent'] is not None and abs(Decimal(str(row[label]['percent']))-expected)<Decimal('0.000000001'))
        for event in enrichment.get('events',[]):
            check(card['id']+event['name']+' event citation',evidence(event['evidence'],doc) and event['name'] in event['evidence']['quote'] and event['role'] in event['evidence']['quote'])
            if event['profile']:check(card['id']+' issuer profile citation',evidence(event['profile']['evidence'],doc) and not event['profile']['independently_verified'])
    timings=[]
    if args.base_url:
        sample = next(c['document']['sha256'] for c in data['cards'] if c.get('document') and c['symbol']=='TCS')
        with opener.open(args.base_url.rstrip('/')+'/api/evidence/'+sample+'.pdf',timeout=15) as response:
            check('HTTP saved evidence bytes match citation hash',response.headers['Content-Type']=='application/pdf' and hashlib.sha256(response.read()).hexdigest()==sample)
        for query in ['window=2d','price_threshold=0','vol_threshold=nan','as_of=2999-01-01T00:00:00Z']:
            try:get('/api/push/digest?'+query);status=200
            except HTTPError as exc:status=exc.code
            check('HTTP rejects '+query,status==422)
        for _ in range(20):
            start=time.perf_counter();get('/api/push/digest?window=7d&price_threshold=3.0&vol_threshold=2.0');timings.append((time.perf_counter()-start)*1000)
    with store.connect() as db:check('SQLite integrity',db.execute('PRAGMA integrity_check').fetchone()[0]=='ok')
    all_cards = data['cards'] + data['buried']
    document_count = sum(bool(c.get('document') and c['document'].get('page_count', 0) > 0
                              and c['document'].get('status') == 'text_extracted') for c in all_cards)
    coverage = {
        'filings': len(all_cards),
        'analysis_records': data['counts']['processed'],
        'documents_available': document_count,
        'documents_unavailable_or_unprocessed': len(all_cards) - document_count,
        'review_required': data['counts']['review_required'],
        'validated_model_outputs': sum(c['classification'].get('model_status') == 'validated_output' for c in all_cards),
        'fully_reviewed': bool(all_cards) and document_count == len(all_cards) and data['counts']['review_required'] == 0,
        'classification_accuracy': None,
        'accuracy_note': 'Passing integrity/citation checks does not measure semantic classification accuracy; independent source labels are required.'}
    summary={'passed':all(c['passed'] for c in checks),'total':len(checks),'failed':[c for c in checks if not c['passed']],
             'coverage': coverage,
             'scope':'Saved real PDF bytes, independent arithmetic, temporal bounds, and optional real local HTTP; not live AI or mobile-browser QA',
             'counts':{w:r['counts'] for w,r in reports.items()},'verified_document_hashes':len(verified_hashes),
             'http_latency_ms':{'requests':len(timings),'median':round(statistics.median(timings),2),'max':round(max(timings),2)} if timings else None,
             'checks':checks}
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(summary,indent=2))
    for w,r in reports.items():out.with_name('day2-digest-'+w+'.json').write_text(json.dumps(r,indent=2))
    print(json.dumps({k:v for k,v in summary.items() if k!='checks'},indent=2))
    raise SystemExit(0 if summary['passed'] else 1)


if __name__=='__main__':main()
