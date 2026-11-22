#!/usr/bin/env python3
"""Read-only comparison of private-study cleanup, records and restricted holds.

Use a separately authorized reader that can SELECT the protected hold table.
This tool grants nothing, changes no role, repairs nothing and authorizes no restore.
"""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets

import psycopg

_spec = importlib.util.spec_from_file_location('retention_privacy_reader', Path(__file__).with_name('check-restore-privacy.py'))
_privacy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_privacy)

CONTROLS = {
    'users': 'jsonb_build_array(x.id,x.closed_at,x.study_history_purged_at,x.private_study_purged_at)',
    'account_study_history_holds': 'to_jsonb(x)',
    'account_closure_recovery': 'to_jsonb(x)',
    'essay_drafts': 'to_jsonb(x)',
    'user_question_bookmarks': 'to_jsonb(x)',
    'material_bookmarks': 'to_jsonb(x)',
    'user_calendar_saved': 'to_jsonb(x)',
}


def reader(stack, dsn):
    conn = stack.enter_context(psycopg.connect(dsn, autocommit=True, connect_timeout=5))
    stack.enter_context(conn.transaction())
    conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
    conn.execute('SET LOCAL search_path=pg_catalog')
    conn.execute("SET LOCAL TimeZone='UTC'")
    conn.execute("SET LOCAL DateStyle='ISO, YMD'")
    conn.execute("SET LOCAL statement_timeout='10s'")
    conn.execute("SET LOCAL lock_timeout='1s'")
    if conn.execute("SELECT current_setting('transaction_read_only')").fetchone() != ('on',):
        raise ValueError('Read-only transaction required')
    # Fail closed if SELECT is unavailable; do not add app access to holds.
    conn.execute('SELECT 1 FROM public.account_study_history_holds LIMIT 0')
    return conn


def compare(reference_dsn, candidate_dsn):
    salt = secrets.token_hex(32)
    with ExitStack() as stack:
        reference = reader(stack, reference_dsn)
        candidate = reader(stack, candidate_dsn)
        if _privacy.identity(reference) == _privacy.identity(candidate):
            raise ValueError('A distinct restored candidate is required')
        mismatches, matched = [], []
        for table, projection in CONTROLS.items():
            before = _privacy.fingerprint(reference, table, projection, salt)
            after = _privacy.fingerprint(candidate, table, projection, salt)
            if before != after:
                mismatches.append({'table': table, 'reference_rows': before[0], 'candidate_rows': after[0]})
            else:
                matched.append(table)
    return {
        'schema': 1, 'source': 'restore-private-study-preflight-v1',
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'status': 'blocked' if mismatches else 'checks_passed',
        'matched_control_tables': matched, 'control_mismatches': mismatches,
        'read_only': True, 'protected_hold_select_required': True,
        'scope': 'Exact private-study rows, both purge markers, closure, protected holds and reopen envelopes; 0133 schema required',
        'reference_currentness_verified': False, 'external_erasure_ledger_replayed': False,
        'deletion_completion_verified': False, 'key_recovery_verified': False,
        'promotion_authorized': False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', required=True)
    parser.parse_args(argv)
    try:
        result = compare(os.environ['FINNA_RESTORE_REFERENCE_DSN'], os.environ['FINNA_RESTORE_CANDIDATE_DSN'])
        code = 2 if result['status'] == 'blocked' else 0
    except Exception as exc:
        # Never emit driver diagnostics, identifiers, email, ciphertext or DSNs.
        result = {'schema': 1, 'source': 'restore-private-study-preflight-v1',
                  'status': 'error', 'error_kind': type(exc).__name__, 'promotion_authorized': False}
        code = 1
    result['operator_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    print(json.dumps(result, indent=2))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
