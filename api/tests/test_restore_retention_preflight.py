"""A restored database must not lose current holds or resurrect erased history."""
from contextlib import contextmanager
from contextlib import ExitStack
import importlib.util
import json
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql
import pytest

spec = importlib.util.spec_from_file_location('test_retention_preflight', Path(__file__).resolve().parents[2] / 'scripts/check-restore-retention.py')
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


@contextmanager
def copy(database):
    name = 'ism_review_test_' + uuid4().hex[:12]
    with psycopg.connect('dbname=postgres', autocommit=True) as admin:
        # The fixture reference connection must be idle for a template copy.
        database[1].close()
        admin.execute(sql.SQL('CREATE DATABASE {} TEMPLATE {}').format(sql.Identifier(name), sql.Identifier(database[0])))
        database[1] = psycopg.connect('dbname=' + database[0], autocommit=True)
        try:
            with psycopg.connect('dbname=' + name, autocommit=True) as conn:
                yield conn, 'dbname=' + name
        finally:
            admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))


@pytest.fixture
def reference(database_schema):
    # Each case uses an independent schema clone so the source fixture stays idle.
    name = 'ism_review_test_' + uuid4().hex[:12]
    with psycopg.connect('dbname=postgres', autocommit=True) as admin:
        admin.execute(sql.SQL('CREATE DATABASE {} TEMPLATE {}').format(sql.Identifier(name), sql.Identifier(database_schema)))
        conn = psycopg.connect('dbname=' + name, autocommit=True)
        # A mutable pair lets copy() reopen its own idle source connection.
        pair = [name, conn]
        try:
            user = 'synthetic-retention-user'
            conn.execute('INSERT INTO users(id,handle) VALUES(%s,%s)', (user, user))
            conn.execute("UPDATE users SET closed_at=now()-interval '31 days',handle='deleted-synthetic',contribution_public=false WHERE id=%s", (user,))
            conn.execute("INSERT INTO account_study_history_holds(user_id,hold_code,expires_at) VALUES(%s,'legal',now()+interval '1 day')", (user,))
            conn.execute("INSERT INTO account_closure_recovery(user_id,email_hash,identity_cipher,expires_at) VALUES(%s,%s,'synthetic-cipher',now()+interval '1 day')", (user, 'a' * 64))
            yield pair
        finally:
            pair[1].close()
            admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))


def test_equal_controls_pass_and_no_private_values_are_exported(reference):
    with copy(reference) as (_, dsn):
        result = preflight.compare('dbname=' + reference[0], dsn)
    assert result['status'] == 'checks_passed' and len(result['matched_control_tables']) == 3
    assert not result['promotion_authorized'] and not result['reference_currentness_verified']
    encoded = json.dumps(result)
    assert 'synthetic-retention-user' not in encoded and 'synthetic-cipher' not in encoded and 'a' * 64 not in encoded


@pytest.mark.parametrize('change', [
    'DELETE FROM account_study_history_holds',
    "UPDATE account_study_history_holds SET hold_code='security'",
    "UPDATE account_study_history_holds SET created_at=created_at-interval '1 hour'",
    "UPDATE account_study_history_holds SET expires_at=expires_at+interval '1 day'",
    'UPDATE account_study_history_holds SET expires_at=NULL',
    'UPDATE account_study_history_holds SET released_at=clock_timestamp()',
])
def test_missing_or_changed_hold_blocks_restore(reference, change):
    with copy(reference) as (conn, dsn):
        conn.execute(change)
        result = preflight.compare('dbname=' + reference[0], dsn)
    assert result['status'] == 'blocked'
    assert [x['table'] for x in result['control_mismatches']] == ['account_study_history_holds']


@pytest.mark.parametrize('change', [
    'UPDATE users SET closed_at=NULL',
    "UPDATE users SET closed_at=closed_at+interval '1 hour'",
    'UPDATE users SET study_history_purged_at=clock_timestamp()',
    'DELETE FROM account_closure_recovery',
    "UPDATE account_closure_recovery SET identity_cipher='different'",
    "UPDATE account_closure_recovery SET email_hash=repeat('b',64)",
    "UPDATE account_closure_recovery SET expires_at=expires_at-interval '1 hour'",
])
def test_changed_closure_purge_or_recovery_decision_blocks_restore(reference, change):
    with copy(reference) as (conn, dsn):
        # Model a genuinely different old snapshot, rather than invoking an
        # application's forbidden closed-identity update as the test setup.
        conn.execute('SET session_replication_role=replica')
        conn.execute(change)
        conn.execute('SET session_replication_role=origin')
        assert preflight.compare('dbname=' + reference[0], dsn)['status'] == 'blocked'


def test_same_database_cannot_certify_itself(reference):
    with pytest.raises(ValueError, match='distinct'):
        preflight.compare('dbname=' + reference[0], 'dbname=' + reference[0])


def test_app_role_cannot_bypass_protected_hold_reader(reference):
    with psycopg.connect('dbname=' + reference[0]) as conn:
        conn.execute('SET LOCAL ROLE mpsc')
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute('SELECT 1 FROM account_study_history_holds LIMIT 0')


def test_reader_is_read_only_even_when_operator_can_write(reference):
    with ExitStack() as stack:
        conn = preflight.reader(stack, 'dbname=' + reference[0])
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
            conn.execute('DELETE FROM public.account_study_history_holds')


def test_cli_redacts_missing_privilege_diagnostics(reference, monkeypatch, capsys):
    monkeypatch.setenv('FINNA_RESTORE_REFERENCE_DSN', 'dbname=' + reference[0] + " options='-c role=mpsc'")
    monkeypatch.setenv('FINNA_RESTORE_CANDIDATE_DSN', 'dbname=' + reference[0])
    assert preflight.main(['--run']) == 1
    output = capsys.readouterr().out
    result = json.loads(output)
    assert result['status'] == 'error' and result['error_kind'] == 'InsufficientPrivilege'
    assert reference[0] not in output and 'synthetic-retention-user' not in output
