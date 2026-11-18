"""Real disposable-mpsc primary-exam practice; no new reward or mastery ledger."""
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
import pytest
from psycopg.types.json import Jsonb
from test_learning_workflows import learner
from test_study_sessions import seed
from test_mobile_companion import connect
from app.services import onboarding_release


@pytest.fixture(autouse=True)
def real_database_role(client,monkeypatch):
    from contextlib import asynccontextmanager
    from app import db
    from app.routers import learning_loop,study_sessions
    original=db.cursor
    @asynccontextmanager
    async def role_cursor():
        async with original() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            await cur.execute('SELECT current_user');assert (await cur.fetchone())['current_user']=='mpsc'
            yield cur
    monkeypatch.setattr(learning_loop,'cursor',role_cursor)
    monkeypatch.setattr(study_sessions,'cursor',role_cursor)


def setup(client,actor,database,n=20):
    user,h=learner(database,actor);conn=database[1];paper,ids=seed(database,n);exam='checkin-'+uuid4().hex
    conn.execute("INSERT INTO collections(id,title,kind,live_version) VALUES(%s,'Synthetic primary exam','exam',1)",(exam,))
    conn.execute("INSERT INTO collection_sections(collection_id,version,path,title,position,query) VALUES(%s,1,'papers','Synthetic papers',0,'{}')",(exam,))
    conn.execute("INSERT INTO collection_papers(collection_id,version,paper_id,section_path) VALUES(%s,1,%s,'papers')",(exam,paper))
    topics={}
    for subject in ('english','mizo'):
        topic=subject+'/'+uuid4().hex;topics[subject]=topic
        conn.execute("INSERT INTO review_taxonomy(id,label,parent_id,level,version) VALUES(%s,%s,%s,'topic','synthetic')",(topic,'Synthetic '+subject,subject))
    for i,qid in enumerate(ids):
        subject='english' if i%2 else 'mizo'
        conn.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,topic_id,topic_label,taxonomy_version,source,review_status) VALUES(%s,%s,%s,%s,'Synthetic topic','synthetic','manual','approved')",(qid,subject,subject,topics[subject]))
    assert client.put('/api/me/exam-bookmarks/'+exam+'/primary',headers=h).status_code==200
    return user,h,exam,ids,paper


def start(client,h,exam,key=None):
    return client.post('/api/me/onboarding',headers=h,json={'request_key':key or uuid4().hex,'collection_id':exam})


def finish(client,h,state,wrong=False):
    for pos,qid in enumerate(state['question_ids']):
        if state['position']!=pos:
            r=client.post('/api/study-sessions/'+state['id']+'/position',headers=h,json={'version':state['version'],'position':pos});assert r.status_code==200,r.text;state.update(r.json())
        q=next(q for q in state['items'] if q['id']==qid)
        r=client.post('/api/study-sessions/'+state['id']+'/answer',headers=h,json={'version':state['version'],'question_id':qid,'chosen_index':0 if wrong else 1,'presentation_hash':q['presentation_hash']})
        assert r.status_code==200,r.text;state.update(r.json())
    r=client.post('/api/study-sessions/'+state['id']+'/finish',headers=h,json={'version':state['version']});assert r.status_code==200,r.text;state.update(r.json());return state


