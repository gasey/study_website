"""Isolated PostgreSQL tests for 0134 private-preference cleanup and audited 18+ corrections."""
from contextlib import asynccontextmanager
from uuid import uuid4

import psycopg
import pytest

from app.config import settings
from app.db import cursor
from app.routers import account_privacy as privacy
from app.services import account_retention, audience
from test_account_study_history_retention import run
from test_learning_workflows import learner

PREF_TABLES = ('user_calendar_preferences', 'inbox_preferences', 'inbox_desk_reads', 'game_preferences')


@pytest.fixture
def pref_sample(client, database):
    conn = database[1]
    with conn.transaction(force_rollback=True):
        users = ['pref-' + uuid4().hex for _ in range(2)]
        for u in users:
            conn.execute('INSERT INTO users(id,handle) VALUES(%s,%s)', (u, u))
        desk_ids = ['pref-desk-' + uuid4().hex for _ in range(2)]
        for d in desk_ids:
            conn.execute("INSERT INTO study_desks(id,owner_id,name) VALUES(%s,%s,'Pref Desk')", (d, users[1]))
        for u in users:
            conn.execute('INSERT INTO user_calendar_preferences(user_id,reminders) VALUES(%s,true)', (u,))
            conn.execute("INSERT INTO inbox_preferences(user_id,in_app) VALUES(%s,'{\"discussions\":false}'::jsonb)", (u,))
            for d in desk_ids:
                conn.execute('INSERT INTO inbox_desk_reads(user_id,desk_id,last_message_id) VALUES(%s,%s,5)', (u, d))
            conn.execute("INSERT INTO game_preferences(user_id,selection) VALUES(%s,'{\"mode\":\"rapid\"}'::jsonb)", (u,))
        # Safety/moderation block row must survive preference cleanup.
        conn.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)', (users[0], users[1]))
        yield conn, users, desk_ids


def _close_pref_user(conn, user, *, days=31, base_done=True, private_study_done=True):
    conn.execute(
        """UPDATE users
           SET closed_at=clock_timestamp()-(%s||' days')::interval,
               handle=%s,
               contribution_public=false,
               study_history_purged_at=CASE WHEN %s THEN clock_timestamp() ELSE NULL END,
               private_study_purged_at=CASE WHEN %s THEN clock_timestamp() ELSE NULL END
           WHERE id=%s""",
        (days, 'deleted-' + uuid4().hex, base_done, private_study_done, user),
    )


def _sweep_prefs(conn, accounts=20, batch=200):
    with conn.transaction():
        conn.execute('SET LOCAL ROLE mpsc')
        result = conn.execute('SELECT sweep_expired_private_preferences(%s,%s)', (accounts, batch)).fetchone()[0]
        conn.execute('RESET ROLE')
        return result


def _pref_counts(conn, user):
    return {t: conn.execute('SELECT count(*) FROM ' + t + ' WHERE user_id=%s', (user,)).fetchone()[0] for t in PREF_TABLES}


def test_only_expired_owners_preferences_removed_and_blocks_survive(pref_sample):
    conn, (user, other), _ = pref_sample
    other_before = _pref_counts(conn, other)
    _close_pref_user(conn, user)
    res = _sweep_prefs(conn)
    assert res == {'accounts_scanned': 1, 'accounts_completed': 1, 'rows_removed': 5}
    assert not any(_pref_counts(conn, user).values())
    assert _pref_counts(conn, other) == other_before
    # Safety block must NOT be deleted.
    assert conn.execute('SELECT count(*) FROM creator_blocks WHERE user_id=%s AND blocked_id=%s', (user, other)).fetchone()[0] == 1
    assert conn.execute('SELECT private_preferences_purged_at IS NOT NULL FROM users WHERE id=%s', (user,)).fetchone()[0]
    event = conn.execute("SELECT detail FROM account_security_events WHERE user_id=%s AND action='closed_private_preferences_purged'", (user,)).fetchone()
    assert event == ({'policy': 'private-preferences-v1'},)
    # Idempotent rerun scans nothing.
    assert _sweep_prefs(conn) == {'accounts_scanned': 0, 'accounts_completed': 0, 'rows_removed': 0}


