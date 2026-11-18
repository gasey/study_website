"""Deck membership follows approved taxonomy, private latest outcomes and scopes."""
from uuid import uuid4
from psycopg.types.json import Jsonb
from test_vocabulary import seed,who,pick

ROOT='english/vocabulary'
def prepare(conn):
    # This repository's SQL test database is shared for the session. Isolate
    # this test's eligible catalog from earlier synthetic vocabulary fixtures.
    conn.execute("UPDATE question_classifications SET review_status='pending' WHERE topic_id=%s",(ROOT,))
    conn.execute("UPDATE question_topic_links SET review_status='pending' WHERE topic_id=%s",(ROOT,))
    conn.execute("UPDATE review_taxonomy SET active=true WHERE parent_id=%s",(ROOT,))
    ids=seed(conn,4)
    for short,label in [('synonyms','Synonyms'),('antonyms','Antonyms'),('idioms-and-phrases','Idioms and Phrases'),('one-word-substitution','One-Word Substitution')]:
        conn.execute("INSERT INTO review_taxonomy(id,label,level,parent_id,version) VALUES(%s,%s,'subtopic',%s,'test') ON CONFLICT DO NOTHING",(ROOT+'/'+short,label,ROOT))
    for qid,name in zip(ids,['synonyms','antonyms','idioms-and-phrases',None]):
        if name:conn.execute('UPDATE question_classifications SET subtopic_id=%s,subtopic_label=%s WHERE question_id=%s',(ROOT+'/'+name,name,qid))
    return ids

def decks(client):
    r=client.get('/api/vocabulary/decks');assert r.status_code==200,r.text
    assert r.headers['cache-control']=='private, no-store'
    return {x['id']:x for x in r.json()['items']}

def next_in(client,h,deck,**kw):
    r=client.post('/api/vocabulary/card',headers=h,json={'deck_id':deck,**kw});assert r.status_code==200,r.text
    return r.json()['card']

def test_reviewed_decks_are_canonical_distinct_and_have_honest_zero_states(client,actor,database):
    conn=database[1];ids=prepare(conn);h=who(actor)
    before=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    d=decks(client)
    assert d[ROOT+'/synonyms']['eligible']==1 and d[ROOT]['eligible']==1
    assert d[ROOT+'/one-word-substitution']['eligible']==0
    assert all(x['attempted']==x['correct_latest']==0 and not x['rusty'] for x in d.values())
    assert client.get('/api/vocabulary/decks').json()['curated_available'] is False
    conn.execute("INSERT INTO question_topic_links(question_id,path_id,subject_id,subject_label,topic_id,topic_label,subtopic_id,subtopic_label,taxonomy_version,source,review_status,evidence) VALUES(%s,%s,'english','English',%s,'Vocabulary',%s,'Synonyms','test','manual','approved','[]')",(ids[0],ROOT+'/synonyms',ROOT,ROOT+'/synonyms'))
    assert decks(client)[ROOT+'/synonyms']['eligible']==1
    assert next_in(client,h,ROOT+'/antonyms')['question_id']==ids[1]
    assert next_in(client,h,ROOT+'/synonyms')['question_id']==ids[0]
    assert next_in(client,h,ROOT)['question_id']==ids[3]
    assert client.get('/api/vocabulary/overview?deck_id='+ROOT+'/antonyms').json()['eligible']==1
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==before
    assert client.post('/api/vocabulary/card',headers=h,json={'deck_id':'invented'}).status_code==422
    assert client.get('/api/vocabulary/overview?deck_id=invented').status_code==422
    client.cookies.clear();assert client.get('/api/vocabulary/decks').status_code==401

def test_deck_progress_uses_latest_verified_attempt_not_lifetime_accuracy(client,actor,database):
    conn=database[1];ids=prepare(conn);h=who(actor);deck=ROOT+'/synonyms';c=next_in(client,h,deck)
    assert pick(client,h,c).status_code==200
    d=decks(client)[deck];assert d['attempted']==d['correct_latest']==1
    # A later wrong answer replaces the same question's latest outcome.
    conn.execute("UPDATE review_items SET due_on=(now() AT TIME ZONE 'Asia/Kolkata')::date WHERE user_id='author' AND item_type='vocab' AND item_id=%s",(ids[0],))
    c=next_in(client,h,deck);assert pick(client,h,c,'A').status_code==200
    d=decks(client)[deck];assert d['attempted']==1 and d['correct_latest']==0
    result=client.post('/api/vocabulary/card',headers=h,json={'deck_id':ROOT+'/antonyms','resume_id':c['id']})
    assert result.status_code==409 and 'another deck' in result.text
    actor('outsider');assert decks(client)[deck]['attempted']==0
    h=who(actor)
    conn.execute("UPDATE question_classifications SET review_status='pending' WHERE question_id=%s",(ids[0],))
    assert decks(client)[deck]['eligible']==0 and next_in(client,h,deck) is None

