"""Assigned source access, stale editor protection and attributed human checks."""
from uuid import uuid4
import pytest
from psycopg.types.json import Jsonb
from test_bank_review import proposal

@pytest.fixture
def source(database):
 c=database[1];key=uuid4().hex;pid='editorial-'+key;qid='cq_'+key;aid='app_'+key
 existing=[r[0] for r in c.execute('SELECT id FROM editorial_assignments').fetchall()]
 c.execute("UPDATE editorial_assignments SET state='revoked',version=version+1 WHERE email='outsider@example.test' AND state<>'revoked'")
 c.execute("INSERT INTO papers(id,exam_type,exam_name,source_file,year) VALUES(%s,'Direct','Synthetic assigned UDC','Old_Questions/test.pdf',2026)",(pid,))
 c.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES(%s,'mcq','Synthetic assigned question',%s,'B','derived')",(qid,Jsonb(['A','B','C','D'])))
 c.execute("INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary,qnum,page) VALUES(%s,%s,'mcq','Synthetic assigned question',%s,1,'derived',%s,true,'1',1)",(aid,pid,Jsonb(['A','B','C','D']),qid))
 c.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,taxonomy_version,source,review_status) VALUES(%s,'english','English','test','manual','approved')",(qid,))
 v=c.execute("SELECT live_version FROM collections WHERE id='udc'").fetchone()[0]
 c.execute("INSERT INTO collection_papers(collection_id,version,paper_id,section_path) VALUES('udc',%s,%s,'papers')",(v,pid))
 try:yield pid,qid,aid
 finally:
  # Keep independent API suites isolated when they share this disposable DB.
  c.execute("UPDATE editorial_assignments SET state='revoked',version=version+1 WHERE email='outsider@example.test' AND state<>'revoked' AND NOT(id=ANY(%s))",(existing,))

def invite(client,actor):
 h=actor('owner');r=client.post('/api/editorial/assignments',headers=h,json={'email':'outsider@example.test','collection_id':'udc','reason':'Owner assigns this synthetic UDC source to a trusted editor.'});assert r.status_code==201,r.text
 return r.json(),h

def active(client,actor):
 a,h=invite(client,actor)
 r=client.post('/api/editorial/assignments/'+a['id']+'/activate',headers=h,json={'expected_version':a['version'],'reason':'Owner confirms the synthetic account and its exact source scope.'});assert r.status_code==200,r.text
 return r.json()

def test_pending_invite_does_not_grant_source_or_admin(client,actor,source):
 a,_=invite(client,actor);actor('outsider')
 mine=client.get('/api/editorial/assignments');assert mine.status_code==200
 assert next(x for x in mine.json()['items'] if x['id']==a['id'])['state']=='pending'
 assert client.get('/api/editorial/assignments/'+a['id']+'/papers').status_code==404
 assert client.get('/api/admin/bank/summary').status_code==403
 snap=client.get('/api/review/questions/'+source[1]+'?appearance_id='+source[2]).json()
 assert snap['record']['answerIndex'] is None
 assert len(snap['baseline_token'])==64
 assert mine.headers['cache-control']=='private, no-store'

def test_active_editor_gets_only_assigned_sources_no_publisher(client,actor,source):
 a=active(client,actor);h=actor('outsider')
 papers=client.get('/api/editorial/assignments/'+a['id']+'/papers');assert papers.status_code==200
 assert source[0] in {p['id'] for p in papers.json()['items']}
 assert client.get('/api/editorial/assignments/'+a['id']+'/questions',params={'paper':'paper-test'}).status_code==404
 assert client.get('/api/editorial/assignments/'+a['id']+'/questions',params={'paper':source[0]}).status_code==200
 snap=client.get('/api/review/questions/'+source[1]+'?appearance_id='+source[2]).json()
 assert snap['record']['answerIndex']==1
 assert client.get('/api/admin/bank/summary').status_code==403
 assert client.post('/api/editorial/assignments',headers=h,json={'email':'reviewer1@example.test','collection_id':'udc','reason':'This must not create a new source assignment.'}).status_code==403
 actor('reviewer1')
 assert client.get('/api/editorial/assignments/'+a['id']+'/papers').status_code==404

