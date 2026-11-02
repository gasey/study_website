"""Offline replay and tampering checks for exact-source image restoration."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'));s=importlib.util.spec_from_file_location('mcs_images',ROOT/'scripts/prepare-mcs-image-restoration-20261103.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
@pytest.fixture
def fixture(tmp_path):
 p=json.loads(m.PACKET.read_text());qs=[]
 for i in p['items']:
  q=copy.deepcopy(i['original_raw_record']);qs.append(q)
  path=tmp_path/i['source_document']['source_file'];path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'synthetic PDF');i['source_document']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
  data=b'synthetic image';sha=hashlib.sha256(data).hexdigest();i['figure_image']='images/page-renders/'+sha+'.png';i['figure_sha256']=sha;path=tmp_path/i['figure_image'];path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
 return p,dict(questions=qs),tmp_path

def test_three_phases_preserve_answers_and_options(fixture):
 p,b,root=fixture;by={q['id']:q for q in b['questions']};before=copy.deepcopy(by)
 for phase,count in [('images',9),('locators',4),('explanations',9)]:
  req=m.prepare(p,b,root,phase);assert len(req['items'])==count
  for item in req['items']:by[item['proposal']['appearance_id']].update(item['proposal']['patch'])
 for aid,q in by.items():
  for key in ['answerIndex','answerSource','answerKeyRef','options','question','classifications']:assert q.get(key)==before[aid].get(key)
  assert q['explanation']and q['figureImage']

def test_cannot_skip_image_and_page_predecessors(fixture):
 p,b,root=fixture
 for phase in ['locators','explanations']:
  with pytest.raises(ValueError):m.prepare(p,b,root,phase)

def test_edited_source_choices_rejected(fixture):
 p,b,root=fixture;b['questions'][0]['options'][0]='Changed choice'
 with pytest.raises(ValueError):m.prepare(p,b,root,'images')

def test_asset_tampering_rejected(fixture):
 p,b,root=fixture;(root/p['items'][0]['figure_image']).write_bytes(b'changed pixels')
 with pytest.raises(ValueError):m.prepare(p,b,root,'images')

def test_pdf_tampering_rejected(fixture):
 p,b,root=fixture;(root/p['items'][0]['source_document']['source_file']).write_bytes(b'changed PDF')
 with pytest.raises(ValueError):m.prepare(p,b,root,'images')

def test_nonempty_explanation_is_not_overwritten(fixture):
 p,b,root=fixture;by={q['id']:q for q in b['questions']}
 for phase in ['images','locators']:
  for i in m.prepare(p,b,root,phase)['items']:by[i['proposal']['appearance_id']].update(i['proposal']['patch'])
 b['questions'][0]['explanation']='An existing teacher explanation must survive.'
 with pytest.raises(ValueError):m.prepare(p,b,root,'explanations')
