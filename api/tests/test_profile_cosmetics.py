"""V.5 account edits, moderation/disclosure, and atomic own-once wallet spending."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from uuid import uuid4
import pytest
from psycopg import sql
from app.db import cursor
from app.routers import profile_identity,avatars,creators,search
from app.services import avatars as catalog
from test_learning_workflows import learner

@pytest.fixture(autouse=True)
def mpsc(monkeypatch):
    @asynccontextmanager
    async def app_cursor():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            yield cur
    for module in (profile_identity,avatars,creators,search):monkeypatch.setattr(module,'cursor',app_cursor)


def edit(client,h,**patch):
    current=client.get('/api/me/identity',headers=h).json()
    body={k:current[k] for k in ('user_id','handle','bio')}
    body.update(name=current['name'] or '',expected_version=current['identity_version'])
    return client.post('/api/me/identity',headers=h,json=body|patch)


def buy(client,h,user,item='top-plum',price=25,**patch):
    return client.post('/api/me/avatar/purchase',headers=h,json={'user_id':user,'item_id':item,'price_points':price,'catalog_sha256':catalog.CATALOG_SHA256,**patch})


def funds(conn,user,points):
    conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,points,note) VALUES(%s,%s,'adjustment',%s,'Synthetic test balance')",(user,uuid4().hex,points))


def test_identity_rename_cooldown_casefold_and_no_reward_writes(client,actor,database):
    user,h=learner(database,actor);conn=database[1];handle='writer_'+uuid4().hex[:10]
    before=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    assert edit(client,h,handle=handle,name='Synthetic Writer').status_code==200
    current=client.get('/api/me/identity',headers=h)
    assert current.headers['cache-control']=='private, no-store'
    assert current.json()['handle']==handle and current.json()['rename_available_at']
    assert client.get('/api/me/profile',headers=h).json()['name']=='Synthetic Writer'
    assert edit(client,h,handle=handle+'x').status_code==409
    assert edit(client,h,name='Updated Writer').status_code==200 # No-op handle doesn't consume rename.
    assert edit(client,h,expected_version=0).status_code==409
    assert edit(client,h,user_id='owner').status_code==409
    assert conn.execute("SELECT count(*) FROM account_security_events WHERE user_id=%s AND action='handle_changed'",(user,)).fetchone()[0]==1
    conn.execute("UPDATE users SET handle_changed_at=now()-interval '30 days 1 second' WHERE id=%s",(user,))
    assert edit(client,h,handle=handle+'x').status_code==200
    other,oh=learner(database,actor)
    assert edit(client,oh,handle=(handle+'x').upper()).status_code==409
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==before


def test_identity_guests_validation_legacy_name_cas_and_concurrent_uniqueness(client,actor,database):
    client.cookies.clear();assert client.get('/api/me/identity').status_code==401
    user,h=learner(database,actor)
    for patch in ({'handle':'admin'},{'handle':'guest-abc'},{'handle':'a b'},{'bio':'x'*141},{'name':'Hello\x00world'},{'points':999}):
        assert edit(client,h,**patch).status_code==422,patch
    assert client.post('/api/me/identity',json={}).status_code==403
    prior=client.get('/api/me/identity',headers=h).json()['identity_version']
    assert client.patch('/api/me/profile',headers=h,json={'name':'Old client edit'}).status_code==200
    assert edit(client,h,expected_version=prior).status_code==409
    # Two owners racing for the same canonical handle: exactly one wins.
    other,oh=learner(database,actor);wanted='reader_'+uuid4().hex[:10]
    def request(which):
        uid,headers=which
        # Credentials are per request; do not mutate the shared TestClient jar.
        return client.post('/api/me/identity',headers=headers|{'Cookie':'ism_session=test-session-'+uid},json={'user_id':uid,'expected_version':database[1].execute('SELECT identity_version FROM users WHERE id=%s',(uid,)).fetchone()[0],'handle':wanted,'name':'','bio':''})
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(request,[(user,h),(other,oh)]))
    assert sorted(r.status_code for r in results)==[200,409]


def test_bio_pending_search_block_report_moderation_and_legacy_route(client,actor,database):
    user,h=learner(database,actor);marker='biomarker'+uuid4().hex[:10]
    assert edit(client,h,bio=marker).json()['bio_needs_approval']
    assert client.post('/api/creators/settings',headers=h,json={'public':True,'bio':marker}).status_code==200
    other,oh=learner(database,actor)
    assert client.get('/api/creators/'+user,headers=oh).json()['bio']==''
    assert client.get('/api/search',headers=oh,params={'q':marker,'category':'people'}).json()['groups'][0]['items']==[]
    assert not any(r['bio']==marker for r in client.get('/api/creators',headers=oh).json()['items'])
    assert client.post('/api/admin/bank/profile-bios/'+user+'/decision',headers=oh,json={'expected_version':1,'action':'approve','reason':'Synthetic moderation decision'}).status_code==403
    owner=actor('owner');queue=client.get('/api/admin/bank/profile-bios',headers=owner).json()
    row=next(r for r in queue['items'] if r['user_id']==user)
    path='/api/admin/bank/profile-bios/'+user+'/decision'
    assert client.post(path,headers=owner,json={'expected_version':row['bio_version'],'action':'approve','reason':'Synthetic bio approval only.'}).status_code==200
    assert client.post(path,headers=owner,json={'expected_version':row['bio_version'],'action':'hide','reason':'Stale synthetic bio action.'}).status_code==409
    oh=actor(other)
    assert client.get('/api/creators/'+user,headers=oh).json()['bio']==marker
    assert client.post('/api/creators/'+user+'/report',headers=oh,json={'reason':'other','note':'Synthetic report about this bio.'}).status_code==200
    owner=actor('owner');row=next(r for r in client.get('/api/admin/bank/profile-bios',headers=owner).json()['items'] if r['user_id']==user)
    assert client.post(path,headers=owner,json={'expected_version':row['bio_version'],'action':'hide','reason':'Synthetic removal decision only.'}).status_code==200
    h=actor(user)
    assert client.post('/api/creators/settings',headers=h,json={'public':True,'bio':marker}).status_code==200
    assert client.get('/api/me/identity',headers=h).json()['bio_hidden'] # Same text cannot unhide.
    assert client.post('/api/creators/settings',headers=h,json={'public':True,'bio':marker+' revised'}).status_code==200
    assert client.get('/api/me/identity',headers=h).json()['bio_needs_approval']
    assert client.post('/api/creators/'+other+'/block',headers=h,json={'enabled':True}).status_code==200
    oh=actor(other);assert client.get('/api/creators/'+user,headers=oh).status_code==404


def test_points_purchase_replay_equip_and_durable_ownership(client,actor,database):
    user,h=learner(database,actor);conn=database[1];funds(conn,user,75)
    before=client.get('/api/me/avatar?catalog_version=2',headers=h).json();assert not next(i for i in before['catalog'] if i['id']=='top-plum')['available']
    result=buy(client,h,user);assert result.status_code==200,result.text
    assert result.json()['points_spent']==25 and result.json()['balance']==50
    assert buy(client,h,user).json()['replayed']
    after=client.get('/api/me/avatar?catalog_version=2',headers=h).json()
    assert after['points']==50 and after['avatar_version']==1
    assert next(i for i in after['catalog'] if i['id']=='top-plum')['claimed']
    look={**catalog.DEFAULT,'top':'Plum'}
    assert client.post('/api/me/avatar?catalog_version=2',headers=h,json={'user_id':user,'expected_version':1,'look':look}).status_code==200
    funds(conn,user,-100)
    assert next(i for i in client.get('/api/me/avatar?catalog_version=2',headers=h).json()['catalog'] if i['id']=='top-plum')['available']
    rows=conn.execute("SELECT xp,points FROM reward_ledger WHERE user_id=%s AND event_key LIKE 'cosmetic:%%'",(user,)).fetchall()
    assert rows==[(0,-25)]
    assert conn.execute("SELECT count(*) FROM avatar_events WHERE user_id=%s AND action='purchased'",(user,)).fetchone()[0]==1
    assert conn.execute('SELECT count(*) FROM reward_daily_counters WHERE user_id=%s',(user,)).fetchone()[0]==0


def test_shop_account_price_catalog_level_and_native_guards(client,actor,database):
    user,h=learner(database,actor);conn=database[1]
    assert buy(client,{},user).status_code==403
    assert buy(client,h,'owner').status_code==409
    assert buy(client,h,user).status_code==409
    funds(conn,user,200)
    assert buy(client,h,user,price=1).status_code==409
    assert buy(client,h,user,catalog_sha256='0'*64).status_code==409
    for item in ('frame-gold','frame-committed','skin-light','not-an-item'):
        assert buy(client,h,user,item=item).status_code==422
    conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,note) VALUES(%s,%s,'adjustment',36000,'Synthetic high XP')",(user,uuid4().hex))
    assert all(not i['available'] for i in client.get('/api/me/avatar?catalog_version=2',headers=h).json()['catalog'] if i.get('price_points'))
    from test_mobile_companion import connect
    headers,_=connect(client,actor,user)
    assert client.get('/api/me/avatar?catalog_version=2',headers=headers).status_code==200
    assert client.get('/api/me/identity',headers=headers).status_code==403
    assert buy(client,headers,user).status_code==403


def test_parallel_own_once_and_shared_wallet_lock(client,actor,database):
    user,h=learner(database,actor);conn=database[1];funds(conn,user,25)
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:buy(client,h,user),range(2)))
    assert all(r.status_code==200 for r in results) and sum(not r.json()['replayed'] for r in results)==1
    assert conn.execute("SELECT count(*) FROM reward_ledger WHERE user_id=%s AND kind='redemption'",(user,)).fetchone()[0]==1
    other,oh=learner(database,actor);funds(conn,other,50)
    def action(which):
        return buy(client,oh,other,item='bg-twilight',price=50) if which else client.post('/api/rewards/streak-shield',headers=oh,json={})
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(action,[0,1]))
    assert sorted(r.status_code for r in results)==[200,409]
    assert conn.execute('SELECT sum(points) FROM reward_ledger WHERE user_id=%s',(other,)).fetchone()[0]>=0


def test_failed_audit_rolls_back_entire_purchase(client,actor,database):
    user,h=learner(database,actor);conn=database[1];funds(conn,user,50)
    name='synthetic_shop_failure_'+uuid4().hex[:8]
    conn.execute(sql.SQL("CREATE FUNCTION {}() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'Synthetic audit failure'; END $$").format(sql.Identifier(name)))
    conn.execute(sql.SQL("CREATE TRIGGER {} BEFORE INSERT ON avatar_events FOR EACH ROW WHEN (NEW.user_id={}) EXECUTE FUNCTION {}()").format(sql.Identifier(name),sql.Literal(user),sql.Identifier(name)))
    try:
        with pytest.raises(Exception,match='Synthetic audit failure'):buy(client,h,user)
        assert conn.execute('SELECT sum(points) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()[0]==50
        assert conn.execute('SELECT count(*) FROM user_avatar_items WHERE user_id=%s',(user,)).fetchone()[0]==0
        assert conn.execute('SELECT avatar_version FROM users WHERE id=%s',(user,)).fetchone()[0]==0
    finally:
        conn.execute(sql.SQL('DROP TRIGGER {} ON avatar_events').format(sql.Identifier(name)))
        conn.execute(sql.SQL('DROP FUNCTION {}()').format(sql.Identifier(name)))


def test_purchase_diagnostics_reconcile_and_detect_orphans_without_repairs(client,actor,database):
    from app.services import cosmetic_shop
    from test_learning_loop import run
    user,h=learner(database,actor);conn=database[1];funds(conn,user,50)
    assert buy(client,h,user).status_code==200
    assert all(n==0 for n in run(client,cosmetic_shop.diagnostics).values())
    conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,points,note) VALUES(%s,%s,'redemption',-1,'Synthetic orphan receipt')",(user,'cosmetic:'+user+':orphan-fixture'))
    count=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    checks=run(client,cosmetic_shop.diagnostics)
    assert checks=={'cosmetic_ledger_mismatches':1,'cosmetic_audit_mismatches':0,'duplicate_cosmetic_purchases':0}
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==count
    assert client.get('/api/admin/bank/reward-diagnostics',headers=h).status_code==403
    owner=actor('owner');result=client.get('/api/admin/bank/reward-diagnostics',headers=owner).json()
    assert result['cosmetic_ledger_mismatches']==1
