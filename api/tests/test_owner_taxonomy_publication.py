import copy
import hashlib,json
from uuid import uuid4
import pytest
from psycopg.types.json import Jsonb
from review_bank_store import record,digest
from test_owner_batch_source_warnings import packet,batch
from test_learning_workflows import official


def taxonomy_packet(tmp_path,written=False):
    bank,pub=packet(tmp_path,'taxonomy',{'classification':{'subject_id':'english','topic_id':'english/grammar','subtopic_id':None},'relatedClassifications':[]})
    m=pub['manifest'];m['admin_edit']={'kind':'taxonomy','actor_id':'synthetic-owner','id':'admin_synthetic'}
    m['taxonomy']=[{'id':'english','parent_id':None,'level':'subject','version':'test'},
                   {'id':'english/grammar','parent_id':'english','level':'topic','version':'test'}]
    if written:
        bank['questions'][0].update(type='descriptive',options=[],answerIndex=None)
        m['baseline']['record']=record(bank['questions'][0])
    return bank,pub


@pytest.mark.parametrize('written',[False,True])
def test_owner_taxonomy_batch_preserves_answers_and_written_type(tmp_path,written):
    bank,pub=taxonomy_packet(tmp_path,written);m=pub['manifest'];pub['manifest_hash']=digest(m)
    before=copy.deepcopy(bank['questions'][0]);out,journal=batch.prepare(bank,[pub],'a'*64,tmp_path)
    after=out['questions'][0]
    assert record(after)['classification']['topic_id']=='english/grammar'
    for key in ('question','options','answerIndex','answerSource','type'):
        assert after[key]==before[key]
    assert len(journal['receipts'])==1


@pytest.mark.parametrize('defect',['answer-patch','wrong-actor','not-admin','old-bank','old-source','changed-document'])
def test_taxonomy_batch_rejects_invalid_authority_or_source(tmp_path,defect):
    bank,pub=taxonomy_packet(tmp_path);m=pub['manifest']
    if defect=='answer-patch':m['payload']['patch']['answerIndex']=0
    if defect=='wrong-actor':m['admin_edit']['actor_id']='other'
    if defect=='not-admin':m.pop('admin_edit')
    if defect=='old-bank':m['bank_sha256']='b'*64
    if defect=='old-source':bank['questions'][0]['question']='New question'
    if defect=='changed-document':(tmp_path/'source.pdf').write_bytes(b'Changed evidence')
    pub['manifest_hash']=digest(m)
    with pytest.raises(ValueError):batch.prepare(bank,[pub],'a'*64,tmp_path)


def test_tagging_progress_is_source_bound_and_separate_from_editorial_checks(client,actor,database):
    from app.services.taxonomy_review_progress import record as record_progress
    q,a,_=official(database);actor('owner')
    run={'run_id':'synthetic-'+uuid4().hex}
    item={'candidate':{'canonical_id':q,'appearance_id':a},'candidate_file':'synthetic.json','candidate_signature':'a'*64}
    url='/api/admin/bank/retag/progress';before=client.get(url).json()
    async def add():
        from app.db import cursor
        async with cursor()as cur:
            await record_progress(cur,'owner',run,item,'confirmed')
            await record_progress(cur,'owner',run,item,'confirmed')
    client.portal.call(add)
    fresh=client.get(url);assert fresh.status_code==200,fresh.text
    result=fresh.json();assert result['confirmed']==before['confirmed']+1
    assert result['includes_answer_verification'] is False
    assert database[1].execute('SELECT count(*) FROM editorial_checks WHERE appearance_id=%s',(a,)).fetchone()[0]==0
    database[1].execute('UPDATE appearances SET question=question||%s WHERE id=%s',(' changed after tagging review',a))
    changed=client.get(url).json()
    assert changed['confirmed']==before['confirmed']
    assert changed['stale']==before['stale']+1
    assert changed['remaining']==result['remaining']+1
    actor('outsider');assert client.get(url).status_code==403


