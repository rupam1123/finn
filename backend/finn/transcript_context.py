"""Primary-document speaker turns and explicitly stated accounting context."""
import re
from .evidence import citation, compact

NAME = r'[A-Z][A-Za-z.\'-]*(?:[ \t]+[A-Z][A-Za-z.\'-]*){1,4}'
TURN = re.compile(r'(?m)^[ \t]*('+NAME+r')[ \t]*:[ \t]*')
PLAIN = re.compile(r'(?m)^[ \t]*('+NAME+r')[ \t]*$')
UNVERIFIED_TURN = re.compile(r'(?mi)^[ \t]*(?:Moderator|Operator|Analyst|Participant|Audience|'
                            r'Unidentified(?:\s+(?:Speaker|Analyst|Participant))?|Unknown(?:\s+Speaker)?|Q|A)[ \t]*(?::|$)')
ROLE = re.compile(r'chief (?:executive|financial|operating)|\bCEO\b|\bCFO\b|'
                  r'(?:deputy )?managing director|executive director|director.{0,20}finance|'
                  r'president|head.{0,20}investor relations',re.I)
NON_NAME = re.compile(r'document|conference|earnings|financial results|page|limited|'
                      r'forward looking|thank you|good evening|good afternoon|chief|officer|director|president',re.I)


def normalized_name(name):
    return re.sub(r'[^a-z]','',re.sub(r'^(Mr|Ms|Mrs|Dr)\.?\s+','',name,flags=re.I).lower())


def management_roster(document):
    """A person's role must occur next to their name in this same document."""
    pages=document.get('pages',[])
    names={m[1].strip() for p in pages for regex in (TURN,PLAIN) for m in regex.finditer(p['text'])
           if not NON_NAME.search(m[1])}
    roster={}
    for name in names:
        # Do not bridge multiple paragraphs, another speaker, or an analyst list.
        pattern=re.compile(r'\s+'.join(re.escape(word) for word in name.split())+
                           r'\s*(?:[,–—-]\s*|\n[ \t]*)'+
                           r'([^\n]{3,150}(?:\n[^\n]{3,70})?)',re.I)
        for page in pages[:4]:
            for match in pattern.finditer(page['text']):
                role=re.split(r'\b(?:MR|MS|MRS|DR)\.\s+|\bMODERATOR\b|\bANALYSTS?\b',compact(match[1]),maxsplit=1,flags=re.I)[0].strip()
                if ROLE.search(role) and not re.search(r'analyst|moderator|capital advisors',role,re.I):
                    roster[normalized_name(name)]={'name':name,'role':role,
                        'citation':citation(document,page['page'],match[0]),
                        'requires_visual_review':page.get('requires_visual_review',False)}
                    break
            if normalized_name(name) in roster:break
    return roster


def turns(document):
    roster=management_roster(document)
    active=None
    output=[]
    for page in document.get('pages',[]):
        text=page['text']
        matches={m.start():m for regex in (TURN,PLAIN) for m in regex.finditer(text)
                 if not NON_NAME.search(m[1])}
        unverified={m.start() for m in UNVERIFIED_TURN.finditer(text)}
        bounds=sorted(set([0,len(text),*matches,*unverified]))
        for left,right in zip(bounds,bounds[1:]):
            match=matches.get(left)
            if left in unverified:active=None
            elif match:active=match[1].strip()
            quote=text[left:right].strip()
            if not quote:continue
            role=roster.get(normalized_name(active or ''))
            output.append({'page':page['page'],'text':quote,'speaker':active,
                'speaker_verified':bool(role and not role['requires_visual_review']),
                'speaker_evidence':role['citation'] if role else None,
                'requires_visual_review':page.get('requires_visual_review',False)})
    return output


def accounting_basis(document, text):
    text=re.sub(r'\bconsol\b','consolidated',text,flags=re.I)
    text=re.sub(r'stand[ -]+alone','standalone',text,flags=re.I)
    local={x.lower() for x in re.findall(r'\b(consolidated|standalone)\b',text,re.I)}
    if len(local)==1:return next(iter(local)),[]
    if len(local)>1:return 'not_explicit',[]
    defaults=[]
    for page in document.get('pages',[]):
        for match in re.finditer(r'(?:all (?:financial )?(?:figures|numbers|results)|'
                r'figures (?:are|have been) reported)\b[^.!?]{0,120}\b(consolidated|standalone)\b[^.!?]{0,100}',
                compact(page['text']),re.I):
            if re.search(r'\bstandalone\b',match[0],re.I) and re.search(r'\bconsolidated\b',match[0],re.I):continue
            if page.get('requires_visual_review'):continue
            defaults.append((match[1].lower(),citation(document,page['page'],match[0])))
    if len({basis for basis,_ in defaults})==1:
        return defaults[0][0],[c for _,c in defaults]
    return 'not_explicit',[]
