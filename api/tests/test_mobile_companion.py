from urllib.parse import urlparse,parse_qs
from uuid import uuid4
from psycopg.types.json import Jsonb
import hashlib
import pytest

@pytest.fixture(autouse=True)
def reset_mobile_test_login_budget(database):
    database[1].execute("DELETE FROM auth_login_attempts")

from app.routers.mobile import challenge_for
from app.services.mobile_identity import allowed

CALLBACK='finna://auth/callback'

def connect(client,actor,user='author',verifier='x'*64):
    client.cookies.clear()
    start=client.post('/api/mobile-auth/start',json={'challenge':challenge_for(verifier),'state':'s'*32,'redirect_uri':CALLBACK})
    assert start.status_code==200,start.text
    flow=start.json()['flow']
    headers=actor(user)
    page=client.get('/api/mobile-auth/authorize',params={'flow':flow});assert page.status_code==200
    assert 'Connect this account' in page.text
    authorize=client.post('/api/mobile-auth/authorize',json={'flow':flow},headers=headers)
    assert authorize.status_code==200,authorize.text
    code=parse_qs(urlparse(authorize.json()['redirect']).query)['code'][0]
    client.cookies.clear()
    body={'flow':flow,'code':code,'verifier':verifier,'redirect_uri':CALLBACK}
    result=client.post('/api/mobile-auth/exchange',json=body)
    assert result.status_code==200,result.text
    return {'Authorization':'Bearer '+result.json()['access_token']},body

def test_mobile_pkce_replay_and_scope(client,actor):
    headers,body=connect(client,actor,'owner')
    assert client.get('/api/mobile/session',headers=headers).json()['id']=='owner'
    assert client.post('/api/mobile-auth/exchange',json=body).status_code==400
    capabilities=client.get('/api/mobile/session',headers=headers).json()['capabilities']
    assert not {'site_notice','admin_ops','account_viewer'} & set(capabilities)
    for path in ['/api/review/session','/api/admin/bank/reports','/api/auth/session','/api/auth/google/start','/api/billing/config','/api/me/onboarding','/api/billing/bulk/me','/api/billing/bulk/admin','/api/site-notice','/api/admin/ops/notice','/api/admin/users']:
        assert client.get(path,headers=headers).status_code==403
    assert client.post('/api/mobile/logout',headers=headers).status_code==200
    assert client.get('/api/mobile/session',headers=headers).status_code==401


def test_mobile_browse_allowance_is_private_and_read_only(client,actor):
    headers,_=connect(client,actor)
    session=client.get('/api/mobile/session',headers=headers).json()
    assert 'browse_allowance' in session['capabilities']
    response=client.get('/api/me/browse-allowance',headers=headers)
    assert response.status_code==200 and response.json()['limit']==3
    assert response.headers['cache-control']=='private, no-store'
    assert 'etag' not in response.headers
    assert client.post('/api/me/browse-allowance',headers=headers,json={}).status_code==403

def test_mobile_learning_reads_and_unnegotiated_writes_stay_closed(client,actor):
    headers,_=connect(client,actor)
    capabilities=client.get('/api/mobile/session',headers=headers).json()['capabilities']
    assert {'mastery','review_queue','focus_subjects_read','today','calendar_layers','learning_habit'}<=set(capabilities)
    for path in ('mastery','review-queue','focus-subjects','today','calendar-layers?start=2026-11-01&end=2026-11-30'):
        response=client.get('/api/me/'+path,headers=headers)
        assert response.status_code==200,response.text
        assert response.headers['cache-control']=='private, no-store' and 'etag' not in response.headers
    assert client.patch('/api/me/focus-subjects',headers=headers,json={'subject_ids':[]}).status_code==403
    assert client.put('/api/me/exam-bookmarks/udc/primary',headers=headers).status_code==403
    assert client.post('/api/review-sessions',headers=headers,json={'request_key':uuid4().hex}).status_code==403

def test_old_mobile_cannot_mutate_web_review_via_inherited_study_routes(client,actor,database):
    from test_learning_loop import questions,due
    user='mobile-review-'+uuid4().hex
    conn=database[1]
    conn.execute('INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)',(user,user,user+'@example.test'))
    conn.execute("INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES(%s,%s,now()+interval '1 day')",(hashlib.sha256(('test-session-'+user).encode()).hexdigest(),user))
    _,ids=questions(database,1);due(conn,user,ids)
    web=actor(user)
    response=client.post('/api/review-sessions',headers=web,json={'request_key':uuid4().hex})
    assert response.status_code==200,response.text
    s=response.json();headers,_=connect(client,actor,user)
    assert client.get('/api/study-sessions/'+s['id'],headers=headers).status_code==200
    for action,body in [('answer',{'version':s['version'],'question_id':ids[0],'chosen_index':1}),
                        ('position',{'version':s['version'],'position':0}),
                        ('viewed',{'question_id':ids[0]}),('finish',{'version':s['version']})]:
        r=client.post('/api/study-sessions/'+s['id']+'/'+action,headers=headers,json=body)
        assert r.status_code==403,r.text

def test_mobile_invalid_pkce_origin_and_callback(client,actor):
    client.cookies.clear()
    assert client.post('/api/mobile-auth/start',json={'challenge':'a'*43,'state':'b'*32,'redirect_uri':'https://evil.example/'}).status_code==422
    start=client.post('/api/mobile-auth/start',json={'challenge':challenge_for('v'*64),'state':'b'*32,'redirect_uri':CALLBACK}).json()
    headers=actor('author')
    assert client.post('/api/mobile-auth/authorize',json={'flow':start['flow']}).status_code==403
    authorized=client.post('/api/mobile-auth/authorize',json={'flow':start['flow']},headers=headers).json()
    code=parse_qs(urlparse(authorized['redirect']).query)['code'][0]
    client.cookies.clear()
    body={'flow':start['flow'],'code':code,'verifier':'wrong'*12,'redirect_uri':CALLBACK}
    assert client.post('/api/mobile-auth/exchange',json=body).status_code==400
    body['verifier']='v'*64
    assert client.post('/api/mobile-auth/exchange',json=body).status_code==200

