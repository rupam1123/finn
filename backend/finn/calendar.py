import json
from datetime import time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

CALENDAR = json.loads(Path(__file__).with_name('nse_calendar_2026.json').read_text())
IST = ZoneInfo('Asia/Kolkata')


def expected_session(as_of):
    if as_of.tzinfo is None:
        raise ValueError('as_of must be timezone-aware')
    local = as_of.astimezone(IST)
    day = local.date()
    if day.isoformat() in CALENDAR['special_sessions_pending']:
        return None
    if local.time() < time(18):
        day -= timedelta(days=1)
    for _ in range(15):
        if day.year != CALENDAR['year'] or day.isoformat() in CALENDAR['special_sessions_pending']:
            return None
        if day.weekday() < 5 and day.isoformat() not in CALENDAR['holidays']:
            return day.isoformat()
        day -= timedelta(days=1)
    return None


def freshness(session, as_of):
    expected = expected_session(as_of)
    return {'status': 'calendar_unknown' if expected is None else 'stale' if not session or session < expected else 'current',
            'expected_session': expected, 'actual_session': session,
            'calendar_source': CALENDAR['source_url'], 'calendar_verified_at': CALENDAR['verified_at'],
            'policy': 'NSE cash-market calendar; completed regular sessions after 18:00 IST; special session abstention'}
