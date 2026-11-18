"""Compatibility recovery retains every irreversible V.5 privacy boundary."""
from contextlib import asynccontextmanager
import importlib.util
import json
import os
from pathlib import Path
from uuid import uuid4
import psycopg
import pytest
from app.db import cursor
from app.routers import account_tools, avatars, calendar_owned, creators, profile_identity, search
from app.services import v5_release
from test_learning_workflows import learner
from test_profile_cosmetics import buy, edit, funds
from test_owned_calendar import save

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('v5_recovery', ROOT/'scripts/recover-finnaplan-v5.py')
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)


@pytest.fixture(autouse=True)
def application_role(monkeypatch):
    @asynccontextmanager
    async def scoped_cursor():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            yield cur
    for module in (account_tools, avatars, calendar_owned, creators, profile_identity, search):
        monkeypatch.setattr(module, 'cursor', scoped_cursor)


@pytest.mark.parametrize('content', [None, '{invalid', '[]', '{"version":true,"writes_enabled":true}',
                                   '{"version":1,"writes_enabled":1}', recovery.RECOVERY.decode()])
def test_missing_or_invalid_release_state_fails_closed(tmp_path, monkeypatch, content):
    target = tmp_path/'state.json'
    if content is not None:
        target.write_text(content)
    monkeypatch.setattr(v5_release, 'STATE_PATH', target)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as denied:
        v5_release.require_writes()
    assert denied.value.status_code == 503


def paired_fixture(tmp_path):
    backup, api, public = (tmp_path/n for n in ('backup', 'api', 'public'))
    (api/'app/data').mkdir(parents=True)
    (backup/'public').mkdir(parents=True)
    public.mkdir()
    (api/recovery.STATE).write_bytes(recovery.ACTIVE)
    (api/'app/privacy.py').write_text('Retain current safe readers and validators')
    (api/'unrelated.py').write_text('Unrelated release artifact')
    (public/'index.html').write_text('New web')
    (public/'new.js').write_text('New chunk')
    (backup/'public/index.html').write_text('Prior web')
    scope = {'candidate': {'api': {name: recovery.digest(api/name) for name in
              (recovery.STATE, 'app/privacy.py')}, 'web': recovery.inventory(public)},
             'web_preimages': recovery.inventory(backup/'public')}
    return backup, api, public, scope


def test_recovery_pairs_prior_static_with_quarantine_and_rejects_newer_changes(tmp_path):
    backup, api, public, scope = paired_fixture(tmp_path)
    original = (api/'app/privacy.py').read_bytes()
    (public/'other-release.js').write_text('Later release')
    with pytest.raises(AssertionError, match='Newer static'):
        recovery.recover_files(backup, api, public, scope)
    assert (api/recovery.STATE).read_bytes() == recovery.ACTIVE
    (public/'other-release.js').unlink()
    (api/'app/privacy.py').write_text('Later API')
    with pytest.raises(AssertionError, match='Newer or missing API'):
        recovery.recover_files(backup, api, public, scope)
    (api/'app/privacy.py').write_bytes(original)
    recovery.recover_files(backup, api, public, scope)
    assert (api/recovery.STATE).read_bytes() == recovery.RECOVERY
    assert (api/'app/privacy.py').read_bytes() == original
    assert (api/'unrelated.py').read_text() == 'Unrelated release artifact'
    assert (public/'index.html').read_text() == 'Prior web' and not (public/'new.js').exists()
    recovery.recover_files(backup, api, public, scope)  # Safe retry after interruption.


