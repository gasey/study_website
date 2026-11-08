"""Pure publication/feedback regressions; runnable with pytest --noconftest."""
import copy
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import pytest
from app.services.publication_verification import CANONICAL_FIELDS,publication_mismatches,verification_status
from app.services.study_feedback import saved_feedback_changes,presentation_digest


def example():
    expected={'id':'appearance-a','type':'mcq','question':'Choose the second letter',
      'options':['A','B','C','D'],'answerIndex':1,'answerSource':'official','answerKeyRef':'key-1',
      'explanation':'B is the second letter.','direction':'Read the choices','passage':None,
      'questionMarkup':None,'optionsMarkup':None,'hasDiagram':False,'figureImage':None,
      'difficulty':'legacy-medium','classification':{'subject_id':'english'}}
    canonical={target:expected[source] for source,target in CANONICAL_FIELDS.items()}
    canonical.update(answer_text='B',difficulty=None,source_defect=None,status='live',key_disputed=False)
    return expected,canonical


def test_exact_receipt_and_retired_difficulty():
    expected,canonical=example()
    assert publication_mismatches(expected,copy.deepcopy(expected),canonical,True,{})==[]
    canonical['difficulty']='legacy-medium'
    assert publication_mismatches(expected,expected,canonical,True,{})==['canonical.difficulty']


@pytest.mark.parametrize('field',list(CANONICAL_FIELDS.values())+['answer_text'])
def test_canonical_drift_blocks_publication_even_when_source_matches(field):
    expected,canonical=example();canonical[field]='DRIFT'
    differences=publication_mismatches(expected,expected,canonical,True,{})
    assert 'canonical.'+field in differences
    assert 'DRIFT' not in str(differences),'Verification must expose field names, not replacement answers'


def test_source_context_options_and_missing_null_fields_are_checked():
    expected,canonical=example();record=copy.deepcopy(expected)
    record['options']=['B','A','C','D'];record['passage']='Another passage';del record['questionMarkup']
    assert publication_mismatches(expected,record,canonical,True,{})==[
      'source.options','source.passage','source.questionMarkup']


def test_nonprimary_source_does_not_overwrite_shared_canonical():
    expected,canonical=example();canonical['question']='Primary question'
    assert publication_mismatches(expected,expected,canonical,False,{})==[]
    assert publication_mismatches(expected,None,canonical,False,{})==['source.unavailable']


def test_defect_publication_and_later_valid_publication_are_distinct():
    expected,canonical=example()
    fields=publication_mismatches(expected,expected,canonical,True,{'sourceDefect':'unresolved-source'})
    assert fields==['canonical.source_defect']
    assert verification_status(fields)=='mismatch'
    assert verification_status(fields,True)=='changed_since_publication'
    assert verification_status([],True)=='matched'


def test_real_worker_refuses_provenance_drift(monkeypatch):
    path=Path(__file__).resolve().parents[2]/'scripts/bank-review-worker.py'
    spec=importlib.util.spec_from_file_location('verify_worker_regression',path)
    worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    expected,canonical=example();rows=[{'record':expected,'canonical':canonical,'is_primary':True}]
    receipt={'after':expected};manifest={'payload':{'patch':{}}}
    worker.verify_live_rows(receipt,manifest,rows)
    canonical['answer_source']='inferred'
    with pytest.raises(ValueError,match='canonical.answer_source'):
        worker.verify_live_rows(receipt,manifest,rows)


