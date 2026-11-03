"""Extract explicitly linked management changes and statutory profiles only."""
import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .evidence import citation, compact, model_pages
from .model import ModelUnavailable

VERSION = 'management-v4'
# The event sentence must bind action, name, role and effective date. Table boilerplate
# lists of appointment/resignation/removal are not evidence of an actual resignation.
EVENT = re.compile(r'(?P<action>re-\s*appointment|appointment) of (?P<name>[A-Z][A-Za-z. ]{2,70}?)\s*,?\s+as '
                   r'(?P<role>.{4,140}?)\s+(?:as per .{1,70}?,\s*)?effective\s+(?P<date>\d{1,2} [A-Za-z]+ 20\d{2})', re.I)
RESIGNATION = re.compile(r'(?:Mr\.|Ms\.|Mrs\.|Dr\.)\s+(?P<name>[A-Z][A-Za-z. ]{2,70}?)\s*'
    r'(?:\(DIN:\s*\d+\))?,\s*(?P<role>.{4,140}?)\s+(?:of the Company\s+)?has tendered '
    r'(?:his|her|their) resignation\s+(?:with effect from|effective)\s+'
    r'(?P<date>\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+20\d{2})', re.I)
POSITION_RESIGNATION = re.compile(
    r'(?:Mr\.|Ms\.|Mrs\.|Dr\.)\s+(?P<name>[A-Z][A-Za-z. ]{2,70}?),\s*'
    r'SMP of the Company has tendered (?:his|her|their) resignation from the position of '
    r'(?P<role>[^,.;]{4,100}),\s*(?:due to [^.;]{1,100}?\s+)?'
    r'with effect from (?:the closure of business hours on )?'
    r'(?P<date>[A-Za-z]+\s+\d{1,2},\s+20\d{2})', re.I)


