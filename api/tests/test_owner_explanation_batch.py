"""Explanation-only owner batches preserve existing usable answer provenance."""
import importlib.util
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from psycopg.types.json import Jsonb
import pytest
from pydantic import ValidationError

from app.services import bank_review as review
from app.services.review_policy import Proposal,digest

spec=importlib.util.spec_from_file_location('owner_explanation_batch',Path(__file__).resolve().parents[2]/'scripts/publish-owner-review-batch.py')
batch=importlib.util.module_from_spec(spec);spec.loader.exec_module(batch)

EXPLANATION='The sentence structure makes the second option the only grammatically consistent choice.'
AUTH='The owner explicitly delegated this isolated explanation maintenance rehearsal.'
REASON='Checked the explanation against the exact registered paper and existing answer.'

@pytest.fixture(autouse=True)
def isolate_export_queue(database):
    conn=database[1];existing=conn.execute("SELECT id FROM bank_publications WHERE state='exported'").fetchall()
    for row in existing:conn.execute("UPDATE bank_publications SET state='failed' WHERE id=%s",(row[0],))
    try:yield
    finally:
        for row in existing:conn.execute("UPDATE bank_publications SET state='exported' WHERE id=%s",(row[0],))


def _real_target(client,actor,database,source='official'):
    from test_learning_workflows import official
    conn=database[1];q,a,p=official(database);actor('owner')
    if source in {'key','derived'}:
        conn.execute("UPDATE canonical_questions SET answer_source=%s WHERE id=%s",(source,q))
        conn.execute("UPDATE appearances SET answer_source=%s WHERE id=%s",(source,a))
    document='explanation-paper-'+uuid4().hex
    conn.execute("INSERT INTO review_documents(id,paper_id,title,source_file,sha256,kind,registered_by) VALUES(%s,%s,'Synthetic paper','synthetic.pdf',%s,'paper','test')",(document,p,'b'*64))
    proposal=Proposal(kind='explanation',canonical_id=q,appearance_id=a,subject_id='english',title='Explain the existing answer',
        patch={'explanation':EXPLANATION},rationale='Explain why the existing printed answer follows from the exact source.',
        evidence=[{'kind':'paper','document_id':document,'sha256':'b'*64,'page':1,'note':'Exact synthetic paper evidence for this isolated test.'}])
    payload=proposal.model_dump(mode='json')
    async def queue(expected):
        from app.db import cursor
        from app.services.operator_maintenance import queue_source_batch
        async with cursor() as cur:
            return await queue_source_batch(cur,'owner',[{'proposal':payload,'expected_source':expected,'paper_id':p,'source_sha':'b'*64,'reason':REASON}],AUTH)
    async def snapshot():
        from app.db import cursor
        async with cursor() as cur:return await review.snapshot(cur,q,a)
    return conn,q,a,p,document,proposal,client.portal.call(snapshot),queue


@pytest.mark.parametrize('source',['official','key','derived'])
def test_owner_batch_explanation_preserves_existing_answer_and_has_no_reward(client,actor,database,source):
    conn,q,a,p,doc,proposal,snap,queue=_real_target(client,actor,database,source)
    before=snap['record'];result=client.portal.call(queue,before);pub=result['publications'][0]
    assert pub['state']=='exported'
    row=conn.execute('SELECT manifest FROM bank_publications WHERE id=%s',(pub['id'],)).fetchone()[0]
    assert row['baseline']['record']==before and row['payload']['kind']=='explanation'
    assert conn.execute('SELECT answer_index,answer_source,answer_key_ref FROM appearances WHERE id=%s',(a,)).fetchone()==(1,source,None)
    assert conn.execute("SELECT count(*) FROM contribution_events WHERE contribution_id=%s AND action='operator_source_adjudication'",(pub['contribution_id'],)).fetchone()[0]==1
    assert conn.execute('SELECT count(*) FROM contribution_decisions WHERE contribution_id=%s',(pub['contribution_id'],)).fetchone()[0]==0
    assert conn.execute('SELECT count(*) FROM contribution_credit WHERE contribution_id=%s',(pub['contribution_id'],)).fetchone()[0]==0
    conn.execute("UPDATE bank_publications SET state='applied' WHERE id=%s",(pub['id'],))


@pytest.mark.parametrize('failure',['missing-expected','mismatched-expected','held','flagged','duplicate-options','answer-changed','missing-figure','disputed'])
def test_owner_explanation_batch_rejects_unusable_or_unreviewed_baselines(client,actor,database,failure):
    conn,q,a,p,doc,proposal,snap,queue=_real_target(client,actor,database)
    expected=snap['record']
    if failure=='mismatched-expected':expected={**expected,'question':'Older source snapshot'}
    if failure=='held':conn.execute("UPDATE canonical_questions SET status='held' WHERE id=%s",(q,))
    if failure=='flagged':conn.execute("UPDATE canonical_questions SET source_defect='unresolved-source' WHERE id=%s",(q,))
    if failure=='missing-figure':conn.execute('UPDATE appearances SET has_diagram=true,figure_image=NULL WHERE id=%s',(a,))
    if failure=='disputed':conn.execute('UPDATE canonical_questions SET key_disputed=true WHERE id=%s',(q,))
    if failure=='duplicate-options':conn.execute('UPDATE appearances SET options=%s WHERE id=%s',(Jsonb(['same','same']),a))
    if failure=='answer-changed':conn.execute('UPDATE appearances SET answer_index=2 WHERE id=%s',(a,))
    if failure=='missing-expected':expected=None
    with pytest.raises(HTTPException):client.portal.call(queue,expected)
    assert conn.execute('SELECT count(*) FROM bank_publications WHERE contribution_id IN (SELECT id FROM bank_contributions WHERE canonical_id=%s)',(q,)).fetchone()[0]==0


