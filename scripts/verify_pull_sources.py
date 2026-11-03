"""Read-only raw hash and re-extracted PDF citation audit, not semantic accuracy."""
import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path
import pymupdf


def citations(value):
    if isinstance(value,dict):
        if all(k in value for k in ('sha256','page','quote')):
            yield value
        else:
            for item in value.values():yield from citations(item)
    elif isinstance(value,list):
        for item in value:yield from citations(item)


def compact(text):return re.sub(r'\s+',' ',text).strip()


def main():
    p=argparse.ArgumentParser();p.add_argument('--db',default='data/finn.sqlite3');p.add_argument('--out',default='verification/day3-source-audit.json');a=p.parse_args()
    db=sqlite3.connect('file:'+str(Path(a.db).resolve())+'?mode=ro',uri=True)
    report={'integrity':db.execute('PRAGMA integrity_check').fetchone()[0],'companies':{},'semantic_accuracy_measured':False}
    cache={}
    for ticker,payload in db.execute("SELECT symbol,payload FROM snapshots WHERE kind='pull'"):
        research=json.loads(payload);checks=[];errors=[];quotes=0;image_citations=0
        for source in research['sources']:
            digest=source['sha256']
            if source.get('source_container'):
                from finn.documents import container_matches
                archive=db.execute('SELECT body FROM raw_responses WHERE sha256=?',(source['source_container']['sha256'],)).fetchone()
                if not archive or not container_matches(source,archive[0]):errors.append({'sha256':digest,'kind':'archive_chain'})
            if digest not in cache:
                row=db.execute('SELECT body FROM raw_responses WHERE sha256=?',(digest,)).fetchone()
                valid=bool(row and hashlib.sha256(row[0]).hexdigest()==digest)
                pages={}
                if valid:
                    with pymupdf.open(stream=row[0],filetype='pdf') as doc:
                        pages={i+1:compact(p.get_text()) for i,p in enumerate(doc)}
                cache[digest]=(valid,pages)
            checks.append({'sha256':digest,'hash_verified':cache[digest][0]})
        for c in citations(research):
            quotes+=1
            source=cache.get(c['sha256'])
            if c.get('evidence_type')=='page_image' and source and source[0]:
                image_citations+=1
                row=db.execute('SELECT body FROM raw_responses WHERE sha256=?',(c['sha256'],)).fetchone()
                try:
                    with pymupdf.open(stream=row[0],filetype='pdf') as pdf:
                        png=pdf[c['page']-1].get_pixmap(matrix=pymupdf.Matrix(2,2),alpha=False).tobytes('png')
                    valid=hashlib.sha256(png).hexdigest()==c.get('image_sha256')
                except Exception:valid=False
                if not valid:errors.append({'sha256':c['sha256'],'page':c['page'],'kind':'image_identity'})
            elif not source or not source[0] or not compact(c['quote']) or compact(c['quote']) not in source[1].get(c['page'],''):
                errors.append({'sha256':c['sha256'],'page':c['page']})
        report['companies'][ticker]={'documents':len(checks),'raw_checks':checks,'citation_count':quotes,
            'citation_errors':errors,'quarter_evidence_periods':research['say_do']['observed_periods'],
            'status':research['status'],'numeric_say_do_verified':False,'image_citations':image_citations,
            'resolved_comparisons':research['say_do'].get('resolved_comparisons',0)}
    Path(a.out).write_text(json.dumps(report,indent=2))
    print(json.dumps({'integrity':report['integrity'],'companies':len(report['companies']),
                      'citation_errors':sum(len(x['citation_errors']) for x in report['companies'].values())}))
    raise SystemExit(0 if report['integrity']=='ok' and report['companies'] and all(not x['citation_errors'] and all(c['hash_verified'] for c in x['raw_checks']) for x in report['companies'].values()) else 1)

if __name__=='__main__':main()
