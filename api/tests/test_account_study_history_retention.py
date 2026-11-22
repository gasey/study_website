"""Opt-in closed-account study-history cleanup; reward and multiplayer rows survive."""
from uuid import uuid4
import pytest
from app.config import settings
from app.db import cursor
from app.services import account_retention


def closed_user(conn, *, days=31):
    uid='closed-'+uuid4().hex
    conn.execute("INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)",(uid,uid,uid+'@example.test'))
    conn.execute("UPDATE users SET closed_at=now()-(%s||' days')::interval,email=NULL,email_verified_at=NULL,password_hash=NULL,name=NULL,avatar=NULL,handle=%s,contribution_public=false WHERE id=%s",(days,'deleted-'+uuid4().hex,uid))
    return uid


def run(client,fn,*args):
    async def invoke():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            return await fn(cur,*args)
    return client.portal.call(invoke)


async def purge(cur,accounts=5,batch=200):
    await cur.execute('SELECT sweep_expired_study_history(%s,%s) AS result',(accounts,batch))
    return (await cur.fetchone())['result']


def add_history(conn,uid):
    attempt=conn.execute("INSERT INTO attempts(user_id,canonical_id,correct,chosen_text,context) VALUES(%s,'cq_test',true,'B','practice') RETURNING id",(uid,)).fetchone()[0]
    conn.execute("INSERT INTO attempt_assessments(attempt_id,input_hash,policy_version,payload) VALUES(%s,'synthetic','test','{}')",(attempt,))
    conn.execute("INSERT INTO practice_request_receipts(user_id,request_key,request_hash,attempt_id,response) VALUES(%s,'practice-key','synthetic',%s,'{}')",(uid,attempt))
    conn.execute("INSERT INTO reward_question_claims(user_id,canonical_id,attempt_id) VALUES(%s,'cq_test',%s)",(uid,attempt))
    ledger=conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note,source_attempt_id) VALUES(%s,%s,'study',10,1,'Synthetic retained reward',%s) RETURNING id",(uid,'retained-'+uid,attempt)).fetchone()[0]
    conn.execute("INSERT INTO mastery_milestones(user_id,subject_id,topic,tier,origin,ledger_id,source_attempt_id) VALUES(%s,'english','english/test','proficient','activity',%s,%s)",(uid,ledger,attempt))
    conn.execute("INSERT INTO user_activity_daily(user_id,collection_key,section_key,subject_key,subject_label,day,answered,correct,last_active_at) VALUES(%s,'udc','','english','English',current_date,1,1,now())",(uid,))
    conn.execute("INSERT INTO user_topic_mastery(user_id,subject_id,topic,state,distinct_attempted,distinct_correct_latest,last_verified_activity_at,rule_version) VALUES(%s,'english','english/test','practicing',1,1,now(),'test')",(uid,))
    game_attempt=conn.execute("INSERT INTO attempts(user_id,canonical_id,correct,chosen_text,context) VALUES(%s,'cq_test',true,'B','game') RETURNING id",(uid,)).fetchone()[0]
    room='room-'+uuid4().hex
    conn.execute("INSERT INTO game_rooms(id,owner_id,mode,capacity,round_seconds,questions,request_key,request_hash) VALUES(%s,%s,'party',2,20,'[]',%s,'synthetic')",(room,uid,'start-'+uuid4().hex))
    conn.execute("INSERT INTO game_members(room_id,user_id) VALUES(%s,%s)",(room,uid))
    conn.execute("INSERT INTO game_answers(room_id,user_id,position,chosen_index,correct,elapsed_ms,attempt_id) VALUES(%s,%s,0,1,true,4000,%s)",(room,uid,game_attempt))
    return attempt,ledger,game_attempt,room


def test_expired_account_purges_private_answers_and_progress_but_retains_rewards_and_game(client,database):
    conn=database[1];uid=closed_user(conn);attempt,ledger,game_attempt,room=add_history(conn,uid)
    focus='focus-'+uuid4().hex
    conn.execute("INSERT INTO study_focus_sessions(id,user_id,duration_seconds,state,elapsed_seconds) VALUES(%s,%s,900,'completed',900)",(focus,uid))
    result=run(client,purge,5,200)
    assert result['accounts_scanned']==1 and result['accounts_completed']==1
    assert conn.execute('SELECT study_history_purged_at IS NOT NULL FROM users WHERE id=%s',(uid,)).fetchone()[0]
    assert conn.execute('SELECT count(*) FROM attempts WHERE id=%s',(attempt,)).fetchone()[0]==0
    assert conn.execute("SELECT count(*) FROM attempt_assessments WHERE attempt_id=%s",(attempt,)).fetchone()[0]==0
    assert conn.execute("SELECT count(*) FROM practice_request_receipts WHERE user_id=%s",(uid,)).fetchone()[0]==0
    assert conn.execute("SELECT count(*) FROM user_activity_daily WHERE user_id=%s",(uid,)).fetchone()[0]==0
    assert conn.execute("SELECT count(*) FROM user_topic_mastery WHERE user_id=%s",(uid,)).fetchone()[0]==0
    assert conn.execute("SELECT count(*) FROM study_focus_sessions WHERE id=%s",(focus,)).fetchone()[0]==0
    assert conn.execute('SELECT source_attempt_id FROM reward_ledger WHERE id=%s',(ledger,)).fetchone()[0] is None
    assert conn.execute('SELECT attempt_id FROM reward_question_claims WHERE user_id=%s',(uid,)).fetchone()[0] is None
    milestone=conn.execute("SELECT source_attempt_id,ledger_id FROM mastery_milestones WHERE user_id=%s",(uid,)).fetchone()
    assert milestone==(None,ledger)
    assert conn.execute('SELECT id FROM attempts WHERE id=%s',(game_attempt,)).fetchone()==(game_attempt,)
    assert conn.execute('SELECT attempt_id FROM game_answers WHERE room_id=%s AND user_id=%s',(room,uid)).fetchone()==(game_attempt,)
    assert conn.execute('SELECT count(*) FROM reward_ledger WHERE id=%s',(ledger,)).fetchone()[0]==1


