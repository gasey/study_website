"""Private inbox pagination, state, delivery settings and desk-message isolation."""
from uuid import uuid4
from app.config import settings

def headers(actor,user='author'):
    return {**actor(user),'x-inbox-user':user}

def notice(conn,user,**kwargs):
    cols=['user_id','event_key','message']+list(kwargs)
    vals=[user,'inbox-test:'+uuid4().hex,'Synthetic Inbox update']+list(kwargs.values())
    return conn.execute('INSERT INTO review_notifications('+','.join(cols)+') VALUES ('+','.join(['%s']*len(vals))+') RETURNING id',vals).fetchone()[0]

def test_notifications_pagination_read_all_and_account_isolation(client,actor,database):
    conn=database[1];h=headers(actor)
    ids=[notice(conn,'author',discussion_question_id='cq_test') for _ in range(5)]
    other=notice(conn,'outsider')
    first=client.get('/api/inbox/notifications?category=discussions&limit=2');assert first.status_code==200,first.text
    assert first.headers['cache-control']=='private, no-store'
    p=first.json();assert [n['id'] for n in p['items']]==ids[-2:][::-1]
    assert all('user_id' not in n and 'event_key' not in n for n in p['items'])
    more=client.get('/api/inbox/notifications?category=discussions&limit=2&before='+str(p['next_cursor'])).json()
    assert [n['id'] for n in more['items']]==ids[-4:-2][::-1]
    newest=notice(conn,'author',discussion_question_id='cq_test')
    assert client.post('/api/inbox/notifications/read-all',headers=h,json={'through_id':p['snapshot_id'],'category':'discussions'}).status_code==200
    assert conn.execute('SELECT read_at IS NULL FROM review_notifications WHERE id=%s',(newest,)).fetchone()[0]
    assert conn.execute('SELECT read_at IS NULL FROM review_notifications WHERE id=%s',(other,)).fetchone()[0]
    assert client.post('/api/inbox/notifications/'+str(other)+'/read',headers=h,json={'read':True}).status_code==404
    assert client.post('/api/inbox/notifications/'+str(ids[0])+'/read',headers=h,json={'read':False}).status_code==200
    assert ids[0] in [n['id'] for n in client.get('/api/inbox/notifications?unread=true').json()['items']]
    assert client.post('/api/inbox/notifications/'+str(ids[0])+'/read',headers={**h,'x-inbox-user':'outsider'},json={'read':True}).status_code==409
    assert client.post('/api/inbox/preferences',headers={**h,'X-Review-CSRF':'invalid'},json={}).status_code==403
    assert client.get('/api/inbox/notifications?category=invalid').status_code==422
    assert client.get('/api/inbox/notifications?before=-1').status_code==422
    actor('outsider');mine=client.get('/api/inbox/notifications').json()['items'];assert all(n['id'] not in ids for n in mine)
    client.cookies.clear();assert client.get('/api/inbox/notifications').status_code==401

def test_preferences_quiet_future_updates_without_losing_history(client,actor,database):
    conn=database[1];h=headers(actor)
    before=notice(conn,'author',discussion_question_id='cq_test')
    prefs=client.get('/api/inbox/preferences').json();assert prefs['in_app']['discussions'] and not prefs['email_available'] and not prefs['push_available']
    payload={**prefs['in_app'],'discussions':False}
    assert client.post('/api/inbox/preferences',headers=h,json=payload).status_code==200
    quiet=notice(conn,'author',discussion_question_id='cq_test')
    assert not conn.execute('SELECT silent FROM review_notifications WHERE id=%s',(before,)).fetchone()[0]
    assert conn.execute('SELECT silent FROM review_notifications WHERE id=%s',(quiet,)).fetchone()[0]
    assert quiet not in [n['id'] for n in client.get('/api/inbox/notifications?unread=true').json()['items']]
    assert quiet in [n['id'] for n in client.get('/api/inbox/notifications').json()['items']]
    legacy=client.get('/api/review/notifications/unread').json()['unread']
    assert legacy==client.get('/api/inbox/notifications').json()['unread']
    assert client.post('/api/inbox/notifications/'+str(quiet)+'/read',headers=h,json={'read':False}).status_code==200
    assert quiet in [n['id'] for n in client.get('/api/inbox/notifications?unread=true').json()['items']]
    assert client.post('/api/inbox/preferences',headers=h,json={**payload,'push':True}).status_code==422
    client.post('/api/inbox/preferences',headers=h,json={})

