"""Study-note gates, shared budgets, dynamic trust, moderation and native boundary."""
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from psycopg.types.json import Jsonb
from test_discussions import database,client,question,answer,create as discussion,approve


def ready(conn,user='author',attempts=50,age=4,established=True):
    conn.execute("UPDATE users SET created_at=now()-(%s * interval '1 day') WHERE id=%s",(age,user))
    conn.execute("INSERT INTO attempts(user_id,canonical_id,chosen_text,correct,context,at) SELECT %s,'cq_test','A',false,'practice',now()-interval '1 day' FROM generate_series(1,%s)",(user,attempts))
    if established:
        conn.execute("INSERT INTO posts(canonical_id,kind,author_id,body,created_at) SELECT 'cq_test','explanation',%s,'Synthetic previously approved explanation',now()-interval '2 days' FROM generate_series(1,3)",(user,))


def note(client,h,body='A synthetic study tip: read the source and compare the wording.',key=None,**extra):
    return client.post('/api/community/study-posts',headers={**h,'Idempotency-Key':key or uuid4().hex},json={'body':body,**extra})


def status(client):
    r=client.get('/api/community/study-posts/status');assert r.status_code==200,r.text
    assert r.headers['cache-control']=='private, no-store'
    return r.json()


def mixed(client,tab='for-you',**params):
    r=client.get('/api/community/feed',params={'content_version':2,'tab':tab,**params});assert r.status_code==200,r.text
    return [p['id'] for p in r.json()['items']]


def voters(conn,post_id,count,qualified=False):
    for _ in range(count):
        user='vote_'+uuid4().hex
        conn.execute('INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)',(user,user,user+'@example.test'))
        conn.execute('INSERT INTO post_votes(post_id,user_id,weight) VALUES(%s,%s,9999)',(post_id,user))
        if qualified:
            conn.execute("INSERT INTO attempts(user_id,canonical_id,chosen_text,correct,context) SELECT %s,'cq_test','A',false,'practice' FROM generate_series(1,50)",(user,))


def test_maturity_gate_does_not_restrict_attempted_question_doubts(client,actor,database):
    _,conn=database;h=actor('author')
    assert not status(client)['can_create']
    assert note(client,h).status_code==403
    ready(conn,attempts=49,established=False)
    assert note(client,h).status_code==403
    conn.execute("UPDATE users SET created_at=now()-interval '2 days' WHERE id='author'")
    conn.execute("INSERT INTO attempts(user_id,canonical_id,chosen_text,correct,context) VALUES('author','cq_test','A',false,'practice')")
    assert not status(client)['can_create']
    assert discussion(client,h,'cq_test').status_code==201
    conn.execute("UPDATE users SET created_at=now()-interval '4 days' WHERE id='author'")
    assert status(client)['can_create']
    result=note(client,h);assert result.status_code==201,result.text
    assert result.json()['needs_approval']


def test_moderation_owner_pending_visibility_and_no_currency(client,actor,database):
    _,conn=database;ready(conn,established=False);h=actor('author')
    before=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    saved=note(client,h,topic_tag='english');assert saved.status_code==201,saved.text
    pid=saved.json()['id'];assert saved.json()['needs_approval']
    assert client.get(f'/api/community/study-posts/{pid}').json()['needs_approval']
    assert pid not in mixed(client)
    actor('outsider');assert client.get(f'/api/community/study-posts/{pid}').status_code==404
    h=actor('owner');queue=client.get('/api/community/admin/queue').json()['items']
    assert any(p['post_id']==pid and p['canonical_id'] is None for p in queue)
    approve(client,actor,pid);h=actor('author')
    assert pid in mixed(client)
    assert pid not in [p['id'] for p in client.get('/api/community/feed').json()['items']]
    assert pid not in mixed(client,tab='questions')
    assert client.post(f'/api/community/posts/{pid}/withdraw',headers=h,json={}).status_code==404
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==before
    assert client.post(f'/api/community/study-posts/{pid}/withdraw',headers=h,json={}).status_code==200
    assert client.get(f'/api/community/study-posts/{pid}').status_code==404