def test_mobile_parent_revocation_and_mixed_cookie(client,actor,database):
    headers,_=connect(client,actor,'outsider')
    client.cookies.set('ism_session','test-session-author')
    assert client.get('/api/mobile/session',headers=headers).status_code==403
    client.cookies.clear()
    c=database[1];token=hashlib.sha256(b'test-session-outsider').hexdigest()
    try:
        c.execute('UPDATE auth_sessions SET revoked_at=now() WHERE token_hash=%s',(token,))
        assert client.get('/api/mobile/session',headers=headers).status_code==401
    finally:c.execute('UPDATE auth_sessions SET revoked_at=NULL WHERE token_hash=%s',(token,))

def test_mobile_bookmarks_and_reports_are_owned(client,actor,database):
    headers,_=connect(client,actor)
    assert client.put('/api/mobile/bookmarks/cq_test',headers=headers).status_code==200
    assert client.put('/api/mobile/bookmarks/cq_test',headers=headers).status_code==200
    assert client.get('/api/mobile/bookmarks',headers=headers).json()['total']==1
    assert client.get('/api/mobile/bookmarks/cq_test',headers=headers).json()=={'saved':True}
    assert client.get('/api/mobile/bookmarks',headers=headers).json()['items'][0]['question']=='Choose the correct synthetic option'
    report=client.post('/api/mobile/questions/cq_test/report',headers=headers,json={'kind':'typo_ocr','note':'Synthetic issue report for this question'})
    assert report.status_code==200,report.text
    other,_=connect(client,actor,'outsider')
    assert client.get('/api/mobile/bookmarks',headers=other).json()['total']==0
    assert client.delete('/api/mobile/bookmarks/cq_test',headers=headers).status_code==200

def test_mobile_stale_question_is_not_answered(client,actor):
    headers,_=connect(client,actor)
    response=client.post('/api/mobile/questions/cq_test/answer',headers=headers,json={'chosen_index':1,'request_key':str(uuid4()),'expected_question':'stale text','expected_options':['A','B','C','D']})
    assert response.status_code==409,response.text

def test_route_allowlist_is_exact():
    assert allowed('POST','/api/games/rooms/game_1/answer')
    assert not allowed('POST','/api/games/rooms/game_1/admin')
    assert not allowed('POST','/api/me/profile')
    assert not allowed('GET','/api/mobile/session/extra')
    assert not allowed('DELETE','/api/questions/cq_test')


def test_study_desk_learner_writes_remain_bounded():
    for path in ('/api/desk/personal','/api/desk/overview','/api/desk/questions',
                 '/api/desk/rooms','/api/desk/rooms/desk_1',
                 '/api/desk/rooms/desk_1/items','/api/desk/rooms/desk_1/messages'):
        assert allowed('GET',path), path
    # Ordinary room actions retain server membership, account and idempotency guards.
    for method,path in (('POST','/api/desk/rooms'),
                        ('POST','/api/desk/focus'),('POST','/api/desk/invites/inv_1'),
                        ('POST','/api/desk/rooms/desk_1/items'),
                        ('POST','/api/desk/rooms/desk_1/messages'),
                        ('POST','/api/desk/rooms/desk_1/invite'),
                        ('POST','/api/desk/rooms/desk_1/sharing'),
                        ('POST','/api/desk/rooms/desk_1/leave'),
                        ('POST','/api/desk/rooms/desk_1/report')):
        assert allowed(method,path), f'{method} {path}'
    assert not allowed('POST','/api/desk/personal')
    assert not allowed('PATCH','/api/desk/rooms/desk_1')
    # Staff moderation is never reachable with mobile credentials.
    assert not allowed('GET','/api/desk/admin/reports')
    assert not allowed('POST','/api/desk/admin/reports/rep_1/resolve')


def test_desk_v4_weekly_goals_are_explicitly_web_only():
    from app.services.mobile_identity import capabilities
    for method in ('GET','HEAD','POST','PATCH','DELETE'):
        assert not allowed(method,'/api/desk/rooms/desk_example/weekly-goal')
        assert not allowed(method,'/api/desk/rooms/desk_example/items/item_example/discussion')
    assert 'desk_weekly_goal' not in capabilities()


def test_profile_reads_and_name_edit_only():
    assert allowed('GET','/api/me/score-summary')
    assert allowed('GET','/api/contributions/summary')
    assert allowed('PATCH','/api/me/profile')
    # Changing the password enforces _same_origin and revokes every
    # auth_session, which would sign the mobile session out of itself.
    assert not allowed('POST','/api/auth/password')
    assert not allowed('PATCH','/api/me/progress')


def test_community_is_full_parity_but_never_moderation():
    for path in ('/api/community/feed','/api/community/contributors',
                 '/api/community/contributions','/api/community/questions/cq_1/discussion',
                 '/api/community/posts/p_1/replies','/api/community/posts/p_1/evidence',
                 '/api/rewards/history','/api/rewards/leaderboard'):
        assert allowed('GET',path), path
    for path in ('/api/community/questions/cq_1/discussion',
                 '/api/community/questions/cq_1/discussion/open',
                 '/api/community/posts/p_1/helpful','/api/community/posts/p_1/accept',
                 '/api/community/posts/p_1/report','/api/community/posts/p_1/withdraw'):
        assert allowed('POST',path), path
    # routers/discussions.py mounts these on the same /api/community prefix.
    assert not allowed('GET','/api/community/admin/queue')
    assert not allowed('POST','/api/community/admin/posts/p_1/action')
    assert not allowed('POST','/api/community/admin/questions/cq_1/lock')
    # Self-service claims and redemption are available; public settings stay excluded.
    assert allowed('POST','/api/rewards/redeem')
    assert allowed('POST','/api/rewards/daily-quests/warmup_circuit/claim')
    for path in ('/api/rewards/streak-shield','/api/rewards/visibility',
                 '/api/rewards/stream-cohort'):
        assert not allowed('POST',path), path

