"""Edits preserve evidence, re-enter review and serialize against acceptance."""
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from psycopg import errors
from psycopg.types.json import Jsonb
from test_discussions import database,client,question,answer,create,approve
from test_study_posts import ready,note,status


def edit(client,h,pid,version=0,text='A revised synthetic explanation with clearer reasoning.',key=None,sources=None):
    return client.post(f'/api/community/posts/{pid}/edit',headers={**h,'Idempotency-Key':key or uuid4().hex},json={'expected_version':version,'body':text,'sources':sources or []})


def review(client,actor,pid,version):
    h=actor('owner');return client.post(f'/api/community/admin/posts/{pid}/action',headers=h,json={'action':'approve','expected_version':version})


def own_note(client,actor,database):
    ready(database[1]);h=actor('author');r=note(client,h);assert r.status_code==201,r.text
    return h,r.json()['id']


def test_edit_records_snapshots_replay_review_and_current_marker(client,actor,database):
    h,pid=own_note(client,actor,database);conn=database[1];original=conn.execute('SELECT body FROM posts WHERE id=%s',(pid,)).fetchone()[0]
    key=uuid4().hex;r=edit(client,h,pid,key=key);assert r.status_code==200,r.text;assert r.json()['needs_approval'];assert r.json()['content_version']==1
    assert edit(client,h,pid,key=key).json()['replayed']
    assert edit(client,h,pid,key=key,text='A different synthetic edit using the same request key.').status_code==409
    post=client.get(f'/api/community/study-posts/{pid}').json();assert post['edited_at'] and post['content_version']==1
    hist=client.get(f'/api/community/posts/{pid}/revisions');assert hist.headers['cache-control']=='private, no-store';assert [v['version'] for v in hist.json()['items']]==[1,0];assert hist.json()['items'][1]['body']==original
    actor('outsider');assert client.get(f'/api/community/study-posts/{pid}').status_code==404;assert client.get(f'/api/community/posts/{pid}/revisions').status_code==404
    h=actor('owner');assert client.post(f'/api/community/admin/posts/{pid}/action',headers=h,json={'action':'approve'}).status_code==409
    queue=client.get('/api/community/admin/queue',headers=h).json()['items'];item=next(i for i in queue if i['post_id']==pid);assert item['content_version']==1;assert item['edit_history'][1]['body']==original
    assert review(client,actor,pid,1).status_code==200
    actor('outsider');assert client.get(f'/api/community/study-posts/{pid}').json()['body'].startswith('A revised');assert client.get(f'/api/community/posts/{pid}/revisions').status_code==403
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==0


def test_stale_edits_budget_noop_and_concurrent_winner(client,actor,database):
    h,pid=own_note(client,actor,database)
    assert edit(client,h,pid,text='A synthetic study tip: read the source and compare the wording.').status_code==422
    r=edit(client,h,pid);assert r.status_code==200,r.text
    assert edit(client,h,pid).status_code==409
    h=actor('author')
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda n:edit(client,h,pid,1,'A distinct synthetic revision number '+str(n)),range(2)))
    assert sorted(r.status_code for r in results)==[200,409]
    assert status(client)['posts_remaining']==2 # One creation and two edits.
    assert edit(client,h,pid,2,'Third synthetic revision for this study note.').status_code==200
    assert edit(client,h,pid,3,'Fourth synthetic revision for this study note.').status_code==200
    assert edit(client,h,pid,4,'Fifth synthetic revision would exceed the shared cap.').status_code==429
    assert note(client,h).status_code==429


def test_edit_ownership_reports_withdrawal_and_immutable_anchor(client,actor,database):
    h,pid=own_note(client,actor,database);conn=database[1]
    other=actor('outsider');assert edit(client,other,pid).status_code==403
    assert client.post(f'/api/community/study-posts/{pid}/report',headers=other,json={'reason':'other','note':'A synthetic report requiring moderation before changes.'}).status_code==200
    h=actor('author');assert edit(client,h,pid).status_code==409
    conn.execute("UPDATE abuse_reports SET status='dismissed' WHERE post_id=%s",(pid,))
    assert edit(client,h,pid,sources=[{'url':'https://example.test/source','note':'Own synthetic source'}]).status_code==422
    assert edit(client,h,pid,text='Use https://example.test instead of the immutable linked item.').status_code==422
    assert client.post(f'/api/community/study-posts/{pid}/withdraw',headers=h).status_code==200
    assert edit(client,h,pid).status_code==404
    with pytest.raises(Exception,match='immutable'):conn.execute('UPDATE posts SET source_context=%s WHERE id=%s',(Jsonb({'changed':True}),pid))


