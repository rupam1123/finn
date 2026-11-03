import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import urlencode, urlparse
from zoneinfo import ZoneInfo

from .universe import symbol

IST = ZoneInfo("Asia/Kolkata")


def filing_time(value):
    for fmt in ["%d-%b-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S"]:
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=IST).astimezone(timezone.utc).isoformat()
        except ValueError:
            pass
    try:
        dt = datetime.fromisoformat(value)
        return dt.replace(tzinfo=dt.tzinfo or IST).astimezone(timezone.utc).isoformat()
    except (ValueError, TypeError):
        raise ValueError("Unrecognized filing timestamp")


def parse_nse(payload, ticker, start, end):
    ticker = symbol(ticker)
    if not isinstance(payload, list):
        raise ValueError("NSE response is not an announcement list")
    rows, errors = [], []
    for raw in payload:
        if not isinstance(raw, dict):
            errors.append("Non-object announcement")
            continue
        if raw.get("symbol") != ticker:
            continue
        try:
            # Dissemination is the first public availability time, not receipt time.
            published = filing_time(raw.get("exchdisstime") or raw.get("an_dt") or raw.get("sort_date") or "")
            if not start <= datetime.fromisoformat(published) <= end:
                continue
            url = (raw.get("attchmntFile") or "").strip()
            if url in {"", "-", "NA", "N/A"}:
                url = None
            if url and (urlparse(url).scheme != "https" or urlparse(url).hostname not in {"nsearchives.nseindia.com", "archives.nseindia.com", "www.nseindia.com"}):
                raise ValueError("Unexpected attachment host")
            # Provider identity must survive changed text and attachment URLs.
            key = f"NSE|{ticker}|{raw['seq_id']}" if raw.get('seq_id') else f"NSE|{ticker}|{published}|{url or raw.get('desc')}"
            rows.append({"id": hashlib.sha256(key.encode()).hexdigest(), "symbol": ticker,
                "published_at": published, "source": "NSE", "title": raw.get("desc", ""),
                "description": raw.get("attchmntText", ""), "document_url": url,
                "exchange_id": raw.get("seq_id"), "isin": raw.get("sm_isin"),
                "industry": raw.get("smIndustry"), "raw": raw})
        except ValueError as exc:
            errors.append(str(exc))
    return {"filings": list({r["id"]: r for r in rows}.values()), "errors": errors,
            "coverage": "provider_response_unverified_completeness", "received_count": len(payload)}


def fetch_nse(ticker, start, end, fetcher):
    ticker = symbol(ticker)
    params = {"index": "equities", "symbol": ticker,
              "from_date": start.astimezone(IST).strftime("%d-%m-%Y"),
              "to_date": end.astimezone(IST).strftime("%d-%m-%Y")}
    url = "https://www.nseindia.com/api/corporate-announcements?" + urlencode(params)
    response = fetcher.get(url, ttl=300)
    try:
        parsed = parse_nse(json.loads(response["body"]), ticker, start, end)
    except (ValueError, TypeError):
        fetcher.store.invalidate_http(url)
        raise
    parsed.update({k: response[k] for k in ["fetched_at", "sha256", "latency_ms"]})
    parsed["source_url"] = url
    parsed["requested_range"] = {"start": start.isoformat(), "end": end.isoformat()}
    parsed["cache_hit"] = response.get("cache_hit", False)
    return parsed


def fetch_annual_reports(ticker,fetcher):
    """Exchange annual-report feed complements announcement and Screener discovery."""
    ticker=symbol(ticker)
    url='https://www.nseindia.com/api/annual-reports?'+urlencode({'index':'equities','symbol':ticker})
    response=fetcher.get(url,ttl=3600)
    try:
        data=json.loads(response['body'])
        if not isinstance(data,dict) or not isinstance(data.get('data'),list):
            raise ValueError('NSE annual-report schema changed')
        reports=[]
        for row in data['data']:
            if not isinstance(row,dict):raise ValueError('Invalid annual-report row')
            link=row.get('fileName') or ''
            parsed=urlparse(link)
            if parsed.scheme!='https' or parsed.hostname not in {'nsearchives.nseindia.com','archives.nseindia.com'}:
                continue
            if not parsed.path.lower().endswith('.pdf'):continue
            year=str(row.get('toYr',''))
            if not year.isdigit() or len(year)!=4:continue
            report={'url':link,'kind':'annual_report','context':f"Annual report {row.get('fromYr')}-{year}",
                    'report_year':year,'discovery_url':url}
            timestamp=row.get('disseminationDateTime') or row.get('broadcast_dttm')
            if timestamp and timestamp!='-':report['published_at']=filing_time(timestamp)
            reports.append(report)
        return sorted(reports,key=lambda r:r['report_year'],reverse=True)
    except (ValueError,TypeError,KeyError):
        fetcher.store.invalidate_http(url)
        raise
