"""Old backups must not resurrect refunded access or discard financial receipts."""
from contextlib import ExitStack
import importlib.util
import json
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql
import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('restore_billing', ROOT/'scripts/check-restore-billing.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


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
                conn.execute("INSERT INTO users(id,handle,email,password_hash) VALUES"
                             "('restore-payer','restore-payer','payer@example.test','private-hash'),"
                             "('other-payer','other-payer','other@example.test','other-hash')")
                conn.execute("UPDATE users SET plan_code='pro',plan_status='active',"
                             "plan_ends_at='2099-01-01Z',razorpay_subscription_id='sub_private' "
                             "WHERE id='restore-payer'")
                conn.execute("INSERT INTO billing_subscriptions(id,user_id,plan_code,billing_period,"
                             "amount_paise,razorpay_plan_id,razorpay_subscription_id,status,"
                             "current_start,current_end,created_at,updated_at) VALUES"
                             "(123,'restore-payer','pro','monthly',5000,'plan_private','sub_private',"
                             "'active','2026-01-01Z','2099-01-01Z','2026-01-01Z','2026-01-01Z')")
                conn.execute("INSERT INTO billing_payments(razorpay_payment_id,razorpay_subscription_id,"
                             "user_id,amount_paise,status,paid_at,created_at) VALUES"
                             "('pay_private','sub_private','restore-payer',5000,'captured',"
                             "'2026-01-01Z','2026-01-01Z')")
            yield names, connections
        finally:
            for conn in connections:
                conn.close()
            for name in created:
                admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))


def check(pair):
    return guard.compare(*('dbname='+name for name in pair[0]))


def mismatches(result):
    return {row['table'] for row in result['control_mismatches']}


def refund(conn, status='processed', amount=5000):
    conn.execute("INSERT INTO billing_refunds(razorpay_refund_id,razorpay_payment_id,amount_paise,"
                 "currency,status,provider_created_at,created_at,updated_at) VALUES"
                 "('rfnd_private','pay_private',%s,'INR',%s,'2026-01-02Z','2026-01-02Z','2026-01-02Z')",
                 (amount, status))


def test_matching_records_pass_only_a_bounded_comparison_without_private_values(pair):
    result = check(pair)
    assert result['status'] == 'checks_passed'
    assert len(result['matched_control_tables']) == 8
    assert result['read_only_role'] == 'mpsc'
    assert result['provider_reconciliation_verified'] is False
    assert result['reference_currentness_verified'] is False
    assert result['external_writer_drain_required'] is True
    assert result['promotion_authorized'] is False
    output = json.dumps(result)
    for secret in ('restore-payer', 'payer@example.test', 'private-hash', 'sub_private',
                   'pay_private', 'plan_private', *pair[0]):
        assert secret not in output


def test_full_refund_after_backup_cannot_silently_restore_pro_or_lose_receipts(pair):
    current, old = pair[1]
    refund(current)
    current.execute("UPDATE billing_subscriptions SET access_ended_at='2026-01-02Z',access_end_reason='full_refund'")
    current.execute("UPDATE billing_payments SET status='refunded',amount_refunded_paise=5000,refund_status='full'")
    current.execute("UPDATE users SET plan_code='free',plan_status='refunded',plan_ends_at='2026-01-02Z' "
                    "WHERE id='restore-payer'")
    assert current.execute("SELECT account_has_pro('restore-payer')").fetchone() == (False,)
    assert old.execute("SELECT account_has_pro('restore-payer')").fetchone() == (True,)
    result = check(pair)
    assert result['status'] == 'blocked'
    assert mismatches(result) == {'users', 'billing_subscriptions', 'billing_payments', 'billing_refunds'}
    assert old.execute('SELECT count(*) FROM billing_refunds').fetchone() == (0,)
    assert old.execute("SELECT account_has_pro('restore-payer')").fetchone() == (True,)
    assert 'rfnd_private' not in json.dumps(result)


