from datetime import datetime, timezone

from finn import cli
from finn.storage import Store


def test_transcript_search_is_not_limited_to_digest_window(tmp_path,monkeypatch):
    class Fetcher:
        def __init__(self,store): pass
        def close(self): pass
    windows=[]
    def announcements(s,start,end,fetcher):
        days=(end-start).days
        windows.append(days)
        rows=[] if days==30 else [{"document_url":"https://nsearchives.nseindia.com/transcript.pdf", "title":"Transcript", "description":""}]
        return {"filings":rows,"errors":[],"coverage":"test"}
    def company(s,fetcher):
        return {"warnings":[],"basis":"consolidated","tables":{},"documents":[],"latency_ms":1}
    def document(url,fetcher):
        return {"url":url,"status":"text_extracted","pages":[],"claims_verified":False,
                "fetched_at":"2026-10-27T00:00:00+00:00", "quality":{"status":"transcript_candidate"}}
    monkeypatch.setattr(cli,"Fetcher",Fetcher)
    monkeypatch.setattr(cli,"fetch_nse",announcements)
    monkeypatch.setattr(cli,"fetch_screener",company)
    monkeypatch.setattr(cli,"resolve_transcript",document)
    store=Store(tmp_path/"test.db")
    _,result=cli.ingest_company("LAURUSLABS",store,datetime(2026,10,27,tzinfo=timezone.utc),primary_sample=True)
    assert windows==[30,180]
    assert result["primary_sample"]["status"]=="text_extracted"
    assert store.filings("LAURUSLABS","2026-01-01")==[]
