"""Copy Git-tracked FINN UI source into the Sites port, preserving unknown edits."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'hosting'
manifest=TARGET/'.openai/synced-files.json'
old=json.loads(manifest.read_text()) if manifest.exists() else {}
files=[p for p in subprocess.check_output(['git','-C',str(ROOT),'ls-files','-z','--','frontend/app','frontend/public']).decode().split('\0') if p]
mapping={p.removeprefix('frontend/'):ROOT/p for p in files}
mapping['backend/calendar.json']=ROOT/'backend/finn/nse_calendar_2026.json'
def source_bytes(p):
    data=p.read_bytes()
    return data.replace(b'\r\n',b'\n') if p.suffix.lower() in {'.ts','.tsx','.css','.js','.mjs','.json','.webmanifest','.svg','.html','.txt'} else data
def digest(p):return hashlib.sha256(source_bytes(p)).hexdigest()
def destination(name):
    raw=TARGET/name
    for part in (raw,*raw.parents):
        if part==TARGET.parent:break
        if part.is_symlink() or getattr(part,'is_junction',lambda:False)():raise SystemExit('Unsafe managed link')
    p=raw.resolve()
    if not p.is_relative_to(TARGET.resolve()):raise SystemExit('Unsafe managed path')
    return p
for name,source in mapping.items():
    destination(name)
    if source.is_symlink() or not source.resolve().is_relative_to(ROOT):raise SystemExit('Unsafe source link')
for name,previous in old.items():
    p=destination(name)
    if p.exists() and digest(p)!=previous and (name not in mapping or digest(p)!=digest(mapping[name])):
        raise SystemExit('Preserving an independent hosted edit: '+name)
new={}
for name,source in mapping.items():
    p=destination(name);p.parent.mkdir(parents=True,exist_ok=True)
    data=source_bytes(source);p.write_bytes(data);new[name]=hashlib.sha256(data).hexdigest()
for name in old.keys()-new.keys():
    p=destination(name)
    if p.exists():p.unlink()
manifest.write_text(json.dumps(new,sort_keys=True,indent=2)+'\n')
print(json.dumps({'synced_files':len(new),'source':'Git-tracked frontend source and retained calendar'}))
