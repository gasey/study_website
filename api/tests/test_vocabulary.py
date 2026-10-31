"""Automatic recognition evidence, source safety and durable account scheduling."""
from datetime import datetime,timedelta,timezone
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from psycopg.types.json import Jsonb
from app.routers.vocabulary import schedule

def seed(conn,count=3,outside=False):
    tag=uuid4().hex[:8];pid='vocab-paper-'+tag;ids=[]
    conn.execute("INSERT INTO papers(id,exam_name,exam_type,year,source_file,exam_scope_id) VALUES (%s,'Synthetic vocabulary source','Direct',2026,'Old_Questions/test.pdf',%s)",(pid,'outside-mizoram' if outside else 'mizoram-recruitment'))
    conn.execute("INSERT INTO review_taxonomy(id,label,level,parent_id,version) VALUES ('english/vocabulary','Vocabulary','topic','english','test') ON CONFLICT DO NOTHING")
    for n in range(count):
        qid='cq_vocab_'+tag+'_'+str(n);ids.append(qid);text='Choose the synonym of the synthetic word '+str(n)
        conn.execute("INSERT INTO canonical_questions(id,type,question,question_markup,options,answer_text,answer_source) VALUES (%s,'mcq',%s,%s,%s,'B','official')",(qid,text,'Choose the **synonym** of the synthetic word '+str(n),Jsonb(['A','B','C','D'])))
        conn.execute("INSERT INTO appearances(id,paper_id,canonical_id,is_primary,type,question,question_markup,options,answer_index,answer_source,direction) VALUES (%s,%s,%s,true,'mcq',%s,%s,%s,1,'official','Select the synonym.')",('a_'+qid,pid,qid,text,'Choose the **synonym** of the synthetic word '+str(n),Jsonb(['A','B','C','D'])))
        conn.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,topic_id,topic_label,taxonomy_version,source,review_status) VALUES (%s,'english','English','english/vocabulary','Vocabulary','test','manual','approved')",(qid,))
    return ids

def who(actor,user='author'):return {**actor(user),'x-vocabulary-user':user}
def card(client,h,scope='mizoram-recruitment'):
    r=client.post('/api/vocabulary/card?exam_scope='+scope,headers=h,json={});assert r.status_code==200,r.text
    return r.json()['card']
def pick(client,h,c,answer='B'):
    return client.post('/api/vocabulary/cards/'+c['id']+'/answer',headers=h,json={'action':'answer','chosen_index':c['question']['options'].index(answer)})

def test_automatic_review_is_private_replay_safe_and_updates_once(client,actor,database):
    conn=database[1];ids=seed(conn);h=who(actor)
    c=card(client,h);assert c['question_id'] in ids
    assert 'answer_text' not in c['question'] and 'explanation' not in c['question']
    assert c['question']['direction']=='Select the synonym.' and '**synonym**' in c['question']['question_markup']
    assert card(client,h)['id']==c['id']
    assert c['question']['options']==['A','B','C','D']
    with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(lambda _:pick(client,h,c),range(2)))
    assert all(r.status_code==200 for r in responses),[r.text for r in responses]
    result=responses[0].json();assert result==responses[1].json() and result['correct'] and result['stage']==1
    assert conn.execute('SELECT count(*) FROM attempts WHERE canonical_id=%s',(c['question_id'],)).fetchone()[0]==1
    restored=client.post('/api/vocabulary/card',headers=h,json={'resume_id':c['id']});assert restored.status_code==200,restored.text
    assert restored.json()['result']==result and restored.json()['restored']
    assert restored.json()['card']['id']==c['id']
    assert pick(client,h,c,'A').status_code==409
    state=conn.execute('SELECT seen,graded,correct,stage FROM vocabulary_state WHERE user_id=\'author\' AND question_id=%s',(c['question_id'],)).fetchone();assert state==(1,1,1,1)
    assert client.get('/api/vocabulary/overview',headers={'x-vocabulary-user':'outsider'}).status_code==409
    other=who(actor,'outsider');assert pick(client,other,c).status_code==404
    assert client.post('/api/vocabulary/card',headers=other,json={'resume_id':c['id']}).json()['card']['id']!=c['id']
    assert client.get('/api/vocabulary/overview').headers['cache-control']=='private, no-store'
    client.cookies.clear();assert client.get('/api/vocabulary/overview').status_code==401

