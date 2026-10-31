import copy
import pytest
from app.services.answer_comparison import published_comparison, source_matches, CONTEXT

CURRENT={'paperId':'p','question':'Which option?','options':['A text','B text'],
 'qnum':'3','direction':'Choose one','questionMarkup':None,'optionsMarkup':None,
 'passage':None,'hasDiagram':False,'figureImage':None}
DOC={'id':'key','paper_id':'p','title':'Final key','sha256':'a'*64,'kind':'official-key','key_status':'final'}

def publication(mode,index=0,state='applied'):
 return {'id':'pub_'+mode,'state':state,'finished_at':None,'manifest':{
  'baseline':{'record':copy.deepcopy(CURRENT)},'admin_decision':{'mode':mode},
  'payload':{'kind':'answer','patch':{'answerIndex':index,'answerSource':'official'if mode=='official'else'derived','answerKeyRef':'key'if mode=='official'else None,'explanation':'Worked explanation.'},
    'evidence':[{'kind':'official-key','document_id':'key','sha256':'a'*64,'page':2,'printed_question':'3','answer_text':CURRENT['options'][index]}] if mode=='official'else[]}}}

def compare(pubs,docs=None,**kw):return published_comparison(CURRENT,pubs,docs if docs is not None else {'key':DOC},**kw)

def test_agreement_keeps_two_independent_publications():
 r=compare([publication('official'),publication('verified')]);assert r['relation']=='agree'
 assert r['official']['publication_id']!=r['solution']['publication_id']
 assert r['official']['document']['page']==2 and r['solution']['document']is None

def test_disagreement_is_not_silently_overwritten():
 r=compare([publication('official',0),publication('verified',1)])
 assert r['relation']=='disagree' and r['official']['answer_text']=='A text' and r['solution']['answer_text']=='B text'

def test_official_key_is_not_independent_verification():
 r=compare([publication('official')]);assert r['solution']is None and r['relation']=='not-compared'

def test_inferred_and_unattested_derived_are_not_verified():
 for mode in ['inferred','answer','unsolved']:
  assert compare([publication(mode)])['solution']is None

@pytest.mark.parametrize('state',['exported','failed','reverted'])
def test_unapplied_or_reverted_publications_hidden(state):
 r=compare([publication('official',state=state),publication('verified',state=state)])
 assert not r['official']and not r['solution']

@pytest.mark.parametrize('field',CONTEXT)
def test_source_changes_invalidate_both_lanes(field):
 a=publication('official');b=publication('verified')
 for p in [a,b]:p['manifest']['baseline']['record'][field]='changed'
 assert compare([a,b])['official']is None and compare([a,b])['solution']is None

@pytest.mark.parametrize('field,value',[('paper_id','wrong'),('sha256','b'*64),('kind','reference'),('key_status','superseded')])
def test_key_registry_must_match(field,value):
 doc={**DOC,field:value};assert compare([publication('official')],{'key':doc})['official']is None

@pytest.mark.parametrize('field,value',[('page',None),('page',True),('printed_question','4'),('answer_text','B text'),('sha256','b'*64)])
def test_exact_key_cell_required(field,value):
 p=publication('official');p['manifest']['payload']['evidence'][0][field]=value
 assert compare([p])['official']is None

def test_latest_reviewed_solution_wins_in_newest_first_order():
 r=compare([publication('verified',1),publication('verified',0),publication('official',0)])
 assert r['relation']=='disagree' and r['solution']['answer_index']==1

def test_held_state_and_review_note_preserved():
 r=compare([publication('official'),publication('verified')],held=True,review_note='Source ambiguity remains.')
 assert r['held']and r['review_note']=='Source ambiguity remains.'

@pytest.mark.parametrize('index',[True,-1,2,None])
def test_malformed_answers_never_disclosed(index):
 p=publication('verified');p['manifest']['payload']['patch']['answerIndex']=index
 assert compare([p])['solution']is None

def separate_solution(index):
 p=publication('verified');d=p['manifest']['admin_decision'];d.update(preserve_official_key=True,solution_answer_text=CURRENT['options'][index])
 p['manifest']['payload'].update(kind='explanation',patch={'explanation':'Separate reviewed reasoning.'},evidence=[{'kind':'reasoning','answer_text':CURRENT['options'][index],'note':'Reviewed reasoning.'}])
 return p

def test_separate_explanation_retains_official_answer():
 r=compare([separate_solution(1),publication('official',0)],held=True)
 assert r['official']['answer_text']=='A text'and r['solution']['answer_text']=='B text'and r['relation']=='disagree'and r['held']

def test_ordinary_explanation_does_not_certify_answer():
 p=separate_solution(1);p['manifest']['admin_decision'].pop('preserve_official_key')
 assert compare([p])['solution']is None

def test_separate_review_requires_exact_reasoning_answer():
 p=separate_solution(1);p['manifest']['payload']['evidence'][0]['answer_text']='A text'
 assert compare([p])['solution']is None
