"""Run a disposable local UI fixture; Ctrl-C drops its database."""
from pathlib import Path
import sys
import os
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest
import uvicorn
from fastapi.responses import Response
research_demo=None

databases=conftest.database.__wrapped__();database=next(databases)
clients=conftest.client.__wrapped__(database);fixture_client=next(clients)
if os.environ.get('ISM_REASSESSMENT_DEMO')=='1':
    from test_scoring_revisions import start_and_finish
    actor=conftest.actor.__wrapped__(fixture_client)
    qid,cid,mid,headers,result=start_and_finish(fixture_client,actor,database)
    database[1].execute("UPDATE canonical_questions SET answer_text='C' WHERE id=%s",(qid,))
    print('Synthetic reassessment demo: http://127.0.0.1:5189/results/'+mid,flush=True)
if os.environ.get('ISM_REPAIR_DEMO')=='1':
    from test_admin_workbench import workbench
    actor=conftest.actor.__wrapped__(fixture_client)
    ids,paper,alt=workbench.__wrapped__(fixture_client,actor,database)
    print('Synthetic repair demo: http://127.0.0.1:5189/admin/bank?tab=questions&paper='+paper+'&question='+ids['missing'],flush=True)
if os.environ.get('ISM_REWARDS_DEMO')=='1':
    from test_scoring_revisions import start_and_finish
    actor=conftest.actor.__wrapped__(fixture_client)
    qid,cid,mid,headers,result=start_and_finish(fixture_client,actor,database)
    database[1].execute("INSERT INTO reward_profiles(user_id,board_public) VALUES('owner',true) ON CONFLICT(user_id) DO UPDATE SET board_public=true")
    conn=database[1]
    conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) SELECT 'reward-demo-'||%s||'-'||n,'mcq','Synthetic verified practice question '||n,'[\"A\",\"B\",\"C\",\"D\"]'::jsonb,'B','official' FROM generate_series(1,20) n",(cid,))
    conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary,qnum,page) SELECT 'appearance-'||id,'paper-test',type,question,options,1,'official',id,true,right(id,2),1 FROM canonical_questions WHERE id LIKE %s",('reward-demo-'+cid+'-%',))
    conn.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,taxonomy_version,source,review_status) SELECT id,'english','English','test','manual','approved' FROM canonical_questions WHERE id LIKE %s",('reward-demo-'+cid+'-%',))
    conn.execute("UPDATE collection_sections SET pins=(SELECT array_agg(id ORDER BY id) FROM canonical_questions WHERE id LIKE %s) WHERE collection_id=%s",('reward-demo-'+cid+'-%',cid))
    conn.execute("INSERT INTO collection_papers(collection_id,version,paper_id) VALUES(%s,1,'paper-test')",(cid,))
    conn.execute("UPDATE collections SET title='Synthetic LDC journey' WHERE id=%s",(cid,))
    print('Synthetic exam journey: http://127.0.0.1:5189/exams/'+cid,flush=True)
if os.environ.get('ISM_CREATORS_DEMO')=='1':
    from test_content_studio import publish,document
    actor=conftest.actor.__wrapped__(fixture_client)
    doc=document();doc['title']='Synthetic English revision notes';doc['summary']='Synthetic browser rehearsal: a short study guide published by a public creator.'
    mid=publish(fixture_client,actor,doc)
    database[1].execute("INSERT INTO creator_profiles(user_id,public,bio) VALUES('author',true,'Synthetic study creator. Clear notes, small practice sessions and thoughtful revision.')")
    print('Synthetic creator profile: http://127.0.0.1:5189/creators/author',flush=True)
