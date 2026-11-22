"""A restore repair review needs additions, removals, changed fields and dependencies."""
from contextlib import ExitStack
import importlib.util
import json
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql
import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('restore_accounts', ROOT/'scripts/diagnose-restore-accounts.py')
operator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operator)


@pytest.fixture
def pair(database_schema):
    names = ['ism_review_test_'+uuid4().hex[:12] for _ in range(2)]
    created, connections = [], []
    with psycopg.connect('dbname=postgres', autocommit=True) as admin:
        try:
            for name in names:
                admin.execute(sql.SQL('CREATE DATABASE {} TEMPLATE {}').format(
                    sql.Identifier(name), sql.Identifier(database_schema)))
                created.append(name)
                conn = psycopg.connect('dbname='+name, autocommit=True)
                connections.append(conn)
                conn.execute("INSERT INTO users(id,handle,email,password_hash,created_at) VALUES"
                             "('shared-one','shared-one','private-one@example.test','private-hash','2026-01-01Z'),"
                             "('shared-two','shared-two',NULL,NULL,'2026-01-01Z')")
            yield names, connections
        finally:
            for conn in connections:
                conn.close()
            for name in created:
                admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))


def check(pair):
    return operator.diagnose(*('dbname='+name for name in pair[0]))


def add(conn, key='new-private', email=None, closed=None):
    conn.execute("INSERT INTO users(id,handle,email,closed_at,contribution_public,created_at) "
                 "VALUES(%s,%s,%s,%s,false,'2026-01-01Z')", (key, key, email, closed))


def dependency(result, table, column):
    return next(row for row in result['direct_foreign_key_counts']
                if row['table'] == table and row['column'] == column)


def test_identical_accounts_are_diagnosed_without_authorizing_repair_or_promotion(pair):
    result = check(pair)
    assert result['user_counts'] == {'reference': 2, 'candidate': 2, 'shared': 2,
                                   'reference_only': 0, 'candidate_only': 0,
                                   'shared_changed': 0, 'shared_identical': 2}
    assert result['shared_field_change_counts'] == {}
    assert result['reference_currentness_verified'] is False
    assert result['repair_authorized'] is False and result['promotion_authorized'] is False
    assert result['read_only_role'] == 'mpsc'
    output = json.dumps(result)
    for private in ('shared-one','private-one@example.test','private-hash',*pair[0]):
        assert private not in output


def test_equal_totals_do_not_hide_different_accounts_and_changed_unprojected_fields(pair):
    current, old = pair[1]
    add(current, 'new-current-private', 'new@example.test')
    add(old, 'old-only-private')
    current.execute("UPDATE users SET password_hash='replacement-secret',avatar_version=2,"
                    "plan_ends_at='2099-01-01Z' WHERE id='shared-one'")
    result = check(pair)
    assert result['user_counts'] == {'reference': 3, 'candidate': 3, 'shared': 2,
                                   'reference_only': 1, 'candidate_only': 1,
                                   'shared_changed': 1, 'shared_identical': 1}
    assert result['shared_field_change_counts'] == {'avatar_version': 1, 'password_hash': 1, 'plan_ends_at': 1}
    assert result['reference_only_categories']['open_with_email'] == 1
    assert result['candidate_only_categories']['open_without_email'] == 1
    for private in ('replacement-secret','new-current-private','old-only-private','new@example.test'):
        assert private not in json.dumps(result)
    assert old.execute("SELECT avatar_version FROM users WHERE id='shared-one'").fetchone() == (0,)


@pytest.mark.parametrize('which', [0, 1])
@pytest.mark.parametrize('email,closed,category', [
    (None,None,'open_without_email'), ('private@example.test',None,'open_with_email'),
    (None,'2026-01-01Z','closed'),
])
def test_added_and_removed_categories_do_not_infer_guest_or_registered_status_after_closure(pair, which, email, closed, category):
    add(pair[1][which], email=email, closed=closed)
    result = check(pair)
    key = 'reference_only_categories' if which == 0 else 'candidate_only_categories'
    assert result[key][category] == 1 and sum(result[key].values()) == 1


def test_direct_dependencies_include_both_account_and_actor_columns_without_mutating_rows(pair):
    current, old = pair[1]
    add(current)
    current.execute("INSERT INTO auth_sessions(token_hash,user_id,expires_at) "
                    "VALUES('private-token','new-private','2099-01-01Z')")
    current.execute("INSERT INTO billing_account_rates(user_id,amount_paise,updated_by) "
                    "VALUES('new-private',5000,'new-private')")
    current.execute("UPDATE users SET name='private name' WHERE id='shared-one'")
    for conn in (current, old):
        conn.execute("INSERT INTO guest_credentials(token_hash,user_id,created_at,expires_at) "
                     "VALUES('private-guest-token','shared-one','2026-01-01Z','2099-01-01Z')")
    result = check(pair)
    for table, column in [('auth_sessions','user_id'), ('billing_account_rates','user_id'), ('billing_account_rates','updated_by')]:
        row = dependency(result, table, column)
        assert row['reference']['only_users_rows'] == 1
        assert row['candidate']['only_users_rows'] == 0
    row = dependency(result, 'guest_credentials', 'user_id')
    assert row['reference']['shared_changed_users_rows'] == 1
    assert row['candidate']['shared_changed_users_rows'] == 1
    assert current.execute('SELECT token_hash FROM auth_sessions').fetchall() == [('private-token',)]
    assert 'private-token' not in json.dumps(result)


