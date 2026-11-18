"""Reviewed editorial practice with exact receipts, no canonical/award fabrication."""
from uuid import uuid4
import copy
from test_content_studio import publish
from test_curated_vocabulary_authoring import deck,card
from test_learning_workflows import learner
import pytest

@pytest.fixture(autouse=True)
def curated_real_role(monkeypatch):
    from contextlib import asynccontextmanager
    from app.db import cursor
    from app.routers import vocabulary,learning_loop,study_sessions,materials,creators
    @asynccontextmanager
    async def role_cursor():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            yield cur
    for module in (vocabulary,learning_loop,study_sessions,materials,creators):monkeypatch.setattr(module,'cursor',role_cursor)


def ready(client,actor,database,n=1,access='free'):
    doc=deck(access);doc['blocks']=[]
    for i in range(n):
        value=card();value.update(word='synthetic'+str(i),cloze_options=['synthetic'+str(i),'other'],cloze_sentence='Use {{word}} for this fixture.',mizo_options=['Mizo test gloss, not learning content','Other test gloss'])
        doc['blocks'].append({'id':'word'+str(i),'type':'vocabulary','vocabulary':value})
    mid=publish(client,actor,doc)
    user,h=learner(database,actor);return mid,user,{**h,'x-vocabulary-user':user,'x-finna-review-items':'curated-v1'}

def next_word(client,h,mid,**kw):
    r=client.post('/api/vocabulary/curated/card?exam_scope=all',headers=h,json={'deck_id':mid,**kw});assert r.status_code==200,r.text
    return r.json()['card']

def answer(client,h,c,index=0,action='answer'):
    return client.post('/api/vocabulary/curated/cards/'+c['id']+'/answer',headers=h,json={'chosen_index':index,'action':action})

