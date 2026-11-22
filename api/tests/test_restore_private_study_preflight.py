"""The supplemental restore gate detects private records and completion drift."""
import importlib.util
import json
from pathlib import Path

import pytest

from test_restore_retention_preflight import reference, copy  # noqa: F401

spec = importlib.util.spec_from_file_location('private_study_reader', Path(__file__).resolve().parents[2] / 'scripts/check-restore-private-study.py')
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


@pytest.fixture
def private_reference(reference):
    conn = reference[1]
    conn.execute("INSERT INTO users(id,handle) VALUES('private-subject','private-subject')")
    conn.execute("INSERT INTO canonical_questions(id,type,question,answer_source) VALUES('private-prompt','descriptive','Synthetic prompt','derived')")
    conn.execute("INSERT INTO essay_drafts(user_id,canonical_id,body) VALUES('private-subject','private-prompt','synthetic private body')")
    conn.execute("INSERT INTO user_question_bookmarks(user_id,question_id) VALUES('private-subject','private-prompt')")
    conn.execute("INSERT INTO material_bookmarks(user_id,material_id) VALUES('private-subject','cms-paid-demo')")
    conn.execute("INSERT INTO exam_calendar_events(id,title,kind,source_url,source_reference,verification_note,verified_on) VALUES('private-event','Synthetic event','notification','https://example.test','synthetic','synthetic',current_date)")
    conn.execute("INSERT INTO user_calendar_saved(user_id,event_id) VALUES('private-subject','private-event')")
    yield reference


def test_all_seven_controls_match_without_exporting_private_body(private_reference):
    with copy(private_reference) as (_, dsn):
        result = preflight.compare('dbname=' + private_reference[0], dsn)
    assert result['status'] == 'checks_passed' and len(result['matched_control_tables']) == 7
    assert 'synthetic private body' not in json.dumps(result)
    assert not result['promotion_authorized']


@pytest.mark.parametrize('change,table', [
    ('DELETE FROM essay_drafts', 'essay_drafts'),
    ("UPDATE essay_drafts SET body='a different private draft'", 'essay_drafts'),
    ('DELETE FROM user_question_bookmarks', 'user_question_bookmarks'),
    ('DELETE FROM material_bookmarks', 'material_bookmarks'),
    ('DELETE FROM user_calendar_saved', 'user_calendar_saved'),
    ("UPDATE users SET private_study_purged_at=now() WHERE id='private-subject'", 'users'),
    ('UPDATE account_study_history_holds SET released_at=now()', 'account_study_history_holds'),
])
def test_private_record_or_decision_drift_blocks_restore(private_reference, change, table):
    with copy(private_reference) as (conn, dsn):
        conn.execute(change)
        result = preflight.compare('dbname=' + private_reference[0], dsn)
    assert result['status'] == 'blocked'
    assert [x['table'] for x in result['control_mismatches']] == [table]


def test_missing_0133_schema_fails_closed_with_redacted_output(private_reference, monkeypatch, capsys):
    with copy(private_reference) as (conn, dsn):
        conn.execute('ALTER TABLE users DROP COLUMN private_study_purged_at CASCADE')
        monkeypatch.setenv('FINNA_RESTORE_REFERENCE_DSN', 'dbname=' + private_reference[0])
        monkeypatch.setenv('FINNA_RESTORE_CANDIDATE_DSN', dsn)
        assert preflight.main(['--run']) == 1
        output = capsys.readouterr().out
    result = json.loads(output)
    assert result['status'] == 'error' and result['error_kind'] == 'UndefinedColumn'
    assert 'synthetic private body' not in output and private_reference[0] not in output