if os.environ.get('ISM_PUBLISHING_DEMO')=='1':
    from test_content_studio import publish,document
    from uuid import uuid4
    actor=conftest.actor.__wrapped__(fixture_client)
    doc=document();doc['title']='Synthetic English source guide';doc['blocks'][0]['text']='Original approved heading'
    mid=publish(fixture_client,actor,doc)
    h=actor('author');d=fixture_client.get('/api/studio/materials/'+mid).json()
    doc['title']='Synthetic English source guide · revision 2';doc['summary']='Synthetic review draft with clearer source guidance and a new revision tip.';doc['blocks'][0]['text']='Revised source-aware heading';doc['blocks'].append({'id':'tip','type':'callout','text':'Check the printed source before choosing an answer.'})
    r=fixture_client.post('/api/studio/materials/'+mid+'/save',headers=h,json={'expected_version':d['lock_version'],'document':doc})
    assert r.status_code==200,r.text
    r=fixture_client.post('/api/studio/materials/'+mid+'/submit',headers=h,json={'expected_version':r.json()['lock_version']});assert r.status_code==200,r.text
    h=actor('outsider');fixture_client.post('/api/materials/'+mid+'/report',headers=h,json={'reason':'copyright','note':'Synthetic source attribution report for the CMS owner.'})
    fixture_client.post('/api/creators/author/report',headers=h,json={'reason':'impersonation','note':'Synthetic creator identity report for owner rehearsal.'})
    database[1].execute("INSERT INTO content_reports(canonical_id,kind,reporter_id,note) VALUES('cq_test','wrong_key','outsider','Synthetic scoring report for owner rehearsal')")
    print('Synthetic publishing dashboard: http://127.0.0.1:5189/admin/bank?tab=workflow',flush=True)
if os.environ.get('ISM_MODULE_INTAKE_DEMO')=='1':
    import tempfile
    from test_module_intake import intake
    with tempfile.TemporaryDirectory(prefix='ism-module-browser-') as demo_dir:
        manifest,rows,bank,receipt=intake.__wrapped__(database,fixture_client,Path(demo_dir))
    if os.environ.get('ISM_MODULE_RESEARCH_DEMO')=='1':
        import copy
        from test_module_intake import imp
        manifest=copy.deepcopy(manifest);manifest['run'].pop('manifest_sha256');manifest['run']['id']+='r'
        for row in manifest['items']:
            row['id']+='r';row['run_id']=manifest['run']['id']
            if row['legacy_id']=='unique':
                row['reviewed_packets']=[{'file':'synthetic-research.json','claim':{'appearanceId':bank[0]['id'],'outcome':'retain_bank','rationale':'Synthetic research rehearsal only: preserve the current answer while inspecting the conflicting module claim. This is not a production adjudication.','reviewStatus':'prepared_independent_review_required','currentBankAnswerIndex':0,'proposedAnswerIndex':None,'sources':[{'url':'https://example.test/synthetic-source','title':'Synthetic source reference','accessed':'2026-10-23'}],'proposals':[]}}]
        manifest['run']['manifest_sha256']=imp.digest(manifest)
        imp.import_manifest(database[1],manifest,'synthetic-browser')
    print('Synthetic module intake: http://127.0.0.1:5189/admin/bank?tab=modules&audit_run='+manifest['run']['id'],flush=True)
if os.environ.get('ISM_PREPARED_DRAFT_DEMO')=='1':
    import tempfile
    from test_module_intake import intake
    from test_prepared_module_drafts import research
    actor=conftest.actor.__wrapped__(fixture_client)
    with tempfile.TemporaryDirectory(prefix='ism-prepared-browser-') as demo_dir:
        inputs=intake.__wrapped__(database,fixture_client,Path(demo_dir))
    research_demo=research.__wrapped__(inputs,database,fixture_client,actor)
    prepared=next(research_demo)
    print('Synthetic prepared draft: http://127.0.0.1:5189/admin/bank?tab=modules&module_item='+prepared['item'],flush=True)
if os.environ.get('ISM_DISCUSSION_DEMO')=='1':
    from test_discussions import answer,create,approve
    actor=conftest.actor.__wrapped__(fixture_client)
    h=answer(fixture_client,actor,'cq_test','author')
    r=create(fixture_client,h,'cq_test',body='Synthetic doubt: why does the worked method give option B? Please compare the printed wording.',sources=[{'url':'https://example.test/synthetic-reference','note':'Synthetic reference used only for UI rehearsal'}],context={'paper_id':'paper-test'})
    assert r.status_code==201,r.text
    root=r.json()['id'];approve(fixture_client,actor,root)
    h=answer(fixture_client,actor,'cq_test','outsider')
    r=create(fixture_client,h,'cq_test',kind='reply',parent=root,body='Synthetic explanation: compare each option with the source. Option B satisfies the stated condition.',sources=[{'url':'https://example.test/synthetic-explanation','note':'Synthetic worked explanation reference'}])
    assert r.status_code==201,r.text
    approve(fixture_client,actor,r.json()['id'])
    print('Synthetic discussion: http://127.0.0.1:5189/bank/cq_test?paper=paper-test#discussion',flush=True)
