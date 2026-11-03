"""Bounded primary research pipeline. Discovery tables never become evidence."""
import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from .documents import fetch_document, resolve_transcript, transcript_quality
from .evidence import citation
from .filings_ingest import fetch_nse, fetch_annual_reports
from .results_enricher import enrich_results
from .screener_scraper import fetch_screener
from .storage import Store, now_iso
from .transport import Fetcher
from .transcript_rag import chunks, retrieve, reported_quarter, quarter_evidence
from .universe import symbol, PORTFOLIO, SHOWCASE

VERSION = 'pull-v11'
TOPICS = {
 'business_snapshot': 'business products customers segments operations',
 'financial_snapshot': 'revenue profit income margin',
 'trajectory': 'growth decline demand volume',
 'narrative_vs_numbers': 'guidance target expect outlook',
 'forward_guidance': 'guidance outlook expect forecast',
 'cash_quality': 'cash flow working capital receivables inventory',
 'balance_sheet_governance': 'debt contingent liabilities related party auditor',
 'bull_bear': 'opportunity growth risk challenges uncertainty',
}


def candidate_date(candidate):
    """Prefer explicit exchange dates to undated/stale discovery links."""
    if candidate.get('published_at'):return candidate['published_at'][:10]
    text=' '.join(str(candidate.get(k,'')) for k in ('context','label','url'))
    m=re.search(r'\b(20\d{2})[-/](\d{2})[-/](\d{2})\b',text)
    if m:return '-'.join(m.groups())
    m=re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(20\d{2})',text,re.I)
    if m:
        import calendar
        month=next(i for i in range(1,13) if calendar.month_abbr[i].lower()==m[1].lower())
        return f'{m[2]}-{month:02d}-01'
    years=re.findall(r'(?:/|_|-|\b)(20\d{2})(?=/|_|-|\b)',text)
    return max(years)+'-01-01' if years else '0000-00-00'


def filing_document_kind(row):
    text=(row['title']+' '+row['description']).lower()
    path=(row.get('document_url') or '').lower()
    if 'transcript' in text:
        return None if re.search(r'annual general meeting|\bagm\b',text) else 'transcript'
    if re.search(r'annual[ _-]*report',text+' '+path) or re.search(r'[-_/]ar[-_]?20\d{2}\.pdf',path):
        return 'annual_report'
    if 'financial results' in text:return 'results'
    return None


def verified_document(store, doc):
    with store.connect() as db:
        row = db.execute('SELECT body FROM raw_responses WHERE sha256=?', (doc['sha256'],)).fetchone()
    if not row or hashlib.sha256(row['body']).hexdigest() != doc['sha256']:
        raise ValueError('Primary raw bytes absent or corrupt')
    return doc


