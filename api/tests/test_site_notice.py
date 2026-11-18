from datetime import datetime,timedelta,timezone
from uuid import uuid4
import pytest
from app.config import settings
from app.db import cursor
from app.routers.site_notice import Notice
from app.services import site_notice

BASE='/api/admin/ops/notice'

@pytest.fixture(autouse=True)
def policy(monkeypatch):
    monkeypatch.setattr(settings,'mfa_enforce_staff',False)
    monkeypatch.setattr(settings,'staff_mfa_exempt_user_ids','')


def test_public_blank_and_plain_text_notice_with_no_private_identity(client,actor,database):
    client.cookies.clear();response=client.get('/api/site-notice');assert response.status_code==200,response.text
    assert response.json()=={'message':'','expires_at':None,'version':1}
    assert response.headers['cache-control']=='no-store'
    h=actor('owner');expiry=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()
    r=client.post(BASE,headers=h,json={'message':'  Maintenance tonight <script>plaintext</script>  ','expires_at':expiry,'expected_version':1});assert r.status_code==200,r.text
    client.cookies.clear();public=client.get('/api/site-notice').json()
    assert public['message']=='Maintenance tonight <script>plaintext</script>' and public['version']==2
    assert datetime.fromisoformat(public['expires_at'])==datetime.fromisoformat(expiry)
    assert 'updated_by' not in public and 'updated_at' not in public
    conn=database[1];event=conn.execute("SELECT user_id,detail FROM account_security_events WHERE action='owner_site_notice_set' ORDER BY id DESC LIMIT 1").fetchone()
    assert event[0]=='owner' and event[1]['before']['version']==1 and event[1]['after']['version']==2
    assert event[1]['after']['message']==public['message']


def test_owner_mfa_csrf_revocation_and_native_boundaries(client,actor,database,monkeypatch):
    for user in ('outsider','author','reviewer1'):
        h=actor(user);assert client.get(BASE).status_code==403
        assert client.post(BASE,headers=h,json={'message':'Test','expected_version':2}).status_code==403
    h=actor('owner');assert client.post(BASE,json={'message':'Test','expected_version':2}).status_code==403
    monkeypatch.setattr(settings,'mfa_enforce_staff',True)
    assert client.get(BASE).status_code==403
    assert client.post(BASE,headers=h,json={'message':'Test','expected_version':2}).status_code==403
    monkeypatch.setattr(settings,'staff_mfa_exempt_user_ids','other-owner')
    assert client.get(BASE).status_code==403
    monkeypatch.setattr(settings,'staff_mfa_exempt_user_ids','owner')
    assert client.get(BASE).status_code==200
    monkeypatch.setattr(settings,'staff_mfa_exempt_user_ids','')
    database[1].execute("UPDATE auth_sessions SET mfa_verified_at=now() WHERE user_id='owner'")
    assert client.get(BASE).status_code==200
    from test_mobile_companion import connect
    monkeypatch.setattr(settings,'mfa_enforce_staff',False)
    headers,_=connect(client,actor,'owner');assert client.get(BASE,headers=headers).status_code==403


def test_stale_update_expiry_clear_and_validation(client,actor,database):
    h=actor('owner');snapshot=client.get(BASE).json();version=snapshot['version']
    assert client.post(BASE,headers=h,json={'message':'Stale overwrite','expected_version':version+999}).status_code==409
    for body in ({'message':'x'*501,'expected_version':version},{'message':'bad\x00text','expected_version':version},
                 {'message':'No timezone','expires_at':'2030-01-01T00:00','expected_version':version},
                 {'message':'No write freeze','maintenance_mode':True,'expected_version':version},
                 {'message':'Bad version','expected_version':True}):
        assert client.post(BASE,headers=h,json=body).status_code==422
    assert client.post(BASE,headers=h,json={'message':'Past','expires_at':(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat(),'expected_version':version}).status_code==422
    # A stored expired notice stops rendering, while its owner can still see it.
    database[1].execute("UPDATE site_notice SET expires_at=now()-interval '1 second' WHERE singleton")
    assert client.get('/api/site-notice').json()['message']==''
    assert client.get(BASE).json()['message']==snapshot['message']
    r=client.post(BASE,headers=h,json={'message':'','expires_at':None,'expected_version':version});assert r.status_code==200,r.text
    assert r.json()['message']=='' and r.json()['expires_at'] is None and r.json()['version']==version+1


def test_real_role_setting_and_audit_commit_are_atomic(client,actor,database):
    async def scenario():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            before=await site_notice.setting(cur)
        try:
            async with cursor() as cur:
                await cur.execute('SET LOCAL ROLE mpsc')
                await site_notice.save(cur,'owner',Notice(message='Rolled back synthetic notice',expected_version=before['version']))
                raise RuntimeError('Synthetic rollback')
        except RuntimeError:pass
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            assert await site_notice.setting(cur)==before
    before=database[1].execute("SELECT count(*) FROM account_security_events WHERE action='owner_site_notice_set'").fetchone()[0]
    client.portal.call(scenario)
    assert database[1].execute("SELECT count(*) FROM account_security_events WHERE action='owner_site_notice_set'").fetchone()[0]==before


def test_notice_outage_is_an_error_instead_of_invented_empty_setting(client,actor,monkeypatch):
    actor('owner')
    async def fail(*args):raise RuntimeError('Synthetic notice outage')
    monkeypatch.setattr(site_notice,'setting',fail)
    with pytest.raises(RuntimeError,match='Synthetic notice outage'):client.get(BASE)
