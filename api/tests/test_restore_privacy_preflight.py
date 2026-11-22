"""A restore is never current merely because its dump can be read back."""
import importlib.util
import json
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql
import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('restore_privacy', ROOT/'scripts/check-restore-privacy.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


@pytest.fixture
def pair(database_schema):
    names = ['ism_review_test_'+uuid4().hex[:12] for _ in range(2)]
    created = []
    connections = []
    with psycopg.connect('dbname=postgres', autocommit=True) as admin:
        try:
            for name in names:
                admin.execute(sql.SQL('CREATE DATABASE {} TEMPLATE {}').format(sql.Identifier(name), sql.Identifier(database_schema)))
                created.append(name)
                conn = psycopg.connect('dbname='+name, autocommit=True)
                connections.append(conn)
                conn.execute("INSERT INTO users(id,handle,email,password_hash) VALUES('restore-subject','restore-subject','sensitive@example.test','synthetic-password-hash')")
            yield names, connections
        finally:
            for conn in connections:
                conn.close()
            for name in created:
                admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))


def check(pair):
    return guard.compare(*('dbname='+n for n in pair[0]))


def mismatches(result):
    return {r['table'] for r in result['control_mismatches']}


def test_current_controls_and_quarantined_candidate_pass_only_the_bounded_checks(pair):
    result = check(pair)
    assert result['status'] == 'checks_passed'
    assert len(result['matched_control_tables']) == 21
    assert result['read_only_role'] == 'mpsc'
    assert not any(result['candidate_quarantine_counts'].values())
    assert result['reference_currentness_verified'] is False
    assert result['external_writer_drain_required'] is True
    assert result['promotion_authorized'] is False
    output = json.dumps(result)
    for secret in ('restore-subject', 'sensitive@example.test', 'synthetic-password-hash', *pair[0]):
        assert secret not in output


def test_closure_after_backup_is_detected_without_rewriting_either_database(pair):
    current, old = pair[1]
    current.execute("UPDATE users SET closed_at=now(),email=NULL,password_hash=NULL,name=NULL,avatar=NULL,handle='deleted-restore-subject',identity_version=1,contribution_public=false WHERE id='restore-subject'")
    assert check(pair)['status'] == 'blocked'
    assert mismatches(check(pair)) == {'users'}
    assert old.execute("SELECT email,closed_at FROM users WHERE id='restore-subject'").fetchone() == ('sensitive@example.test', None)
    assert current.execute("SELECT email,closed_at IS NOT NULL FROM users WHERE id='restore-subject'").fetchone() == (None, True)


@pytest.mark.parametrize('reference_category,candidate_category', [('under18','adult'), ('under18',None), (None,'adult')])
def test_unknown_and_under18_categories_cannot_be_replaced_by_an_old_adult_declaration(pair, reference_category, candidate_category):
    for conn, category in zip(pair[1], (reference_category, candidate_category)):
        if category:
            conn.execute("INSERT INTO account_audience(user_id,category,declared_at) VALUES('restore-subject',%s,'2026-01-01Z')", (category,))
    assert 'account_audience' in mismatches(check(pair))


@pytest.mark.parametrize('state', ['received','in_review','completed','declined','withdrawn'])
def test_missing_current_privacy_request_or_terminal_state_blocks(pair, state):
    current, _ = pair[1]
    current.execute("INSERT INTO privacy_requests(id,user_id,kind,request_key,state) VALUES('synthetic-request','restore-subject','erasure','synthetic-request-key',%s)", (state,))
    current.execute("INSERT INTO privacy_request_events(request_id,actor_id,state) VALUES('synthetic-request','restore-subject',%s)", (state,))
    assert {'privacy_requests','privacy_request_events'} <= mismatches(check(pair))


def test_same_request_id_with_stale_state_and_version_is_not_accepted(pair):
    for conn in pair[1]:
        conn.execute("INSERT INTO privacy_requests(id,user_id,kind,request_key,created_at,updated_at) VALUES('synthetic-request','restore-subject','guardian','synthetic-request-key','2026-01-01Z','2026-01-01Z')")
    pair[1][0].execute("UPDATE privacy_requests SET state='withdrawn',version=2 WHERE id='synthetic-request'")
    assert 'privacy_requests' in mismatches(check(pair))


