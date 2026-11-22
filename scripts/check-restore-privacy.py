#!/usr/bin/env python3
"""Read-only comparison of a quarantined restore against a current reference.

This is a bounded preflight, never a restore, repair or promotion command. DSNs
come from environment variables and neither DSNs nor record identifiers are logged.
The database computes fresh, privately salted row hashes; secrets stay in SQL.
"""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets

import psycopg
from psycopg import sql


# Fixed projections: compare current identity/security and privacy controls, not
# scores, bank content, billing state or an invented general retention schedule.
CONTROLS = {
    'users': "jsonb_build_array(x.id,x.handle,x.email,x.password_hash,x.name,x.avatar,"
             "x.email_verified_at,x.identity_version,x.closed_at,x.contribution_public,x.role)",
    'account_audience': 'to_jsonb(x)',
    'privacy_requests': 'to_jsonb(x)',
    'privacy_request_events': 'to_jsonb(x)',
    'google_identities': 'to_jsonb(x)',
    'account_mfa': 'to_jsonb(x)',
    'mfa_recovery_codes': 'to_jsonb(x)',
    'account_closure_recovery': 'to_jsonb(x)',
    'review_grants': 'to_jsonb(x)',
    'account_mail_deliveries': 'to_jsonb(x)',
    'review_digest_deliveries': 'to_jsonb(x)',
    'review_digest_preferences': 'to_jsonb(x)',
    'user_calendar_preferences': 'to_jsonb(x)',
    'creator_profiles': 'to_jsonb(x)',
    'creator_follows': 'to_jsonb(x)',
    'reward_profiles': 'jsonb_build_array(x.user_id,x.board_public)',
    'referral_codes': 'to_jsonb(x)',
    'study_desk_members': 'to_jsonb(x)',
    'study_desk_invites': 'to_jsonb(x)',
}
CLOSED_PRIVATE = ('calendar_entries', 'personal_desks')
QUARANTINE = {
    'auth_sessions': 'x.revoked_at IS NULL AND x.expires_at > now()',
    'mobile_sessions': 'x.revoked_at IS NULL AND x.expires_at > now()',
    'guest_credentials': 'x.adopted_at IS NULL AND x.expires_at > now()',
    'account_email_tokens': 'x.consumed_at IS NULL AND x.expires_at > now()',
    'google_auth_flows': 'x.expires_at > now()',
    'mobile_auth_flows': 'x.consumed_at IS NULL AND x.expires_at > now()',
    'audience_browser_flows': 'x.expires_at > now()',
    'calendar_feed_tokens': 'x.token_hash IS NOT NULL',
    'account_mail_outbox': "x.sent_at IS NULL AND x.token_cipher<>''",
    'review_digest_outbox': "x.state='pending'",
}
# These are durable, possibly final capacity receipts. Keep them intact and
# compare them above; an uncertain receipt must not be deleted to clear a gate.
DELIVERY_REVIEW = {
    'account_mail_deliveries': "x.state IN ('reserved','uncertain')",
    'review_digest_deliveries': "x.state IN ('reserved','uncertain')",
}


def connect_readonly(stack, dsn):
    conn = stack.enter_context(psycopg.connect(dsn, autocommit=True, connect_timeout=5))
    stack.enter_context(conn.transaction())
    conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
    conn.execute('SET LOCAL ROLE mpsc')
    conn.execute("SET LOCAL search_path=pg_catalog")
    conn.execute("SET LOCAL TimeZone='UTC'")
    conn.execute("SET LOCAL DateStyle='ISO, YMD'")
    conn.execute("SET LOCAL statement_timeout='10s'")
    conn.execute("SET LOCAL lock_timeout='1s'")
    role, readonly = conn.execute('SELECT current_user,current_setting(\'transaction_read_only\')').fetchone()
    if role != 'mpsc' or readonly != 'on':
        raise ValueError('Read-only application role required')
    return conn


