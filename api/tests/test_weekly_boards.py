"""Real-role weekly standings: consent, blocks, bounded ties and disclosure."""
from datetime import datetime,timedelta,timezone
from uuid import uuid4
import pytest
from psycopg.types.json import Jsonb
from app.services import weekly_boards
from test_learning_loop import run
from test_rewards import learner


@pytest.fixture(autouse=True)
def reset_standings(database):
    database[1].execute('UPDATE reward_profiles SET board_public=false')


def profile(conn,xp=0,public=True,at=None):
    user='board-'+uuid4().hex
    conn.execute('INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)',(user,user,user+'@example.test'))
    conn.execute('INSERT INTO reward_profiles(user_id,board_public) VALUES(%s,%s)',(user,public))
    if xp:conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note,created_at) VALUES(%s,%s,'adjustment',%s,99,'Isolated board fixture',COALESCE(%s,now()))",(user,uuid4().hex,xp,at))
    return user


def game(conn,user,score=100,mode='speed',at=None,*,state='finished',left=False,scored=True,public=False):
    rid='board-game-'+uuid4().hex
    conn.execute("INSERT INTO game_rooms(id,owner_id,mode,state,capacity,questions,round_seconds,request_key,request_hash,finished_at) VALUES(%s,%s,%s,%s,2,'[]',20,%s,'fixture',COALESCE(%s,now()))",(rid,user,mode,state,rid,at))
    conn.execute("INSERT INTO game_members(room_id,user_id,score,correct,public_result,released_at,left_at) VALUES(%s,%s,%s,%s,%s,now(),CASE WHEN %s THEN now() END)",(rid,user,score,int(scored),public,left))
    return rid


def test_xp_top_neighborhood_private_rank_and_league(client,learner,database):
    user,_=learner;conn=database[1]
    others=[profile(conn,290-i*5) for i in range(40)]
    conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,note) VALUES(%s,%s,'adjustment',173,'Isolated viewer')",(user,uuid4().hex))
    other_league=profile(conn,700)
    before=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    board=run(client,weekly_boards.xp,user)
    assert board['league']['floor_xp']==0 and board['total']==40
    assert len(board['top'])==10 and len(board['items'])<=35
    assert board['placement']=={'rank':25,'xp':173,'public':False}
    assert all(row['handle'] not in (user,other_league) for row in board['items'])
    assert all(set(row)=={'handle','xp','rank','avatar','level','profile_public','user_id'} for row in board['items'])
    assert all(row['profile_public'] is False and row['user_id'] is None and row['level']>=1 for row in board['items'])
    assert any(row['rank']>=23 for row in board['nearby'])
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==before
    # Another person's view never inserts this private learner or shifts ranks.
    other=run(client,weekly_boards.xp,others[0])
    assert other['placement']['rank']==1 and all(row['handle']!=user for row in other['items'])
    conn.execute('INSERT INTO reward_profiles(user_id,board_public) VALUES(%s,true)',(user,))
    public=client.get('/api/rewards/leaderboard').json()
    assert public['placement']['public'] and any(row['handle']==user for row in public['nearby'])
    assert client.get('/api/rewards/leaderboard?period=month&contract=2').status_code==422


def test_ties_bounded_blocks_both_directions_and_opt_out(client,learner,database):
    conn=database[1];user,_=learner
    tie=[profile(conn,10) for _ in range(42)]
    conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,note) VALUES(%s,%s,'adjustment',10,'Isolated tie')",(user,uuid4().hex))
    conn.execute('INSERT INTO reward_profiles(user_id,board_public) VALUES(%s,true)',(user,))
    for blocker,blocked in ((user,tie[0]),(tie[1],user)):
        conn.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)',(blocker,blocked))
    board=run(client,weekly_boards.xp,user)
    assert board['neighborhood_truncated'] and len(board['nearby'])==25
    assert {r['rank'] for r in board['items']}=={1}
    assert any(r['handle']==user for r in board['nearby'])
    assert all(r['handle'] not in tie[:2] for r in board['items'])
    conn.execute('UPDATE reward_profiles SET board_public=false WHERE user_id=%s',(tie[2],))
    assert all(r['handle']!=tie[2] for r in run(client,weekly_boards.xp,user)['items'])


def test_ist_week_half_open_and_future_rows(client,database):
    conn=database[1];at=datetime(2030,1,7,0,0,tzinfo=timezone.utc) # Monday05:30 IST
    boundary=datetime(2030,1,6,18,30,tzinfo=timezone.utc)
    user=profile(conn,10,True,boundary)
    profile(conn,299,True,boundary-timedelta(microseconds=1))
    profile(conn,298,True,at+timedelta(seconds=1))
    profile(conn,297,True,boundary+timedelta(days=7))
    async def check(cur):return await weekly_boards.xp(cur,user,as_of=at)
    b=run(client,check)
    assert b['period_start']==boundary and b['period_end']==boundary+timedelta(days=7)
    assert len(b['items'])==1 and b['items'][0]['handle']==user and b['items'][0]['xp']==10 and b['items'][0]['rank']==1
    assert b['items'][0]['user_id']==user  # self row always linkable