def test_defer_reveal_wrong_and_spaced_success_have_distinct_evidence(client,actor,database):
    conn=database[1];ids=seed(conn,1);h=who(actor,'outsider');c=card(client,h)
    r=client.post('/api/vocabulary/cards/'+c['id']+'/answer',headers=h,json={'action':'defer'});assert r.status_code==200,r.text
    assert r.json()['answer_text'] is None and r.json()['correct'] is None
    assert conn.execute('SELECT graded,lapses FROM vocabulary_state WHERE user_id=\'outsider\' AND question_id=%s',(c['question_id'],)).fetchone()==(0,0)
    conn.execute("UPDATE vocabulary_state SET due_at=now()-interval '1 sec',stage=4 WHERE user_id='outsider' AND question_id=%s",(c['question_id'],))
    c=card(client,h);r=client.post('/api/vocabulary/cards/'+c['id']+'/answer',headers=h,json={'action':'defer'});assert r.json()['stage']==4
    conn.execute("UPDATE vocabulary_state SET due_at=now()-interval '1 sec' WHERE user_id='outsider' AND question_id=%s",(c['question_id'],))
    c=card(client,h);r=client.post('/api/vocabulary/cards/'+c['id']+'/answer',headers=h,json={'action':'reveal'});assert r.json()['answer_text']=='B' and r.json()['stage']==0 and r.json()['correct'] is None
    conn.execute("UPDATE vocabulary_state SET due_at=now()-interval '1 sec' WHERE user_id='outsider' AND question_id=%s",(c['question_id'],))
    c=card(client,h);assert pick(client,h,c,'A').json()['correct'] is False
    conn.execute("UPDATE vocabulary_state SET due_at=now()-interval '1 sec' WHERE user_id='outsider' AND question_id=%s",(c['question_id'],))
    c=card(client,h);assert pick(client,h,c).json()['stage']==1
    conn.execute("UPDATE vocabulary_state SET due_at=now()-interval '1 sec',last_exposure_at=now()-interval '2 days',last_credit_day=current_date-2 WHERE user_id='outsider' AND question_id=%s",(c['question_id'],))
    # A recent Bank/review answer is still an exposure despite an old scheduler timestamp.
    c=card(client,h);assert pick(client,h,c).json()['stage']==1
    conn.execute("UPDATE attempts SET at=now()-interval '2 days' WHERE user_id='outsider' AND canonical_id=%s",(c['question_id'],))
    conn.execute("UPDATE vocabulary_state SET due_at=now()-interval '1 sec',last_exposure_at=now()-interval '2 days',last_credit_day=current_date-2 WHERE user_id='outsider' AND question_id=%s",(c['question_id'],))
    c=card(client,h);assert pick(client,h,c).json()['stage']==2
    assert conn.execute("SELECT graded,correct,lapses FROM vocabulary_state WHERE user_id='outsider' AND question_id=%s",(c['question_id'],)).fetchone()==(4,3,1)

def test_midnight_and_early_success_do_not_manufacture_delayed_mastery():
    now=datetime(2026,10,24,0,1,tzinfo=timezone.utc)
    state={'stage':2,'last_credit_day':now.date()-timedelta(days=1),'last_exposure_at':now-timedelta(minutes=2),'due_at':now-timedelta(seconds=1)}
    assert schedule(state,now.date(),now,True,'answer')[0]==2
    state['last_exposure_at']=now-timedelta(days=2);state['due_at']=now+timedelta(days=1)
    assert schedule(state,now.date(),now,True,'answer')[0]==2
    assert schedule(state,now.date(),now,None,'defer')[0]==2
    assert schedule(state,now.date(),now,None,'reveal')[0]==0

def test_scope_cards_share_progress_and_changed_keys_reset_without_false_wrong(client,actor,database):
    conn=database[1];ids=seed(conn,1);h=who(actor,'owner');a=card(client,h);b=card(client,h,'all');assert a['question_id']==b['question_id']
    assert pick(client,h,a).status_code==200
    assert pick(client,h,b).status_code==409
    conn.execute("UPDATE canonical_questions SET answer_text='A' WHERE id=%s",(a['question_id'],))
    c=card(client,h);assert c and c['question_id']==a['question_id'] and c['stage']==0
    assert pick(client,h,c,'A').json()['correct'] is True
    before=conn.execute('SELECT count(*) FROM attempts WHERE canonical_id=%s',(c['question_id'],)).fetchone()[0]
    conn.execute("UPDATE vocabulary_state SET due_at=now()-interval '1 sec' WHERE user_id='owner' AND question_id=%s",(c['question_id'],))
    d=card(client,h);conn.execute("UPDATE canonical_questions SET answer_text='B' WHERE id=%s",(d['question_id'],))
    assert pick(client,h,d).status_code==409
    assert conn.execute('SELECT count(*) FROM attempts WHERE canonical_id=%s',(c['question_id'],)).fetchone()[0]==before

def test_outside_scope_and_unsafe_sources_are_not_silently_included(client,actor,database):
    conn=database[1];ids=seed(conn,1,outside=True);h=who(actor,'reviewer1')
    base=client.get('/api/vocabulary/overview').json()['eligible']
    assert client.get('/api/vocabulary/overview?exam_scope=all').json()['eligible']==base+1
    conn.execute("UPDATE appearances SET has_diagram=true,figure_image=NULL WHERE canonical_id=%s",(ids[0],))
    assert client.get('/api/vocabulary/overview?exam_scope=all').json()['eligible']==base
    assert client.post('/api/vocabulary/card?exam_scope=invalid',headers=h,json={}).status_code==422