if os.environ.get('ISM_STUDY_DESK_DEMO')=='1':
    from app.config import settings
    from test_study_desks import room,join
    settings.study_desks_private_enabled=True
    actor=conftest.actor.__wrapped__(fixture_client)
    database[1].execute("UPDATE users SET plan_code='pro',plan_status='trial',trial_ends_at=now()+interval '7 days' WHERE id='author'")
    did=room(fixture_client,actor);join(fixture_client,actor,did)
    h=actor('author');doc=fixture_client.get('/api/desk/personal').json()['data'];doc.update(goal='Revise English and practise a focused question set',goalSubject='english',saved=['cq_test'],recent=['cq_test'],notes=[{'id':'synthetic-note','title':'Check the original wording','body':'Synthetic private note: compare the printed source and option order before drawing a conclusion.','subject':'English'}])
    r=fixture_client.post('/api/desk/personal',headers=h,json={'user_id':'author','expected_version':0,'data':doc});assert r.status_code==200,r.text
    from uuid import uuid4
    r=fixture_client.post('/api/desk/rooms/'+did+'/items',headers={**h,'idempotency-key':uuid4().hex},json={'kind':'question','question_id':'cq_test','body':'Synthetic shared question: compare the source wording together.'});assert r.status_code==201,r.text
    fixture_client.post('/api/desk/rooms/'+did+'/items',headers={**h,'idempotency-key':uuid4().hex},json={'kind':'note','title':'Our source-checking method','body':'Synthetic shared note. Read the question carefully, keep option order fixed and cite the source.'})
    fixture_client.post('/api/desk/rooms/'+did+'/messages',headers={**h,'idempotency-key':uuid4().hex},json={'body':'Synthetic chat: shall we compare the source after our focus session?'})
    print('Synthetic Study Desk: http://127.0.0.1:5189/desk/'+did,flush=True)
if os.environ.get('ISM_INBOX_DEMO')=='1':
    from uuid import uuid4
    from app.config import settings
    settings.study_desks_private_enabled=True
    conn=database[1]
    did='synthetic-inbox-desk'
    conn.execute("INSERT INTO study_desks(id,owner_id,name,goal) VALUES (%s,'author','Evening revision desk','Compare sources and revise together')",(did,))
    conn.execute("INSERT INTO study_desk_members(desk_id,user_id) VALUES (%s,'author'),(%s,'outsider')",(did,did))
    for n in range(3):
        conn.execute("INSERT INTO study_desk_messages(desk_id,author_id,body,request_key,request_hash) VALUES (%s,%s,%s,%s,'synthetic')",(did,'outsider' if n!=1 else 'author',['Shall we revise geography together today?','Yes, let’s compare the original questions first.','I have the source paper ready.'][n],uuid4().hex))
    for n in range(25):
        conn.execute("INSERT INTO review_notifications(user_id,event_key,message,discussion_question_id) VALUES('author',%s,%s,'cq_test')",('synthetic-inbox:'+str(n),'Synthetic discussion update '+str(n+1)+': a partner shared their reasoning.'))
    conn.execute("INSERT INTO review_notifications(user_id,event_key,message,study_desk_id) VALUES('author','synthetic-desk-inbox','New messages in your evening revision desk',%s)",(did,))
    print('Synthetic Inbox: http://127.0.0.1:5189/inbox?desk='+did,flush=True)
if os.environ.get('ISM_LIBRARY_DEMO')=='1':
    from test_library_topics import question
    from test_content_studio import document,publish
    actor=conftest.actor.__wrapped__(fixture_client)
    question(database[1]);question(database[1],primary='general-studies',related=False)
    doc=document();doc['title']='Synthetic Geography revision note';doc['tags']=['Geography'];doc['summary']='A synthetic source-aware revision note for the new Geography shelf.'
    publish(fixture_client,actor,doc)
    print('Synthetic Library: http://127.0.0.1:5189/library',flush=True)
