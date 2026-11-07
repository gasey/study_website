"""Pure local publication guards; synthetic records, no DB or network."""
import copy
import importlib.util
from pathlib import Path
import pytest
from review_bank_store import digest, record

spec=importlib.util.spec_from_file_location('owner_batch_source_warnings',Path(__file__).resolve().parents[2]/'scripts/publish-owner-review-batch.py')
batch=importlib.util.module_from_spec(spec);spec.loader.exec_module(batch)


def packet(tmp_path,kind,patch,index=1):
    q={'id':'synthetic-appearance','paperId':'synthetic-paper','type':'mcq','question':'Choose a pair of words.',
       'options':['first, pair','incomplete','third, pair','fourth, pair'],'answerIndex':index,'answerSource':'derived'}
    doc=tmp_path/'source.pdf';doc.write_bytes(b'Synthetic source evidence, not a real exam.')
    sha=batch.sha(doc)
    m={'schema':1,'id':'pub_synthetic','author_id':'synthetic-owner','contribution_id':'con_synthetic','bank_sha256':'a'*64,
       'payload':{'kind':kind,'canonical_id':'cq_synthetic','patch':patch,'evidence':[{'kind':'paper','document_id':'doc_synthetic','sha256':sha,'page':1}]},
       'baseline':{'record':record(q),'metadata':{}},'operator_maintenance':{'owner_id':'synthetic-owner'},
       'documents':[{'source_file':'source.pdf','sha256':sha}]}
    return {'questions':[q],'papers':[{'id':'synthetic-paper'}]}, {'id':m['id'],'manifest':m,'manifest_hash':digest(m)}


def run(tmp_path,kind,patch,index=1):
    bank,pub=packet(tmp_path,kind,patch,index)
    return batch.prepare(bank,[pub],'a'*64,tmp_path)


def test_warning_can_withdraw_but_not_assign(tmp_path):
    out,_=run(tmp_path,'transcription',{'answerIndex':None,'explanation':'Printed option is incomplete; no missing word has been invented.'})
    assert out['questions'][0]['answerIndex']is None
    assert out['questions'][0]['answerSource']=='derived'


@pytest.mark.parametrize('patch',[
    {'explanation':'A warning without an explicit answer withdrawal is rejected.'},
    {'answerIndex':2,'explanation':'An answer assignment cannot masquerade as a source warning.'},
    {'answerIndex':None,'explanation':'too short'},
    {'answerIndex':None,'answerSource':'official','explanation':'A source warning cannot introduce official provenance.'},
])
def test_reject_invalid_source_warning(tmp_path,patch):
    with pytest.raises(ValueError):run(tmp_path,'transcription',patch)


def test_unresolved_source_flag_requires_withdrawn_answer(tmp_path):
    patch={'sourceDefect':'unresolved-source','disputeNote':'Original paper has an incomplete choice; review is required.'}
    out,_=run(tmp_path,'defect',patch,index=None)
    assert out['questions'][0]['sourceDefect']=='unresolved-source'
    with pytest.raises(ValueError):run(tmp_path,'defect',patch,index=1)


def test_unresolved_flag_requires_paper_evidence(tmp_path):
    bank,pub=packet(tmp_path,'defect',{'sourceDefect':'unresolved-source','disputeNote':'Printed choice is incomplete and needs source review.'},None)
    pub['manifest']['payload']['evidence']=[];pub['manifest_hash']=digest(pub['manifest'])
    with pytest.raises(ValueError):batch.prepare(bank,[pub],'a'*64,tmp_path)

@pytest.mark.parametrize('defect',['valid','answered','missing-evidence','missing-image','wrong-flag','duplicate-options'])
def test_reviewed_unresolved_clearance_has_no_answer_and_requires_readable_source(tmp_path,defect):
    bank,pub=packet(tmp_path,'defect',{'sourceDefect':None,'disputeNote':'Checked registered paper shows complete distinct options; source warning is resolved.'},None)
    q=bank['questions'][0];pub['manifest']['baseline']['metadata']['sourceDefect']='unresolved-source'
    if defect=='answered':q['answerIndex']=0
    if defect=='missing-evidence':pub['manifest']['payload']['evidence']=[]
    if defect=='missing-image':q['hasDiagram']=True;q['figureImage']=None
    if defect=='wrong-flag':pub['manifest']['baseline']['metadata']['sourceDefect']='diagram-not-embedded'
    if defect=='duplicate-options':q['options']=['same','same']
    pub['manifest']['baseline']['record']=record(q);pub['manifest_hash']=digest(pub['manifest'])
    if defect=='valid':
        out,_=batch.prepare(bank,[pub],'a'*64,tmp_path)
        assert out['questions'][0]['sourceDefect']is None
        assert out['questions'][0]['answerIndex']is None
    else:
        with pytest.raises(ValueError):batch.prepare(bank,[pub],'a'*64,tmp_path)

@pytest.mark.parametrize('kind,patch',[
    ('source_reference',{'page':2,'qnum':'7'}),
    ('transcription',{'direction':'Answer any two questions from this printed section.','passage':'Source context.'}),
])
def test_written_source_repair_preserves_identity_and_has_no_answer(tmp_path,kind,patch):
    bank,pub=packet(tmp_path,kind,patch,None)
    q=bank['questions'][0];q.update(type='descriptive',options=[],answerSource=None)
    pub['manifest']['baseline']['record']=record(q);pub['manifest_hash']=digest(pub['manifest'])
    out,journal=batch.prepare(bank,[pub],'a'*64,tmp_path)
    assert out['questions'][0]['id']==q['id']
    assert out['questions'][0]['answerIndex'] is None
    assert out['questions'][0]['answerSource'] is None
    assert all(out['questions'][0][k]==v for k,v in patch.items())
    assert journal['receipts'][0]['appearance_id']==q['id']

@pytest.mark.parametrize('patch',[{'options':['new','choices']},{'answerIndex':None},{'hasDiagram':True}])
def test_written_source_batch_rejects_mcq_mutation(tmp_path,patch):
    bank,pub=packet(tmp_path,'transcription',patch,None)
    q=bank['questions'][0];q.update(type='descriptive',options=[],answerSource=None)
    pub['manifest']['baseline']['record']=record(q);pub['manifest_hash']=digest(pub['manifest'])
    with pytest.raises(ValueError,match='Written source repairs'):
        batch.prepare(bank,[pub],'a'*64,tmp_path)

@pytest.mark.parametrize('journal,current,valid',[
    (None,'before',False),({'output_sha256':'after'},'before',False),
    ({'output_sha256':'after'},'unrelated',False),({'output_sha256':'after'},'after',True),
])
def test_failed_ack_recovery_requires_exact_already_written_output(journal,current,valid):
    pubs=[{'state':'failed'}]
    if valid:batch.require_recoverable_failures(pubs,journal,current)
    else:
        with pytest.raises(ValueError,match='already-written'):batch.require_recoverable_failures(pubs,journal,current)