def test_taxonomy_budget_scope_does_not_change_http_or_normal_staff_limits(client,actor,database):
    from app.services import bank_review as review
    from app.services.review_policy import Proposal
    from fastapi import HTTPException
    q,a,_=official(database);actor('owner');conn=database[1]
    prefix='tax_limit_'+uuid4().hex
    conn.execute("INSERT INTO bank_contributions(id,author_id,canonical_id,appearance_id,kind,subject_id,title,idempotency_key,request_hash) SELECT %s||n::text,'owner',%s,%s,'source_request','english','Synthetic quota fixture',%s||n::text,%s FROM generate_series(0,499)n",(prefix,q,a,prefix,'a'*64))
    p=Proposal(kind='taxonomy',canonical_id=q,appearance_id=a,subject_id='english',title='Synthetic owner taxonomy proposal',patch={'classification':{'subject_id':'english'}},rationale='Owner accepted this saved synthetic taxonomy review.',evidence=[{'kind':'reasoning','note':'Synthetic rationale for quota isolation.'}])
    async def create(scoped):
        from app.db import cursor
        scope=review.owner_maintenance_quota_run.set({'owner_id':'owner','canonical_ids':frozenset([q]),'purpose':'owner-taxonomy-publication','authorization':'Explicit owner authorization for this synthetic bounded taxonomy run.','run_id':'synthetic'}) if scoped else None
        try:
            async with cursor()as cur:return await review.create(cur,'owner',p,uuid4().hex,admin_attestation=True)
        finally:
            if scope is not None:review.owner_maintenance_quota_run.reset(scope)
    try:
        with pytest.raises(HTTPException)as error:client.portal.call(create,False)
        assert error.value.status_code==429
        result=client.portal.call(create,True)
        assert conn.execute('SELECT count(*) FROM contribution_decisions WHERE contribution_id=%s',(result['id'],)).fetchone()[0]==0
    finally:conn.execute('DELETE FROM bank_contributions WHERE id LIKE %s',(prefix+'%',))


