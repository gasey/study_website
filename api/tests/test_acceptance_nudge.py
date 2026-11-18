"""An optional prompt is private, eligible-only and once per doubt across devices."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
import pytest
from test_discussions import database,client,question,answer,create,approve


def setup(client,actor,qid,*,kind='doubt'):
    h=answer(client,actor,qid,'author');pid=create(client,h,qid,kind=kind).json()['id'];approve(client,actor,pid)
    return pid


def reply(client,actor,qid,pid,user='outsider',published=True):
    h=answer(client,actor,qid,user);rid=create(client,h,qid,kind='reply',parent=pid).json()['id']
    if published:approve(client,actor,rid)
    return rid


def claim(client,h,pid):
    return client.post(f'/api/community/posts/{pid}/acceptance-nudge',headers=h,json={})


def test_once_across_concurrent_sessions_reload_and_real_role(client,actor,question,monkeypatch):
    from app.routers import discussions
    qid,conn=question;pid=setup(client,actor,qid);rid=reply(client,actor,qid,pid);h=actor('author')|{'Cookie':'ism_session=test-session-author'}
    original=discussions.cursor
    @asynccontextmanager
    async def application_role():
        async with original() as cur:
            await cur.execute('SET LOCAL ROLE mpsc');yield cur
    monkeypatch.setattr(discussions,'cursor',application_role)
    notifications=conn.execute('SELECT count(*) FROM review_notifications').fetchone()[0]
    ledger=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    # Ordinary reads do not consume the once-only prompt.
    for _ in range(2):assert client.get(f'/api/community/posts/{pid}/replies').status_code==200
    assert not conn.execute("SELECT 1 FROM discussion_events WHERE action='acceptance_nudged'").fetchone()
    with ThreadPoolExecutor(max_workers=3) as pool:rs=list(pool.map(lambda _:claim(client,h,pid),range(3)))
    assert all(r.status_code==200 and r.headers['cache-control']=='private, no-store' for r in rs),[r.text for r in rs]
    assert sum(r.json()['prompt'] for r in rs)==1
    assert claim(client,h,pid).json()=={'prompt':False}
    assert conn.execute("SELECT count(*) FROM discussion_events WHERE post_id=%s AND action='acceptance_nudged'",(pid,)).fetchone()[0]==1
    assert conn.execute('SELECT count(*) FROM review_notifications').fetchone()[0]==notifications
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==ledger
    with pytest.raises(Exception,match='unique'):
        conn.execute("INSERT INTO discussion_events(canonical_id,post_id,actor_id,action) VALUES(%s,%s,'author','acceptance_nudged')",(qid,pid))
    assert client.post(f'/api/community/posts/{rid}/accept',headers=h,json={'enabled':True}).status_code==200
    assert client.post(f'/api/community/posts/{rid}/accept',headers=h,json={'enabled':False}).status_code==200
    assert claim(client,h,pid).json()=={'prompt':False}


def test_no_prompt_for_empty_self_pending_or_previously_solved_doubts(client,actor,question):
    qid,conn=question;pid=setup(client,actor,qid);h=actor('author');assert claim(client,h,pid).json()=={'prompt':False}
    reply(client,actor,qid,pid,user='author');h=actor('author');assert claim(client,h,pid).json()=={'prompt':False}
    rid=reply(client,actor,qid,pid,published=False);h=actor('author');assert claim(client,h,pid).json()=={'prompt':False}
    approve(client,actor,rid);h=actor('author')
    assert client.post(f'/api/community/posts/{rid}/accept',headers=h,json={'enabled':True}).status_code==200
    assert claim(client,h,pid).json()=={'prompt':False}
    assert client.post(f'/api/community/posts/{rid}/accept',headers=h,json={'enabled':False}).status_code==200
    assert claim(client,h,pid).json()=={'prompt':False}
    assert not conn.execute("SELECT 1 FROM discussion_events WHERE action='acceptance_nudged'").fetchone()


@pytest.mark.parametrize('direction',[('author','outsider'),('outsider','author')])
def test_blocked_reply_does_not_consume_prompt(client,actor,question,direction):
    qid,conn=question;pid=setup(client,actor,qid);reply(client,actor,qid,pid)
    conn.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)',direction)
    h=actor('author');assert claim(client,h,pid).json()=={'prompt':False}
    conn.execute('DELETE FROM creator_blocks');assert claim(client,h,pid).json()=={'prompt':True}


def test_disclosure_assessment_lock_and_sanction_do_not_consume_prompt(client,actor,question):
    qid,conn=question;conn.execute("UPDATE canonical_questions SET answer_text=NULL,answer_source='none' WHERE id=%s",(qid,))
    h=actor('author');assert client.post(f'/api/community/questions/{qid}/discussion/open',headers=h,json={}).status_code==200
    pid=create(client,h,qid).json()['id'];approve(client,actor,pid)
    other=actor('outsider');assert client.post(f'/api/community/questions/{qid}/discussion/open',headers=other,json={}).status_code==200
    rid=create(client,other,qid,kind='reply',parent=pid).json()['id'];approve(client,actor,rid);h=actor('author')
    conn.execute('DELETE FROM discussion_disclosures WHERE user_id=%s AND canonical_id=%s',('author',qid));assert claim(client,h,pid).status_code==403
    assert client.post(f'/api/community/questions/{qid}/discussion/open',headers=h,json={}).status_code==200
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds,started_at) VALUES('nudge-active','author','udc',%s,600,now())",([qid],))
    assert claim(client,h,pid).status_code==409;conn.execute("DELETE FROM mock_sessions WHERE id='nudge-active'")
    conn.execute("INSERT INTO thread_locks(canonical_id,locked_by,reason) VALUES(%s,'owner','Synthetic moderation lock')",(qid,))
    assert claim(client,h,pid).status_code==409;conn.execute('DELETE FROM thread_locks WHERE canonical_id=%s',(qid,))
    mid=conn.execute("INSERT INTO mod_actions(actor_id,action,target_user) VALUES('owner','mute','author') RETURNING id").fetchone()[0]
    conn.execute("INSERT INTO sanctions(user_id,kind,step,action_id,starts_at,ends_at) VALUES('author','mute',1,%s,now()-interval '1 minute',now()+interval '1 hour')",(mid,))
    assert claim(client,h,pid).status_code==403;conn.execute("UPDATE sanctions SET lifted_at=now() WHERE user_id='author'")
    assert claim(client,h,pid).json()=={'prompt':True}


def test_only_author_published_doubt_and_browser_write_binding(client,actor,question):
    qid,conn=question;pid=setup(client,actor,qid);rid=reply(client,actor,qid,pid)
    other=actor('outsider');assert claim(client,other,pid).status_code==403
    assert claim(client,other,rid).json()=={'prompt':False}
    h=actor('author');assert claim(client,{},pid).status_code==403
    assert client.get(f'/api/community/posts/{pid}/acceptance-nudge').status_code==405
    assert client.post(f'/api/community/posts/{pid}/edit',headers=h|{'Idempotency-Key':'nudge-edit-key-123456'},json={'expected_version':0,'body':'A synthetic revised doubt awaiting moderation.'}).status_code==200
    assert claim(client,h,pid).json()=={'prompt':False}
    assert not conn.execute("SELECT 1 FROM discussion_events WHERE action='acceptance_nudged'").fetchone()
    assert client.post(f'/api/community/posts/{pid}/withdraw',headers=h,json={}).status_code==200
    assert claim(client,h,pid).status_code==404


def test_native_token_cannot_claim_web_prompt(client,actor,question):
    from test_mobile_companion import connect
    qid,_=question;pid=setup(client,actor,qid);reply(client,actor,qid,pid)
    native,_=connect(client,actor,'author')
    assert claim(client,native,pid).status_code==403


@pytest.mark.parametrize('field',['hidden','before_fix','needs_approval'])
def test_unavailable_reply_does_not_consume_prompt(client,actor,question,field):
    qid,conn=question;pid=setup(client,actor,qid);rid=reply(client,actor,qid,pid)
    conn.execute('UPDATE posts SET '+field+'=true WHERE id=%s',(rid,))
    h=actor('author');assert claim(client,h,pid).json()=={'prompt':False}
    assert not conn.execute("SELECT 1 FROM discussion_events WHERE action='acceptance_nudged'").fetchone()


def test_explanations_never_prompt(client,actor,question):
    qid,conn=question;pid=setup(client,actor,qid,kind='explanation');reply(client,actor,qid,pid)
    h=actor('author');assert claim(client,h,pid).json()=={'prompt':False}
