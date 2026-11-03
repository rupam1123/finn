"""EOD anomalies with point-in-time links, never causal attribution."""
import math
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from .market_data import indicators

IST = ZoneInfo('Asia/Kolkata')


def alert_cutoff(session):
    return datetime.combine(datetime.fromisoformat(session).date(), time(18), IST).astimezone(timezone.utc)


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def signal_coverage(snapshot, since, as_of):
    counts = {'saved_sessions_in_window': 0, 'price_evaluable_sessions': 0, 'volume_evaluable_sessions': 0}
    if not snapshot or datetime.fromisoformat(snapshot['fetched_at']) > as_of:
        return counts
    bars = sorted(snapshot['data'].get('indicator_history') or snapshot['data'].get('bars', []), key=lambda b: b['date'])
    for index, bar in enumerate(bars):
        if since <= alert_cutoff(bar['date']) <= as_of:
            stats = indicators(bars[:index+1])
            counts['saved_sessions_in_window'] += 1
            counts['price_evaluable_sessions'] += finite(stats['return_1d_pct'])
            counts['volume_evaluable_sessions'] += finite(stats['volume_ratio_20d'])
    return counts


def signals(snapshot, filings, since, as_of, price_threshold=3.0, vol_threshold=2.0):
    if not finite(price_threshold) or not 0 < price_threshold <= 100 or not finite(vol_threshold) or not 0 < vol_threshold <= 100:
        raise ValueError('Thresholds must be finite and greater than zero, at most 100')
    if since.tzinfo is None or as_of.tzinfo is None or since > as_of:
        raise ValueError('Invalid timezone-aware window')
    if not snapshot or datetime.fromisoformat(snapshot['fetched_at']) > as_of:
        return []
    data = snapshot['data']
    bars = sorted(data.get('indicator_history') or data.get('bars', []), key=lambda b: b['date'])
    result = []
    for index, bar in enumerate(bars):
        cutoff = alert_cutoff(bar['date'])
        if not since <= cutoff <= as_of:
            continue
        stats = indicators(bars[:index+1])
        price, volume = stats['return_1d_pct'], stats['volume_ratio_20d']
        # Compare exact saved decimal inputs, not rounded/display float returns.
        price_hit = False
        if finite(price):
            current = Decimal(str(bar['adjusted_close']))
            previous = Decimal(str(bars[index-1]['adjusted_close']))
            price_hit = abs(current-previous)*100 >= previous*Decimal(str(price_threshold))
        volume_hit = False
        if finite(volume):
            prior_sum = sum(Decimal(str(b['volume'])) for b in bars[index-20:index])
            volume_hit = Decimal(str(bar['volume']))*20 > prior_sum*Decimal(str(vol_threshold))
        if not price_hit and not volume_hit:
            continue
        contemporaneous, retrospective = [], []
        for filing in filings:
            if filing['symbol'] != data['symbol']:
                continue
            published = datetime.fromisoformat(filing['published_at'])
            observed = datetime.fromisoformat(filing['observed_at'])
            if max(published, observed) > as_of or abs((published-cutoff).total_seconds()) > 48*3600:
                continue
            item = {k: filing[k] for k in ['id', 'title', 'published_at', 'observed_at', 'document_url']}
            if published <= cutoff and observed <= cutoff:
                contemporaneous.append(item)
            else:
                item['reason'] = 'published_after_alert' if published > cutoff else 'observed_after_alert'
                retrospective.append(item)
        result.append({'id': data['symbol'] + ':' + bar['date'], 'symbol': data['symbol'],
                       'session': bar['date'], 'alert_cutoff': cutoff.isoformat(), 'materiality': 75,
                       'price_triggered': price_hit, 'volume_triggered': volume_hit, 'indicators': stats,
                       'nearby_filings': contemporaneous, 'retrospective_filings': retrospective,
                       'context': 'nearby_filing' if contemporaneous else 'no_matching_filing_in_available_point_in_time_coverage',
                       'observation_mode': 'retrospective' if datetime.fromisoformat(data['fetched_at']) > cutoff else 'observed_by_cutoff',
                       'source_url': data['source_url'], 'sha256': data['sha256'],
                       'observed_at': data['fetched_at'], 'last_attempt': snapshot['last_attempt'],
                       'warnings': ['Nearby filings do not establish causation. Coverage may be incomplete.',
                                    'Historical returns use the provider adjustment basis of the saved snapshot.']})
    return sorted(result, key=lambda r: (r['alert_cutoff'], r['symbol']), reverse=True)