def test_caps_are_shared_atomic_and_replays_do_not_spend_slots(client,actor,database):
    _,conn=database;ready(conn);h=actor('author');key=uuid4().hex
    first=note(client,h,key=key);assert first.status_code==201,first.text
    with ThreadPoolExecutor(max_workers=7) as pool:
        results=list(pool.map(lambda i:note(client,h,body='A synthetic independent study note number '+str(i)),range(7)))
    assert sum(r.status_code==201 for r in results)==4,[r.text for r in results]
    assert sum(r.status_code==429 for r in results)==3
    assert status(client)['posts_remaining']==0
    assert note(client,h,key=key).json()['id']==first.json()['id']
    assert note(client,h,body='Different synthetic text for a replay conflict.',key=key).status_code==409
    assert discussion(client,h,'cq_test').status_code==429
    # Replies have their own thirty-per-day budget; posted notes do not consume it.
    parent=conn.execute("SELECT id FROM posts WHERE author_id='author' AND kind='explanation' LIMIT 1").fetchone()[0]
    conn.execute("INSERT INTO posts(canonical_id,kind,parent_id,author_id,body) SELECT 'cq_test','reply',%s,'author','Synthetic reply budget fixture' FROM generate_series(1,30)",(parent,))
    assert discussion(client,h,'cq_test',kind='reply',parent=parent).status_code==429
    assert status(client)['replies_remaining']==0


def test_helper_regular_weights_and_pending_privilege_loss(client,actor,database):
    _,conn=database;ready(conn,attempts=0,age=0);h=actor('author')
    pid=conn.execute("SELECT id FROM posts WHERE author_id='author' LIMIT 1").fetchone()[0]
    voters(conn,pid,39);assert status(client)['weighted_helpful']==9.75
    assert note(client,h).status_code==403
    voters(conn,pid,1);s=status(client);assert s['weighted_helpful']==10 and s['tier']=='Helper' and s['can_create']
    voters(conn,pid,15,qualified=True);s=status(client)
    assert s['weighted_helpful']==25 and s['post_limit']==10 and s['reply_limit']==60
    saved=note(client,h);assert saved.status_code==201,saved.text
    # Open review removes ladder privileges, but not the recorded vote evidence.
    conn.execute('UPDATE posts SET needs_approval=true WHERE id=%s',(saved.json()['id'],))
    s=status(client);assert s['privileges_restricted'] and not s['can_create'] and s['post_limit']==5
    approve(client,actor,saved.json()['id']);actor('author');assert status(client)['can_create']
    assert status(client)['post_limit']==10
    voter=conn.execute('SELECT user_id FROM post_votes WHERE post_id=%s LIMIT 1',(pid,)).fetchone()[0]
    conn.execute("INSERT INTO creator_blocks(user_id,blocked_id) VALUES('author',%s)",(voter,))
    assert status(client)['weighted_helpful']<25


def test_regular_top_and_reply_caps_and_ist_reset(client,actor,database):
    _,conn=database;ready(conn);h=actor('author')
    parent=conn.execute("SELECT id FROM posts WHERE author_id='author' LIMIT 1").fetchone()[0]
    voters(conn,parent,25,qualified=True)
    conn.execute("INSERT INTO posts(canonical_id,kind,author_id,body) SELECT 'cq_test','doubt','author','Synthetic top-level cap fixture' FROM generate_series(1,10)")
    conn.execute("INSERT INTO posts(canonical_id,kind,parent_id,author_id,body) SELECT 'cq_test','reply',%s,'author','Synthetic regular reply cap fixture' FROM generate_series(1,60)",(parent,))
    s=status(client);assert s['posts_remaining']==0 and s['replies_remaining']==0
    assert note(client,h).status_code==429
    assert discussion(client,h,'cq_test',kind='reply',parent=parent).status_code==429
    assert s['post_limit']==10 and s['reply_limit']==60
    # Old fixture rows from two days ago did not consume today's ten slots.
    assert conn.execute("SELECT count(*) FROM posts WHERE author_id='author' AND parent_id IS NULL").fetchone()[0]==13


