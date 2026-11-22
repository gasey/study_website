#!/usr/bin/env python3
"""Compare a quarantined restore's billing/access records with a current reference.

Read-only, independent of the privacy preflight, and never a repair or promotion
command. Supply DSNs privately in the operator environment. No provider calls,
record identifiers, row hashes, salts or connection details are exported.
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


# Explicit projections require the refund schema even when tables are empty.
# Compare durable inputs, including expired/future grants, rather than evaluating
# account_has_pro() at two different clocks. Account identity is checked by the
# separate privacy operator; email eligibility is sufficient here.
# updated_at is deliberately excluded: migration 0132 backfills payment write
# timestamps independently in each restored database. It is not access evidence.
CONTROLS = {
    'users': 'jsonb_build_array(x.id,x.email IS NOT NULL,x.closed_at,x.plan_code,'
             'x.plan_status,x.trial_ends_at,x.plan_ends_at,x.razorpay_subscription_id)',
    'billing_subscriptions': 'jsonb_build_array(x.id,x.user_id,x.plan_code,x.billing_period,'
                            'x.amount_paise,x.currency,x.razorpay_plan_id,x.razorpay_subscription_id,'
                            'x.razorpay_payment_id,x.status,x.current_start,x.current_end,x.created_at,'
                            'x.access_ended_at,x.access_end_reason)',
    'billing_payments': 'jsonb_build_array(x.razorpay_payment_id,x.razorpay_subscription_id,'
                       'x.user_id,x.amount_paise,x.currency,x.status,x.paid_at,x.created_at,'
                       'x.amount_refunded_paise,x.refund_status)',
    'billing_refunds': 'jsonb_build_array(x.razorpay_refund_id,x.razorpay_payment_id,'
                      'x.amount_paise,x.currency,x.status,x.provider_created_at,x.created_at)',
    'billing_webhook_events': 'jsonb_build_array(x.event_key,x.event_name,x.received_at)',
    'billing_account_rates': 'jsonb_build_array(x.user_id,x.amount_paise,x.updated_by)',
    'billing_access_grants': 'jsonb_build_array(x.id,x.user_id,x.granted_by,x.idempotency_key,'
                            'x.days,x.starts_at,x.ends_at,x.created_at,x.source)',
    'reward_redemptions': 'jsonb_build_array(x.id,x.user_id,x.idempotency_key,x.catalog_id,'
                          'x.catalog_version,x.points,x.starts_at,x.ends_at,x.created_at)',
}


def connect_readonly(stack, dsn):
    conn = stack.enter_context(psycopg.connect(dsn, autocommit=True, connect_timeout=5))
    stack.enter_context(conn.transaction())
    conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
    conn.execute('SET LOCAL ROLE mpsc')
    conn.execute('SET LOCAL search_path=pg_catalog')
    conn.execute("SET LOCAL TimeZone='UTC'")
    conn.execute("SET LOCAL DateStyle='ISO, YMD'")
    conn.execute("SET LOCAL statement_timeout='10s'")
    conn.execute("SET LOCAL lock_timeout='1s'")
    role, readonly = conn.execute("SELECT current_user,current_setting('transaction_read_only')").fetchone()
    if role != 'mpsc' or readonly != 'on':
        raise ValueError('Read-only application role required')
    return conn


def identity(conn):
    return conn.execute('SELECT oid,pg_postmaster_start_time() FROM pg_database '
                        'WHERE datname=current_database()').fetchone()


def fingerprint(conn, table, projection, salt):
    query = sql.SQL("SELECT encode(sha256(convert_to(%s || ({})::text,'UTF8')),'hex') "
                    'FROM public.{} x ORDER BY 1').format(sql.SQL(projection), sql.Identifier(table))
    digest = hashlib.sha256()
    count = 0
    with conn.cursor(name='restore_billing_'+table) as cur:
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
        for table, projection in CONTROLS.items():
            current = fingerprint(reference, table, projection, salt)
            restored = fingerprint(candidate, table, projection, salt)
            if current != restored:
                mismatches.append({'table': table, 'reference_rows': current[0],
                                   'candidate_rows': restored[0]})
            else:
                matched.append(table)
    return {
        'schema': 1,
        'source': 'restore-billing-preflight-v1',
        'status': 'blocked' if mismatches else 'checks_passed',
        'checked_at': checked.isoformat(),
        'read_only_role': 'mpsc',
        'matched_control_tables': matched,
        'control_mismatches': mismatches,
        'provider_reconciliation_verified': False,
        'reference_currentness_verified': False,
        'external_writer_drain_required': True,
        'promotion_authorized': False,
        'scope': 'stored billing/access inputs and receipts only; excludes reward balances, '
                 'catalog/provider configuration, live provider state and runtime/schema certification',
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', required=True)
    parser.parse_args(argv)
    try:
        result = compare(os.environ['FINNA_RESTORE_REFERENCE_DSN'],
                         os.environ['FINNA_RESTORE_CANDIDATE_DSN'])
        code = 2 if result['status'] == 'blocked' else 0
    except Exception as exc:
        # Driver diagnostics can contain private DSNs, record values and SQL.
        result = {'schema': 1, 'source': 'restore-billing-preflight-v1',
                  'status': 'error', 'error_kind': type(exc).__name__,
                  'promotion_authorized': False}
        code = 1
    result['operator_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    print(json.dumps(result, indent=2))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
