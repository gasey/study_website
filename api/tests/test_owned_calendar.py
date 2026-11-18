"""Private calendar behavior, replay guards and export boundaries on disposable PG."""
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from uuid import uuid4
import hashlib
import pytest
from app.db import cursor
from app.routers import calendar_owned
from app.services import owned_calendar
from test_learning_loop import run
from test_learning_workflows import learner


@pytest.fixture(autouse=True)
def application_role(monkeypatch):
    @asynccontextmanager
    async def app_cursor():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            yield cur
    monkeypatch.setattr(calendar_owned,'cursor',app_cursor)


def save(client,h,**patch):
    eid=patch.pop('id',str(uuid4()))
    body={'expected_version':0,'date':'2026-11-20','title':'Finish Polity chapter 3','note':'Private goal','kind':'personal',**patch}
    return client.post('/api/me/calendar/entries/'+eid,headers=h,json=body)


def layers(client,h):
    r=client.get('/api/me/calendar-layers?start=2026-11-01&end=2026-11-30',headers=h)
    assert r.status_code==200,r.text
    assert r.headers['cache-control']=='private, no-store' and 'etag' not in r.headers
    return r.json()


def test_owned_crud_account_scope_and_stale_edits(client,actor,database):
    user,h=learner(database,actor)
    before=database[1].execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    r=save(client,h);assert r.status_code==200,r.text
    entry=r.json();eid=entry['id'];assert entry['version']==1
    mine=layers(client,h);assert mine['registered'] and [e['id'] for e in mine['entries']]==[eid]
    assert mine['occurrences'][0]['day']=='2026-11-20'
    other,oh=learner(database,actor)
    assert layers(client,oh)['entries']==[]
    assert save(client,oh,id=eid,expected_version=1).status_code==404
    assert client.post('/api/me/calendar/entries/'+eid+'/delete',headers=oh,json={'expected_version':1}).status_code==404
    h=actor(user)
    assert save(client,h,id=eid).status_code==409
    assert save(client,h,id=eid,expected_version=1,title='Updated private goal').json()['version']==2
    assert client.post('/api/me/calendar/entries/'+eid+'/delete',headers=h,json={'expected_version':1}).status_code==409
    assert client.post('/api/me/calendar/entries/'+eid+'/delete',headers=h,json={'expected_version':2}).json()=={'deleted':True}
    assert layers(client,h)['entries']==[]
    assert database[1].execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==before


def test_guests_validation_csrf_and_caps(client,actor,database):
    client.cookies.clear()
    assert not layers(client,{})['registered'] and layers(client,{})['entries']==[]
    assert save(client,{}).status_code==401
    assert client.get('/api/me/calendar/feed').status_code==401
    user,h=learner(database,actor)
    assert save(client,{}).status_code==403
    for patch in ({'user_id':'outsider'},{'title':' '},{'date':'2101-01-01'},
                  {'recurrence':7},{'kind':'progress-test'},{'kind':'progress-test','recurrence':8},
                  {'title':'Hello\x00world'},{'collection_id':'nonexistent-private-exam'}):
        assert save(client,h,**patch).status_code==422,patch
    # Enforced under the owner lock, counting all dates, using the app-role writes.
    conn=database[1]
    cid='calendar-test-'+uuid4().hex
    conn.execute("INSERT INTO collections(id,title,kind,visibility) VALUES(%s,'Synthetic exam','exam','public')",(cid,))
    for i in range(20):
        conn.execute("INSERT INTO calendar_entries(id,user_id,date,title,kind,recurrence,collection_id) VALUES(%s,%s,'2026-01-01','Synthetic slot','progress-test',7,%s)",(uuid4(),user,cid))
    assert save(client,h,kind='progress-test',recurrence=14,collection_id=cid).status_code==409
    # Existing slots can be edited at the cap.
    eid=str(conn.execute('SELECT id FROM calendar_entries WHERE user_id=%s LIMIT 1',(user,)).fetchone()[0])
    assert save(client,h,id=eid,expected_version=1,kind='progress-test',recurrence=14,collection_id=cid).status_code==200
    conn.execute("INSERT INTO calendar_entries(id,user_id,date,title,kind) SELECT gen_random_uuid(),%s,'2026-01-01','Synthetic old note','personal' FROM generate_series(1,480)",(user,))
    assert save(client,h).status_code==409


