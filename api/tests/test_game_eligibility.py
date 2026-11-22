"""Prospective game eligibility: real controller/role, synthetic rooms only."""
import asyncio
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from psycopg.errors import UniqueViolation
from fastapi import HTTPException
from psycopg.types.json import Jsonb
from app.config import settings
from app.db import cursor
from app.services import games as g, audience, game_audience, account_tools
from app.routers import games as routes
from test_games_search import game_case
from test_account_privacy import declare
from test_learning_eligibility import wait_for_advisory_wait


@pytest.fixture(scope='module',autouse=True)
def controlled_workers():
    from app import main
    async def idle():await asyncio.Event().wait()
    with pytest.MonkeyPatch.context() as patch:
        for name in ('game_worker','learning_worker','assessment_worker'):patch.setattr(main,name,idle)
        yield


@pytest.fixture(autouse=True)
def original_flag(monkeypatch):
    monkeypatch.setattr(settings,'audience_gate_enabled',False)


@asynccontextmanager
async def role():
    async with cursor() as cur:
        await cur.execute('SET LOCAL ROLE mpsc')
        yield cur


def run(client,fn,*args):
    async def invoke():
        async with role() as cur:return await fn(cur,*args)
    return client.portal.call(invoke)


def room_case(client,game_case,mode='speed',players=1,state='running'):
    conn,_,users,headers,ids=game_case;count=g.MODES[mode][0]
    async def frozen(cur):
        rows=await g.current_questions(cur,ids[:count])
        return [{'id':qid,**{key:rows[qid].get(key) for key in g.IDENTITY}} for qid in ids[:count]]
    frozen_rows=run(client,frozen);rid='eligibility-game-'+uuid4().hex
    conn.execute('''INSERT INTO game_rooms(id,owner_id,mode,state,capacity,questions,round_seconds,
      request_key,request_hash,round_started_at,round_ends_at,deadline)
      VALUES(%s,%s,%s,%s,%s,%s,20,%s,'synthetic',now()-interval '4 seconds',now()+interval '16 seconds',now()+interval '10 minutes')''',
      (rid,users[0],mode,state,max(players,g.MODES[mode][2]),Jsonb(frozen_rows),rid))
    for user in users[:players]:
        conn.execute('INSERT INTO game_members(room_id,user_id,public_result,ready) VALUES(%s,%s,true,true)',(rid,user))
        conn.execute("INSERT INTO account_audience(user_id,category) VALUES(%s,'adult')",(user,))
    return conn,rid,users,headers,frozen_rows


def choices(conn,rid,user,rows):
    for i,q in enumerate(rows):
        conn.execute('''INSERT INTO game_answers(room_id,user_id,position,chosen_index,correct,elapsed_ms)
          VALUES(%s,%s,%s,%s,true,4000)''',(rid,user,i,q['options'].index(q['answer_text'])))


def history(conn,user):
    return {table:conn.execute('SELECT * FROM '+table+' WHERE user_id=%s ORDER BY 1,2',(user,)).fetchall()
      for table in ('attempts','reward_ledger','review_items','user_topic_mastery',
                    'user_activity_daily','user_activity_questions','learning_rollup_jobs')}


async def finish(cur,rid):await g.finish(cur,await g.room(cur,rid),await g.clock(cur))
async def advance(cur,rid):return await g.advance(cur,await g.room(cur,rid),await g.clock(cur))


@pytest.mark.parametrize('mode',list(g.MODES))
@pytest.mark.parametrize('category',[None,'under18'])
def test_all_modes_withhold_attempts_and_rewards_and_preserve_choices(client,game_case,monkeypatch,mode,category):
    conn,rid,users,_,frozen=room_case(client,game_case,mode)
    user=users[0];choices(conn,rid,user,frozen)
    saved=conn.execute('SELECT * FROM game_answers WHERE room_id=%s ORDER BY position',(rid,)).fetchall()
    if category:conn.execute('UPDATE account_audience SET category=%s WHERE user_id=%s',(category,user))
    else:conn.execute('DELETE FROM account_audience WHERE user_id=%s',(user,))
    before=history(conn,user);monkeypatch.setattr(settings,'audience_gate_enabled',True)
    run(client,finish,rid);run(client,finish,rid)
    assert history(conn,user)==before
    assert conn.execute('SELECT * FROM game_answers WHERE room_id=%s ORDER BY position',(rid,)).fetchall()==saved
    assert conn.execute('SELECT left_at IS NOT NULL,released_at IS NOT NULL,public_result,score FROM game_members WHERE room_id=%s',(rid,)).fetchone()==(True,True,False,0)
    assert conn.execute('SELECT count(*) FROM game_events WHERE room_id=%s AND action=%s',(rid,game_audience.ENDED)).fetchone()==(1,)
    assert conn.execute('SELECT count(*) FROM game_completion_rewards WHERE room_id=%s',(rid,)).fetchone()==(0,)


