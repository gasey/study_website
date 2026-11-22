"""Question-note attachment, export disclosure and live shared-note links."""
from uuid import uuid4
from contextlib import asynccontextmanager
import pytest
from psycopg.types.json import Jsonb
from test_study_desks import desk_setup,room,join


@pytest.fixture(autouse=True)
def real_role(monkeypatch):
    from app.db import cursor
    from app.routers import study_desks,account_tools
    @asynccontextmanager
    async def role_cursor():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            yield cur
    monkeypatch.setattr(study_desks,'cursor',role_cursor)
    monkeypatch.setattr(account_tools,'cursor',role_cursor)


def save(client,h,data,version=0):
    return client.post('/api/desk/personal',headers=h,json={'user_id':'author','expected_version':version,'data':data})


def note(qid='cq_test',**kw):
    return {'id':'n1','title':'Synthetic question note','body':'PRIVATE_NOTE_BODY','subject':'English','question_id':qid,**kw}


def shared(client,actor,did,**kw):
    r=client.post(f'/api/desk/rooms/{did}/items',headers={**actor('author'),'Idempotency-Key':uuid4().hex},
      json={'kind':'note','title':'Synthetic linked note','body':'SHARED_NOTE_BODY','question_id':'cq_test',**kw})
    assert r.status_code==201,r.text
    return r.json()['id']


def message(client,h,did,iid,key=None,body='QUESTION_CONTEXT_BODY'):
    return client.post(f'/api/desk/rooms/{did}/messages',headers={**h,'Idempotency-Key':key or uuid4().hex},json={'body':body,'note_id':iid})


def mock(conn,user='author'):
    mid=uuid4().hex
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,%s,'udc',%s,600)",(mid,user,['cq_test']))
    return mid


def finish(conn,mid):
    conn.execute('UPDATE mock_sessions SET submitted_at=now(),elapsed_seconds=0,score=0,n_correct=0,n_wrong=0,n_skipped=1 WHERE id=%s',(mid,))


def test_personal_question_validation_cas_hidden_merge_and_no_rewards(client,actor,database):
    conn=database[1];h=actor('author')
    before=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    data={'notes':[note()]};r=save(client,h,data);assert r.status_code==200,r.text
    assert r.json()['data']['notes'][0]['question_id']=='cq_test'
    assert save(client,h,data).status_code==409
    assert save(client,h,{'notes':[note('missing')]},1).status_code==422
    locked=mock(conn)
    personal=client.get('/api/desk/personal').json()
    assert personal['data']['notes']==[] and personal['hidden_notes']==1
    assert save(client,h,{'notes':[note(body='ALTERED')]},1).status_code==409
    # Full-document save of a different field preserves hidden notes exactly.
    r=save(client,h,{'goal':'Revise tomorrow','notes':[]},1);assert r.status_code==200,r.text
    assert r.json()['data']['notes']==[]
    assert conn.execute("SELECT document->'notes'->0->>'body' FROM personal_desks WHERE user_id='author'").fetchone()[0]=='PRIVATE_NOTE_BODY'
    finish(conn,locked)
    assert client.get('/api/desk/personal').json()['data']['notes'][0]['body']=='PRIVATE_NOTE_BODY'
    assert save(client,h,{'notes':[note(None)]},2).status_code==200
    actor('outsider');assert client.get('/api/desk/personal').json()['data']['notes']==[]
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==before


def test_print_and_json_use_owned_snapshot_escape_markup_and_hide_assessed_notes(client,actor,database):
    conn=database[1];h=actor('author')
    data={'notes':[note(title='<script>alert(1)</script>',body='<img src="https://evil.test/x"> & Unicode: Ṭawng'),
                   note(None,id='n2',body='UNLINKED_NOTE')]}
    assert save(client,h,data).status_code==200
    url='/api/me/desk-notes-print?user_id=author'
    r=client.get(url);assert r.status_code==200,r.text
    assert r.headers['cache-control']=='private, no-store' and "default-src 'none'" in r.headers['content-security-policy']
    assert '<script>' not in r.text and '&lt;script&gt;' in r.text and '<img src=' not in r.text
    assert 'Ṭawng' in r.text and 'UNLINKED_NOTE' in r.text and 'Save as PDF' in r.text
    assert client.get('/api/me/desk-notes-print?user_id=outsider').status_code==409
    mid=mock(conn)
    r=client.get(url);assert r.status_code==200
    assert 'Ṭawng' not in r.text and 'UNLINKED_NOTE' in r.text
    exported=client.get('/api/me/data-export?user_id=author');assert exported.status_code==200,exported.text
    assert len(exported.json()['private_desk'][0]['document']['notes'])==1
    assert 'UNLINKED_NOTE' in exported.text and 'evil.test' not in exported.text
    finish(conn,mid)
    assert 'Ṭawng' in client.get(url).text
    actor('outsider');assert 'UNLINKED_NOTE' not in client.get('/api/me/desk-notes-print?user_id=outsider').text


