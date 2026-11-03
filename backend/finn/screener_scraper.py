import re
from urllib.parse import quote, urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup

from .finance import number
from .transport import FetchError
from .universe import symbol

SECTIONS = ["quarters", "profit-loss", "balance-sheet", "cash-flow", "ratios", "shareholding"]


def parse_screener(body, ticker, url):
    ticker = symbol(ticker)
    soup = BeautifulSoup(body, "html.parser")
    info = soup.find(id="company-info")
    if info is None or soup.find(id="quarters") is None:
        raise ValueError("Not a company results page; unavailable or HTML schema changed")
    actual_path = urlparse(url).path
    if f"/company/{ticker}/" not in actual_path:
        raise ValueError("Unexpected company redirect")
    flag = info.get("data-consolidated", "").lower()
    basis = "consolidated" if flag == "true" else "standalone" if flag == "false" else "unknown"
    tables, warnings = {}, []
    for name in SECTIONS:
        sec = soup.find(id=name)
        table = sec.find("table", class_="data-table") if sec else None
        if table is None:
            warnings.append(f"Missing table: {name}")
            continue
        heads = table.select("thead th")[1:]
        periods = [{"label": h.get_text(" ", strip=True), "end_date": h.get("data-date-key")} for h in heads]
        rows = []
        for tr in table.select("tbody tr"):
            cells = tr.find_all("td", recursive=False)
            if not cells:
                continue
            label = re.sub(r"\s+", " ", cells[0].get_text(" ", strip=True)).rstrip(" +")
            values = [c.get_text(" ", strip=True) for c in cells[1:]]
            if len(values) != len(periods):
                warnings.append(f"Column mismatch: {name}/{label}")
                continue
            unit = "percent" if "%" in label else "INR_per_share" if "EPS" in label else "days" if "Days" in label or "Cycle" in label else "unknown" if name == "ratios" else "INR_crore"
            if name == "shareholding":
                unit = "count" if "Shareholders" in label else "percent"
            rows.append({"label": label, "unit": unit, "values": [
                {"raw": v, "value": str(n) if (n := number(v)) is not None else None} for v in values]})
        if not periods or not rows:
            warnings.append(f"Empty table: {name}")
        subtitle = sec.find("p", class_="sub")
        header = subtitle.get_text(" ", strip=True) if subtitle else ""
        tables[name] = {"periods": periods, "rows": rows, "basis": basis, "reported_header": header,
                        "verified_primary": False, "source_url": url}
    documents = []
    seen = set()
    docsec = soup.find(id="documents")
    if docsec:
        for group in docsec.select("div.documents"):
            heading = group.find(["h3", "h2"])
            title = heading.get_text(" ", strip=True).lower() if heading else ""
            for a in group.find_all("a", href=True):
                href = urljoin(url, a["href"])
                if urlparse(href).scheme != "https":
                    continue
                label = a.get_text(" ", strip=True)
                row = a.find_parent("li")
                context = row.get_text(" ", strip=True) if row else label
                kind = "transcript" if "transcript" in label.lower() else "annual_report" if "annual report" in title else "presentation" if label.upper() == "PPT" else "announcement" if "announcement" in title else None
                if "credit rating" in title:
                    kind = None
                if kind is None or label in {"All", "Notes", "Add Missing"} or (kind, href) in seen:
                    continue
                seen.add((kind, href))
                documents.append({"kind": kind, "url": href, "label": label, "context": context,
                                  "discovery_url": url, "primary_verified": False})
    bse_code = None
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "bseindia.com" in href:
            m = re.search(r"/(\d{6})(?:/|$)", href)
            if m:
                bse_code = m.group(1)
                break
    heading = soup.find("h1")
    if basis == "unknown":
        warnings.append("Accounting basis not observed")
    return {"symbol": ticker, "company_name": heading.get_text(" ", strip=True) if heading else ticker,
            "basis": basis, "bse_code": bse_code, "tables": tables, "documents": documents,
            "source_url": url, "source_role": "secondary_staging_and_primary_document_discovery",
            "eligible_for_pull_claims": False, "warnings": warnings}


def fetch_screener(ticker, fetcher):
    ticker = symbol(ticker)
    url = f"https://www.screener.in/company/{quote(ticker, safe='')}/consolidated/"
    try:
        result = fetcher.get(url, ttl=3600)
    except FetchError as exc:
        if "404 Not Found" not in str(exc):
            raise
        url = url.replace("consolidated/", "")
        result = fetcher.get(url, ttl=3600)
    try:
        data = parse_screener(result["body"], ticker, result["url"])
    except ValueError:
        fetcher.store.invalidate_http(url)
        raise
    data.update({k: result[k] for k in ["fetched_at", "sha256", "latency_ms"]})
    data["cache_hit"] = result.get("cache_hit", False)
    return data