def test_protected_public_proposal_needs_fresh_source_version(client,actor,source,database):
 active(client,actor);h=actor('outsider');pid,qid,aid=source
 p=proposal();p.update(canonical_id=qid,appearance_id=aid)
 h['Idempotency-Key']=uuid4().hex
 assert client.post('/api/contributions',headers=h,json=p).status_code==428
 snap=client.get('/api/review/questions/'+qid,params={'appearance_id':aid}).json()
 h['X-Review-Source-Version']=snap['baseline_token']
 database[1].execute("UPDATE appearances SET question='The source has been corrected by a human' WHERE id=%s",(aid,))
 assert client.post('/api/contributions',headers=h,json=p).status_code==409
 current=client.get('/api/review/questions/'+qid,params={'appearance_id':aid}).json()
 h['X-Review-Source-Version']=current['baseline_token']
 r=client.post('/api/contributions',headers=h,json=p);assert r.status_code==201,r.text
 assert r.json()['state']=='draft'
 database[1].execute("UPDATE canonical_questions SET answer_text='D' WHERE id=%s",(qid,))
 # An identical successful request replays instead of creating a second draft.
 assert client.post('/api/contributions',headers=h,json=p).json()['id']==r.json()['id']

def test_checks_are_attributed_immutable_and_do_not_verify_answer(client,actor,source,database):
 a=active(client,actor);h=actor('outsider');pid,qid,aid=source
 token=client.get('/api/review/questions/'+qid,params={'appearance_id':aid}).json()['baseline_token']
 payload={'appearance_id':aid,'source_version':token,'outcome':'checked','source_checked':True,'options_checked':True,'answer_checked':True,'explanation_checked':False,'note':'Synthetic human source comparison.'}
 url='/api/editorial/assignments/'+a['id']+'/checks'
 assert client.post(url,headers=h,json=payload).status_code==422
 payload['explanation_checked']=True
 before=database[1].execute('SELECT answer_source,answer_text FROM canonical_questions WHERE id=%s',(qid,)).fetchone()
 result=client.post(url,headers=h,json=payload);assert result.status_code==200,result.text
 row=database[1].execute('SELECT reviewer_id,outcome FROM editorial_checks WHERE id=%s',(result.json()['id'],)).fetchone();assert row==('outsider','checked')
 assert database[1].execute('SELECT answer_source,answer_text FROM canonical_questions WHERE id=%s',(qid,)).fetchone()==before
 with pytest.raises(Exception,match='append-only'):database[1].execute('UPDATE editorial_checks SET outcome=outcome WHERE id=%s',(result.json()['id'],))
 database[1].execute("UPDATE canonical_questions SET question='Changed while reviewer was reading' WHERE id=%s",(qid,))
 assert client.post(url,headers=h,json=payload).status_code==409

def test_revoked_assignment_and_email_change_remove_source_privilege(client,actor,source,database):
 a=active(client,actor);h=actor('owner')
 r=client.post('/api/editorial/assignments/'+a['id']+'/revoke',headers=h,json={'expected_version':a['version'],'reason':'Owner ends this synthetic paper-review assignment.'});assert r.status_code==200
 actor('outsider');assert client.get('/api/editorial/assignments/'+a['id']+'/papers').status_code==404
 assert client.get('/api/review/questions/'+source[1],params={'appearance_id':source[2]}).json()['record']['answerIndex'] is None

def test_missing_account_cannot_be_silently_activated(client,actor,source):
 h=actor('owner');r=client.post('/api/editorial/assignments',headers=h,json={'email':uuid4().hex+'@example.test','collection_id':'combined-prelims','reason':'Reserve a future human reviewer without creating a login.'});assert r.status_code==201
 a=r.json();assert client.post('/api/editorial/assignments/'+a['id']+'/activate',headers=h,json={'expected_version':a['version'],'reason':'Account has not been created and must not be fabricated.'}).status_code==409

