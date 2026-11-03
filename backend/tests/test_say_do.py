from finn.say_do import evaluate,observations
import pytest

def fact(kind):
 return dict(kind=kind,metric='operating_margin',target_period='Q1 FY2027',unit='percent',definition='reported_operating_margin',basis='consolidated',speaker_verified=True,citation={'quote':'synthetic'},lower='20',upper='22',value='21')

def test_aligned_and_mismatched_horizons():
 assert evaluate(fact('guidance'),fact('actual'))['status']=='within_target'
 assert evaluate(dict(fact('guidance'),target_period='FY2027'),fact('actual'))['status']=='not_comparable'
 assert evaluate(dict(fact('guidance'),basis='not_explicit'),fact('actual'))['status']=='review_required'
 assert evaluate(fact('guidance'),None)['status']=='actual_unavailable'

def test_literal_extraction_does_not_invent_basis_or_speaker():
 d={'kind':'transcript','url':'https://example.test','sha256':'a'*64,'fetched_at':'2026-01-01','pages':[{'page':1,'text':'Q4 FY2026\nOur operating margin guidance for financial year 2027 is 20% to 22%.'}]}
 out=observations(d)
 assert out[0]['target_period']=='FY2027'
 assert out[0]['basis']=='not_explicit'
 assert not out[0].get('speaker_verified')
