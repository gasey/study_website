"""Exact-source backfill guards and arithmetic checks for the checked MCS packet."""
import copy,hashlib,importlib.util,json,math
from fractions import Fraction as F
from pathlib import Path
import pytest
from review_bank_store import record,digest
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('mcs_explanation_preparer',ROOT/'scripts/prepare-mcs-explanation-batch.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)


def fixture(tmp_path):
    p=tmp_path/'pdfs/paper.pdf';p.parent.mkdir();p.write_bytes(b'Synthetic source, not a real examination.')
    q={'id':'a','paperId':'MCS Combined 2023 synthetic','type':'mcq','question':'Choose the synthetic source answer.', 'options':['One','Two'],'answerIndex':1,'answerSource':'key','answerKeyRef':'original-reference','qnum':'1','page':1,'explanation':None,'classifications':[{'subject_id':'english','is_primary':True}]}
    item={'appearance_id':'a','canonical_id':'cq_a','baseline_sha256':digest(q),'expected_source':record(q),'source_document':{'id':'doc','kind':'paper','paper_id':q['paperId'],'source_file':'pdfs/paper.pdf','sha256':hashlib.sha256(p.read_bytes()).hexdigest()},'physical_pdf_page':1,'explanation':'The existing second choice fits the stated synthetic source rule.','source_review_note':'Read the exact source and checked the reasoning.','supporting_references':[]}
    bank={'questions':[q],'papers':[{'id':q['paperId'],'year':2023}]};packet={'scope':{'paper_ids':[q['paperId']]},'items':[item]}
    return packet,bank


def test_preparation_changes_only_explanation_and_preserves_key_reference(tmp_path):
    packet,bank=fixture(tmp_path);old=copy.deepcopy(bank)
    request,identical=m.prepare(packet,bank,tmp_path)
    assert bank==old and not identical
    item=request['items'][0]
    assert item['proposal']['kind']=='explanation'
    assert item['proposal']['patch']=={'explanation':packet['items'][0]['explanation']}
    assert item['expected_source']['answerSource']=='key'and item['expected_source']['answerKeyRef']=='original-reference'


@pytest.mark.parametrize('change',['answer','reference','options','direction','already-written','pdf','outside-scope','duplicate-target'])
def test_backfill_requires_original_answer_source_and_empty_text(tmp_path,change):
    packet,bank=fixture(tmp_path);q=bank['questions'][0]
    if change=='answer':q['answerIndex']=0
    if change=='reference':q['answerKeyRef']='another-reference'
    if change=='options':q['options']=['One','Changed']
    if change=='direction':q['direction']='New unreviewed context'
    if change=='already-written':q['explanation']='Existing useful working must not be overwritten.'
    if change=='pdf':(tmp_path/'pdfs/paper.pdf').write_bytes(b'Changed source')
    if change=='outside-scope':packet['scope']['paper_ids']=[]
    if change=='duplicate-target':packet['items'].append(copy.deepcopy(packet['items'][0]))
    with pytest.raises(ValueError):m.prepare(packet,bank,tmp_path)


def test_identical_text_can_be_skipped_without_claiming_a_publication(tmp_path):
    packet,bank=fixture(tmp_path);bank['questions'][0]['explanation']=packet['items'][0]['explanation']
    request,identical=m.prepare(packet,bank,tmp_path)
    assert not request['items']and identical==['a']


def test_checked_packet_is_explanation_only_and_keeps_ambiguous_source_work_separate():
    packet=json.loads(m.PACKET.read_text())
    assert len(packet['items'])==72 and len(packet['groups'])==28
    assert all(i['expected_source']['explanation']is None for i in packet['items'])
    assert all(i['expected_source']['answerIndex']is not None and i['physical_pdf_page']>=1 for i in packet['items'])
    assert all(i['category']in('math','english','factual')for i in packet['items'])
    assert all(i['native_text_checked']or i['visual_source_checked']for i in packet['items'])
    tree=next(g for g in packet['groups']if g['id']=='mcsx-94182f6079df')
    assert '8√3'in tree['explanation']and '13.84'in tree['explanation']


def test_math_working_independently_satisfies_the_stated_constraints():
    assert F('228.96')/((1+F(12,100))**2-1)==900
    assert 16==2*8 and 12==3*4 and 16-12==8-4
    assert 5*30-4*28==38
    man=F(1,24*16);woman=F(1,32*24);team=16*(man+woman)
    assert team==F(1,16)and(1-12*team)/2-team==24*man
    assert F(80,40+120)==F(1,2)
    assert 1057%23==22 and (1057+1)%23==0
    assert 7+(34-1)*6==205
    assert F(1,12)-F(1,30)==F(1,20)
    assert 2*F(1,2)**2+7*F(1,2)-4==0
    assert math.isclose((math.sqrt(5)+math.sqrt(2))**2,7+2*math.sqrt(10))
    assert F(4,3)*21**3/F('1.4')**2/100==63
    assert (1-9*(F(1,45)+F(1,40)))/F(1,40)==23
    assert math.isclose(4*math.sqrt(121)/(2*float(F(22,7))),7)
    assert math.sqrt(15**2-9**2)+math.sqrt(15**2-12**2)==21
    assert F(280*12-300*10,300*10)==F(12,100)
    assert 50-5==3*(20-5)and 50+10==2*(20+10)
    assert F(240)/F(20,100)+240==1440
    assert F(15*48,30)==24
    assert 24*F(1,3)*F('1.73')==F('13.84')
    assert F(540,60)*40==360