def test_recovery_after_purchase_moderation_and_closure_preserves_history(client, actor, database, tmp_path, monkeypatch):
    conn = database[1]
    buyer, h = learner(database, actor)
    funds(conn, buyer, 100)
    assert buy(client, h, buyer).status_code == 200
    look = avatars.avatars.DEFAULT | {'top': 'Plum'}
    assert client.post('/api/me/avatar?catalog_version=2', headers=h,
                       json={'user_id': buyer, 'expected_version': 1, 'look': look}).status_code == 200
    marker = 'pending-bio-'+uuid4().hex[:8]
    assert edit(client, h, bio=marker).json()['bio_needs_approval']
    assert client.post('/api/creators/settings', headers=h, json={'public': True, 'bio': marker}).status_code == 200
    entry = str(uuid4())
    assert save(client, h, id=entry).status_code == 200
    feed = client.post('/api/me/calendar/feed/rotate', headers=h, json={'expected_version': 0}).json()['url']
    closed, ch = learner(database, actor)
    assert client.post('/api/me/account-close', headers=ch,
                       json={'user_id': closed, 'expected_version': 0, 'confirmation': 'DELETE MY ACCOUNT'}).status_code == 200
    redemption = uuid4().hex
    conn.execute("""INSERT INTO reward_redemptions(id,user_id,idempotency_key,catalog_id,catalog_version,points,starts_at,ends_at)
      VALUES(%s,%s,%s,'pro-month',1,1500,now(),now()+interval '30 days')""", (redemption, buyer, redemption))
    receipt = conn.execute('SELECT * FROM reward_redemptions WHERE id=%s', (redemption,)).fetchone()
    ledger = conn.execute('SELECT * FROM reward_ledger ORDER BY id').fetchall()
    guards = recovery.database_guards(conn)
    backup, api, public, scope = paired_fixture(tmp_path)
    recovery.recover_files(backup, api, public, scope)
    monkeypatch.setattr(v5_release, 'STATE_PATH', api/recovery.STATE)
    h = actor(buyer)
    for result in (
        buy(client, h, buyer, item='bg-twilight', price=50),
        edit(client, h, name='Paused edit'),
        save(client, h),
        client.post('/api/me/calendar/feed/rotate', headers=h, json={'expected_version': 1}),
        client.post('/api/me/avatar?catalog_version=2', headers=h,
                    json={'user_id': buyer, 'expected_version': 2, 'look': look}),
        client.post('/api/creators/settings', headers=h, json={'public': True, 'bio': marker+' edit'}),
        client.post('/api/me/account-close', headers=h,
                    json={'user_id': buyer, 'expected_version': 2, 'confirmation': 'DELETE MY ACCOUNT'}),
    ):
        assert result.status_code == 503, result.text
        assert result.headers['retry-after'] == '300'
    current = client.get('/api/me/avatar?catalog_version=2', headers=h).json()
    assert current['avatar'] == look and current['points'] == 75
    assert next(i for i in current['catalog'] if i['id'] == 'top-plum')['claimed']
    # Prior static/native clients still get a safe catalog and cannot clobber a
    # look they cannot render. The current moderation-aware search stays loaded.
    old = client.get('/api/me/avatar', headers=h).json()
    assert len(old['catalog']) == 26 and old['requires_web_editor']
    assert client.post('/api/me/avatar', headers=h,
                       json={'user_id': buyer, 'expected_version': 2, 'look': None}).status_code == 409
    observer, oh = learner(database, actor)
    assert client.get('/api/creators/'+buyer, headers=oh).json()['bio'] == ''
    assert client.get('/api/search', headers=oh, params={'q': marker, 'category': 'people'}).json()['groups'][0]['items'] == []
    h = actor(buyer)
    assert client.get('/api/me/data-export', headers=h, params={'user_id': buyer}).json()['account']['id'] == buyer
    assert client.post('/api/me/calendar/entries/'+entry+'/delete', headers=h, json={'expected_version': 1}).status_code == 200
    assert client.post('/api/me/calendar/feed/revoke', headers=h, json={'expected_version': 1}).status_code == 200
    assert client.get(feed).status_code == 404
    conn.execute("UPDATE users SET plan_code='pro',plan_status='active' WHERE id=%s", (closed,))
    assert not conn.execute('SELECT account_has_pro(%s)', (closed,)).fetchone()[0]
    with pytest.raises(psycopg.Error, match='Account is closed'):
        with conn.transaction():
            conn.execute('SET LOCAL ROLE mpsc')
            conn.execute('UPDATE auth_sessions SET revoked_at=NULL WHERE user_id=%s', (closed,))
    # A request authenticated before closure cannot recreate a shared desk or
    # restore membership/sharing after the closure transaction has committed.
    desk = uuid4().hex
    conn.execute("INSERT INTO study_desks(id,owner_id,name) VALUES(%s,%s,'Recovery fixture desk')", (desk, buyer))
    for query, params in (
        ("INSERT INTO study_desks(id,owner_id,name) VALUES(%s,%s,'Closed owner')", (uuid4().hex, closed)),
        ('INSERT INTO study_desk_members(desk_id,user_id) VALUES(%s,%s)', (desk, closed)),
    ):
        with pytest.raises(psycopg.Error, match='Account is closed'):
            with conn.transaction():
                conn.execute('SET LOCAL ROLE mpsc')
                conn.execute(query, params)
    assert conn.execute('SELECT * FROM reward_ledger ORDER BY id').fetchall() == ledger
    assert conn.execute('SELECT * FROM reward_redemptions WHERE id=%s', (redemption,)).fetchone() == receipt
    assert conn.execute('SELECT account_has_pro(%s)', (buyer,)).fetchone()[0]
    assert recovery.database_guards(conn) == guards
    assert client.post('/api/me/account-signout-all', headers=h, json={'user_id': buyer}).status_code == 200
    if target := os.environ.get('FINNA_V5_RECOVERY_REPORT'):
        Path(target).write_text(json.dumps({key: True for key in (
            'write_quarantine', 'paired_static_restore', 'purchased_items_preserved',
            'moderated_bios_private', 'closed_accounts_anonymous', 'entitlements_preserved',
            'database_guards_preserved')}, indent=2)+'\n')