def test_canonical_sources_and_disclosure_block_assessment_gates(client,actor,question):
    qid,conn=question;h=answer(client,actor,qid,'author');r=create(client,h,qid);pid=r.json()['id'];approve(client,actor,pid)
    h=actor('author');sources=[{'url':'https://example.test/revised','note':'Clarifies the source wording'}]
    r=edit(client,h,pid,sources=sources);assert r.status_code==200,r.text
    assert client.get(f'/api/community/posts/{pid}/revisions').json()['items'][0]['source_links']==sources
    assert review(client,actor,pid,1).status_code==200
    h=actor('author');conn.execute("INSERT INTO creator_blocks(user_id,blocked_id) VALUES('outsider','author')")
    other=answer(client,actor,qid,'outsider');assert edit(client,other,pid).status_code==404
    h=actor('author');conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds,started_at) VALUES('edit-active','author','udc',%s,600,now())",([qid],))
    try:
        assert edit(client,h,pid,1).status_code==409
        assert client.get(f'/api/community/posts/{pid}/revisions').status_code==409
    finally:conn.execute("DELETE FROM mock_sessions WHERE id='edit-active'")


def test_accepted_once_reply_stays_locked_after_unaccept(client,actor,question):
    qid,conn=question;h=answer(client,actor,qid,'author');pid=create(client,h,qid).json()['id'];approve(client,actor,pid)
    h=answer(client,actor,qid,'outsider');rid=create(client,h,qid,kind='reply',parent=pid).json()['id'];approve(client,actor,rid)
    h=actor('author');assert client.post(f'/api/community/posts/{rid}/accept',headers=h,json={'enabled':True}).status_code==200
    assert client.post(f'/api/community/posts/{rid}/accept',headers=h,json={'enabled':False}).status_code==200
    other=actor('outsider');assert edit(client,other,rid).status_code==409
    assert conn.execute('SELECT edit_locked FROM posts WHERE id=%s',(rid,)).fetchone()[0]
    with pytest.raises(Exception,match='locked'):conn.execute('UPDATE posts SET edit_locked=false WHERE id=%s',(rid,))
    with pytest.raises(Exception,match='locked'):conn.execute('SELECT community_edit_post(%s,%s,0,%s,%s,%s,%s)',(rid,'outsider','An attempted change after acceptance.',Jsonb([]),uuid4().hex,'synthetic'))


def test_edit_waits_for_fresh_moderation_and_undo_cannot_republish_new_revision(client,actor,database):
    h,pid=own_note(client,actor,database);assert edit(client,h,pid).status_code==200;assert review(client,actor,pid,1).status_code==200
    conn=database[1];action=conn.execute('SELECT id FROM mod_actions WHERE post_id=%s ORDER BY id DESC LIMIT 1',(pid,)).fetchone()[0]
    h=actor('author');assert edit(client,h,pid,1,'Another synthetic revision needing a separate approval.').status_code==200
    assert review(client,actor,pid,1).status_code==409
    # Legacy admin undo cannot remove the new version's moderation hold.
    from app.routers.moderation import undo_action
    import asyncio
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as e:asyncio.run(undo_action(action,'owner'))
    assert e.value.status_code==409
    assert conn.execute('SELECT needs_approval FROM posts WHERE id=%s',(pid,)).fetchone()[0]


def test_revision_table_is_append_only_for_application_role(client,actor,database):
    h,pid=own_note(client,actor,database);assert edit(client,h,pid).status_code==200
    conn=database[1]
    with pytest.raises(Exception,match='append-only'):conn.execute('UPDATE post_revisions SET body=%s WHERE post_id=%s',('Forged synthetic replacement',pid))
    with pytest.raises(Exception,match='append-only'):conn.execute('DELETE FROM post_revisions WHERE post_id=%s',(pid,))
    conn.execute('SET ROLE mpsc')
    try:
        with pytest.raises(errors.InsufficientPrivilege):conn.execute('INSERT INTO post_revisions(post_id,version,body,source_links,actor_id) VALUES(%s,99,%s,%s,%s)',(pid,'Forged synthetic snapshot',Jsonb([]),'author'))
    finally:conn.execute('RESET ROLE')