def test_other_exam_practice_and_idempotent_answer(client,actor,database):
    from test_study_sessions import seed
    c=database[1];p,ids=seed(database);collection='mobile-exam-'+uuid4().hex
    c.execute("INSERT INTO collections(id,title,kind,visibility,live_version) VALUES(%s,'Mobile test exam','exam','public',1)",(collection,))
    c.execute('INSERT INTO collection_papers(collection_id,version,paper_id,section_path,as_mock) VALUES(%s,1,%s,\'papers\',true)',(collection,p))
    headers,_=connect(client,actor)
    body={'request_key':uuid4().hex,'collection_id':collection,'filters':{'paper_id':p,'year_from':2025,'year_to':2025}}
    r=client.post('/api/study-sessions',json=body,headers=headers);assert r.status_code==200,r.text
    s=r.json();assert s['collection_id']==collection
    assert client.post('/api/study-sessions',json=body,headers=headers).json()['id']==s['id']
    q=s['items'][0]
    answer={'version':s['version'],'question_id':q['id'],'chosen_index':1,'presentation_hash':q['presentation_hash']}
    url='/api/study-sessions/'+s['id']+'/answer'
    checked=client.post(url,json=answer,headers=headers);assert checked.status_code==200,checked.text
    timing=checked.headers.get('server-timing','')
    assert timing.startswith('answer;dur=') and float(timing.partition('=')[2])>=0
    assert client.post(url,json=answer,headers=headers).json()['results'][q['id']]['result']['correct']
    recent=client.get('/api/study-sessions',params={'collection_id':collection},headers=headers).json()
    assert recent['items'][0]['id']==s['id']
    other,_=connect(client,actor,'outsider')
    assert client.get('/api/study-sessions/'+s['id'],headers=other).status_code==404
    assert c.execute('SELECT count(*) FROM attempts WHERE user_id=\'author\' AND canonical_id=%s AND collection_id=%s',(q['id'],collection)).fetchone()[0]==1

def test_mobile_mock_deadline_and_filters(client,actor,database):
    from test_study_sessions import seed
    c=database[1];p,ids=seed(database,3);collection='mobile-mock-'+uuid4().hex
    c.execute("INSERT INTO collections(id,title,kind,visibility,live_version) VALUES(%s,'Mock mobile exam','exam','public',1)",(collection,))
    c.execute('INSERT INTO collection_papers(collection_id,version,paper_id,section_path,as_mock) VALUES(%s,1,%s,\'papers\',true)',(collection,p))
    c.execute("INSERT INTO collection_sections(collection_id,version,path,title,position,query) VALUES (%s,1,'papers','Papers',0,%s)",(collection,Jsonb({'paper_ids':[p]})))
    c.execute("UPDATE users SET plan_code='pro',plan_status='active',plan_ends_at=now()+interval '1 day' WHERE id='reviewer2'")
    headers,_=connect(client,actor,'reviewer2')
    started=client.post('/api/mocks',headers=headers,json={'collection_id':collection,'count':2,'duration_minutes':1,'selection':{'paper_id':p,'year_from':2025,'year_to':2025,'q':'Synthetic set'}})
    assert started.status_code==200,started.text
    mock=started.json();qid=mock['questions'][0]['id'];url='/api/mocks/'+mock['id']
    answer={'question_id':qid,'chosen_index':1,'position':0,'marked':False}
    assert client.put(url+'/answers',json=answer,headers=headers).status_code==200
    c.execute("UPDATE mock_sessions SET started_at=now()-interval '65 seconds' WHERE id=%s",(mock['id'],))
    assert client.put(url+'/answers',json={**answer,'chosen_index':0},headers=headers).status_code==409
    submitted=client.post(url+'/submit',headers=headers,json={'answers':[{'question_id':qid,'chosen_index':0}]})
    assert submitted.status_code==200,submitted.text
    assert submitted.json()['n_correct']==1
    assert submitted.json()['n_skipped']==1

def test_mobile_answer_receipt_survives_later_content_change(client,actor,database):
    from test_study_sessions import seed
    c=database[1];p,ids=seed(database,1);headers,_=connect(client,actor,'reviewer1')
    body={'chosen_index':1,'request_key':str(uuid4()),'expected_question':'Synthetic set question 0','expected_options':['A','B','C','D'],'paper_id':p}
    url='/api/mobile/questions/'+ids[0]+'/answer'
    result=client.post(url,headers=headers,json=body);assert result.status_code==200,result.text
    timing=result.headers.get('server-timing','')
    assert timing.startswith('answer;dur=') and float(timing.partition('=')[2])>=0
    c.execute("UPDATE canonical_questions SET question='Changed later' WHERE id=%s",(ids[0],))
    again=client.post(url,headers=headers,json=body);assert again.status_code==200 and again.json()==result.json()
    assert client.post(url,headers=headers,json={**body,'chosen_index':0}).status_code==409
    assert c.execute('SELECT count(*) FROM attempts WHERE canonical_id=%s',(ids[0],)).fetchone()[0]==1