@pytest.mark.parametrize('reverse',[False,True])
def test_note_chat_links_recheck_blocks_reveal_and_source_removal(client,actor,database,reverse):
    conn=database[1];did=room(client,actor);join(client,actor,did);iid=shared(client,actor,did)
    h=actor('outsider');url=f'/api/desk/rooms/{did}/notes/{iid}'
    assert client.get(url).json()['body']=='SHARED_NOTE_BODY'
    key=uuid4().hex;r=message(client,h,did,iid,key);assert r.status_code==201,r.text
    assert message(client,h,did,iid,key).json()['id']==r.json()['id']
    assert message(client,h,did,iid,key,body='DIFFERENT').status_code==409
    listed=client.get(f'/api/desk/rooms/{did}/messages').json()['items'][0]
    assert listed['note_id']==iid and listed['note_title']=='Synthetic linked note'
    mid=mock(conn,'outsider')
    assert client.get(url).status_code==409
    hidden=client.get(f'/api/desk/rooms/{did}/messages').json()['items'][0]
    assert hidden['note_id'] is None and 'QUESTION_CONTEXT_BODY' not in hidden['body']
    assert not client.get(f'/api/desk/rooms/{did}/items?kind=note').json()['items']
    assert message(client,h,did,iid).status_code==409
    finish(conn,mid)
    a,b=('outsider','author') if reverse else ('author','outsider')
    conn.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)',(a,b))
    assert client.get(url).status_code==404
    assert message(client,h,did,iid).status_code==404
    conn.execute('DELETE FROM creator_blocks WHERE user_id=%s AND blocked_id=%s',(a,b))
    conn.execute('UPDATE study_desk_items SET deleted_at=now() WHERE id=%s',(iid,))
    assert client.get(url).status_code==404
    assert client.get(f'/api/desk/rooms/{did}/messages').json()['items'][0]['note_id'] is None


def test_link_room_scope_departure_and_edit_gate(client,actor,database):
    conn=database[1];did=room(client,actor);join(client,actor,did);iid=shared(client,actor,did)
    other=room(client,actor);h=actor('author')
    assert message(client,h,other,iid).status_code==404
    mid=mock(conn)
    assert client.post(f'/api/desk/rooms/{did}/items/{iid}',headers=h,json={'expected_version':1,'title':'Change','body':'Changed','question_id':None}).status_code==409
    finish(conn,mid)
    assert client.post(f'/api/desk/rooms/{did}/items/{iid}',headers=h,json={'expected_version':1,'title':'Change','body':'Changed','question_id':None}).status_code==200
    assert client.get(f'/api/desk/rooms/{did}/notes/{iid}').json()['question_id'] is None
    h=actor('outsider');conn.execute("UPDATE study_desk_members SET left_at=now() WHERE desk_id=%s AND user_id='author'",(did,))
    assert client.get(f'/api/desk/rooms/{did}/notes/{iid}').status_code==404
    assert client.get(f'/api/desk/rooms/{did}/items?kind=note').json()['items']==[]
    actor('reviewer1');assert client.get(f'/api/desk/rooms/{did}/notes/{iid}').status_code==404


def test_native_link_mutation_denied_but_plain_chat_unchanged(client,actor,database):
    from test_mobile_companion import connect
    did=room(client,actor);join(client,actor,did);iid=shared(client,actor,did)
    mobile,_=connect(client,actor,'outsider')
    assert client.get('/api/me/desk-notes-print?user_id=outsider',headers=mobile).status_code==403
    assert client.get(f'/api/desk/rooms/{did}/notes/{iid}',headers=mobile).status_code==403
    assert message(client,mobile,did,iid).status_code==403
    response=client.post(f'/api/desk/rooms/{did}/messages',headers={**mobile,'Idempotency-Key':uuid4().hex},json={'body':'Ordinary native chat'})
    assert response.status_code==201,response.text


def test_room_print_only_own_notes_and_same_room_sql_guard(client,actor,database):
    import psycopg
    conn=database[1];did=room(client,actor);join(client,actor,did);iid=shared(client,actor,did)
    h=actor('outsider')
    other=client.post(f'/api/desk/rooms/{did}/items',headers={**h,'Idempotency-Key':uuid4().hex},json={'kind':'note','title':'Other author','body':'OTHER_MEMBER_NOTE'})
    assert other.status_code==201,other.text
    r=client.get(f'/api/me/desk-notes-print?user_id=outsider&desk_id={did}')
    assert r.status_code==200 and 'OTHER_MEMBER_NOTE' in r.text and 'SHARED_NOTE_BODY' not in r.text
    actor('author');mid=mock(conn)
    r=client.get(f'/api/me/desk-notes-print?user_id=author&desk_id={did}')
    assert r.status_code==200 and 'SHARED_NOTE_BODY' not in r.text
    finish(conn,mid)
    assert 'SHARED_NOTE_BODY' in client.get(f'/api/me/desk-notes-print?user_id=author&desk_id={did}').text
    second=room(client,actor)
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        conn.execute("INSERT INTO study_desk_messages(desk_id,author_id,body,note_id,request_key,request_hash) VALUES(%s,'author','Wrong room',%s,%s,'test')",(second,iid,uuid4().hex))
    actor('reviewer1');assert client.get(f'/api/me/desk-notes-print?user_id=reviewer1&desk_id={did}').status_code==404
