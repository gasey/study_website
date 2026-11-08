"""Organisation changes preserve historical content and fail closed for simulation."""
import hashlib
from uuid import uuid4
import pytest
from psycopg.types.json import Jsonb
from test_admin_workbench import workbench

BASE='/api/admin/bank/organization'


def scheme_body(**changes):
    return {'title':'Synthetic legacy scheme','exam_key':'legacy-test','edition':'Historical edition',
      'period':'legacy','state':'draft','source_url':'','source_checked':False,'notes':'Historical source not yet recovered.',
      'papers':[{'key':'paper-1','title':'Paper I','format':'mixed','sections':[]}],**changes}


def save_profile(client,h,paper,profile):
    current=client.get(BASE+'/paper',params={'paper_id':paper})
    assert current.status_code==200,current.text
    data=current.json()
    return client.post(BASE+'/paper',headers=h,json={'paper_id':paper,'expected_version':data['saved']['version'] if data['saved'] else 0,
      'expected_context':data['context'],'profile':profile,'reason':'Inspected the synthetic source and its exact historical applicability.'})


def test_legacy_scheme_unknown_values_and_immutable_revisions(client,actor,database):
    h=actor('owner');sid='legacy-'+uuid4().hex
    body={'scheme_id':sid,'expected_revision':0,'scheme':scheme_body(),'reason':'Keep unknown historical rules unset until the original notice is inspected.'}
    r=client.post(BASE+'/schemes',headers=h,json=body);assert r.status_code==200,r.text
    assert r.json()['revision']==1
    assert client.post(BASE+'/schemes',headers=h,json=body).status_code==409
    body['expected_revision']=1;body['scheme']['title']='Updated legacy scheme draft'
    assert client.post(BASE+'/schemes',headers=h,json=body).json()['revision']==2
    editions=[r for r in client.get(BASE+'/schemes').json()['items'] if r['scheme_id']==sid]
    assert [r['revision'] for r in editions]==[2,1]
    assert all(r['payload']['papers'][0]['duration_minutes'] is None for r in editions)
    body['expected_revision']=2;body['scheme']['state']='verified'
    assert client.post(BASE+'/schemes',headers=h,json=body).status_code==422
    body['scheme']['state']='draft'
    actor('reviewer1');assert client.post(BASE+'/schemes',headers=actor('reviewer1'),json=body).status_code==403
    actor('outsider');assert client.get(BASE+'/schemes').status_code==403
    assert database[1].execute('SELECT count(*) FROM bank_scheme_revisions WHERE scheme_id=%s',(sid,)).fetchone()[0]==2


def test_source_provider_scope_legacy_filter_and_stale_profile(client,actor,workbench,database):
    ids,paper,_=workbench;h=actor('owner');pid='book-'+uuid4().hex
    r=client.post(BASE+'/providers',headers=h,json={'id':pid,'label':'Synthetic book source','kind':'book','url':'https://example.test/source','reason':'Register an independently identified synthetic source publication.'})
    assert r.status_code==200,r.text
    profile={'provider_id':pid,'corpus':'Legacy book edition','period':'legacy','source_checked':False}
    r=save_profile(client,h,paper,profile);assert r.status_code==200,r.text
    rows=client.get('/api/admin/bank/tag-issues',params={'bank':pid,'period':'legacy','paper':paper,'issue':'all'}).json()
    assert rows['total']==8 and all(q['bank']==pid for q in rows['items'])
    assert client.get('/api/admin/bank/tag-issues',params={'bank':'mpsc','paper':paper,'issue':'all'}).json()['total']==0
    assert client.get('/api/admin/bank/tag-sources',params={'bank':pid}).json()['items'][0]['id']==paper
    current=client.get(BASE+'/paper',params={'paper_id':paper}).json()
    assert not current['readiness']['full_simulation_ready'] and current['readiness']['scheme'] is None
    database[1].execute('UPDATE appearances SET page=7 WHERE paper_id=%s',(paper,))
    r=client.post(BASE+'/paper',headers=h,json={'paper_id':paper,'expected_version':1,'expected_context':current['context'],'profile':profile,'reason':'A stale layout must not be recorded as freshly inspected source evidence.'})
    assert r.status_code==409,r.text
    assert not client.get(BASE+'/paper',params={'paper_id':paper}).json()['readiness']['context_current']