def test_mobile_changed_context_and_expired_flow(client,actor,database):
    from test_study_sessions import seed
    c=database[1];p,ids=seed(database,1);headers,_=connect(client,actor)
    body={'chosen_index':1,'request_key':str(uuid4()),'expected_question':'Synthetic set question 0','expected_options':['A','B','C','D'],'paper_id':p,'expected_context':{'passage':'An outdated passage'}}
    rejected=client.post('/api/mobile/questions/'+ids[0]+'/answer',headers=headers,json=body)
    assert rejected.status_code==409,rejected.text
    assert c.execute('SELECT count(*) FROM attempts WHERE canonical_id=%s',(ids[0],)).fetchone()[0]==0
    body['expected_context']={}
    accepted=client.post('/api/mobile/questions/'+ids[0]+'/answer',headers=headers,json=body)
    assert accepted.status_code==200,accepted.text
    client.cookies.clear()
    flow=client.post('/api/mobile-auth/start',json={'challenge':challenge_for('z'*64),'state':'s'*32,'redirect_uri':CALLBACK}).json()['flow']
    c.execute("UPDATE mobile_auth_flows SET expires_at=now()-interval '1 second' WHERE id=%s",(flow,))
    assert client.get('/api/mobile-auth/authorize',params={'flow':flow}).status_code==400

def test_mobile_progress_and_game_requests_use_existing_rules(client,actor,database):
    from test_learning_workflows import learner
    from test_study_sessions import seed
    uid,_=learner(database,actor);c=database[1];p,ids=seed(database,12)
    c.execute('UPDATE appearances a SET question=q.question FROM canonical_questions q WHERE a.canonical_id=q.id AND q.id=ANY(%s)',(ids,))
    for qid in ids:
        c.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,taxonomy_version,source,review_status) VALUES(%s,'english','English','test','manual','approved')",(qid,))
    collection='mobile-game-'+uuid4().hex
    c.execute("INSERT INTO collections(id,title,kind,visibility,live_version) VALUES(%s,'Mobile game exam','exam','public',1)",(collection,))
    c.execute("INSERT INTO collection_papers(collection_id,version,paper_id,section_path,as_mock) VALUES(%s,1,%s,'papers',true)",(collection,p))
    headers,_=connect(client,actor,uid)
    for path in ['/api/me/progress','/api/rewards/me','/api/me/exam-bookmarks','/api/games']:
        response=client.get(path,headers=headers);assert response.status_code==200,(path,response.text)
    selection={'kind':'exam','collection_id':collection,'excluded_areas':[]}
    preview=client.post('/api/games/preview',headers=headers,json={'mode':'speed','selection':selection})
    assert preview.status_code==200,preview.text
    body={'mode':'speed','selection':selection,'preview_hash':preview.json()['context_hash'],'request_key':uuid4().hex,'matchmaking':False,'public_result':False}
    created=client.post('/api/games/rooms',headers=headers,json=body);assert created.status_code==200,created.text
    room=created.json();url='/api/games/rooms/'+room['id']
    assert client.post('/api/games/rooms',headers=headers,json=body).json()['id']==room['id']
    answer={'position':room['position'],'chosen_index':1}
    first=client.post(url+'/answer',headers=headers,json=answer);assert first.status_code==200,first.text
    assert client.post(url+'/answer',headers=headers,json=answer).status_code==200
    assert c.execute('SELECT count(*) FROM game_answers WHERE room_id=%s AND user_id=%s AND position=%s',(room['id'],uid,room['position'])).fetchone()[0]==1
    assert client.post(url+'/leave',headers=headers,json={}).status_code==200


def test_chronicle_mobile_scope_is_read_only_and_exact():
    path='/api/learning-catalog/bank-dates'
    assert allowed('GET',path)
    assert allowed('HEAD',path)
    for method in ('POST','PUT','PATCH','DELETE'):
        assert not allowed(method,path)
    for suffix in ('/extra','/manage','-admin'):
        assert not allowed('GET',path+suffix)
    assert not allowed('GET','/api/learning-catalog/manage')


def test_chronicle_mobile_read_preserves_live_assessment_gate(client,actor,database):
    headers,_=connect(client,actor,'outsider')
    response=client.get('/api/learning-catalog/bank-dates',headers=headers,params={'limit':1})
    assert response.status_code==200,response.text
    assert response.headers['cache-control']=='private, no-store'
    conn=database[1]
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES('mobile-chronicle-active','outsider','combined-prelims',%s,600)",(['cq_test'],))
    try:
        blocked=client.get('/api/learning-catalog/bank-dates',headers=headers,params={'limit':1})
        assert blocked.status_code==409,blocked.text
    finally:conn.execute("DELETE FROM mock_sessions WHERE id='mobile-chronicle-active'")


def test_content_and_inbox_routes_never_grant_editorial_access():
    for path in ('/api/materials','/api/materials/mat_1','/api/studio/materials',
                 '/api/studio/materials/mat_1','/api/creators','/api/creators/author',
                 '/api/inbox/notifications','/api/inbox/threads/desk_1/messages'):
        assert allowed('GET',path)
        assert allowed('HEAD',path)
    for path in ('/api/studio/materials','/api/studio/materials/mat_1/save',
                 '/api/studio/materials/mat_1/submit','/api/materials/mat_1/reaction',
                 '/api/creators/author/follow','/api/inbox/notifications/read-all',
                 '/api/inbox/notifications/1/read','/api/inbox/threads/desk_1/read'):
        assert allowed('POST',path)
    for path in ('/api/admin/bank/content','/api/admin/bank/content/mat_1/review',
                 '/api/review/session','/api/inbox/admin','/api/desk/admin/reports',
                 '/api/studio/materials/mat_1/review','/api/studio/materials/mat_1/publish'):
        assert not allowed('GET',path)
        assert not allowed('POST',path)
    assert not allowed('DELETE','/api/studio/materials/mat_1')
    assert not allowed('GET','/api/inbox/notifications/1/read')