def test_eligible_player_keeps_completion_and_replay_while_other_is_restricted(client,game_case,monkeypatch):
    conn,rid,users,_,frozen=room_case(client,game_case,'duel',2)
    for user in users[:2]:choices(conn,rid,user,frozen)
    conn.execute("UPDATE account_audience SET category='under18' WHERE user_id=%s",(users[0],))
    before=history(conn,users[0]);monkeypatch.setattr(settings,'audience_gate_enabled',True)
    run(client,finish,rid)
    assert history(conn,users[0])==before
    assert conn.execute('SELECT count(*) FROM attempts WHERE user_id=%s',(users[1],)).fetchone()==(len(frozen),)
    assert conn.execute('SELECT user_id FROM game_completion_rewards WHERE room_id=%s',(rid,)).fetchall()==[(users[1],)]
    completed=history(conn,users[1]);run(client,finish,rid)
    assert history(conn,users[1])==completed


@pytest.mark.parametrize('mode',['gauntlet','trail','daily'])
def test_clock_does_not_fabricate_timeouts_or_reveals_for_restricted_player(client,game_case,monkeypatch,mode):
    conn,rid,users,_,_=room_case(client,game_case,mode)
    conn.execute("UPDATE account_audience SET category='under18' WHERE user_id=%s",(users[0],))
    conn.execute("UPDATE game_rooms SET round_ends_at=now()-interval '1 second',deadline=now()-interval '1 second' WHERE id=%s",(rid,))
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    result=run(client,advance,rid)
    assert result['state']=='finished'
    assert conn.execute('SELECT count(*) FROM game_answers WHERE room_id=%s',(rid,)).fetchone()==(0,)
    assert conn.execute('SELECT count(*) FROM answer_reveals WHERE user_id=%s',(users[0],)).fetchone()==(0,)
    assert conn.execute('SELECT count(*) FROM attempts WHERE user_id=%s',(users[0],)).fetchone()==(0,)


def test_actual_sweep_releases_restricted_seat_before_round_due_without_extending_deadline(client,game_case,monkeypatch):
    conn,rid,users,_,_=room_case(client,game_case,'party',2)
    clocks=conn.execute('SELECT current_position,round_started_at,round_ends_at,deadline FROM game_rooms WHERE id=%s',(rid,)).fetchone()
    conn.execute("UPDATE account_audience SET category='under18' WHERE user_id=%s",(users[1],))
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert run(client,g.sweep)>=1
    assert conn.execute('SELECT current_position,round_started_at,round_ends_at,deadline FROM game_rooms WHERE id=%s',(rid,)).fetchone()==clocks
    assert conn.execute('SELECT left_at IS NOT NULL,released_at IS NOT NULL FROM game_members WHERE room_id=%s AND user_id=%s',(rid,users[1])).fetchone()==(True,True)
    assert conn.execute('SELECT left_at FROM game_members WHERE room_id=%s AND user_id=%s',(rid,users[0])).fetchone()==(None,)


def test_waiting_restricted_host_cancels_and_releases_every_reservation(client,game_case,monkeypatch):
    conn,rid,users,_,_=room_case(client,game_case,'party',2,'waiting')
    conn.execute("UPDATE account_audience SET category='under18' WHERE user_id=%s",(users[0],))
    monkeypatch.setattr(settings,'audience_gate_enabled',True);run(client,g.sweep)
    assert conn.execute('SELECT state FROM game_rooms WHERE id=%s',(rid,)).fetchone()==('cancelled',)
    assert conn.execute('SELECT count(*) FROM game_members WHERE room_id=%s AND released_at IS NULL',(rid,)).fetchone()==(0,)


def test_busy_account_defers_room_and_releases_other_participant_leases(client,game_case,monkeypatch):
    conn,rid,users,_,_=room_case(client,game_case,'duel',2)
    for user in users[:2]:choices(conn,rid,user,conn.execute('SELECT questions FROM game_rooms WHERE id=%s',(rid,)).fetchone()[0])
    before=[history(conn,user) for user in users[:2]]
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    async def scenario():
        async with role() as cur:
            await audience.learning_processing_lock(cur,users[1],restricting=True)
            async with role() as other:
                await asyncio.wait_for(finish(other,rid),5)
                await cur.execute('SELECT pg_try_advisory_xact_lock(hashtextextended(%s,0)) AS claimed',('audience-learning-processing-v1:'+users[0],))
                assert (await cur.fetchone())['claimed'],'Deferred room retained a participant lease'
    client.portal.call(scenario)
    assert conn.execute('SELECT state FROM game_rooms WHERE id=%s',(rid,)).fetchone()==('running',)
    assert [history(conn,user) for user in users[:2]]==before