class LocatedEvents(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    pages: list[int] = Field(min_length=1, max_length=10)


class EventCandidate(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    name:str=Field(min_length=3,max_length=100)
    role:str=Field(min_length=3,max_length=150)
    action:Literal['appointment','reappointment','resignation','retirement']
    effective_date:str
    date_text:str=Field(min_length=6,max_length=60)
    page:int=Field(ge=1)
    quote:str=Field(min_length=20,max_length=1500)
    profile_page:int|None=None
    profile_quote:str|None=None


class EventCandidates(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    events:list[EventCandidate]=Field(max_length=8)


def validate_event(document,candidate):
    evidence=citation(document,candidate.page,candidate.quote)
    quote=compact(candidate.quote)
    if any(compact(x).lower() not in quote.lower() for x in (candidate.name,candidate.role,candidate.date_text)):
        raise ValueError('Event fields are not linked by the quoted primary sentence')
    patterns={'appointment':r'appoint','reappointment':r're.?appoint','resignation':r'resign','retirement':r'retir'}
    if not re.search(patterns[candidate.action],quote,re.I):raise ValueError('Event action is unsupported')
    clean=re.sub(r'(?<=\d)(st|nd|rd|th)\b','',candidate.date_text,flags=re.I).strip()
    parsed=None
    for fmt in ('%d %B %Y','%B %d, %Y','%d %b %Y','%d-%m-%Y','%d.%m.%Y','%Y-%m-%d'):
        try:parsed=datetime.strptime(clean,fmt).date().isoformat();break
        except ValueError:continue
    if parsed!=candidate.effective_date:raise ValueError('Effective date is not supported')
    profile=None
    if candidate.profile_quote:
        if not candidate.profile_page or candidate.name.lower() not in compact(candidate.profile_quote).lower():raise ValueError('Profile is not tied to the named person')
        profile={'text':candidate.profile_quote,'source_type':'issuer_statutory_brief_profile','independently_verified':False,
                 'evidence':citation(document,candidate.profile_page,candidate.profile_quote)}
    return {'name':candidate.name,'role':candidate.role,'action':candidate.action,'effective_date':parsed,
            'evidence':evidence,'profile':profile,'conditions':quote if re.search(r'subject to|proposed|approval',quote,re.I) else 'Issuer-reported event; see the primary filing.'}


def enrich_management(document, model=None):
    base = {'version': VERSION, 'status': 'review_required', 'events': [],
            'external_bio_status': 'not_requested_no_verified_external_source',
            'model_status': 'not_configured' if model is None or not model.configured else 'not_needed',
            'warnings': []}
    if not document or document.get('status') != 'text_extracted':
        return {**base, 'warnings': ['Primary text unavailable; event and bio not inferred.']}
    pages = document['pages']
    events = []
    for page in pages:
        text = compact(page['text']).replace('re- appointment', 're-appointment')
        for match in EVENT.finditer(text):
            try:
                effective = datetime.strptime(match['date'], '%d %B %Y').date().isoformat()
            except ValueError:
                continue
            name, role = match['name'].strip(), match['role'].strip()
            # Preserve original spacing for source verification, including PDF line-wrap hyphenation.
            source_text = compact(page['text'])
            start = source_text.lower().find(match.group(0).lower())
            if start >= 0:
                evidence_quote = source_text[start:start+len(match.group(0))]
            else:
                # Only normalized re- line break may differ, not content.
                pattern = re.escape(match.group(0)).replace(r're\-appointment', r're-\s*appointment')
                source_match = re.search(pattern, source_text, re.I)
                if not source_match:
                    continue
                evidence_quote = source_match[0]
            event = {'name': name, 'role': role, 'action': 'reappointment' if match['action'].lower().startswith('re-') else 'appointment',
                     'effective_date': effective, 'evidence': citation(document, page['page'], evidence_quote),
                     'profile': None, 'conditions': 'Read the cited filing for terms and regulatory approvals.'}
            for profile_page in pages:
                ptext = compact(profile_page['text'])
                marker = re.search(r'Brief Profile\s*(?:\(in case of appointment\))?\s*', ptext, re.I)
                if marker:
                    profile = ptext[marker.end():]
                    profile = re.split(r'\b(?:\d[.]?\s+)?Disclosure of relationships', profile, maxsplit=1, flags=re.I)[0].strip()
                    if name.lower() in profile.lower() and len(profile) <= 2500:
                        event['profile'] = {'text': profile, 'source_type': 'issuer_statutory_brief_profile',
                                            'independently_verified': False,
                                            'evidence': citation(document, profile_page['page'], profile)}
                        break
            if not any(e['name'] == name and e['action'] == event['action'] for e in events):
                events.append(event)
        matches = [*RESIGNATION.finditer(compact(page['text'])),
                   *POSITION_RESIGNATION.finditer(compact(page['text']))]
        for match in matches:
            try:
                date_text = re.sub(r'(?<=\d)(st|nd|rd|th)\b', '', match['date'])
                date_format = '%B %d, %Y' if ',' in date_text else '%d %B %Y'
                effective = datetime.strptime(date_text, date_format).date().isoformat()
            except ValueError:
                continue
            name = match['name'].strip()
            role = re.sub(r'\s+of the Company$', '', match['role'], flags=re.I).strip()
            if not any(e['name'] == name and e['action'] == 'resignation' for e in events):
                events.append({'name': name, 'role': role, 'action': 'resignation', 'effective_date': effective,
                               'evidence': citation(document, page['page'], match[0]), 'profile': None,
                               'conditions': 'Reason and terms are issuer-reported; see the original filing.'})
    if not events and model and model.configured:
        try:
            located, usage = model.generate('Identify pages containing explicit actual management-change events, '
                'excluding boilerplate lists. Return their page numbers. Do not invent dates, careers, names or roles.',
                {'pages': model_pages(document)}, LocatedEvents.model_json_schema())
            located = LocatedEvents.model_validate(located)
            available = {p['page'] for p in pages}
            if not set(located.pages) <= available:
                raise ValueError('Unknown page')
            base.update(model_status='review_pages_located', usage=usage,
                        review_evidence=[citation(document, p['page'], p['text']) for p in pages if p['page'] in located.pages])
        except (ModelUnavailable, ValueError, TypeError, KeyError):
            base['model_status'] = 'unavailable_or_invalid'
        try:
            output,usage=model.generate('Extract explicitly disclosed management changes and issuer-provided career profiles. '
                'Every event quote must link the person, role, action and exact effective date. Preserve approval/proposed conditions. '
                'Never infer a resignation from a boilerplate list of event types. Profile quote must include the named person. '
                'No invented careers, outside knowledge or inferred dates; omit unsupported events.',
                {'pages':model_pages(document)},EventCandidates.model_json_schema())
            candidates=EventCandidates.model_validate(output)
            events=[validate_event(document,event) for event in candidates.events]
            base.update(model_status='event_fields_source_validated',usage=usage)
        except (ModelUnavailable,ValueError,TypeError,KeyError):
            base['model_status']='unavailable_or_invalid'
    return {**base, 'events': events, 'status': 'source_extracted' if events else 'review_required',
            'warnings': ['Only explicit, single-event sentences are automated. Other changes need review.',
                         'Profiles are issuer statements; no external employment history was invented.']}