def test_modes_disclosure_no_individual_result_consent_override(client,learner,database):
    conn=database[1];user,_=learner
    shown=profile(conn);hidden=profile(conn,public=False);blocked=profile(conn)
    for who,score in ((shown,111),(hidden,999),(blocked,888)):
        game(conn,who,score,public=True)
    for state,scored,left in [('running',True,False),('finished',False,False),('finished',True,True)]:
        game(conn,shown,9000,state=state,scored=scored,left=left)
    game(conn,shown,9001,at=datetime.now(timezone.utc)+timedelta(days=8))
    conn.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)',(blocked,user))
    b=client.get('/api/games/leaderboard?track=speed').json()
    assert len(b['items'])==1 and b['items'][0]['handle']==shown and b['items'][0]['score']==111 and b['items'][0]['rank']==1,b
    assert b['items'][0]['profile_public'] is False and b['items'][0]['user_id'] is None
    assert run(client,weekly_boards.games,user,'speed')['items']==b['items']
    assert client.get('/api/games/leaderboard?track=gk_gs&contract=2').status_code==422
    assert client.get('/api/games/leaderboard?track=speed&period=month&contract=2').status_code==422
    assert client.get('/api/games/leaderboard?track=gauntlet').json()['items']==[]


def test_duel_strict_wins_ties_and_empty_or_abandoned_opponents(client,learner,database):
    conn=database[1];user,_=learner;opponent=profile(conn)
    conn.execute('INSERT INTO reward_profiles(user_id,board_public) VALUES(%s,true)',(user,))
    for mine,theirs,left,answered in [(200,100,False,1),(200,200,False,1),(200,100,True,1),(200,0,False,0)]:
        rid=game(conn,user,mine,'duel')
        conn.execute("INSERT INTO game_members(room_id,user_id,score,correct,released_at,left_at) VALUES(%s,%s,%s,%s,now(),CASE WHEN %s THEN now() END)",(rid,opponent,theirs,answered,left))
    b=run(client,weekly_boards.games,user,'duel')
    assert b['placement']['score']==1 and next(r for r in b['items'] if r['handle']==user)['score']==1


def test_daily_best_consecutive_completed_days_within_week(client,learner,database):
    conn=database[1];user,_=learner
    conn.execute('INSERT INTO reward_profiles(user_id,board_public) VALUES(%s,true)',(user,))
    at=datetime(2030,1,13,10,tzinfo=timezone.utc)
    for offset in (-1,0,1,3,4,5):
        day=datetime(2030,1,7,8,tzinfo=timezone.utc)+timedelta(days=offset);did=day.date().isoformat()
        conn.execute("INSERT INTO game_dailies(id,opens_at,closes_at,questions) VALUES(%s,%s,%s,'[]') ON CONFLICT DO NOTHING",(did,day-timedelta(hours=8),day+timedelta(hours=16)))
        rid=game(conn,user,mode='daily',at=day)
        conn.execute('UPDATE game_rooms SET daily_id=%s WHERE id=%s',(did,rid))
        conn.execute('INSERT INTO game_daily_entries(daily_id,user_id,room_id) VALUES(%s,%s,%s)',(did,user,rid))
    async def check(cur):return await weekly_boards.games(cur,user,'daily',as_of=at)
    assert run(client,check)['placement']['score']==3


def test_public_learner_profile_enrichment_and_board_link(client,learner,database):
    conn=database[1];viewer,_=learner
    champ=profile(conn,xp=240,public=True)
    conn.execute("INSERT INTO creator_profiles(user_id,public,bio) VALUES(%s,true,'Preparing for MPSC')",(champ,))
    conn.execute("UPDATE reward_profiles SET district='Aizawl' WHERE user_id=%s",(champ,))
    board=run(client,weekly_boards.xp,viewer)
    row=next(r for r in board['items'] if r['handle']==champ)
    assert row['profile_public'] is True and row['user_id']==champ and row['level']>=2
    res=client.get(f'/api/creators/{champ}')
    assert res.status_code==200,res.text
    body=res.json()
    assert body['level']>=2 and body['scholar_title']
    assert body['district']=='Aizawl' and body['board_public'] is True
    assert isinstance(body['target_exams'],list)
    assert body['scores']['weekly_xp']==240 and body['scores']['lifetime_xp']==240
    # When board_public is turned off, another viewer cannot see district or scores
    conn.execute('UPDATE reward_profiles SET board_public=false WHERE user_id=%s',(champ,))
    priv=client.get(f'/api/creators/{champ}').json()
    assert priv['board_public'] is False and priv['district'] is None and priv['scores'] is None
    # Algorithmic discovery surfaces public learners cleanly and hides weekly_xp when private
    disc=client.get('/api/creators/discover?seed=test-rot-1')
    assert disc.status_code==200,disc.text
    dbody=disc.json()
    assert 'learners' in dbody and 'materials' in dbody
    found=next((x for x in dbody['learners'] if x['id']==champ),None)
    assert found is not None and found['weekly_xp'] is None and found['match_reason']