def identity(conn):
    # Same database reached through different host/socket aliases must not certify
    # itself. No superuser-only system identifier query or host details in output.
    return conn.execute("SELECT oid,pg_postmaster_start_time() FROM pg_database WHERE datname=current_database()").fetchone()


def fingerprint(conn, table, projection, salt, where='true'):
    query = sql.SQL("SELECT encode(sha256(convert_to(%s || ({})::text,'UTF8')),'hex') "
                    "FROM public.{} x WHERE {} ORDER BY 1").format(
                        sql.SQL(projection), sql.Identifier(table), sql.SQL(where))
    digest = hashlib.sha256()
    count = 0
    with conn.cursor(name='restore_privacy_'+table) as cur:
        cur.execute(query, (salt,))
        while rows := cur.fetchmany(500):
            for (value,) in rows:
                digest.update(bytes.fromhex(value))
                count += 1
    return count, digest.digest()


def compare(reference_dsn, candidate_dsn):
    checked = datetime.now(timezone.utc)
    salt = secrets.token_hex(32)
    with ExitStack() as stack:
        reference = connect_readonly(stack, reference_dsn)
        candidate = connect_readonly(stack, candidate_dsn)
        if identity(reference) == identity(candidate):
            raise ValueError('A distinct restored candidate is required')
        mismatches = []
        matched = []
        controls = {**CONTROLS, **{t: 'to_jsonb(x)' for t in CLOSED_PRIVATE}}
        for table, projection in controls.items():
            where = ('EXISTS(SELECT 1 FROM public.users u WHERE u.id=x.user_id AND u.closed_at IS NOT NULL)'
                     if table in CLOSED_PRIVATE else 'true')
            current = fingerprint(reference, table, projection, salt, where)
            restored = fingerprint(candidate, table, projection, salt, where)
            if current != restored:
                mismatches.append({'table': table, 'reference_rows': current[0], 'candidate_rows': restored[0]})
            else:
                matched.append(table)
        quarantine = {}
        for table, where in QUARANTINE.items():
            query = sql.SQL('SELECT count(*) FROM public.{} x WHERE {}').format(sql.Identifier(table), sql.SQL(where))
            # Match the candidate database's credential clock, not the laptop's.
            quarantine[table] = candidate.execute(query).fetchone()[0]
        review = {}
        for table, where in DELIVERY_REVIEW.items():
            query = sql.SQL('SELECT count(*) FROM public.{} x WHERE {}').format(sql.Identifier(table), sql.SQL(where))
            review[table] = candidate.execute(query).fetchone()[0]
        blocked = bool(mismatches or any(quarantine.values()))
    return {
        'schema': 1,
        'source': 'restore-privacy-preflight-v1',
        'status': 'blocked' if blocked else 'checks_passed',
        'checked_at': checked.isoformat(),
        'read_only_role': 'mpsc',
        'matched_control_tables': matched,
        'control_mismatches': mismatches,
        'candidate_quarantine_counts': quarantine,
        'delivery_reservations_for_review': review,
        'provider_delivery_reconciliation_verified': False,
        'reference_currentness_verified': False,
        'external_writer_drain_required': True,
        'promotion_authorized': False,
        'scope': 'account controls and candidate credential/mail quarantine only',
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', required=True)
    args = parser.parse_args(argv)
    try:
        reference = os.environ['FINNA_RESTORE_REFERENCE_DSN']
        candidate = os.environ['FINNA_RESTORE_CANDIDATE_DSN']
        result = compare(reference, candidate)
        code = 2 if result['status'] == 'blocked' else 0
    except Exception as exc:
        # Driver diagnostics can contain DSNs, SQL values and identifiers. Never
        # print the exception message or a traceback in an exportable receipt.
        result = {'schema': 1, 'source': 'restore-privacy-preflight-v1',
                  'status': 'error', 'error_kind': type(exc).__name__,
                  'promotion_authorized': False}
        code = 1
    result['operator_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    print(json.dumps(result, indent=2))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
