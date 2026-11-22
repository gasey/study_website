"""Separate private draft/saved-link cleanup with the existing closure holds."""
from uuid import uuid4

import psycopg
import pytest

from app.config import settings
from app.services import account_retention
from test_account_study_history_retention import closed_user, run

TABLES = ('essay_drafts', 'user_question_bookmarks', 'material_bookmarks', 'user_calendar_saved')


@pytest.fixture
def sample(client, database):
    conn = database[1]
    with conn.transaction(force_rollback=True):
        users = ['private-' + uuid4().hex for _ in range(2)]
        for user in users:
            conn.execute('INSERT INTO users(id,handle) VALUES(%s,%s)', (user, user))
        questions = ['private-q-' + uuid4().hex for _ in range(3)]
        for question in questions:
            conn.execute("INSERT INTO canonical_questions(id,type,question,answer_source) VALUES(%s,'descriptive','Synthetic private writing prompt','derived')", (question,))
        events = ['private-event-' + uuid4().hex for _ in range(3)]
        for event in events:
            conn.execute("INSERT INTO exam_calendar_events(id,title,kind,source_url,source_reference,verification_note,verified_on,created_by,updated_by) VALUES(%s,'Synthetic calendar event','notification','https://example.test','synthetic','synthetic',current_date,%s,%s)", (event, users[1], users[1]))
        for user in users:
            for question in questions:
                conn.execute("INSERT INTO essay_drafts(user_id,canonical_id,body) VALUES(%s,%s,'Synthetic private draft')", (user, question))
                conn.execute('INSERT INTO user_question_bookmarks(user_id,question_id) VALUES(%s,%s)', (user, question))
            conn.execute("INSERT INTO material_bookmarks(user_id,material_id) VALUES(%s,'cms-paid-demo')", (user,))
            for event in events:
                conn.execute('INSERT INTO user_calendar_saved(user_id,event_id) VALUES(%s,%s)', (user, event))
        yield conn, users, questions, events


def close(conn, user, days=31, base_done=True):
    conn.execute("UPDATE users SET closed_at=clock_timestamp()-(%s||' days')::interval,handle=%s,contribution_public=false,study_history_purged_at=CASE WHEN %s THEN clock_timestamp() ELSE NULL END WHERE id=%s", (days, 'deleted-' + uuid4().hex, base_done, user))


def sweep(conn, accounts=20, batch=200):
    with conn.transaction():
        conn.execute('SET LOCAL ROLE mpsc')
        result = conn.execute('SELECT sweep_expired_private_study(%s,%s)', (accounts, batch)).fetchone()[0]
        conn.execute('RESET ROLE')
        return result


def counts(conn, user):
    return {table: conn.execute('SELECT count(*) FROM ' + table + ' WHERE user_id=%s', (user,)).fetchone()[0] for table in TABLES}


def test_only_expired_owners_private_rows_are_removed_and_shared_sources_survive(sample):
    conn, (user, other), questions, events = sample
    expected_other = counts(conn, other)
    shared_before = conn.execute("SELECT to_jsonb(m) FROM materials m WHERE id='cms-paid-demo'").fetchone()
    close(conn, user)
    result = sweep(conn)
    assert result == {'accounts_scanned': 1, 'accounts_completed': 1, 'rows_removed': 10}
    assert not any(counts(conn, user).values())
    assert counts(conn, other) == expected_other
    assert conn.execute('SELECT count(*) FROM canonical_questions WHERE id=ANY(%s)', (questions,)).fetchone()[0] == 3
    assert conn.execute('SELECT count(*) FROM exam_calendar_events WHERE id=ANY(%s)', (events,)).fetchone()[0] == 3
    assert conn.execute("SELECT to_jsonb(m) FROM materials m WHERE id='cms-paid-demo'").fetchone() == shared_before
    assert conn.execute('SELECT private_study_purged_at IS NOT NULL FROM users WHERE id=%s', (user,)).fetchone()[0]
    assert sweep(conn)['accounts_scanned'] == 0
    assert conn.execute("SELECT detail FROM account_security_events WHERE user_id=%s AND action='closed_private_study_purged'", (user,)).fetchall() == [({'policy': 'private-study-extras-v1'},)]


@pytest.mark.parametrize('hold', ['legal', 'dispute', 'security', 'manual_review'])
def test_every_active_hold_pauses_private_rows_until_release(sample, hold):
    conn, (user, _), _, _ = sample
    close(conn, user)
    conn.execute('INSERT INTO account_study_history_holds(user_id,hold_code) VALUES(%s,%s)', (user, hold))
    before = counts(conn, user)
    assert sweep(conn)['accounts_scanned'] == 0
    assert counts(conn, user) == before
    conn.execute('UPDATE account_study_history_holds SET released_at=clock_timestamp() WHERE user_id=%s', (user,))
    assert sweep(conn)['accounts_completed'] == 1


@pytest.mark.parametrize('state', ['active', 'grace', 'reopened', 'base-pending'])
def test_ineligible_accounts_keep_every_private_row(sample, state):
    conn, (user, _), _, _ = sample
    if state != 'active':
        close(conn, user, days=29 if state == 'grace' else 31, base_done=state != 'base-pending')
    if state == 'reopened':
        conn.execute('UPDATE users SET closed_at=NULL WHERE id=%s', (user,))
    before = counts(conn, user)
    assert sweep(conn)['accounts_scanned'] == 0
    assert counts(conn, user) == before


