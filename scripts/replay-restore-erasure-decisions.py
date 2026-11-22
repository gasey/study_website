#!/usr/bin/env python3
"""Export, verify and replay authoritative closure/hold/erasure decisions on isolated restores.

Requires a separately authorized reader/operator with SELECT (and in isolated apply mode,
INSERT/UPDATE) on public.account_study_history_holds plus the 0134 schema.
Never exports emails, handles, names, passwords, essay bodies, answers or ciphertexts.
Never forges purge completion markers and never authorizes production promotion.
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


def _iso(val):
    return val.astimezone(timezone.utc).isoformat() if val is not None else None


def _canonical_hash(payload):
    body = {k: v for k, v in payload.items() if k != 'ledger_sha256'}
    raw = json.dumps(body, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def verify_ledger_integrity(ledger):
    if not isinstance(ledger, dict) or ledger.get('schema') != 1 or ledger.get('source') != 'finna-erasure-decision-ledger-v1':
        raise ValueError('Unsupported erasure decision ledger format')
    expected = ledger.get('ledger_sha256')
    if not expected or expected != _canonical_hash(ledger):
        raise ValueError('Erasure decision ledger integrity check failed')
    return ledger


def _open_readonly(stack, dsn):
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
    # Fail closed if protected hold table or 0134 schema is unavailable.
    conn.execute('SELECT 1 FROM public.account_study_history_holds LIMIT 0')
    conn.execute('SELECT private_preferences_purged_at FROM public.users LIMIT 0')
    return conn


def export_ledger(reference_dsn):
    with ExitStack() as stack:
        conn = _open_readonly(stack, reference_dsn)
        closed_rows = conn.execute('''
            SELECT id, closed_at, study_history_purged_at, private_study_purged_at, private_preferences_purged_at
            FROM public.users
            WHERE closed_at IS NOT NULL
            ORDER BY id
        ''').fetchall()
        hold_rows = conn.execute('''
            SELECT user_id, hold_code, created_at, expires_at, released_at
            FROM public.account_study_history_holds
            ORDER BY user_id, created_at
        ''').fetchall()
        reopen_rows = conn.execute('''
            SELECT user_id
            FROM public.account_closure_recovery
            WHERE expires_at > clock_timestamp()
            ORDER BY user_id
        ''').fetchall()
    payload = {
        'schema': 1,
        'source': 'finna-erasure-decision-ledger-v1',
        'exported_at': datetime.now(timezone.utc).isoformat(),
        'closed_accounts': [
            {
                'user_id': r[0],
                'closed_at': _iso(r[1]),
                'study_history_purged_at': _iso(r[2]),
                'private_study_purged_at': _iso(r[3]),
                'private_preferences_purged_at': _iso(r[4]),
            }
            for r in closed_rows
        ],
        'holds': [
            {
                'user_id': r[0],
                'hold_code': r[1],
                'created_at': _iso(r[2]),
                'expires_at': _iso(r[3]),
                'released_at': _iso(r[4]),
            }
            for r in hold_rows
        ],
        'active_reopen_envelope_users': [r[0] for r in reopen_rows],
    }
    payload['ledger_sha256'] = _canonical_hash(payload)
    return payload


def verify_candidate(candidate_dsn, ledger):
    verify_ledger_integrity(ledger)
    closed_map = {row['user_id']: row for row in ledger['closed_accounts']}
    hold_map = {(row['user_id'], row['created_at']): row for row in ledger['holds']}
    active_reopen = set(ledger['active_reopen_envelope_users'])

    with ExitStack() as stack:
        conn = _open_readonly(stack, candidate_dsn)
        user_rows = {}
        if closed_map:
            rows = conn.execute('''
                SELECT id, closed_at, study_history_purged_at, private_study_purged_at, private_preferences_purged_at
                FROM public.users
                WHERE id = ANY(%s)
            ''', (list(closed_map.keys()),)).fetchall()
            user_rows = {
                r[0]: {
                    'closed_at': _iso(r[1]),
                    'study_history_purged_at': _iso(r[2]),
                    'private_study_purged_at': _iso(r[3]),
                    'private_preferences_purged_at': _iso(r[4]),
                }
                for r in rows
            }
        cand_holds = {
            (r[0], _iso(r[2])): {
                'hold_code': r[1],
                'expires_at': _iso(r[3]),
                'released_at': _iso(r[4]),
            }
            for r in conn.execute('''
                SELECT user_id, hold_code, created_at, expires_at, released_at
                FROM public.account_study_history_holds
            ''').fetchall()
        }
        cand_reopen_users = {
            r[0] for r in conn.execute('SELECT user_id FROM public.account_closure_recovery').fetchall()
        }

    missing_users = 0
    unapplied_closures = 0
    unapplied_base_purges = 0
    unapplied_private_study_purges = 0
    unapplied_private_preferences_purges = 0
    for uid, ref in closed_map.items():
        cand = user_rows.get(uid)
        if cand is None:
            missing_users += 1
            continue
        if cand['closed_at'] is None:
            unapplied_closures += 1
        if ref['study_history_purged_at'] is not None and cand['study_history_purged_at'] is None:
            unapplied_base_purges += 1
        if ref['private_study_purged_at'] is not None and cand['private_study_purged_at'] is None:
            unapplied_private_study_purges += 1
        if ref['private_preferences_purged_at'] is not None and cand['private_preferences_purged_at'] is None:
            unapplied_private_preferences_purges += 1

    missing_holds = 0
    hold_state_mismatches = 0
    for key, ref_h in hold_map.items():
        cand_h = cand_holds.get(key)
        if cand_h is None:
            missing_holds += 1
        elif (cand_h['hold_code'], cand_h['expires_at'], cand_h['released_at']) != (
            ref_h['hold_code'], ref_h['expires_at'], ref_h['released_at']
        ):
            hold_state_mismatches += 1

    stale_reopen_envelopes = sum(
        1 for uid in cand_reopen_users if uid in closed_map and uid not in active_reopen
    )

    drift = {
        'missing_users_in_candidate': missing_users,
        'unapplied_closures': unapplied_closures,
        'missing_holds': missing_holds,
        'hold_state_mismatches': hold_state_mismatches,
        'unapplied_base_purges': unapplied_base_purges,
        'unapplied_private_study_purges': unapplied_private_study_purges,
        'unapplied_private_preferences_purges': unapplied_private_preferences_purges,
        'stale_reopen_envelopes': stale_reopen_envelopes,
    }
    has_drift = any(v > 0 for v in drift.values())
    return {
        'schema': 1,
        'source': 'restore-erasure-decision-verify-v1',
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'ledger_sha256': ledger['ledger_sha256'],
        'status': 'drift_detected' if has_drift else 'reconciled',
        'read_only': True,
        'drift': drift,
        'promotion_authorized': False,
    }


def _replay_closure(conn, uid, closed_at_iso):
    conn.execute('UPDATE public.auth_sessions SET revoked_at=clock_timestamp() WHERE user_id=%s AND revoked_at IS NULL', (uid,))
    conn.execute('UPDATE public.mobile_sessions SET revoked_at=clock_timestamp() WHERE user_id=%s AND revoked_at IS NULL', (uid,))
    row = conn.execute('SELECT subject FROM public.google_identities WHERE user_id=%s', (uid,)).fetchone()
    conn.execute('DELETE FROM public.google_auth_flows WHERE link_user_id=%s OR subject=%s', (uid, row[0] if row else None))
    conn.execute('DELETE FROM public.google_identities WHERE user_id=%s', (uid,))
    conn.execute('UPDATE public.account_email_tokens SET consumed_at=COALESCE(consumed_at,clock_timestamp()) WHERE user_id=%s', (uid,))
    conn.execute('DELETE FROM public.account_mail_outbox WHERE user_id=%s AND sent_at IS NULL', (uid,))
    conn.execute('DELETE FROM public.review_digest_outbox WHERE user_id=%s', (uid,))
    conn.execute('DELETE FROM public.review_digest_preferences WHERE user_id=%s', (uid,))
    conn.execute('UPDATE public.referral_codes SET enabled=false,version=version+1 WHERE user_id=%s AND enabled', (uid,))
    conn.execute('UPDATE public.account_mfa SET secret_cipher=NULL,pending_cipher=NULL,pending_until=NULL,enabled_at=NULL,last_counter=-1 WHERE user_id=%s', (uid,))
    conn.execute('DELETE FROM public.mfa_recovery_codes WHERE user_id=%s', (uid,))
    conn.execute('DELETE FROM public.calendar_entries WHERE user_id=%s', (uid,))
    conn.execute('UPDATE public.calendar_feed_tokens SET token_hash=NULL,revoked_at=clock_timestamp(),version=version+1 WHERE user_id=%s', (uid,))
    conn.execute('DELETE FROM public.personal_desks WHERE user_id=%s', (uid,))
    conn.execute("UPDATE public.creator_profiles SET public=false,bio='',bio_hidden=true,bio_needs_approval=false,bio_version=bio_version+1 WHERE user_id=%s", (uid,))
    conn.execute('DELETE FROM public.creator_follows WHERE follower_id=%s OR creator_id=%s', (uid, uid))
    conn.execute('UPDATE public.reward_profiles SET board_public=false WHERE user_id=%s', (uid,))
    conn.execute("UPDATE public.study_desk_members SET left_at=COALESCE(left_at,clock_timestamp()),sharing='{}'::jsonb WHERE user_id=%s", (uid,))
    conn.execute("UPDATE public.study_desk_invites SET state='cancelled' WHERE state='pending' AND (sender_id=%s OR recipient_id=%s)", (uid, uid))
    conn.execute('''
        UPDATE public.users
        SET closed_at=%s::timestamptz,email=NULL,email_verified_at=NULL,password_hash=NULL,
            name=NULL,avatar=NULL,avatar_version=avatar_version+1,identity_version=identity_version+1,
            handle=%s,contribution_public=false
        WHERE id=%s AND closed_at IS NULL
    ''', (closed_at_iso, 'deleted-' + secrets.token_hex(16), uid))
    conn.execute(
        "INSERT INTO public.account_security_events(user_id,action,detail) VALUES(%s,'restore_closure_replayed',jsonb_build_object('source','erasure-decision-ledger-v1'))",
        (uid,),
    )


def apply_candidate(candidate_dsn, ledger, *, allow_isolated_candidate_write=False, max_sweep_passes=25):
    if not allow_isolated_candidate_write:
        raise ValueError('Explicit --allow-isolated-candidate-write is required to modify an isolated restore candidate')
    verify_ledger_integrity(ledger)
    closed_map = {row['user_id']: row for row in ledger['closed_accounts']}
    active_reopen = set(ledger['active_reopen_envelope_users'])

    holds_replayed = 0
    closures_replayed = 0
    stale_envelopes_removed = 0
    sweep_results = {'study_history': 0, 'private_study': 0, 'private_preferences': 0}
    deferred_sweep_stages = []

    with ExitStack() as stack:
        conn = stack.enter_context(psycopg.connect(candidate_dsn, autocommit=True, connect_timeout=5))
        stack.enter_context(conn.transaction())
        conn.execute('SET LOCAL search_path=pg_catalog')
        conn.execute("SET LOCAL TimeZone='UTC'")
        conn.execute("SET LOCAL DateStyle='ISO, YMD'")
        conn.execute("SET LOCAL statement_timeout='30s'")
        conn.execute("SET LOCAL lock_timeout='2s'")
        # Fail closed if protected hold table or 0134 schema is unavailable.
        conn.execute('SELECT 1 FROM public.account_study_history_holds LIMIT 0')
        conn.execute('SELECT private_preferences_purged_at FROM public.users LIMIT 0')

        # Quarantine guard: refuse to write if any active non-revoked session exists.
        live_web = conn.execute('SELECT count(*) FROM public.auth_sessions WHERE revoked_at IS NULL AND expires_at > clock_timestamp()').fetchone()[0]
        live_mobile = conn.execute('SELECT count(*) FROM public.mobile_sessions WHERE revoked_at IS NULL AND expires_at > clock_timestamp()').fetchone()[0]
        if live_web > 0 or live_mobile > 0:
            raise ValueError('Candidate has active unquarantined sessions; quarantine credentials before replay')

        # 1. Replay holds first so protected accounts are never swept.
        existing_users = {
            r[0] for r in conn.execute('SELECT id FROM public.users WHERE id = ANY(%s)', (list({h['user_id'] for h in ledger['holds']} | set(closed_map.keys())),)).fetchall()
        }
        for h in ledger['holds']:
            if h['user_id'] not in existing_users:
                continue
            conn.execute('''
                INSERT INTO public.account_study_history_holds(user_id, hold_code, created_at, expires_at, released_at)
                VALUES(%s, %s, %s::timestamptz, %s::timestamptz, %s::timestamptz)
                ON CONFLICT(user_id, created_at) DO UPDATE
                SET hold_code=EXCLUDED.hold_code, expires_at=EXCLUDED.expires_at, released_at=EXCLUDED.released_at
            ''', (h['user_id'], h['hold_code'], h['created_at'], h['expires_at'], h['released_at']))
            holds_replayed += 1

        # 2. Replay unapplied closures.
        for uid, ref in closed_map.items():
            if uid not in existing_users:
                continue
            cur_closed = conn.execute('SELECT closed_at FROM public.users WHERE id=%s FOR UPDATE', (uid,)).fetchone()[0]
            if cur_closed is None:
                _replay_closure(conn, uid, ref['closed_at'])
                closures_replayed += 1

        # 3. Remove stale reopen envelopes not active in the authoritative ledger.
        stale_targets = [uid for uid in closed_map if uid in existing_users and uid not in active_reopen]
        if stale_targets:
            res = conn.execute('DELETE FROM public.account_closure_recovery WHERE user_id = ANY(%s)', (stale_targets,))
            stale_envelopes_removed = res.rowcount

        # 4. Invoke real bounded sweepers only when no non-ledger-purged account would be swept.
        stages = [
            (
                'study_history',
                'study_history_purged_at',
                'public.sweep_expired_study_history(20, 1000)',
                'a.closed_at <= clock_timestamp() - interval \'30 days\' AND a.study_history_purged_at IS NULL',
            ),
            (
                'private_study',
                'private_study_purged_at',
                'public.sweep_expired_private_study(20, 1000)',
                'a.closed_at <= clock_timestamp() - interval \'30 days\' AND a.study_history_purged_at IS NOT NULL AND a.private_study_purged_at IS NULL',
            ),
            (
                'private_preferences',
                'private_preferences_purged_at',
                'public.sweep_expired_private_preferences(20, 1000)',
                'a.closed_at <= clock_timestamp() - interval \'30 days\' AND a.study_history_purged_at IS NOT NULL AND a.private_study_purged_at IS NOT NULL AND a.private_preferences_purged_at IS NULL',
            ),
        ]
        for stage_name, col, fn_call, eligibility_sql in stages:
            want_purged = {uid for uid, ref in closed_map.items() if ref[col] is not None}
            if not want_purged:
                continue
            eligible_rows = {
                r[0] for r in conn.execute(f'''
                    SELECT a.id FROM public.users a
                    WHERE {eligibility_sql}
                      AND NOT EXISTS(SELECT 1 FROM public.account_study_history_holds h
                        WHERE h.user_id=a.id AND h.released_at IS NULL
                          AND (h.expires_at IS NULL OR h.expires_at > clock_timestamp()))
                ''').fetchall()
            }
            if not (eligible_rows & want_purged):
                continue
            if eligible_rows - want_purged:
                # Never over-delete an account not yet marked purged in the authoritative ledger.
                deferred_sweep_stages.append(stage_name)
                continue
            for _ in range(max_sweep_passes):
                out = conn.execute(f'SELECT {fn_call}').fetchone()[0]
                sweep_results[stage_name] += int(out.get('accounts_completed', 0))
                if int(out.get('accounts_scanned', 0)) == 0:
                    break

    post = verify_candidate(candidate_dsn, ledger)
    return {
        'schema': 1,
        'source': 'restore-erasure-decision-apply-v1',
        'applied_at': datetime.now(timezone.utc).isoformat(),
        'ledger_sha256': ledger['ledger_sha256'],
        'holds_replayed': holds_replayed,
        'closures_replayed': closures_replayed,
        'stale_reopen_envelopes_removed': stale_envelopes_removed,
        'sweep_accounts_completed': sweep_results,
        'deferred_sweep_stages': deferred_sweep_stages,
        'post_verify_status': post['status'],
        'post_verify_drift': post['drift'],
        'promotion_authorized': False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--export-ledger', action='store_true')
    mode.add_argument('--verify-candidate', action='store_true')
    mode.add_argument('--apply-candidate', action='store_true')
    parser.add_argument('--out', type=Path, help='Output path for --export-ledger')
    parser.add_argument('--ledger', type=Path, help='Input ledger path for verify/apply')
    parser.add_argument('--allow-isolated-candidate-write', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.export_ledger:
            ledger = export_ledger(os.environ['FINNA_RESTORE_REFERENCE_DSN'])
            if args.out:
                args.out.write_text(json.dumps(ledger, indent=2) + '\n', encoding='utf-8')
            result = {
                'schema': 1,
                'source': 'restore-erasure-decision-export-v1',
                'status': 'exported',
                'ledger_sha256': ledger['ledger_sha256'],
                'closed_accounts_count': len(ledger['closed_accounts']),
                'holds_count': len(ledger['holds']),
                'active_reopen_envelopes_count': len(ledger['active_reopen_envelope_users']),
                'promotion_authorized': False,
            }
            code = 0
        elif args.verify_candidate:
            if not args.ledger:
                raise ValueError('--ledger is required')
            ledger = json.loads(args.ledger.read_text(encoding='utf-8'))
            result = verify_candidate(os.environ['FINNA_RESTORE_CANDIDATE_DSN'], ledger)
            code = 0 if result['status'] == 'reconciled' else 2
        else:
            if not args.ledger:
                raise ValueError('--ledger is required')
            ledger = json.loads(args.ledger.read_text(encoding='utf-8'))
            result = apply_candidate(
                os.environ['FINNA_RESTORE_CANDIDATE_DSN'],
                ledger,
                allow_isolated_candidate_write=args.allow_isolated_candidate_write,
            )
            code = 0 if result['post_verify_status'] == 'reconciled' else 2
    except Exception as exc:
        # Never emit driver diagnostics, identifiers, emails, ciphertexts or DSNs.
        result = {
            'schema': 1,
            'source': 'restore-erasure-decision-replay-v1',
            'status': 'error',
            'error_kind': type(exc).__name__,
            'promotion_authorized': False,
        }
        code = 1
    result['operator_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    print(json.dumps(result, indent=2))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