def test_paper_progress_counts_latest_checks_and_resumes_across_pages(client,actor,source,database):
 a=active(client,actor);actor('outsider');pid,qid,first=source;c=database[1]
 c.execute('UPDATE appearances SET qnum_seq=1 WHERE id=%s',(first,))
 ids=[first]
 for n in range(2,27):
  appearance=first+'_'+str(n);ids.append(appearance)
  c.execute("INSERT INTO appearances(id,paper_id,type,question,options,canonical_id,qnum,qnum_seq) VALUES(%s,%s,'mcq','Synthetic progress question',%s,%s,%s,%s)",(appearance,pid,Jsonb(['A','B']),qid,str(n),n))
 def record(appearance,outcome):
  token=client.get('/api/review/questions/'+qid,params={'appearance_id':appearance}).json()['baseline_token']
  c.execute('INSERT INTO editorial_checks(assignment_id,appearance_id,canonical_id,reviewer_id,source_version,outcome,checklist,note) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',(a['id'],appearance,qid,'outsider',token,outcome,Jsonb({k:True for k in ('source_checked','options_checked','answer_checked','explanation_checked')}),'Synthetic progress fixture only.'))
 def paper():
  r=client.get('/api/editorial/assignments/'+a['id']+'/papers');assert r.status_code==200,r.text
  return next(p for p in r.json()['items'] if p['id']==pid)
 initial=paper();assert initial['questions']==26 and initial['recorded']==0
 assert initial['resume']['appearance']==first and initial['resume']['offset']==0
 for appearance in ids[:25]:record(appearance,'checked')
 record(first,'needs_correction')  # Rechecking must replace its count, not add one.
 p=paper();assert (p['recorded'],p['checked'],p['flagged'])==(25,24,1)
 assert p['resume']['appearance']==ids[25] and p['resume']['offset']==25
 record(ids[25],'cannot_verify')
 p=paper();assert (p['recorded'],p['checked'],p['flagged'])==(26,24,2)
 assert p['resume']['appearance']==first
 # Historical checks stay recorded after source edits, not advertised as fresh verification.
 c.execute("UPDATE appearances SET question='Changed source' WHERE id=%s",(first,))
 assert paper()['recorded']==26
 actor('reviewer1');assert client.get('/api/editorial/assignments/'+a['id']+'/papers').status_code==404

def save_source_check(client,actor,assignment,source,outcome='checked'):
 h=actor('outsider');token=client.get('/api/review/questions/'+source[1],params={'appearance_id':source[2]}).json()['baseline_token']
 r=client.post('/api/editorial/assignments/'+assignment['id']+'/checks',headers=h,json={'appearance_id':source[2],'source_version':token,'outcome':outcome,'source_checked':True,'options_checked':True,'answer_checked':True,'explanation_checked':True,'note':'Synthetic reviewer compared this exact source version.'})
 assert r.status_code==200,r.text
 return token

@pytest.mark.parametrize('change',[
 "UPDATE canonical_questions SET explanation='Changed explanation' WHERE id=%s",
 "UPDATE appearances SET question='Changed printed prompt' WHERE canonical_id=%s",
 "UPDATE papers SET exam_name='Changed paper identity' WHERE id=(SELECT paper_id FROM appearances WHERE canonical_id=%s LIMIT 1)",
 "UPDATE question_classifications SET review_status='pending' WHERE question_id=%s",
 "INSERT INTO question_topic_links(question_id,path_id,subject_id,subject_label,taxonomy_version,source,review_status,evidence) VALUES(%s,'mizo','mizo','Mizo','test','manual','approved','Synthetic source evidence')",
])
def test_changed_sources_require_recheck_without_erasing_history(client,actor,source,database,change):
 a=active(client,actor);save_source_check(client,actor,a,source)
 url='/api/editorial/assignments/'+a['id']
 current=next(p for p in client.get(url+'/papers').json()['items'] if p['id']==source[0])
 assert (current['checked'],current['recheck'])==(1,0)
 database[1].execute(change,(source[1],))
 changed=next(p for p in client.get(url+'/papers').json()['items'] if p['id']==source[0])
 assert (changed['recorded'],changed['checked'],changed['recheck'])==(1,0,1)
 assert changed['resume']['reason']=='recheck'
 q=client.get(url+'/questions',params={'paper':source[0]}).json()['items'][0]
 assert q['previous_check']['stale'] is True and q['previous_check']['outcome']=='checked'
 save_source_check(client,actor,a,source)
 checked=next(p for p in client.get(url+'/papers').json()['items'] if p['id']==source[0])
 assert (checked['recorded'],checked['checked'],checked['recheck'])==(1,1,0)


