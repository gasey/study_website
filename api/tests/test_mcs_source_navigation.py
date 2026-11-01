"""Source navigation preparation preserves answers and requires exact staged context."""
import copy,hashlib,importlib.util
from pathlib import Path
import pytest
from review_bank_store import record,digest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('nav',ROOT/'scripts/prepare-mcs-source-navigation.py')
nav=importlib.util.module_from_spec(spec);spec.loader.exec_module(nav)

@pytest.fixture
def source_fixture(tmp_path):
    path=tmp_path/'pdfs/p.pdf';path.parent.mkdir();path.write_bytes(b'fixed test PDF evidence')
    q=dict(id='a',paperId='p',type='mcq',qnum=89,page=14,question='Bent tree? ( 3  1.73)',options=['12.73','13.84','15.34','17.3'],answerIndex=1,answerSource='official',answerKeyRef='exact-key',explanation='Existing explanation preserved',classifications=[dict(subject_id='mathematics',topic_id=None,subtopic_id=None,is_primary=True,review_status='approved')])
    doc=dict(id='doc',kind='paper',paper_id='p',source_file='pdfs/p.pdf',sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    base=dict(appearance_id='a',canonical_id='cq_a',paper_id='p',source_document=doc,physical_pdf_page=15,baseline_sha256=digest(q),expected_source=record(q),reason='Exact inspected source page and printed radical restored.')
    transcription={**base,'kind':'transcription','patch':{'question':'Bent tree? (√3 = 1.73)'}}
    locator={**base,'kind':'source_reference','patch':{'page':15}}
    return dict(items=[transcription,locator]),dict(questions=[q]),tmp_path

def test_transcription_only_changes_stem(source_fixture):
    packet,bank,root=source_fixture;original=copy.deepcopy(bank)
    result=nav.prepare(packet,bank,root,'transcription');assert len(result['items'])==1
    assert result['items'][0]['proposal']['patch']=={'question':'Bent tree? (√3 = 1.73)'}
    assert result['items'][0]['expected_source']['answerKeyRef']=='exact-key'
    assert bank==original

def test_locator_requires_exact_predecessor(source_fixture):
    packet,bank,root=source_fixture
    with pytest.raises(ValueError,match='predecessor'):nav.prepare(packet,bank,root,'source_reference')
    bank['questions'][0]['question']='Bent tree? (√3 = 1.73)'
    result=nav.prepare(packet,bank,root,'source_reference');assert result['items'][0]['proposal']['patch']=={'page':15}
    bank['questions'][0]['page']=15
    assert nav.prepare(packet,bank,root,'source_reference')['items']==[]

@pytest.mark.parametrize('field,value',[('answerIndex',0),('answerSource','derived'),('answerKeyRef','other-key'),('explanation','Replacement'),('page',13)])
def test_changed_baseline_rejected(source_fixture,field,value):
    packet,bank,root=source_fixture;bank['questions'][0][field]=value
    with pytest.raises(ValueError,match='baseline'):nav.prepare(packet,bank,root,'transcription')

def test_changed_pdf_rejected(source_fixture):
    packet,bank,root=source_fixture;(root/'pdfs/p.pdf').write_bytes(b'changed')
    with pytest.raises(ValueError,match='PDF'):nav.prepare(packet,bank,root,'transcription')

def test_answer_patch_injection_rejected(source_fixture):
    packet,bank,root=source_fixture;packet['items'][0]['patch']['answerIndex']=0
    with pytest.raises(ValueError,match='Only'):nav.prepare(packet,bank,root,'transcription')

def test_arbitrary_stem_edit_rejected(source_fixture):
    packet,bank,root=source_fixture;packet['items'][0]['patch']['question']='Invented different question'
    with pytest.raises(ValueError,match='radical'):nav.prepare(packet,bank,root,'transcription')