@pytest.mark.parametrize('status', ['pending', 'processed', 'failed'])
def test_partial_and_unsuccessful_refund_history_matters_even_if_access_matches(pair, status):
    current, old = pair[1]
    refund(current, status, 1000)
    for conn in (current, old):
        assert conn.execute("SELECT account_has_pro('restore-payer')").fetchone() == (True,)
    assert mismatches(check(pair)) == {'billing_refunds'}


@pytest.mark.parametrize('statement,table', [
    ("UPDATE billing_subscriptions SET access_ended_at='2026-01-02Z',access_end_reason='full_refund'", 'billing_subscriptions'),
    ("UPDATE billing_payments SET amount_refunded_paise=1000,refund_status='partial'", 'billing_payments'),
    ("UPDATE billing_payments SET amount_paise=10000", 'billing_payments'),
    ("UPDATE billing_payments SET user_id='other-payer'", 'billing_payments'),
    ("UPDATE billing_payments SET currency='USD'", 'billing_payments'),
    ("UPDATE billing_subscriptions SET status='cancelled'", 'billing_subscriptions'),
    ("UPDATE billing_subscriptions SET current_end='2027-01-01Z'", 'billing_subscriptions'),
    ("UPDATE users SET razorpay_subscription_id='sub_replacement' WHERE id='restore-payer'", 'users'),
    ("UPDATE users SET trial_ends_at='2099-01-01Z' WHERE id='other-payer'", 'users'),
    ("UPDATE users SET plan_ends_at='2027-01-01Z' WHERE id='restore-payer'", 'users'),
    ("UPDATE users SET email=NULL WHERE id='restore-payer'", 'users'),
    ("UPDATE users SET closed_at='2026-01-02Z',email=NULL,password_hash=NULL,name=NULL,avatar=NULL,"
     "handle='deleted-restore-payer',identity_version=1,contribution_public=false WHERE id='restore-payer'", 'users'),
])
def test_equal_row_counts_do_not_hide_changed_access_and_payment_ownership(pair, statement, table):
    pair[1][0].execute(statement)
    result = check(pair)
    assert result['status'] == 'blocked'
    assert mismatches(result) == {table}
    difference = result['control_mismatches'][0]
    assert difference['reference_rows'] == difference['candidate_rows']


@pytest.mark.parametrize('which', [0, 1])
@pytest.mark.parametrize('starts,ends', [('2025-01-01Z','2025-01-08Z'), ('2099-01-01Z','2099-01-08Z')])
def test_lost_or_resurrected_owner_and_earned_grants_are_compared_outside_current_access(pair, which, starts, ends):
    conn = pair[1][which]
    conn.execute("INSERT INTO billing_access_grants(id,user_id,granted_by,idempotency_key,days,"
                 "starts_at,ends_at,created_at) VALUES(123,'other-payer','restore-payer',"
                 "'private-grant-key',7,%s,%s,'2026-01-01Z')", (starts, ends))
    conn.execute("INSERT INTO reward_redemptions(id,user_id,idempotency_key,catalog_id,catalog_version,"
                 "points,starts_at,ends_at,created_at) VALUES('private-redemption','other-payer',"
                 "'private-redemption-key','pro-week',1,1000,%s,%s,'2026-01-01Z')", (starts, ends))
    result = check(pair)
    assert mismatches(result) == {'billing_access_grants', 'reward_redemptions'}
    assert 'private-grant' not in json.dumps(result)


def test_missing_webhook_receipt_and_changed_negotiated_rate_block(pair):
    current, old = pair[1]
    current.execute("INSERT INTO billing_webhook_events(event_key,event_name) VALUES('private-event','refund.processed')")
    for conn in (current, old):
        conn.execute("INSERT INTO billing_account_rates(user_id,amount_paise,updated_by) "
                     "VALUES('restore-payer',5000,'other-payer')")
    current.execute('UPDATE billing_account_rates SET amount_paise=10000')
    assert mismatches(check(pair)) == {'billing_webhook_events', 'billing_account_rates'}


