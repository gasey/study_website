"""Offline checks for exact-source repair phases and preserved case-sensitive keys."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
def module(name):
 s=importlib.util.spec_from_file_location(name,ROOT/'scripts'/name);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
F=module('prepare-mcs-figure-repairs.py');S=module('prepare-mcs-source-repairs-20261102.py');E=module('prepare-mcs-completion-explanations.py')
@pytest.fixture
def data(tmp_path):
 fp=json.loads(F.PACKET.read_text());sp=json.loads(S.PACKET.read_text());ep=json.loads((ROOT/'docs/sources/mcs-checked-explanations-20261102.json').read_text())
 by={}
 for items,key in [(fp['items'],'original_raw_record'),(sp['items'],'original_raw_record'),(ep['items'],'reviewed_raw_record')]:
  for item in items:by[item['appearance_id']]=copy.deepcopy(item[key])
 # Synthetic source bytes keep these checks independent of the external bank,
 # production SSH and archive. The committed snapshots supply only test shapes.
 for packet in [fp,sp,ep]:
  for item in packet['items']:
   for doc in [item['source_document']]+([item['key']]if 'key'in item else[]):
    path=tmp_path/doc['source_file'];path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'synthetic source fixture');doc['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
   if 'figure_sha256'in item:
    image=b'synthetic image fixture';sha=hashlib.sha256(image).hexdigest();item['figure_image']='images/page-renders/'+sha+'.png';item['figure_sha256']=sha;path=tmp_path/item['figure_image'];path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(image)
 for q in by.values():
  if q.get('figureImage'):
   path=tmp_path/q['figureImage'];path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'synthetic existing figure')
 bank=dict(questions=list(by.values()),papers=[dict(id=pid,year=2023 if '2023' in pid else 2025)for pid in {q['paperId']for q in by.values()}])
 return bank,fp,sp,ep,by,tmp_path

def test_figure_phases_require_exact_predecessor(data):
 bank,p,_,_,by,root=data
 for idx in range(2):
  req=F.prepare(p,bank,root,'withdraw',idx);assert req['repair']['mode']=='unsolved';by[p['items'][idx]['appearance_id']].update(answerIndex=None,answerSource='none',answerKeyRef=None,explanation=p['items'][idx]['withdrawal_explanation'])
 for phase in ['transcription','defect']:
  req=F.prepare(p,bank,root,phase)
  for item in req['items']:by[item['proposal']['appearance_id']].update(item['proposal']['patch'])
 req=F.prepare(p,bank,root,'answers');assert [r['answer_index']for r in req['repairs']]==[1,1];assert all(r['mode']=='official'for r in req['repairs'])

def test_figure_cannot_skip_withdrawal(data):
 bank,p,_,_,_,root=data
 with pytest.raises(ValueError):F.prepare(p,bank,root,'transcription')

def test_source_and_explanation_prerequisites(data):
 bank,_,p,e,by,root=data
 with pytest.raises(ValueError):E.prepare(e,bank,root)
 for phase in ['transcription','locators']:
  req=S.prepare(p,bank,root,phase)
  for item in req['items']:by[item['proposal']['appearance_id']].update(item['proposal']['patch'])
 req,same=E.prepare(e,bank,root);assert len(req['items'])==18 and not same
 assert all(set(i['proposal']['patch'])=={'explanation'}for i in req['items'])
 assert len([i for i in req['items']if 'GRAPHITE'in i['expected_source']['question']])==4

def test_changed_option_or_context_rejected(data):
 bank,_,p,_,by,root=data;by[p['items'][0]['appearance_id']]['options'][0]='different source choice'
 with pytest.raises(ValueError):S.prepare(p,bank,root,'transcription')

def test_source_cannot_mutate_answers(data):
 bank,_,p,_,_,root=data;p['items'][0]['patch']['answerIndex']=2
 with pytest.raises(ValueError):S.prepare(p,bank,root,'transcription')

def test_figure_reordered_mapping_rejected(data):
 bank,p,_,_,_,root=data;p['items'][0]['key']['answer_index']=0
 with pytest.raises(ValueError):F.prepare(p,bank,root,'withdraw',0)
