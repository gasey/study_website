"""Guard source predecessors and explanation-only updates before publication."""
import copy,hashlib,importlib.util
from pathlib import Path
import pytest
from review_bank_store import record,digest
ROOT=Path(__file__).resolve().parents[2]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
ex=module('completion','scripts/prepare-mcs-completion-explanations.py')
reading=module('reading','scripts/prepare-mcs-reading-passages.py')

@pytest.fixture
def prepared(tmp_path):
    pid='MCS Combined 2025 source.pdf';path=tmp_path/'pdfs'/pid;path.parent.mkdir();path.write_bytes(b'exact source')
    q=dict(id='a',paperId=pid,type='mcq',qnum=1,page=1,question='What does the passage say?',options=['A','B','C','D'],answerIndex=1,answerSource='official',answerKeyRef='key',explanation='',passage=None,legacy='preserved',classifications=[dict(subject_id='english',topic_id=None,subtopic_id=None,is_primary=True,review_status='approved')])
    passage='A complete source passage with enough context for independent reading. '*3
    doc=dict(id='doc',kind='paper',paper_id=pid,source_file='pdfs/'+pid,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    expected={**q,'passage':passage}
    item=dict(appearance_id='a',canonical_id='cq_a',paper_id=pid,kind='transcription',reviewed_raw_record=copy.deepcopy(q),baseline_sha256=digest(q),expected_source=record(q),required_source_patch={'passage':passage},post_source_expected=record(expected),source_document=doc,physical_pdf_page=2,source_pages=[1,2],passage_kind='context',patch={'passage':passage},source_review_note='Entire original passage inspected on both physical source pages.',explanation='The source passage explicitly establishes the keyed answer.',supporting_references=[])
    packet=dict(scope={'paper_ids':[pid]},items=[item],blocks=[dict(paper_id=pid,kind='context',text=passage,source_pages=[1,2])])
    return packet,dict(questions=[q],papers=[dict(id=pid,year=2025)]),tmp_path

def test_missing_predecessor_refused(prepared):
    packet,bank,root=prepared
    with pytest.raises(ValueError,match='not completed'):ex.prepare(packet,bank,root)

def test_exact_predecessor_and_publication_metadata_allowed(prepared):
    packet,bank,root=prepared;bank['questions'][0].update(packet['items'][0]['required_source_patch']);bank['questions'][0]['reviewPublicationId']='pub_source'
    request,identical=ex.prepare(packet,bank,root);assert not identical and len(request['items'])==1
    assert request['items'][0]['proposal']['patch']=={'explanation':packet['items'][0]['explanation']}
    assert request['items'][0]['expected_source']['answerKeyRef']=='key'

@pytest.mark.parametrize('field,value',[('answerIndex',0),('answerSource','derived'),('answerKeyRef','other'),('legacy','changed'),('page',3)])
def test_no_arbitrary_rebase(prepared,field,value):
    packet,bank,root=prepared;bank['questions'][0].update(packet['items'][0]['required_source_patch']);bank['questions'][0][field]=value
    with pytest.raises(ValueError,match='changed'):ex.prepare(packet,bank,root)

def test_no_nonempty_overwrite(prepared):
    packet,bank,root=prepared;bank['questions'][0]['explanation']='Existing different explanation'
    with pytest.raises(ValueError,match='Never overwrite'):ex.prepare(packet,bank,root)

def test_identical_explanation_is_only_skipped_when_source_unchanged(prepared):
    packet,bank,root=prepared;q=bank['questions'][0];q.update(packet['items'][0]['required_source_patch']);q['explanation']=packet['items'][0]['explanation'];q['reviewPublicationId']='pub_explanation'
    request,identical=ex.prepare(packet,bank,root);assert request['items']==[]and identical==['a']
    q['options'][0]='Changed option'
    with pytest.raises(ValueError):ex.prepare(packet,bank,root)

def test_inferred_answer_not_certified(prepared):
    packet,bank,root=prepared;q=bank['questions'][0];q.update(packet['items'][0]['required_source_patch']);q['answerSource']='inferred'
    with pytest.raises(ValueError,match='usable'):ex.prepare(packet,bank,root)

def test_reading_evidence_includes_continuation_and_question_pages(prepared):
    packet,bank,root=prepared;before=copy.deepcopy(bank);request=reading.prepare(packet,bank,root)
    assert bank==before and request['items'][0]['proposal']['patch']==packet['items'][0]['patch']
    assert [e['page']for e in request['items'][0]['proposal']['evidence']]==[1,2]

def test_reading_does_not_combine_answer_edits(prepared):
    packet,bank,root=prepared;packet['items'][0]['patch']['answerIndex']=0
    with pytest.raises(ValueError,match='complete exact'):reading.prepare(packet,bank,root)

def test_reading_changed_document_rejected(prepared):
    packet,bank,root=prepared;(root/packet['items'][0]['source_document']['source_file']).write_bytes(b'other')
    with pytest.raises(ValueError,match='paper changed'):reading.prepare(packet,bank,root)