def build_research(ticker, documents, errors, staging=None, model=None, store=None, progress=lambda event: None):
    index, financials, sources, annual = [], [], [], []
    from .say_do import analyze as analyze_say_do
    from .annual_forensics import extract_annual, extract_leverage
    for number, doc in enumerate(documents, 1):
        progress({'stage':'analysis_document','document_index':number,'documents':len(documents),
                  'kind':doc.get('kind'),'url':doc.get('url')})
        index.extend(chunks(doc))
        text = '\n'.join(p['text'] for p in doc.get('pages', []))
        statement_text='\n'.join(p['text'] for p in doc.get('pages',[]) if re.search(
            r'(?im)^.*(?:statement of.*(?:results|profit)|financial results|consolidated balance sheet).*$',p['text']))
        lender_self=re.search(r'(?i)the (?:company|group) is (?:a |an )?(?:registered )?(?:non.banking financial|banking company)',text)
        profile = ('nbfc' if lender_self and 'non' in lender_self[0].lower() else
                   'bank' if lender_self or (re.search(r'interest earned',statement_text,re.I) and re.search(r'non.performing assets|net interest income',statement_text,re.I)) else
                   'nonfinancial')
        # A short filing need not repeat the issuer's regulated industry. Keep
        # the same two assessment identity guards used by Push; missing boilerplate
        # cannot turn these lenders into industrial companies on another page.
        profile={'HDFCBANK':'bank','BAJFINANCE':'nbfc'}.get(ticker,profile)
        financials.append(enrich_results(doc, profile, model if doc.get('kind') in {'results','presentation'} else None,store))
        if doc.get('kind')=='annual_report':
            if profile=='nonfinancial':
                annual.append({**extract_annual(doc),'leverage':extract_leverage(doc),'sha256':doc['sha256']})
            else:
                annual.append({'status':'not_applicable','reason':'Industrial cash-conversion ratios are not used for lenders','source_url':doc['url'],'sha256':doc['sha256'],'facts':[],'periods':[],'leverage':[]})
        progress({'stage':'analysis_document_done','document_index':number,'documents':len(documents)})
        sources.append({k:doc.get(k) for k in ('url','sha256','fetched_at','kind','page_count','extraction_scope','omitted_page_count','source_container')})
    from .forensic_analyzer import governance_excerpts
    governance = governance_excerpts(index)
    modules = {name: {'status':'evidence_candidates' if index else 'unavailable',
                     'excerpts':retrieve(index, query, 5), 'claims_verified':False}
               for name, query in TOPICS.items()}
    # Never claim four periods merely because four PDFs were downloaded.
    extracted=[];extraction_usage=None
    if model and model.configured:
        from .say_do_model import extract as extract_observations
        try:extracted,extraction_usage=extract_observations(documents,model)
        except Exception as exc:
            from .model import model_failure
            errors.append({'stage':'say_do_extraction','error':model_failure(exc)})
    progress({'stage':'analysis_ledger','documents':len(documents)})
    say_do=analyze_say_do(documents,extracted)
    say_do['model_extraction']=extraction_usage
    from .research_views import assemble
    modules=assemble(modules,financials,annual,say_do)
    return {'version':VERSION,'symbol':ticker,'fetched_at':now_iso(),'status':'partial' if documents else 'unavailable',
            'generated_at':now_iso(),'source_observed_at':max((d['fetched_at'] for d in documents),default=None),
            'oldest_source_observed_at':min((d['fetched_at'] for d in documents),default=None),
            'sources':sources,'annual_forensics':annual,'governance':governance,'source_errors':errors,'modules':modules,'financial_statements':financials,
            'say_do':say_do,
            'source_mode':'transcripts' if any(d.get('kind')=='transcript' for d in documents) else 'annual_report_fallback' if any(d.get('kind')=='annual_report' for d in documents) else 'filings_only' if documents else 'unavailable',
            'secondary_staging_available':bool(staging), 'claims_verified':False,
            'limitations':['Excerpts are source evidence candidates, not synthesized conclusions.',
                          'Four-quarter verdicts require aligned guidance and primary actuals.']}


