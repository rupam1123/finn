"""Model-assisted observation extraction; values, context and roles are independently bound."""
import re
from decimal import Decimal, InvalidOperation
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,ValidationError
from .evidence import compact
from .transcript_context import accounting_basis

class Fact(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    kind:Literal['guidance','actual']
    metric:Literal['revenue_growth','operating_margin','ebitda_margin','pbt_margin','pat_margin','net_interest_margin']
    target_period:str=Field(pattern=r'^(?:Q[1-4] )?FY20\d{2}$')
    operator:Literal['band','at_least','actual']
    lower:str|None=None
    upper:str|None=None
    value:str|None=None
    basis:Literal['consolidated','standalone','unknown']
    source_index:int=Field(ge=0)
    quote:str=Field(min_length=15,max_length=1800)
    context_index:int=Field(ge=0)
    context_quote:str=Field(min_length=10,max_length=1800)

class Facts(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    facts:list[Fact]=Field(max_length=32)


class FactCandidates(BaseModel):
    """Validate the collection first, then reject malformed proposals individually."""
    model_config=ConfigDict(extra='forbid',strict=True)
    facts:list[object]=Field(max_length=32)


def extract(documents,model):
    from .transcript_rag import chunks,retrieve,reported_quarter
    from .say_do import PERIOD,period,GUIDANCE_WORDS
    sources=[];docs={};seen=set()
    for doc in documents:
        if doc.get('kind')!='transcript' or not reported_quarter(doc):continue
        docs[doc['sha256']]=doc
        index=chunks(doc)
        for query in ('guidance target outlook expect','revenue growth operating margin','full year consolidated standalone'):
            for item in retrieve(index,query,3):
                c=item['citation'];key=(c['sha256'],c['page'],c['quote'])
                if key not in seen:
                    sources.append(item);seen.add(key)
    sources=sources[:40]
    if not sources:return [],None
    payload=[{'index':i,'text':x['citation']['quote'],'reported_period':reported_quarter(docs[x['citation']['sha256']])['label'],
              'speaker':x.get('speaker'),'management_verified':x.get('speaker_verified',False)} for i,x in enumerate(sources)]
    output,usage=model.generate('Extract explicit percentage management guidance and reported actuals only. '
        'Capture annual versus quarterly horizons, minimum targets and revised ranges. '
        'Do not mistake analyst questions, sector forecasts, segment metrics, adjusted margins or prior guidance recalled retrospectively for new promises. '
        'Return exact source quotes for each number and a context quote proving basis and target period from the SAME document. '
        'The quote must be a complete verbatim source sentence or clause containing the metric name and number, '
        'at least 15 characters; never return only a number or percentage range. '
        'The context quote must also be a complete verbatim source clause, at least 10 characters. '
        'Use canonical target periods Q1 FY2026 or FY2026. Unknown context is unknown, never guessed. Annual targets never become quarter targets. '
        'For kind=actual, set operator=actual and value to the printed percentage; lower and upper are null. '
        'For kind=guidance, use a band with lower and upper, or at_least with lower; value is null. '
        'Return at most 16 source-supported observations, using the exact schema field names and full four-digit fiscal years. '
        'Omit unsupported metrics. No verdicts or arithmetic.',
        {'sources':payload},Facts.model_json_schema())
    parsed=FactCandidates.model_validate(output);facts=[];rejections=[];schema_rejections=[]
    for proposal in parsed.facts:
        try:
            item=Fact.model_validate(proposal)
            if item.source_index>=len(sources) or item.context_index>=len(sources):raise ValueError('Unknown source')
            src=sources[item.source_index];ctx=sources[item.context_index]
            if src['citation']['sha256']!=ctx['citation']['sha256']:raise ValueError('Context from different document')
            if compact(item.quote) not in compact(src['citation']['quote']) or compact(item.context_quote) not in compact(ctx['citation']['quote']):raise ValueError('Quote absent')
            doc=docs[src['citation']['sha256']];reported=reported_quarter(doc)['label']
            metric_text=item.metric.replace('_',' ')
            if item.metric=='revenue_growth':supported=bool(re.search(r'revenue.{0,30}(?:growth|grew)|growth.{0,20}revenue',item.quote,re.I))
            else:supported=metric_text in compact(item.quote).lower()
            if not supported:raise ValueError('Metric is not supported by quotation')
            if item.kind=='guidance' and (not GUIDANCE_WORDS.search(item.quote) or re.search(r'earlier guidance|previous guidance|had guided|had given',item.quote,re.I)):
                raise ValueError('A prior target or actual cannot become a new promise')
            if re.search(r'\b(?:segment|vertical|division|business|9m|6m|h1|h2|ytd)\b|'
                         r'half.year|nine.month|six.month|year.to.date|adjusted|excluding',item.quote,re.I):raise ValueError('Metric scope differs')
            def percent(value):
                if value is None:return False
                try:v=Decimal(value)
                except InvalidOperation:return False
                if not v.is_finite():return False
                return any(Decimal(m[1])==v for m in re.finditer(r'(-?\d+(?:\.\d+)?)\s*(?:%|percent)',item.quote,re.I))
            values=[item.value] if item.kind=='actual' else [item.lower]+([item.upper] if item.operator=='band' else [])
            if not all(percent(v) for v in values):raise ValueError('Percentage is absent or ambiguous')
            if item.kind=='actual' and item.operator!='actual':raise ValueError('Invalid actual operator')
            if item.kind=='guidance' and item.operator not in {'band','at_least'}:raise ValueError('Invalid guidance operator')
            combined=item.quote+' '+item.context_quote
            periods={period(m[0]) for m in re.finditer(PERIOD,combined,re.I)}
            target=item.target_period
            if target not in periods:
                if not (target=='FY'+reported.split('FY')[-1] and re.search(r'full year|financial year|annual',item.quote,re.I)):
                    raise ValueError('Target period is not supported')
            basis,_=accounting_basis(doc,combined)
            if basis!=item.basis or item.basis=='unknown':raise ValueError('Accounting basis is not supported')
            cc=bool(re.search(r'constant.currency',combined,re.I))
            definition=('constant_currency_yoy' if cc else 'reported_currency_yoy') if item.metric=='revenue_growth' else 'reported_'+item.metric
            if item.metric=='revenue_growth' and not target.startswith('FY') and not re.search(r'year.on.year|\by[- ]?o(?:n)?[- ]?y\b',item.quote,re.I):raise ValueError('Growth denominator is unknown')
            evidence={**src['citation'],'quote':item.quote}
            context={**ctx['citation'],'quote':item.context_quote}
            facts.append({'kind':item.kind,'metric':item.metric,'target_period':target,'statement_period':reported,
                'unit':'percent','definition':definition,'basis':basis,'scope':'company','scope_verified':True,'horizon_verified':True,
                'speaker':src.get('speaker'),'speaker_verified':src.get('speaker_verified',False),
                'requires_visual_review':src.get('requires_visual_review',False),'citation':evidence,
                'context_citations':[context]+([src['speaker_evidence']] if src.get('speaker_evidence') else []),
                'lower':item.lower,'upper':item.upper,'value':item.value,'comparison_operator':item.operator,
                'method':'model_proposal_with_literal_value_context_role_checks'})
        except ValidationError as exc:
            rejections.append('Observation schema did not match the required fields')
            schema_rejections.extend({'field':e['loc'][0] if e['loc'] and e['loc'][0] in Fact.model_fields else 'unknown_field',
                                      'type':e['type']} for e in exc.errors(include_input=False,include_url=False))
        except (ValueError,KeyError,TypeError) as exc:rejections.append(str(exc))
    return facts,{'usage':usage,'accepted_observations':len(facts),'rejected_observations':len(rejections),
                  'rejection_reasons':rejections,'schema_rejections':schema_rejections}
