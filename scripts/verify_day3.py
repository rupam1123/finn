"""Read-only Day 1–3 gate report. An absent check is never a passing check.

Run locally against the existing full database after refreshing the repaired
pipelines. This script writes only its JSON report and exits 1 for open gates.
"""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from finn.universe import PORTFOLIO, SHOWCASE, symbol
from finn.calendar import freshness
from finn.market_data import indicators
from finn.pull import VERSION
from finn.push import analysis_key
from finn.evidence import compact
from finn.validation import has_live_usage

RESOLVED={'within_target','above_target','below_target'}


def citations(value):
    if isinstance(value,dict):
        if all(k in value for k in ('sha256','page','quote')):yield value
        else:
            for item in value.values():yield from citations(item)
    elif isinstance(value,list):
        for item in value:yield from citations(item)


def audit(path,unseen='KPIL',as_of=None):
    as_of=as_of or datetime.now(timezone.utc)
    db=sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)
    checks=[];companies={};source_pages={}
    def gate(name,passed,detail=''):
        checks.append({'name':name,'passed':bool(passed),'detail':detail})
    def snapshot(kind,ticker):
        row=db.execute('SELECT payload FROM snapshots WHERE kind=? AND symbol=?',(kind,ticker)).fetchone()
        return json.loads(row[0]) if row else None
    try:
        gate('SQLite integrity',db.execute('PRAGMA integrity_check').fetchone()[0]=='ok')
        for ticker in PORTFOLIO:
            market=snapshot('market',ticker);coverage=snapshot('filings_coverage',ticker)
            valid=False;why='No saved market snapshot'
            if market:
                try:
                    stats=indicators(market['bars'])
                    valid=(len(market['bars'])>=21 and stats['as_of']==market['indicators']['as_of']
                           and freshness(stats['as_of'],as_of)['status']=='current')
                    why=f"Latest completed session: {stats['as_of']}"
                except (ValueError,KeyError,TypeError) as exc:why=str(exc)
            gate(ticker+' current EOD data',valid,why)
            gate(ticker+' filing provider available',coverage is not None and coverage.get('status') in {'ok','partial'} and not coverage.get('errors'),
                 'Provider response completeness remains explicitly unverified; this checks availability and parser errors.')
        gate('Unseen ticker outside portfolio/showcase',unseen not in PORTFOLIO+SHOWCASE,unseen)
        warm_tickers=list(dict.fromkeys(PORTFOLIO+SHOWCASE))
        warm_missing=[t for t in warm_tickers if not (snapshot('pull',t) or {}).get('sources') or (snapshot('pull',t) or {}).get('version')!=VERSION]
        gate('Portfolio and showcase primary caches warmed',not warm_missing,
             'Missing current primary research: '+', '.join(warm_missing) if warm_missing else f'{len(warm_tickers)} current primary research caches')
        for ticker in dict.fromkeys(['INFY','DEEPAKNTR','HDFCBANK',unseen]):
            saved=snapshot('pull',ticker)
            if saved is None:
                gate(ticker+' research exists',False);continue
            gate(ticker+' current pipeline version',saved.get('version')==VERSION)
            say=saved.get('say_do',{});ledger=say.get('ledger',[])
            gate(ticker+' four delivered source periods',say.get('observed_periods')==4 and len(ledger)==4)
            resolved=sum(c.get('status') in RESOLVED for row in ledger for c in row.get('comparisons',[]))
            # A record saying "review required" is not a completed Say–Do audit.
            completed=all((row.get('status')=='compared' and any(c.get('status') in RESOLVED for c in row.get('comparisons',[])))
                          or (row.get('comparisons') and all(c.get('status')=='not_yet_due' and c.get('citations') for c in row['comparisons']))
                          or any(x.get('validation_status')=='semantic_review_required' and x.get('citations')
                                 and isinstance(x.get('assessment'),str) and len(x['assessment'].strip())>=40
                                 for x in row.get('model_assessments',[]))
                          or (row.get('status') in {'reviewed_qualitative','reviewed_no_explicit_guidance','reviewed_not_comparable'}
                              and row.get('reviewed_primary') is True and row.get('review_citations')) for row in ledger)
            gate(ticker+' four-period Say–Do acceptance',len(ledger)==4 and completed,
                 'Each period needs a supported comparison, an explicitly pending annual target, or source-linked qualitative analysis. AI analysis remains subject to user verification; this is a workflow gate, not an independent semantic-accuracy score.')
            errors=[];raw_errors=[];count=0
            for source in saved.get('sources',[]):
                digest=source['sha256']
                if source.get('source_container'):
                    from finn.documents import container_matches
                    archive=db.execute('SELECT body FROM raw_responses WHERE sha256=?',(source['source_container']['sha256'],)).fetchone()
                    if not archive or not container_matches(source,archive[0]):raw_errors.append(source['source_container']['sha256'])
                if digest not in source_pages:
                    raw=db.execute('SELECT body FROM raw_responses WHERE sha256=?',(digest,)).fetchone()
                    if not raw or hashlib.sha256(raw[0]).hexdigest()!=digest:
                        source_pages[digest]=None
                    else:
                        try:
                            from finn.pdf_runtime import pymupdf
                            with pymupdf.open(stream=raw[0],filetype='pdf') as pdf:
                                source_pages[digest]={i+1:compact(p.get_text()) for i,p in enumerate(pdf)}
                        except Exception:source_pages[digest]=None
                if source_pages[digest] is None:raw_errors.append(digest)
            for c in citations(saved):
                count+=1;pages=source_pages.get(c['sha256'])
                if c.get('evidence_type')=='page_image' and pages:
                    try:
                        raw=db.execute('SELECT body FROM raw_responses WHERE sha256=?',(c['sha256'],)).fetchone()
                        from finn.pdf_runtime import pymupdf
                        with pymupdf.open(stream=raw[0],filetype='pdf') as pdf:
                            png=pdf[c['page']-1].get_pixmap(matrix=pymupdf.Matrix(2,2),alpha=False).tobytes('png')
                        valid=hashlib.sha256(png).hexdigest()==c.get('image_sha256')
                    except Exception:valid=False
                    if not valid:errors.append({'sha256':c['sha256'],'page':c['page'],'kind':'image_identity'})
                elif not pages or not compact(c['quote']) or compact(c['quote']) not in pages.get(c['page'],''):
                    errors.append({'sha256':c['sha256'],'page':c['page']})
            gate(ticker+' raw bytes and exact-page citations',bool(saved.get('sources')) and not errors and not raw_errors)
            companies[ticker]={'sources':len(saved.get('sources',[])),'periods':say.get('observed_periods',0),
                'resolved_numerical_comparisons':resolved,'citation_count':count,'citation_errors':errors,
                'raw_errors':raw_errors,'source_errors':saved.get('source_errors',[])}
        # Content-versioned analyses must match the repaired classifier/results
        # versions; old outputs do not silently count as newly validated work.
        rows=db.execute('SELECT payload,content_hash FROM filing_versions WHERE revision=(SELECT max(w.revision) FROM filing_versions w WHERE w.id=filing_versions.id)').fetchall()
        relevant=[]
        from datetime import timedelta
        for payload,content_hash in rows:
            f=json.loads(payload)
            if f['symbol'] in PORTFOLIO and as_of-timedelta(days=30)<=datetime.fromisoformat(f['published_at'])<=as_of:
                f['content_hash']=content_hash;relevant.append(f)
        processed=sum(snapshot('push_analysis',analysis_key(f)) is not None for f in relevant)
        gate('Portfolio Push analyses use repaired versions',bool(relevant) and processed==len(relevant),f'{processed}/{len(relevant)} filings')
        readable=[];classified=0
        for filing in relevant:
            analysis=snapshot('push_analysis',analysis_key(filing))
            if not analysis or analysis.get('status')!='processed':continue
            readable.append(filing);decision=analysis.get('classification') or {}
            routine=decision.get('model_status')=='not_needed' and decision.get('buried') is True and not decision.get('critical_override')
            classified+=routine or (decision.get('model_status')=='validated_output' and has_live_usage(decision))
        gate('Readable portfolio filings have live model or routine classification',bool(readable) and classified==len(readable),
             f'{classified}/{len(readable)} readable filings; unavailable/scanned sources are separate coverage gaps. This is usage coverage, not independent accuracy.')
        required=list(dict.fromkeys(['INFY','DEEPAKNTR','HDFCBANK',unseen]))
        no_live=[t for t in required if not has_live_usage(snapshot('pull',t))]
        gate('Actual live model run recorded',not no_live,
             'Missing real provider response: '+', '.join(no_live) if no_live else 'Real usage recorded for every acceptance company; semantic review remains required.')
        return {'generated_at':as_of.isoformat(),'database':str(Path(path).name),'passed':all(c['passed'] for c in checks),
                'checks':checks,'open_gates':[c for c in checks if not c['passed']],'companies':companies,
                'limits':['Mechanical citations are not independent semantic accuracy evaluation.',
                          'Phone/browser QA and deployment belong to later phases.']}
    finally:db.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',default='data/finn.sqlite3');p.add_argument('--unseen',default='KPIL')
    p.add_argument('--out',default='verification/day3-acceptance-current.json');a=p.parse_args()
    try:report=audit(a.db,symbol(a.unseen))
    except Exception as exc:report={'passed':False,'error':str(exc),'open_gates':[{'name':'Audit could not complete','passed':False}]}
    target=Path(a.out);target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(report,indent=2))
    print(json.dumps({'passed':report['passed'],'open_gates':report['open_gates'],'report':str(target)},indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__=='__main__':main()
