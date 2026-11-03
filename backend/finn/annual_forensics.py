"""Strict two-column annual cash/PAT reconciliation from primary statements.

Unsupported units, headers, layouts and cash subtotals abstain. No Screener input.
"""
import calendar
import re
from datetime import date,timedelta
from decimal import Decimal
from .evidence import citation
from .finance import number,to_crores
from .forensic_analyzer import ratio

NUM=r'\(?-?\d[\d,]*(?:\.\d+)?\)?'


def row(text,label,allow_note=False):
    lines=list(re.finditer(r'[^\n]+',text))
    found=[]
    for i,line in enumerate(lines):
        if not re.fullmatch(label,line[0].strip(),re.I):continue
        following=[m for m in lines[i+1:] if m[0].strip()]
        if len(following)<3:continue
        if allow_note and len(following)>=4 and re.fullmatch(r'\d{1,2}',following[0][0].strip()) and all(re.fullmatch(NUM,m[0].strip()) for m in following[1:3]):
            following=following[1:]
        values=[m[0].strip() for m in following[:2]]
        if not all(re.fullmatch(NUM,v) for v in values):continue
        if re.fullmatch(NUM,following[2][0].strip()):continue
        valid=True
        for value in values:
            raw=value.strip('()-')
            if ',' in raw and not re.fullmatch(r'(?:\d{1,3}(?:,\d{3})+|\d{1,2}(?:,\d{2})*,\d{3})(?:\.\d+)?',raw):valid=False
        if valid:found.append(([number(v) for v in values],text[line.start():following[1].end()].strip()))
    return found[0] if len(found)==1 else None



def context(page):
    text=page['text']
    if page.get('requires_visual_review'):return None
    if not re.search(r'(?im)^\s*Consolidated (?:Statement of Profit and Loss|Cash Flow Statement|Statement of Cash Flows|Balance Sheet)\s*$',text):return None
    if re.search(r'\bstandalone\b|\bUSD\b|US\s*\$',text,re.I):return None
    unit=re.findall(r'(?:₹|INR|Rs\.?|Rupees)\s*(?:in\s*)?(Crores?|Lakhs?|Millions?)',text,re.I)
    if len(set(x.lower().rstrip('s') for x in unit))!=1:return None
    months='|'.join(calendar.month_name[1:])
    headers=re.findall(r'(?:(?:For\s+the\s+)?year\s+ended|as\s+at)\s+('+months+r')\s+(\d{1,2}),?\s+(20\d{2})',text,re.I)
    dates=[]
    for month,day,year in headers:
        m=next(i for i in range(1,13) if calendar.month_name[i].lower()==month.lower())
        end=date(int(year),m,int(day))
        if end not in dates:dates.append(end)
    if len(dates)!=2 or not 364<=(dates[0]-dates[1]).days<=366:return None
    return dates,unit[0].lower().rstrip('s')+'s'


