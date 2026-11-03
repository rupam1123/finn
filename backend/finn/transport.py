import time
from urllib.parse import urlparse

import httpx

from .storage import now_iso


class FetchError(RuntimeError):
    pass


class Fetcher:
    def __init__(self, store, client=None, force=False):
        self.store = store
        self.force = force
        self.client = client or httpx.Client(timeout=httpx.Timeout(20, connect=8),
            follow_redirects=False, headers={"User-Agent": "FINN-Research-Prototype/0.1", "Accept": "*/*"})

    def close(self):
        self.client.close()

    def get(self, url, max_bytes=8_000_000, ttl=0):
        started = time.perf_counter()
        cache_key = url
        original_host = urlparse(url).hostname
        if urlparse(url).scheme != "https":
            raise FetchError("HTTPS required")
        if ttl and not self.force:
            cached = self.store.cached_http(url, ttl, max_bytes)
            if cached:
                return cached
        for hop in range(4):
            for attempt in range(2):
                try:
                    with self.client.stream("GET", url) as response:
                        if response.status_code in {429, 500, 502, 503, 504} and attempt == 0:
                            time.sleep(0.5)
                            continue
                        if response.is_redirect:
                            nxt = str(response.url.join(response.headers["location"]))
                            target = urlparse(nxt)
                            if target.scheme != "https" or target.hostname != original_host or target.username or target.password or target.port not in {None, 443}:
                                raise FetchError("Cross-host redirect requires explicit approval in source adapter")
                            url = nxt
                            break
                        response.raise_for_status()
                        body = bytearray()
                        for chunk in response.iter_bytes():
                            body.extend(chunk)
                            if len(body) > max_bytes:
                                raise FetchError("Source exceeds size limit")
                        body = bytes(body)
                        result = {"url": str(response.url), "body": body, "fetched_at": now_iso(),
                                "sha256": self.store.raw(str(response.url), body),
                                "latency_ms": round((time.perf_counter()-started)*1000, 1), "cache_hit": False}
                        if ttl:
                            self.store.cache_http(cache_key, result)
                        return result
                except httpx.HTTPError as exc:
                    raise FetchError(str(exc)) from exc
            else:
                raise FetchError("Request retry budget exhausted")
        raise FetchError("Too many redirects")