@pytest.mark.parametrize('table,statement', [
    ('auth_sessions', "INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES('synthetic-web-secret','restore-subject',now()+interval '1 day')"),
    ('mobile_sessions', "INSERT INTO mobile_sessions(token_hash,public_id,user_id,parent_session_hash) VALUES('synthetic-mobile-secret','synthetic-mobile','restore-subject','gone-parent')"),
    ('guest_credentials', "INSERT INTO guest_credentials(token_hash,user_id) VALUES('synthetic-guest-secret','restore-subject')"),
    ('account_email_tokens', "INSERT INTO account_email_tokens(token_hash,user_id,purpose,expires_at) VALUES('synthetic-reset-secret','restore-subject','reset',now()+interval '1 day')"),
    ('google_auth_flows', "INSERT INTO google_auth_flows(token_hash,stage) VALUES('synthetic-google-secret','authorize')"),
    ('mobile_auth_flows', "INSERT INTO mobile_auth_flows(id,challenge,state,redirect_uri) VALUES('synthetic-mobile-flow','challenge','state','finna://callback')"),
    ('audience_browser_flows', "INSERT INTO audience_browser_flows(token_hash,category) VALUES(repeat('a',64),'adult')"),
    ('calendar_feed_tokens', "INSERT INTO calendar_feed_tokens(user_id,token_hash,version) VALUES('restore-subject',repeat('b',64),1)"),
    ('account_mail_outbox', "INSERT INTO account_mail_outbox(user_id,purpose,token_cipher) VALUES('restore-subject','reset','synthetic-ciphertext')"),
    ('review_digest_outbox', "INSERT INTO review_digest_outbox(user_id,day,consent_version) VALUES('restore-subject',current_date,1)"),
])
def test_each_restored_credential_or_outbound_queue_requires_quarantine(pair, table, statement):
    pair[1][1].execute(statement)
    result = check(pair)
    assert result['status'] == 'blocked'
    assert result['candidate_quarantine_counts'][table] == 1
    assert result['control_mismatches'] == []
    assert 'synthetic-' not in json.dumps(result)


def test_revoked_expired_and_consumed_credentials_are_not_mistaken_for_live_access(pair):
    old = pair[1][1]
    old.execute("INSERT INTO auth_sessions(token_hash,user_id,expires_at,revoked_at) VALUES('revoked','restore-subject',now()+interval '1 day',now()),('expired','restore-subject',now()-interval '1 day',NULL)")
    old.execute("INSERT INTO account_email_tokens(token_hash,user_id,purpose,expires_at,consumed_at) VALUES('consumed','restore-subject','reset',now()+interval '1 day',now())")
    assert check(pair)['status'] == 'checks_passed'


@pytest.mark.parametrize('table', ['account_mail_deliveries','review_digest_deliveries'])
def test_lost_or_resurrected_delivery_receipts_are_not_discarded_during_recovery(pair, table):
    pair[1][0].execute(sql.SQL("INSERT INTO public.{}(outbox_id,attempt,state,finished_at) VALUES(123,1,'uncertain','2026-01-01Z')").format(sql.Identifier(table)))
    result = check(pair)
    assert table in mismatches(result)


def test_matching_uncertain_history_and_cancelled_outbox_do_not_require_history_deletion(pair):
    for conn in pair[1]:
        conn.execute("INSERT INTO account_mail_deliveries(outbox_id,attempt,state,finished_at,reserved_at) VALUES(123,1,'uncertain','2026-01-02Z','2026-01-01Z')")
        conn.execute("INSERT INTO review_digest_deliveries(outbox_id,attempt,state,finished_at,reserved_at) VALUES(123,1,'uncertain','2026-01-02Z','2026-01-01Z')")
    pair[1][1].execute("INSERT INTO account_mail_outbox(user_id,purpose,token_cipher,last_error) VALUES('restore-subject','reset','','Cancelled')")
    result = check(pair)
    assert result['status'] == 'checks_passed'
    assert result['candidate_quarantine_counts']['account_mail_outbox'] == 0
    assert result['delivery_reservations_for_review'] == {'account_mail_deliveries':1,'review_digest_deliveries':1}
    assert result['provider_delivery_reconciliation_verified'] is False
    assert result['promotion_authorized'] is False
    for conn in pair[1]:
        assert conn.execute('SELECT state FROM account_mail_deliveries WHERE outbox_id=123').fetchone() == ('uncertain',)


