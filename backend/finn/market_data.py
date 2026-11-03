import math
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from .universe import symbol
from .storage import now_iso
from .calendar import freshness

IST = ZoneInfo("Asia/Kolkata")


def indicators(bars):
    bars = sorted(bars, key=lambda r: r["date"])
    if len({r["date"] for r in bars}) != len(bars):
        raise ValueError("Duplicate trading sessions")
    for r in bars:
        for key in ["close", "adjusted_close", "volume"]:
            if not math.isfinite(r[key]) or r[key] < 0 or (key != "volume" and r[key] == 0):
                raise ValueError("Invalid market bar")
    if not bars:
        return {"as_of": None, "return_1d_pct": None, "return_5d_pct": None,
                "volume_ratio_20d": None, "warnings": ["No completed sessions"]}
    latest = bars[-1]
    ans = {"as_of": latest["date"], "return_1d_pct": None, "return_5d_pct": None,
           "volume_ratio_20d": None, "warnings": [], "return_basis": "adjusted_close",
           "volume_basis": "provider_raw_volume"}
    if len(bars) >= 2:
        ans["return_1d_pct"] = (latest["adjusted_close"] / bars[-2]["adjusted_close"] - 1) * 100
    if len(bars) >= 6:
        ans["return_5d_pct"] = (latest["adjusted_close"] / bars[-6]["adjusted_close"] - 1) * 100
    if len(bars) >= 21:
        baseline = sum(r["volume"] for r in bars[-21:-1]) / 20
        if baseline > 0:
            ans["volume_ratio_20d"] = latest["volume"] / baseline
        else:
            ans["warnings"].append("Zero baseline volume")
    else:
        ans["warnings"].append("Fewer than 21 completed sessions")
    if any(r.get("split", 0) != 0 for r in bars[-21:]):
        ans["volume_ratio_20d"] = None
        ans["warnings"].append("Corporate action in volume window; suppress volume alert")
    return ans


def frame_bars(frame, as_of,limit=30):
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    now = as_of.astimezone(IST)
    bars = []
    for idx, r in frame.iterrows():
        day = idx.date()
        if day > now.date() or (day == now.date() and now.time() < time(18, 0)):
            continue
        bars.append({"date": day.isoformat(), "open": float(r["Open"]), "high": float(r["High"]),
                     "low": float(r["Low"]), "close": float(r["Close"]),
                     "adjusted_close": float(r["Adj Close"]), "volume": float(r["Volume"]),
                     "dividend": float(r.get("Dividends", 0)), "split": float(r.get("Stock Splits", 0))})
    return bars[-limit:]


def accept_market(store, ticker, payload, as_of, attempt_id):
    state = freshness(payload['indicators']['as_of'], as_of)
    payload['freshness'] = state
    payload['status'] = 'ok' if state['status'] == 'current' else state['status']
    if not store.put('market', ticker, payload):
        prior = store.get('market', ticker)
        result = {'status': 'rejected_older', 'symbol': ticker,
                  'error': 'Provider response is older than the saved market snapshot',
                  'received_as_of': payload['indicators']['as_of'],
                  'retained_as_of': prior['data']['indicators']['as_of'],
                  'sha256': payload['sha256'], 'freshness': state}
        store.finish_attempt(attempt_id, 'rejected_older', **{k: v for k, v in result.items() if k != 'status'})
        return result
    store.finish_attempt(attempt_id, payload['status'], source_observed_at=payload['fetched_at'],
                         received_as_of=payload['indicators']['as_of'], freshness=state)
    return payload


def fetch_market(tickers, as_of, store, force=False, exchange_fallback=False):
    tickers = [symbol(t) for t in tickers]
    results, pending, attempts = {}, [], {}
    for ticker in tickers:
        deferred = None if force else store.retry_deferred('market', ticker)
        if deferred:
            prior = store.get('market', ticker)
            results[ticker] = {'status': deferred['status'], 'symbol': ticker, 'cache_hit': True,
                              'retry_after_seconds': deferred['retry_after_seconds'],
                              'error': deferred['details'].get('error', 'Source freshness is unresolved'),
                              'retained_as_of': prior['data']['indicators']['as_of'] if prior else None}
            continue
        cached = None if force else store.reusable('market', ticker)
        if cached and freshness(cached['data']['indicators']['as_of'], as_of)['status'] == 'current':
            results[ticker] = {**cached['data'], 'cache_hit': True, 'status': 'cached'}
        else:
            pending.append(ticker)
            attempts[ticker] = store.start_attempt('market', ticker)
    if not pending:
        return results
    import yfinance as yf
    local_date = as_of.astimezone(IST).date()
    start = local_date - timedelta(days=90)
    try:
        frame = yf.download([s + '.NS' for s in pending], start=start.isoformat(),
                            end=(local_date + timedelta(days=1)).isoformat(),
                            auto_adjust=False, actions=True, group_by='ticker', threads=False,
                            progress=False, timeout=15, multi_level_index=True)
    except Exception as exc:
        for ticker in pending:
            store.finish_attempt(attempts[ticker], 'unavailable', error=str(exc))
            results[ticker] = {'status': 'unavailable', 'symbol': ticker, 'error': str(exc)}
        return results
    fallback_frames={};fallback_hashes={}
    for ticker in pending:
        digest = None
        try:
            one = frame[ticker + '.NS'].dropna(how='all', subset=['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])
            source_url = f'https://finance.yahoo.com/quote/{ticker}.NS/history/'
            digest = store.raw(source_url, one.to_json(orient='table').encode())
            bars = frame_bars(one, as_of)
            context=frame_bars(one,as_of,limit=60)
            fallback_frames[ticker]=context
            fallback_hashes[ticker]=digest
            if not bars:
                raise ValueError('Provider returned no completed sessions')
            for bar in bars:
                for key in ['open', 'high', 'low', 'close', 'adjusted_close', 'volume', 'dividend', 'split']:
                    if not math.isfinite(bar[key]) or bar[key] < 0:
                        raise ValueError(f"Invalid {key} on completed session {bar['date']}")
                if not 0 < bar['low'] <= min(bar['open'], bar['close']) <= max(bar['open'], bar['close']) <= bar['high']:
                    raise ValueError('Inconsistent OHLC range')
            stats = indicators(bars)
            payload = {'symbol': ticker, 'source': 'Yahoo Finance / yfinance', 'source_url': source_url,
                       'fetched_at': now_iso(), 'bars': bars, 'sha256': digest, 'indicators': stats,
                       'indicator_history':context,
                       'cache_hit': False,
                       'calendar_days_since_last_bar': (local_date - datetime.fromisoformat(stats['as_of']).date()).days}
            results[ticker] = accept_market(store, ticker, payload, as_of, attempts[ticker])
        except Exception as exc:
            results[ticker] = {'status': 'unavailable', 'symbol': ticker, 'error': str(exc)}
            store.finish_attempt(attempts[ticker], 'unavailable', error=str(exc), response_sha256=digest)
    if exchange_fallback:
        failed=[s for s in pending if results[s]['status']=='unavailable' and s in fallback_frames]
        if failed:
            from .nse_market import repair_latest
            results.update(repair_latest(failed,fallback_frames,as_of,store,fallback_hashes))
    return results
