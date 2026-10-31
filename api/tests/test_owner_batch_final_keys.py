"""Final-key batch guards: synthetic files only; no database or network."""
import copy
import importlib.util
from pathlib import Path
import pytest
from review_bank_store import digest,record

spec=importlib.util.spec_from_file_location('final_key_batch',Path(__file__).resolve().parents[2]/'scripts/publish-owner-review-batch.py')
batch=importlib.util.module_from_spec(spec);spec.loader.exec_module(batch)

def packet(tmp_path):
    f=tmp_path/'key.pdf';f.write_bytes(b'Synthetic local final-key evidence; not an actual exam.')
    q={'id':'appearance','paperId':'paper-series-A','qnum':7,'type':'mcq','question':'Synthetic question?',
       'options':['first','second','third'],'answerIndex':None,'answerSource':'none'}
    doc={'id':'key_synthetic','paper_id':q['paperId'],'source_file':'key.pdf','sha256':batch.sha(f),'kind':'official-key','key_status':'final'}
    m={'schema':1,'id':'pub_synthetic','author_id':'owner','contribution_id':'con_synthetic','bank_sha256':'a'*64,
       'admin_decision':{'mode':'official'},'baseline':{'record':copy.deepcopy(record(q))},'documents':[{k:v for k,v in doc.items()if k!='key_status'}],
       'payload':{'kind':'answer','canonical_id':'cq_synthetic','patch':{'answerIndex':1,'answerSource':'official','answerKeyRef':doc['id'],'explanation':'Exact final examiner key maps the second printed choice.'},
                  'evidence':[{'kind':'official-key','document_id':doc['id'],'sha256':doc['sha256'],'page':2,'printed_question':'7','answer_text':'second'}]}}
    return {'questions':[q],'papers':[{'id':q['paperId']}]},m,{doc['id']:doc}

def apply(tmp_path,bank,m,keys):
    return batch.prepare(bank,[{'id':m['id'],'manifest':m,'manifest_hash':digest(m)}],'a'*64,tmp_path,keys)

def test_exact_final_key_is_publishable(tmp_path):
    bank,m,keys=packet(tmp_path);out,journal=apply(tmp_path,bank,m,keys)
    assert out['questions'][0]['answerIndex']==1
    assert out['questions'][0]['answerSource']=='official'
    assert journal['receipts'][0]['after']['answerKeyRef']=='key_synthetic'

def test_exact_final_key_does_not_require_a_fabricated_worked_explanation(tmp_path):
    bank,m,keys=packet(tmp_path);m['payload']['patch']['explanation']=None
    out,journal=apply(tmp_path,bank,m,keys)
    assert out['questions'][0]['explanation']is None
    assert journal['receipts'][0]['after']['answerSource']=='official'

def test_unofficial_solution_still_requires_worked_explanation(tmp_path):
    bank,m,keys=packet(tmp_path);m['admin_decision']['mode']='verified'
    m['payload']['patch'].update(answerSource='derived',answerKeyRef=None,explanation=None)
    with pytest.raises(ValueError,match='worked explanation'):apply(tmp_path,bank,m,keys)

@pytest.mark.parametrize('field,value',[
    ('key_status','provisional'),('key_status','superseded'),('paper_id','paper-series-B'),('sha256','b'*64),('kind','reference'),('source_file','other.pdf'),
])
def test_wrong_or_stale_registered_key_is_rejected(tmp_path,field,value):
    bank,m,keys=packet(tmp_path);keys['key_synthetic'][field]=value
    with pytest.raises(ValueError):apply(tmp_path,bank,m,keys)

@pytest.mark.parametrize('field,value',[
    ('printed_question','8'),('answer_text','first'),('page',0),('page',None),('document_id','other-key'),('sha256','b'*64),('kind','reasoning'),
])
def test_inexact_key_cell_is_rejected(tmp_path,field,value):
    bank,m,keys=packet(tmp_path);m['payload']['evidence'][0][field]=value
    with pytest.raises(ValueError):apply(tmp_path,bank,m,keys)

def test_official_requires_live_final_registry_lookup(tmp_path):
    bank,m,keys=packet(tmp_path)
    with pytest.raises(ValueError):apply(tmp_path,bank,m,{})

def test_unofficial_decision_cannot_claim_official_provenance(tmp_path):
    bank,m,keys=packet(tmp_path);m['admin_decision']['mode']='verified'
    with pytest.raises(ValueError):apply(tmp_path,bank,m,keys)

def test_final_key_document_must_remain_immutable(tmp_path):
    bank,m,keys=packet(tmp_path);(tmp_path/'key.pdf').write_bytes(b'Changed after review')
    with pytest.raises(ValueError):apply(tmp_path,bank,m,keys)

def test_choice_order_changes_require_fresh_review(tmp_path):
    bank,m,keys=packet(tmp_path);bank['questions'][0]['options'].reverse()
    with pytest.raises(ValueError):apply(tmp_path,bank,m,keys)

def test_source_repair_cannot_assign_official_answer(tmp_path):
    bank,m,keys=packet(tmp_path);m['payload']['kind']='transcription';m['operator_maintenance']={'owner_id':'owner'}
    with pytest.raises(ValueError):apply(tmp_path,bank,m,keys)
