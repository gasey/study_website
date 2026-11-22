"""Deletion holds and original-key recovery, using synthetic identities only."""
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

from cryptography.fernet import Fernet
from fastapi import HTTPException
import psycopg
import pytest

from app.config import settings
from app.services import account_identity, mfa
from test_account_reopen import real_role  # noqa: F401 — shared provider-free role fixture
from test_account_study_history_retention import closed_user
from test_learning_workflows import learner


@pytest.fixture(autouse=True)
def synthetic_catalog(client):
    """Seed the shared synthetic question through the normal isolated fixture."""
    yield


@pytest.mark.parametrize('code', ['legal', 'dispute', 'security', 'manual_review'])
def test_each_active_hold_blocks_then_release_allows_cleanup(database, code):
    conn = database[1]
    with conn.transaction(force_rollback=True):
        user = closed_user(conn)
        attempt = conn.execute("INSERT INTO attempts(user_id,canonical_id,correct,context) VALUES(%s,'cq_test',false,'practice') RETURNING id", (user,)).fetchone()[0]
        conn.execute('INSERT INTO account_study_history_holds(user_id,hold_code) VALUES(%s,%s)', (user, code))
        conn.execute('SET LOCAL ROLE mpsc')
        assert conn.execute('SELECT sweep_expired_study_history(20,200)').fetchone()[0]['accounts_scanned'] == 0
        assert conn.execute('SELECT id FROM attempts WHERE id=%s', (attempt,)).fetchone()
        conn.execute('RESET ROLE')
        conn.execute('UPDATE account_study_history_holds SET released_at=clock_timestamp() WHERE user_id=%s', (user,))
        conn.execute('SET LOCAL ROLE mpsc')
        assert conn.execute('SELECT sweep_expired_study_history(20,200)').fetchone()[0]['accounts_completed'] == 1
        assert not conn.execute('SELECT id FROM attempts WHERE id=%s', (attempt,)).fetchone()
        # Completion remains idempotent and emits one minimal receipt.
        assert conn.execute('SELECT sweep_expired_study_history(20,200)').fetchone()[0]['accounts_completed'] == 0
        assert conn.execute("SELECT count(*) FROM account_security_events WHERE user_id=%s AND action='closed_study_history_purged'", (user,)).fetchone()[0] == 1


def test_expired_hold_does_not_override_another_active_hold(database):
    conn = database[1]
    with conn.transaction(force_rollback=True):
        user = closed_user(conn)
        conn.execute("INSERT INTO account_study_history_holds(user_id,hold_code,created_at,expires_at) VALUES(%s,'dispute',now()-interval '2 days',now()-interval '1 day')", (user,))
        conn.execute("INSERT INTO account_study_history_holds(user_id,hold_code) VALUES(%s,'legal')", (user,))
        conn.execute('SET LOCAL ROLE mpsc')
        assert conn.execute('SELECT sweep_expired_study_history(20,200)').fetchone()[0]['accounts_scanned'] == 0
        conn.execute('RESET ROLE')
        conn.execute("UPDATE account_study_history_holds SET released_at=clock_timestamp() WHERE user_id=%s AND hold_code='legal'", (user,))
        conn.execute('SET LOCAL ROLE mpsc')
        assert conn.execute('SELECT sweep_expired_study_history(20,200)').fetchone()[0]['accounts_completed'] == 1


def test_grace_period_is_enforced_before_cleanup(database):
    conn = database[1]
    with conn.transaction(force_rollback=True):
        user = closed_user(conn, days=29)
        conn.execute('SET LOCAL ROLE mpsc')
        assert conn.execute('SELECT sweep_expired_study_history(20,200)').fetchone()[0]['accounts_scanned'] == 0
        assert conn.execute('SELECT study_history_purged_at FROM users WHERE id=%s', (user,)).fetchone() == (None,)


@pytest.mark.parametrize('statement', [
    'SELECT * FROM account_study_history_holds',
    "INSERT INTO account_study_history_holds(user_id,hold_code) VALUES('owner','legal')",
    'UPDATE account_study_history_holds SET released_at=clock_timestamp()',
    'DELETE FROM account_study_history_holds',
])
def test_application_role_cannot_inspect_or_mutate_holds(database, statement):
    with database[1].transaction(force_rollback=True):
        database[1].execute('SET LOCAL ROLE mpsc')
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            with database[1].transaction():
                database[1].execute(statement)


def test_spoofed_purge_context_cannot_bypass_immutable_receipts(database):
    conn = database[1]
    with conn.transaction(force_rollback=True):
        user = closed_user(conn)
        attempt = conn.execute("INSERT INTO attempts(user_id,canonical_id,correct,context) VALUES(%s,'cq_test',false,'practice') RETURNING id", (user,)).fetchone()[0]
        conn.execute("INSERT INTO practice_request_receipts(user_id,request_key,request_hash,attempt_id,response) VALUES(%s,'proof','synthetic',%s,'{}')", (user, attempt))
        conn.execute('SET LOCAL ROLE mpsc')
        conn.execute("SELECT set_config('finna.study_history_purge_user',%s,true)", (user,))
        with pytest.raises(psycopg.Error):
            with conn.transaction():
                conn.execute('DELETE FROM practice_request_receipts WHERE user_id=%s', (user,))
        assert conn.execute('SELECT count(*) FROM practice_request_receipts WHERE user_id=%s', (user,)).fetchone()[0] == 1