def test_composed_taxonomy_groups_have_one_verified_output_and_exact_scope(tmp_path):
    bank,template=taxonomy_packet(tmp_path);original=bank['questions'][0];pubs=[];items=[];questions=[]
    for n in range(101):
        q=copy.deepcopy(original);q['id']='appearance_'+str(n);questions.append(q)
        pub=copy.deepcopy(template);m=pub['manifest'];m['id']=pub['id']='pub_'+str(n)
        m['baseline']['record']=record(q);m['payload']['canonical_id']='canonical_'+str(n)
        m['contribution_id']='con_'+str(n);pub['manifest_hash']=digest(m);pubs.append(pub)
        items.append({'candidate':{'canonical_id':m['payload']['canonical_id']},'source_fingerprint':digest(m['baseline']),
                      'primary':m['payload']['patch']['classification'],'related':[]})
    bank['questions']=questions
    scope={'review_kind':'owner-delegated-ai-taxonomy','authorization':'Owner authorized this exact synthetic taxonomy run.','items':items}
    out,journal=batch.prepare_taxonomy_groups(bank,pubs,'a'*64,tmp_path,scope)
    assert len(journal['receipts'])==101
    assert len({r['output_sha256']for r in journal['receipts']})==1
    assert journal['output_sha256']==hashlib.sha256((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode()).hexdigest()
    assert all(record(q)['classification']['topic_id']=='english/grammar'for q in out['questions'])
    assert all(q['answerIndex']==original['answerIndex']for q in out['questions'])
    changed=copy.deepcopy(scope);changed['items'][0]['primary']['subject_id']='other'
    with pytest.raises(ValueError):batch.prepare_taxonomy_groups(bank,pubs,'a'*64,tmp_path,changed)
    with pytest.raises(ValueError):batch.prepare_taxonomy_groups(bank,pubs,'a'*64,tmp_path,{**scope,'items':items[1:]})
    with pytest.raises(ValueError):batch.prepare_taxonomy_groups(bank,pubs+pubs,'a'*64,tmp_path,scope)


def test_current_affairs_scope_requires_the_historical_period(tmp_path):
    _,pub=taxonomy_packet(tmp_path)
    path={'subject_id':'general-studies','topic_id':'general-studies/current-affairs','subtopic_id':None}
    pub['manifest']['payload']['patch']['classification']=path
    item={'candidate':{'canonical_id':pub['manifest']['payload']['canonical_id']},
          'source_fingerprint':digest(pub['manifest']['baseline']),'primary':path,'related':[]}
    scope={'review_kind':'owner-delegated-ai-taxonomy','authorization':'Owner authorized this exact synthetic taxonomy run.','items':[item]}
    with pytest.raises(ValueError,match='historical reference period'):batch.taxonomy_scope([pub],scope)
    item['candidate']['context_candidate']={'reference_period':'2024','reference_basis':'exam-date'}
    batch.taxonomy_scope([pub],scope)


def test_taxonomy_preserves_legacy_unanswered_representation(tmp_path):
    bank,pub=taxonomy_packet(tmp_path)
    bank['questions'][0]['answerIndex']=-1
    pub['manifest']['baseline']['record']=record(bank['questions'][0])
    pub['manifest_hash']=digest(pub['manifest'])
    out,journal=batch.prepare(bank,[pub],'a'*64,tmp_path)
    assert out['questions'][0]['answerIndex']==-1
    assert journal['receipts'][0]['after']['answerIndex'] is None


@pytest.mark.parametrize('fully_attributed',[False,True])
def test_bulk_run_does_not_use_the_ordinary_edit_allowance(client,actor,database,fully_attributed):
    from app.services import bank_review as review
    from app.services.review_policy import Proposal
    from fastapi import HTTPException
    q,a,_=official(database);actor('owner');conn=database[1];prefix='scope_budget_'+uuid4().hex
    conn.execute("INSERT INTO bank_contributions(id,author_id,canonical_id,appearance_id,kind,subject_id,title,idempotency_key,request_hash) SELECT %s||n::text,'owner',%s,%s,'taxonomy','english','Synthetic operator budget fixture',%s||n::text,%s FROM generate_series(0,499)n",(prefix,q,a,prefix,'a'*64))
    conn.execute("INSERT INTO contribution_events(contribution_id,actor_id,action,detail) SELECT id,'operator:owner-source-maintenance','owner_maintenance_quota_exemption',%s FROM bank_contributions WHERE id LIKE %s",(Jsonb({'owner_id':'owner','run_id':prefix}),prefix+'%'))
    if fully_attributed:
        conn.execute("INSERT INTO contribution_events(contribution_id,actor_id,action,detail) SELECT id,'operator:owner-source-maintenance','operator_taxonomy_authorization',%s FROM bank_contributions WHERE id LIKE %s",(Jsonb({'owner_id':'owner','run_id':prefix}),prefix+'%'))
    p=Proposal(kind='taxonomy',canonical_id=q,appearance_id=a,subject_id='english',title='Synthetic normal owner edit',patch={'classification':{'subject_id':'english'}},rationale='A normal edit after the explicitly scoped operator run.',evidence=[{'kind':'reasoning','note':'Synthetic taxonomy rationale for a disposable database.'}])
    async def create():
        from app.db import cursor
        async with cursor()as cur:return await review.create(cur,'owner',p,uuid4().hex,admin_attestation=True)
    try:
        if fully_attributed:assert client.portal.call(create)['id']
        else:
            with pytest.raises(HTTPException)as error:client.portal.call(create)
            assert error.value.status_code==429
    finally:
        # Immutable operator events intentionally prevent deleting their parent
        # contribution. Age only these disposable quota fixtures out instead.
        conn.execute("UPDATE bank_contributions SET created_at=now()-interval '2 days' WHERE id LIKE %s",(prefix+'%',))