def research(ticker, store, emit=lambda event:None, force=False, saved_only=False, max_documents=9, model=None):
    ticker = symbol(ticker)
    sink = emit
    def emit(event):sink({'symbol':ticker,'at':now_iso(),**event})
    start = time.perf_counter()
    cached = store.get('pull',ticker)
    from .model import Flash,Reasoner
    reasoner=Reasoner(key=model.key) if isinstance(model,Flash) else model
    model_name = model.model if model and model.configured else None
    reasoning_model_name=reasoner.model if reasoner and reasoner.configured else None
    if (cached and not force and cached['data'].get('version')==VERSION
            and cached['data'].get('model_name') == model_name
            and cached['data'].get('reasoning_model_name') == reasoning_model_name
            and cached['cache_age_seconds'] < 86400
            and (not cached['last_attempt'] or cached['last_attempt']['status'] in {'partial', 'complete'})):
        emit({'stage':'cached','symbol':ticker})
        return cached['data']
    attempt = store.start_attempt('pull',ticker)
    fetcher = Fetcher(store,force=force)
    docs, errors, candidates = [], [], []
    if saved_only and cached:
        # A new model attempt replaces those stage results. Original failures
        # remain in pull_history; source failures retain their original scope.
        retried={'say_do_extraction','say_do_reasoning','reasoning'} if model and model.configured else set()
        errors.extend(e for e in cached['data'].get('source_errors',[]) if not isinstance(e,dict) or e.get('stage') not in retried)
    staging = store.get('fundamentals',ticker)
    try:
        emit({'stage':'discovery','symbol':ticker})
        if not saved_only:
            try:
                discovery_attempt=store.start_attempt('fundamentals',ticker)
                data = fetch_screener(ticker,fetcher)
                if data.get('warnings'):
                    store.finish_attempt(discovery_attempt,'unavailable',error='Incomplete staging tables',warnings=data['warnings'])
                    errors.append({'stage':'staging_tables','error':'Incomplete staging tables; previous accepted snapshot retained'})
                else:
                    store.put('fundamentals',ticker,data)
                    store.finish_attempt(discovery_attempt,'ok',source_observed_at=data.get('fetched_at'))
                staging = {'data':data}
            except Exception as exc:
                store.finish_attempt(discovery_attempt,'unavailable',error=str(exc))
                errors.append({'stage':'discovery','error':str(exc)})
            try:
                now = datetime.now(timezone.utc)
                filings = fetch_nse(ticker,now-timedelta(days=550),now,fetcher)
                for row in sorted(filings['filings'],key=lambda x:x['published_at'],reverse=True):
                    kind = filing_document_kind(row)
                    if kind and row.get('document_url'):
                        candidates.append({'url':row['document_url'],'kind':kind,'published_at':row['published_at']})
                try:
                    candidates.extend(fetch_annual_reports(ticker,fetcher))
                except Exception as exc:
                    errors.append({'stage':'annual_report_discovery','error':str(exc)})
            except Exception as exc:
                errors.append({'stage':'exchange_discovery','error':str(exc)})
        if staging:
            candidates = [d for d in staging['data']['documents'] if d['kind'] in ('transcript','annual_report','presentation')] + candidates
        with store.connect() as db:
            saved = db.execute("SELECT payload FROM snapshots WHERE (symbol=? AND kind='primary_sample') OR (kind='filing_document' AND symbol IN (SELECT id FROM filings WHERE symbol=?)) OR (kind='pull_document' AND symbol LIKE ?)",(ticker,ticker,ticker+':%')).fetchall()
        # filing_document keys are filing IDs; primary_sample is symbol-keyed.
        for row in saved:
            try:
                doc = verified_document(store,json.loads(row['payload']))
                doc['kind'] = doc.get('kind') or ('transcript' if transcript_quality(doc)['status']=='transcript_candidate' else 'results')
                if not any(d['sha256']==doc['sha256'] for d in docs):
                    docs.append(doc)
            except (ValueError,KeyError) as exc:
                errors.append({'stage':'saved_source','error':str(exc)})
        saved_by_url = {d['url']: d for d in docs}
        if not saved_only:
            candidates.sort(key=lambda c:candidate_date(c),reverse=True)
            candidates.sort(key=lambda c: ({'transcript':0,'annual_report':1,'results':2,'presentation':3}[c['kind']], 1 if 'bseindia.com' in c['url'] else 0))
            # Budgets apply to this discovery run, not all historical cache rows.
            # Otherwise five old quarters permanently prevent discovering a sixth.
            counts = dict.fromkeys(('transcript','annual_report','presentation','results'), 0)
            quarter_labels = set()
            attempted = dict.fromkeys(counts, 0)
            seen = set()
            fetched_count = 0
            for candidate in candidates:
                kind,url = candidate['kind'],candidate['url']
                if url in seen or counts[kind] >= (5 if kind=='transcript' else 2):
                    continue
                if fetched_count >= max_documents or len(seen) >= 24:
                    break
                if attempted[kind] >= (12 if kind=='transcript' else 3):
                    continue
                attempted[kind] += 1
                seen.add(url)
                emit({'stage':'document','url':url,'kind':kind})
                try:
                    # Force revalidates bytes even at a previously seen URL. Warm
                    # runs can reuse that URL while still checking new candidates.
                    if url in saved_by_url and not force:
                        doc = saved_by_url[url]
                    else:
                        downloaded = (resolve_transcript(url,fetcher) if kind=='transcript' else
                                      fetch_document(url,fetcher,section_mode=True) if kind=='annual_report' else fetch_document(url,fetcher))
                        doc = verified_document(store,downloaded)
                    if kind=='transcript' and (transcript_quality(doc)['status']!='transcript_candidate' or not reported_quarter(doc)):
                        raise ValueError('Attachment is not a full transcript')
                    if force or url not in saved_by_url:fetched_count += 1
                    doc['kind']=kind
                    if not any(d['sha256']==doc['sha256'] for d in docs):
                        docs.append(doc)
                    if kind=='transcript':
                        quarter_labels.add(reported_quarter(doc)['label'])
                        counts[kind]=len(quarter_labels)
                    else:
                        counts[kind]+=1
                    store.put('pull_document',ticker+':'+doc['sha256'],doc)
                except Exception as exc:
                    errors.append({'stage':'document','url':url,'error':str(exc)})
        emit({'stage':'analysis','documents':len(docs)})
        result = build_research(ticker,docs,errors,staging,model,store,progress=emit)
        result['model_name'] = model_name
        result['reasoning_model_name'] = reasoning_model_name
        result['source_refresh_attempted'] = not saved_only
        if model and model.configured:
            from .pull_reasoning import synthesize, audit_four_quarters
            result['reasoning'] = []
            try:
                result['say_do_reasoning'] = audit_four_quarters(result['say_do'], reasoner)
                for failure in result['say_do_reasoning'].get('errors',[]):
                    result['source_errors'].append({'stage':'say_do_reasoning',**failure})
                for comparison in result['say_do_reasoning']['comparisons']:
                    for row in result['say_do']['ledger']:
                        if row['period_end']==comparison['period']:
                            row.setdefault('model_assessments',[]).append(comparison)
            except Exception as exc:
                from .model import model_failure
                result['source_errors'].append({'stage':'say_do_reasoning','error':model_failure(exc)})
            try:
                proposal=synthesize([item for doc in docs for item in chunks(doc)],reasoner)
                result['reasoning'].append(proposal)
                for claim in proposal['proposals']:
                    result['modules'][claim['module']].setdefault('analysis',[]).append(claim)
            except Exception as exc:
                from .model import model_failure
                result['source_errors'].append({'stage':'reasoning','error':model_failure(exc)})
        result['elapsed_ms']=round((time.perf_counter()-start)*1000,2)
        if docs:
            if cached:
                previous=cached['data']
                observed=previous.get('fetched_at') or cached['fetched_at']
                store.put('pull_history',ticker+':'+observed,previous)
            store.put('pull_history',ticker+':'+result['fetched_at'],result)
            store.put('pull',ticker,result)
        store.finish_attempt(attempt,result['status'],errors=errors)
        emit({'stage':'finished','status':result['status']})
        return result
    except Exception as exc:
        store.finish_attempt(attempt,'unavailable',error=str(exc))
        raise
    finally:
        fetcher.close()