def test_future_module_expansion_is_explicit_versioned_and_preserves_checks(client,actor,source,database):
 c=database[1];cid='future-'+uuid4().hex
 c.execute("INSERT INTO collections(id,title,kind,live_version) VALUES(%s,'Future subject module','practice',1)",(cid,))
 c.execute("INSERT INTO collection_papers(collection_id,version,paper_id,section_path) VALUES(%s,1,%s,'papers')",(cid,source[0]))
 h=actor('owner');r=client.post('/api/editorial/assignments',headers=h,json={'email':'outsider@example.test','collection_id':cid,'reason':'Synthetic future module assignment with exact registered sources.'});assert r.status_code==201,r.text
 a=r.json();a=client.post('/api/editorial/assignments/'+a['id']+'/activate',headers=h,json={'expected_version':a['version'],'reason':'Confirm synthetic future module reviewer identity.'}).json()
 save_source_check(client,actor,a,source)
 new='future-paper-'+uuid4().hex;c.execute("INSERT INTO papers(id,exam_type,exam_name) VALUES(%s,'Direct','Future source paper')",(new,))
 c.execute("INSERT INTO collection_papers(collection_id,version,paper_id,section_path) VALUES(%s,1,%s,'papers')",(cid,new))
 url='/api/editorial/assignments/'+a['id']
 assert new not in {p['id'] for p in client.get(url+'/papers').json()['items']}
 assert client.get(url+'/available-papers').status_code==403
 h=actor('owner');available=client.get(url+'/available-papers').json();assert [p['id'] for p in available['items']]==[new]
 payload={'expected_version':a['version'],'paper_ids':[new],'reason':'Explicitly add the newly registered module paper.'}
 assert client.post(url+'/add-papers',headers=h,json={**payload,'expected_version':999}).status_code==409
 assert client.post(url+'/add-papers',headers=h,json={**payload,'paper_ids':['paper-test']}).status_code==422
 assert client.post(url+'/add-papers',headers=h,json=payload).status_code==200
 assert client.post(url+'/add-papers',headers=h,json=payload).status_code==409
 actor('outsider');papers=client.get(url+'/papers').json()['items'];assert new in {p['id'] for p in papers}
 assert next(p for p in papers if p['id']==source[0])['checked']==1
 assert c.execute("SELECT count(*) FROM contribution_events WHERE action='editorial_scope_expanded' AND detail->>'assignment'=%s",(a['id'],)).fetchone()[0]==1


def test_individual_website_papers_and_catalog_keep_exact_scope(client,actor,source,database):
 c=database[1];pid='website-'+uuid4().hex;c.execute("INSERT INTO papers(id,exam_type,exam_name) VALUES(%s,'Community','Synthetic Website question set')",(pid,))
 h=actor('owner');before=c.execute('SELECT count(*) FROM canonical_questions').fetchone()[0]
 assert client.get('/api/editorial/catalog',params={'kind':'papers','search':pid}).json()['items'][0]['bank']=='website'
 payload={'email':'outsider@example.test','paper_ids':[pid,source[0]],'title':'Mixed source review','reason':'Owner selects two exact registered sources for synthetic review.'}
 a=client.post('/api/editorial/assignments',headers=h,json=payload);assert a.status_code==201,a.text;a=a.json()
 # Reordered identical scope is the same reservation, not a second assignment.
 assert client.post('/api/editorial/assignments',headers=h,json={**payload,'paper_ids':list(reversed(payload['paper_ids']))}).json()['id']==a['id']
 assert client.post('/api/editorial/assignments',headers=h,json={**payload,'collection_id':'udc'}).status_code==422
 assert client.post('/api/editorial/assignments',headers=h,json={**payload,'title':'   '}).status_code==422
 r=client.post('/api/editorial/assignments/'+a['id']+'/activate',headers=h,json={'expected_version':a['version'],'reason':'Confirm synthetic account before activating exact paper access.'});assert r.status_code==200,r.text
 actor('outsider');papers=client.get('/api/editorial/assignments/'+a['id']+'/papers').json()['items'];assert {p['id'] for p in papers}=={pid,source[0]}
 assert next(p for p in papers if p['id']==pid)['bank']=='website'
 assert client.get('/api/editorial/catalog').status_code==403
 assert client.get('/api/editorial/assignments/'+a['id']+'/questions',params={'paper':'paper-test'}).status_code==404
 assert c.execute('SELECT count(*) FROM canonical_questions').fetchone()[0]==before


