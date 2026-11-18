"""Room completion cannot hold a tier lock while waiting for another player's wallet."""
from contextlib import asynccontextmanager
import psycopg
from test_discussions import database,client
from test_games_search import game_case,create,play


def test_all_player_reward_locks_precede_tier_capture_at_fiftieth_attempt(client,database,game_case,monkeypatch):
    conn,subject,users,headers,ids=game_case
    pid=conn.execute("INSERT INTO posts(kind,author_id,body) VALUES('study','author','Synthetic shared author for game/account lock regression') RETURNING id").fetchone()[0]
    for user in users[:2]:
        conn.execute("INSERT INTO attempts(user_id,canonical_id,chosen_text,correct,context) SELECT %s,%s,'A',false,'practice' FROM generate_series(1,49)",(user,ids[0]))
        conn.execute('INSERT INTO post_votes(post_id,user_id) VALUES(%s,%s)',(pid,user))
    room=create(client,headers[0],subject,mode='duel',matchmaking=True).json()
    joined=create(client,headers[1],subject,mode='duel',matchmaking=True);assert joined.status_code==200,joined.text
    assert joined.json()['id']==room['id']
    assert client.post('/api/games/rooms/'+room['id']+'/ready',headers=headers[0],json={'ready':True}).status_code==200
    room=client.post('/api/games/rooms/'+room['id']+'/ready',headers=headers[1],json={'ready':True}).json()
    from app.routers import games
    original=games.cursor;checked=[]
    class CheckedCursor:
        def __init__(self,cur):self.cur=cur
        def __getattr__(self,name):return getattr(self.cur,name)
        async def execute(self,query,args=None):
            if str(query).lstrip().startswith('INSERT INTO attempts'):
                # A separate real session represents account closure's first
                # reward lock. It must be unable to enter while a room can hold
                # any tier capture lock for these players' shared voted author.
                with psycopg.connect('dbname='+database[0]) as probe:
                    for user in users[:2]:
                        acquired=probe.execute('SELECT pg_try_advisory_xact_lock(hashtext(%s))',('rewards:'+user,)).fetchone()[0]
                        assert not acquired,'Room must own every player reward lock before tier capture'
                    probe.rollback()
                checked.append(args[0])
            return await self.cur.execute(query,args)
    @asynccontextmanager
    async def guarded():
        async with original() as cur:yield CheckedCursor(cur)
    monkeypatch.setattr(games,'cursor',guarded)
    for _ in range(10):
        first=play(client,headers[0],room);assert first.status_code==200,first.text
        second=play(client,headers[1],first.json());assert second.status_code==200,second.text
        room=second.json()
    assert room['state']=='finished' and len(room['players'])==2
    assert set(checked)==set(users[:2]) and len(checked)==20
    assert conn.execute('SELECT count(*) FROM attempts WHERE user_id=ANY(%s) AND context=\'game\'',(users[:2],)).fetchone()[0]==20