def test_small_batches_do_not_mark_completion_early(sample):
    conn, (user, _), _, _ = sample
    close(conn, user)
    first = sweep(conn, 1, 1)
    assert first == {'accounts_scanned': 1, 'accounts_completed': 0, 'rows_removed': 4}
    assert conn.execute('SELECT private_study_purged_at FROM users WHERE id=%s', (user,)).fetchone() == (None,)
    assert sweep(conn, 1, 1)['accounts_completed'] == 0
    assert sweep(conn, 1, 1)['accounts_completed'] == 1


def test_expired_hold_allows_cleanup(sample):
    conn, (user, _), _, _ = sample
    close(conn, user)
    conn.execute("INSERT INTO account_study_history_holds(user_id,hold_code,created_at,expires_at) VALUES(%s,'dispute',now()-interval '2 days',now()-interval '1 day')", (user,))
    assert sweep(conn)['accounts_completed'] == 1


@pytest.mark.parametrize('table', TABLES)
def test_stale_insert_cannot_recreate_data_after_completion(sample, table):
    conn, (user, _), questions, events = sample
    close(conn, user)
    assert sweep(conn)['accounts_completed'] == 1
    statements = {
        'essay_drafts': ('INSERT INTO essay_drafts(user_id,canonical_id) VALUES(%s,%s)', questions[0]),
        'user_question_bookmarks': ('INSERT INTO user_question_bookmarks(user_id,question_id) VALUES(%s,%s)', questions[0]),
        'material_bookmarks': ('INSERT INTO material_bookmarks(user_id,material_id) VALUES(%s,%s)', 'cms-paid-demo'),
        'user_calendar_saved': ('INSERT INTO user_calendar_saved(user_id,event_id) VALUES(%s,%s)', events[0]),
    }
    statement, source = statements[table]
    with pytest.raises(psycopg.Error, match='Account is closed'):
        with conn.transaction():
            conn.execute(statement, (user, source))


@pytest.mark.parametrize('accounts,batch', [(0, 1), (21, 1), (1, 0), (1, 1001), (None, 1), (1, None)])
def test_invalid_cleanup_bounds_are_rejected(sample, accounts, batch):
    with pytest.raises(psycopg.Error, match='Invalid private-study cleanup bounds'):
        with sample[0].transaction():
            sweep(sample[0], accounts, batch)


@pytest.mark.parametrize('table', TABLES)
def test_closed_account_cannot_recreate_or_update_private_rows(sample, table):
    conn, (user, _), _, _ = sample
    close(conn, user)
    with conn.transaction():
        with pytest.raises(psycopg.Error, match='Account is closed'):
            with conn.transaction():
                conn.execute('UPDATE ' + table + ' SET user_id=user_id WHERE user_id=%s', (user,))


def test_application_cannot_forge_private_cleanup_completion(sample):
    conn, (user, _), _, _ = sample
    close(conn, user)
    with conn.transaction():
        conn.execute('SET LOCAL ROLE mpsc')
        with pytest.raises(psycopg.Error, match='completion is operator managed'):
            with conn.transaction():
                conn.execute('UPDATE users SET private_study_purged_at=now() WHERE id=%s', (user,))


def test_application_cannot_premark_a_new_account_as_already_cleaned(client, database):
    conn = database[1]
    user = 'forged-' + uuid4().hex
    with conn.transaction(force_rollback=True):
        conn.execute('SET LOCAL ROLE mpsc')
        with pytest.raises(psycopg.Error, match='completion is operator managed'):
            with conn.transaction():
                conn.execute('INSERT INTO users(id,handle,private_study_purged_at) VALUES(%s,%s,now())', (user, user))
        conn.execute('INSERT INTO users(id,handle) VALUES(%s,%s)', (user, user))
        assert conn.execute('SELECT private_study_purged_at FROM users WHERE id=%s', (user,)).fetchone() == (None,)


@pytest.mark.parametrize('base,private', [(False, False), (False, True), (True, False), (True, True)])
def test_worker_requires_both_explicit_flags(client, database, monkeypatch, base, private):
    conn = database[1]
    user = closed_user(conn)
    monkeypatch.setattr(settings, 'study_history_retention_enabled', base)
    monkeypatch.setattr(settings, 'private_study_retention_enabled', private)
    result = run(client, account_retention.sweep)
    if base and private:
        assert result['private_study']['accounts_completed'] >= 1
        assert conn.execute('SELECT private_study_purged_at IS NOT NULL FROM users WHERE id=%s', (user,)).fetchone()[0]
    else:
        assert result['private_study'] == 'disabled'
        assert conn.execute('SELECT private_study_purged_at FROM users WHERE id=%s', (user,)).fetchone() == (None,)


def test_locked_account_is_skipped_and_completes_after_unlock(client, database):
    conn = database[1]
    user = closed_user(conn)
    conn.execute('UPDATE users SET study_history_purged_at=clock_timestamp() WHERE id=%s', (user,))
    with psycopg.connect('dbname=' + database[0]) as competitor:
        competitor.execute('SELECT id FROM users WHERE id=%s FOR UPDATE', (user,))
        sweep(conn)
        assert conn.execute('SELECT private_study_purged_at FROM users WHERE id=%s', (user,)).fetchone() == (None,)
    sweep(conn)
    assert conn.execute('SELECT private_study_purged_at IS NOT NULL FROM users WHERE id=%s', (user,)).fetchone()[0]
