import copy
import json
from decimal import Decimal
from pathlib import Path
from finn.annual_forensics import extract_annual,extract_leverage


def fixture():
    return json.loads((Path(__file__).parent/'fixtures/day3/deepakntr-financials.json').read_text())


def test_real_reconciled_cash_and_leverage():
    doc=fixture();result=extract_annual(doc)
    assert len(result['facts'])==4
    current=result['periods'][0]
    assert current['period_end']=='2026-03-31'
    assert Decimal(current['cash_conversion']['value'])==Decimal('538.95')/Decimal('550.66')
    lev=extract_leverage(doc)
    assert lev[0]['debt_crore']=='1527.82'
    assert lev[0]['equity_crore']=='5869.28'


def test_tampered_cash_subtotal_abstains():
    doc=fixture()
    doc['pages'][-1]['text']=doc['pages'][-1]['text'].replace('538.95','738.95')
    result=extract_annual(doc)
    assert not [f for f in result['facts'] if f['metric']=='cfo']
    assert result['rejections']


def test_unknown_currency_and_scans_abstain():
    doc=fixture()
    for p in doc['pages']:p['text']=p['text'].replace('₹','?')
    assert not extract_annual(doc)['facts']
    doc=fixture()
    for p in doc['pages']:p['requires_visual_review']=True
    assert not extract_annual(doc)['facts']
    assert not extract_leverage(doc)


def test_unbalanced_balance_sheet_abstains():
    doc=fixture()
    doc['pages'][0]['text']=doc['pages'][0]['text'].replace('5,869.28','5,869.29').replace('8,680.68','9,680.68')
    assert not extract_leverage(doc)
