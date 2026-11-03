"""Load only FINN's server settings from a local .env; never execute its contents."""
import os
from pathlib import Path

ALLOWED={'GEMINI_API_KEY','FINN_FLASH_MODEL','FINN_REASONING_MODEL','FINN_DB','FINN_ALLOWED_ORIGINS','FINN_MODEL_RPM','FINN_PUBLIC_REVIEW'}

def load_local_settings(path='.env'):
    p=Path(path)
    if not p.is_file():return
    for line in p.read_text(encoding='utf-8-sig').splitlines():
        line=line.strip()
        if not line or line.startswith('#') or '=' not in line:continue
        key,value=line.split('=',1);key=key.strip();value=value.strip()
        if key not in ALLOWED:continue
        if len(value)>=2 and value[0]==value[-1] and value[0] in {'"',"'"}:value=value[1:-1]
        if value and key not in os.environ:os.environ[key]=value