if os.environ.get('ISM_ALL_EXAMS_DEMO')=='1':
    from test_library_topics import question
    conn=database[1];qid,aid=question(conn,primary='general-studies',related=False)
    conn.execute("INSERT INTO papers(id,exam_type,exam_name,year,source_file,exam_scope_id) VALUES ('synthetic-outside-paper','Direct','Synthetic outside exam system',2026,'Old_Questions/test.pdf','outside-mizoram')")
    conn.execute("UPDATE appearances SET paper_id='synthetic-outside-paper',question='Outside exam synthetic geography question' WHERE id=%s",(aid,))
    conn.execute("UPDATE canonical_questions SET question='Outside exam synthetic geography question' WHERE id=%s",(qid,))
    print('Synthetic All exams: http://127.0.0.1:5189/library/topics/geography',flush=True)
if os.environ.get('ISM_VOCABULARY_DEMO')=='1':
    from test_vocabulary import seed
    from psycopg.types.json import Jsonb
    conn=database[1];ids=seed(conn,12)
    for n,qid in enumerate(ids):
        word=['abundant','brief','cautious'][n%3];right=['plentiful','short','careful'][n%3]
        text='Choose the synonym of '+word+'.';markup='Choose the synonym of __'+word+'__.';options=Jsonb(['scarce',right,'distant','noisy'])
        conn.execute("UPDATE canonical_questions SET question=%s,question_markup=%s,options=%s,answer_text=%s WHERE id=%s",(text,markup,options,right,qid))
        conn.execute("UPDATE appearances SET question=%s,question_markup=%s,options=%s,direction='Choose the option closest in meaning to the underlined word.' WHERE canonical_id=%s",(text,markup,options,qid))
    print('Synthetic Vocabulary: http://127.0.0.1:5189/vocabulary',flush=True)
if os.environ.get('ISM_GAMES_DEMO')=='1':
    from psycopg.types.json import Jsonb
    for number in range(40):
        qid='cq_game_demo_'+str(number)
        database[1].execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES(%s,'mcq',%s,%s,'B','official')",(qid,'Synthetic game gate '+str(number+1)+': select the second option.',Jsonb(['A','B','C','D'])))
        database[1].execute("INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary) VALUES(%s,'paper-test','mcq',%s,%s,1,'official',%s,true)",('a_'+qid,'Synthetic game gate '+str(number+1)+': select the second option.',Jsonb(['A','B','C','D']),qid))
        database[1].execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,taxonomy_version,source,review_status) VALUES(%s,'english','English','test','manual','approved')",(qid,))
    database[1].execute("INSERT INTO creator_profiles(user_id,public,bio) VALUES('outsider',true,'Synthetic public creator: English study notes.')")
    database[1].execute("INSERT INTO personal_desks(user_id,document) VALUES('author',%s)",(Jsonb({'notes':[{'id':'demo-note','title':'English private revision note','body':'Synthetic own-account note for global search verification.'}]}),))
    print('Synthetic Games: http://127.0.0.1:5189/games',flush=True)
if os.environ.get('ISM_MOCK_RESUME_DEMO')=='1':
    from psycopg.types.json import Jsonb
    actor=conftest.actor.__wrapped__(fixture_client)
    database[1].execute("INSERT INTO collections(id,title,kind,visibility,live_version) VALUES ('synthetic-resume-exam','LDC · Synthetic unfinished mock','exam','public',1)")
    database[1].execute("INSERT INTO collection_sections(collection_id,version,path,title,position,query) VALUES ('synthetic-resume-exam',1,'general/english','English',0,%s)",(Jsonb({'subject_id':'english'}),))
    h=actor('author')
    r=fixture_client.post('/api/mocks',headers=h,json={'collection_id':'synthetic-resume-exam','section_path':'general/english','answer_mode':'derived-practice','count':2,'duration_minutes':1})
    assert r.status_code==200,r.text
    database[1].execute("UPDATE mock_sessions SET started_at=now()-interval '2 minutes' WHERE id=%s",(r.json()['id'],))
    print('Synthetic blocked games/resume: http://127.0.0.1:5189/games',flush=True)