def test_missing_dependency_read_permission_is_reported_as_a_gap(pair):
    pair[1][1].execute('REVOKE SELECT ON billing_account_rates FROM mpsc')
    result = check(pair)
    assert result['status'] == 'diagnosed_with_dependency_gaps'
    assert any(row['table'] == 'billing_account_rates' for row in result['dependency_gaps'])
    row = dependency(result, 'billing_account_rates', 'user_id')
    assert row['candidate'] == {'reviewed': False, 'reason': 'read_privilege_missing'}


def test_missing_account_column_and_different_foreign_key_inventory_fail_closed(pair):
    current, old = pair[1]
    current.execute('ALTER TABLE users ADD COLUMN new_private_column text')
    with pytest.raises(ValueError, match='column schemas'):
        check(pair)
    current.execute('ALTER TABLE users DROP COLUMN new_private_column')
    old.execute('ALTER TABLE auth_sessions DROP CONSTRAINT auth_sessions_user_id_fkey')
    with pytest.raises(ValueError, match='foreign-key inventories'):
        check(pair)


def test_composite_account_reference_is_an_explicit_review_gap(pair):
    for conn in pair[1]:
        conn.execute('ALTER TABLE users ADD UNIQUE(id,handle)')
        conn.execute('CREATE TABLE synthetic_composite_actor(actor text,actor_handle text,'
                     'FOREIGN KEY(actor,actor_handle) REFERENCES users(id,handle))')
    result = check(pair)
    assert result['status'] == 'diagnosed_with_dependency_gaps'
    assert {'schema': 'public', 'table': 'synthetic_composite_actor', 'column': 'actor',
            'reason': 'non_simple_account_id_reference'} in result['dependency_gaps']


def test_same_database_cannot_supply_both_sides(pair):
    with pytest.raises(ValueError, match='distinct restored candidate'):
        operator.diagnose('dbname='+pair[0][0], 'dbname='+pair[0][0]+' application_name=alias')


def test_shared_readonly_helper_still_enforces_application_role_and_no_writes(pair):
    with ExitStack() as stack:
        conn = operator.readonly.connect_readonly(stack, 'dbname='+pair[0][1])
        assert conn.execute("SELECT current_user,current_setting('transaction_read_only')").fetchone() == ('mpsc','on')
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
            conn.execute("UPDATE public.users SET email=NULL WHERE id='shared-one'")


def test_cli_needs_explicit_run_and_redacts_errors(monkeypatch, capsys):
    with pytest.raises(SystemExit) as exc:
        operator.main([])
    assert exc.value.code == 2
    capsys.readouterr()
    monkeypatch.setenv('FINNA_RESTORE_REFERENCE_DSN', 'password=private-reference')
    monkeypatch.setenv('FINNA_RESTORE_CANDIDATE_DSN', 'private-candidate')
    def failed(*_):
        raise RuntimeError('password=private-reference private@example.test')
    monkeypatch.setattr(operator, 'diagnose', failed)
    assert operator.main(['--run']) == 1
    result = json.loads(capsys.readouterr().out)
    assert result['status'] == 'error' and result['error_kind'] == 'RuntimeError'
    assert result['repair_authorized'] is False and result['promotion_authorized'] is False
    assert len(result['operator_sha256']) == len(result['readonly_helper_sha256']) == 64
    assert 'private' not in json.dumps(result)


def test_cli_distinguishes_dependency_gaps_without_treating_diagnosis_as_promotion(monkeypatch, capsys):
    monkeypatch.setenv('FINNA_RESTORE_REFERENCE_DSN', 'reference')
    monkeypatch.setenv('FINNA_RESTORE_CANDIDATE_DSN', 'candidate')
    for gaps, expected in [([],0), ([{'reason': 'read_privilege_missing'}],2)]:
        monkeypatch.setattr(operator, 'diagnose', lambda *_: {
            'status': 'diagnosed_with_dependency_gaps' if gaps else 'diagnosed',
            'dependency_gaps': gaps, 'repair_authorized': False, 'promotion_authorized': False})
        assert operator.main(['--run']) == expected
        result = json.loads(capsys.readouterr().out)
        assert result['repair_authorized'] is False and result['promotion_authorized'] is False