def test_source_intake_rejects_answer_fields_and_blank_explanations(client,actor,database):
    conn,q,a,p,doc,proposal,snap,queue=_real_target(client,actor,database)
    from app.services.operator_maintenance import intake_source
    for patch in ({'explanation':' '},{'explanation':EXPLANATION,'answerIndex':2}):
        payload={**proposal.model_dump(mode='json'),'patch':patch}
        async def call():
            from app.db import cursor
            async with cursor()as cur:return await intake_source(cur,'owner',payload,AUTH)
        with pytest.raises((HTTPException,ValidationError)):client.portal.call(call)


def test_single_item_queue_cannot_skip_exact_batch_source_snapshot(client,actor,database):
    conn,q,a,p,doc,proposal,snap,queue=_real_target(client,actor,database)
    from app.services.operator_maintenance import intake_source,queue_source
    async def intake():
        from app.db import cursor
        async with cursor()as cur:return await intake_source(cur,'owner',proposal.model_dump(mode='json'),AUTH)
    created=client.portal.call(intake)
    async def single():
        from app.db import cursor
        async with cursor()as cur:return await queue_source(cur,'owner',created['id'],created['payload_hash'],p,'b'*64,REASON,AUTH)
    with pytest.raises(HTTPException):client.portal.call(single)
    assert conn.execute('SELECT count(*) FROM bank_publications WHERE contribution_id IN (SELECT id FROM bank_contributions WHERE canonical_id=%s)',(q,)).fetchone()[0]==0


def _publisher_packet(tmp_path,source='official'):
    q={'id':'synthetic-a','paperId':'paper-a','type':'mcq','question':'Pick the grammatical sentence.',
       'options':['First choice','Second choice','Third choice','Fourth choice'],'answerIndex':1,'answerSource':source,
       'answerKeyRef':None,'explanation':None,'hasDiagram':False}
    file=tmp_path/'paper.pdf';file.write_bytes(b'synthetic registered paper evidence')
    file_sha=batch.sha(file)
    manifest={'schema':1,'id':'pub_explanation','author_id':'owner-a','contribution_id':'con_explanation','bank_sha256':'a'*64,
        'payload':{'kind':'explanation','canonical_id':'cq-a','patch':{'explanation':EXPLANATION},
                   'evidence':[{'kind':'paper','document_id':'doc-a','sha256':file_sha,'page':1}]},
        'baseline':{'record':batch.record(q),'metadata':{'sourceDefect':None}},
        'documents':[{'id':'doc-a','kind':'paper','paper_id':'paper-a','source_file':'paper.pdf','sha256':file_sha}],
        'operator_maintenance':{'owner_id':'owner-a'}}
    return {'questions':[q],'papers':[{'id':'paper-a'}]},manifest


@pytest.mark.parametrize('source',['official','key','derived'])
def test_publisher_explanation_changes_only_explanation_and_preserves_provenance(tmp_path,source):
    bank,manifest=_publisher_packet(tmp_path,source)
    output,_=batch.prepare(bank,[{'id':manifest['id'],'manifest':manifest,'manifest_hash':digest(manifest)}],'a'*64,tmp_path)
    changed=output['questions'][0]
    assert changed['explanation']==EXPLANATION
    assert (changed['answerIndex'],changed['answerSource'],changed['answerKeyRef'])==(1,source,None)


@pytest.mark.parametrize('mutate',['missing-owner','answer-field','blank','missing-evidence','flagged','bad-options','changed-answer','missing-figure'])
def test_publisher_independently_rejects_invalid_explanation_maintenance(tmp_path,mutate):
    bank,manifest=_publisher_packet(tmp_path)
    q=bank['questions'][0]
    if mutate=='missing-owner':manifest['operator_maintenance']['owner_id']='someone-else'
    elif mutate=='answer-field':manifest['payload']['patch']={'explanation':EXPLANATION,'answerIndex':2}
    elif mutate=='blank':manifest['payload']['patch']={'explanation':'  '}
    elif mutate=='missing-evidence':manifest['payload']['evidence']=[]
    elif mutate=='flagged':manifest['baseline']['metadata']['sourceDefect']='duplicate-options'
    elif mutate=='bad-options':q['options']=['same','same'];manifest['baseline']['record']=batch.record(q)
    elif mutate=='changed-answer':q['answerIndex']=2
    elif mutate=='missing-figure':q['hasDiagram']=True;manifest['baseline']['record']=batch.record(q)
    with pytest.raises(ValueError):batch.prepare(bank,[{'id':manifest['id'],'manifest':manifest,'manifest_hash':digest(manifest)}],'a'*64,tmp_path)

@pytest.mark.parametrize('still_eligible',[True,False])
def test_publisher_rechecks_live_explanation_targets_after_export(monkeypatch,still_eligible):
    pubs=[{'state':'exported','manifest':{'payload':{'kind':'explanation','canonical_id':'cq-a'}}}]
    queries=[]
    def remote(query,json_result=False):
        queries.append(query)
        return [{'id':'cq-a'}]if still_eligible else[]
    monkeypatch.setattr(batch.w,'remote',remote)
    if still_eligible:batch.check_live_explanation_targets(pubs)
    else:
        with pytest.raises(ValueError,match='after review'):batch.check_live_explanation_targets(pubs)
    assert "status='live'"in queries[0]and 'NOT key_disputed'in queries[0]
    batch.check_live_explanation_targets([{'state':'applied','manifest':pubs[0]['manifest']}])
    assert len(queries)==1
