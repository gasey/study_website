"""Desk binding exercises the real frozen party controller and ordinary rewards."""
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import json
import pytest
from psycopg.types.json import Jsonb
from test_games_search import game_case


@pytest.fixture
def case(client,game_case,monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings,'study_desks_private_enabled',True)
    conn,subject,users,h,ids = game_case
    did='desk_'+uuid4().hex
    conn.execute('INSERT INTO study_desks(id,owner_id,name) VALUES(%s,%s,\'Synthetic session Desk\')',(did,users[0]))
    for user in users[:5]:
        conn.execute('INSERT INTO study_desk_members(desk_id,user_id) VALUES(%s,%s)',(did,user))
    shares=[]
    for qid in ids[:10]:
        iid='item_'+uuid4().hex;shares.append(iid)
        conn.execute("INSERT INTO study_desk_items(id,desk_id,author_id,kind,question_id,request_key,request_hash) VALUES(%s,%s,%s,'question',%s,%s,'test')",(iid,did,users[0],qid,uuid4().hex))
    return conn,did,users,h,ids,shares


def overview(client,c,n=0):
    r=client.get(f'/api/desk/rooms/{c[1]}/practice',headers=c[3][n])
    assert r.status_code==200,r.text
    assert r.headers['cache-control']=='private, no-store'
    return r.json()


def create(client,c,key=None,preview=None):
    data={'request_key':key or uuid4().hex,'preview_hash':(preview or overview(client,c)['preview'])['context_hash']}
    return client.post(f'/api/desk/rooms/{c[1]}/practice',headers=c[3][0],json=data)


def join(client,c,r,n=1,**changes):
    return client.post(f'/api/desk/rooms/{c[1]}/practice/{r["id"]}/join',headers=c[3][n],json={'context_hash':r['context_hash'],**changes})


def start(client,c):
    r=create(client,c);assert r.status_code==200,r.text;r=r.json()
    result=join(client,c,r);assert result.status_code==200,result.text
    for h in c[3][:2]:
        response=client.post(f'/api/games/rooms/{r["id"]}/ready',headers=h,json={'ready':True})
        assert response.status_code==200,response.text
    response=client.post(f'/api/games/rooms/{r["id"]}/start',headers=c[3][0],json={})
    assert response.status_code==200,response.text
    return response.json()


def play(client,c,r):
    conn=c[0]
    while r['state']=='running':
        conn.execute("UPDATE game_rooms SET round_started_at=clock_timestamp()-interval '4 seconds' WHERE id=%s",(r['id'],))
        for h in c[3][:2]:
            response=client.post(f'/api/games/rooms/{r["id"]}/answer',headers=h,json={'position':r['position'],'chosen_index':1})
            assert response.status_code==200,response.text
        r=response.json()
    return r


def test_preview_only_explicit_shared_eligible_sources_and_stale_confirmation(client,case):
    c=case;conn,did,users,h,ids,shares=c
    p=overview(client,c)['preview'];assert p['available']==10 and p['required']==10 and p['capacity']==4 and p['can_start']
    assert 'answer_text' not in json.dumps(p) and 'desk_sources' not in json.dumps(p)
    conn.execute("UPDATE study_desk_items SET kind='note' WHERE id=%s",(shares[0],))
    r=create(client,c,preview=p);assert r.status_code==409,r.text
    p=overview(client,c)['preview'];assert p['available']==9 and not p['can_start']
    assert create(client,c,preview=p).status_code==422
    conn.execute("UPDATE study_desk_items SET kind='mistake' WHERE id=%s",(shares[0],))
    conn.execute("UPDATE study_desk_members SET sharing='{"+'"mistakes":true'+"}' WHERE desk_id=%s",(did,))
    assert overview(client,c)['preview']['available']==9,'Mistake consent does not authorize a frozen party copy'
    conn.execute("UPDATE study_desk_items SET kind='bookmark' WHERE id=%s",(shares[0],))
    conn.execute("UPDATE canonical_questions SET answer_source='derived' WHERE id=%s",(ids[0],))
    assert overview(client,c)['preview']['available']==9
    conn.execute("UPDATE canonical_questions SET answer_source='official' WHERE id=%s",(ids[0],))
    assert overview(client,c)['preview']['available']==10
    assert client.get(f'/api/desk/rooms/{did}/practice',headers=h[5]).status_code==404


