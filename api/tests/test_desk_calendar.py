"""One owned calendar store, explicit room consent and live membership visibility."""
from contextlib import asynccontextmanager
from datetime import timedelta
from uuid import uuid4
import pytest
from test_study_desks import desk_setup,room,join
from test_owned_calendar import save


@pytest.fixture(autouse=True)
def app_role(monkeypatch):
    from app.db import cursor
    from app.routers import study_desks,calendar_owned
    @asynccontextmanager
    async def role_cursor():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            yield cur
    monkeypatch.setattr(study_desks,'cursor',role_cursor)
    monkeypatch.setattr(calendar_owned,'cursor',role_cursor)


def view(client,actor,did,user='outsider',**params):
    return client.get(f'/api/desk/rooms/{did}/calendar',headers=actor(user),params={'start':'2026-11-01','end':'2026-12-01',**params})


def test_explicit_sharing_central_edit_withdrawal_and_owned_exports(client,actor,database):
    conn=database[1];did=room(client,actor);join(client,actor,did)
    before=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    p=save(client,actor('author'),title='PRIVATE_DATE',note='PRIVATE_NOTE').json()
    assert view(client,actor,did).json()['occurrences']==[]
    r=save(client,actor('author'),id=p['id'],expected_version=1,desk_id=did,title='Shared target',note='Deliberate note',kind='exam-target')
    assert r.status_code==200,r.text
    r=view(client,actor,did);assert r.status_code==200,r.text
    assert r.headers['cache-control']=='private, no-store'
    x=r.json()['occurrences'];assert len(x)==1 and x[0]['title']=='Shared target' and x[0]['note']=='Deliberate note' and not x[0]['is_you']
    assert 'PRIVATE_NOTE' not in r.text
    # Not a copied event: central CAS edit changes the room immediately.
    h=actor('author');assert save(client,h,id=p['id'],expected_version=1,desk_id=did).status_code==409
    assert save(client,h,id=p['id'],expected_version=2,title='Live changed').status_code==200
    assert view(client,actor,did).json()['occurrences'][0]['title']=='Live changed'
    own=client.get('/api/me/calendar-layers?start=2026-11-01&end=2026-12-01',headers=actor('outsider')).json()
    assert own['entries']==[]
    export=client.get('/api/me/data-export?user_id=outsider',headers=actor('outsider'));assert export.status_code==200 and 'Live changed' not in export.text
    assert save(client,actor('author'),id=p['id'],expected_version=3,desk_id=None).status_code==200
    assert view(client,actor,did).json()['occurrences']==[]
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==before


@pytest.mark.parametrize('reverse',[False,True])
def test_blocks_departure_rejoin_epoch_closure_and_no_other_room(client,actor,database,reverse):
    conn=database[1];did=room(client,actor);join(client,actor,did)
    p=save(client,actor('author'),desk_id=did).json()
    assert len(view(client,actor,did).json()['occurrences'])==1
    a,b=('author','outsider') if reverse else ('outsider','author')
    conn.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)',(a,b))
    assert view(client,actor,did).json()['occurrences']==[]
    conn.execute('DELETE FROM creator_blocks WHERE user_id=%s AND blocked_id=%s',(a,b))
    assert len(view(client,actor,did).json()['occurrences'])==1
    conn.execute("UPDATE study_desk_members SET left_at=now() WHERE desk_id=%s AND user_id='author'",(did,))
    assert view(client,actor,did).json()['occurrences']==[]
    conn.execute("UPDATE study_desk_members SET left_at=NULL,joined_at=clock_timestamp() WHERE desk_id=%s AND user_id='author'",(did,))
    assert view(client,actor,did).json()['occurrences']==[]
    assert save(client,actor('author'),id=p['id'],expected_version=1).status_code==409
    assert save(client,actor('author'),id=p['id'],expected_version=1,desk_id=did).status_code==200
    assert len(view(client,actor,did).json()['occurrences'])==1
    second=room(client,actor);join(client,actor,second)
    assert view(client,actor,second).json()['occurrences']==[]
    conn.execute('UPDATE study_desks SET closed_at=now() WHERE id=%s',(did,))
    assert view(client,actor,did).status_code==404
    conn.execute('UPDATE study_desks SET closed_at=NULL WHERE id=%s',(did,))
    from test_learning_workflows import learner
    uid,h=learner(database,actor)
    conn.execute('INSERT INTO study_desk_members(desk_id,user_id) VALUES(%s,%s)',(did,uid))
    assert save(client,h,desk_id=did,title='CLOSED_AUTHOR_DATE').status_code==200
    assert 'CLOSED_AUTHOR_DATE' in view(client,actor,did).text
    conn.execute("UPDATE users SET closed_at=now(),email=NULL,password_hash=NULL,name=NULL,avatar=NULL,email_verified_at=NULL,contribution_public=false WHERE id=%s",(uid,))
    assert 'CLOSED_AUTHOR_DATE' not in view(client,actor,did).text



def test_membership_flag_span_delete_and_native_boundaries(client,actor,database,monkeypatch):
    from app.config import settings
    from app.services.mobile_identity import allowed,capabilities
    did=room(client,actor);join(client,actor,did)
    assert save(client,actor('reviewer1'),desk_id=did).status_code==404
    assert view(client,actor,did,'reviewer1').status_code==404
    assert view(client,actor,did,end='2027-06-01').status_code==422
    assert view(client,actor,did,end='2026-10-01').status_code==422
    p=save(client,actor('author'),desk_id=did).json()
    monkeypatch.setattr(settings,'study_desks_private_enabled',False)
    assert view(client,actor,did).status_code==409
    # Disabling or closing shared views never prevents withdrawing owned content.
    assert save(client,actor('author'),id=p['id'],expected_version=1,desk_id=None).status_code==200
    monkeypatch.setattr(settings,'study_desks_private_enabled',True)
    assert save(client,actor('author'),id=p['id'],expected_version=2,desk_id=did).status_code==200
    r=client.post('/api/me/calendar/entries/'+p['id']+'/delete',headers=actor('author'),json={'expected_version':3});assert r.status_code==200,r.text
    assert view(client,actor,did).json()['occurrences']==[]
    from test_mobile_companion import connect
    mobile,_=connect(client,actor,'outsider')
    assert client.get(f'/api/desk/rooms/{did}/calendar?start=2026-11-01&end=2026-12-01',headers=mobile).status_code==403
    assert not allowed('GET',f'/api/desk/rooms/{did}/calendar')
    assert 'desk_calendar' not in capabilities()


def test_recurring_slots_reuse_owner_projection_without_participation(client,actor,database):
    from app.services import owned_calendar
    conn=database[1];did=room(client,actor);join(client,actor,did)
    today=owned_calendar.india_today();day=today+timedelta(days=2)
    conn.execute("UPDATE collections SET kind='exam',visibility='public' WHERE id='udc'")
    r=save(client,actor('author'),desk_id=did,kind='progress-test',recurrence=7,collection_id='udc',date=day.isoformat());assert r.status_code==200,r.text
    before=conn.execute('SELECT count(*) FROM mock_sessions').fetchone()[0]
    result=view(client,actor,did,start=today.isoformat(),end=(today+timedelta(days=30)).isoformat()).json()['occurrences']
    assert [x['day'] for x in result]==[(day+timedelta(days=n)).isoformat() for n in (0,7,14,21,28)]
    assert conn.execute('SELECT count(*) FROM mock_sessions').fetchone()[0]==before
    # The private subscription is still sourced by the account owner only.
    from test_learning_loop import run
    text=run(client,owned_calendar.subscription,'outsider')
    assert r.json()['title'] not in text
