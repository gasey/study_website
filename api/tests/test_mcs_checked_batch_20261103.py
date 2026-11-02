"""Offline exact-predecessor and explanation-only tests for the checked packet."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'));s=importlib.util.spec_from_file_location('checked_batch',ROOT/'scripts/prepare-mcs-checked-batch-20261103.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
@pytest.fixture
def packet(tmp_path):
 p=json.loads(m.PACKET.read_text());questions=[]
 for i in p['items']:
  q=copy.deepcopy(i['reviewed_raw_record']);questions.append(q);doc=i['source_document'];path=tmp_path/doc['source_file'];path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'synthetic PDF source');doc['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
  if q.get('figureImage'):
   path=tmp_path/q['figureImage'];path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'synthetic existing figure')
 papers=[dict(id=pid,year=2023 if '2023'in pid else 2025)for pid in {q['paperId']for q in questions}]
 return p,dict(questions=questions,papers=papers),tmp_path

def test_tree_precedes_eighty_explanation_only_patches(packet):
 p,b,root=packet;before=copy.deepcopy(b)
 with pytest.raises(ValueError):m.prepare(p,b,root,'explanations')
 request,same=m.prepare(p,b,root,'tree');assert len(request['items'])==1 and not same
 item=request['items'][0];assert set(item['proposal']['patch'])=={'question'};assert b==before
 q=next(q for q in b['questions']if q['id']==item['proposal']['appearance_id']);q.update(item['proposal']['patch'])
 request,same=m.prepare(p,b,root,'explanations');assert len(request['items'])==80 and not same
 assert all(set(i['proposal']['patch'])=={'explanation'}for i in request['items'])

def test_no_unreviewed_tree_rewrite(packet):
 p,b,root=packet;i=next(i for i in p['items']if i['required_source_patch']);i['required_source_patch']['question']='Changed distance or approximation'
 with pytest.raises(ValueError):m.prepare(p,b,root,'tree')

def test_changed_ordered_choices_fail_before_source_patch(packet):
 p,b,root=packet;q=next(q for q in b['questions']if q['id']=='0eed0b2ebf96f8e03af7');q['options'].reverse()
 with pytest.raises(ValueError):m.prepare(p,b,root,'tree')

def test_source_hash_change_is_rejected(packet):
 p,b,root=packet;i=next(i for i in p['items']if i['required_source_patch']);(root/i['source_document']['source_file']).write_bytes(b'a changed PDF')
 with pytest.raises(ValueError):m.prepare(p,b,root,'tree')