def test_same_refund_id_with_new_processed_state_is_detected(pair):
    for conn in pair[1]:
        refund(conn, 'pending', 1000)
    pair[1][0].execute("UPDATE billing_refunds SET status='processed'")
    result = check(pair)
    assert mismatches(result) == {'billing_refunds'}
    assert result['control_mismatches'][0]['reference_rows'] == 1
    assert result['control_mismatches'][0]['candidate_rows'] == 1


def test_local_migration_write_timestamps_are_not_financial_state(pair):
    pair[1][0].execute("UPDATE billing_payments SET updated_at='2026-01-02Z'")
    pair[1][1].execute("UPDATE billing_payments SET updated_at='2026-01-03Z'")
    assert check(pair)['status'] == 'checks_passed'


@pytest.mark.parametrize('ddl,error', [
    ('ALTER TABLE billing_refunds RENAME TO hidden_refunds', psycopg.errors.UndefinedTable),
    ('ALTER TABLE billing_subscriptions DROP COLUMN access_ended_at', psycopg.errors.UndefinedColumn),
    ('ALTER TABLE billing_payments DROP COLUMN refund_status', psycopg.errors.UndefinedColumn),
    ('REVOKE SELECT ON billing_refunds FROM mpsc', psycopg.errors.InsufficientPrivilege),
])
def test_missing_schema_or_read_privilege_fails_closed_even_for_empty_refunds(pair, ddl, error):
    pair[1][1].execute(ddl)
    with pytest.raises(error):
        check(pair)


def test_same_database_aliases_cannot_certify_themselves(pair):
    with pytest.raises(ValueError, match='distinct restored candidate'):
        guard.compare('dbname='+pair[0][0], 'dbname='+pair[0][0]+' application_name=second-alias')


def test_operator_enforces_read_only_mpsc_despite_its_normal_write_permissions(pair):
    with ExitStack() as stack:
        conn = guard.connect_readonly(stack, 'dbname='+pair[0][1])
        assert conn.execute("SELECT current_user,current_setting('transaction_read_only')").fetchone() == ('mpsc','on')
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
            conn.execute("UPDATE public.users SET plan_code='free' WHERE id='restore-payer'")


def test_cli_error_does_not_export_driver_diagnostics_or_dsns(monkeypatch, capsys):
    monkeypatch.setenv('FINNA_RESTORE_REFERENCE_DSN', 'password=private-reference')
    monkeypatch.setenv('FINNA_RESTORE_CANDIDATE_DSN', 'password=private-candidate')
    def failed(*_):
        raise RuntimeError('private-reference payer@example.test pay_private')
    monkeypatch.setattr(guard, 'compare', failed)
    assert guard.main(['--run']) == 1
    result = json.loads(capsys.readouterr().out)
    assert result['status'] == 'error' and result['error_kind'] == 'RuntimeError'
    assert result['promotion_authorized'] is False
    assert 'private' not in json.dumps(result) and '@' not in json.dumps(result)
    assert len(result['operator_sha256']) == 64


def test_cli_has_no_implicit_run_and_keeps_blocked_separate_from_pass(pair, monkeypatch, capsys):
    with pytest.raises(SystemExit) as exc:
        guard.main([])
    assert exc.value.code == 2
    capsys.readouterr()
    monkeypatch.setenv('FINNA_RESTORE_REFERENCE_DSN', 'dbname='+pair[0][0])
    monkeypatch.setenv('FINNA_RESTORE_CANDIDATE_DSN', 'dbname='+pair[0][1])
    assert guard.main(['--run']) == 0
    assert json.loads(capsys.readouterr().out)['status'] == 'checks_passed'
    pair[1][0].execute("UPDATE billing_payments SET amount_refunded_paise=1000,refund_status='partial'")
    assert guard.main(['--run']) == 2
    assert json.loads(capsys.readouterr().out)['status'] == 'blocked'