def test_create_replay_ready_join_limits_and_frozen_shared_set(client,case):
    c=case;conn,did,users,h,ids,shares=c;p=overview(client,c)['preview'];key=uuid4().hex
    with ThreadPoolExecutor(max_workers=2) as pool:
        rs=list(pool.map(lambda _:create(client,c,key,p),range(2)))
    assert [r.status_code for r in rs]==[200,200],[r.text for r in rs]
    r=rs[0].json();assert rs[1].json()['id']==r['id']
    assert r['mode']=='party' and r['desk_id']==did and r['join_code'] is None and r['question'] is None
    raw=conn.execute('SELECT questions FROM game_rooms WHERE id=%s',(r['id'],)).fetchone()[0]
    assert {q['id'] for q in raw}==set(ids[:10])
    assert overview(client,c)['active_game']['id']==r['id']
    assert join(client,c,r,5).status_code==404
    assert join(client,c,r,1,context_hash='0'*64).status_code==409
    for n in (1,2,3):assert join(client,c,r,n).status_code==200
    assert join(client,c,r,4).status_code==409
    assert join(client,c,r,1).status_code==200,'Join replay returns same reservation'
    assert client.post(f'/api/games/rooms/{r["id"]}/start',headers=h[0],json={}).status_code==409
    assert client.post(f'/api/games/rooms/{r["id"]}/start',headers=h[1],json={}).status_code==403
    for header in h[:4]:assert client.post(f'/api/games/rooms/{r["id"]}/ready',headers=header,json={'ready':True}).status_code==200
    running=client.post(f'/api/games/rooms/{r["id"]}/start',headers=h[0],json={});assert running.status_code==200,running.text
    assert running.json()['question']['id'] in ids[:10] and 'answer_text' not in json.dumps(running.json())
    detail=client.get(f'/api/questions/{raw[0]["id"]}',headers=h[1])
    assert detail.status_code==200 and detail.json().get('answer_text') is None
    assert join(client,c,r,4).status_code==409
    assert conn.execute('SELECT count(*) FROM attempts WHERE user_id=ANY(%s)',(users,)).fetchone()[0]==0


@pytest.mark.parametrize('reverse',[False,True])
def test_block_visibility_and_source_withdrawal_release_without_rewards(client,case,reverse):
    c=case;conn,did,users,h,ids,shares=c;r=start(client,c)
    a,b=(users[1],users[0]) if reverse else (users[0],users[1])
    conn.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)',(a,b))
    assert not overview(client,c,1)['sessions'] and overview(client,c,1)['preview']['available']==0
    assert client.get(f'/api/games/rooms/{r["id"]}',headers=h[1]).status_code==403
    # The actual worker adapter executes with the actual app role, no HTTP actor.
    advance(conn,r['id'])
    assert conn.execute('SELECT count(*) FROM game_members WHERE room_id=%s AND left_at IS NULL',(r['id'],)).fetchone()[0]==0
    assert conn.execute('SELECT count(*) FROM reward_ledger WHERE user_id=ANY(%s)',(users,)).fetchone()[0]==0


def advance(conn,rid):
    import asyncio,psycopg
    from psycopg.rows import dict_row
    from app.services import games as g
    async def run():
        async with await psycopg.AsyncConnection.connect(conn.info.dsn,row_factory=dict_row) as db:
            async with db.cursor() as cur:
                await cur.execute('SET LOCAL ROLE mpsc')
                await g.advance(cur,await g.room(cur,rid),await g.clock(cur))
    asyncio.run(run())


