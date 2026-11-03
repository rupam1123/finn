"""Read-only digest assembly from versioned, precomputed evidence."""
from datetime import datetime, timedelta, timezone, time
from zoneinfo import ZoneInfo

from .calendar import freshness,expected_session
from .classifier import classify
from .classifier import VERSION as CLASSIFIER_VERSION
from .cross_signal import signals, signal_coverage
from .evidence import fingerprint
from .management_enricher import VERSION as MANAGEMENT_VERSION
from .results_enricher import VERSION as RESULTS_VERSION
from .universe import PORTFOLIO,CATEGORIES

PIPELINE_VERSION = 'push-v2'
WINDOWS = {'1d': 1, '3d': 3, '7d': 7, '30d': 30,'latest':None}


def analysis_key(filing):
    return fingerprint({'id': filing['id'], 'content_hash': filing['content_hash'], 'pipeline': PIPELINE_VERSION,
                        'classifier': CLASSIFIER_VERSION, 'results': RESULTS_VERSION, 'management': MANAGEMENT_VERSION})


def coverage(store, kind, symbol, as_of):
    snapshot = store.get(kind, symbol)
    if snapshot and datetime.fromisoformat(snapshot['fetched_at']) > as_of:
        return {'available': False, 'status': 'no_snapshot_observed_by_as_of'}
    attempt = snapshot['last_attempt'] if snapshot else store.last_attempt(kind, symbol)
    # Never leak later status into a requested historical digest.
    if attempt and datetime.fromisoformat(attempt['finished_at'] or attempt['started_at']) > as_of:
        attempt = None
    if not snapshot:
        return {'available': False, 'status': 'unavailable', 'last_attempt': attempt}
    result = {k: snapshot[k] for k in ['fetched_at', 'cache_age_seconds', 'cache_expired']}
    age = (as_of-datetime.fromisoformat(snapshot['fetched_at'])).total_seconds()
    result.update(cache_age_seconds=round(max(0, age), 2), cache_expired=age >= snapshot['ttl_seconds'])
    result.update(available=True, last_attempt=attempt, status='cached_snapshot')
    if kind == 'market':
        result['freshness'] = freshness(snapshot['data']['indicators']['as_of'], as_of)
    else:
        result['provider_coverage'] = snapshot['data']
    return result