def test_worker_projection_reads_real_postgres_and_detects_canonical_only_drift(tmp_path,monkeypatch):
    pg=Path('/usr/lib/postgresql/16/bin')
    if not (pg/'postgres').is_file():pytest.skip('PostgreSQL standalone binary unavailable')
    cluster=tmp_path/'pg'
    subprocess.run([str(pg/'initdb'),'-D',str(cluster),'-A','trust'],check=True,capture_output=True)
    def sql(statement,json_result=False):
        if json_result:statement="SELECT COALESCE(json_agg(result),'[]'::json) AS result FROM ("+statement+") result;"
        result=subprocess.run([str(pg/'postgres'),'--single','-D',str(cluster),'postgres'],
          input=statement.replace('\n',' ')+'\n',text=True,capture_output=True,check=True)
        assert not re.search(r'\b(ERROR|FATAL):',result.stderr),result.stderr
        if json_result:
            match=re.search(r'result = "(.*)"\s+\(typeid',result.stdout)
            assert match,result.stdout
            return json.loads(match[1])
    expected,canonical=example();canonical['id']='qid'
    expected.update(paperId='paper',page=1,qnum='1')
    expected['classification'].update(topic_id=None,subtopic_id=None)
    source={target:expected[name] for name,target in CANONICAL_FIELDS.items()}
    source.update(id='appearance-a',paper_id='paper',canonical_id='qid',is_primary=True,
      answer_index=1,difficulty='legacy-medium',page=1,qnum='1',has_diagram=False,figure_image=None)
    def create(table,values):
        types={'options':'jsonb','options_markup':'jsonb','key_disputed':'boolean','is_primary':'boolean',
          'has_diagram':'boolean','page':'int','answer_index':'int'}
        def value(v):
            if v is None:return 'NULL'
            if isinstance(v,bool):return 'true' if v else 'false'
            if isinstance(v,(dict,list)):v=json.dumps(v)
            return "'"+str(v).replace("'","''")+"'"
        sql('CREATE TABLE '+table+'('+','.join(key+' '+types.get(key,'text') for key in values)+');'+
            'INSERT INTO '+table+' VALUES ('+','.join(map(value,values.values()))+');')
    create('canonical_questions',canonical);create('appearances',source)
    create('question_classifications',{'question_id':'qid','subject_id':'english','topic_id':None,'subtopic_id':None})
    sql('CREATE TABLE question_topic_links(question_id text,subject_id text,topic_id text,subtopic_id text,review_status text);')
    path=Path(__file__).resolve().parents[2]/'scripts/bank-review-worker.py'
    spec=importlib.util.spec_from_file_location('postgres_verification_worker',path)
    worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    monkeypatch.setattr(worker,'remote',sql)
    receipt={'appearance_id':'appearance-a','after':expected};manifest={'payload':{'patch':{}}}
    worker.verify_live(receipt,manifest)
    sql("UPDATE canonical_questions SET answer_source='inferred' WHERE id='qid';")
    with pytest.raises(ValueError,match='canonical.answer_source'):worker.verify_live(receipt,manifest)


def old_feedback():
    _,current=example()
    source={'id':'appearance-a','has_diagram':False,'figure_image':None}
    snap={k:current.get(k) for k in ('question','options','answer_text','answer_source','direction','passage','question_markup','options_markup')}
    snap.update(appearance_id='appearance-a',has_diagram=False,figure_image=None)
    return snap,{'correct':True,'answer_text':'B','explanation':current['explanation']},current,source


def test_saved_feedback_is_preserved_but_later_key_and_option_changes_are_flagged():
    snap,response,current,source=old_feedback();before=copy.deepcopy((snap,response))
    assert saved_feedback_changes(snap,response,current,source)==[]
    current.update(answer_text='C',options=['B','A','C','D'])
    assert saved_feedback_changes(snap,response,current,source)==['options','answer']
    assert (snap,response)==before


def test_saved_feedback_marks_figure_context_hold_and_unavailability_without_replacement_answers():
    snap,response,current,source=old_feedback()
    source.update(figure_image='images/changed.png',has_diagram=True,passage='New passage')
    current['status']='held'
    assert saved_feedback_changes(snap,response,current,source)==['passage','figure','review status']
    assert saved_feedback_changes(snap,response,None,None)==['availability']