@pytest.mark.parametrize('table,statement', [
    ('google_identities', "INSERT INTO google_identities(subject,user_id) VALUES('synthetic-google-subject','restore-subject')"),
    ('account_mfa', "INSERT INTO account_mfa(user_id,secret_cipher,enabled_at) VALUES('restore-subject','synthetic-mfa-secret',now())"),
    ('mfa_recovery_codes', "INSERT INTO mfa_recovery_codes(user_id,code_hash) VALUES('restore-subject','synthetic-recovery-secret')"),
    ('creator_profiles', "INSERT INTO creator_profiles(user_id,public,bio) VALUES('restore-subject',true,'synthetic private bio')"),
    ('reward_profiles', "INSERT INTO reward_profiles(user_id,board_public) VALUES('restore-subject',true)"),
    ('user_calendar_preferences', "INSERT INTO user_calendar_preferences(user_id,reminders) VALUES('restore-subject',true)"),
    ('review_digest_preferences', "INSERT INTO review_digest_preferences(user_id,enabled,version,token_hash,token_cipher,email_hash) VALUES('restore-subject',true,1,'synthetic-unsubscribe','synthetic-digest-secret','synthetic-email-hash')"),
    ('referral_codes', "INSERT INTO referral_codes(user_id,code) VALUES('restore-subject',repeat('r',24))"),
])
def test_unlink_mfa_privacy_and_delivery_preferences_are_compared(pair, table, statement):
    pair[1][1].execute(statement)
    result = check(pair)
    assert table in mismatches(result)
    assert 'synthetic-' not in json.dumps(result)


def test_closed_private_document_resurrection_is_detected(pair):
    # An old document can predate closure; inserting after closure is correctly
    # rejected by the existing active-account guard.
    pair[1][1].execute("INSERT INTO personal_desks(user_id,document) VALUES('restore-subject','{\"private\":\"synthetic text\"}')")
    for conn in pair[1]:
        conn.execute("UPDATE users SET closed_at='2026-01-01Z',email=NULL,password_hash=NULL,name=NULL,avatar=NULL,handle='deleted-restore-subject',identity_version=1,contribution_public=false WHERE id='restore-subject'")
    assert 'personal_desks' in mismatches(check(pair))


def test_password_change_without_identity_version_change_is_detected(pair):
    pair[1][0].execute("UPDATE users SET password_hash='new-synthetic-hash' WHERE id='restore-subject'")
    assert 'users' in mismatches(check(pair))


def test_revoked_staff_grant_cannot_return_with_an_old_backup(pair):
    for conn in pair[1]:
        conn.execute("INSERT INTO review_grants(user_id,role,granted_by,reason,created_at) VALUES('restore-subject','reviewer','test','Synthetic fixture grant','2026-01-01Z')")
    pair[1][0].execute("UPDATE review_grants SET revoked_at='2026-01-02Z' WHERE user_id='restore-subject'")
    assert 'review_grants' in mismatches(check(pair))


def test_left_membership_and_cancelled_invitation_cannot_be_restored_as_active(pair):
    for conn in pair[1]:
        conn.execute("INSERT INTO users(id,handle,email) VALUES('second-subject','second-subject','second@example.test')")
        conn.execute("INSERT INTO study_desks(id,owner_id,name,created_at) VALUES('synthetic-desk','restore-subject','Synthetic desk','2026-01-01Z')")
        conn.execute("INSERT INTO study_desk_members(desk_id,user_id,joined_at) VALUES('synthetic-desk','restore-subject','2026-01-01Z')")
        conn.execute("INSERT INTO study_desk_invites(id,desk_id,sender_id,recipient_id,expires_at,created_at) VALUES('synthetic-invite','synthetic-desk','restore-subject','second-subject','2026-12-01Z','2026-01-01Z')")
        conn.execute("INSERT INTO creator_follows(follower_id,creator_id,created_at) VALUES('restore-subject','second-subject','2026-01-01Z')")
    pair[1][0].execute("UPDATE study_desk_members SET left_at=now(),sharing='{}' WHERE user_id='restore-subject'")
    pair[1][0].execute("UPDATE study_desk_invites SET state='cancelled'")
    pair[1][0].execute('DELETE FROM creator_follows')
    assert {'study_desk_members','study_desk_invites','creator_follows'} <= mismatches(check(pair))


