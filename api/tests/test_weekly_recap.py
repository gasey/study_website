"""Historical source fixtures for Monday-only, private, read-only recaps."""
from datetime import datetime,timedelta,timezone
from uuid import uuid4
from app.services import weekly_boards,weekly_recap
from test_learning_loop import run
from test_rewards import learner

MONDAY=datetime(2030,1,7,10,tzinfo=timezone.utc)
START=datetime(2029,12,30,18,30,tzinfo=timezone.utc)
END=START+timedelta(days=7)


def test_monday_period_ledger_rollups_focus_and_first_milestones(client,learner,database,monkeypatch):
    conn=database[1];user,h=learner;other='outsider'
    for who,xp,when in [(user,100,START),(user,-10,END-timedelta(seconds=1)),(user,999,END),(other,888,START),(user,777,START-timedelta(microseconds=1))]:
        conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,note,created_at) VALUES(%s,%s,'adjustment',%s,'Isolated historical source receipt',%s)",(who,uuid4().hex,xp,when))
    for i in range(7):conn.execute('INSERT INTO user_learning_days(user_id,day) VALUES(%s,%s)',(user,START.date()+timedelta(days=i+1)))
    conn.execute("INSERT INTO study_focus_sessions(id,user_id,duration_seconds,state,elapsed_seconds,created_at,ended_at) VALUES(%s,%s,600,'cancelled',300,%s,%s)",(uuid4().hex,user,START,START+timedelta(hours=1)))
    conn.execute("INSERT INTO study_focus_sessions(id,user_id,duration_seconds,state,elapsed_seconds,created_at,ended_at) VALUES(%s,%s,600,'completed',600,%s,%s)",(uuid4().hex,other,START,START+timedelta(hours=1)))
    # A real historical first-milestone receipt, paired to its immutable claim.
    q='recap-'+uuid4().hex
    conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES(%s,'mcq','Isolated recap item','[\"A\",\"B\"]','B','official')",(q,))
    attempt=conn.execute("INSERT INTO attempts(user_id,canonical_id,chosen_text,correct,context,at,scoring_snapshot) VALUES(%s,%s,'B',true,'game',%s,'{\"answer_source\":\"official\",\"answer_text\":\"B\"}') RETURNING id",(user,q,START)).fetchone()[0]
    topic='recap/topic-'+uuid4().hex
    receipt=conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note,created_at,source_attempt_id) VALUES(%s,%s,'study',30,3,'Isolated first-tier receipt',%s,%s) RETURNING id",(user,f'mastery:{user}:{topic}:proficient',START,attempt)).fetchone()[0]
    conn.execute("INSERT INTO mastery_milestones(user_id,subject_id,topic,tier,origin,ledger_id,source_attempt_id,created_at) VALUES(%s,'english',%s,'proficient','activity',%s,%s,%s)",(user,topic,receipt,attempt,START))
    conn.execute("INSERT INTO mastery_milestones(user_id,subject_id,topic,tier,origin,created_at) VALUES(%s,'english',%s,'proficient','baseline',%s)",(user,topic+'-baseline',START))
    sid=uuid4().hex
    conn.execute("INSERT INTO practice_study_sessions(id,user_id,request_key,request_hash,requested_size,question_ids,paper_ids,filters,kind,created_at,finished_at) VALUES(%s,%s,%s,'fixture',10,%s,%s,'{}','review',%s,%s)",(sid,user,sid,[q],['paper-test'],START,START+timedelta(minutes=1)))
    conn.execute('INSERT INTO review_item_completions(user_id,canonical_id,scheduled_due,session_id,attempt_id,correct,completed_on) VALUES(%s,%s,%s,%s,%s,true,%s)',(user,q,START.date()+timedelta(days=1),sid,attempt,START.date()+timedelta(days=1)))
    before=conn.execute('SELECT count(*),sum(xp),sum(points) FROM reward_ledger').fetchone()
    async def read(cur):return await weekly_recap.compose(cur,user,as_of=MONDAY)
    recap=run(client,read)
    assert recap['week_start'].isoformat()=='2029-12-31' and recap['week_end'].isoformat()=='2030-01-06'
    assert (recap['xp'],recap['active_days'],recap['reviews_cleared'],recap['focus_seconds'])==(120,7,1,300)
    assert recap['streak_kept'] and recap['topics']==[{'topic':topic,'topic_label':topic,'tier':'proficient'}]
    assert run(client,read)==recap
    assert conn.execute('SELECT count(*),sum(xp),sum(points) FROM reward_ledger').fetchone()==before
    original=weekly_boards.window
    async def monday(cur,as_of=None):return await original(cur,MONDAY)
    monkeypatch.setattr(weekly_boards,'window',monday)
    page=client.get('/api/me/today',headers=h)
    assert page.status_code==200 and page.json()['weekly_recap']['xp']==120
    assert page.headers['cache-control']=='private, no-store'
    client.cookies.clear()
    assert client.get('/api/me/today').json()['weekly_recap'] is None


def test_recap_absent_off_monday_and_empty_is_honest(client,learner,database):
    user,_=learner
    async def tuesday(cur):return await weekly_recap.compose(cur,user,as_of=MONDAY+timedelta(days=1))
    async def monday(cur):return await weekly_recap.compose(cur,user,as_of=MONDAY)
    assert run(client,tuesday) is None
    recap=run(client,monday)
    assert recap['xp']==recap['reviews_cleared']==recap['active_days']==recap['focus_seconds']==0
    assert recap['topics']==[] and not recap['streak_kept']
