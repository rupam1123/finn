"""Common primary-document evidence checks. Text is data, never instructions."""
import hashlib
import json
import re


def compact(text):
    return re.sub(r'\s+', ' ', text).strip()


def citation(document, page, quote):
    source = next((p['text'] for p in document.get('pages', []) if p['page'] == page), None)
    if not source or not quote or compact(quote) not in compact(source):
        raise ValueError('Quote is not present on the cited primary page')
    result={'url': document['url'], 'sha256': document['sha256'], 'page': page,
            'quote': quote, 'observed_at': document['fetched_at']}
    if document.get('source_container'):result['source_container']=document['source_container']
    return result


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def model_pages(document, limit=100_000):
    """Reject oversized inputs rather than silently omitting material content."""
    pages = [{'page': p['page'], 'text': p['text']} for p in document.get('pages', [])]
    if sum(len(p['text']) for p in pages) > limit:
        raise ValueError('Document exceeds model input budget; review required')
    return pages