@pytest.mark.parametrize('change',['share','author_departure','player_departure','closure','flag'])
def test_lifecycle_worker_rechecks_sources_membership_epochs_and_flag(client,case,monkeypatch,change):
    c=case;conn,did,users,h,ids,shares=c;r=start(client,c)
    response=client.post(f'/api/games/rooms/{r["id"]}/answer',headers=h[1],json={'position':0,'chosen_index':1})
    assert response.status_code==200,response.text
    if change=='share':conn.execute('UPDATE study_desk_items SET deleted_at=now() WHERE id=%s',(shares[0],))
    elif change=='author_departure':conn.execute('UPDATE study_desk_members SET left_at=now() WHERE desk_id=%s AND user_id=%s',(did,users[0]))
    elif change=='player_departure':
        conn.execute('UPDATE study_desk_members SET left_at=now() WHERE desk_id=%s AND user_id=%s',(did,users[1]))
        # Rejoining this Desk does not restore an old game seat.
        conn.execute('UPDATE study_desk_members SET left_at=NULL,joined_at=clock_timestamp() WHERE desk_id=%s AND user_id=%s',(did,users[1]))
    elif change=='closure':conn.execute('UPDATE study_desks SET closed_at=now() WHERE id=%s',(did,))
    else:
        from app.config import settings
        monkeypatch.setattr(settings,'study_desks_private_enabled',False)
        # A direct worker shares settings only in this process; use direct async.
        advance(conn,r['id'])
    advance(conn,r['id'])
    assert conn.execute('SELECT released_at IS NOT NULL FROM game_members WHERE room_id=%s AND user_id=%s',(r['id'],users[1])).fetchone()[0]
    assert conn.execute('SELECT count(*) FROM reward_ledger WHERE user_id=%s',(users[1],)).fetchone()[0]==0
    assert client.get(f'/api/games/rooms/{r["id"]}',headers=h[1]).status_code in (404,409)
    # Access revocation never prevents explicit reservation release.
    assert client.post(f'/api/games/rooms/{r["id"]}/leave',headers=h[1],json={}).status_code==200


def test_normal_completion_discovery_play_cap_and_replay(client,case):
    c=case;conn,did,users,h,ids,shares=c
    for n in range(3):
        # Synthetic timing compresses several real sessions into seconds.
        conn.execute('DELETE FROM review_rate_buckets')
        r=play(client,c,start(client,c));assert r['state']=='finished' and len(r['review'])==10
        assert r['players'][0]['correct']==10
        before=conn.execute('SELECT count(*) FROM reward_ledger WHERE user_id=ANY(%s)',(users,)).fetchone()[0]
        assert client.get(f'/api/games/rooms/{r["id"]}',headers=h[0]).status_code==200
        assert client.post(f'/api/games/rooms/{r["id"]}/answer',headers=h[0],json={'position':9,'chosen_index':1}).status_code==200
        assert conn.execute('SELECT count(*) FROM reward_ledger WHERE user_id=ANY(%s)',(users,)).fetchone()[0]==before
    for user in users[:2]:
        assert conn.execute('SELECT count(*) FROM reward_question_claims WHERE user_id=%s',(user,)).fetchone()[0]==10
        rewards=conn.execute('SELECT count(*),sum(l.points) FROM game_completion_rewards c JOIN reward_ledger l ON l.id=c.ledger_id WHERE c.user_id=%s',(user,)).fetchone()
        assert rewards==(3,4),rewards
        assert conn.execute("SELECT count(*) FROM reward_ledger WHERE user_id=%s AND event_key LIKE 'desk:%%'",(user,)).fetchone()[0]==0


def test_per_viewer_mock_and_cup_embargo(client,case):
    c=case;conn,did,users,h,ids,shares=c;r=create(client,c).json()
    mock='mock_'+uuid4().hex
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,%s,'udc',%s,600)",(mock,users[1],ids[:1]))
    assert overview(client,c,1)['preview']['available']==9
    assert join(client,c,r).status_code==409
    conn.execute('UPDATE mock_sessions SET submitted_at=now(),elapsed_seconds=0,score=0,n_correct=0,n_wrong=0,n_skipped=1 WHERE id=%s',(mock,))
    cup='cup_'+uuid4().hex;embargo='game_'+uuid4().hex
    conn.execute("INSERT INTO game_cups(id,opens_at,closes_at,questions) VALUES(%s,now()-interval '1 hour',now()+interval '1 hour',%s)",(cup,Jsonb([{'id':ids[0]}])))
    conn.execute("INSERT INTO game_rooms(id,owner_id,mode,state,capacity,round_seconds,questions,request_key,request_hash,cup_id) VALUES(%s,%s,'cup','finished',1,30,%s,%s,'test',%s)",(embargo,users[1],Jsonb([{'id':ids[0]}]),uuid4().hex,cup))
    conn.execute('INSERT INTO game_members(room_id,user_id,released_at) VALUES(%s,%s,now())',(embargo,users[1]))
    assert overview(client,c,1)['preview']['available']==9
    assert join(client,c,r).status_code==409
    # Cup windows are immutable. A different member without the embargo may join.
    assert join(client,c,r,2).status_code==200
    assert client.get(f'/api/desk/rooms/{did}/items',headers=h[2]).json()['items']==[]
    assert client.get(f'/api/questions/{ids[0]}/answer-comparison',headers=h[2]).status_code==409


