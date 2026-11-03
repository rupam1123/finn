import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
from finn.pdf_runtime import pymupdf
import pytest

from finn.documents import document_url, extract_document
from finn.filings_ingest import parse_nse
from finn.screener_scraper import parse_screener, fetch_screener
from finn.storage import Store
from finn.transport import FetchError, Fetcher
from finn.universe import CATEGORIES, PORTFOLIO, SHOWCASE, symbol, parse_master

FIX = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("ticker,file", [("TCS","tcs.html"),("HDFCBANK","hdfcbank.html")])
def test_real_html_parser(ticker,file):
    result = parse_screener((FIX/file).read_bytes(),ticker,f"https://www.screener.in/company/{ticker}/consolidated/")
    assert result["basis"] == "consolidated"
    assert len(result["tables"]) == 6
    assert not result["eligible_for_pull_claims"]
    assert any(d["kind"] == "transcript" for d in result["documents"])
    assert any(d["kind"] == "annual_report" for d in result["documents"])
    assert all(not table["verified_primary"] for table in result["tables"].values())
    rows = result["tables"]["quarters"]["rows"]
    assert next(r for r in rows if "EPS" in r["label"])["unit"] == "INR_per_share"


def test_no_silent_html_success():
    with pytest.raises(ValueError): parse_screener("<h1>Access denied</h1>","TCS","https://www.screener.in/company/TCS/")


def test_no_standalone_fallback_on_block(tmp_path):
    requests=[]
    def respond(req):
        requests.append(str(req.url))
        return httpx.Response(403)
    fetcher=Fetcher(Store(tmp_path/"a.db"),httpx.Client(transport=httpx.MockTransport(respond)))
    with pytest.raises(FetchError): fetch_screener("TCS",fetcher)
    assert len(requests)==1


def test_real_announcements_and_dedup():
    payload=json.loads((FIX/"nse.json").read_text())
    start=datetime(2026,10,1,tzinfo=timezone.utc)
    end=datetime(2026,10,27,tzinfo=timezone.utc)
    out=parse_nse(payload+payload,"TCS",start,end)
    assert len(out["filings"])==len(payload)
    assert out["errors"]==[]
    assert all(row["symbol"]=="TCS" for row in out["filings"])
    assert out["filings"][0]["published_at"].endswith("+00:00")


def test_wrong_symbol_and_invalid_feed():
    start=datetime(2026,10,1,tzinfo=timezone.utc)
    end=datetime(2026,10,27,tzinfo=timezone.utc)
    with pytest.raises(ValueError):parse_nse({"error":"denied"},"TCS",start,end)
    assert parse_nse([{"symbol":"INFY"}],"TCS",start,end)["filings"]==[]
    assert parse_nse([{"symbol":"TCS","an_dt":"nonsense"}],"TCS",start,end)["errors"]


def test_no_attachment_is_valid_disclosure():
    start=datetime(2026,10,1,tzinfo=timezone.utc)
    end=datetime(2026,10,27,tzinfo=timezone.utc)
    row={"symbol":"TMPV","an_dt":"10-Oct-2026 12:00:00","attchmntFile":"-", "desc":"News verification"}
    result=parse_nse([row],"TMPV",start,end)
    assert not result["errors"]
    assert len(result["filings"])==1
    assert result["filings"][0]["document_url"] is None


@pytest.mark.parametrize("bad", ["../TCS", "https://evil.test", "TATA MOTORS", "", "TATAMOTORS"])
def test_bad_symbols(bad):
    with pytest.raises(ValueError):symbol(bad)


def test_universe():
    assert len(PORTFOLIO)==len(set(PORTFOLIO))==18
    assert len(SHOWCASE)==5 and not set(SHOWCASE)&set(PORTFOLIO)
    assert len(CATEGORIES)==17
    assert symbol(" astral.ns ")=="ASTRAL"
    assert symbol("zomato")=="ETERNAL"
    assert parse_master("SYMBOL,NAME OF COMPANY, SERIES, ISIN NUMBER\nABC,Example, EQ, INE0000\n")[0]["symbol"]=="ABC"


def test_safe_document_urls():
    with pytest.raises(ValueError):document_url("https://127.0.0.1/a.pdf")
    with pytest.raises(ValueError):document_url("https://www.tcs.com.evil.test/a.pdf")
    assert document_url("https://www.bseindia.com/stockinfo/AnnPdfOpen.aspx?Pname=test.pdf").endswith("AttachLive/test.pdf")


def test_pdf_pages_and_scan_abstention():
    doc=pymupdf.open()
    page=doc.new_page()
    page.insert_text((40,40),"Synthetic parser test: revenue guidance is twenty percent. This is not company evidence.")
    out=extract_document(doc.tobytes(),"https://www.tcs.com/test.pdf")
    assert out["status"]=="text_extracted" and out["pages"][0]["page"]==1
    assert not out["claims_verified"]
    doc=pymupdf.open();doc.new_page()
    assert extract_document(doc.tobytes(),"test")["status"]=="ocr_required"
    with pytest.raises(ValueError):extract_document(b"<html>blocked</html>","test")