def test_topic_related_subtopic_filters_and_broad_resolution(client,actor,workbench,database):
    ids,paper,_=workbench;conn=database[1];h=actor('owner');qid=ids['unverified'];aid='app-'+qid
    conn.execute("INSERT INTO review_taxonomy(id,label,parent_id,level,version) VALUES('english/org-topic','Test topic','english','topic','test'),('english/org-topic/sub','Test subtopic','english/org-topic','subtopic','test') ON CONFLICT DO NOTHING")
    conn.execute("INSERT INTO question_topic_links VALUES(%s,'english/org-topic/sub','english','English','english/org-topic','Test topic','english/org-topic/sub','Test subtopic','test','manual','approved','Inspected synthetic related path')",(qid,))
    params={'paper':paper,'issue':'all','topic':'english/org-topic','subtopic':'english/org-topic/sub'}
    assert client.get('/api/admin/bank/tag-issues',params=params).json()['total']==0
    related=client.get('/api/admin/bank/tag-issues',params={**params,'path':'related'}).json()
    assert [q['id'] for q in related['items']]==[qid]
    current=client.get(BASE+'/questions/'+qid+'/context',params={'appearance_id':aid}).json()
    body={'appearance_id':aid,'source_version':current['source_version'],'expected_version':0,
      'context':{'region':'mizoram','time_behavior':'changes-over-time','reference_period':'2020','reference_basis':'exam-date','broad_subject_intentional':True},
      'reason':'Inspected the wording; the broad subject is intentional for this source item.'}
    r=client.post(BASE+'/questions/'+qid+'/context',headers=h,json=body);assert r.status_code==200,r.text
    assert qid not in {q['id'] for q in client.get('/api/admin/bank/tag-issues',params={'paper':paper,'issue':'no-topic'}).json()['items']}
    assert client.get('/api/admin/bank/tag-issues',params={'paper':paper,'issue':'all','region':'mizoram','time_behavior':'changes-over-time'}).json()['items'][0]['id']==qid
    assert client.post(BASE+'/questions/'+qid+'/context',headers=h,json=body).status_code==409
    # A tag decision reopens coverage; old broad-subject resolution cannot mask it.
    conn.execute("UPDATE question_classifications SET subject_id='mizo' WHERE question_id=%s",(qid,))
    assert qid in {q['id'] for q in client.get('/api/admin/bank/tag-issues',params={'paper':paper,'issue':'no-topic'}).json()['items']}
    assert not client.get(BASE+'/questions/'+qid+'/context',params={'appearance_id':aid}).json()['current']


def test_saved_work_views_are_account_scoped_and_reject_external_routes(client,actor):
    h=actor('owner');name='Legacy cleanup '+uuid4().hex
    body={'title':name,'expected_version':0,'filters':{'tag_issue':'no-topic','tag_period':'legacy','tag_offset':'40','tag_selected':'cq_test'}}
    r=client.post(BASE+'/views',headers=h,json=body);assert r.status_code==200,r.text
    vid=r.json()['id'];saved=next(v for v in client.get(BASE+'/views').json() if v['id']==vid)
    assert saved['filters']==body['filters']
    bad={**body,'filters':{'redirect':'https://example.test'}}
    assert client.post(BASE+'/views',headers=h,json=bad).status_code==422
    actor('reviewer1');assert not any(v['id']==vid for v in client.get(BASE+'/views').json())
    assert client.post(BASE+'/views',headers=actor('reviewer1'),json={**body,'id':vid,'expected_version':1}).status_code==404


def test_repeat_review_preserves_ids_answers_and_rejects_stale_sources(client,actor,workbench,database):
    ids,paper,_=workbench;conn=database[1];h=actor('owner');qids=sorted([ids['missing'],ids['unverified']])
    conn.execute("UPDATE canonical_questions SET stem_norm='a sufficiently long synthetic repeated question about an institution' WHERE id=ANY(%s)",(qids,))
    before=conn.execute('SELECT id,answer_text,answer_source,status FROM canonical_questions WHERE id=ANY(%s) ORDER BY id',(qids,)).fetchall()
    result=client.get(BASE+'/questions/'+qids[0]+'/repeats');assert result.status_code==200,result.text
    assert qids[1] in {q['id'] for q in result.json()['candidates']}
    snapshots=[client.get('/api/review/questions/'+q,params={'appearance_id':'app-'+q}).json() for q in qids]
    body={'left_id':qids[0],'right_id':qids[1],'left_appearance':snapshots[0]['record']['id'],'right_appearance':snapshots[1]['record']['id'],
      'left_version':snapshots[0]['baseline_token'],'right_version':snapshots[1]['baseline_token'],'expected_revision':0,
      'relation':'same-concept','reason':'The compared sources test a shared concept but need separate answer evidence.'}
    r=client.post(BASE+'/repeats',headers=h,json=body);assert r.status_code==200,r.text
    assert r.json()['content_changed'] is False
    assert conn.execute('SELECT id,answer_text,answer_source,status FROM canonical_questions WHERE id=ANY(%s) ORDER BY id',(qids,)).fetchall()==before
    conn.execute('UPDATE appearances SET page=8 WHERE id=%s',(body['right_appearance'],))
    assert client.post(BASE+'/repeats',headers=h,json={**body,'expected_revision':1}).status_code==409
    assert client.get(BASE+'/questions/'+qids[0]+'/repeats').json()['relations'][0]['current'] is False


