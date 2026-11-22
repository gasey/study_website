"""Isolated PostgreSQL tests for authoritative closure/hold/erasure decision replay."""
import importlib.util
import json
from pathlib import Path

import pytest

from test_restore_retention_preflight import reference, copy  # noqa: F401

spec = importlib.util.spec_from_file_location(
    'erasure_replay_operator',
    Path(__file__).resolve().parents[2] / 'scripts/replay-restore-erasure-decisions.py',
)
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


@pytest.fixture
def replay_reference(reference):
    conn = reference[1]
    # Active open user (will be closed in reference after snapshot copy).
    conn.execute("INSERT INTO users(id,handle,email) VALUES('u-open','u-open','secret-open@example.test')")
    # Expired closed user with private study & preference rows to be purged in reference.
    conn.execute("INSERT INTO users(id,handle,email) VALUES('u-purged','u-purged','secret-purged@example.test')")
    conn.execute("INSERT INTO canonical_questions(id,type,question,answer_source) VALUES('q-replay','descriptive','Prompt','derived')")
    conn.execute("INSERT INTO essay_drafts(user_id,canonical_id,body) VALUES('u-purged','q-replay','super-secret-essay-text')")
    conn.execute('INSERT INTO user_calendar_preferences(user_id,reminders) VALUES(%s,true)', ('u-purged',))
    conn.execute("INSERT INTO game_preferences(user_id,selection) VALUES('u-purged','{\"mode\":\"rapid\"}'::jsonb)")
    # Held closed user whose hold must survive replay.
    conn.execute("INSERT INTO users(id,handle,email) VALUES('u-held','u-held','secret-held@example.test')")
    conn.execute("INSERT INTO essay_drafts(user_id,canonical_id,body) VALUES('u-held','q-replay','held-essay-text')")
    yield reference


def test_export_ledger_has_zero_pii_and_detects_tampering(replay_reference):
    conn = replay_reference[1]
    conn.execute("UPDATE users SET closed_at=clock_timestamp()-interval '40 days',email=NULL,handle='deleted-1',contribution_public=false WHERE id='u-purged'")
    conn.execute("INSERT INTO account_study_history_holds(user_id,hold_code) VALUES('u-held','legal')")
    ledger = replay.export_ledger('dbname=' + replay_reference[0])
    raw = json.dumps(ledger)
    assert 'secret-open@example.test' not in raw
    assert 'super-secret-essay-text' not in raw
    assert 'held-essay-text' not in raw
    assert {x['user_id'] for x in ledger['closed_accounts']} >= {'u-purged'}
    assert {x['user_id'] for x in ledger['holds']} >= {'u-held'}
    assert replay.verify_ledger_integrity(ledger) is ledger
    # Tampering breaks SHA-256 verification.
    tampered = json.loads(raw)
    tampered['holds'][0]['hold_code'] = 'dispute'
    with pytest.raises(ValueError):
        replay.verify_ledger_integrity(tampered)


def test_apply_refuses_unquarantined_candidate_with_active_session(replay_reference):
    with copy(replay_reference) as (cand_conn, cand_dsn):
        cand_conn.execute(
            "INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES(%s,'u-open',clock_timestamp()+interval '1 day')",
            ('a' * 64,),
        )
        ledger = replay.export_ledger('dbname=' + replay_reference[0])
        with pytest.raises(ValueError, match='unquarantined'):
            replay.apply_candidate(cand_dsn, ledger, allow_isolated_candidate_write=True)


