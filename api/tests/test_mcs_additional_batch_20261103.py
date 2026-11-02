"""Exact missing context precedes source links and explanation-only publication."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
s=importlib.util.spec_from_file_location('additional_batch',ROOT/'scripts/prepare-mcs-additional-batch-20261103.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
@pytest.fixture
def packet(tmp_path):
    p=json.loads(m.PACKET.read_text());questions=[]
    for i in p['items']:
        q=copy.deepcopy(i['reviewed_raw_record']);questions.append(q);doc=i['source_document'];path=tmp_path/doc['source_file'];path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'synthetic source PDF');doc['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        if q.get('figureImage'):
            image=tmp_path/q['figureImage'];image.parent.mkdir(parents=True,exist_ok=True);image.write_bytes(b'synthetic existing figure')
    return p,dict(questions=questions,papers=[dict(id=pid,year=2023 if '2023'in pid else 2025)for pid in p['scope']['paper_ids']]),tmp_path

def apply(bank,request):
    by={q['id']:q for q in bank['questions']}
    for i in request['items']:by[i['proposal']['appearance_id']].update(i['proposal']['patch']);by[i['proposal']['appearance_id']]['reviewPublicationId']='synthetic-audit-receipt'

def test_context_then_locators_then_explanations(packet):
    p,b,r=packet;before=copy.deepcopy(b)
    with pytest.raises(ValueError):m.prepare(p,b,r,'explanations')
    with pytest.raises(ValueError):m.prepare(p,b,r,'locators')
    req,_=m.prepare(p,b,r,'contexts');assert b==before and len(req['items'])==5
    assert sum(set(i['proposal']['patch'])=={'direction'}for i in req['items'])==4
    assert all(set(i['proposal']['patch'])<={'question','direction'}for i in req['items']);apply(b,req)
    req,_=m.prepare(p,b,r,'locators');assert len(req['items'])==13
    assert all(set(i['proposal']['patch'])=={'page'}for i in req['items']);apply(b,req)
    req,_=m.prepare(p,b,r,'explanations');assert len(req['items'])==93
    assert all(set(i['proposal']['patch'])=={'explanation'}for i in req['items'])

def test_changed_key_blocks_source_context(packet):
    p,b,r=packet;q=next(q for q in b['questions']if q['id']=='08aa866bfdcecb3c3c93');q['answerIndex']=0
    with pytest.raises(ValueError):m.prepare(p,b,r,'contexts')

def test_missing_direction_blocks_explanation_even_after_page_fixes(packet):
    p,b,r=packet
    for i,q in zip(p['items'],b['questions']):q.update(i['required_source_patch'])
    q=next(q for q in b['questions']if q.get('direction'));q.pop('direction')
    with pytest.raises(ValueError):m.prepare(p,b,r,'explanations')

def test_changed_pdf_blocks_context_and_explanation(packet):
    p,b,r=packet;i=next(i for i in p['items']if'direction'in i['required_source_patch']);(r/i['source_document']['source_file']).write_bytes(b'changed source')
    with pytest.raises(ValueError):m.prepare(p,b,r,'contexts')