def extract_annual(document):
    facts=[];rejections=[]
    for page in document.get('pages',[]):
        ctx=context(page)
        if not ctx:continue
        dates,unit=ctx;text=page['text']
        cfo=row(text,r'Net Cash (?:Inflow from|Generated from|Provided by|from) Operating Activities(?:\s*\(A\))?')
        pat=row(text,r'Profit for the Year(?:\s*\([IVX-]+\))?')
        if cfo:
            generated=row(text,r'Cash Generated from Operations')
            taxes=row(text,r'Income Tax Paid(?:\s*\(net of refund\))?')
            if not generated or not taxes or any(abs(g+t-c)>Decimal('.02') for g,t,c in zip(generated[0],taxes[0],cfo[0])):
                rejections.append({'page':page['page'],'reason':'Cash subtotal reconciliation unavailable or failed'});cfo=None
        if pat:
            pbt=row(text,r'Profit before tax(?:\s*\([IVX-]+\))?')
            current=row(text,r'Current Tax');deferred=row(text,r'Deferred Tax')
            if not pbt or not current or not deferred or any(abs(b-c-d-p)>Decimal('.02') for b,c,d,p in zip(pbt[0],current[0],deferred[0],pat[0])):
                rejections.append({'page':page['page'],'reason':'PAT reconciliation unavailable or failed'});pat=None
        for metric,found in [('cfo',cfo),('pat',pat)]:
            if not found:continue
            for end,value in zip(dates,found[0]):
                try:start=end.replace(year=end.year-1)+timedelta(days=1)
                except ValueError:continue
                normalized=to_crores(str(value),unit)
                facts.append({'metric':metric,'value':str(normalized),'period_start':start.isoformat(),'period_end':end.isoformat(),
                    'duration':'annual','currency':'INR','unit':'crore','basis':'consolidated',
                    'definition':'total_group_profit_including_NCI' if metric=='pat' else 'net_cash_after_operating_tax',
                    'reviewed_primary':True,'method':'strict_two_column_reconciled_statement',
                    'citations':[citation(document,page['page'],found[1]),citation(document,page['page'],text)]})
    periods=sorted({f['period_end'] for f in facts},reverse=True)
    analysis=[]
    for end in periods:
        cfo=[f for f in facts if f['metric']=='cfo' and f['period_end']==end]
        pat=[f for f in facts if f['metric']=='pat' and f['period_end']==end]
        result=ratio(cfo[0] if len(cfo)==1 else None,pat[0] if len(pat)==1 else None)
        analysis.append({'period_end':end,'cash_conversion':result})
    return {'facts':facts,'periods':analysis,'rejections':rejections,
            'status':'partial' if facts else 'unsupported_layout','source_url':document['url']}


def extract_leverage(document):
    output=[]
    for page in document.get('pages',[]):
        ctx=context(page);text=page['text']
        if not ctx or not re.search(r'(?im)^Consolidated Balance Sheet\s*$',text):continue
        dates,unit=ctx
        current=re.search(r'(?im)^Current Liabilities\s*$',text)
        noncurrent=re.search(r'(?im)^Non-Current Liabilities\s*$',text)
        if not current or not noncurrent or noncurrent.start()>current.start():continue
        long=row(text[noncurrent.end():current.start()],r'Borrowings',True)
        short=row(text[current.end():],r'Borrowings',True)
        equity=row(text,r'Total Equity')
        assets=row(text,r'TOTAL ASSETS');liabilities=row(text,r'Total Liabilities')
        if not all((long,short,equity,assets,liabilities)):continue
        if any(abs(a-e-l)>Decimal('.02') for a,e,l in zip(assets[0],equity[0],liabilities[0])):continue
        for i,end in enumerate(dates):
            debt=long[0][i]+short[0][i];eq=equity[0][i]
            output.append({'period_end':end.isoformat(),'basis':'consolidated','currency':'INR',
                'debt_crore':str(to_crores(str(debt),unit)),'equity_crore':str(to_crores(str(eq),unit)),
                'debt_to_equity':str(debt/eq) if eq>0 else None,
                'reconciliation_proof':{'noncurrent_borrowings_crore':str(to_crores(str(long[0][i]),unit)),
                    'current_borrowings_crore':str(to_crores(str(short[0][i]),unit)),
                    'assets_crore':str(to_crores(str(assets[0][i]),unit)),
                    'liabilities_crore':str(to_crores(str(liabilities[0][i]),unit)),
                    'residual_raw':str(assets[0][i]-eq-liabilities[0][i]),'tolerance_raw':'0.02',
                    'source_unit':unit,'status':'passed'},
                'definition':'current_plus_noncurrent_reported_borrowings_excluding_leases_over_total_equity_including_NCI',
                'status':'computed' if eq>0 else 'undefined',
                'citations':[citation(document,page['page'],q) for q in (long[1],short[1],equity[1],text)]})
    return output
