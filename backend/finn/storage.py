import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock

DB_LOCK = RLock()
SCHEMA_VERSION = 2
CACHE_TTLS = {'pull': 86400, 'fundamentals': 3600, 'market': 900, 'filings_coverage': 300,
              'primary_sample': 86400, 'universe': 86400}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def utc_iso(value):
    dt = datetime.fromisoformat(value) if isinstance(value, str) else value
    return dt.replace(tzinfo=dt.tzinfo or timezone.utc).astimezone(timezone.utc).isoformat()


def canonical_filing(row):
    row = dict(row)
    if row.get('source') == 'NSE' and row.get('exchange_id'):
        key = f"NSE|{row['symbol']}|{row['exchange_id']}"
        row['id'] = hashlib.sha256(key.encode()).hexdigest()
    row['published_at'] = utc_iso(row['published_at'])
    return row


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                PRAGMA journal_mode=DELETE;
                CREATE TABLE IF NOT EXISTS schema_version(version INTEGER PRIMARY KEY);
                CREATE TABLE IF NOT EXISTS snapshots(
                    kind TEXT, symbol TEXT, fetched_at TEXT, payload TEXT, PRIMARY KEY(kind,symbol));
                CREATE TABLE IF NOT EXISTS raw_responses(
                    sha256 TEXT PRIMARY KEY, url TEXT, fetched_at TEXT, body BLOB);
                CREATE TABLE IF NOT EXISTS filings(
                    id TEXT PRIMARY KEY, symbol TEXT, published_at TEXT, payload TEXT);
                CREATE TABLE IF NOT EXISTS runs(id INTEGER PRIMARY KEY, started_at TEXT, payload TEXT);
                CREATE TABLE IF NOT EXISTS attempts(
                    id INTEGER PRIMARY KEY, kind TEXT, symbol TEXT, started_at TEXT,
                    finished_at TEXT, status TEXT, details TEXT);
                CREATE INDEX IF NOT EXISTS attempts_source ON attempts(kind,symbol,id);
                CREATE TABLE IF NOT EXISTS http_cache(url TEXT PRIMARY KEY, payload TEXT);
                CREATE TABLE IF NOT EXISTS filing_versions(
                    id TEXT, revision INTEGER, symbol TEXT, observed_at TEXT,
                    published_at TEXT, content_hash TEXT, payload TEXT, PRIMARY KEY(id,revision));
                CREATE INDEX IF NOT EXISTS filing_window ON filing_versions(symbol,published_at,observed_at);
            ''')
            db.execute('BEGIN IMMEDIATE')
            version = db.execute('SELECT max(version) FROM schema_version').fetchone()[0] or 0
            if version < SCHEMA_VERSION:
                rows = db.execute('SELECT payload FROM filings ORDER BY rowid').fetchall()
                for row in rows:
                    self._filing(db, json.loads(row['payload']), now_iso())
                db.execute('DELETE FROM filings')
                db.execute('''INSERT INTO filings SELECT v.id,v.symbol,v.published_at,v.payload
                    FROM filing_versions v WHERE v.revision=(SELECT max(w.revision)
                    FROM filing_versions w WHERE w.id=v.id)''')
                db.execute('DELETE FROM schema_version')
                db.execute('INSERT INTO schema_version VALUES(?)', (SCHEMA_VERSION,))

    @contextmanager
    def connect(self):
        with DB_LOCK:
            db = sqlite3.connect(self.path, timeout=10)
            db.row_factory = sqlite3.Row
            try:
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise
            finally:
                db.close()

    def raw(self, url, body):
        digest = hashlib.sha256(body).hexdigest()
        with self.connect() as db:
            db.execute('INSERT OR IGNORE INTO raw_responses VALUES(?,?,?,?)', (digest, url, now_iso(), body))
        return digest

    def put(self, kind, symbol, payload):
        encoded = json.dumps(payload, allow_nan=False)
        observed = utc_iso(payload.get('fetched_at') or now_iso())
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            previous = db.execute('SELECT payload FROM snapshots WHERE kind=? AND symbol=?', (kind, symbol)).fetchone()
            if previous and kind == 'market':
                old = json.loads(previous['payload'])
                prior_date = old.get('indicators', {}).get('as_of')
                new_date = payload.get('indicators', {}).get('as_of')
                if prior_date and (not new_date or new_date < prior_date):
                    return False
                if prior_date == new_date and old.get('fetched_at') and observed < utc_iso(old['fetched_at']):
                    return False
            db.execute('INSERT OR REPLACE INTO snapshots VALUES(?,?,?,?)', (kind, symbol, observed, encoded))
        return True

    def start_attempt(self, kind, symbol):
        with self.connect() as db:
            return db.execute('INSERT INTO attempts(kind,symbol,started_at,status,details) VALUES(?,?,?,?,?)',
                              (kind, symbol, now_iso(), 'refreshing', '{}')).lastrowid

    def finish_attempt(self, attempt_id, status, **details):
        with self.connect() as db:
            db.execute('UPDATE attempts SET finished_at=?,status=?,details=? WHERE id=?',
                       (now_iso(), status, json.dumps(details, allow_nan=False), attempt_id))

    def last_attempt(self, kind, symbol):
        with self.connect() as db:
            row = db.execute('SELECT * FROM attempts WHERE kind=? AND symbol=? ORDER BY id DESC LIMIT 1', (kind, symbol)).fetchone()
        if row is None:
            return None
        return {**dict(row), 'details': json.loads(row['details'])}

    def get(self, kind, symbol):
        with self.connect() as db:
            row = db.execute('SELECT * FROM snapshots WHERE kind=? AND symbol=?', (kind, symbol)).fetchone()
            attempt = db.execute('SELECT * FROM attempts WHERE kind=? AND symbol=? ORDER BY id DESC LIMIT 1', (kind, symbol)).fetchone()
        if not row:
            return None
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(row['fetched_at'])).total_seconds()
        ttl = CACHE_TTLS.get(kind, 0)
        return {'fetched_at': row['fetched_at'], 'last_success_at': row['fetched_at'], 'cache_age_seconds': round(max(0, age), 2),
                'cache_expired': age < 0 or age >= ttl, 'ttl_seconds': ttl,
                'last_attempt': {**dict(attempt), 'details': json.loads(attempt['details'])} if attempt else None,
                'data': json.loads(row['payload'])}

    def reusable(self, kind, symbol):
        snapshot = self.get(kind, symbol)
        if not snapshot or snapshot['cache_expired']:
            return None
        attempt = snapshot['last_attempt']
        if attempt and attempt['status'] not in {'ok', 'cached', 'text_extracted'}:
            return None
        return snapshot

    def retry_deferred(self, kind, symbol, seconds=300):
        attempt = self.last_attempt(kind, symbol)
        if not attempt or attempt['status'] not in {'unavailable', 'rejected_older', 'stale', 'calendar_unknown'} or not attempt['finished_at']:
            return None
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(attempt['finished_at'])).total_seconds()
        if 0 <= age < seconds:
            return {**attempt, 'retry_after_seconds': round(seconds-age, 2)}
        return None

    def cached_http(self, url, ttl, max_bytes):
        with self.connect() as db:
            row = db.execute('SELECT payload FROM http_cache WHERE url=?', (url,)).fetchone()
            if not row:
                return None
            data = json.loads(row['payload'])
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(data['fetched_at'])).total_seconds()
            if not 0 <= age < ttl:
                return None
            raw = db.execute('SELECT body FROM raw_responses WHERE sha256=?', (data['sha256'],)).fetchone()
        if not raw or len(raw['body']) > max_bytes or hashlib.sha256(raw['body']).hexdigest() != data['sha256']:
            return None
        return {**data, 'body': raw['body'], 'cache_hit': True, 'latency_ms': 0.0}

    def cache_http(self, url, response):
        data = {k: response[k] for k in ['url', 'fetched_at', 'sha256']}
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO http_cache VALUES(?,?)', (url, json.dumps(data)))

    def invalidate_http(self, url):
        with self.connect() as db:
            db.execute('DELETE FROM http_cache WHERE url=?', (url,))

    def _filing(self, db, row, observed_at):
        row = canonical_filing(row)
        encoded = json.dumps(row, sort_keys=True, allow_nan=False)
        digest = hashlib.sha256(encoded.encode()).hexdigest()
        old = db.execute('SELECT revision,content_hash,observed_at FROM filing_versions WHERE id=? ORDER BY revision DESC LIMIT 1', (row['id'],)).fetchone()
        if old and (old['content_hash'] == digest or observed_at < old['observed_at']):
            return
        revision = old['revision'] + 1 if old else 1
        db.execute('INSERT INTO filing_versions VALUES(?,?,?,?,?,?,?)',
                   (row['id'], revision, row['symbol'], observed_at, row['published_at'], digest, encoded))
        db.execute('INSERT OR REPLACE INTO filings VALUES(?,?,?,?)',
                   (row['id'], row['symbol'], row['published_at'], encoded))

    def add_filings(self, rows, observed_at=None):
        observed_at = utc_iso(observed_at or now_iso())
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            for row in rows:
                self._filing(db, row, observed_at)

    def filings(self, symbol, since, until=None):
        since, until = utc_iso(since), utc_iso(until or now_iso())
        if since > until:
            raise ValueError('Start must be at or before end')
        with self.connect() as db:
            rows = db.execute('''SELECT v.payload,v.revision,v.observed_at,v.content_hash
                FROM filing_versions v WHERE v.symbol=? AND v.published_at>=? AND v.published_at<=?
                AND v.observed_at<=? AND v.revision=(SELECT max(w.revision) FROM filing_versions w
                  WHERE w.id=v.id AND w.observed_at<=?) ORDER BY v.published_at DESC,v.id''',
                (symbol, since, until, until, until)).fetchall()
        return [{**json.loads(r['payload']), 'revision': r['revision'], 'observed_at': r['observed_at'],
                 'content_hash': r['content_hash']} for r in rows]

    def run(self, payload):
        with self.connect() as db:
            db.execute('INSERT INTO runs(started_at,payload) VALUES(?,?)', (now_iso(), json.dumps(payload)))