def test_saved_independent_review_status_cannot_inherit_a_different_current_status():
    snap,response,current,source=old_feedback()
    snap['reviewed_derived']=True;current['reviewed_derived']=True
    assert saved_feedback_changes(snap,response,current,source)==[]
    current['reviewed_derived']=False
    assert saved_feedback_changes(snap,response,current,source)==['review status']


def test_presentation_token_detects_admin_edits_but_contains_no_answer():
    question={'id':'q','type':'mcq','question':'Case-sensitive ABC','options':['A','B'],
      'source_appearance':{'paper_id':'paper','qnum':'7','page':2}}
    original=presentation_digest(question)
    assert len(original)==64 and original==presentation_digest(copy.deepcopy(question))
    assert original==presentation_digest({**question,'answer_text':'DO NOT EXPOSE'})
    for patch in ({'question':'Case-sensitive abc'},{'options':['B','A']},{'passage':'New passage'},
                  {'figure_image_url':'/changed.png'},{'source_appearance':{'paper_id':'other'}}):
        assert presentation_digest({**question,**patch})!=original


@pytest.mark.parametrize('stale',[False,True])
def test_udc_check_rejects_stale_display_before_grading(monkeypatch,stale):
    import asyncio
    from contextlib import asynccontextmanager
    from types import SimpleNamespace
    from unittest.mock import AsyncMock
    from fastapi import HTTPException
    from app.routers import study_sessions as route
    row={'question_ids':['qid'],'paper_ids':['paper'],'position':0,'version':1,'finished_at':None}
    class Cursor:
        def __init__(self):self.queries=[]
        async def execute(self,sql,params=None):self.queries.append(sql)
        async def fetchall(self):return []
        async def fetchone(self):return row
    cur=Cursor()
    @asynccontextmanager
    async def cursor():yield cur
    monkeypatch.setattr(route,'cursor',cursor)
    monkeypatch.setattr(route,'owned',AsyncMock(return_value=row))
    monkeypatch.setattr(route,'receipts',AsyncMock(return_value={}))
    monkeypatch.setattr(route,'state',AsyncMock(return_value={'items':[SimpleNamespace(id='qid',presentation_hash='b'*64)]}))
    grader=AsyncMock();monkeypatch.setattr(route,'_answer_question',grader)
    body=route.Check(version=1,question_id='qid',chosen_index=0,presentation_hash=('a' if stale else 'b')*64)
    if stale:
        with pytest.raises(HTTPException) as exc:asyncio.run(route.check('set',body,'learner'))
        assert exc.value.status_code==409 and 'no attempt was recorded' in exc.value.detail
        grader.assert_not_awaited()
        assert not any(sql.startswith('UPDATE') for sql in cur.queries)
    else:
        asyncio.run(route.check('set',body,'learner'))
        grader.assert_awaited_once()
    assert any('FOR SHARE' in sql for sql in cur.queries)


