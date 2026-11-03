"""Process-local request pacing and redacted provider retry metadata."""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import math
import re
import threading
import time


class QuotaUnavailable(RuntimeError):
    pass


class RequestPacer:
    def __init__(self, clock=None, sleep=None):
        self.clock = clock or time.monotonic
        self.sleep = sleep or time.sleep
        self.lock = threading.Lock()
        self.next_start = {}
        self.blocked = {}

    def block(self, model, reason):
        with self.lock:self.blocked[model] = reason

    def wait(self, model, rpm):
        if not math.isfinite(rpm) or not 0 < rpm <= 1000:
            raise ValueError('FINN_MODEL_RPM must be finite and between 0 and 1000')
        # One shared model gate covers Flash, Reasoner and retry attempts.
        with self.lock:
            if model in self.blocked:
                raise QuotaUnavailable(self.blocked[model])
            delay = max(0, self.next_start.get(model, 0) - self.clock())
            if delay:
                self.sleep(delay)
            self.next_start[model] = self.clock() + 60 / rpm


PACER = RequestPacer()


def retry_metadata(body, header=None, default=60):
    """Never return provider messages, project IDs, headers or credential text."""
    delay = default
    if header:
        try:
            value = float(header)
        except (ValueError, TypeError):
            try:value = (parsedate_to_datetime(header) - datetime.now(timezone.utc)).total_seconds()
            except (ValueError, TypeError, OverflowError):value = default
        if math.isfinite(value):delay = max(0, value)
    identifiers = []
    try:
        data = json.loads(body)
        for detail in data.get('error', {}).get('details', []):
            kind = detail.get('@type', '')
            if kind.endswith('/google.rpc.RetryInfo'):
                value = detail.get('retryDelay', '')
                if isinstance(value,str) and re.fullmatch(r'\d+(?:\.\d+)?s', value):
                    delay = max(delay, float(value[:-1]))
            if kind.endswith('/google.rpc.QuotaFailure'):
                for item in detail.get('violations', []):
                    value = item.get('quotaId', '')
                    if isinstance(value,str) and re.fullmatch(r'Generate[A-Za-z0-9_-]{1,120}', value):
                        identifiers.append(value)
    except (ValueError, TypeError, AttributeError):
        pass
    daily = any('perday' in value.lower() for value in identifiers)
    return {'delay': delay, 'daily': daily, 'quota_ids': sorted(set(identifiers))}