def test_mobile_inbox_keeps_account_binding_and_cookie_identity(client,actor,database):
    c=database[1]
    mine=c.execute("INSERT INTO review_notifications(user_id,event_key,message) VALUES('author',%s,'Native account notice') RETURNING id",('mobile-inbox:'+uuid4().hex,)).fetchone()[0]
    other=c.execute("INSERT INTO review_notifications(user_id,event_key,message) VALUES('outsider',%s,'Private other notice') RETURNING id",('mobile-inbox:'+uuid4().hex,)).fetchone()[0]
    headers,_=connect(client,actor)
    response=client.get('/api/inbox/notifications',headers=headers)
    assert response.status_code==200,response.text
    assert mine in [n['id'] for n in response.json()['items']]
    assert other not in [n['id'] for n in response.json()['items']]
    path=f'/api/inbox/notifications/{mine}/read'
    assert client.post(path,headers=headers,json={'read':True}).status_code==409
    assert client.post(path,headers={**headers,'X-Inbox-User':'outsider'},json={'read':True}).status_code==409
    bound={**headers,'X-Inbox-User':'author'}
    assert client.post(path,headers=bound,json={'read':True}).status_code==200
    assert client.post(f'/api/inbox/notifications/{other}/read',headers=bound,json={'read':True}).status_code==404
    assert client.get('/api/review/session',headers=headers).status_code==403
    client.cookies.clear()
    # Cookie callers still require same-origin CSRF; mobile support does not relax it.
    actor('author')
    assert client.post(path,headers={'X-Inbox-User':'author'},json={'read':True}).status_code==403


def test_mobile_material_drafts_stay_private_and_versioned(client,actor,database):
    database[1].execute("DELETE FROM review_rate_buckets WHERE bucket LIKE 'cms:%'")
    headers,_=connect(client,actor)
    doc={'title':'Native synthetic note','summary':'A synthetic material used to verify private native draft ownership.',
         'kind':'note','access':'free','price_paise':0,'tags':[],
         'blocks':[{'id':'paragraph1','type':'paragraph','text':'Synthetic draft body.'}],
         'collection_id':None,'subject_id':None,'preview':''}
    keyed={**headers,'Idempotency-Key':uuid4().hex}
    created=client.post('/api/studio/materials',headers=keyed,json=doc)
    assert created.status_code==201,created.text
    mid=created.json()['id']
    assert client.post('/api/studio/materials',headers=keyed,json=doc).json()['id']==mid
    assert client.get('/api/materials/'+mid,headers=headers).status_code==404
    draft=client.get('/api/studio/materials/'+mid,headers=headers).json()
    assert draft['document']['blocks'][0]['text']=='Synthetic draft body.'
    response=client.post(f'/api/studio/materials/{mid}/save',headers=headers,json={'expected_version':draft['lock_version']+1,'document':doc})
    assert response.status_code==409,response.text
    submitted=client.post(f'/api/studio/materials/{mid}/submit',headers=headers,json={'expected_version':draft['lock_version']})
    assert submitted.status_code==200,submitted.text
    assert client.get('/api/materials/'+mid,headers=headers).status_code==404
    other,_=connect(client,actor,'outsider')
    assert client.get('/api/studio/materials/'+mid,headers=other).status_code==404
    assert client.post('/api/admin/bank/content/'+mid+'/review',headers=headers,json={}).status_code==403


def test_native_chat_retries_membership_and_block_rules(client,actor,database):
    from app.config import settings
    c=database[1]; previous=settings.study_desks_private_enabled;settings.study_desks_private_enabled=True
    did='native-desk-'+uuid4().hex
    c.execute("INSERT INTO study_desks(id,owner_id,name,goal) VALUES(%s,'author','Native desk','Synthetic study goal')",(did,))
    c.execute("INSERT INTO study_desk_members(desk_id,user_id) VALUES(%s,'author'),(%s,'reviewer1')",(did,did))
    c.execute("DELETE FROM review_rate_buckets WHERE bucket LIKE 'cms:%'")
    try:
        headers,_=connect(client,actor)
        path=f'/api/desk/rooms/{did}/messages';keyed={**headers,'Idempotency-Key':uuid4().hex}
        sent=client.post(path,headers=keyed,json={'body':'A synthetic native message'})
        assert sent.status_code==201,sent.text
        assert client.post(path,headers=keyed,json={'body':'A synthetic native message'}).json()['id']==sent.json()['id']
        assert client.post(path,headers=keyed,json={'body':'Changed native message'}).status_code==409
        other,_=connect(client,actor,'outsider')
        assert client.get(f'/api/inbox/threads/{did}/messages',headers=other).status_code==404
        assert client.post(path,headers={**other,'Idempotency-Key':uuid4().hex},json={'body':'Not a member'}).status_code==404
        c.execute("INSERT INTO creator_blocks(user_id,blocked_id) VALUES('reviewer1','author') ON CONFLICT DO NOTHING")
        reviewer,_=connect(client,actor,'reviewer1')
        assert client.get(f'/api/inbox/threads/{did}/messages',headers=reviewer).json()['items']==[]
        c.execute("UPDATE study_desk_members SET left_at=now() WHERE desk_id=%s AND user_id='author'",(did,))
        assert client.get(f'/api/inbox/threads/{did}/messages',headers=headers).status_code==404
    finally:
        settings.study_desks_private_enabled=previous
        c.execute("DELETE FROM creator_blocks WHERE user_id='reviewer1' AND blocked_id='author'")


