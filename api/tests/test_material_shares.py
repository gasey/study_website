"""Shares reveal reviewed catalog metadata only, never a second content body."""
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
import hashlib,json
import pytest
from test_discussions import database,client,approve
from test_study_posts import ready,note,mixed,status
from test_content_studio import publish,create,document


def share(client,h,mid,**extra):
    return note(client,h,kind='material-share',reference={'kind':'material','id':mid},**extra)


def test_share_uses_published_revision_and_never_exposes_paid_body(client,actor,database):
    _,conn=database
    mid=publish(client,actor,document('paid-preview'),user='outsider')
    ready(conn);h=actor('author')
    saved=share(client,h,mid);assert saved.status_code==201,saved.text
    pid=saved.json()['id']
    assert conn.execute('SELECT kind,material_id,canonical_id FROM posts WHERE id=%s',(pid,)).fetchone()==('material-share',mid,None)
    detail=client.get(f'/api/community/study-posts/{pid}');assert detail.status_code==200
    assert detail.json()['kind']=='material-share' and detail.json()['reference']['access']=='paid-preview'
    assert 'PRIVATE_BODY_MARKER' not in detail.text
    h=actor('outsider');draft=client.get('/api/studio/materials/'+mid).json();doc=document('paid-preview');doc['title']='UNREVIEWED_TITLE'
    assert client.post('/api/studio/materials/'+mid+'/save',headers=h,json={'expected_version':draft['lock_version'],'document':doc}).status_code==200
    actor('author');feed=client.get('/api/community/feed?content_version=2').json();card=next(r for r in feed['items'] if r['id']==pid)
    assert card['material']['label']==document()['title'] and card['material']['access']=='paid-preview'
    assert 'PRIVATE_BODY_MARKER' not in str(feed) and 'UNREVIEWED_TITLE' not in str(feed)
    assert 'UNREVIEWED_TITLE' not in client.get(f'/api/community/study-posts/{pid}').text
    assert client.get('/api/materials/'+mid).json()['can_read'] is False
    assert pid not in [p['id'] for p in client.get('/api/community/feed').json()['items']]
    assert pid not in mixed(client,'questions') and pid not in mixed(client,discussion='doubts')


def test_share_validates_reviewed_anchor_and_content_immutability(client,actor,database):
    _,conn=database;draft,_,_=create(client,actor,user='outsider');ready(conn);h=actor('author')
    assert share(client,h,draft).status_code==404
    assert note(client,h,kind='material-share').status_code==422
    assert note(client,h,kind='material-share',reference={'kind':'question','id':'cq_test'}).status_code==422
    assert share(client,h,'missing').status_code==404
    assert status(client)['posts_remaining']==5
    mid=publish(client,actor,user='outsider');h=actor('author');pid=share(client,h,mid).json()['id']
    with conn.transaction():
        conn.execute('SET LOCAL ROLE mpsc');assert conn.execute('SELECT material_id FROM posts WHERE id=%s',(pid,)).fetchone()[0]==mid
    for sql in ["UPDATE posts SET material_id=NULL WHERE id=%s","UPDATE posts SET source_context='{}' WHERE id=%s"]:
        with pytest.raises(Exception,match='immutable'):
            with conn.transaction():conn.execute(sql,(pid,))
    with pytest.raises(Exception,match='posts_material_anchor'):
        with conn.transaction():conn.execute("INSERT INTO posts(kind,author_id,body) VALUES('material-share','author','Synthetic invalid material share')")


def test_share_rechecks_both_block_pairs_unpublish_and_follow_consent(client,actor,database):
    _,conn=database;mid=publish(client,actor,user='outsider');ready(conn);h=actor('author');pid=share(client,h,mid).json()['id']
    h=actor('owner');assert pid in mixed(client)
    conn.execute("INSERT INTO creator_profiles(user_id,public) VALUES('author',true)")
    client.post('/api/creators/author/follow',headers=h,json={'enabled':True});assert pid in mixed(client,'following')
    conn.execute("UPDATE creator_profiles SET public=false WHERE user_id='author'");assert pid not in mixed(client,'following')
    conn.execute("UPDATE creator_profiles SET public=true WHERE user_id='author'")
    for a,b in [('owner','author'),('author','owner'),('owner','outsider'),('outsider','owner')]:
        conn.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)',(a,b))
        assert pid not in mixed(client) and pid not in mixed(client,'following')
        assert client.get(f'/api/community/study-posts/{pid}').status_code==404
        assert client.post(f'/api/community/study-posts/{pid}/helpful',headers=h,json={'enabled':True}).status_code==404
        conn.execute('DELETE FROM creator_blocks WHERE user_id=%s AND blocked_id=%s',(a,b))
    conn.execute("UPDATE materials SET status='removed' WHERE id=%s",(mid,))
    assert pid not in mixed(client) and client.get(f'/api/community/study-posts/{pid}').status_code==404
    h=actor('author');assert client.post(f'/api/community/study-posts/{pid}/withdraw',headers=h,json={}).status_code==200