def test_accept_edit_race_has_one_safe_outcome(client,actor,question):
    qid,conn=question;h=answer(client,actor,qid,'author');pid=create(client,h,qid).json()['id'];approve(client,actor,pid)
    h=answer(client,actor,qid,'outsider');rid=create(client,h,qid,kind='reply',parent=pid).json()['id'];approve(client,actor,rid)
    ah=actor('author')|{'Cookie':'ism_session=test-session-author'}
    rh=actor('outsider')|{'Cookie':'ism_session=test-session-outsider'}
    with ThreadPoolExecutor(max_workers=2) as pool:
        accepted=pool.submit(client.post,f'/api/community/posts/{rid}/accept',headers=ah,json={'enabled':True})
        edited=pool.submit(edit,client,rh,rid)
        results=[accepted.result(),edited.result()]
    assert sorted(r.status_code for r in results)==[200,409],[r.text for r in results]
    locked,pending,version=conn.execute('SELECT edit_locked,needs_approval,content_version FROM posts WHERE id=%s',(rid,)).fetchone()
    assert (locked and not pending and version==0) or (not locked and pending and version==1)


def test_edit_pause_and_live_mpsc_role_permissions(client,actor,database,monkeypatch):
    from contextlib import asynccontextmanager
    from app.routers import discussions
    h,pid=own_note(client,actor,database);conn=database[1];original=discussions.cursor
    @asynccontextmanager
    async def application_role():
        async with original() as cur:
            await cur.execute('SET LOCAL ROLE mpsc');yield cur
    monkeypatch.setattr(discussions,'cursor',application_role)
    assert edit(client,h,pid).status_code==200
    conn.execute('REVOKE EXECUTE ON FUNCTION community_edit_post(bigint,text,integer,text,jsonb,text,text) FROM mpsc')
    assert edit(client,h,pid,1,'An edit while authoring is paused should stay unsaved.').status_code==503
    assert conn.execute('SELECT content_version FROM posts WHERE id=%s',(pid,)).fetchone()[0]==1
    assert len(client.get(f'/api/community/posts/{pid}/revisions').json()['items'])==2


def test_history_disclosure_and_edit_sanction_are_current(client,actor,question):
    qid,conn=question;conn.execute("UPDATE canonical_questions SET answer_text=NULL,answer_source='none' WHERE id=%s",(qid,))
    h=actor('author');assert client.post(f'/api/community/questions/{qid}/discussion/open',headers=h,json={}).status_code==200
    pid=create(client,h,qid).json()['id'];approve(client,actor,pid)
    h=actor('author');assert edit(client,h,pid).status_code==200
    conn.execute('DELETE FROM discussion_disclosures WHERE user_id=%s AND canonical_id=%s',('author',qid))
    assert client.get(f'/api/community/posts/{pid}/revisions').status_code==403
    assert edit(client,h,pid,1,'A revision after answer disclosure was withdrawn.').status_code==403
    assert client.post(f'/api/community/questions/{qid}/discussion/open',headers=h,json={}).status_code==200
    mid=conn.execute("INSERT INTO mod_actions(actor_id,action,target_user) VALUES('owner','mute','author') RETURNING id").fetchone()[0]
    conn.execute("INSERT INTO sanctions(user_id,kind,step,action_id,starts_at,ends_at) VALUES('author','mute',1,%s,now()-interval '1 minute',now()+interval '1 hour')",(mid,))
    assert edit(client,h,pid,1,'A revision while posting privileges are muted.').status_code==403


def test_edited_accepted_excerpt_keeps_marker_and_block_gate(client,actor,question):
    qid,conn=question;h=answer(client,actor,qid,'author');pid=create(client,h,qid).json()['id'];approve(client,actor,pid)
    h=answer(client,actor,qid,'outsider');rid=create(client,h,qid,kind='reply',parent=pid).json()['id'];approve(client,actor,rid)
    h=actor('outsider');assert edit(client,h,rid).status_code==200;assert review(client,actor,rid,1).status_code==200
    h=actor('author');assert client.post(f'/api/community/posts/{rid}/accept',headers=h,json={'enabled':True}).status_code==200
    item=next(p for p in client.get('/api/community/feed?tab=questions').json()['items'] if p['id']==pid)
    assert item['accepted_answer_edited_at'];assert item['accepted_answer'].startswith('A revised')
    conn.execute("INSERT INTO creator_blocks(user_id,blocked_id) VALUES('author','outsider')")
    item=next(p for p in client.get('/api/community/feed?tab=questions').json()['items'] if p['id']==pid)
    assert item['accepted_answer'] is None and item['accepted_answer_edited_at'] is None