def test_projection_rolls_forward_without_writes_and_keeps_fortnight_anchor(client,actor,database):
    user,h=learner(database,actor);conn=database[1]
    cid='calendar-test-'+uuid4().hex
    conn.execute("INSERT INTO collections(id,title,kind,visibility) VALUES(%s,'Synthetic exam','exam','public')",(cid,))
    assert save(client,h,kind='progress-test',recurrence=14,collection_id=cid,date='2026-11-02').status_code==200
    assert save(client,h,kind='exam-target',collection_id=cid,title='My target exam',date='2026-11-30').status_code==200
    rows=run(client,owned_calendar.entries,user)
    result=owned_calendar.occurrences(rows,date(2026,11,1),date(2026,12,31),date(2026,11,17))
    assert [r['day'] for r in result if r['kind']=='progress-test']==[date(2026,11,30),date(2026,12,14),date(2026,12,28)]
    assert len([r for r in result if r['kind']=='exam-target'])==1
    before=conn.execute('SELECT count(*) FROM mock_sessions').fetchone()[0]
    for _ in range(2):
        projection=run(client,owned_calendar.layers,user,date(2026,11,1),date(2026,12,31))
        assert len(projection['entries'])==2
    assert conn.execute('SELECT count(*) FROM mock_sessions').fetchone()[0]==before
    assert conn.execute('SELECT version FROM calendar_entries WHERE user_id=%s ORDER BY kind',(user,)).fetchall()==[(1,),(1,)]


def test_feed_hash_once_rotation_revocation_scope_and_cookie_independence(client,actor,database):
    user,h=learner(database,actor);conn=database[1]
    own=save(client,h,title='Private personal title').json()
    state=client.get('/api/me/calendar/feed',headers=h).json();assert state['version']==0 and not state['active']
    r=client.post('/api/me/calendar/feed/rotate',headers=h,json={'expected_version':0})
    assert r.status_code==200,r.text
    first=r.json();token=first['url'].rsplit('/',1)[1][:-4]
    row=conn.execute('SELECT token_hash,version FROM calendar_feed_tokens WHERE user_id=%s',(user,)).fetchone()
    assert row==(hashlib.sha256(token.encode()).hexdigest(),1) and token not in str(row)
    assert 'url' not in client.get('/api/me/calendar/feed',headers=h).json()
    other,oh=learner(database,actor)
    assert save(client,oh,title='Other account secret').status_code==200
    fetched=client.get(first['url']) # Other signed-in account cannot replace feed ownership.
    assert fetched.status_code==200 and 'Private personal title' in fetched.text and 'Other account secret' not in fetched.text
    client.cookies.clear();users=conn.execute('SELECT count(*) FROM users').fetchone()[0]
    r=client.get(first['url']);assert r.status_code==200 and not r.cookies
    assert conn.execute('SELECT count(*) FROM users').fetchone()[0]==users
    assert r.headers['cache-control']=='private, no-store' and r.headers['referrer-policy']=='no-referrer'
    assert 'etag' not in r.headers and 'text/calendar' in r.headers['content-type']
    h=actor(user)
    assert client.post('/api/me/calendar/feed/rotate',headers=h,json={'expected_version':0}).status_code==409
    second=client.post('/api/me/calendar/feed/rotate',headers=h,json={'expected_version':1}).json()
    assert client.get(first['url']).status_code==404
    assert client.get(second['url']).status_code==200
    assert client.post('/api/me/calendar/feed/revoke',headers=h,json={'expected_version':1}).status_code==409
    assert client.post('/api/me/calendar/feed/revoke',headers=h,json={'expected_version':2}).json()=={'version':3,'active':False}
    assert client.get(second['url']).status_code==404
    assert conn.execute('SELECT token_hash,revoked_at IS NOT NULL FROM calendar_feed_tokens WHERE user_id=%s',(user,)).fetchone()==(None,True)
    assert client.get('/api/calendar/feed/invalid.ics').status_code==404