def test_assessed_questions_do_not_leak_through_deck_counts_or_card_discovery(client,actor,database):
    conn=database[1];ids=prepare(conn);h=who(actor);qid=ids[1];cid='deck-gate-'+uuid4().hex
    conn.execute("UPDATE users SET plan_code='pro',plan_status='trial',trial_ends_at=now()+interval '1 day' WHERE id='author'")
    conn.execute("INSERT INTO collections(id,title,kind,visibility,live_version) VALUES(%s,'Synthetic deck gate','exam','public',1)",(cid,))
    conn.execute("INSERT INTO collection_sections(collection_id,version,path,title,position,query,pins) VALUES(%s,1,'general','General',1,'{}',%s)",(cid,[qid]))
    r=client.post('/api/mocks',headers=h,json={'collection_id':cid,'count':1,'duration_minutes':1});assert r.status_code==200,r.text
    mid=r.json()['id']
    try:
        assert decks(client)[ROOT+'/antonyms']['eligible']==0
        assert client.get('/api/vocabulary/overview?deck_id='+ROOT+'/antonyms').json()['eligible']==0
        assert next_in(client,h,ROOT+'/antonyms') is None
    finally:client.post('/api/mocks/'+mid+'/submit',headers=h,json={'answers':[]})
    assert decks(client)[ROOT+'/antonyms']['eligible']==1

def test_decks_inherit_focus_and_exclude_unapproved_and_inactive_paths(client,actor,database):
    conn=database[1];ids=prepare(conn);outside=seed(conn,1,outside=True)[0];actor('outsider')
    conn.execute('UPDATE question_classifications SET subtopic_id=%s WHERE question_id=%s',(ROOT+'/synonyms',outside))
    assert decks(client)[ROOT+'/synonyms']['eligible']==1
    r=client.get('/api/vocabulary/decks?exam_scope=all');assert r.status_code==200,r.text
    assert next(x for x in r.json()['items'] if x['id']==ROOT+'/synonyms')['eligible']==2
    conn.execute('UPDATE review_taxonomy SET active=false WHERE id=%s',(ROOT+'/antonyms',))
    d=decks(client);assert ROOT+'/antonyms' not in d and d[ROOT]['eligible']==2
    assert client.get('/api/vocabulary/overview?deck_id='+ROOT+'/antonyms').status_code==422

def test_deck_decay_ignores_recent_excluded_assessment_and_keeps_original_attempt(client,actor,database):
    conn=database[1];prepare(conn);ids=seed(conn,20);actor('outsider')
    # The shared mastery semantics are latest canonical answers + a decay overlay,
    # not repeated drills or unscored recent activity keeping a deck fresh.
    for qid in ids:
        conn.execute("INSERT INTO attempts(user_id,canonical_id,correct,chosen_text,context,scoring_snapshot,at) VALUES('outsider',%s,true,'B','practice',%s,now()-interval '46 days')",(qid,Jsonb({'answer_source':'official'})))
    d=decks(client)[ROOT];assert d['state']=='proficient' and d['rusty'] and d['attempted']==20
    attempt=conn.execute("INSERT INTO attempts(user_id,canonical_id,correct,chosen_text,context,scoring_snapshot) VALUES('outsider',%s,true,'B','practice',%s) RETURNING id",(ids[0],Jsonb({'answer_source':'official'}))).fetchone()[0]
    conn.execute("INSERT INTO attempt_assessments(attempt_id,input_hash,policy_version,payload) VALUES(%s,%s,'synthetic-deck-test',%s)",(attempt,uuid4().hex,Jsonb({'outcome':'excluded','reason':'synthetic-source-hold'})))
    d=decks(client)[ROOT];assert d['attempted']==19 and d['correct_latest']==19 and d['rusty'] and d['state']=='proficient'
    assert conn.execute('SELECT correct FROM attempts WHERE id=%s',(attempt,)).fetchone()[0] is True
    from app.services.mobile_identity import allowed
    assert not allowed('GET','/api/vocabulary/decks') and not allowed('POST','/api/vocabulary/card')

def test_mastered_deck_requires_delayed_finished_scored_review(client,actor,database):
    from test_learning_workflows import learner
    from test_learning_loop import attempt,run
    from test_learning_habit import review
    from app.services import mastery
    conn=database[1];prepare(conn);ids=seed(conn,20)
    for delayed in (False,True):
        user,h=learner(database,actor)
        for qid in ids:attempt(conn,user,qid)
        run(client,mastery.refresh,user)
        assert decks(client)[ROOT]['state']=='proficient'
        if delayed:conn.execute("UPDATE user_topic_mastery SET proficient_at=now()-interval '15 days' WHERE user_id=%s AND topic=%s",(user,ROOT))
        # A real one-question due review supplies an ordinary server-issued
        # attempt receipt. Finishing it early must not qualify as delayed proof.
        aid=attempt(conn,user,ids[0],False)
        conn.execute("INSERT INTO review_items(user_id,item_type,item_id,canonical_id,box,due_on,last_result,last_attempt_id) VALUES(%s,'question',%s,%s,1,current_date,false,%s)",(user,ids[0],ids[0],aid))
        saved=review(client,h,conn,[ids[0]],correct=1,finish=False)
        assert decks(client)[ROOT]['state']=='proficient'
        finished=client.post('/api/study-sessions/'+saved['id']+'/finish',headers=h,json={'version':saved['version']})
        assert finished.status_code==200,finished.text
        assert decks(client)[ROOT]['state']==('mastered' if delayed else 'proficient')
