import re
import importlib.util
import json
import subprocess
import sys
import hashlib
import io
import zipfile
from urllib.parse import parse_qs, urlparse

APPROVED_HOSTS = {"www.godeepak.com", "kalpataruprojects.com", "www.infosys.com", "www.hdfc.bank.in", "nsearchives.nseindia.com", "archives.nseindia.com", "www.bseindia.com",
                  "www.tcs.com", "www.hdfcbank.com", "www.lauruslabs.com", "www.astralpipes.com", "www.astralltd.com", "www.suzlon.com"}


def primary_page_image(document,page,store):
    with store.connect() as db:
        row=db.execute('SELECT body FROM raw_responses WHERE sha256=?',(document['sha256'],)).fetchone()
    if not row or hashlib.sha256(row['body']).hexdigest()!=document['sha256']:raise ValueError('Primary PDF bytes unavailable or corrupt')
    try:
        result=subprocess.run([sys.executable,'-m','finn.pdf_worker',document['url'],str(page),'image'],
                              input=row['body'],capture_output=True,timeout=30,check=False)
    except subprocess.TimeoutExpired as exc:raise ValueError('Primary page render exceeded its time limit') from exc
    if result.returncode:raise ValueError('Primary page image could not be rendered')
    return json.loads(result.stdout)


def document_url(url):
    p = urlparse(url)
    if p.scheme != "https" or p.hostname not in APPROVED_HOSTS or p.username or p.password or p.port not in {None, 443}:
        raise ValueError("Document host must be reviewed and approved")
    if p.hostname == "www.bseindia.com" and p.path.lower().endswith("annpdfopen.aspx"):
        filename = parse_qs(p.query).get("Pname", [None])[0]
        if not filename or "/" in filename or "\\" in filename or ".." in filename:
            raise ValueError("Invalid BSE document name")
        return "https://www.bseindia.com/xml-data/corpfiling/AttachLive/" + filename
    return url


def extract_document(body, url, max_pages=500, section_mode=False):
    # PyMuPDF cannot run safely on worker threads. A bounded child process owns
    # each document, also bounding damaged-PDF parsing time and crash propagation.
    if not body.startswith(b"%PDF"):
        raise ValueError("Source did not return a PDF")
    if len(body) > (80_000_000 if section_mode else 30_000_000):
        raise ValueError("PDF exceeds size limit")
    if importlib.util.find_spec('pymupdf') is None:
        raise ValueError('PDF runtime unavailable; install the project dependencies before source extraction')
    try:
        result = subprocess.run([sys.executable, '-m', 'finn.pdf_worker', url, str(max_pages), 'sections' if section_mode else 'full'],
                                input=body, capture_output=True, timeout=60, check=False)
    except subprocess.TimeoutExpired as exc:
        raise ValueError('PDF extraction time limit exceeded') from exc
    if result.returncode:
        raise ValueError('PDF extraction failed (encrypted, damaged, or page limit exceeded)')
    return json.loads(result.stdout)