if os.environ.get('ISM_CALENDAR_DEMO')=='1':
    from test_calendar import doc,save
    from datetime import datetime,timedelta
    from zoneinfo import ZoneInfo
    actor=conftest.actor.__wrapped__(fixture_client)
    calendar_cid='synthetic-calendar-exam'
    database[1].execute("INSERT INTO collections(id,title,kind,visibility) VALUES(%s,'Synthetic LDC calendar','exam','public')",(calendar_cid,))
    h=actor('owner')
    d=doc(calendar_cid,title='Synthetic LDC written examination',state='published',starts_on=str(datetime.now(ZoneInfo('Asia/Kolkata')).date()+timedelta(days=7)))
    r=save(fixture_client,h,'synthetic-calendar-event',d);assert r.status_code==200,r.text
    print('Synthetic Calendar: http://127.0.0.1:5189/calendar',flush=True)
if os.environ.get('ISM_EXAM_INVENTORY_DEMO')=='1':
    from test_exam_inventory import create,body
    from test_admin_workbench import workbench
    actor=conftest.actor.__wrapped__(fixture_client)
    ids,paper,alt=workbench.__wrapped__(fixture_client,actor,database)
    eid,h=create(fixture_client,actor,'Synthetic English recruitment · 2020')
    r=fixture_client.post('/api/admin/bank/inventory/expectations',headers=h,json=body(eid,paper));assert r.status_code==200,r.text
    pending=body(eid);pending['title']='Synthetic missing-link paper · 2026';pending['year']=2026
    r=fixture_client.post('/api/admin/bank/inventory/expectations',headers=h,json=pending);assert r.status_code==200,r.text
    print('Synthetic exam inventory: http://127.0.0.1:5189/admin/bank?tab=exams&exam='+eid,flush=True)
if os.environ.get('ISM_LEARNING_WORKFLOWS_DEMO')=='1':
    from test_learning_workflows import official,attempt
    from test_exam_inventory import create,body
    from test_admin_workbench import workbench
    actor=conftest.actor.__wrapped__(fixture_client)
    q,a,p=official(database)
    database[1].execute("UPDATE canonical_questions SET question='Synthetic: Which option is the recorded key?' WHERE id=%s",(q,))
    attempt(database[1],'owner',q)
    database[1].execute("INSERT INTO personal_desks(user_id,document) VALUES('owner',%s) ON CONFLICT(user_id) DO UPDATE SET document=EXCLUDED.document",(conftest.Jsonb({'saved':[q],'tasks':[{'id':'task-one','text':'Synthetic: revise an English paper','done':False,'week':False}]}),))
    h=actor('owner');h['X-Learning-User']='owner'
    r=fixture_client.post('/api/learning/checkpoint',headers=h,json={'route':'/english?view=practice','question_id':q,'expected_version':0});assert r.status_code==200,r.text
    ids,paper,alt=workbench.__wrapped__(fixture_client,actor,database)
    eid,h=create(fixture_client,actor,'Synthetic intake exam')
    payload=body(eid,paper)
    r=fixture_client.post('/api/admin/bank/inventory/expectations',headers=h,json=payload);assert r.status_code==200,r.text
    print('Synthetic learning workflows: http://127.0.0.1:5189/library | /revision | /admin/bank?tab=intake',flush=True)
try:next(clients)
except StopIteration:pass
if os.environ.get('ISM_RETAG_DEMO')=='1':
    from test_admin_workbench import workbench
    actor=conftest.actor.__wrapped__(fixture_client)
    ids,paper,alt=workbench.__wrapped__(fixture_client,actor,database)
    database[1].execute("INSERT INTO review_taxonomy(id,label,level,version,parent_id) VALUES ('general-knowledge','General Knowledge','subject','test',NULL),('general-studies','General Studies','subject','test',NULL),('gk-current','Current Affairs','topic','test','general-knowledge'),('gs-current','Current Affairs','topic','test','general-studies') ON CONFLICT DO NOTHING")
    print('Synthetic tag review: http://127.0.0.1:5189/admin/bank?tab=retag&paper='+paper,flush=True)
    print('Synthetic identity: http://127.0.0.1:5189/admin/bank?tab=exams&inventory_paper='+paper,flush=True)