def test_native_paths_closed_and_inherited_game_controls_reject_bound_room(client,case,actor):
    from test_mobile_companion import connect
    from app.services.mobile_identity import capabilities
    import hashlib
    c=case;conn,did,users,h,ids,shares=c;r=create(client,c).json()
    token='test-session-'+users[0]
    conn.execute("INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES(%s,%s,now()+interval '1 day')",(hashlib.sha256(token.encode()).hexdigest(),users[0]))
    mobile,_=connect(client,actor,users[0])
    assert 'desk_practice' not in capabilities()
    assert client.get(f'/api/desk/rooms/{did}/practice',headers=mobile).status_code==403
    for path,body in [('/practice',{'preview_hash':'0'*64,'request_key':uuid4().hex}),('/practice/'+r['id']+'/join',{'context_hash':r['context_hash']})]:
        assert client.post(f'/api/desk/rooms/{did}'+path,headers=mobile,json=body).status_code==403
    assert client.get('/api/games/rooms/'+r['id'],headers=mobile).status_code==200
    for action,body in [('ready',{'ready':True}),('start',{}),('answer',{'position':0,'chosen_index':1})]:
        response=client.post(f'/api/games/rooms/{r["id"]}/{action}',headers=mobile,json=body)
        assert response.status_code==403,response.text
    assert client.post(f'/api/games/rooms/{r["id"]}/leave',headers=mobile,json={}).status_code==200


def test_restriction_expiry_seat_release_and_schema_binding_guards(client,case):
    import psycopg
    c=case;conn,did,users,h,ids,shares=c;r=create(client,c).json()
    action=conn.execute("INSERT INTO mod_actions(actor_id,action,target_user,note) VALUES('owner','mute',%s,'Synthetic restriction') RETURNING id",(users[1],)).fetchone()[0]
    conn.execute("INSERT INTO sanctions(user_id,kind,step,ends_at,action_id) VALUES(%s,'mute',1,now()+interval '1 hour',%s)",(users[1],action))
    assert join(client,c,r).status_code==403
    conn.execute('UPDATE sanctions SET lifted_at=now() WHERE user_id=%s',(users[1],))
    assert join(client,c,r).status_code==200
    assert client.post(f'/api/games/rooms/{r["id"]}/leave',headers=h[1],json={}).status_code==200
    assert join(client,c,r).status_code==409,'A forfeited seat is not resurrected'
    assert client.get('/api/games/join-preview?code=ABCDEF123456',headers=h[4]).status_code==404
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("UPDATE game_rooms SET join_code='ABCDEF123456' WHERE id=%s",(r['id'],))
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute('UPDATE game_rooms SET desk_id=NULL WHERE id=%s',(r['id'],))
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("INSERT INTO game_rooms(id,owner_id,mode,capacity,questions,round_seconds,request_key,request_hash,desk_id) VALUES(%s,%s,'duel',2,'[]',20,%s,'test',%s)",('bad_'+uuid4().hex,users[0],uuid4().hex,did))
    conn.execute("UPDATE game_rooms SET created_at=now()-interval '11 minutes' WHERE id=%s",(r['id'],))
    assert not overview(client,c)['sessions']
    advance(conn,r['id'])
    assert conn.execute('SELECT state FROM game_rooms WHERE id=%s',(r['id'],)).fetchone()[0]=='cancelled'
    assert conn.execute('SELECT count(*) FROM game_members WHERE room_id=%s AND released_at IS NULL',(r['id'],)).fetchone()[0]==0