@pytest.mark.parametrize('later,drift,expected_status',[(False,False,'matched'),(False,True,'mismatch'),(True,True,'changed_since_publication')])
def test_admin_recheck_reads_current_source_and_canonical_without_writing(monkeypatch,later,drift,expected_status):
    import asyncio
    from contextlib import asynccontextmanager
    from datetime import datetime,timezone
    from types import SimpleNamespace
    from unittest.mock import AsyncMock
    from app.routers import admin_answers as route
    expected,canonical=example();canonical.update(id='qid',current_subject='english',answer_status='needs-review' if drift else 'official')
    if drift:canonical['answer_source']='inferred'
    stamp=datetime.now(timezone.utc)
    pub={'id':'pub','canonical_id':'qid','subject_id':'english','state':'applied','finished_at':stamp,
         'receipt':{'appearance_id':'appearance-a','after':expected},'manifest':{'payload':{'patch':{}}}}
    class Cursor:
        def __init__(self):self.queries=[];self.value=None
        async def execute(self,sql,params=None):
            self.queries.append(sql)
            if 'SELECT p.*' in sql:self.value=pub
            elif 'transaction_timestamp' in sql:self.value={'checked_at':stamp}
            elif 'SELECT q.*' in sql:self.value=canonical
            elif 'SELECT is_primary' in sql:self.value={'is_primary':True}
            elif 'SELECT EXISTS' in sql:self.value={'newer':later}
        async def fetchone(self):return self.value
    cur=Cursor()
    @asynccontextmanager
    async def cursor():yield cur
    monkeypatch.setattr(route,'cursor',cursor)
    permission=AsyncMock();monkeypatch.setattr(route,'require_role',permission)
    protection=AsyncMock();monkeypatch.setattr(route.service,'protect_answer',protection)
    monkeypatch.setattr(route.service,'snapshot',AsyncMock(return_value={'record':expected}))
    result=asyncio.run(route.verify_publication('pub',SimpleNamespace(id='owner')))
    assert result['status']==expected_status
    assert cur.queries[0]=='SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'
    assert not any(sql.lstrip().split()[0] in {'UPDATE','INSERT','DELETE'} for sql in cur.queries)
    assert permission.await_count==2
    protection.assert_awaited_once_with(cur,'owner','qid')
    assert 'receipt' not in result and 'canonical' not in result


def test_adjusted_assessment_preserves_original_result_and_maps_reordered_options_by_text():
    from app.services.scoring_revisions import evaluate
    snap,response,current,source=old_feedback()
    current['presentation']={key:snap.get(key) for key in ('direction','passage','question_markup','options_markup','has_diagram','figure_image')}
    before=copy.deepcopy((snap,response))
    current['options']=['B','A','C','D']
    assert evaluate(snap,current,'B','derived-practice')['outcome']=='correct'
    current['answer_text']='C'
    adjusted=evaluate(snap,current,'B','derived-practice')
    assert adjusted['outcome']=='wrong' and adjusted['reason']=='key_corrected'
    current['presentation']['passage']='Changed source passage'
    assert evaluate(snap,current,'B','derived-practice')['outcome']=='excluded'
    assert (snap,response)==before


@pytest.mark.parametrize('source,valid',[(None,True),('none',True),('derived',False),('official',False),('key',False)])
def test_written_absent_provenance_accepts_sync_normalization_only(source,valid):
    expected,canonical=example()
    expected.update(type='descriptive',options=[],answerIndex=None,answerSource=None,answerKeyRef=None)
    canonical.update(type='descriptive',options=[],answer_text=None,answer_source=source,answer_key_ref=None)
    result=publication_mismatches(expected,expected,canonical,True,{'page':2})
    assert ('canonical.answer_source' not in result)==valid


def test_unanswered_mcq_provenance_comparison_stays_strict():
    expected,canonical=example();expected.update(answerIndex=None,answerSource=None)
    canonical.update(answer_text=None,answer_source='none')
    assert 'canonical.answer_source' in publication_mismatches(expected,expected,canonical,True,{})


@pytest.mark.parametrize('source,accepted',[('none',True),('derived',False),('official',False),('inferred',False)])
def test_tag_only_unanswered_mcq_accepts_only_absent_provenance(source,accepted):
    expected,canonical=example();expected.update(answerIndex=None,answerSource=None)
    canonical.update(answer_text=None,answer_source=source)
    patch={'classification':{'subject_id':'english'}}
    assert ('canonical.answer_source' not in publication_mismatches(expected,expected,canonical,True,patch))==accepted
    assert 'canonical.answer_source' in publication_mismatches(expected,expected,canonical,True,{'explanation':'Other change'})


def test_tag_only_absent_provenance_does_not_mask_an_answer():
    expected,canonical=example();expected.update(answerIndex=None,answerSource=None)
    canonical.update(answer_text='Unexpected answer',answer_source='none')
    result=publication_mismatches(expected,expected,canonical,True,{'classification':{'subject_id':'english'}})
    assert 'canonical.answer_source' in result and 'canonical.answer_text' in result
