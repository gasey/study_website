"""Offline gates: model consensus never grants approval or changes a key."""
import copy,importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('pilot',Path(__file__).resolve().parents[2]/'scripts/prepare-explanation-pilot.py');pilot=importlib.util.module_from_spec(spec);spec.loader.exec_module(pilot)
def fixtures():
    bank={'id':'q','question':'Choose one','options':['A','B'],'answerIndex':0,'answerSource':'official'}
    question={'id':'q','canonical_id':'cq_q','question':'Choose one','options':['A','B'],'topic':'english/grammar','identity_sha256':pilot.identity(bank),'source':{'paper_id':'paper.pdf','path':'unused','sha256':'a'*64,'page':1,'printed_question':'1'}}
    draft={'id':'q','answer_index':0,'status':'proposed','explanation':'The first option supplies the correct verb for this sentence because the singular subject requires a singular verb in the simple present tense here.','option_analysis':[{'index':0,'reason':'Singular subject agrees with this singular verb.'},{'index':1,'reason':'The plural verb does not agree with the singular subject.'}],'citations':[{'url':'https://example.test/grammar','title':'Synthetic grammar rule','supports':'Synthetic unit test reference only.'}],'source_checks':['Synthetic source checked']}
    blind={'id':'q','answer_index':0,'status':'supported','source_checks':['Synthetic source checked']}
    critique={'id':'q','status':'approve_draft','presentation_fixes':[]};keys={'id':'q','answer_index':0}
    return [[question],[draft],[blind],[critique],[keys],[bank]]
def run(rows):return pilot.adjudicate(*rows,check_files=False)[0]
def test_ready_packet_only_patches_explanation_and_discloses_model_review():
    row=run(fixtures());assert row['status']=='ready_for_human_review'
    assert set(row['proposal']['patch'])=={'explanation'}
    assert 'not human approvals' in row['proposal']['evidence'][0]['note']
def test_disagreement_context_fix_and_changed_baseline_block_packet():
    for change in ['answer','presentation','baseline','status']:
        data=fixtures()
        if change=='answer':data[2][0]['answer_index']=1
        if change=='presentation':data[3][0]['presentation_fixes']=[{'field':'direction'}]
        if change=='baseline':data[5][0]['question']='Changed after drafting'
        if change=='status':data[3][0]['status']='revise'
        row=run(data);assert row['status']=='hold' and row['proposal']is None

def test_malformed_or_generic_outputs_are_held():
    for analysis in [['bad'],[{'index':False,'reason':'Generic reason here'},{'index':1,'reason':'Generic reason here'}],[{'index':0,'reason':'Matches the passage deduction or grammatical rule'},{'index':1,'reason':'A genuinely specific other reason.'}]]:
        data=fixtures();data[1][0]['option_analysis']=analysis
        assert run(data)['status']=='hold'
    for citation in [{'url':None},{'url':'http://example.test','title':'Rule','supports':'Enough text here'},{'url':'https://user:secret@example.test','title':'Rule','supports':'Enough text here'}]:
        data=fixtures();data[1][0]['citations']=[citation];assert run(data)['status']=='hold'