def test_reviewed_repeats_share_practice_slot_only_with_fresh_matching_answers(client,actor,workbench,database):
    import asyncio
    import psycopg
    from psycopg.rows import dict_row
    from app.services.repeat_selection import distinct_candidates
    ids,_,_=workbench;conn=database[1];qids=sorted([ids['keyed'],ids['unverified']]);h=actor('owner')
    snapshots=[client.get('/api/review/questions/'+q,params={'appearance_id':'app-'+q}).json() for q in qids]
    body={'left_id':qids[0],'right_id':qids[1],'left_appearance':snapshots[0]['record']['id'],'right_appearance':snapshots[1]['record']['id'],
      'left_version':snapshots[0]['baseline_token'],'right_version':snapshots[1]['baseline_token'],'expected_revision':0,
      'relation':'same-question','reason':'Inspected these synthetic sources, equivalent options and matching answer text.'}
    assert client.post(BASE+'/repeats',headers=h,json=body).status_code==200
    async def selected():
        async with await psycopg.AsyncConnection.connect('dbname='+database[0],row_factory=dict_row) as db:
            async with db.cursor() as cur:return await distinct_candidates(cur,qids)
    result=asyncio.run(selected())
    assert result==[ids['keyed']]  # Prefer the eligible official source without changing either key.
    assert conn.execute('SELECT count(*) FROM canonical_questions WHERE id=ANY(%s)',(qids,)).fetchone()[0]==2
    conn.execute('UPDATE appearances SET page=9 WHERE id=%s',(body['right_appearance'],))
    assert asyncio.run(selected())==qids


def test_official_templates_are_drafts_and_keep_independent_editions(client,actor):
    actor('owner');templates=client.get(BASE+'/schemes').json()['templates']
    assert {'legacy-custom','mcs-prelims-2025','group-b-ng-2026','group-b-gazetted-2025'}<={t['id'] for t in templates}
    assert all(t['scheme']['state']=='draft' and not t['scheme']['source_checked'] for t in templates)


def test_assistant_udc_template_keeps_combined_mixed_paper_and_separate_scheme(client,actor):
    from app.services.bank_organization import Scheme
    actor('owner');templates=client.get(BASE+'/schemes').json()['templates']
    template=next(t for t in templates if t['id']=='assistant-udc-combined-2026')
    scheme=Scheme.model_validate(template['scheme'])
    assert scheme.exam_key=='assistant-udc-combined' and scheme.state=='draft' and not scheme.source_checked
    p1,p2=scheme.papers
    assert p1.format=='mixed' and p1.questions is None and p1.marks==200 and p1.duration_minutes==180
    assert sum(s.marks for s in p1.sections)==200
    assert [(s.key,s.questions) for s in p1.sections if s.format=='mcq']==[('gk',50),('english',25)]
    assert {s.key for s in p1.sections if s.format=='written'}=={'precis','essay','comprehension'}
    assert p2.questions==100 and sum(s.questions for s in p2.sections)==100
    assert sum(s.marks for s in p2.sections)==200
    assert scheme.effective_from is None and scheme.effective_to is None


def test_original_paper_counts_printed_appearances_instead_of_collapsing_repeats(client,actor,workbench,database):
    ids,paper,_=workbench;conn=database[1];qid=ids['keyed'];aid='org-repeat-'+uuid4().hex
    conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary,qnum,page) VALUES(%s,%s,'mcq','Synthetic repeat in the same original',%s,1,'official',%s,false,'99',2)",(aid,paper,Jsonb(['A','B','C','D']),qid))
    conn.execute("INSERT INTO collection_papers(collection_id,version,paper_id,section_path,as_mock) VALUES('ldc',1,%s,'papers',false)",(paper,))
    r=client.get('/api/collections/ldc/paper-questions',params={'paper_id':paper,'limit':100})
    assert r.status_code==200,r.text
    assert r.json()['total']==len(r.json()['items'])==9
    assert len([q for q in r.json()['items'] if q['id']==qid])==2
    actor('owner');r=client.get(BASE+'/paper',params={'paper_id':paper})
    assert any('Repeated identities' in b for b in r.json()['readiness']['blockers'])