def digest(store, window='1d', price_threshold=3.0, vol_threshold=2.0, as_of=None, symbols=None,watch_categories=None):
    if window not in WINDOWS:
        raise ValueError('Window must be 1d, 3d, 7d, 30d or latest')
    end = as_of or datetime.now(timezone.utc)
    if end.tzinfo is None or end > datetime.now(timezone.utc):
        raise ValueError('as_of must be timezone-aware and no later than now')
    end = end.astimezone(timezone.utc)
    if window=='latest':
        session=expected_session(end)
        if not session:raise ValueError('Latest session is unavailable for this calendar date')
        start=datetime.combine(datetime.fromisoformat(session).date(),time(0),ZoneInfo('Asia/Kolkata')).astimezone(timezone.utc)
    else:start = end - timedelta(days=WINDOWS[window])
    watched=set(['results','M&A','management_change','litigation','fund_raise','capex','pledging'] if watch_categories is None else watch_categories)
    if not watched<=set(CATEGORIES):raise ValueError('Unknown watched announcement category')
    symbols = list(dict.fromkeys(PORTFOLIO if symbols is None else symbols))
    cards, buried, alerts, sources = [], [], [], {}
    processed = 0
    for symbol in symbols:
        # Extra two days support only nearby-filing context, not digest count inflation.
        context = store.filings(symbol, start-timedelta(hours=48), end)
        selected = [f for f in context if datetime.fromisoformat(f['published_at']) >= start]
        for filing in selected:
            card, was_processed = filing_card(store, filing, end)
            processed += was_processed
            decision = card['classification']
            (buried if decision['buried'] else cards).append(card)
        snapshot = store.get('market', symbol)
        if snapshot:
            # Do not mutate the original last-attempt record.
            snapshot['last_attempt'] = coverage(store, 'market', symbol, end).get('last_attempt')
        alerts.extend(signals(snapshot, context, start, end, price_threshold, vol_threshold))
        sources[symbol] = {'filings': coverage(store, 'filings_coverage', symbol, end),
                           'market': coverage(store, 'market', symbol, end)}
        sources[symbol]['market']['signal_coverage'] = signal_coverage(snapshot, start, end)
    cards.sort(key=lambda c: (c['classification']['materiality'], c['published_at'], c['id']), reverse=True)
    buried.sort(key=lambda c: (c['published_at'], c['id']), reverse=True)
    alerts.sort(key=lambda a: (a['materiality'], a['alert_cutoff'], a['id']), reverse=True)
    total = len(cards)+len(buried)
    filing_alerts=[{'filing_id':c['id'],'symbol':c['symbol'],'category':c['classification']['category'],
                    'published_at':c['published_at'],'status':'needs_review' if c['classification']['review_required'] else 'material',
                    'reason':c['classification']['reason']} for c in cards if c['classification']['category'] in watched and c['classification']['materiality']>=60]
    return {'window': window, 'since': start.isoformat(), 'as_of': end.isoformat(),
            'watch_categories':sorted(watched),'announcement_alerts':filing_alerts,
            'thresholds': {'price_pct_inclusive': price_threshold, 'volume_ratio_exclusive': vol_threshold},
            'counts': {'scanned': total, 'surfaced': len(cards), 'buried': len(buried),
                       'review_required': sum(c['classification']['review_required'] for c in cards),
                       'processed': processed, 'unprocessed': total-processed, 'market_alerts': len(alerts)},
            'cards': cards, 'buried': buried, 'market_alerts': alerts, 'coverage': sources,
            'status': 'cached_partial_coverage', 'pipeline_version': PIPELINE_VERSION,
            'warnings': ['Cached evidence, not a live feed. Refresh status and source times are shown separately.',
                         'Surfaced includes unknown/review items, not just material events.',
                         'Some earlier sessions lack the 20 prior observations needed for volume alerts; an absent alert does not prove normal volume.',
                         'No matching filing does not prove absence. Backfilled observations cannot establish historical completeness.'],
            'history_policy': 'Only revisions and analyses observed by as_of; latest market snapshot must also have been observed by then.'}


def filing_card(store, filing, end):
    saved = store.get('push_analysis', analysis_key(filing))
    analysis = saved['data'] if saved and datetime.fromisoformat(saved['fetched_at']) <= end else None
    if analysis and analysis.get('filing_content_hash') != filing['content_hash']:
        analysis = None
    if analysis:
        decision = analysis['classification']
    else:
        decision = classify(filing)
    card = {k: filing[k] for k in ['id', 'symbol', 'title', 'description', 'published_at', 'observed_at', 'document_url', 'revision', 'content_hash']}
    card.update(classification=decision,
                enrichment=analysis.get('enrichment') if analysis else None,
                analysis_status=analysis['status'] if analysis else 'not_processed',
                analyzed_at=saved['fetched_at'] if analysis else None,
                document=analysis.get('document') if analysis else None,
                last_attempt=store.last_attempt('push_analysis', analysis_key(filing)))
    if card['last_attempt'] and datetime.fromisoformat(card['last_attempt']['finished_at'] or card['last_attempt']['started_at']) > end:
        card['last_attempt'] = None
    if decision['buried'] and card['last_attempt'] and card['last_attempt']['status'] not in {'processed', 'cached'}:
        decision = {**decision, 'buried': False, 'review_required': True,
                    'reason': 'Latest document refresh failed or is incomplete; previous routine decision needs review'}
        card['classification'] = decision
    return card, bool(analysis)
