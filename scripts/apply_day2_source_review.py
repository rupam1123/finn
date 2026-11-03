"""Apply the recorded primary-event review to the frozen Windows-backup cohort.

These are assistant source-review decisions, not an independent benchmark.
Full-document materiality/financial-table review is intentionally not cleared.
The ledger records exact revision, source hash, page and supporting cover text.
"""
import hashlib
import argparse
import json
from pathlib import Path

from finn.classifier import classify
from finn.evidence import citation, compact
from finn.storage import Store, now_iso


GROUPS = {
    'fund_raise': [0,1,4,5,7,8,10,73,81,103,114,117,118,119,128,135,136,137,141,142,143,145,146],
    'M&A': [14,29,30,99,120,129,157,158,175,207,210],
    'credit_rating': [3,78,139,140,154],
    'litigation': [9,182,188,194,195,197,198,199,200],
    'results': [19,24,26,39,40,54,55,57,88,89,107,108,131,144,148,149,150,151,190,191,192,193],
    'management_change': [31,38,46,47,48,80,96,105,124,156,178],
    'dividend': [20,23,25,56],
    'earnings_call': [16,22,33,37,42,50,76,94,102,104,111,127,132,138,147,160,170,186,189,196,202,208,211,215,220],
    'investor_meetings': [13,28,52,101,109,110,159,167,168,169,173,176,181,183,185,187],
    'postal_ballot': [35,36,43,44,83,84],
    'agm_egm': [112,113,162,163,164,180],
    'capex': [204],
    'unclassified': [6,11,18,32,34,41,49,62,63,68,72,77,79,86,87,90,95,106,115,121,122,123,126,130,133,134,152,155,161,165,166,171,172,174,179,184,201,203,205,206,209,212,213,214,216,218,221,222,223],
}
FOLLOWUP = {
    58: 'Results-release announcement also schedules a conference call; multiple event types need adjudication.',
    130: 'Visual review of PDF page 2 identifies Shareholders Letter and Results, Q2FY27. The extracted text is only 0; validated OCR and financial-table review remain open.',
    205: 'Visual review confirms intra-group preference-share funding. OCR misreads numeric text; taxonomy and validated extraction remain open. Do not present it as external funding.',
}
NOTES = {
    24: 'Recovered readable primary PDF: financial-results press release. Ind AS/IFRS measures must not be mixed; acquisition and dividend events also appear.',
    40: 'Recovered readable primary PDF: bank financial results. Image-heavy tables remain unverified for numeric extraction.',
    19: 'Results publication advertisement, not a management change.',
    20: 'Dividend publication advertisement.',
    30: 'Investment committee approved the BBY Services India acquisition; completion is conditional.',
    45: 'Provisional advances/deposits operating update; statutory insider-trading reference is not an insider trade.',
    67: 'Production/sales operating report; figures are explicitly unaudited.',
    81: 'Board approved NCD issuance and also reports an independent-director resignation; preserve both in source review.',
    94: 'Meeting table explicitly schedules the Q2/H1 earnings conference call.',
    106: 'Employee stock option issuance; no external capital raise inferred.',
    111: 'Second cover subject explicitly describes the earnings conference call.',
    116: 'Provisional customer/loan/AUM update; statutory PIT reference does not imply an insider transaction.',
    120: 'Binding term sheet for conditional divestment of a subsidiary; do not imply completed sale.',
    129: 'Internal business transfer and other transactions share a document with financial results.',
    131: 'Board approved financial results and multiple business transactions; other events remain reviewable.',
    157: 'Nagarro takeover announcement; offer conditions and closing still matter.',
    171: 'Subsidiary guarantee is important despite no dedicated category. Keep visible.',
    172: 'ESG rating is not an investor meeting or a debt credit rating.',
    177: 'License agreement by an existing joint venture; no new acquisition inferred.',
    184: 'Share-capital audit, not a management-change event.',
    204: 'Commissioning of a chemical plant; do not infer additional financial metrics.',
    223: 'Fire-related insurance settlement remains visible; unclassified does not mean immaterial.',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default='data/finn.sqlite3')
    args = parser.parse_args()
    root = Path('verification/day2-backup-review')
    baseline = json.loads((root/'baseline.json').read_text(encoding='utf-8'))
    rows = baseline['filings']
    assert baseline['as_of'] == '2026-10-29T04:51:36.974427+00:00' and len(rows) == 224
    # Index labels belong only to this immutable cohort; exported records use IDs.
    assert rows[0]['id'] == '8ecb2b2713558297684c7499b3c7813d61965b7897b588b848b48caafcdcebef'
    assert rows[26]['id'] == 'd275e4e159ab8f779bdebdad9feca75940acd80e3e7cb867fe1878fc327273ff'
    labels = {i: category for category, indices in GROUPS.items() for i in indices}
    assert len(labels) == sum(map(len, GROUPS.values()))
    store = Store(args.db)
    ledger = []
    for i, f in enumerate(rows):
        entry = {'index': i, 'filing_id': f['id'], 'symbol': f['symbol'],
                 'filing_content_hash': f['content_hash'], 'originally_pending': f['id'] in baseline['pending_ids'],
                 'originally_uncertain': f['id'] in baseline['uncertain_ids']}
        saved = store.get('filing_document', f['id'])
        d = saved['data'] if saved else None
        if not d or not d.get('pages') or d.get('status') != 'text_extracted':
            entry.update(status='source_unavailable_or_unreadable', reason='No readable verified PDF; metadata-only candidate remains visible.')
        else:
            with store.connect() as db:
                raw = db.execute('SELECT body FROM raw_responses WHERE sha256=?', (d['sha256'],)).fetchone()
            assert raw and hashlib.sha256(raw[0]).hexdigest() == d['sha256']
            page = d['pages'][1] if i in {24,157} and len(d['pages']) > 1 else d['pages'][0]
            quote = compact(page['text'])
            entry.update(document_sha256=d['sha256'], source_url=d['url'], page=page['page'],
                         quote=quote, page_requires_visual_review=page.get('requires_visual_review'))
            if i in FOLLOWUP or len(quote) < 80:
                entry.update(status='needs_further_review', reason=FOLLOWUP.get(i, 'Insufficient primary-page text'))
            else:
                category = labels.get(i, 'press_release')
                reason = NOTES.get(i, 'Primary event category reviewed against the issuer disclosure; full-document materiality and extraction are not certified.')
                review = {**entry, 'category': category, 'scope': 'primary_event_category',
                          'reason': reason, 'reviewed_at': now_iso()}
                citation(d, review['page'], quote)
                store.put('source_review', f['id'], review)
                entry.update(status='category_reviewed' if category != 'unclassified' else 'unclassified_retained',
                             category=category, rule_category=classify(f,d)['category'], reason=reason)
        ledger.append(entry)
    (root/'source-review-ledger.json').write_text(json.dumps({'scope': 'Assistant primary-event category review; not independent accuracy or full-document certification',
        'cohort_as_of': baseline['as_of'], 'entries': ledger}, indent=2, ensure_ascii=False), encoding='utf-8')
    from collections import Counter
    print(json.dumps(dict(Counter(e['status'] for e in ledger))))


if __name__ == '__main__':
    main()
