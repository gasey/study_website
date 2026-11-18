"""Chronological following uses existing consent, moderation and disclosure gates."""
from uuid import uuid4
from psycopg.types.json import Jsonb
from test_discussions import database, client, question, answer, create, approve


def followed(client, actor, question, kind='doubt'):
    qid, conn = question
    h = answer(client, actor, qid, 'author')
    pid = create(client, h, qid, kind=kind).json()['id']
    approve(client, actor, pid)
    conn.execute("INSERT INTO creator_profiles(user_id,public) VALUES('author',true) ON CONFLICT(user_id) DO UPDATE SET public=true")
    h = actor('outsider')
    assert client.post('/api/creators/author/follow', headers=h, json={'enabled':True}).status_code == 200
    return qid, conn, pid


def feed(client, **params):
    result = client.get('/api/community/feed', params={'tab':'following', **params})
    assert result.status_code == 200, result.text
    assert result.headers['cache-control'] == 'private, no-store'
    assert result.json()['available']
    return result.json()


def ids(client, **params):
    return [p['id'] for p in feed(client, **params)['items']]


def test_following_requires_disclosure_and_current_public_profile(client, actor, question):
    qid, conn, pid = followed(client, actor, question)
    assert pid not in ids(client)  # Following never discloses a question's answer.
    h = answer(client, actor, qid, 'outsider')
    assert pid in ids(client)
    assert client.post('/api/creators/author/follow', headers=h, json={'enabled':False}).status_code == 200
    assert pid not in ids(client)
    client.post('/api/creators/author/follow', headers=h, json={'enabled':True})
    conn.execute("UPDATE creator_profiles SET public=false WHERE user_id='author'")
    assert pid not in ids(client)
    conn.execute("UPDATE creator_profiles SET public=true WHERE user_id='author'")
    assert pid in ids(client)
    actor('reviewer2')  # Another account's graph never carries over.
    assert not ids(client)
    client.cookies.clear()
    assert not ids(client)


def test_following_blocks_both_directions_and_moderation(client, actor, question):
    qid, conn, pid = followed(client, actor, question)
    answer(client, actor, qid, 'outsider')
    for blocker, blocked in [('author','outsider'), ('outsider','author')]:
        # Keep the graph row to prove the read gate independently of block's cleanup.
        conn.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)', (blocker, blocked))
        assert pid not in ids(client)
        conn.execute('DELETE FROM creator_blocks WHERE user_id=%s AND blocked_id=%s', (blocker, blocked))
    for flag in ['hidden', 'needs_approval', 'before_fix']:
        conn.execute(f'UPDATE posts SET {flag}=true WHERE id=%s', (pid,))
        assert pid not in ids(client)
        conn.execute(f'UPDATE posts SET {flag}=false WHERE id=%s', (pid,))
    assert pid in ids(client)


def test_following_is_chronological_paged_and_mock_protected(client, actor, question):
    qid, conn, first = followed(client, actor, question, kind='explanation')
    h = actor('author')
    second = create(client, h, qid, body='A newer synthetic discussion about the same wording.').json()['id']
    approve(client, actor, second)
    conn.execute('UPDATE posts SET pinned=true WHERE id=%s', (first,))
    answer(client, actor, qid, 'outsider')
    page = feed(client, limit=1)
    assert page['items'][0]['id'] == second and page['has_more']
    assert ids(client, limit=1, offset=1) == [first]
    mock = 'following_mock_' + uuid4().hex
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,'outsider','udc',%s,600)", (mock, [qid]))
    try:
        assert not ({first, second} & set(ids(client)))
    finally:
        conn.execute('DELETE FROM mock_sessions WHERE id=%s', (mock,))
    assert {first, second} <= set(ids(client))


def test_following_answer_reveal_is_not_an_attempt_or_award(client, actor, question):
    qid, conn, pid = followed(client, actor, question)
    before = conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    attempts = conn.execute("SELECT count(*) FROM attempts WHERE user_id='outsider'").fetchone()[0]
    assert client.post('/api/questions/' + qid + '/reveal', headers=actor('outsider')).status_code == 200
    assert pid in ids(client)
    assert pid in [p['id'] for p in client.get('/api/community/feed').json()['items']]
    assert conn.execute("SELECT count(*) FROM attempts WHERE user_id='outsider'").fetchone()[0] == attempts
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0] == before


def test_following_exceptional_disclosure_and_game_protection(client, actor, question):
    qid, conn, pid = followed(client, actor, question)
    conn.execute("UPDATE canonical_questions SET status='held' WHERE id=%s", (qid,))
    h = actor('outsider')
    assert pid not in ids(client)
    assert client.post(f'/api/community/questions/{qid}/discussion/open', headers=h, json={}).status_code == 200
    assert pid in ids(client)
    room = 'following_room_' + uuid4().hex
    conn.execute("INSERT INTO game_rooms(id,mode,state,owner_id,capacity,round_seconds,request_key,request_hash,questions) VALUES(%s,'gauntlet','running','outsider',1,30,%s,'synthetic',%s)", (room, room, Jsonb([{'id':qid}])))
    conn.execute("INSERT INTO game_members(room_id,user_id) VALUES(%s,'outsider')", (room,))
    try:
        assert pid not in ids(client)
    finally:
        conn.execute('DELETE FROM game_members WHERE room_id=%s', (room,))
        conn.execute('DELETE FROM game_rooms WHERE id=%s', (room,))
    assert pid in ids(client)


def test_following_query_with_actual_runtime_role(client, actor, question):
    qid, conn, pid = followed(client, actor, question)
    answer(client, actor, qid, 'outsider')
    from app.routers.community import community_feed
    from fastapi import Response
    import asyncio
    from psycopg.rows import dict_row
    # Run the actual reader under mpsc, rather than a superuser-only SQL check.
    async def check():
        from app import db
        original = db._pool
        from psycopg_pool import AsyncConnectionPool
        async with AsyncConnectionPool('postgresql:///' + conn.info.dbname, kwargs={'row_factory':dict_row,'options':'-c role=mpsc -c default_transaction_read_only=on'}, open=False) as pool:
            await pool.open()
            db._pool = pool
            try:
                result = await community_feed('outsider', Response(), tab='following', discussion='all', shelf_id=None, limit=20, offset=0)
                assert pid in [item.id for item in result.items]
            finally:
                db._pool = original
    asyncio.run(check())


def test_following_retains_existing_mobile_boundary(client, actor, question):
    qid, _, _ = followed(client, actor, question)
    client.cookies.clear()
    invalid = {'Authorization':'Bearer ism_mobile_invalid'}
    assert client.get('/api/community/feed?tab=following', headers=invalid).status_code == 401
    # Legacy question-discussion writes already exist in the native contract.
    # This reader release grants no new endpoint or moderation capability.
    assert client.post(f'/api/community/questions/{qid}/discussion', headers=invalid, json={}).status_code == 401
    assert client.get('/api/community/admin/queue', headers=invalid).status_code == 403
    assert client.post('/api/community/admin/posts/1/action', headers=invalid, json={}).status_code == 403
