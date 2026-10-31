"""Public identity is explicit consent; graph actions are account-only and unscored."""
from concurrent.futures import ThreadPoolExecutor
import pytest
from test_content_studio import publish

@pytest.fixture(autouse=True)
def clean_graph(database):
    _,conn=database
    conn.execute('DELETE FROM creator_follows');conn.execute('DELETE FROM creator_blocks');conn.execute('DELETE FROM creator_reports');conn.execute('DELETE FROM creator_profiles')
    conn.execute("DELETE FROM review_rate_buckets WHERE bucket LIKE 'cms:%'")

def opt_in(client,actor,user='author'):
    h=actor(user)
    r=client.post('/api/creators/settings',headers=h,json={'public':True,'bio':'A synthetic creator bio.'});assert r.status_code==200,r.text
    return h

def test_private_default_and_public_contract(client,actor):
    h=actor('author');r=client.get('/api/creators/settings');assert r.status_code==200 and not r.json()['public']
    actor('outsider');assert client.get('/api/creators/author').status_code==404
    assert not client.get('/api/creators?q=author').json()['items']
    opt_in(client,actor);actor('outsider')
    r=client.get('/api/creators/author');assert r.status_code==200,r.text
    assert not set(r.json())&{'email','name','role','progress','plan_code','password_hash'}
    assert r.headers['cache-control']=='private, no-store'
    assert client.get('/api/creators?q=author').json()['items'][0]['id']=='author'
    h=actor('author');assert client.post('/api/creators/settings',headers=h,json={'public':True,'bio':'x'*601}).status_code==422
    assert client.post('/api/creators/settings',json={'public':True}).status_code==403

def test_follow_retry_visibility_and_no_rewards(client,actor,database):
    _,conn=database;opt_in(client,actor)
    h=actor('outsider');before=conn.execute("SELECT count(*) FROM reward_ledger WHERE user_id='outsider'").fetchone()[0]
    with ThreadPoolExecutor(max_workers=4) as pool:
        rs=list(pool.map(lambda _:client.post('/api/creators/author/follow',headers=h,json={'enabled':True}),range(4)))
    assert all(r.status_code==200 for r in rs),[r.text for r in rs]
    assert conn.execute("SELECT count(*) FROM creator_follows WHERE follower_id='outsider' AND creator_id='author'").fetchone()[0]==1
    assert client.get('/api/creators/author').json()['following']
    assert client.post('/api/creators/outsider/follow',headers=h,json={'enabled':True}).status_code==422
    h=actor('author');client.post('/api/creators/settings',headers=h,json={'public':False})
    h=actor('outsider');assert client.get('/api/creators/author').status_code==404
    assert client.post('/api/creators/author/follow',headers=h,json={'enabled':True}).status_code==404
    assert client.post('/api/creators/author/follow',headers=h,json={'enabled':False}).status_code==200
    assert conn.execute("SELECT count(*) FROM reward_ledger WHERE user_id='outsider'").fetchone()[0]==before

def test_following_materials_exact_public_revision_and_block(client,actor,database):
    _,conn=database;mid=publish(client,actor);opt_in(client,actor)
    h=actor('outsider');client.post('/api/creators/author/follow',headers=h,json={'enabled':True})
    items=client.get('/api/materials?following=true').json()['items'];assert mid in [r['id'] for r in items]
    assert all('blocks' not in r['payload'] for r in items)
    assert all(r['author_id']=='author' and r['creator_public'] for r in items)
    assert mid in [r['id'] for r in client.get('/api/materials?creator_id=author').json()['items']]
    assert client.post('/api/creators/author/block',headers=h,json={'enabled':True}).status_code==200
    assert client.post('/api/creators/author/block',headers=h,json={'enabled':True}).status_code==200
    assert not client.get('/api/materials?following=true').json()['items']
    assert mid not in [r['id'] for r in client.get('/api/materials').json()['items']]
    assert client.get('/api/materials/'+mid).status_code==404
    assert client.get('/api/creators/author').status_code==404
    assert conn.execute("SELECT count(*) FROM creator_follows WHERE creator_id='author' AND follower_id='outsider'").fetchone()[0]==0
    actor('author');assert client.get('/api/creators/outsider').status_code==404
    h=actor('outsider');client.post('/api/creators/author/block',headers=h,json={'enabled':False})
    assert client.get('/api/materials/'+mid).status_code==200
    assert not client.get('/api/materials?following=true').json()['items']

def test_hidden_profile_leaves_publication_but_not_following(client,actor):
    mid=publish(client,actor);opt_in(client,actor)
    h=actor('outsider');client.post('/api/creators/author/follow',headers=h,json={'enabled':True})
    h=actor('author');client.post('/api/creators/settings',headers=h,json={'public':False})
    actor('outsider');assert client.get('/api/materials/'+mid).status_code==200
    assert not client.get('/api/materials/'+mid).json()['creator_public']
    assert not client.get('/api/materials?following=true').json()['items']
    assert not client.get('/api/materials?creator_id=author').json()['items']
    h=actor('author');client.post('/api/creators/settings',headers=h,json={'public':True})
    actor('outsider');assert mid in [r['id'] for r in client.get('/api/materials?following=true').json()['items']]

def test_report_scope_resolution_and_guest_denial(client,actor,database):
    _,conn=database;opt_in(client,actor);h=actor('outsider')
    body={'reason':'spam','note':'Synthetic reported spam profile for review.'}
    for _ in range(2):assert client.post('/api/creators/author/report',headers=h,json=body).status_code==200
    assert client.get('/api/admin/bank/creator-reports').status_code==403
    actor('owner');queue=client.get('/api/admin/bank/creator-reports').json();assert len(queue['items'])==1
    rid=queue['items'][0]['id'];h=actor('owner')
    assert client.post(f'/api/admin/bank/creator-reports/{rid}/resolve',headers=h,json={'reason':'Investigated synthetic spam report.'}).status_code==200
    assert not client.get('/api/admin/bank/creator-reports').json()['items']
    assert client.post(f'/api/admin/bank/creator-reports/{rid}/resolve',headers=h,json={'reason':'Retry duplicate resolution.'}).status_code==409
    client.cookies.clear();guest={'X-Device-Id':'11111111-1111-4111-8111-111111111111'}
    assert client.get('/api/materials?following=true',headers=guest).status_code==401
    assert client.get('/api/creators/settings',headers=guest).status_code==401
    assert client.post('/api/creators/author/follow',headers=guest,json={'enabled':True}).status_code==401
    assert conn.execute('SELECT count(*) FROM creator_reports').fetchone()[0]==1

def test_graph_role_privileges_and_audit(database,client,actor):
    _,conn=database;opt_in(client,actor)
    with conn.transaction():
        conn.execute('SET LOCAL ROLE mpsc')
        conn.execute("INSERT INTO creator_profiles(user_id) VALUES('outsider') ON CONFLICT DO NOTHING")
        conn.execute("INSERT INTO creator_follows(follower_id,creator_id) VALUES('outsider','author')")
        conn.execute("DELETE FROM creator_follows WHERE follower_id='outsider'")
        conn.execute("SELECT * FROM creator_blocks");conn.execute("SELECT * FROM creator_reports")
    with pytest.raises(Exception,match='append-only'):
        with conn.transaction():conn.execute("UPDATE creator_events SET action='tampered'")
