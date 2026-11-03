import httpx
import pytest
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient

from finn.main import create_app
from finn.storage import Store
from finn.transport import Fetcher,FetchError


def test_durable_snapshot_and_raw_hash(tmp_path):
    path=tmp_path/"test.db"
    first=Store(path)
    first.put("fundamentals","ASTRAL",{"value":0})
    assert first.raw("https://example.com",b"test")==first.raw("https://example.com",b"test")
    second=Store(path)
    assert second.get("fundamentals","ASTRAL")["data"]["value"]==0
    assert second.get("fundamentals","ASTRAL")["cache_age_seconds"]>=0
    with pytest.raises(ValueError):first.put("market","TCS",{"value":float("nan")})


def test_insert_idempotent(tmp_path):
    store=Store(tmp_path/"test.db")
    row={"id":"1","symbol":"TCS","published_at":"2026-10-01T00:00:00+00:00"}
    store.add_filings([row,row])
    assert len(store.filings("TCS","2026-09-01"))==1


def test_concurrent_writes_and_integrity(tmp_path):
    store=Store(tmp_path/"concurrent.db")
    def write(i):
        store.put("test",str(i),{"value":i})
        store.raw("https://example.com/"+str(i),bytes([i])*10000)
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(write,range(30)))
    with store.connect() as db:
        assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        assert db.execute("SELECT count(*) FROM snapshots").fetchone()[0]==30


def test_api_missing_data_and_boundaries(tmp_path):
    path=tmp_path/"api.db"
    client=TestClient(create_app(path))
    assert client.get("/health").json()["status"]=="ok"
    assert len(client.get("/api/portfolio").json()["portfolio"])==18
    assert client.get("/api/company/ASTRAL").status_code==404
    assert client.get("/api/company/TATAMOTORS").status_code==422
    assert client.get("/api/filings/TCS?days=0").status_code==422
    assert client.get("/api/filings/TCS?days=31").status_code==422
    assert client.get("/api/universe").status_code==503
    Store(path).put("fundamentals","ASTRAL",{"symbol":"ASTRAL"})
    assert client.get("/api/company/ASTRAL").json()["data"]["symbol"]=="ASTRAL"


def test_transport_size_limit_redirect_and_retry(tmp_path):
    def respond(req):
        if req.url.path=="/large":return httpx.Response(200,content=b"x"*100)
        if req.url.path=="/redirect":return httpx.Response(302,headers={"location":"https://evil.test/a"})
        return httpx.Response(200,content=b"hello")
    fetcher=Fetcher(Store(tmp_path/"http.db"),httpx.Client(transport=httpx.MockTransport(respond)))
    assert fetcher.get("https://example.com/ok")["body"]==b"hello"
    with pytest.raises(FetchError):fetcher.get("https://example.com/large",max_bytes=10)
    with pytest.raises(FetchError):fetcher.get("https://example.com/redirect")