def test_linked_question_disclosure_blocks_and_active_assessment(client,actor,question):
    qid,conn=question;ready(conn);h=answer(client,actor,qid,'author')
    saved=note(client,h,reference={'kind':'question','id':qid});assert saved.status_code==201,saved.text
    pid=saved.json()['id'];actor('outsider')
    assert pid not in mixed(client)
    assert client.get(f'/api/community/study-posts/{pid}').status_code==403
    h=answer(client,actor,qid,'outsider');assert pid in mixed(client)
    assert client.get(f'/api/community/study-posts/{pid}').json()['reference']['id']==qid
    for blocker,blocked in [('author','outsider'),('outsider','author')]:
        conn.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)',(blocker,blocked))
        assert pid not in mixed(client)
        assert client.get(f'/api/community/study-posts/{pid}').status_code==404
        conn.execute('DELETE FROM creator_blocks WHERE user_id=%s AND blocked_id=%s',(blocker,blocked))
    mock='study_mock_'+uuid4().hex
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,'outsider','udc',%s,600)",(mock,[qid]))
    assert pid not in mixed(client)
    assert client.get(f'/api/community/study-posts/{pid}').status_code==409
    # A moderation reviewer in an active mock also cannot inspect the linked note.
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,'owner','udc',%s,600)",(mock+'_owner',[qid]))
    conn.execute('UPDATE posts SET needs_approval=true WHERE id=%s',(pid,))
    h=actor('owner');assert pid not in [r['post_id'] for r in client.get('/api/community/admin/queue?tab=New%20users').json()['items']]
    assert client.post(f'/api/community/admin/posts/{pid}/action',headers=h,json={'action':'approve'}).status_code==409


def test_validation_following_reports_and_repeat_flag_review(client,actor,database):
    _,conn=database;ready(conn);h=actor('author')
    for body in ['Read https://example.test for the answer.','Use www.example.com for practice.','Read example.xyz for a shortcut.','[Source](//example.test) has the answer.']:
        assert note(client,h,body=body).status_code==422
    assert note(client,{},body='Synthetic CSRF guard content for a note.').status_code==403
    assert note(client,h,topic_tag='missing-topic').status_code==422
    assert note(client,h,reference={'kind':'exam','id':'private-missing'}).status_code==404
    assert note(client,h,reference={'kind':'url','id':'https://example.test'}).status_code==422
    saved=note(client,h);pid=saved.json()['id'];second=note(client,h,body='Another synthetic useful note with a different purpose.').json()['id']
    conn.execute("INSERT INTO creator_profiles(user_id,public) VALUES('author',true)")
    h=actor('outsider');client.post('/api/creators/author/follow',headers=h,json={'enabled':True})
    assert pid in mixed(client,'following')
    for post in [pid,second]:
        assert client.post(f'/api/community/study-posts/{post}/report',headers=h,json={'reason':'spam','note':'Synthetic independent report for moderation review.'}).status_code==200
    h=actor('author');assert status(client)['repeat_flagged'] and status(client)['needs_approval']
    pending=note(client,h);assert pending.json()['needs_approval']
    approve(client,actor,pending.json()['id']);actor('author');assert not status(client)['repeat_flagged']
    actor('owner');assert any(p['post_id']==pid for p in client.get('/api/community/admin/queue?tab=Reported').json()['items'])


def test_votes_no_currency_no_self_and_new_mobile_paths_denied(client,actor,database):
    _,conn=database;ready(conn);h=actor('author');pid=note(client,h).json()['id']
    before=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    assert client.post(f'/api/community/study-posts/{pid}/helpful',headers=h,json={'enabled':True}).status_code==403
    h=actor('outsider')
    for _ in range(2):assert client.post(f'/api/community/study-posts/{pid}/helpful',headers=h,json={'enabled':True}).json()['helpful']==1
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==before
    from test_mobile_companion import connect
    native,_=connect(client,actor,'outsider')
    assert client.get('/api/community/feed',headers=native).status_code==200
    assert client.get('/api/community/feed?content_version=2',headers=native).status_code==403
    for method,path in [('GET','/api/community/study-posts/status'),('GET',f'/api/community/study-posts/{pid}'),('POST','/api/community/study-posts'),('POST',f'/api/community/study-posts/{pid}/helpful')]:
        assert client.request(method,path,headers=native,json={} if method=='POST' else None).status_code==403
    assert client.post(f'/api/community/posts/{pid}/helpful',headers=native,json={'enabled':True}).status_code==404


