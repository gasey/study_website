"""IST, disclosure, scoring and concurrency boundaries on isolated PostgreSQL."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from psycopg.types.json import Jsonb

from test_study_desks import desk_setup, room, join


def path(did):
    return '/api/desk/rooms/' + did + '/weekly-goal'


def share(client, actor, did, user, enabled=True):
    response = client.post('/api/desk/rooms/' + did + '/sharing', headers=actor(user),
                           json={'progress': enabled})
    assert response.status_code == 200, response.text


def body(client, did, target=300):
    current = client.get(path(did)).json()
    return {k: current[k] for k in ('week_start',)} | {
        'expected_version': current['version'], 'target': target,
    }


def question(conn, source='official', **extra):
    qid = 'cq_goal_' + uuid4().hex
    conn.execute('''INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source)
      VALUES(%s,'mcq','Synthetic weekly goal question',%s,'B',%s)''',
      (qid, Jsonb(['A','B','C','D']), source))
    for key, value in extra.items():
        assert key in ('status', 'key_disputed', 'source_defect')
        conn.execute('UPDATE canonical_questions SET '+key+'=%s WHERE id=%s', (value,qid))
    return qid


def attempt(conn, qid, user='author', source='official', at=None, correct=True, chosen='B'):
    text, options, answer = conn.execute('SELECT question,options,answer_text FROM canonical_questions WHERE id=%s',(qid,)).fetchone()
    snapshot = {'question':text,'options':options,'answer_text':answer,'answer_source':source,'context_basis':'canonical'}
    return conn.execute('''INSERT INTO attempts(user_id,canonical_id,correct,chosen_text,context,scoring_snapshot,at)
      VALUES(%s,%s,%s,%s,'practice',%s,COALESCE(%s,clock_timestamp())) RETURNING id''',
      (user,qid,correct,chosen,Jsonb(snapshot),at)).fetchone()[0]


def test_private_owner_cas_replay_and_no_awards(client, actor, database):
    conn = database[1]
    did = room(client, actor)
    join(client, actor, did)
    h = actor('author')
    initial = client.get(path(did))
    assert initial.status_code == 200 and initial.headers['cache-control'] == 'private, no-store'
    assert initial.json()['target'] is None and initial.json()['version'] == 0
    assert initial.json()['scored_attempts'] == 0 and initial.json()['sharing_members'] == 0
    data = body(client, did)
    before = {t:conn.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in (
        'attempts','reward_ledger','reward_question_claims','calendar_entries','study_focus_sessions')}
    assert client.post(path(did),json=data).status_code == 403
    assert client.post(path(did),headers={**h,'X-Desk-User':'outsider'},json=data).status_code == 409
    h = actor('outsider')
    assert client.get(path(did)).json()['can_edit'] is False
    assert client.post(path(did),headers=h,json=data).status_code == 403
    h = actor('reviewer1')
    assert client.get(path(did)).status_code == 404
    assert client.post(path(did),headers=h,json=data).status_code == 404
    h = actor('author')
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _:client.post(path(did),headers=h,json=data), range(2)))
    assert sorted(r.status_code for r in responses) == [200,409]
    assert client.post(path(did),headers=h,json=data).status_code == 409
    assert conn.execute("SELECT count(*) FROM study_desk_events WHERE desk_id=%s AND action='weekly_goal_set'",(did,)).fetchone()[0] == 1
    assert conn.execute('SELECT count(*) FROM study_desk_weekly_goals WHERE desk_id=%s',(did,)).fetchone()[0] == 1
    assert client.post(path(did),headers=h,json=body(client,did,450)).json()['version'] == 2
    assert client.get(path(did)).json()['target'] == 450
    assert {t:conn.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in before} == before
    client.cookies.clear()
    assert client.get(path(did)).status_code == 401
    conn.execute("UPDATE study_desks SET closed_at=now() WHERE id=%s",(did,))
    actor('author'); assert client.get(path(did)).status_code == 404


def test_validation_flag_sanctions_and_week_rollover(client, actor, database, monkeypatch):
    from app.config import settings
    from app.services import desk_goals
    conn = database[1]; did = room(client, actor); h = actor('author')
    data = body(client,did)
    for target in (0,10001,1.5,True,'300'):
        assert client.post(path(did),headers=h,json=data|{'target':target}).status_code == 422
    assert client.post(path(did),headers=h,json=data|{'scored_attempts':300}).status_code == 422
    assert client.post(path(did),headers=h,json=data|{'week_start':'2020-01-06'}).status_code == 409
    monkeypatch.setattr(settings,'study_desks_private_enabled',False)
    assert client.get(path(did)).status_code == 409
    assert client.post(path(did),headers=h,json=data).status_code == 409
    monkeypatch.setattr(settings,'study_desks_private_enabled',True)
    action = conn.execute("INSERT INTO mod_actions(actor_id,target_user,action,note) VALUES('owner','author','mute','Synthetic desk-goal test') RETURNING id").fetchone()[0]
    sid = conn.execute("INSERT INTO sanctions(user_id,kind,step,ends_at,action_id) VALUES('author','mute',1,now()+interval '1 hour',%s) RETURNING id",(action,)).fetchone()[0]
    assert client.post(path(did),headers=h,json=data).status_code == 403
    conn.execute('UPDATE sanctions SET lifted_at=now() WHERE id=%s',(sid,))
    original = desk_goals.clock
    async def monday(cur, **_):
        return await original(cur,as_of=datetime(2026,11,22,18,30,tzinfo=timezone.utc))
    monkeypatch.setattr(desk_goals,'clock',monday)
    current = client.get(path(did)).json()
    assert current['week_start'] == '2026-11-23' and current['week_end'] == '2026-11-29'
    assert client.post(path(did),headers=h,json=data).status_code == 409
    assert client.post(path(did),headers=h,json=body(client,did,1)).status_code == 200
    async def following(cur, **_):
        return await original(cur,as_of=datetime(2026,11,29,18,30,tzinfo=timezone.utc))
    monkeypatch.setattr(desk_goals,'clock',following)
    next_week = client.get(path(did)).json()
    assert next_week['week_start'] == '2026-11-30' and next_week['target'] is None
    assert conn.execute('SELECT target FROM study_desk_weekly_goals WHERE desk_id=%s',(did,)).fetchone()[0] == 1


@pytest.mark.parametrize('reverse',[False,True])
def test_current_consent_blocks_membership_and_join_time(client, actor, database, reverse):
    conn = database[1]; did = room(client,actor); join(client,actor,did)
    qid = question(conn)
    attempt(conn,qid); attempt(conn,qid,'outsider')
    actor('author'); assert client.get(path(did)).json()['scored_attempts'] == 0
    share(client,actor,did,'author')
    assert client.get(path(did)).json()['scored_attempts'] == 1
    share(client,actor,did,'outsider')
    actor('author'); assert client.get(path(did)).json()['scored_attempts'] == 2
    a,b = ('outsider','author') if reverse else ('author','outsider')
    conn.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)',(a,b))
    result = client.get(path(did)).json()
    assert result['scored_attempts'] == 1 and result['sharing_members'] == 1
    conn.execute('DELETE FROM creator_blocks WHERE user_id=%s AND blocked_id=%s',(a,b))
    share(client,actor,did,'outsider',False)
    actor('author'); assert client.get(path(did)).json()['scored_attempts'] == 1
    share(client,actor,did,'outsider')
    conn.execute("UPDATE study_desk_members SET left_at=now() WHERE desk_id=%s AND user_id='outsider'",(did,))
    actor('outsider'); assert client.get(path(did)).status_code == 404
    actor('author'); assert client.get(path(did)).json()['scored_attempts'] == 1
    conn.execute("UPDATE study_desk_members SET left_at=NULL,joined_at=clock_timestamp() WHERE desk_id=%s AND user_id='outsider'",(did,))
    assert client.get(path(did)).json()['scored_attempts'] == 1
    attempt(conn,qid,'outsider')
    assert client.get(path(did)).json()['scored_attempts'] == 2


def test_latest_scoring_and_provenance_not_raw_correctness(client,actor,database):
    conn = database[1]; did = room(client,actor); share(client,actor,did,'author')
    good = question(conn)
    wrong = attempt(conn,good,correct=False,chosen='A')
    excluded = attempt(conn,good)
    conn.execute("INSERT INTO attempt_assessments(attempt_id,input_hash,policy_version,payload) VALUES(%s,'excluded','synthetic',%s)", (excluded,Jsonb({'outcome':'excluded'})))
    attempt(conn,good,source='derived')
    attempt(conn,good,source='none')
    attempt(conn,good,chosen=None)
    for qid in (question(conn,'derived'),question(conn,key_disputed=True),question(conn,status='held'),question(conn,source_defect='unresolved-source')):
        attempt(conn,qid)
    result = client.get(path(did)).json()
    assert result['scored_attempts'] == 1, result
    # Latest append-only reassessment can restore eligibility without rewriting attempts.
    conn.execute("INSERT INTO attempt_assessments(attempt_id,input_hash,policy_version,payload) VALUES(%s,'restored','synthetic',%s)", (excluded,Jsonb({'outcome':'wrong'})))
    assert client.get(path(did)).json()['scored_attempts'] == 2
    assert conn.execute('SELECT correct FROM attempts WHERE id=%s',(wrong,)).fetchone()[0] is False
    data = body(client,did,1)
    assert client.post(path(did),headers=actor('author'),json=data).status_code == 200
    result = client.get(path(did)).json()
    assert result['completed'] and result['scored_attempts'] == 2
    for secret in ('answer_text','chosen_text','canonical_id','user_id','handle','correct','wrong'):
        assert '"'+secret+'"' not in str(client.get(path(did)).text)


def test_real_role_read_only_ist_window_and_no_read_side_effects(client,actor,database,monkeypatch):
    from app.db import cursor
    from app.services import desk_goals
    conn = database[1]; did = room(client,actor); share(client,actor,did,'author')
    qid = question(conn)
    start = datetime(2026,11,22,18,30,tzinfo=timezone.utc)
    conn.execute('UPDATE study_desk_members SET joined_at=%s WHERE desk_id=%s',(start-timedelta(days=1),did))
    for when in (start-timedelta(microseconds=1),start,start+timedelta(days=6),start+timedelta(days=7)):
        attempt(conn,qid,at=when)
    before = conn.execute('SELECT count(*) FROM study_desk_weekly_goals').fetchone()[0]
    async def read(as_of):
        async with cursor() as cur:
            await cur.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            await cur.execute('SET LOCAL ROLE mpsc')
            return await desk_goals.summary(cur,did,'author',await desk_goals.clock(cur,as_of=as_of))
    assert client.portal.call(read,start)['scored_attempts'] == 1
    assert client.portal.call(read,start+timedelta(days=6,hours=23))['scored_attempts'] == 2
    assert client.portal.call(read,start+timedelta(days=7))['scored_attempts'] == 1
    assert conn.execute('SELECT count(*) FROM study_desk_weekly_goals').fetchone()[0] == before


def test_closed_account_cannot_create_or_update_goal_as_real_role(client,actor,database):
    import psycopg
    conn=database[1];did=room(client,actor);actor('author')
    current=body(client,did)
    assert client.post(path(did),headers=actor('author'),json=current).status_code==200
    uid='closed_goal_'+uuid4().hex
    conn.execute('INSERT INTO users(id,handle,closed_at,contribution_public) VALUES(%s,%s,now(),false)',(uid,uid))
    for statement, params in (
        ('INSERT INTO study_desk_weekly_goals(desk_id,week_start,target,updated_by) VALUES(%s,%s,300,%s)',(did,'2020-01-06',uid)),
        ('UPDATE study_desk_weekly_goals SET updated_by=%s WHERE desk_id=%s',(uid,did)),
    ):
        with pytest.raises(psycopg.Error,match='Account is closed'):
            with conn.transaction():
                conn.execute('SET LOCAL ROLE mpsc');conn.execute(statement,params)
    assert conn.execute('SELECT updated_by FROM study_desk_weekly_goals WHERE desk_id=%s',(did,)).fetchone()[0]=='author'