def test_curated_publication_roles_modes_receipts_and_no_per_card_points(client,actor,database):
    conn=database[1];mid,user,h=ready(client,actor,database)
    before=conn.execute('SELECT count(*) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()[0]
    assert before==0
    data=client.get('/api/vocabulary/curated/decks?exam_scope=all').json();item=next(x for x in data['items'] if x['id']==mid)
    assert item['eligible_cards']==item['eligible_words']==1 and item['known']==0
    for mode in ['recognition','cloze','mizo-to-english','english-to-mizo']:
        if mode!='recognition':
            conn.execute("UPDATE review_items SET due_on=(now() AT TIME ZONE 'Asia/Kolkata')::date WHERE user_id=%s AND vocab_card_id IS NOT NULL",(user,))
        c=next_word(client,h,mid,mode=mode);assert c['source']=='reviewed-editorial'
        assert 'answer_text' not in c and 'meaning' not in c
        r=answer(client,h,c);assert r.status_code==200,r.text
        assert r.json()['correct'] and r.json()['points']==r.json()['xp']==0 and r.json()['stage']==1
        assert answer(client,h,c).json()==r.json()
        assert answer(client,h,c,1).status_code==409
    assert conn.execute('SELECT count(*) FROM vocab_attempts WHERE user_id=%s',(user,)).fetchone()[0]==4
    assert conn.execute('SELECT count(*) FROM attempts WHERE user_id=%s',(user,)).fetchone()[0]==0
    assert conn.execute('SELECT count(*) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()[0]==before
    assert client.post('/api/vocabulary/curated/card',headers={**h,'x-vocabulary-user':'other'},json={}).status_code==409
    assert client.get('/api/vocabulary/curated/decks').headers['cache-control']=='private, no-store'


def test_curated_scope_block_entitlement_source_change_and_cross_account_boundaries(client,actor,database):
    conn=database[1];mid,user,h=ready(client,actor,database,access='pro')
    assert next_word(client,h,mid) is None
    conn.execute("UPDATE users SET plan_code='pro',plan_status='trial',trial_ends_at=now()+interval '1 day' WHERE id=%s",(user,))
    c=next_word(client,h,mid);assert c
    other,oh=learner(database,actor);oh={**oh,'x-vocabulary-user':other}
    assert answer(client,oh,c).status_code==404
    actor(user);conn.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,\'author\')',(user,))
    assert answer(client,h,c).status_code==404
    conn.execute('DELETE FROM creator_blocks WHERE user_id=%s',(user,))
    conn.execute("UPDATE users SET trial_ends_at=now()-interval '1 day' WHERE id=%s",(user,))
    assert answer(client,h,c).status_code==404
    from app.services.mobile_identity import allowed
    assert not allowed('GET','/api/vocabulary/curated/decks') and not allowed('POST','/api/vocabulary/curated/card')


def test_curated_grading_and_own_material_publication_share_lock_order(client,actor,database,monkeypatch):
    import psycopg
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from app.services import curated_practice
    mid,_,_=ready(client,actor,database)
    h={**actor('author'),'x-vocabulary-user':'author'};c=next_word(client,h,mid)
    before_source=Event();original=curated_practice.available
    async def available(cur,user,card,scope='all',lock=False):
        if lock:before_source.set()
        return await original(cur,user,card,scope,lock)
    monkeypatch.setattr(curated_practice,'available',available)
    with psycopg.connect('dbname='+database[0],options='-c role=mpsc -c lock_timeout=2000') as publisher:
        with ThreadPoolExecutor(max_workers=1) as pool:
            publisher.execute('SELECT id FROM materials WHERE id=%s FOR UPDATE',(mid,))
            pending=pool.submit(answer,client,h,c)
            try:
                assert before_source.wait(5)
                # This is the lock publication takes after locking the material.
                # The grade must still be waiting for the material, holding no
                # conflicting author habit lock. No publication is fabricated.
                publisher.execute('SELECT learning_habit_lock(%s)',('author',))
            finally:publisher.rollback()
            result=pending.result(timeout=5)
            assert result.status_code==200,result.text


def test_curated_five_new_limit_is_rechecked_at_grade_and_due_reviews_do_not_consume_it(client,actor,database):
    conn=database[1];mid,user,h=ready(client,actor,database,n=6)
    ids=[r[0] for r in conn.execute('SELECT id FROM vocab_cards WHERE deck_id=%s ORDER BY block_id',(mid,)).fetchall()]
    pending=[next_word(client,h,mid,card_id=q) for q in ids]
    for c in pending[:5]:assert answer(client,h,c).status_code==200
    assert answer(client,h,pending[5]).status_code==409
    assert conn.execute('SELECT count(*) FROM vocab_attempts WHERE user_id=%s',(user,)).fetchone()[0]==5
    conn.execute("UPDATE review_items SET due_on=(now() AT TIME ZONE 'Asia/Kolkata')::date WHERE user_id=%s AND vocab_card_id IS NOT NULL",(user,))
    conn.execute("UPDATE vocab_exposures SET last_exposure_at=now()-interval '2 days' WHERE user_id=%s AND first_review_at IS NOT NULL",(user,))
    for q in ids[:5]:
        c=next_word(client,h,mid,card_id=q);r=answer(client,h,c);assert r.status_code==200 and r.json()['stage']==2,r.text
    assert conn.execute('SELECT count(*) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()[0]==0


def test_curated_current_publication_invalidates_old_source_and_word_identity(client,actor,database):
    from test_curated_vocabulary_authoring import deck
    conn=database[1];mid,user,h=ready(client,actor,database)
    c=next_word(client,h,mid)
    ah=actor('author');draft=client.get('/api/studio/materials/'+mid).json();doc=draft['document']
    doc['blocks'][0]['vocabulary']['meaning']='A revised synthetic meaning'
    doc['blocks'][0]['vocabulary']['recognition_options']=['A revised synthetic meaning','Other']
    assert client.post('/api/studio/materials/'+mid+'/save',headers=ah,json={'expected_version':draft['lock_version'],'document':doc}).status_code==200
    assert client.post('/api/studio/materials/'+mid+'/submit',headers=ah,json={'expected_version':draft['lock_version']+1}).status_code==200
    oh=actor('owner');r=client.post('/api/admin/bank/content/'+mid+'/review',headers=oh,json={'expected_version':draft['lock_version']+2,'decision':'publish'});assert r.status_code==200,r.text
    actor(user);assert answer(client,h,c).status_code==409
    assert conn.execute('SELECT count(*) FROM vocab_attempts WHERE user_id=%s',(user,)).fetchone()[0]==0
    fresh=next_word(client,h,mid);assert fresh['id']!=c['id'] and fresh['card_id']==c['card_id']
    result=answer(client,h,fresh);assert result.status_code==200 and result.json()['stage']==1
    # Every result and definition is append-only; a changed approved definition
    # does not edit an earlier presentation or manufacture a canonical attempt.
    import psycopg,pytest
    with pytest.raises(psycopg.errors.RaiseException):conn.execute('UPDATE vocab_attempts SET correct=false WHERE user_id=%s',(user,))
    with pytest.raises(psycopg.errors.RaiseException):conn.execute("UPDATE vocab_card_revisions SET payload='{}' WHERE card_id=%s",(c['card_id'],))
    with pytest.raises(psycopg.errors.RaiseException):conn.execute("UPDATE vocab_presentations SET result='{}' WHERE id=%s",(fresh['id'],))


def test_curated_graduation_nullable_due_wrong_restart_and_write_quarantine(client,actor,database,tmp_path,monkeypatch):
    from app.services import curated_release
    conn=database[1];mid,user,h=ready(client,actor,database)
    c=next_word(client,h,mid);wrong=answer(client,h,c,1);assert wrong.status_code==200 and wrong.json()['stage']==0
    assert conn.execute("SELECT box,last_result FROM review_items WHERE user_id=%s AND vocab_card_id=%s",(user,c['card_id'])).fetchone()==(1,False)
    conn.execute("UPDATE review_items SET box=5,due_on=(now() AT TIME ZONE 'Asia/Kolkata')::date WHERE user_id=%s AND vocab_card_id=%s",(user,c['card_id']))
    conn.execute("UPDATE vocab_exposures SET last_exposure_at=now()-interval '2 days' WHERE user_id=%s",(user,))
    c=next_word(client,h,mid);r=answer(client,h,c);assert r.status_code==200,r.text
    assert r.json()['graduated'] and r.json()['stage']==6 and r.json()['next_due'] is None
    item=next(x for x in client.get('/api/vocabulary/curated/decks?exam_scope=all').json()['items'] if x['id']==mid)
    assert item['known']==1 and item['due']==0
    flag=tmp_path/'writes.json';flag.write_text('{"version":1,"writes_enabled":false}');monkeypatch.setattr(curated_release,'STATE_PATH',flag)
    assert answer(client,h,c).json()==r.json()
    assert client.post('/api/vocabulary/curated/card',headers=h,json={'deck_id':mid}).status_code==503
    resumed=client.post('/api/vocabulary/curated/card',headers=h,json={'deck_id':mid,'resume_id':c['id']});assert resumed.status_code==200 and resumed.json()['result']==r.json()
    assert client.get('/api/vocabulary/curated/decks').status_code==200
    flag.write_text('{"version":true,"writes_enabled":true}');assert not curated_release.enabled()
    flag.unlink();assert not curated_release.enabled()


def due_words(conn,user,mid):
    rows=conn.execute('SELECT id,content_hash FROM v_curated_vocabulary WHERE deck_id=%s ORDER BY id',(mid,)).fetchall()
    for cid,fingerprint in rows:
        conn.execute("INSERT INTO vocab_exposures(user_id,card_id,content_hash,seen,first_review_at,last_exposure_at) VALUES(%s,%s,%s,1,now()-interval '2 days',now()-interval '2 days') ON CONFLICT DO NOTHING",(user,cid,fingerprint))
        conn.execute("INSERT INTO review_items(user_id,item_type,item_id,canonical_id,vocab_card_id,vocab_content_hash,box,due_on,last_result) VALUES(%s,'vocab',%s,NULL,%s,%s,1,(now() AT TIME ZONE 'Asia/Kolkata')::date,false) ON CONFLICT DO NOTHING",(user,cid,cid,fingerprint))
    return [r[0] for r in rows]


def word_set(client,h,conn,mid,size=8,correct=8,timed=True,backtrack=False):
    r=client.post('/api/review-sessions',headers=h,json={'request_key':uuid4().hex,'size':size,'item_type':'vocab','deck_id':mid});assert r.status_code==200,r.text
    state=r.json();url='/api/study-sessions/'+state['id']
    assert state['filters']['has_curated'] and all(q.get('curated') for q in state['items'])
    for i,cid in enumerate(state['question_ids']):
        if i:state=client.post(url+'/position',headers=h,json={'version':state['version'],'position':i}).json()
        if timed:conn.execute("UPDATE vocab_review_session_items SET opened_at=clock_timestamp()-interval '4 seconds' WHERE session_id=%s AND card_id=%s",(state['id'],cid))
        r=client.post(url+'/answer',headers=h,json={'version':state['version'],'question_id':cid,'chosen_index':0 if i<correct else 1});assert r.status_code==200,r.text
        state=r.json()
    if backtrack:
        r=client.post(url+'/position',headers=h,json={'version':state['version'],'position':0});assert r.status_code==200,r.text
        state=r.json()
    r=client.post(url+'/finish',headers=h,json={'version':state['version']});assert r.status_code==200,r.text
    return r.json()


def test_curated_saved_sets_share_award_slots_xp_caps_and_plan_ring_with_canonical_reviews(client,actor,database):
    conn=database[1];mid,user,h=ready(client,actor,database,n=24);ids=due_words(conn,user,mid)
    queue=client.get('/api/me/review-queue',headers=h).json();assert queue['due_count']==queue['vocabulary_due_count']==queue['curated_due_count']==24
    today=client.get('/api/me/today',headers=h).json();assert today['vocabulary']['due']==24 and today['vocabulary']['url']=='/revise?item_type=vocab'
    day=conn.execute("SELECT (now() AT TIME ZONE 'Asia/Kolkata')::date").fetchone()[0]
    from datetime import timedelta
    layers=client.get('/api/me/calendar-layers',headers=h,params={'start':day.isoformat(),'end':(day+timedelta(days=1)).isoformat()}).json()
    assert sum(x['count'] for x in layers['forecast'])==24
    for n in range(3):
        if n==1:conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note) VALUES(%s,%s,'study',273,0,'Synthetic shared XP remainder')",(user,uuid4().hex))
        done=word_set(client,h,conn,mid,backtrack=True);reward=done['summary']['reward']
        assert reward['status']==('daily_cap' if n==2 else 'awarded'),reward
        assert (reward['xp'],reward['points'])==((0,0) if n==2 else (7,2) if n==1 else (20,2))
        assert client.post('/api/study-sessions/'+done['id']+'/finish',headers=h,json={'version':1}).json()['summary']==done['summary']
    assert conn.execute('SELECT count(*) FROM review_session_rewards WHERE user_id=%s',(user,)).fetchone()[0]==2
    assert conn.execute('SELECT count(*) FROM vocab_review_completions WHERE user_id=%s',(user,)).fetchone()[0]==24
    assert conn.execute('SELECT count(*) FROM attempts WHERE user_id=%s',(user,)).fetchone()[0]==0
    assert conn.execute("SELECT sum(xp) FROM reward_ledger WHERE user_id=%s AND kind IN ('study','game')",(user,)).fetchone()[0]==300
    plan=client.get('/api/me/today',headers=h).json()['plan_status'];review=next(x for x in plan['tasks'] if x['key']=='reviews')
    assert review['progress']==review['target']==24


def test_curated_review_fast_wrong_and_duplicate_occurrences_do_not_pay(client,actor,database):
    conn=database[1]
    for correct,timed in [(8,False),(4,True)]:
        mid,user,h=ready(client,actor,database,n=8);due_words(conn,user,mid)
        done=word_set(client,h,conn,mid,correct=correct,timed=timed)
        assert done['summary']['reward']['status']=='not_eligible'
        assert conn.execute('SELECT count(*) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()[0]==0
    mid,user,h=ready(client,actor,database,n=8);due_words(conn,user,mid)
    pending=client.post('/api/review-sessions',headers=h,json={'request_key':uuid4().hex,'size':8,'deck_id':mid}).json()
    done=word_set(client,h,conn,mid);assert done['summary']['reward']['status']=='awarded'
    # The second frozen occurrence can record real checks, but cannot pay again.
    state=pending;url='/api/study-sessions/'+state['id']
    for i,cid in enumerate(state['question_ids']):
        if i:state=client.post(url+'/position',headers=h,json={'version':state['version'],'position':i}).json()
        conn.execute("UPDATE vocab_review_session_items SET opened_at=clock_timestamp()-interval '4 seconds' WHERE session_id=%s AND card_id=%s",(state['id'],cid))
        r=client.post(url+'/answer',headers=h,json={'version':state['version'],'question_id':cid,'chosen_index':0});assert r.status_code==200,r.text
        state=r.json()
    r=client.post(url+'/finish',headers=h,json={'version':state['version']});assert r.status_code==200,r.text
    assert r.json()['summary']['reward']['status']=='not_eligible'
    assert conn.execute('SELECT count(*) FROM review_session_rewards WHERE user_id=%s',(user,)).fetchone()[0]==1


def test_mixed_review_uses_one_session_one_award_and_private_source_kinds(client,actor,database):
    from test_learning_loop import questions,due
    conn=database[1];mid,user,h=ready(client,actor,database,n=4);words=due_words(conn,user,mid)
    _,bank=questions(database,4);due(conn,user,bank)
    r=client.post('/api/review-sessions',headers=h,json={'request_key':uuid4().hex,'size':8});assert r.status_code==200,r.text
    state=r.json();url='/api/study-sessions/'+state['id']
    assert set(state['question_ids'])==set(words+bank)
    legacy={k:v for k,v in h.items() if k!='x-finna-review-items'}
    key=conn.execute('SELECT request_key FROM practice_study_sessions WHERE id=%s',(state['id'],)).fetchone()[0]
    assert client.post('/api/review-sessions',headers=legacy,json={'request_key':key,'size':8}).status_code==409
    legacy_queue=client.get('/api/me/review-queue',headers=legacy).json()
    assert {x['item_id'] for x in legacy_queue['items']}==set(bank)
    assert sum(bool(q.get('curated')) for q in state['items'])==4
    for i,cid in enumerate(state['question_ids']):
        if i:state=client.post(url+'/position',headers=h,json={'version':state['version'],'position':i}).json()
        if cid in words:
            conn.execute("UPDATE vocab_review_session_items SET opened_at=clock_timestamp()-interval '4 seconds' WHERE session_id=%s AND card_id=%s",(state['id'],cid));pick=0
        else:
            conn.execute("UPDATE review_session_items SET opened_at=clock_timestamp()-interval '4 seconds' WHERE session_id=%s AND canonical_id=%s",(state['id'],cid));pick=1
        displayed=client.get(url,headers=h).json()
        item=next(q for q in displayed['items'] if q['id']==cid)
        r=client.post(url+'/answer',headers=h,json={'version':state['version'],'question_id':cid,'chosen_index':pick,'presentation_hash':item.get('presentation_hash')});assert r.status_code==200,r.text
        state=r.json()
    r=client.post(url+'/finish',headers=h,json={'version':state['version']});assert r.status_code==200,r.text
    summary=r.json()['summary'];assert summary['reward']['points']==2 and summary['curated_checked']==4 and summary['correct']==8
    assert conn.execute('SELECT count(*) FROM review_session_rewards WHERE user_id=%s',(user,)).fetchone()[0]==1
    assert conn.execute("SELECT count(*) FROM attempts WHERE user_id=%s AND context='review'",(user,)).fetchone()[0]==4
    assert conn.execute('SELECT count(*) FROM vocab_attempts WHERE user_id=%s',(user,)).fetchone()[0]==4


def test_bank_and_curated_introductions_share_five_places_even_with_old_open_cards(client,actor,database):
    from test_vocabulary import seed
    from test_vocabulary_decks import prepare
    conn=database[1];prepare(conn);bank=seed(conn,1)[0];mid,user,h=ready(client,actor,database,n=5)
    r=client.post('/api/vocabulary/card?exam_scope=all',headers=h,json={'question_id':bank});assert r.status_code==200,r.text
    pending=r.json()['card'];assert pending
    for _ in range(5):
        c=next_word(client,h,mid);assert c;assert answer(client,h,c).status_code==200
    r=client.post('/api/vocabulary/cards/'+pending['id']+'/answer',headers=h,json={'chosen_index':1,'action':'answer'});assert r.status_code==409,r.text
    assert client.post('/api/vocabulary/card?exam_scope=all',headers=h,json={}).json()['card'] is None
    assert conn.execute('SELECT count(*) FROM attempts WHERE user_id=%s',(user,)).fetchone()[0]==0
    today=client.get('/api/me/today',headers=h).json()['vocabulary'];assert today['introduced']==5 and today['remaining']==0


def test_curated_saved_reveals_and_quarantine_keep_canonical_reviews_available(client,actor,database,tmp_path,monkeypatch):
    from app.services import curated_release
    from test_learning_loop import questions,due
    from app.services.curated_sessions import native_guard
    from app.services.mobile_identity import allowed
    from fastapi import HTTPException
    from types import SimpleNamespace
    import pytest
    conn=database[1];mid,user,h=ready(client,actor,database,n=24);due_words(conn,user,mid)
    r=client.post('/api/review-sessions',headers=h,json={'request_key':uuid4().hex,'size':8,'deck_id':mid});assert r.status_code==200,r.text
    state=r.json();cid=state['question_ids'][0];url='/api/study-sessions/'+state['id']
    assert not allowed('POST',url+'/word-reveal')
    with pytest.raises(HTTPException) as blocked:native_guard({'filters':{'has_curated':True}},SimpleNamespace(state=SimpleNamespace(mobile_session={'id':'synthetic'})))
    assert blocked.value.status_code==403
    r=client.post(url+'/word-reveal',headers=h,json={'version':state['version'],'question_id':cid});assert r.status_code==200,r.text
    state=r.json();assert cid in state['viewed_ids'] and state['summary']['viewed']==1 and state['summary']['correct']==0
    assert client.get(url).status_code==409
    assert client.get(url,headers=h).json()['items'][0]['curated']['revealed_result']['outcome']=='reveal'
    _,bank=questions(database,8);due(conn,user,bank)
    flag=tmp_path/'writes.json';flag.write_text('{"version":1,"writes_enabled":false}');monkeypatch.setattr(curated_release,'STATE_PATH',flag)
    # More than20old word dues cannot hide the8canonical questions in recovery.
    r=client.post('/api/review-sessions',headers=h,json={'request_key':uuid4().hex,'size':8});assert r.status_code==200,r.text
    assert set(r.json()['question_ids'])==set(bank) and not r.json()['filters']['has_curated']
    assert client.post('/api/review-sessions',headers=h,json={'request_key':uuid4().hex,'deck_id':mid}).status_code==503


def test_curated_mastery_needs_twenty_current_words_and_exact_finished_delayed_review(client,actor,database):
    conn=database[1];mid,user,h=ready(client,actor,database,n=20);ids=due_words(conn,user,mid)
    for cid in ids:
        c=next_word(client,h,mid,card_id=cid);assert answer(client,h,c).status_code==200
    item=lambda:next(x for x in client.get('/api/vocabulary/curated/decks?exam_scope=all').json()['items'] if x['id']==mid)
    assert item()['attempted']==item()['correct_latest']==20 and item()['state']=='proficient' and item()['known']==0
    conn.execute("UPDATE user_vocab_deck_mastery SET proficient_at=now()-interval '15 days' WHERE user_id=%s AND deck_id=%s",(user,mid))
    conn.execute("UPDATE review_items SET due_on=(now() AT TIME ZONE 'Asia/Kolkata')::date WHERE user_id=%s AND vocab_card_id=%s",(user,ids[0]))
    conn.execute("UPDATE vocab_exposures SET last_exposure_at=now()-interval '2 days' WHERE user_id=%s",(user,))
    state=client.post('/api/review-sessions',headers=h,json={'request_key':uuid4().hex,'deck_id':mid,'size':1}).json();sid=state['id'];cid=state['question_ids'][0]
    r=client.post('/api/study-sessions/'+sid+'/answer',headers=h,json={'version':state['version'],'question_id':cid,'chosen_index':0});assert r.status_code==200,r.text
    state=r.json();assert item()['state']=='proficient','An unfinished set is not delayed mastery proof'
    finished=client.post('/api/study-sessions/'+sid+'/finish',headers=h,json={'version':state['version']});assert finished.status_code==200,finished.text
    assert finished.json()['summary']['reward']['status']=='not_eligible'
    assert item()['state']=='mastered','Mastery proof is distinct from currency eligibility'
    # A receipt outside its frozen question membership is not proof.
    conn.execute('UPDATE practice_study_sessions SET question_ids=%s WHERE id=%s',([ids[1]],sid))
    assert item()['state']=='proficient'
    conn.execute('UPDATE practice_study_sessions SET question_ids=%s WHERE id=%s',([cid],sid))
    assert item()['state']=='mastered'


def test_native_transport_keeps_word_endpoints_and_mixed_sets_closed(client,actor,database):
    from test_mobile_companion import connect
    from test_learning_loop import questions,due
    conn=database[1];mid,user,web=ready(client,actor,database,n=8);due_words(conn,user,mid)
    _,ids=questions(database,2);due(conn,user,ids)
    mixed=client.post('/api/review-sessions',headers=web,json={'request_key':uuid4().hex,'size':10}).json()
    headers,_=connect(client,actor,user)
    assert client.get('/api/vocabulary/curated/decks',headers=headers).status_code==403
    assert client.post('/api/vocabulary/curated/card',headers=headers,json={'deck_id':mid}).status_code==403
    assert client.get('/api/study-sessions/'+mixed['id'],headers=headers).status_code==403
    assert client.get('/api/me/review-queue',headers=headers).json()['due_count']==2
    assert client.get('/api/me/review-queue?deck_id='+mid,headers=headers).status_code==403
    compose=headers|{'X-Finna-Capability':'review_sessions'}
    r=client.post('/api/review-sessions',headers=compose,json={'request_key':uuid4().hex});assert r.status_code==200,r.text
    assert set(r.json()['question_ids'])==set(ids) and not r.json()['filters']['has_curated']
    assert client.post('/api/review-sessions',headers=compose,json={'request_key':uuid4().hex,'deck_id':mid}).status_code==403


def test_curated_diagnostics_detect_forged_grades_and_per_card_claims_without_persisting_them(client,actor,database):
    import asyncio,psycopg
    from psycopg.rows import dict_row
    from psycopg.types.json import Jsonb
    from app.services import reward_economy
    mid,user,h=ready(client,actor,database)
    c=next_word(client,h,mid);assert answer(client,h,c).status_code==200
    async def probe():
        async with await psycopg.AsyncConnection.connect('dbname='+database[0],options='-c role=mpsc',row_factory=dict_row) as connection:
            async with connection.cursor() as cur:
                initial=await reward_economy.diagnostics(cur);assert all(initial[k]==0 for k in reward_economy.INTEGRITY_FIELDS)
                async with connection.transaction(force_rollback=True):
                    await cur.execute('SELECT * FROM vocab_presentations WHERE id=%s',(c['id'],));original=await cur.fetchone()
                    snapshot=copy.deepcopy(original['snapshot']);snapshot['card']['word']='FORGED_SOURCE'
                    pid='vp_fake_'+uuid4().hex;response={'correct':True}
                    await cur.execute('SELECT clock_timestamp() AS at');stamp=(await cur.fetchone())['at']
                    await cur.execute('''INSERT INTO vocab_presentations(id,user_id,card_id,revision,content_hash,state_version,mode,snapshot,answered_at,action,chosen_index,result)
                      VALUES(%s,%s,%s,%s,%s,1,'recognition',%s,%s,'answer',1,%s)''',(pid,user,c['card_id'],original['revision'],original['content_hash'],Jsonb(snapshot),stamp,Jsonb(response)))
                    await cur.execute('''INSERT INTO vocab_attempts(user_id,card_id,revision,content_hash,mode,chosen_index,chosen_text,correct,presentation_id,at)
                      VALUES(%s,%s,%s,%s,'recognition',1,%s,true,%s,%s)''',(user,c['card_id'],original['revision'],original['content_hash'],snapshot['options'][1],pid,stamp))
                    await cur.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note) VALUES(%s,%s,'study',0,1,'Disposable forged per-card claim')",(user,'question:'+user+':'+c['card_id']))
                    bad=await reward_economy.diagnostics(cur)
                    assert bad['curated_grade_receipt_mismatches']==1 and bad['curated_per_card_claims']==1
                restored=await reward_economy.diagnostics(cur);assert all(restored[k]==0 for k in reward_economy.INTEGRITY_FIELDS)
                assert len(reward_economy.INTEGRITY_FIELDS)==25
    asyncio.run(probe())