@pytest.mark.parametrize('missing', ['', 'not-a-fernet-key'])
def test_missing_or_invalid_key_rejects_encryption(monkeypatch, missing):
    monkeypatch.setattr(settings, 'mfa_encryption_key', missing)
    with pytest.raises(HTTPException) as failure:
        mfa.encrypt('synthetic-user', 'synthetic-payload')
    assert failure.value.status_code == 503


def test_wrong_key_and_wrong_account_cannot_decrypt(monkeypatch):
    original = settings.mfa_encryption_key
    cipher = mfa.encrypt('synthetic-user', 'synthetic-payload')
    with pytest.raises(HTTPException):
        mfa.decrypt('another-user', cipher)
    monkeypatch.setattr(settings, 'mfa_encryption_key', Fernet.generate_key().decode())
    with pytest.raises(HTTPException):
        mfa.decrypt('synthetic-user', cipher)
    monkeypatch.setattr(settings, 'mfa_encryption_key', original)
    assert mfa.decrypt('synthetic-user', cipher) == 'synthetic-payload'


def test_backed_up_original_key_recovers_all_cipher_purposes_in_fresh_process(monkeypatch, tmp_path):
    original = settings.mfa_encryption_key
    user = 'synthetic-' + uuid4().hex
    email = 'recovery@example.test'
    values = ['SYNTHETICTOTPSEED', 'synthetic-mail-token', json.dumps({'email': email})]
    envelope = {'user': user, 'values': [mfa.encrypt(user, value) for value in values],
                'expected': values, 'email': email, 'email_hash': account_identity.closure_email_hash(email)}
    key_file = tmp_path / 'original.key'
    key_file.write_text(original)
    key_file.chmod(0o600)
    # The child restores a private key file, with no key in argv or output.
    child = '''import json,sys
from pathlib import Path
from app.config import settings
from app.services import mfa,account_identity
settings.mfa_encryption_key=Path(sys.argv[1]).read_text()
x=json.load(sys.stdin)
assert [mfa.decrypt(x['user'],v) for v in x['values']]==x['expected']
assert account_identity.closure_email_hash(x['email'])==x['email_hash']
print('original-key-recovery-passed')
'''
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1]))
    env.pop('MFA_ENCRYPTION_KEY', None)
    recovered = subprocess.run([sys.executable, '-c', child, str(key_file)], input=json.dumps(envelope),
                               capture_output=True, text=True, env=env, timeout=15)
    assert recovered.returncode == 0
    assert recovered.stdout.strip() == 'original-key-recovery-passed'
    assert original not in recovered.stdout + recovered.stderr
    key_file.unlink()


def test_reopen_wrong_key_leaves_link_and_identity_intact_then_original_key_succeeds(client, actor, database, monkeypatch):
    conn = database[1]
    user, headers = learner(database, actor)
    email = user + '@example.test'
    original = settings.mfa_encryption_key
    conn.execute('UPDATE users SET email_verified_at=now() WHERE id=%s', (user,))
    assert client.post('/api/me/account-close', headers=headers, json={
        'user_id': user, 'expected_version': 0, 'confirmation': 'DELETE MY ACCOUNT'}).status_code == 200
    origin = {'Origin': 'https://study.hawayu.in'}
    assert client.post('/api/auth/recovery/request', headers=origin, json={'email': email}).status_code == 200
    cipher = conn.execute("SELECT token_cipher FROM account_mail_outbox WHERE user_id=%s AND purpose='reopen'", (user,)).fetchone()[0]
    raw = mfa.decrypt(user, cipher)
    escrow = conn.execute('SELECT email_hash,identity_cipher FROM account_closure_recovery WHERE user_id=%s', (user,)).fetchone()
    monkeypatch.setattr(settings, 'mfa_encryption_key', Fernet.generate_key().decode())
    assert account_identity.closure_email_hash(email) != escrow[0]
    failed = client.post('/api/auth/reopen/complete', headers=origin, json={'token': raw, 'password': 'NewPassword12345!'})
    assert failed.status_code == 503
    assert conn.execute('SELECT email_hash,identity_cipher FROM account_closure_recovery WHERE user_id=%s', (user,)).fetchone() == escrow
    assert conn.execute('SELECT consumed_at FROM account_email_tokens WHERE token_hash=%s', (account_identity.digest(raw),)).fetchone() == (None,)
    assert conn.execute('SELECT closed_at IS NOT NULL,email FROM users WHERE id=%s', (user,)).fetchone() == (True, None)
    monkeypatch.setattr(settings, 'mfa_encryption_key', original)
    assert client.post('/api/auth/reopen/complete', headers=origin, json={'token': raw, 'password': 'NewPassword12345!'}).status_code == 200
    assert conn.execute('SELECT closed_at,email FROM users WHERE id=%s', (user,)).fetchone() == (None, email)
    assert conn.execute('SELECT count(*) FROM auth_sessions WHERE user_id=%s AND revoked_at IS NULL', (user,)).fetchone()[0] == 0