def test_context_shows_shared_work_without_private_draft_leak_or_answer_gate_bypass(client,actor,source,database):
 a=active(client,actor);h=actor('outsider');c=database[1];url='/api/editorial/assignments/'+a['id']
 own='own-'+uuid4().hex;other='other-'+uuid4().hex;submitted='submitted-'+uuid4().hex
 for cid,author,state in [(own,'outsider','draft'),(other,'author','draft'),(submitted,'author','submitted')]:
  c.execute('INSERT INTO bank_contributions(id,author_id,canonical_id,appearance_id,kind,subject_id,title,idempotency_key,request_hash,state) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(cid,author,source[1],source[2],'explanation','english','Private synthetic title',uuid4().hex,'a'*64,state))
 ctx=client.get(url+'/context',params={'appearance':source[2]});assert ctx.status_code==200,ctx.text;ctx=ctx.json()
 assert [p['id'] for p in ctx['mine']]==[own]
 assert ctx['corrections']==[{'state':'submitted','count':1}]
 assert other not in str(ctx) and submitted not in str(ctx) and 'Private synthetic title' not in str(ctx)
 assert ctx['modules'] and ctx['reviewers'][0]['handle']=='outsider'
 paper=next(p for p in client.get(url+'/papers').json()['items'] if p['id']==source[0]);assert paper['corrections']=={'pending':1,'published':0,'failed':0}
 mid='context-mock-'+uuid4().hex;c.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,'outsider','ldc',%s,60)",(mid,[source[1]]))
 assert client.get(url+'/context',params={'appearance':source[2]}).status_code==409
 c.execute('DELETE FROM mock_sessions WHERE id=%s',(mid,))
 assert client.get(url+'/context',params={'appearance':'appearance-test'}).status_code==404
 actor('reviewer1');assert client.get(url+'/context',params={'appearance':source[2]}).status_code==404


def test_shared_canonical_edit_marks_each_assigned_appearance_stale(client,actor,source,database):
 a=active(client,actor);c=database[1];second=source[2]+'-second';pid=source[0]+'-second'
 c.execute("INSERT INTO papers(id,exam_type,exam_name) VALUES(%s,'Direct','Other use of shared question')",(pid,))
 c.execute("INSERT INTO appearances(id,paper_id,type,question,options,canonical_id,qnum) VALUES(%s,%s,'mcq','Shared synthetic source',%s,%s,'1')",(second,pid,Jsonb(['A','B']),source[1]))
 c.execute('INSERT INTO editorial_assignment_papers(assignment_id,paper_id) VALUES(%s,%s)',(a['id'],pid))
 save_source_check(client,actor,a,source);save_source_check(client,actor,a,(pid,source[1],second))
 c.execute("UPDATE canonical_questions SET explanation='Shared correction was published' WHERE id=%s",(source[1],))
 rows=client.get('/api/editorial/assignments/'+a['id']+'/papers').json()['items']
 assert all(p['recheck']==1 for p in rows if p['id'] in {source[0],pid})
 ctx=client.get('/api/editorial/assignments/'+a['id']+'/context',params={'appearance':second}).json();assert ctx['shared_papers']==2


def test_future_assigned_sources_require_fresh_correction_tokens(client,actor,source):
 h=actor('owner');a=client.post('/api/editorial/assignments',headers=h,json={'email':'outsider@example.test','paper_ids':['paper-test'],'title':'Other paper review','reason':'Synthetic individual source review outside UDC and Prelims.'}).json()
 client.post('/api/editorial/assignments/'+a['id']+'/activate',headers=h,json={'expected_version':a['version'],'reason':'Confirm individual registered source reviewer.'})
 h=actor('outsider');p=proposal();h['Idempotency-Key']=uuid4().hex
 assert client.post('/api/contributions',headers=h,json=p).status_code==428
 snap=client.get('/api/review/questions/cq_test',params={'appearance_id':'appearance-test'}).json();h['X-Review-Source-Version']=snap['baseline_token']
 r=client.post('/api/contributions',headers=h,json=p);assert r.status_code==201,r.text