def test_mpsc_grants_and_note_content_immutability(client,actor,database):
    _,conn=database;ready(conn);h=actor('author');pid=note(client,h,topic_tag='english').json()['id']
    with conn.transaction():
        conn.execute('SET LOCAL ROLE mpsc')
        assert conn.execute('SELECT kind FROM posts WHERE id=%s',(pid,)).fetchone()[0]=='study'
        assert conn.execute('SELECT canonical_id FROM discussion_events WHERE post_id=%s',(pid,)).fetchone()[0] is None
    with pytest.raises(Exception,match='immutable'):
        with conn.transaction():conn.execute("UPDATE posts SET topic_tag='mizo' WHERE id=%s",(pid,))
    with pytest.raises(Exception,match='posts_anchor_kind'):
        with conn.transaction():conn.execute("INSERT INTO posts(kind,author_id,body) VALUES('doubt','author','Synthetic invalid unanchored doubt')")


def test_material_paper_exam_references_keep_visibility_and_published_lifecycle(client,actor,database):
    _,conn=database
    from test_content_studio import publish
    mid=publish(client,actor,user='outsider')
    ready(conn);h=actor('author')
    saved=note(client,h,reference={'kind':'material','id':mid});assert saved.status_code==201,saved.text
    pid=saved.json()['id']
    assert pid in mixed(client)
    # The referenced author can be blocked independently of the note's author.
    conn.execute("INSERT INTO creator_blocks(user_id,blocked_id) VALUES('author','outsider')")
    assert pid not in mixed(client)
    assert client.get(f'/api/community/study-posts/{pid}').status_code==404
    conn.execute("DELETE FROM creator_blocks WHERE user_id='author' AND blocked_id='outsider'")
    conn.execute("UPDATE materials SET status='removed' WHERE id=%s",(mid,))
    assert pid not in mixed(client)
    assert client.get(f'/api/community/study-posts/{pid}').status_code==404
    paper=note(client,h,reference={'kind':'paper','id':'Old_Questions/test.pdf'});assert paper.status_code==201,paper.text
    detail=client.get('/api/community/study-posts/'+str(paper.json()['id'])).json()
    assert detail['reference']['id']=='paper-test' and detail['reference']['url']=='/papers/source/Old_Questions/test.pdf'
    exam=note(client,h,reference={'kind':'exam','id':'udc'});assert exam.status_code==201,exam.text
    assert exam.json()['id'] in mixed(client)
    conn.execute("UPDATE collections SET visibility='hidden' WHERE id='udc'")
    assert exam.json()['id'] not in mixed(client)
    assert client.get('/api/community/study-posts/'+str(exam.json()['id'])).status_code==404


def test_guest_reads_do_not_require_an_attempt_for_an_unlinked_note(client,actor,database):
    _,conn=database;ready(conn);h=actor('author');pid=note(client,h).json()['id']
    client.cookies.clear()
    assert not status(client)['registered']
    response=client.get(f'/api/community/study-posts/{pid}')
    assert response.status_code==200 and not response.json()['registered']
    assert pid in mixed(client)
    assert note(client,{}).status_code==401


def test_withdrawn_pending_note_does_not_quarantine_helper_forever(client,actor,database):
    _,conn=database;ready(conn,attempts=0,age=0);h=actor('author')
    parent=conn.execute("SELECT id FROM posts WHERE author_id='author' LIMIT 1").fetchone()[0]
    voters(conn,parent,10,qualified=True)
    saved=note(client,h);pid=saved.json()['id']
    conn.execute('UPDATE posts SET needs_approval=true WHERE id=%s',(pid,))
    assert not status(client)['can_create']
    assert client.post(f'/api/community/study-posts/{pid}/withdraw',headers=h,json={}).status_code==200
    assert status(client)['can_create'] and not status(client)['privileges_restricted']