def test_native_original_question_review_and_owner_boundary(client,actor,database):
    headers,_=connect(client,actor,'owner')
    proposal={'kind':'new_question','canonical_id':None,'appearance_id':None,'subject_id':'english',
      'title':'Native original synthetic MCQ '+uuid4().hex[:6],
      'rationale':'A disposable original proposal to test the native learner review path.',
      'patch':{'question':'Which synthetic native token is second? '+uuid4().hex,
        'options':['Alpha','Beta','Gamma','Delta'],'answerIndex':1,'answerSource':'derived',
        'explanation':'Beta is second in this explicitly ordered synthetic list.',
        'classification':{'subject_id':'english'}},
      'evidence':[{'kind':'reasoning','note':'The ordered list supplies the reasoning for the synthetic answer.'}]}
    keyed={**headers,'Idempotency-Key':uuid4().hex}
    r=client.post('/api/mobile/contributions',headers=keyed,json=proposal)
    assert r.status_code==201,r.text
    row=r.json();cid=row['id']
    assert client.post('/api/mobile/contributions',headers=keyed,json=proposal).json()['id']==cid
    detail=client.get('/api/mobile/contributions/'+cid,headers=headers)
    assert detail.status_code==200,detail.text
    assert detail.json()['permissions']==[]
    credit=client.get('/api/mobile/contributions/summary',headers=headers)
    assert credit.status_code==200,credit.text
    assert isinstance(credit.json()['credit'],int)
    assert client.get('/api/mobile/session',headers=headers).status_code==200
    submitted=client.post(f'/api/mobile/contributions/{cid}/submit',headers=headers,json={'expected_version':row['lock_version']})
    assert submitted.status_code==200,submitted.text
    assert submitted.json()['state']=='submitted'
    assert client.post(f'/api/admin/bank/contributions/{cid}/publish',headers=headers,json={}).status_code==403
    other,_=connect(client,actor,'outsider')
    assert client.get('/api/mobile/contributions/'+cid,headers=other).status_code==404
    assert client.post(f'/api/mobile/contributions/{cid}/submit',headers=other,json={'expected_version':row['lock_version']}).status_code==404
    forbidden={**proposal,'kind':'explanation','canonical_id':'cq_test','patch':{'explanation':'This native editor must never mutate existing bank content.'}}
    assert client.post('/api/mobile/contributions',headers=keyed,json=forbidden).status_code==403


def test_native_learning_is_owned_retry_safe_and_never_publishes(client,actor,database):
    headers,_=connect(client,actor,'owner')
    content={'kind':'day','title':'Synthetic native day','description':'A disposable source-bound learning day, never published.',
      'subject_id':'english','question_ids':[],'month':11,'day':15,
      'sources':[{'title':'Synthetic source','url':'https://example.test/source','checked_on':'2026-01-01'}]}
    body={'id':'learn_'+uuid4().hex,'expected_version':0,'content':content,'reason':'Testing native learning authoring with synthetic data.'}
    r=client.post('/api/mobile/learning',headers=headers,json=body)
    assert r.status_code==200,r.text
    row=r.json();eid=row['id']
    assert client.post('/api/mobile/learning',headers=headers,json=body).json()['version']==row['version']
    for action in ('publish','owner_publish','reject','request_changes'):
        r=client.post(f'/api/mobile/learning/{eid}/decision',headers=headers,json={'expected_version':row['version'],'action':action,'reason':'A native learner must not inherit owner publication privileges.'})
        assert r.status_code==422,r.text
    r=client.post(f'/api/mobile/learning/{eid}/decision',headers=headers,json={'expected_version':row['version'],'action':'submit','reason':'Please independently check the date, source and linked content.'})
    assert r.status_code==200,r.text
    assert r.json()['state']=='submitted' and r.json()['live_payload'] is None
    other,_=connect(client,actor,'outsider')
    assert eid not in [x['id'] for x in client.get('/api/mobile/learning',headers=other).json()['items']]
    body['expected_version']=2
    assert client.post('/api/mobile/learning',headers=other,json=body).status_code==403
    assert client.post(f'/api/mobile/learning/{eid}/decision',headers=other,json={'expected_version':2,'action':'submit','reason':'An unrelated account cannot submit another author’s content.'}).status_code==404


def test_native_timed_test_preserves_frozen_question_identity(client,actor,database):
    from test_learning_workflows import official
    qid=official(database)[0]
    headers,_=connect(client,actor)
    body={'id':'learn_'+uuid4().hex,'expected_version':0,'reason':'Create a private native timed test from a synthetic source.',
      'content':{'kind':'practice','title':'Native timed test','description':'A synthetic timed test with explicit source questions and marking.',
      'subject_id':'english','question_ids':[qid],
      'test_config':{'duration_minutes':7,'marks_correct':2,'marks_wrong':0.5,'answer_mode':'official'}}}
    r=client.post('/api/mobile/learning',headers=headers,json=body)
    assert r.status_code==200,r.text
    assert r.json()['payload']['question_ids']==[qid]
    assert client.get('/api/tests/'+body['id'],headers=headers).status_code==404
    selection=client.get('/api/tests/selection',headers=headers,params={'ids':qid})
    assert selection.status_code==200,selection.text
    assert 'answer_text' not in selection.text


def test_native_avatar_and_security_remain_account_bound(client,actor,database):
    from app.services.avatars import DEFAULT
    headers,_=connect(client,actor)
    r=client.get('/api/me/avatar',headers=headers);assert r.status_code==200,r.text
    version=r.json()['avatar_version']
    assert client.post('/api/me/avatar',headers=headers,json={'user_id':'outsider','expected_version':version,'look':DEFAULT}).status_code==409
    assert client.post('/api/me/avatar',headers=headers,json={'user_id':'author','expected_version':version,'look':DEFAULT}).status_code==200
    first=client.get('/api/mobile/security',headers=headers)
    assert first.status_code==200,first.text
    assert 'token_hash' not in first.text and 'parent_session_hash' not in first.text
    current=next(s for s in first.json()['mobile'] if s['current'])
    assert client.post('/api/mobile/security/revoke',headers=headers,json={'kind':'mobile','id':current['id']}).status_code==409
    other,_=connect(client,actor,'outsider')
    assert client.post('/api/mobile/security/revoke',headers=other,json={'kind':'mobile','id':current['id']}).json()['revoked']==0
    second,_=connect(client,actor)
    assert client.post('/api/mobile/security/revoke',headers=second,json={'kind':'mobile','id':current['id']}).json()['revoked']==1
    assert client.get('/api/mobile/session',headers=headers).status_code==401
    assert client.get('/api/mobile/billing',headers=second).status_code==200
    assert client.post('/api/billing/checkout',headers=second,json={'period':'monthly'}).status_code==403


