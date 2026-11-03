"""Evidence-based checks: a configured model is not a successful provider call."""


def has_live_usage(value):
    if isinstance(value,dict):
        usage=value.get('usage')
        if isinstance(usage,dict) and usage.get('live') is True:return True
        return any(has_live_usage(item) for item in value.values())
    if isinstance(value,list):return any(has_live_usage(item) for item in value)
    return False


def push_model_check(analysis):
    if not analysis:return {'passed':False,'reason':'No saved analysis'}
    classification=analysis.get('classification') or {};enrichment=analysis.get('enrichment') or {}
    failed=[stage for stage,output in [('classification',classification),('enrichment',enrichment)]
            if 'unavailable' in output.get('model_status','') or 'invalid' in output.get('model_status','')]
    needs=classification.get('category') in {'results','management_change'}
    enriched=enrichment.get('status') in {'extracted','source_extracted','partial'}
    live=has_live_usage(analysis)
    return {'passed':analysis.get('status')=='processed' and live and not failed and (not needs or enriched),
            'live_usage_recorded':live,'failed_model_stages':failed,'category':classification.get('category'),
            'enrichment_status':enrichment.get('status'),'primary_status':analysis.get('status'),'needs_enrichment':needs}


def model_preflight(models):
    records=[];seen=set()
    for model in models:
        if model.model in seen:continue
        seen.add(model.model)
        try:
            value,usage=model.generate('Return exactly {"ready": true} as a structured-output connection check.',{},
                {'type':'object','properties':{'ready':{'type':'boolean'}},'required':['ready'],'additionalProperties':False})
            records.append({'model':model.model,'passed':value.get('ready') is True and usage.get('live') is True,'usage':usage})
        except Exception as exc:records.append({'model':model.model,'passed':False,'error':str(exc)})
    return {'passed':bool(records) and all(r['passed'] for r in records),'models':records}


REVIEW_FILES=('result.json','acceptance.json','research.json','live-model-push.json','model-preflight.json',
              'push-audit.json','source-audit.json','cold-http.json','warm.json','portfolio.json','day1-audit/summary.json')


def create_review_bundle(out):
    from pathlib import Path
    from zipfile import ZipFile,ZIP_DEFLATED
    out=Path(out)
    with ZipFile(out/'day3_verification.zip','w',compression=ZIP_DEFLATED) as archive:
        for name in REVIEW_FILES:
            path=out/name
            if path.is_file():archive.write(path,name)
    return out/'day3_verification.zip'