def test_share_moderation_reports_votes_and_native_isolation(client,actor,database):
    _,conn=database;mid=publish(client,actor,user='outsider');ready(conn,established=False);h=actor('author')
    before=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    pid=share(client,h,mid).json()['id'];assert pid not in mixed(client)
    actor('outsider');assert client.get(f'/api/community/study-posts/{pid}').status_code==404
    actor('owner');queue=client.get('/api/community/admin/queue?tab=New%20users').json()['items'];queued=next(r for r in queue if r['post_id']==pid);assert queued['material']['id']==mid and 'PRIVATE_BODY_MARKER' not in str(queued)
    approve(client,actor,pid);h=actor('author');assert pid in mixed(client)
    assert client.post(f'/api/community/study-posts/{pid}/helpful',headers=h,json={'enabled':True}).status_code==403
    h=actor('outsider')
    assert client.post(f'/api/community/study-posts/{pid}/helpful',headers=h,json={'enabled':True}).json()['helpful']==1
    assert client.post(f'/api/community/study-posts/{pid}/report',headers=h,json={'reason':'spam','note':'Synthetic conduct issue for material share review.'}).status_code==200
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==before
    from test_mobile_companion import connect
    native,_=connect(client,actor,'author')
    assert client.get('/api/community/feed',headers=native).status_code==200
    assert client.get('/api/community/feed?content_version=2',headers=native).status_code==403
    for path in [f'/api/community/study-posts/{pid}',f'/api/community/study-posts/{pid}/helpful',f'/api/community/study-posts/{pid}/withdraw']:
        r=client.get(path,headers=native) if path.endswith(str(pid)) else client.post(path,headers=native,json={})
        assert r.status_code==403
    for action in ['helpful','withdraw']:
        assert client.post(f'/api/community/posts/{pid}/{action}',headers=native,json={'enabled':True} if action=='helpful' else {'body':'Synthetic native reply must not be accepted'} if action=='replies' else {}).status_code==404
    assert client.get(f'/api/community/posts/{pid}/replies',headers=native).status_code==404
    assert client.post('/api/community/questions/cq_test/discussion',headers={**native,'Idempotency-Key':uuid4().hex},json={'kind':'reply','parent_id':pid,'body':'Synthetic native reply cannot cross anchors'}).status_code==404
    assert share(client,native,mid).status_code==403


def test_share_caps_maturity_retry_and_existing_study_hash_contract(client,actor,database):
    _,conn=database;mid=publish(client,actor,user='outsider');h=actor('author');assert share(client,h,mid).status_code==403
    ready(conn);key=uuid4().hex;saved=share(client,h,mid,key=key);assert saved.status_code==201
    with ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(lambda i:share(client,h,mid,body='A synthetic material recommendation number '+str(i)),range(6)))
    assert sum(r.status_code==201 for r in results)==4 and sum(r.status_code==429 for r in results)==2
    assert share(client,h,mid,key=key).json()['id']==saved.json()['id']
    assert note(client,h,key=key).status_code==409
    assert note(client,h).status_code==429
    # Simulate an old request generated before Note.kind existed, without writes to production.
    old_key=uuid4().hex;payload={'body':'Synthetic prior request remains replayable.','topic_tag':None,'reference':None}
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
    pid=conn.execute("INSERT INTO posts(kind,author_id,body,request_key,request_hash) VALUES('study','author',%s,%s,%s) RETURNING id",(payload['body'],old_key,digest)).fetchone()[0]
    assert note(client,h,body=payload['body'],key=old_key).json()['id']==pid


def test_moderation_reference_rechecks_blocks_and_withdrawal(client,actor,database):
    _,conn=database;mid=publish(client,actor,user='outsider');ready(conn,established=False);h=actor('author');pid=share(client,h,mid).json()['id']
    h=actor('owner')
    for a,b in [('owner','outsider'),('outsider','owner')]:
        conn.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)',(a,b))
        queued=next(r for r in client.get('/api/community/admin/queue?tab=New%20users').json()['items'] if r['post_id']==pid)
        assert queued['material']=={'unavailable':True}
        assert client.post(f'/api/community/admin/posts/{pid}/action',headers=h,json={'action':'approve'}).status_code==404
        conn.execute('DELETE FROM creator_blocks WHERE user_id=%s AND blocked_id=%s',(a,b))
    conn.execute("UPDATE materials SET status='removed' WHERE id=%s",(mid,))
    assert client.post(f'/api/community/admin/posts/{pid}/action',headers=h,json={'action':'approve'}).status_code==404
    assert conn.execute('SELECT needs_approval FROM posts WHERE id=%s',(pid,)).fetchone()[0]