def test_native_trail_permission_is_literal_and_non_admin():
    assert allowed('GET','/api/topic-trail')
    assert allowed('POST','/api/topic-trail/start')
    assert allowed('POST','/api/topic-trail/game_1/begin')
    for path in ('/api/topic-trail/manage','/api/topic-trail/pool','/api/topic-trail/packs'):
        assert not allowed('GET',path)
        assert not allowed('POST',path)
    for path in ('/api/mobile/learning/x/publish','/api/mobile/contributions/x/decisions','/api/mobile/security/revoke/all'):
        assert not allowed('POST',path)


def test_weekly_boards_use_mobile_identity_without_widening_writes(client,actor,database):
    headers,_=connect(client,actor,'outsider')
    caps=client.get('/api/mobile/session',headers=headers).json()['capabilities']
    assert {'weekly_boards','weekly_recap'}<=set(caps)
    conn=database[1]
    conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,note) VALUES('outsider',%s,'adjustment',13,'Isolated mobile placement')",(uuid4().hex,))
    response=client.get('/api/rewards/leaderboard',headers=headers)
    assert response.status_code==200,response.text
    assert response.json()['placement']=={'xp':13,'rank':1,'public':False}
    assert response.headers['cache-control']=='private, no-store' and 'etag' not in response.headers
    for mode in ('gauntlet','speed','duel','daily'):
        result=client.get('/api/games/leaderboard?track='+mode,headers=headers)
        assert result.status_code==200 and result.headers['cache-control']=='private, no-store'
    assert 'weekly_recap' in client.get('/api/me/today',headers=headers).json()
    assert client.post('/api/rewards/visibility',headers=headers,json={'public':True}).status_code==403
    assert client.post('/api/review-sessions',headers=headers,json={'request_key':uuid4().hex}).status_code==403


@pytest.fixture
def mobile_learning_role(monkeypatch):
    from contextlib import asynccontextmanager
    from app.db import cursor
    from app.routers import learning_loop,study_sessions
    @asynccontextmanager
    async def role_cursor():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            yield cur
    for module in (learning_loop,study_sessions):monkeypatch.setattr(module,'cursor',role_cursor)


def test_mobile_capabilities_derive_from_complete_allowlist_and_negotiate(client,actor,database,monkeypatch):
    from app.services import mobile_identity as boundary
    headers,_=connect(client,actor)
    expected={'review_sessions','review_answers','focus_subjects_write'}
    assert expected<=set(client.get('/api/mobile/session',headers=headers).json()['capabilities'])
    for name,paths in boundary.FEATURES:
        if name in expected:assert all(allowed(method,path) for method,path in paths)
    old=boundary.WRITE
    monkeypatch.setattr(boundary,'WRITE',old|{'POST':tuple(p for p in old['POST'] if p!=r'/api/review-sessions')})
    assert 'review_sessions' not in client.get('/api/mobile/session',headers=headers).json()['capabilities']
    assert client.post('/api/review-sessions',headers=headers|{'X-Finna-Capability':'review_sessions'},json={'request_key':uuid4().hex}).status_code==403
    monkeypatch.setattr(boundary,'WRITE',old)
    for method,path in [('POST','/api/review-sessions'),('PATCH','/api/me/focus-subjects')]:
        assert client.request(method,path,headers={'Authorization':'Bearer ism_mobile_invalid'},json={}).status_code==401
    for method,path in [('PUT','/api/me/focus-subjects'),('DELETE','/api/review-sessions'),('POST','/api/review-sessions/award')]:
        assert client.request(method,path,headers=headers,json={}).status_code==403


def test_mobile_focus_write_owned_registry_limits_and_no_queue_or_award_loss(client,actor,database,mobile_learning_role):
    from test_learning_loop import questions,due
    conn=database[1];_,ids=questions(database,2);due(conn,'author',ids)
    headers,_=connect(client,actor);headers|={'X-Finna-Capability':'focus_subjects_write'}
    before=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    for subjects in (['english','english'],['missing'],['english']*6):
        assert client.patch('/api/me/focus-subjects',headers=headers,json={'subject_ids':subjects}).status_code==422
    assert client.patch('/api/me/focus-subjects',headers=headers,json={'subject_ids':['english'],'user_id':'outsider'}).status_code==422
    assert client.patch('/api/me/focus-subjects',headers=headers,json={'subject_ids':['english']}).status_code==200
    assert conn.execute('SELECT subject_id FROM user_focus_subjects WHERE user_id=\'author\'').fetchall()==[('english',)]
    assert conn.execute('SELECT count(*) FROM user_focus_subjects WHERE user_id=\'outsider\'').fetchone()[0]==0
    assert client.patch('/api/me/focus-subjects',headers=headers,json={'subject_ids':[]}).status_code==200
    assert client.get('/api/me/review-queue',headers=headers).json()['due_count']>=2
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==before


