"""Read-only comparison of the immutable Windows backup and updated database."""
import argparse
import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--backup', required=True)
    p.add_argument('--db', default='data/finn.sqlite3')
    p.add_argument('--out', default='verification/day2-backup-review/preservation.json')
    args = p.parse_args()
    checks = []
    def check(name, passed): checks.append({'name': name, 'passed': bool(passed)})
    backup = Path(args.backup).resolve(strict=True)
    current = Path(args.db).resolve(strict=True)
    with closing(sqlite3.connect(backup.as_uri()+'?mode=ro', uri=True)) as old, closing(sqlite3.connect(current.as_uri()+'?mode=ro', uri=True)) as new:
        for name, db in [('backup', old), ('updated', new)]:
            check(name+' SQLite integrity', db.execute('PRAGMA integrity_check').fetchall() == [('ok',)])
            check(name+' foreign keys', not db.execute('PRAGMA foreign_key_check').fetchall())
            valid = all(hashlib.sha256(body).hexdigest() == sha for sha,body in db.execute('SELECT sha256,body FROM raw_responses'))
            check(name+' all raw hashes', valid)
        for table, key in [('filings','id'), ('filing_versions','id,revision'), ('raw_responses','sha256'), ('attempts','id'), ('runs','id')]:
            columns = [r[1] for r in old.execute(f'PRAGMA table_info({table})')]
            positions = [columns.index(k) for k in key.split(',')]
            where = ' AND '.join(k+'=?' for k in key.split(','))
            count = 0
            for row in old.execute(f'SELECT * FROM {table}'):
                saved = new.execute(f'SELECT * FROM {table} WHERE {where}', tuple(row[i] for i in positions)).fetchone()
                if saved != row:
                    raise AssertionError(f'Existing {table} row changed')
                count += 1
            check(f'All {count} original {table} rows preserved exactly', True)
        for kind in ['push_analysis','market','fundamentals','filings_coverage','primary_sample','universe']:
            rows = old.execute('SELECT * FROM snapshots WHERE kind=?', (kind,)).fetchall()
            check(f'Original {kind} snapshots preserved', all(
                new.execute('SELECT * FROM snapshots WHERE kind=? AND symbol=?', (r[0],r[1])).fetchone() == r for r in rows))
        counts = {t:new.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in ['filings','filing_versions','snapshots','raw_responses','attempts','runs']}
    sha = hashlib.file_digest(backup.open('rb'), 'sha256').hexdigest()
    check('Original upload SHA-256 unchanged', sha == 'eb7f829c35a90c6a93dcc822e206ba55f16d8361226d8e650a299fa7b99ca63c')
    report = {'passed': all(c['passed'] for c in checks), 'backup_sha256': sha, 'updated_counts':counts, 'checks': checks}
    Path(args.out).write_text(json.dumps(report,indent=2), encoding='utf-8')
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