def test_ics_escaping_unicode_folding_stable_uids_and_exclusive_end():
    now=datetime(2026,11,17,18,31,tzinfo=timezone.utc)
    row={'id':str(uuid4()),'date':date(2026,11,18),'title':'é漢🙂'*60,
         'note':'Private, text; slash\\\r\nBEGIN:VEVENT\rATTENDEE:fake@example.test',
         'kind':'personal','recurrence':None,'collection_id':None,'version':3,'updated_at':now}
    content=owned_calendar.feed([row],date(2026,11,17))
    assert content.endswith('END:VCALENDAR\r\n')
    assert all(len(line.encode())<=75 for line in content.split('\r\n'))
    unfolded=content.replace('\r\n ','')
    assert unfolded.count('\r\nBEGIN:VEVENT\r\n')==1
    assert '\r\nATTENDEE:' not in unfolded
    assert 'DESCRIPTION:Private\\, text\\; slash\\\\\\nBEGIN:VEVENT\\nATTENDEE:' in unfolded
    assert 'DTSTART;VALUE=DATE:20261118\r\nDTEND;VALUE=DATE:20261119' in unfolded
    assert 'DTSTAMP:20261117T183100Z' in unfolded and 'SEQUENCE:3' in unfolded
    assert owned_calendar.feed([row],date(2026,11,17))==content


def test_mobile_reads_private_layers_but_calendar_writes_and_token_management_stay_closed(client,actor,database):
    from test_mobile_companion import connect
    user,h=learner(database,actor)
    assert save(client,h,title='My native-visible note').status_code==200
    headers,_=connect(client,actor,user)
    assert layers(client,headers)['entries'][0]['title']=='My native-visible note'
    assert client.post('/api/me/calendar/entries/'+str(uuid4()),headers=headers,json={}).status_code==403
    assert client.get('/api/me/calendar/feed',headers=headers).status_code==403
    for action in ('rotate','revoke'):
        assert client.post('/api/me/calendar/feed/'+action,headers=headers,json={'expected_version':0}).status_code==403


def test_feed_aggregate_learning_eligibility_and_owner_scope(client,actor,database):
    from test_learning_loop import questions,attempt
    from app.services import review_queue
    user,h=learner(database,actor);conn=database[1]
    _,ids=questions(database,2)
    aid=attempt(conn,user,ids[0],False)
    run(client,review_queue.apply_attempt,aid)
    other,oh=learner(database,actor)
    other_aid=attempt(conn,other,ids[1],False)
    run(client,review_queue.apply_attempt,other_aid)
    h=actor(user)
    url=client.post('/api/me/calendar/feed/rotate',headers=h,json={'expected_version':0}).json()['url']
    exported=client.get(url).text.replace('\r\n ','')
    assert exported.count('SUMMARY:1 projected reviews')==1
    assert exported.count('SUMMARY:1 verified checks')==1
    assert all(q not in exported for q in ids) and user not in exported and other not in exported
    conn.execute("UPDATE canonical_questions SET status='held' WHERE id=%s",(ids[0],))
    exported=client.get(url).text
    assert 'projected reviews' not in exported and 'verified checks' not in exported


def test_feed_credentials_are_redacted_from_uvicorn_access_records():
    import logging
    token='a'*43
    record=logging.LogRecord('uvicorn.access',logging.INFO,'test',1,'%s - "%s %s HTTP/%s" %d',
                             ('127.0.0.1','GET','/api/calendar/feed/'+token+'.ics','1.1',200),None)
    assert owned_calendar.RedactFeedAccess().filter(record)
    assert token not in record.getMessage() and '[redacted].ics' in record.getMessage()