def test_mobile_review_compose_answer_replay_owner_and_presentation_guards(client,actor,database,mobile_learning_role):
    from test_learning_loop import questions,due
    from test_learning_workflows import learner
    conn=database[1];user,_=learner(database,actor);_,ids=questions(database,2);due(conn,user,ids)
    headers,_=connect(client,actor,user);compose=headers|{'X-Finna-Capability':'review_sessions'}
    body={'request_key':uuid4().hex,'size':2}
    assert client.post('/api/review-sessions',headers=compose,json=body|{'question_ids':ids}).status_code==422
    response=client.post('/api/review-sessions',headers=compose,json=body);assert response.status_code==200,response.text
    s=response.json();url='/api/study-sessions/'+s['id'];qid=s['question_ids'][0]
    assert client.post('/api/review-sessions',headers=compose,json=body).json()['id']==s['id']
    assert client.post('/api/review-sessions',headers=compose,json=body|{'size':1}).status_code==409
    answer=headers|{'X-Finna-Capability':'review_answers'}
    submitted={'version':s['version'],'question_id':qid,'chosen_index':1}
    assert client.post(url+'/answer',headers=answer,json=submitted).status_code==422
    q=next(q for q in s['items'] if q['id']==qid)
    assert client.post(url+'/answer',headers=answer,json=submitted|{'presentation_hash':'0'*64}).status_code==409
    submitted|={'presentation_hash':q['presentation_hash']}
    for _ in range(2):
        response=client.post(url+'/answer',headers=answer,json=submitted);assert response.status_code==200,response.text
    assert conn.execute("SELECT count(*) FROM practice_request_receipts WHERE user_id=%s AND request_key LIKE %s",(user,'study:'+s['id']+':%')).fetchone()[0]==1
    assert client.post(url+'/answer',headers=answer,json=submitted|{'chosen_index':0}).status_code==409
    other,_=connect(client,actor,'outsider');other|={'X-Finna-Capability':'review_answers'}
    assert client.get(url,headers=other).status_code==404
    assert client.post(url+'/answer',headers=other,json=submitted).status_code==404
    conn.execute('UPDATE auth_sessions SET revoked_at=now() WHERE user_id=%s',(user,))
    assert client.post(url+'/finish',headers=answer,json={'version':response.json()['version']}).status_code==401


def test_mobile_scheduled_review_awards_use_same_timing_replay_and_two_slot_cap(client,actor,database,mobile_learning_role):
    from test_learning_loop import questions,due
    from test_learning_workflows import learner
    conn=database[1];user,_=learner(database,actor);_,ids=questions(database,24)
    headers,_=connect(client,actor,user)
    for n in range(3):
        due(conn,user,ids[8*n:8*(n+1)])
        s=client.post('/api/review-sessions',headers=headers|{'X-Finna-Capability':'review_sessions'},json={'request_key':uuid4().hex,'size':8}).json()
        url='/api/study-sessions/'+s['id'];answer=headers|{'X-Finna-Capability':'review_answers'}
        for i,qid in enumerate(s['question_ids']):
            if i:s=client.post(url+'/position',headers=answer,json={'version':s['version'],'position':i}).json()
            conn.execute("UPDATE review_session_items SET opened_at=clock_timestamp()-interval '4 seconds' WHERE session_id=%s AND canonical_id=%s",(s['id'],qid))
            q=next(q for q in client.get(url,headers=headers).json()['items'] if q['id']==qid)
            response=client.post(url+'/answer',headers=answer,json={'version':s['version'],'question_id':qid,'chosen_index':1 if i<5 else 0,'presentation_hash':q['presentation_hash']})
            assert response.status_code==200,response.text;s=response.json()
        finished=client.post(url+'/finish',headers=answer,json={'version':s['version']});assert finished.status_code==200,finished.text
        reward=finished.json()['summary']['reward']
        assert reward['status']==('daily_cap' if n==2 else 'awarded')
        assert client.post(url+'/finish',headers=answer,json={'version':1}).json()['summary']['reward']==reward
    assert conn.execute('SELECT count(*),sum(points) FROM reward_ledger WHERE user_id=%s AND event_key LIKE \'review:%%\'',(user,)).fetchone()==(2,4)
    # The capability header is not proof of time spent: fast sets still earn0.
    fast,_=learner(database,actor);_,fastids=questions(database,8);due(conn,fast,fastids)
    mobile,_=connect(client,actor,fast)
    s=client.post('/api/review-sessions',headers=mobile|{'X-Finna-Capability':'review_sessions'},json={'request_key':uuid4().hex,'size':8}).json()
    url='/api/study-sessions/'+s['id'];answer=mobile|{'X-Finna-Capability':'review_answers'}
    for i,qid in enumerate(s['question_ids']):
        if i:s=client.post(url+'/position',headers=answer,json={'version':s['version'],'position':i}).json()
        q=next(q for q in client.get(url,headers=mobile).json()['items'] if q['id']==qid)
        s=client.post(url+'/answer',headers=answer,json={'version':s['version'],'question_id':qid,'chosen_index':1,'presentation_hash':q['presentation_hash']}).json()
    done=client.post(url+'/finish',headers=answer,json={'version':s['version']})
    assert done.status_code==200,done.text
    assert done.json()['summary']['reward']['status']=='not_eligible'


def test_community_edits_and_revision_history_remain_web_only():
    from app.services.mobile_identity import allowed
    assert not allowed('POST','/api/community/posts/123/edit')
    assert not allowed('GET','/api/community/posts/123/revisions')


def test_acceptance_nudge_remains_web_only():
    from app.services.mobile_identity import allowed
    assert not allowed('POST','/api/community/posts/123/acceptance-nudge')


def test_community_standing_and_guide_reads_remain_web_only():
    from app.services.mobile_identity import allowed
    assert not allowed('GET','/api/community/standing')
    assert not allowed('GET','/api/community/guides')


def test_submission_tracker_remains_web_only():
    from app.services.mobile_identity import allowed
    assert not allowed('GET','/api/community/submissions')


def test_desk_practice_surface_stays_closed_without_native_capability():
    from app.services.mobile_identity import capabilities
    assert 'desk_practice' not in capabilities()
    for method,path in [('GET','/api/desk/rooms/example/practice'),
                        ('POST','/api/desk/rooms/example/practice'),
                        ('POST','/api/desk/rooms/example/practice/game/join')]:
        assert not allowed(method,path)
    # Inherited game reads and explicit reservation release remain available;
    # Desk-bound ready/start/answer are additionally checked in the router.
    assert allowed('GET','/api/games/rooms/example')
    assert allowed('POST','/api/games/rooms/example/leave')


def test_question_note_export_and_link_reader_remain_web_only():
    from app.services.mobile_identity import capabilities
    assert 'desk_notes' not in capabilities()
    for path in ('/api/me/desk-notes-print','/api/desk/rooms/example/notes/item'):
        assert not allowed('GET',path)