def test_hold_reopened_and_active_accounts_are_skipped(client,database):
    conn=database[1];held=closed_user(conn);reopened=closed_user(conn);active='active-'+uuid4().hex
    conn.execute('UPDATE users SET closed_at=NULL WHERE id=%s',(reopened,))
    conn.execute("INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)",(active,active,active+'@example.test'))
    held_attempt=conn.execute("INSERT INTO attempts(user_id,canonical_id,correct,chosen_text,context) VALUES(%s,'cq_test',false,'A','practice') RETURNING id",(held,)).fetchone()[0]
    reopened_attempt=conn.execute("INSERT INTO attempts(user_id,canonical_id,correct,chosen_text,context) VALUES(%s,'cq_test',false,'A','practice') RETURNING id",(reopened,)).fetchone()[0]
    active_attempt=conn.execute("INSERT INTO attempts(user_id,canonical_id,correct,chosen_text,context) VALUES(%s,'cq_test',false,'A','practice') RETURNING id",(active,)).fetchone()[0]
    conn.execute("INSERT INTO account_study_history_holds(user_id,hold_code) VALUES(%s,'manual_review')",(held,))
    result=run(client,purge,5,200)
    assert result['accounts_scanned']==0
    assert conn.execute('SELECT count(*) FROM attempts WHERE id=ANY(%s)',([held_attempt,reopened_attempt,active_attempt],)).fetchone()[0]==3
    assert conn.execute('SELECT study_history_purged_at FROM users WHERE id=%s',(held,)).fetchone()[0] is None


def test_mpsc_cannot_directly_delete_immutable_answer_receipts(client,database):
    conn=database[1];uid=closed_user(conn);attempt=conn.execute("INSERT INTO attempts(user_id,canonical_id,correct,chosen_text,context) VALUES(%s,'cq_test',false,'A','practice') RETURNING id",(uid,)).fetchone()[0]
    conn.execute("INSERT INTO practice_request_receipts(user_id,request_key,request_hash,attempt_id,response) VALUES(%s,'protected','synthetic',%s,'{}')",(uid,attempt))
    with pytest.raises(Exception,match='Study history is immutable'):
        with conn.transaction():conn.execute("DELETE FROM practice_request_receipts WHERE user_id=%s",(uid,))
    assert conn.execute('SELECT count(*) FROM practice_request_receipts WHERE user_id=%s',(uid,)).fetchone()[0]==1


def test_mpsc_cannot_directly_delete_study_roots(client,database):
    conn=database[1]
    with conn.transaction():
        conn.execute('SET LOCAL ROLE mpsc')
        for table in ('attempts','mock_sessions','review_items','study_focus_sessions'):
            with pytest.raises(Exception,match='permission denied'):
                with conn.transaction():
                    conn.execute(f'DELETE FROM {table} WHERE false')


def test_sweep_is_disabled_by_default(client,database,monkeypatch):
    conn=database[1];uid=closed_user(conn);attempt=conn.execute("INSERT INTO attempts(user_id,canonical_id,correct,chosen_text,context) VALUES(%s,'cq_test',false,'A','practice') RETURNING id",(uid,)).fetchone()[0]
    monkeypatch.setattr(settings,'study_history_retention_enabled',False)
    result=run(client,account_retention.sweep)
    assert result['study_history']=='disabled'
    assert conn.execute('SELECT 1 FROM attempts WHERE id=%s',(attempt,)).fetchone()==(1,)


def test_small_batches_resume_until_every_attempt_and_child_is_gone(client,database):
    conn=database[1];uid=closed_user(conn,days=365);attempts=[]
    for i in range(2):
        attempt=conn.execute("INSERT INTO attempts(user_id,canonical_id,correct,chosen_text,context) VALUES(%s,'cq_test',false,'A','practice') RETURNING id",(uid,)).fetchone()[0]
        conn.execute("INSERT INTO attempt_assessments(attempt_id,input_hash,policy_version,payload) VALUES(%s,%s,'test','{}')",(attempt,'batch-'+str(i)))
        attempts.append(attempt)
    first=run(client,purge,1,1)
    remaining=conn.execute('SELECT id FROM attempts WHERE id=ANY(%s) ORDER BY id',(attempts,)).fetchall()
    assert first['accounts_scanned']==1 and first['accounts_completed']==0, (first,remaining)
    assert conn.execute('SELECT study_history_purged_at FROM users WHERE id=%s',(uid,)).fetchone()[0] is None
    for _ in range(4):
        run(client,purge,1,1)
    assert conn.execute('SELECT count(*) FROM attempts WHERE id=ANY(%s)',(attempts,)).fetchone()[0]==0
    assert conn.execute('SELECT count(*) FROM attempt_assessments WHERE attempt_id=ANY(%s)',(attempts,)).fetchone()[0]==0
    assert conn.execute('SELECT study_history_purged_at IS NOT NULL FROM users WHERE id=%s',(uid,)).fetchone()[0]