from app.routers.auth import _hash_password
from app.config import settings
from app.main import app
settings.public_origin='http://127.0.0.1:5189'
from cryptography.fernet import Fernet
settings.mfa_encryption_key=Fernet.generate_key().decode()
settings.mfa_enforce_staff=os.environ.get('ISM_RETAG_DEMO')!='1' and os.environ.get('ISM_LEARNING_WORKFLOWS_DEMO')!='1' and os.environ.get('ISM_CMS_DEMO')!='1' and os.environ.get('ISM_EXAM_INVENTORY_DEMO')!='1'
for user in ['owner','author','reviewer1','reviewer2','outsider']:
    database[1].execute('UPDATE users SET password_hash=%s WHERE id=%s',(_hash_password('SyntheticPassword123!'),user))
serve_app=app
if os.environ.get('ISM_EXAM_POLISH_DEMO')=='1':
    import asyncio
    from psycopg.types.json import Jsonb
    conn=database[1];pid='exam-polish-paper'
    conn.execute("INSERT INTO papers(id,exam_type,exam_name,year,source_file,exam_scope_id) VALUES(%s,'Direct','Synthetic clerical examination',2026,'Old_Questions/test.pdf','mizoram-recruitment')",(pid,))
    for n in range(30):
        qid=f'cq_polish_{n:02d}'
        conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source,explanation) VALUES(%s,'mcq',%s,%s,'B','official','Synthetic working: B is the second letter.')",(qid,f'Synthetic exam polish question {n+1:02d}: which letter comes second?',Jsonb(['A','B','C','D'])))
        conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary,qnum,page) VALUES(%s,%s,'mcq',%s,%s,1,'official',%s,true,%s,1)",(f'app_polish_{n}',pid,f'Synthetic exam polish question {n+1:02d}: which letter comes second?',Jsonb(['A','B','C','D']),qid,str(n+1)))
        subject='general-knowledge' if n%2==0 else 'english'
        conn.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,topic_id,topic_label,taxonomy_version,source,review_status) VALUES(%s,%s,%s,%s,'Synthetic topic','test','manual','approved')",(qid,subject,'General Knowledge' if n%2==0 else 'English',subject+'/synthetic'))
    for cid in ['udc','ldc','assistant']:
        conn.execute('DELETE FROM collection_papers WHERE collection_id=%s',(cid,))
        conn.execute("UPDATE collection_sections SET query=%s WHERE collection_id=%s",(Jsonb({'paper_ids':[pid]}),cid))
        conn.execute("INSERT INTO collection_papers(collection_id,version,paper_id,as_mock,section_path) SELECT id,live_version,%s,false,'papers' FROM collections WHERE id=%s",(pid,cid))
    failed={}
    async def polish_rehearsal(request,call_next):
        if request.url.path in ('/api/collections/udc','/api/collections/ldc'):
            if failed.get(request.url.path,0)<2:
                failed[request.url.path]=failed.get(request.url.path,0)+1
                return Response('Synthetic metadata outage',status_code=503)
            await asyncio.sleep(6)
        if request.url.path=='/api/questions' and request.query_params.get('q')=='rehearsal-error':
            return Response('Synthetic question outage',status_code=503)
        return await call_next(request)
    from starlette.middleware.base import BaseHTTPMiddleware
    serve_app=BaseHTTPMiddleware(app,dispatch=polish_rehearsal)
    print('Synthetic polish rehearsal: http://127.0.0.1:5189/exams/udc?view=practice',flush=True)

@app.get('/papers/source/Old_Questions/test.pdf')
async def fixture_pdf():
    objects=[b'<< /Type /Catalog /Pages 2 0 R >>',b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 400 300] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>',b'<< /Length 83 >>\nstream\nBT /F1 14 Tf 30 250 Td (Synthetic source paper - Choose the correct option) Tj ET\nendstream',b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>']
    pdf=b'%PDF-1.4\n';offsets=[0]
    for i,obj in enumerate(objects,1):offsets.append(len(pdf));pdf+=str(i).encode()+b' 0 obj\n'+obj+b'\nendobj\n'
    xref=len(pdf);pdf+=b'xref\n0 6\n0000000000 65535 f \n'+b''.join(f'{off:010d} 00000 n \n'.encode() for off in offsets[1:])+f'trailer << /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF'.encode()
    return Response(pdf,media_type='application/pdf')
try:uvicorn.run(serve_app,host='127.0.0.1',port=8019,log_level='warning')
finally:
    if research_demo:
        try:next(research_demo)
        except StopIteration:pass
    try:next(databases)
    except StopIteration:pass