def test_threads_respect_membership_join_time_blocks_and_read_cursor(client,actor,database):
    conn=database[1];previous=settings.study_desks_private_enabled;settings.study_desks_private_enabled=True
    try:
        did='inbox-desk-'+uuid4().hex
        conn.execute("INSERT INTO study_desks(id,owner_id,name,goal) VALUES (%s,'author','Synthetic Inbox desk','Study together')",(did,))
        conn.execute("INSERT INTO study_desk_members(desk_id,user_id) VALUES (%s,'author'),(%s,'reviewer1')",(did,did))
        def msg(author,body):return conn.execute('INSERT INTO study_desk_messages(desk_id,author_id,body,request_key,request_hash) VALUES (%s,%s,%s,%s,%s) RETURNING id',(did,author,body,uuid4().hex,'test')).fetchone()[0]
        old=msg('reviewer1','Before join');conn.execute("UPDATE study_desk_messages SET created_at=now()-interval '1 day' WHERE id=%s",(old,))
        mid=msg('reviewer1','Visible partner message');h=headers(actor)
        rows=client.get('/api/inbox/threads');assert rows.status_code==200,rows.text
        thread=next(x for x in rows.json()['items'] if x['id']==did);assert thread['unread']==1 and thread['last_message']=='Visible partner message'
        assert next(x for x in client.get('/api/inbox/threads?selected='+did).json()['items'])['id']==did
        assert client.get('/api/inbox/threads/'+did+'/messages').json()['items'][0]['id']==mid
        assert client.get('/api/inbox/threads?limit=0').status_code==422
        assert client.get('/api/inbox/unread').json()['conversations']>=1
        assert client.post('/api/inbox/threads/'+did+'/read',headers=h,json={'through_id':10**12}).json()['through_id']==mid
        new=msg('reviewer1','New unread partner message')
        assert next(x['unread'] for x in client.get('/api/inbox/threads').json()['items'] if x['id']==did)==1
        conn.execute("INSERT INTO creator_blocks(user_id,blocked_id) VALUES ('author','reviewer1') ON CONFLICT DO NOTHING")
        t=next(x for x in client.get('/api/inbox/threads').json()['items'] if x['id']==did);assert t['last_message'] is None and t['unread']==0
        assert client.get('/api/inbox/unread').json()['conversations']==0
        conn.execute("DELETE FROM creator_blocks WHERE user_id='author' AND blocked_id='reviewer1'")
        headers(actor,'outsider');assert did not in [t['id'] for t in client.get('/api/inbox/threads').json()['items']]
        assert client.post('/api/inbox/threads/'+did+'/read',headers=headers(actor,'outsider'),json={'through_id':new}).status_code==404
        assert client.get('/api/inbox/threads/'+did+'/messages').status_code==404
        h=headers(actor);conn.execute("UPDATE study_desk_members SET left_at=now() WHERE desk_id=%s AND user_id='author'",(did,))
        assert did not in [t['id'] for t in client.get('/api/inbox/threads').json()['items']]
        assert client.post('/api/inbox/threads/'+did+'/read',headers=h,json={'through_id':new}).status_code==404
    finally:
        settings.study_desks_private_enabled=previous

def test_inbox_self_service_does_not_require_staff_bank_mfa(client,actor,database):
    conn=database[1];h=headers(actor,'owner');nid=notice(conn,'owner')
    previous=settings.mfa_enforce_staff;settings.mfa_enforce_staff=True
    try:
        assert client.post('/api/inbox/notifications/'+str(nid)+'/read',headers=h,json={'read':True}).status_code==200
        assert client.get('/api/inbox/notifications',headers={'x-inbox-user':'author'}).status_code==409
    finally:settings.mfa_enforce_staff=previous
