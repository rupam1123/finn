"""Own the review database for the whole run; publish only an integrity-checked checkpoint.

The temporary database avoids concurrent workspace synchronization during writes.
The immutable uploaded backup is opened read-only. Existing workspace bytes are
retained for diagnosis, never treated as a valid recovery source.
"""
import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup', required=True)
    parser.add_argument('--resume', action='store_true', help='Use the healthy current checkpoint and retry only unavailable PDFs')
    args = parser.parse_args()
    backup = Path(args.backup).resolve(strict=True)
    expected = 'eb7f829c35a90c6a93dcc822e206ba55f16d8361226d8e650a299fa7b99ca63c'
    with backup.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == expected
    out = Path('verification/day2-backup-review').resolve()
    phases = []
    def run(name, command, allowed=(0,)):
        count = 0
        with (out/(name+'.txt')).open('w',encoding='utf-8') as log:
            process = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
            for line in process.stdout:
                log.write(line); log.flush()
                count += 1
                if count % 25 == 0:
                    print(json.dumps({'phase':name,'output_lines':count}),flush=True)
            code = process.wait()
        phases.append({'name':name,'exit_code':code})
        print(json.dumps(phases[-1]),flush=True)
        if code not in allowed:
            raise RuntimeError(name+' failed; see saved log; working database was not published')
    with tempfile.TemporaryDirectory(prefix='finn-review-') as temp:
        db = Path(temp)/'finn.sqlite3'
        source = Path('data/finn.sqlite3').resolve(strict=True) if args.resume else backup
        with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as src, closing(sqlite3.connect(db)) as dst:
            assert src.execute('PRAGMA integrity_check').fetchall() == [('ok',)]
            src.backup(dst)
        py = sys.executable
        if args.resume:
            from finn.storage import Store
            from finn.push import analysis_key
            from finn.push_ingest import process_filing
            store = Store(db)
            rows = json.loads((out/'baseline.json').read_text(encoding='utf-8'))['filings']
            retried = []
            for filing in rows:
                old = store.get('push_analysis', analysis_key(filing))
                if old and old['data']['status'] != 'processed' and (filing.get('document_url') or '').lower().endswith('.pdf'):
                    retried.append(process_filing(store, filing, force=True))
            (out/'source-retries.json').write_text(json.dumps(retried,indent=2),encoding='utf-8')
            print(json.dumps({'retried':retried}),flush=True)
        else:
            run('source-processing',[py,'scripts/review_day2_batch.py','--db',str(db),'--prefer-saved'],(0,1))
            shutil.copyfile(out/'processing-summary.json',out/'source-processing-summary.json')
            shutil.copyfile(out/'processing.jsonl',out/'source-processing.jsonl')
        run('category-review',[py,'scripts/apply_day2_source_review.py','--db',str(db)])
        run('reviewed-processing',[py,'scripts/review_day2_batch.py','--db',str(db),'--saved-documents'],(0,1))
        run('preservation',[py,'scripts/audit_backup_preservation.py','--backup',str(backup),'--db',str(db)])
        run('saved-source-audit',[py,'scripts/verify_day2.py','--db',str(db),'--out',str(out/'saved-source-audit.json')])
        # Integration failures are reported explicitly and do not discard a healthy
        # source checkpoint. They still block the Day 3 acceptance gate.
        run('integration',[py,'scripts/run_integration.py','--db',str(db),'--out',str(out/'integration')],(0,1))
        ready = Path('data/finn.ready.sqlite3')
        with closing(sqlite3.connect(db)) as src, closing(sqlite3.connect(ready)) as dst:
            src.backup(dst)
        with closing(sqlite3.connect(ready.resolve().as_uri()+'?mode=ro',uri=True)) as check:
            assert check.execute('PRAGMA integrity_check').fetchall() == [('ok',)]
        target = Path('data/finn.sqlite3')
        if target.exists() and not args.resume:
            baseline = Path('data/baselines/finn_interrupted_20261030.sqlite3')
            baseline.parent.mkdir(exist_ok=True)
            if baseline.exists():
                raise FileExistsError('Preserve the existing diagnostic baseline before publishing another checkpoint')
            os.replace(target,baseline)
        os.replace(ready,target)
    (out/'workflow.json').write_text(json.dumps({'database_published':True,'phases':phases},indent=2),encoding='utf-8')
    print(json.dumps({'database_published':True,'phases':phases}),flush=True)


if __name__ == '__main__':
    main()