@pytest.mark.parametrize('days,base_done,priv_done', [
    (29, True, True),
    (31, False, True),
    (31, True, False),
    (31, False, False),
])
def test_prerequisites_block_preference_cleanup(pref_sample, days, base_done, priv_done):
    conn, (user, _), _ = pref_sample
    _close_pref_user(conn, user, days=days, base_done=base_done, private_study_done=priv_done)
    assert _sweep_prefs(conn) == {'accounts_scanned': 0, 'accounts_completed': 0, 'rows_removed': 0}
    assert sum(_pref_counts(conn, user).values()) == 5


@pytest.mark.parametrize('hold_code', ['legal', 'dispute', 'security', 'manual_review'])
def test_holds_pause_and_release_resumes_preference_cleanup(pref_sample, hold_code):
    conn, (user, _), _ = pref_sample
    _close_pref_user(conn, user)
    conn.execute("INSERT INTO account_study_history_holds(user_id,hold_code) VALUES(%s,%s)", (user, hold_code))
    assert _sweep_prefs(conn) == {'accounts_scanned': 0, 'accounts_completed': 0, 'rows_removed': 0}
    conn.execute("UPDATE account_study_history_holds SET released_at=clock_timestamp() WHERE user_id=%s", (user,))
    assert _sweep_prefs(conn)['accounts_completed'] == 1
    assert not any(_pref_counts(conn, user).values())


def test_batched_preference_cleanup_resumes_cleanly(pref_sample):
    conn, (user, _), _ = pref_sample
    _close_pref_user(conn, user)
    first = _sweep_prefs(conn, accounts=1, batch=1)
    assert first['accounts_scanned'] == 1 and first['accounts_completed'] == 0 and first['rows_removed'] == 4
    assert conn.execute('SELECT private_preferences_purged_at FROM users WHERE id=%s', (user,)).fetchone()[0] is None
    second = _sweep_prefs(conn, accounts=1, batch=1)
    assert second == {'accounts_scanned': 1, 'accounts_completed': 1, 'rows_removed': 1}
    assert conn.execute('SELECT private_preferences_purged_at IS NOT NULL FROM users WHERE id=%s', (user,)).fetchone()[0]


@pytest.mark.parametrize('accounts,batch', [(0, 10), (21, 10), (1, 0), (1, 1001), (None, 10), (1, None)])
def test_invalid_preference_sweep_bounds_rejected(pref_sample, accounts, batch):
    conn, _, _ = pref_sample
    with pytest.raises(psycopg.errors.RaiseException):
        _sweep_prefs(conn, accounts=accounts, batch=batch)


def test_closed_account_cannot_recreate_preferences_and_mpsc_cannot_forge_marker(pref_sample):
    conn, (user, _), (desk_id, _) = pref_sample
    _close_pref_user(conn, user)
    _sweep_prefs(conn)
    for sql_stmt, params in [
        ('INSERT INTO user_calendar_preferences(user_id,reminders) VALUES(%s,true)', (user,)),
        ("INSERT INTO inbox_preferences(user_id,in_app) VALUES(%s,'{}'::jsonb)", (user,)),
        ('INSERT INTO inbox_desk_reads(user_id,desk_id,last_message_id) VALUES(%s,%s,1)', (user, desk_id)),
        ("INSERT INTO game_preferences(user_id,selection) VALUES(%s,'{}'::jsonb)", (user,)),
    ]:
        with pytest.raises(psycopg.errors.RaiseException):
            with conn.transaction():
                conn.execute('SET LOCAL ROLE mpsc')
                conn.execute(sql_stmt, params)
    # App role cannot forge private_preferences_purged_at on UPDATE or INSERT.
    with pytest.raises(psycopg.errors.RaiseException):
        with conn.transaction():
            conn.execute('SET LOCAL ROLE mpsc')
            conn.execute("UPDATE users SET private_preferences_purged_at=NULL WHERE id=%s", (user,))
    with pytest.raises(psycopg.errors.RaiseException):
        with conn.transaction():
            conn.execute('SET LOCAL ROLE mpsc')
            conn.execute("INSERT INTO users(id,handle,private_preferences_purged_at) VALUES(%s,%s,now())", ('forge-' + uuid4().hex, 'forge-' + uuid4().hex))