def test_restriction_waits_for_admitted_game_transaction(client,game_case,monkeypatch):
    conn,rid,users,headers,frozen=room_case(client,game_case)
    choices(conn,rid,users[0],frozen);monkeypatch.setattr(settings,'audience_gate_enabled',True)
    async def scenario():
        async with role() as cur:
            await finish(cur,rid)
            task=asyncio.create_task(asyncio.to_thread(declare,client,'under18',headers=headers[0],user_id=users[0],expected_version=1))
            try:await wait_for_advisory_wait(cur,task)
            except BaseException:task.cancel();raise
        response=await asyncio.wait_for(task,5);assert response.status_code==200,response.text
    client.portal.call(scenario)
    before=history(conn,users[0]);run(client,finish,rid)
    assert history(conn,users[0])==before
    assert conn.execute('SELECT category FROM account_audience WHERE user_id=%s',(users[0],)).fetchone()==('under18',)


def test_closed_player_is_not_finalized_but_other_player_is(client,game_case,monkeypatch):
    conn,rid,users,_,frozen=room_case(client,game_case,'duel',2)
    for user in users[:2]:choices(conn,rid,user,frozen)
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    run(client,account_tools.close,users[0],0)
    before=history(conn,users[0]);run(client,finish,rid)
    assert history(conn,users[0])==before
    assert conn.execute('SELECT user_id FROM game_completion_rewards WHERE room_id=%s',(rid,)).fetchall()==[(users[1],)]


def test_withheld_choices_cannot_be_regraded_after_confirmation_or_flag_off(client,game_case,monkeypatch):
    conn,rid,users,_,frozen=room_case(client,game_case,'party',2)
    choices(conn,rid,users[1],frozen)
    conn.execute('DELETE FROM account_audience WHERE user_id=%s',(users[1],))
    monkeypatch.setattr(settings,'audience_gate_enabled',True);run(client,advance,rid)
    assert conn.execute('SELECT state FROM game_rooms WHERE id=%s',(rid,)).fetchone()==('running',)
    conn.execute("INSERT INTO account_audience(user_id,category) VALUES(%s,'adult')",(users[1],))
    async def rejoin(cur):await routes.add_member(cur,await g.room(cur,rid),users[1])
    with pytest.raises(HTTPException) as exc:run(client,rejoin)
    assert exc.value.status_code==409
    monkeypatch.setattr(settings,'audience_gate_enabled',False);before=history(conn,users[1])
    run(client,finish,rid)
    assert history(conn,users[1])==before
    assert conn.execute('SELECT count(*) FROM game_events WHERE room_id=%s AND action=%s',(rid,game_audience.ENDED)).fetchone()==(1,)


def test_flag_off_keeps_original_unknown_age_completion(client,game_case):
    conn,rid,users,_,frozen=room_case(client,game_case)
    choices(conn,rid,users[0],frozen);conn.execute('DELETE FROM account_audience WHERE user_id=%s',(users[0],))
    run(client,finish,rid)
    assert conn.execute('SELECT count(*) FROM attempts WHERE user_id=%s',(users[0],)).fetchone()==(len(frozen),)
    assert conn.execute('SELECT user_id FROM game_completion_rewards WHERE room_id=%s',(rid,)).fetchall()==[(users[0],)]


def test_marker_is_once_only_and_generic_plan_uses_partial_index(client,game_case):
    conn,rid,users,_,_=room_case(client,game_case)
    conn.execute("INSERT INTO game_events(room_id,actor_id,action) VALUES(%s,%s,'audience_access_ended')",(rid,users[0]))
    with pytest.raises(UniqueViolation):
        conn.execute("INSERT INTO game_events(room_id,actor_id,action) VALUES(%s,%s,'audience_access_ended')",(rid,users[0]))
    # Ordinary game events can repeat. Keep the marker index selective while
    # exercising a generic prepared plan, as a pooled production driver can do.
    conn.execute("INSERT INTO game_events(room_id,actor_id,action) SELECT %s,%s,'synthetic' FROM generate_series(1,4000)",(rid,users[0]))
    conn.execute('ANALYZE game_events')
    with conn.transaction():
        conn.execute('SET LOCAL ROLE mpsc')
        conn.execute('SET LOCAL plan_cache_mode=force_generic_plan')
        conn.execute("PREPARE marker_check(text,text) AS SELECT 1 FROM game_events WHERE room_id=$1 AND actor_id=$2 AND action='audience_access_ended'")
        try:
            plan=conn.execute("EXPLAIN (FORMAT JSON) EXECUTE marker_check('missing','missing')").fetchone()[0]
            import json
            assert 'game_audience_marker_once' in json.dumps(plan),plan
            assert conn.execute("EXECUTE marker_check('missing','missing')").fetchall()==[]
        finally:conn.execute('DEALLOCATE marker_check')