def _extract_document_worker(body, url, max_pages=500, section_mode=False):
    from .pdf_runtime import pymupdf

    if not body.startswith(b"%PDF"):
        raise ValueError("Source did not return a PDF")
    with pymupdf.open(stream=body, filetype="pdf") as doc:
        if doc.is_encrypted:
            raise ValueError("Encrypted PDF")
        if not len(doc):
            raise ValueError("PDF contains no pages")
        if len(doc) > (1500 if section_mode else max_pages):
            raise ValueError("PDF page limit exceeded")
        pages = []
        text_size = 0
        selected=[]
        if section_mode:
            # Scan text under the same subprocess time limit, retaining original
            # page numbers. Selected sections never masquerade as the full AR.
            terms=re.compile(r'consolidated (?:statement|balance|cash)|statement of (?:profit|cash)|'
                             r'management discussion|directors.{0,8}report|independent auditor|'
                             r'contingent liabilit|related.party transaction|working capital|'
                             r'business overview|segment (?:information|report)',re.I)
            hits=[i for i,p in enumerate(doc) if terms.search(p.get_text())]
            covers=list(range(min(len(doc),max(1,min(8,max_pages//10)))))
            selected=list(dict.fromkeys(covers+hits))[:max_pages]
            selected=sorted(selected)
        else:selected=list(range(len(doc)))
        for i in selected:
            page=doc[i]
            # Large raster regions may carry material text that get_text() cannot see.
            # Such a document can be displayed, but cannot pass routine burial.
            area = page.rect.get_area()
            raster = any(pymupdf.Rect(info['bbox']).get_area() > area * .25 for info in page.get_image_info())
            text = page.get_text()
            text_size += len(text)
            if text_size > 2_000_000:
                raise ValueError('Extracted text limit exceeded')
            pages.append({"page": i+1, "text": text, "requires_visual_review": raster})
        links = list(dict.fromkeys(link['uri'] for i in selected for link in doc[i].get_links() if link.get('uri')))
        page_count=len(doc)
    has_text = any(len(p["text"].strip()) > 40 for p in pages)
    return {"url": url, "page_count": page_count, "pages": pages,
            "status": "text_extracted" if has_text else "ocr_required", "claims_verified": False,
            "links": links,'extraction_scope':'selected_primary_sections' if section_mode else 'full_document',
            'omitted_page_count':page_count-len(pages)}


def fetch_document(url, fetcher, section_mode=False):
    url = document_url(url)
    # Only fixed, reviewed public hosts are accepted; the transport rejects cross-host redirects.
    # DNS is resolved by the environment's HTTPS/SOCKS transport, not a second local resolver.
    response = fetcher.get(url, max_bytes=80_000_000 if section_mode else 30_000_000, ttl=86400)
    try:
        result = extract_document(response["body"], response["url"],section_mode=section_mode)
    except ValueError:
        fetcher.store.invalidate_http(url)
        raise
    result.update({k: response[k] for k in ["fetched_at", "sha256", "latency_ms"]})
    result['cache_hit'] = response.get('cache_hit', False)
    return result


def transcript_quality(doc):
    text = '\n'.join(p['text'] for p in doc['pages'])
    turns = re.findall(r'^\s*(?:Moderator|[A-Z][A-Za-z. -]{2,55}):\s*', text, re.MULTILINE)
    looks_like_call = bool(re.search(r'(earnings|conference|concall|results)\s*(conference\s*)?call|question.and.answer', text, re.I))
    passed = len(text.strip()) >= 3000 and len(turns) >= 5 and looks_like_call
    return {'status': 'transcript_candidate' if passed else 'not_full_transcript',
            'text_characters': len(text.strip()), 'speaker_turns': len(turns),
            'method': 'conservative_content_heuristic_v1', 'claims_verified': False}


def archive_pdf(body):
    """Read one bounded primary PDF in memory; never extract paths to disk."""
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        entries=[e for e in archive.infolist() if not e.is_dir()]
        if not entries or len(entries)>10 or sum(e.file_size for e in entries)>30_000_000:raise ValueError('Archive exceeds entry or expanded-size limit')
        if any(e.flag_bits & 1 or e.file_size>max(1,e.compress_size)*200 for e in entries):raise ValueError('Encrypted or excessive-ratio archive')
        pdfs=[e for e in entries if e.filename.lower().endswith('.pdf')]
        if len(pdfs)!=1:raise ValueError('Archive must contain exactly one primary PDF')
        entry=pdfs[0]
        if '\\' in entry.filename or entry.filename.startswith('/') or '..' in entry.filename.split('/') or ':' in entry.filename:raise ValueError('Invalid archive entry name')
        with archive.open(entry) as stream:pdf=stream.read(30_000_001)
        if len(pdf)>30_000_000 or not pdf.startswith(b'%PDF'):raise ValueError('Archive PDF is invalid or too large')
        return entry.filename,pdf


def fetch_filing_document(url,fetcher):
    if not urlparse(url).path.lower().endswith('.zip'):return fetch_document(url,fetcher)
    url=document_url(url)
    if urlparse(url).hostname not in {'nsearchives.nseindia.com','archives.nseindia.com'}:raise ValueError('Only official NSE filing archives are supported')
    response=fetcher.get(url,max_bytes=20_000_000,ttl=86400)
    try:
        entry,pdf=archive_pdf(response['body']);result=extract_document(pdf,response['url'])
    except (ValueError,zipfile.BadZipFile,RuntimeError) as exc:
        fetcher.store.invalidate_http(url);raise ValueError('Primary archive rejected: '+str(exc)) from exc
    digest=fetcher.store.raw(response['url'],pdf)
    result.update(fetched_at=response['fetched_at'],sha256=digest,latency_ms=response['latency_ms'],cache_hit=response.get('cache_hit',False),
                  source_container={'type':'zip','url':response['url'],'sha256':response['sha256'],'entry':entry})
    return result


def container_matches(document,body):
    try:
        c=document['source_container']
        if hashlib.sha256(body).hexdigest()!=c['sha256'] or c['url']!=document['url']:return False
        entry,pdf=archive_pdf(body)
        return entry==c['entry'] and hashlib.sha256(pdf).hexdigest()==document['sha256']
    except (KeyError,ValueError,zipfile.BadZipFile,RuntimeError):return False


def resolve_transcript(url, fetcher, max_documents=4):
    pending, visited, chain, failures = [url], set(), [], []
    while pending and len(visited) < max_documents:
        candidate = pending.pop(0)
        if candidate in visited:
            continue
        visited.add(candidate)
        try:
            candidate = document_url(candidate)
            doc = fetch_document(candidate, fetcher)
            quality = transcript_quality(doc)
            chain.append({'url': doc['url'], 'sha256': doc['sha256'], 'page_count': doc['page_count'],
                          'quality': quality, 'fetched_at': doc['fetched_at']})
            if quality['status'] == 'transcript_candidate':
                return {**doc, 'quality': quality, 'discovery_chain': chain}
            for link in doc.get('links', []):
                try:
                    safe = document_url(link)
                    if urlparse(safe).path.lower().endswith('.pdf') and safe not in visited:
                        pending.append(safe)
                except ValueError:
                    continue
        except Exception as exc:
            failures.append(f'{candidate}: {exc}')
    raise ValueError('No suitable full transcript within bounded approved links: ' + str({'checked': chain, 'errors': failures}))