def test_worker_requires_all_three_default_off_flags(client, database, monkeypatch):
    assert settings.study_history_retention_enabled is False
    assert settings.private_study_retention_enabled is False
    assert settings.private_preferences_retention_enabled is False
    # Enabling only private_preferences (or private_study + private_preferences without base) stays disabled.
    monkeypatch.setattr(settings, 'study_history_retention_enabled', False)
    monkeypatch.setattr(settings, 'private_study_retention_enabled', True)
    monkeypatch.setattr(settings, 'private_preferences_retention_enabled', True)
    counts = run(client, account_retention.sweep)
    assert counts['study_history'] == 'disabled'
    assert counts['private_study'] == 'disabled'
    assert counts['private_preferences'] == 'disabled'

    monkeypatch.setattr(settings, 'study_history_retention_enabled', True)
    monkeypatch.setattr(settings, 'private_study_retention_enabled', False)
    monkeypatch.setattr(settings, 'private_preferences_retention_enabled', True)
    counts = run(client, account_retention.sweep)
    assert counts['private_study'] == 'disabled'
    assert counts['private_preferences'] == 'disabled'

    monkeypatch.setattr(settings, 'private_study_retention_enabled', True)
    monkeypatch.setattr(settings, 'private_preferences_retention_enabled', True)
    counts = run(client, account_retention.sweep)
    assert isinstance(counts['private_preferences'], dict) and 'accounts_scanned' in counts['private_preferences']


# ---- 18+ Audited Age-Declaration Correction Tests ----

@pytest.fixture
def mpsc_privacy_role(monkeypatch):
    @asynccontextmanager
    async def role_cursor():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            yield cur
    monkeypatch.setattr(privacy, 'cursor', role_cursor)
    monkeypatch.setattr(audience, 'cursor', role_cursor)