def main():
    from .settings import load_local_settings
    load_local_settings()
    p=argparse.ArgumentParser(description='Primary research ingestion; JSON progress events on stdout')
    p.add_argument('--db',default='data/finn.sqlite3')
    p.add_argument('--symbols',nargs='+',default=['INFY','DEEPAKNTR','HDFCBANK','KPIL'])
    p.add_argument('--use-model',action='store_true')
    p.add_argument('--warm',action='store_true')
    p.add_argument('--saved-only',action='store_true')
    p.add_argument('--force',action='store_true')
    p.add_argument('--workers',type=int,choices=[1,2,3],help='Default 3 for model-free warm-up, otherwise 1')
    p.add_argument('--output',default='verification/day3-pull.json')
    args=p.parse_args(); store=Store(args.db)
    from .model import Flash
    model=Flash() if args.use_model else None
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from threading import Lock, Event, Thread
    output_lock = Lock()
    active = {}
    completed = set()
    stop = Event()
    tickers = list(dict.fromkeys(PORTFOLIO + SHOWCASE if args.warm else args.symbols))
    def emit(event):
        with output_lock:
            ticker = event.get('symbol')
            if ticker in active:
                active[ticker] = {'stage':event['stage'],'changed':time.monotonic()}
            print(json.dumps(event), flush=True)
    def heartbeat():
        while not stop.wait(30):
            with output_lock:
                print(json.dumps({'stage':'heartbeat','at':now_iso(),'completed':len(completed),'total':len(tickers),
                    'active':[{'symbol':ticker,'stage':state['stage'],
                               'idle_seconds':round(time.monotonic()-state['changed'],1)} for ticker,state in active.items()]}),flush=True)
    def run(ticker):
        with output_lock:active[ticker] = {'stage':'starting','changed':time.monotonic()}
        try:
            return ticker,research(ticker,store,emit,args.force,args.saved_only,model=model)
        except Exception as exc:
            emit({'stage':'failed','symbol':ticker,'at':now_iso(),'error':str(exc)})
            return ticker,{'status':'failed','error':str(exc)}
        finally:
            with output_lock:
                active.pop(ticker,None)
                completed.add(ticker)
    output = Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    results = {}
    workers = args.workers or (3 if args.warm and model is None else 1)
    pulse = Thread(target=heartbeat,daemon=True)
    pulse.start()
    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(run,ticker) for ticker in tickers]
            for future in as_completed(futures):
                ticker,value = future.result()
                results[ticker] = value
                temporary = output.with_name(output.name+'.tmp')
                temporary.write_text(json.dumps(results,indent=2),encoding='utf-8')
                temporary.replace(output)
    finally:
        stop.set()
        pulse.join(timeout=1)
    raise SystemExit(1 if any(r.get('status') in {'failed','unavailable'} for r in results.values()) else 0)

if __name__=='__main__':
    main()