def test_expiry_and_forged_state_never_create_a_grade(client,actor,database):
    conn=database[1];seed(conn,1);h=who(actor,'reviewer2');c=card(client,h)
    before=conn.execute('SELECT count(*) FROM attempts WHERE canonical_id=%s',(c['question_id'],)).fetchone()[0]
    assert client.post('/api/vocabulary/cards/'+c['id']+'/answer',headers=h,json={'correct':True,'stage':6,'chosen_index':1}).status_code==422
    assert client.post('/api/vocabulary/cards/'+c['id']+'/answer',headers={**h,'X-Review-CSRF':'invalid'},json={'chosen_index':1}).status_code==403
    assert client.post('/api/vocabulary/cards/'+c['id']+'/answer',headers=h,json={'chosen_index':None}).status_code==422
    conn.execute("UPDATE vocabulary_cards SET expires_at=now()-interval '1 minute' WHERE id=%s",(c['id'],))
    assert pick(client,h,c).status_code==409
    assert conn.execute('SELECT count(*) FROM attempts WHERE canonical_id=%s',(c['question_id'],)).fetchone()[0]==before

def test_vocabulary_respects_an_active_mock_answer_gate(client,actor,database):
    conn=database[1];seed(conn,1);h=who(actor);c=card(client,h)
    original=conn.execute("SELECT plan_code,plan_status,trial_ends_at FROM users WHERE id='author'").fetchone()
    conn.execute("UPDATE users SET plan_code='pro',plan_status='trial',trial_ends_at=now()+interval '7 days' WHERE id='author'")
    cid='vocab-gate-'+uuid4().hex;mid=None
    try:
        conn.execute("INSERT INTO collections(id,title,kind,visibility,live_version) VALUES (%s,'Vocabulary gate test','exam','public',1)",(cid,))
        conn.execute("INSERT INTO collection_sections(collection_id,version,path,title,position,query,pins) VALUES (%s,1,'general','General',1,'{}',%s)",(cid,[c['question_id']]))
        r=client.post('/api/mocks',headers=h,json={'collection_id':cid,'count':1,'duration_minutes':1});assert r.status_code==200,r.text;mid=r.json()['id']
        assert pick(client,h,c).status_code==409
    finally:
        if mid:client.post('/api/mocks/'+mid+'/submit',headers=h,json={'answers':[]})
        conn.execute("UPDATE users SET plan_code=%s,plan_status=%s,trial_ends_at=%s WHERE id='author'",original)


def test_equivalent_mizoram_printing_with_outside_primary_shares_semantic_progress(client,actor,database):
    conn=database[1];ids=seed(conn,1,outside=True);qid=ids[0]
    pid='vocab-mizo-'+uuid4().hex
    conn.execute("INSERT INTO papers(id,exam_name,exam_type,year,source_file,exam_scope_id) VALUES (%s,'Equivalent synthetic printing','Direct',2026,'Old_Questions/test.pdf','mizoram-recruitment')",(pid,))
    aid='a_equiv_'+uuid4().hex
    conn.execute("INSERT INTO appearances(id,paper_id,canonical_id,is_primary,type,question,question_markup,options,answer_index,answer_source,direction) SELECT %s,%s,canonical_id,false,type,question,question_markup,options,answer_index,answer_source,direction FROM appearances WHERE canonical_id=%s AND is_primary",(aid,pid,qid))
    assert conn.execute("SELECT count(*) FROM v_vocabulary_eligible WHERE id=%s",(qid,)).fetchone()[0]==2
    assert conn.execute("SELECT appearance_id FROM v_vocabulary_eligible WHERE id=%s AND focus='mizoram-recruitment'",(qid,)).fetchone()[0]==aid
    # Keep previous synthetic cards out of this account's short review queue.
    conn.execute("UPDATE question_classifications SET review_status='pending' WHERE topic_id='english/vocabulary' AND question_id<>%s",(qid,))
    h=who(actor,'reviewer1');a=card(client,h);assert a['question_id']==qid
    assert pick(client,h,a).json()['stage']==1
    conn.execute("UPDATE vocabulary_state SET due_at=now()-interval '1 sec' WHERE user_id='reviewer1' AND question_id=%s",(qid,))
    b=card(client,h,'all');assert b['question_id']==qid and b['stage']==1
    assert conn.execute("SELECT appearance_id FROM vocabulary_state WHERE user_id='reviewer1' AND question_id=%s",(qid,)).fetchone()[0]=='a_'+qid