def test_new_current_account_missing_from_backup_is_not_silently_discarded(pair):
    pair[1][0].execute("INSERT INTO users(id,handle,email) VALUES('new-subject','new-subject','new@example.test')")
    assert 'users' in mismatches(check(pair))


def test_matching_restriction_and_retired_sessions_clear_only_the_reported_blockers(pair):
    current, old = pair[1]
    for conn in pair[1]:
        conn.execute("INSERT INTO account_audience(user_id,category,declared_at) VALUES('restore-subject','adult','2026-01-01Z')")
    current.execute("UPDATE account_audience SET category='under18',version=2,declared_at='2026-01-02Z'")
    old.execute("INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES('old-web-token','restore-subject',now()+interval '1 day')")
    blocked = check(pair)
    assert blocked['status'] == 'blocked'
    assert mismatches(blocked) == {'account_audience'}
    assert blocked['candidate_quarantine_counts']['auth_sessions'] == 1
    old.execute("UPDATE account_audience SET category='under18',version=2,declared_at='2026-01-02Z'")
    old.execute('UPDATE auth_sessions SET revoked_at=now()')
    passed = check(pair)
    assert passed['status'] == 'checks_passed'
    assert passed['promotion_authorized'] is False


def test_missing_required_schema_fails_closed_instead_of_ignoring_age_controls(pair):
    pair[1][1].execute('ALTER TABLE account_audience RENAME TO hidden_audience')
    with pytest.raises(psycopg.errors.UndefinedTable):
        check(pair)


def test_same_database_through_two_connections_cannot_certify_itself(pair):
    with pytest.raises(ValueError, match='distinct restored candidate'):
        guard.compare('dbname='+pair[0][0], 'dbname='+pair[0][0])


def test_application_role_is_enforced_read_only_even_though_it_normally_has_write_grants(pair):
    from contextlib import ExitStack
    with ExitStack() as stack:
        conn = guard.connect_readonly(stack, 'dbname='+pair[0][1])
        assert conn.execute("SELECT current_user,current_setting('transaction_read_only')").fetchone() == ('mpsc','on')
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
            conn.execute("UPDATE public.users SET name='should-never-write' WHERE id='restore-subject'")


def test_cli_error_receipt_never_exports_driver_details_or_dsn(monkeypatch, capsys):
    monkeypatch.setenv('FINNA_RESTORE_REFERENCE_DSN', 'private-DSN-password')
    monkeypatch.setenv('FINNA_RESTORE_CANDIDATE_DSN', 'other-private-DSN')
    def failed(*_):
        raise RuntimeError('secret@example.test password=private-DSN-password')
    monkeypatch.setattr(guard, 'compare', failed)
    assert guard.main(['--run']) == 1
    result = json.loads(capsys.readouterr().out)
    assert result['status'] == 'error' and result['error_kind'] == 'RuntimeError'
    assert result['promotion_authorized'] is False
    assert 'private-DSN' not in json.dumps(result) and '@' not in json.dumps(result)


def test_cli_keeps_blocked_and_scoped_pass_distinct(monkeypatch, capsys):
    monkeypatch.setenv('FINNA_RESTORE_REFERENCE_DSN', 'reference')
    monkeypatch.setenv('FINNA_RESTORE_CANDIDATE_DSN', 'candidate')
    for status, expected in [('blocked',2),('checks_passed',0)]:
        monkeypatch.setattr(guard, 'compare', lambda *_: {'status':status,'promotion_authorized':False})
        assert guard.main(['--run']) == expected
        assert json.loads(capsys.readouterr().out)['status'] == status
