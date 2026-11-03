import os
import hashlib
import re
import json
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

from .storage import Store, SCHEMA_VERSION
from .calendar import freshness
from .documents import transcript_quality
from .universe import PORTFOLIO, SHOWCASE, symbol
from .push import digest


def create_app(db_path=None):
    store = Store(db_path or os.getenv("FINN_DB", "data/finn.sqlite3"))
    app = FastAPI(title="FINN ingestion API", version="0.1.0")
    origins = [x.strip().rstrip('/') for x in os.getenv("FINN_ALLOWED_ORIGINS", "http://localhost:3000").split(",") if x.strip() and x.strip() != '*']
    origins=list(dict.fromkeys(origins+['http://localhost:3000','http://127.0.0.1:3000']))
    public_review = os.getenv('FINN_PUBLIC_REVIEW', '0') == '1'
    app.add_middleware(CORSMiddleware, allow_origins=origins,
                       allow_methods=["GET", "POST"], allow_headers=["Accept", "Content-Type"])

    @app.middleware('http')
    async def protect_response(request: Request, call_next):
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        if request.url.path.startswith('/api/') and not request.url.path.endswith('.pdf'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.get('/api/capabilities')
    def capabilities():
        return {'public_review': public_review, 'research_jobs_enabled': not public_review}

    def checked(value):
        try:
            return symbol(value)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    from .workspace_api import install,annotate_quotes
    install(app,store,checked)

    @app.get("/health")
    def health():
        with store.connect() as db:
            db.execute("SELECT 1").fetchone()
        return {"status": "ok", "phase": "day3_research", "schema_version": SCHEMA_VERSION}

    @app.get("/api/push/digest")
    def push_digest(window: Literal['1d', '3d', '7d', '30d','latest'] = '1d',
                    price_threshold: float = Query(3.0, gt=0, le=100, allow_inf_nan=False),
                    vol_threshold: float = Query(2.0, gt=0, le=100, allow_inf_nan=False),
                    as_of: datetime | None = None,watch_categories: str | None = None):
        try:
            watched=None if watch_categories is None else [c for c in watch_categories.split(',') if c]
            return annotate_quotes(digest(store, window, price_threshold, vol_threshold, as_of,watch_categories=watched))
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.get('/api/evidence/{sha256}.pdf')
    def evidence_pdf(sha256: str):
        if not re.fullmatch(r'[0-9a-f]{64}', sha256):
            raise HTTPException(422, 'Expected a SHA-256 document hash')
        with store.connect() as db:
            row = db.execute('SELECT body FROM raw_responses WHERE sha256=?', (sha256,)).fetchone()
        if not row or not row['body'].startswith(b'%PDF'):
            raise HTTPException(404, 'Saved primary PDF not found')
        if hashlib.sha256(row['body']).hexdigest() != sha256:
            raise HTTPException(503, 'Saved evidence integrity check failed')
        return Response(row['body'], media_type='application/pdf', headers={
            'ETag': '"'+sha256+'"', 'Cache-Control': 'public, max-age=31536000, immutable',
            'Content-Disposition': 'inline; filename="'+sha256+'.pdf"',
            'X-Content-Type-Options': 'nosniff', 'Content-Security-Policy': "default-src 'none'; sandbox"})

    @app.get("/api/portfolio")
    def portfolio():
        return {"portfolio": PORTFOLIO, "showcase": SHOWCASE}

    @app.get("/api/universe")
    def universe(q: str = Query("", max_length=60)):
        cached = store.get("universe", "NSE")
        if not cached:
            raise HTTPException(503, "Security master not ingested")
        from difflib import SequenceMatcher
        query = q.strip().upper()
        rows = cached["data"]["companies"]
        def score(row):
            ticker,name=row['symbol'],row['company_name'].upper()
            if not query:return 1
            if query==ticker:return 10
            if ticker.startswith(query):return 8
            if query in name or query in ticker:return 6+max((SequenceMatcher(None,query,word).ratio() for word in name.split()),default=0)
            if len(query)<3:return 0
            return max(SequenceMatcher(None,query,ticker).ratio(),SequenceMatcher(None,query,name[:len(query)+5]).ratio()) if len(query)>=3 else 0
        with store.connect() as db:
            available={r['symbol'] for r in db.execute("SELECT symbol FROM snapshots WHERE kind='pull'")}
        rows=[{**r,'research_available':r['symbol'] in available} for r in rows]
        ranked=sorted(((score(row),row) for row in rows),key=lambda pair:(-pair[0],pair[1]['symbol']))
        return {"fetched_at":cached['fetched_at'],"total":len(rows),"matches":[row for score,row in ranked if score>=.65][:30]}

    @app.get('/api/portfolio/overview')
    def portfolio_overview():
        # One connection; never decode every large Pull workspace just to check
        # whether it exists. This endpoint is called on every fresh app load.
        slots=','.join('?' for _ in PORTFOLIO)
        with store.connect() as db:
            markets = {r['symbol']:r for r in db.execute(f"SELECT symbol,payload,fetched_at FROM snapshots WHERE kind='market' AND symbol IN ({slots})",PORTFOLIO)}
            names = {r['symbol']:r['name'] for r in db.execute(f"SELECT symbol,json_extract(payload,'$.company_name') AS name FROM snapshots WHERE kind='fundamentals' AND symbol IN ({slots})",PORTFOLIO)}
            available = {r['symbol'] for r in db.execute(f"SELECT symbol FROM snapshots WHERE kind='pull' AND symbol IN ({slots})",PORTFOLIO)}
            counts = {r['symbol']:r['n'] for r in db.execute(f'SELECT symbol,count(*) AS n FROM filings WHERE symbol IN ({slots}) GROUP BY symbol',PORTFOLIO)}
            attempts = {r['symbol']:r['status'] for r in db.execute("SELECT a.symbol,a.status FROM attempts a WHERE a.kind='market' AND a.id=(SELECT max(b.id) FROM attempts b WHERE b.kind='market' AND b.symbol=a.symbol)")}
        holdings=[]
        for ticker in PORTFOLIO:
            row=markets.get(ticker)
            market=json.loads(row['payload']) if row else None
            if market:
                market['freshness']=freshness(market.get('indicators',{}).get('as_of'),datetime.now(timezone.utc))
            holdings.append({'symbol':ticker,'name':names.get(ticker) or ticker,
                'market':market,'observed_at':row['fetched_at'] if row else None,
                'research_available':ticker in available,'filing_count':counts.get(ticker,0),
                'latest_attempt':attempts.get(ticker)})
        return {'holdings':holdings,'showcase':SHOWCASE,'as_of':datetime.now(timezone.utc).isoformat(),
                'mode':'saved_snapshots','replay':os.getenv('FINN_QA_REPLAY')=='1','note':'No network or model requests are made by this endpoint.'}

    @app.get("/api/company/{ticker}")
    def company(ticker: str):
        s = checked(ticker)
        snapshot = store.get("fundamentals", s)
        if snapshot is None:
            attempt = store.last_attempt("fundamentals", s)
            if attempt:
                raise HTTPException(503, {"code": "source_unavailable", "last_attempt": attempt})
            raise HTTPException(404, {"code": "not_ingested", "symbol": s,
                                      "message": "Company staging data is not cached. Submit a research job in the Pull workspace."})
        snapshot['source_status'] = {}
        for kind in ['market', 'filings_coverage', 'primary_sample']:
            saved = store.get(kind, s)
            attempt = saved['last_attempt'] if saved else store.last_attempt(kind, s)
            snapshot['source_status'][kind] = {
                'available': saved is not None, 'fetched_at': saved['fetched_at'] if saved else None,
                'cache_expired': saved['cache_expired'] if saved else True, 'last_attempt': attempt}
            if kind == 'market' and saved:
                snapshot['source_status'][kind]['freshness'] = freshness(saved['data']['indicators']['as_of'], datetime.now(timezone.utc))
        return snapshot

    @app.get("/api/market/{ticker}")
    def market(ticker: str):
        s = checked(ticker)
        snapshot = store.get("market", s)
        if snapshot is None:
            attempt = store.last_attempt("market", s)
            raise HTTPException(503 if attempt else 404, {"message": "Market data unavailable", "last_attempt": attempt})
        snapshot["freshness"] = freshness(snapshot["data"]["indicators"]["as_of"], datetime.now(timezone.utc))
        return snapshot

    @app.get("/api/filings/{ticker}")
    def filings(ticker: str, days: int = Query(1, ge=1, le=30), as_of: datetime | None = None):
        s = checked(ticker)
        now = datetime.now(timezone.utc)
        if as_of is not None and (as_of.tzinfo is None or as_of > now):
            raise HTTPException(422, "as_of must be timezone-aware and no later than now")
        end = (as_of or now).astimezone(timezone.utc)
        since = (end - timedelta(days=days)).isoformat()
        return {"symbol": s, "since": since, "as_of": end.isoformat(),
                "filings": store.filings(s, since, end), "ingestion": store.get("filings_coverage", s),
                "last_attempt": store.last_attempt("filings_coverage", s),
                "history_policy": "Only revisions observed by as_of; legacy observations start at schema-2 migration"}

    @app.get("/api/primary/{ticker}")
    def primary(ticker: str):
        s = checked(ticker)
        snapshot = store.get("primary_sample", s)
        if snapshot is None:
            attempt = store.last_attempt("primary_sample", s)
            raise HTTPException(503 if attempt else 404, {"message": "Primary transcript unavailable", "last_attempt": attempt})
        snapshot['data']['quality'] = transcript_quality(snapshot['data'])
        if snapshot['data']['quality']['status'] != 'transcript_candidate':
            raise HTTPException(503, {"message": "Stored document is not a suitable full transcript; refresh required",
                                      "last_attempt": snapshot['last_attempt']})
        return snapshot

    from .pull_jobs import initialize, enqueue, get_job, QueueLimit
    initialize(store)

    @app.get('/api/pull/{ticker}')
    def pull_research(ticker: str):
        snapshot = store.get('pull', checked(ticker))
        if snapshot is None:
            raise HTTPException(404, 'Research not available; submit a research job')
        from .workspace_projection import consecutive_ledger
        from .workspace_api import annotate_quotes
        annotate_quotes(snapshot['data'])
        snapshot['data']['say_do']=consecutive_ledger(snapshot['data'].get('say_do',{}))
        return snapshot

    @app.post('/api/pull/{ticker}/jobs', status_code=202)
    def pull_job(ticker: str, request: Request, refresh: bool = False):
        if public_review:
            raise HTTPException(403, 'Public review is read-only. Source discovery is available in the local owner session.')
        origin=request.headers.get('origin')
        if request.headers.get('sec-fetch-site') == 'cross-site' or (origin and origin.rstrip('/') not in origins):
            raise HTTPException(403, 'Research requests must come from a configured workspace origin.')
        try:
            return enqueue(store, checked(ticker), refresh=refresh, api_budget=True)
        except QueueLimit as exc:
            raise HTTPException(429,str(exc),headers={'Retry-After':'3600'}) from None

    @app.get('/api/pull/{ticker}/jobs')
    def active_pull_job(ticker: str):
        with store.connect() as db:
            row = db.execute("SELECT id FROM pull_jobs WHERE symbol=? AND status IN ('queued','running') ORDER BY updated_at DESC LIMIT 1", (checked(ticker),)).fetchone()
        return {'active': get_job(store, row['id']) if row else None}

    @app.get('/api/pull-jobs/{job_id}')
    def job_status(job_id: str):
        result = get_job(store, job_id)
        if result is None:
            raise HTTPException(404, 'Unknown research job')
        return result

    @app.get('/api/pull-jobs/{job_id}/events')
    def job_events(job_id: str):
        if get_job(store, job_id) is None:
            raise HTTPException(404, 'Unknown research job')
        async def events():
            import asyncio
            import json
            for _ in range(30):
                job = get_job(store, job_id)
                yield 'data: ' + json.dumps(job) + '\n\n'
                if job['status'] not in ('queued', 'running'):
                    return
                await asyncio.sleep(1)
        return StreamingResponse(events(), media_type='text/event-stream', headers={'Cache-Control':'no-cache'})

    return app


app = create_app()