def test_self_declarations_and_owner_correction_are_audited_and_immutable(client, actor, database, monkeypatch, mpsc_privacy_role):
    monkeypatch.setattr(settings, 'audience_gate_enabled', True)
    conn = database[1]
    user, uh = learner(database, actor)

    # 1. Self-declare under18 -> logged in account_audience_events.
    r = client.post('/api/account-privacy/declare', headers=uh, json={'category': 'under18', 'user_id': user, 'expected_version': 0})
    assert r.status_code == 200
    ev = conn.execute("SELECT previous_category,new_category,reason_code,request_id FROM account_audience_events WHERE user_id=%s ORDER BY id", (user,)).fetchall()
    assert ev == [(None, 'under18', 'self_declaration', None)]

    # 2. User opens a 'correction' privacy request; completing it alone does NOT upgrade audience.
    req = client.post('/api/account-privacy/requests', headers=uh, json={'user_id': user, 'kind': 'correction', 'request_key': uuid4().hex})
    assert req.status_code == 200
    rid = req.json()['id']

    # Non-owner cannot call admin correction.
    assert client.post('/api/account-privacy/admin/audience-correction', headers=uh, json={
        'user_id': user, 'request_id': rid, 'expected_audience_version': 1, 'new_category': 'adult',
    }).status_code == 403

    # Owner cannot apply correction while request is still 'received' (must be 'in_review').
    oh = actor('owner')
    assert client.post('/api/account-privacy/admin/audience-correction', headers=oh, json={
        'user_id': user, 'request_id': rid, 'expected_audience_version': 1, 'new_category': 'adult',
    }).status_code == 409

    # Move request to in_review.
    assert client.post('/api/account-privacy/admin/requests/' + rid, headers=oh, json={
        'user_id': user, 'expected_version': 1, 'state': 'in_review',
    }).status_code == 200

    # MFA enforcement blocks unverified owner.
    monkeypatch.setattr(settings, 'mfa_enforce_staff', True)
    assert client.post('/api/account-privacy/admin/audience-correction', headers=oh, json={
        'user_id': user, 'request_id': rid, 'expected_audience_version': 1, 'new_category': 'adult',
    }).status_code == 403
    monkeypatch.setattr(settings, 'mfa_enforce_staff', False)

    # Stale audience version fails with 409.
    assert client.post('/api/account-privacy/admin/audience-correction', headers=oh, json={
        'user_id': user, 'request_id': rid, 'expected_audience_version': 0, 'new_category': 'adult',
    }).status_code == 409

    # Valid owner correction under18 -> adult succeeds and appends immutable event.
    ok = client.post('/api/account-privacy/admin/audience-correction', headers=oh, json={
        'user_id': user, 'request_id': rid, 'expected_audience_version': 1, 'new_category': 'adult',
    })
    assert ok.status_code == 200 and ok.json() == {'user_id': user, 'category': 'adult', 'version': 2, 'request_id': rid}
    ev = conn.execute("SELECT previous_category,new_category,reason_code,request_id FROM account_audience_events WHERE user_id=%s ORDER BY id", (user,)).fetchall()
    assert ev == [
        (None, 'under18', 'self_declaration', None),
        ('under18', 'adult', 'owner_verified_correction', rid),
    ]
    # Audit events are strictly immutable (UPDATE/DELETE rejected).
    with pytest.raises(psycopg.errors.RaiseException):
        with conn.transaction():
            conn.execute('UPDATE account_audience_events SET new_category=%s WHERE user_id=%s', ('under18', user))
    with pytest.raises(psycopg.errors.RaiseException):
        with conn.transaction():
            conn.execute('DELETE FROM account_audience_events WHERE user_id=%s', (user,))


def test_owner_correction_forbids_grandfathering_unknown_account_as_adult(client, actor, database, monkeypatch, mpsc_privacy_role):
    monkeypatch.setattr(settings, 'audience_gate_enabled', True)
    user, uh = learner(database, actor)
    rid = client.post('/api/account-privacy/requests', headers=uh, json={'user_id': user, 'kind': 'correction', 'request_key': uuid4().hex}).json()['id']
    oh = actor('owner')
    assert client.post('/api/account-privacy/admin/requests/' + rid, headers=oh, json={'user_id': user, 'expected_version': 1, 'state': 'in_review'}).status_code == 200

    # Unknown account (no row in account_audience) CANNOT be grandfathered as adult by owner.
    res = client.post('/api/account-privacy/admin/audience-correction', headers=oh, json={
        'user_id': user, 'request_id': rid, 'expected_audience_version': 0, 'new_category': 'adult',
    })
    assert res.status_code == 409

    # However, an owner CAN restrict an undeclared/adult account to under18, revoking its sessions/channels.
    conn = database[1]
    conn.execute('INSERT INTO user_calendar_preferences(user_id,reminders) VALUES(%s,true)', (user,))
    res2 = client.post('/api/account-privacy/admin/audience-correction', headers=oh, json={
        'user_id': user, 'request_id': rid, 'expected_audience_version': 0, 'new_category': 'under18',
    })
    assert res2.status_code == 200 and res2.json()['category'] == 'under18'
    assert conn.execute('SELECT reminders FROM user_calendar_preferences WHERE user_id=%s', (user,)).fetchone()[0] is False
    assert conn.execute('SELECT count(*) FROM auth_sessions WHERE user_id=%s AND revoked_at IS NULL', (user,)).fetchone()[0] == 0