def test_optional_private_status_and_normal_practice_mastery_flow(client,actor,database):
    user,h,exam,ids,paper=setup(client,actor,database);conn=database[1]
    before=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    r=client.get('/api/me/onboarding',headers=h);assert r.status_code==200,r.text
    assert r.json()['available'] and r.json()['session'] is None
    assert r.headers['cache-control']=='private, no-store' and 'etag' not in r.headers
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==before
    assert conn.execute('SELECT count(*) FROM practice_study_sessions WHERE user_id=%s',(user,)).fetchone()[0]==0
    key=uuid4().hex;r=start(client,h,exam,key);assert r.status_code==200,r.text;state=r.json()
    assert state['kind']=='practice' and state['total']==10 and len(set(state['question_ids']))==10
    assert {q['taxonomy_subject_id'] for q in state['items']}=={'english','mizo'}
    assert not any(x in r.text for x in ('answer_text','explanation','answer_index'))
    assert start(client,h,exam,key).json()['id']==state['id'] and start(client,h,exam).json()['id']==state['id']
    assert state['id'] not in [s['id'] for s in client.get('/api/study-sessions?collection_id='+exam,headers=h).json()['items']]
    final=finish(client,h,state,wrong=True)
    attempts=conn.execute("SELECT id,context FROM attempts WHERE user_id=%s",(user,)).fetchall()
    assert len(attempts)==10 and {a[1] for a in attempts}=={'practice'}
    mastery=client.get('/api/me/mastery',headers=h).json()['items'];assert sum(m['distinct_attempted'] for m in mastery)==10
    summary=client.get('/api/me/onboarding/'+state['id']+'/summary',headers=h);assert summary.status_code==200,summary.text
    assert set(summary.json()['suggested_subject_ids'])=={'english','mizo'}
    assert sum(s['checked'] for s in summary.json()['subjects'])==10
    assert conn.execute('SELECT count(*) FROM user_focus_subjects WHERE user_id=%s',(user,)).fetchone()[0]==0
    count=conn.execute('SELECT count(*) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()[0]
    assert start(client,h,exam).json()['id']==state['id']
    replay=client.post('/api/study-sessions/'+state['id']+'/finish',headers=h,json={'version':1});assert replay.status_code==200
    assert conn.execute('SELECT count(*) FROM attempts WHERE user_id=%s',(user,)).fetchone()[0]==10
    assert conn.execute('SELECT count(*) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()[0]==count
    assert not any('onboarding' in str(r) for r in conn.execute('SELECT kind,event_key FROM reward_ledger WHERE user_id=%s',(user,)).fetchall())


def test_no_primary_small_or_ineligible_pool_never_starts_short_quiz(client,actor,database):
    user,h=learner(database,actor)
    assert client.get('/api/me/onboarding',headers=h).json()['exam'] is None
    user,h,exam,ids,paper=setup(client,actor,database,9)
    assert not client.get('/api/me/onboarding',headers=h).json()['available']
    assert start(client,h,exam).status_code==422
    database[1].execute("UPDATE canonical_questions SET answer_source='inferred' WHERE id=ANY(%s)",(ids,))
    assert start(client,h,exam).status_code==422


def test_primary_switch_and_request_identity_are_bound(client,actor,database):
    user,h,exam,ids,paper=setup(client,actor,database)
    key=uuid4().hex;state=start(client,h,exam,key).json()
    assert client.get('/api/me/onboarding',headers={**h,'X-Learning-User':'other'}).status_code==409
    assert client.put('/api/me/exam-bookmarks/udc/primary',headers=h).status_code==200
    assert start(client,h,exam,key).status_code==409
    assert start(client,h,'udc',key).status_code==409
    assert client.get('/api/study-sessions/'+state['id'],headers=h).status_code==200
    assert client.put('/api/me/exam-bookmarks/'+exam+'/primary',headers=h).status_code==200
    assert start(client,h,exam).json()['id']==state['id']
    other,otherh=learner(database,actor)
    assert client.get('/api/me/onboarding/'+state['id']+'/summary',headers=otherh).status_code==404


def test_concurrent_starts_share_one_saved_set(client,actor,database):
    user,h,exam,ids,paper=setup(client,actor,database)
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows=list(pool.map(lambda _:start(client,h,exam),range(2)))
    assert all(r.status_code==200 for r in rows),[r.text for r in rows]
    assert rows[0].json()['id']==rows[1].json()['id']


def test_pause_preserves_resumption_and_saved_answers(client,actor,database,tmp_path,monkeypatch):
    user,h,exam,ids,paper=setup(client,actor,database);state=start(client,h,exam).json()
    path=tmp_path/'flag.json';monkeypatch.setattr(onboarding_release,'STATE_PATH',path)
    assert not onboarding_release.enabled()
    assert start(client,h,exam).json()['id']==state['id']
    assert client.get('/api/study-sessions/'+state['id'],headers=h).status_code==200
    assert client.put('/api/me/exam-bookmarks/udc/primary',headers=h).status_code==200
    assert start(client,h,'udc').status_code==503
    path.write_text('{"version":true,"writes_enabled":true}')
    assert not onboarding_release.enabled()


def test_native_cannot_open_or_grade_web_checkin(client,actor,database):
    user,h,exam,ids,paper=setup(client,actor,database);state=start(client,h,exam).json()
    mobile,_=connect(client,actor,user)
    for path in ('/api/me/onboarding','/api/me/onboarding/'+state['id']+'/summary','/api/study-sessions/'+state['id']):
        assert client.get(path,headers=mobile).status_code==403
    assert client.post('/api/study-sessions',headers=mobile,json={'request_key':uuid4().hex,'collection_id':exam,'review_session_id':state['id']}).status_code==403
    for action,body in [('position',{'version':1,'position':1}),('answer',{'version':1,'question_id':state['question_ids'][0],'chosen_index':1}),('finish',{'version':1})]:
        assert client.post('/api/study-sessions/'+state['id']+'/'+action,headers=mobile,json=body).status_code==403


def test_guests_and_missing_csrf_cannot_start_and_reads_do_not_create_guests(client,actor,database):
    client.cookies.clear();before=database[1].execute('SELECT count(*) FROM users').fetchone()[0]
    r=client.get('/api/me/onboarding');assert r.status_code==401 and 'ism_guest' not in r.cookies
    assert database[1].execute('SELECT count(*) FROM users').fetchone()[0]==before
    user,h,exam,ids,paper=setup(client,actor,database)
    assert client.post('/api/me/onboarding',headers={'X-Learning-User':user},json={'request_key':uuid4().hex,'collection_id':exam}).status_code==403
    database[1].execute("UPDATE collections SET visibility='hidden' WHERE id=%s",(exam,))
    assert client.get('/api/me/onboarding',headers=h).json()['exam'] is None
    assert start(client,h,exam).status_code==409


def test_suggestions_ignore_viewed_skipped_excluded_and_rekeyed_sources(client,actor,database):
    user,h,exam,ids,paper=setup(client,actor,database);state=finish(client,h,start(client,h,exam).json(),wrong=True);conn=database[1]
    qid=state['question_ids'][0]
    aid=conn.execute('SELECT id FROM attempts WHERE user_id=%s AND canonical_id=%s',(user,qid)).fetchone()[0]
    conn.execute("INSERT INTO attempt_assessments(attempt_id,input_hash,policy_version,payload) VALUES(%s,%s,'synthetic',%s)",(aid,uuid4().hex,Jsonb({'outcome':'excluded'})))
    summary=client.get('/api/me/onboarding/'+state['id']+'/summary',headers=h).json()
    assert sum(s['checked'] for s in summary['subjects'])==9
    conn.execute("UPDATE canonical_questions SET status='held' WHERE id=%s",(state['question_ids'][1],))
    summary=client.get('/api/me/onboarding/'+state['id']+'/summary',headers=h).json()
    assert sum(s['checked'] for s in summary['subjects'])==8
    # An empty finished check-in does not invent weaker subjects.
    user2,h2=learner(database,actor);assert client.put('/api/me/exam-bookmarks/'+exam+'/primary',headers=h2).status_code==200
    state2=start(client,h2,exam).json();r=client.post('/api/study-sessions/'+state2['id']+'/finish',headers=h2,json={'version':state2['version']});assert r.status_code==200,r.text
    summary=client.get('/api/me/onboarding/'+state2['id']+'/summary',headers=h2).json()
    assert summary['subjects']==[] and summary['suggested_subject_ids']==[]