def test_replay_reconciles_closures_holds_and_real_sweeps_on_isolated_candidate(replay_reference):
    # Take older backup candidate BEFORE reference closes/holds/purges accounts.
    with copy(replay_reference) as (cand_conn, cand_dsn):
        ref_conn = replay_reference[1]
        # Advance reference: close u-open, hold+close u-held, close+sweep u-purged across 0131 -> 0133 -> 0134.
        ref_conn.execute("UPDATE users SET closed_at=clock_timestamp()-interval '5 days',email=NULL,handle='deleted-open',contribution_public=false WHERE id='u-open'")
        ref_conn.execute("UPDATE users SET closed_at=clock_timestamp()-interval '40 days',email=NULL,handle='deleted-held',contribution_public=false WHERE id='u-held'")
        ref_conn.execute("INSERT INTO account_study_history_holds(user_id,hold_code) VALUES('u-held','legal')")
        ref_conn.execute("UPDATE users SET closed_at=clock_timestamp()-interval '40 days',email=NULL,handle='deleted-purged',contribution_public=false WHERE id='u-purged'")
        assert ref_conn.execute('SELECT sweep_expired_study_history(20, 200)').fetchone()[0]['accounts_completed'] == 1
        assert ref_conn.execute('SELECT sweep_expired_private_study(20, 200)').fetchone()[0]['accounts_completed'] == 1
        assert ref_conn.execute('SELECT sweep_expired_private_preferences(20, 200)').fetchone()[0]['accounts_completed'] == 1

        ledger = replay.export_ledger('dbname=' + replay_reference[0])

        # Verify detects exact drift on older candidate.
        before = replay.verify_candidate(cand_dsn, ledger)
        assert before['status'] == 'drift_detected'
        assert before['drift']['unapplied_closures'] == 3
        assert before['drift']['missing_holds'] == 1
        assert before['drift']['unapplied_base_purges'] == 1
        assert before['drift']['unapplied_private_study_purges'] == 1
        assert before['drift']['unapplied_private_preferences_purges'] == 1
        assert not before['promotion_authorized']

        # Apply requires explicit opt-in flag.
        with pytest.raises(ValueError):
            replay.apply_candidate(cand_dsn, ledger, allow_isolated_candidate_write=False)

        # Apply on quarantined candidate replays holds, closures, and real sweepers.
        applied = replay.apply_candidate(cand_dsn, ledger, allow_isolated_candidate_write=True)
        assert applied['holds_replayed'] == 2
        assert applied['closures_replayed'] == 3
        assert applied['sweep_accounts_completed'] == {'study_history': 1, 'private_study': 1, 'private_preferences': 1}
        assert applied['post_verify_status'] == 'reconciled'
        assert applied['promotion_authorized'] is False

        # Verify held user's essay draft survived while purged user's essay & preferences were genuinely deleted.
        assert cand_conn.execute("SELECT count(*) FROM essay_drafts WHERE user_id='u-held'").fetchone()[0] == 1
        assert cand_conn.execute("SELECT count(*) FROM essay_drafts WHERE user_id='u-purged'").fetchone()[0] == 0
        assert cand_conn.execute("SELECT count(*) FROM user_calendar_preferences WHERE user_id='u-purged'").fetchone()[0] == 0
        assert cand_conn.execute("SELECT count(*) FROM game_preferences WHERE user_id='u-purged'").fetchone()[0] == 0
        assert cand_conn.execute("SELECT email,closed_at IS NOT NULL FROM users WHERE id='u-open'").fetchone() == (None, True)


def test_cli_export_verify_and_missing_0134_fails_closed(replay_reference, tmp_path, monkeypatch, capsys):
    ledger_path = tmp_path / 'ledger.json'
    monkeypatch.setenv('FINNA_RESTORE_REFERENCE_DSN', 'dbname=' + replay_reference[0])
    assert replay.main(['--export-ledger', '--out', str(ledger_path)]) == 0
    exported_out = json.loads(capsys.readouterr().out)
    assert exported_out['status'] == 'exported' and not exported_out['promotion_authorized']

    with copy(replay_reference) as (cand_conn, cand_dsn):
        monkeypatch.setenv('FINNA_RESTORE_CANDIDATE_DSN', cand_dsn)
        assert replay.main(['--verify-candidate', '--ledger', str(ledger_path)]) == 0
        verify_out = json.loads(capsys.readouterr().out)
        assert verify_out['status'] == 'reconciled'

        # Dropping 0134 column fails closed with redacted output.
        cand_conn.execute('ALTER TABLE users DROP COLUMN private_preferences_purged_at CASCADE')
        assert replay.main(['--verify-candidate', '--ledger', str(ledger_path)]) == 1
        err_raw = capsys.readouterr().out
        err = json.loads(err_raw)
        assert err['status'] == 'error' and err['error_kind'] == 'UndefinedColumn'
        assert replay_reference[0] not in err_raw