def test_full_simulation_requires_complete_source_and_uses_pinned_rules(client,actor,database):
    conn=database[1];suffix=uuid4().hex;pid='org-paper-'+suffix;sid='org-scheme-'+suffix
    h=actor('owner')
    conn.execute("INSERT INTO papers(id,exam_type,exam_name,source_file,year,exam_scope_id) VALUES(%s,'Direct','Synthetic complete original','Old_Questions/test.pdf',2017,'mizoram-recruitment')",(pid,))
    ids=[];appearances=[]
    for i in range(2):
        q='org-question-'+suffix+str(i);a='org-appearance-'+suffix+str(i);ids.append(q);appearances.append(a)
        opts=['Alpha option','Beta option','Gamma option','Delta option'];stem='A complete synthetic source question number '+str(i)
        conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source,status) VALUES(%s,'mcq',%s,%s,%s,'official','live')",(q,stem,Jsonb(opts),opts[1]))
        conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary,qnum,qnum_seq,page,option_order) VALUES(%s,%s,'mcq',%s,%s,1,'official',%s,true,%s,%s,1,%s)",(a,pid,stem,Jsonb(opts),q,str(i+1),i+1,[0,1,2,3]))
    conn.execute("INSERT INTO collection_papers(collection_id,version,paper_id,section_path,as_mock) VALUES('ldc',1,%s,'papers',true)",(pid,))
    initial=client.get('/api/collections/ldc/paper-readiness',params={'paper_id':pid});assert initial.status_code==200,initial.text
    assert not initial.json()['full_simulation_ready']
    spec=scheme_body(state='verified',source_url='https://example.test/legacy.pdf',source_sha256='a'*64,evidence_page=1,source_checked=True,
      papers=[{'key':'paper-1','title':'Historical MCQ paper','format':'mcq','questions':2,'marks':4,'duration_minutes':90,'negative_fraction':1/3,'sections':[]}])
    r=client.post(BASE+'/schemes',headers=h,json={'scheme_id':sid,'expected_revision':0,'scheme':spec,'reason':'Synthetic exact historical scheme inspected in the disposable test only.'});assert r.status_code==200,r.text
    profile={'provider_id':'mpsc','period':'legacy','scheme_id':sid,'scheme_revision':1,'scheme_paper_key':'paper-1','expected_questions':2,'appearance_order':list(reversed(appearances)),'source_checked':True}
    r=save_profile(client,h,pid,profile);assert r.status_code==200,r.text
    assert r.json()['readiness']['full_simulation_ready'],r.json()['readiness']['blockers']
    user='org-user-'+suffix;token='test-session-'+user
    conn.execute("INSERT INTO users(id,handle,email,role) VALUES(%s,%s,%s,'learner')",(user,user,user+'@example.test'))
    conn.execute("INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES(%s,%s,now()+interval '1 day')",(hashlib.sha256(token.encode()).hexdigest(),user))
    mh=actor(user)
    r=client.post('/api/mocks',headers=mh,json={'collection_id':'ldc','paper_id':pid,'paper_mode':'full','count':1,'marks_correct':9,'duration_minutes':10})
    assert r.status_code==200,r.text
    session=r.json();assert session['paper_mode']=='full' and session['duration_seconds']==5400
    assert [q['id'] for q in session['questions']]==list(reversed(ids))
    saved=conn.execute('SELECT marks_correct,marks_wrong,scheme_snapshot FROM mock_sessions WHERE id=%s',(session['id'],)).fetchone()
    assert float(saved[0])==2 and abs(float(saved[1])-2/3)<0.001 and saved[2]['revision']==1
    assert client.get('/api/mocks/current').json()['paper_mode']=='full'
    conn.execute("UPDATE canonical_questions SET status='held' WHERE id=%s",(ids[0],))
    assert not client.get('/api/collections/ldc/paper-readiness',params={'paper_id':pid}).json()['full_simulation_ready']
    assert client.get('/api/collections/ldc/paper-readiness',params={'paper_id':'nonexistent'}).status_code==404
