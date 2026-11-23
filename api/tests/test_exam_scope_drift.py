"""Exam scope: the three definitions must agree, and an unknown scope must fail.

Phase V.19 (§VIII.3.1). `ExamScope` was a two-valued `Literal` threaded through
~207 call sites. Nothing type-checks Python against TypeScript anywhere in this
project, so the Python allowlist and the web mirror are held together by this
test and nothing else.

The behavioural half matters more than the drift half: with an open type, an
unrecognised scope must be **rejected**, not silently served as the default.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.exam_scope import (ALL, DEFAULT_SCOPE, KNOWN_SCOPES, pool_view,
                            question_scope, scope_condition)

ROOT = Path(__file__).resolve().parents[2]


def _web_scopes() -> set[str]:
    source = (ROOT / 'web/src/lib/examScope.ts').read_text()
    block = source[source.index('KNOWN_EXAM_SCOPES = ['):]
    block = block[:block.index(']')]
    return set(re.findall(r'"([a-z-]+)"', block))


def test_python_and_web_agree_on_the_scope_list():
    assert _web_scopes() == set(KNOWN_SCOPES), (
        'api/app/exam_scope.py KNOWN_SCOPES and web/src/lib/examScope.ts '
        'KNOWN_EXAM_SCOPES have drifted; a new exam body must be added to both'
    )


def test_the_default_is_a_known_scope():
    assert DEFAULT_SCOPE in KNOWN_SCOPES
    assert ALL in KNOWN_SCOPES


def test_an_unknown_scope_is_refused_rather_than_defaulted():
    """The regression this phase exists to prevent: with an open type, a typo or a
    probe must not quietly return the Mizoram pool."""
    for bad in ('ssc', 'MIZORAM-RECRUITMENT', '', "all'; DROP TABLE papers--"):
        with pytest.raises(ValueError):
            scope_condition('p', bad)
        with pytest.raises(ValueError):
            question_scope('v', bad)
        with pytest.raises(ValueError):
            pool_view('all', bad)


def test_the_two_shipped_scopes_behave_exactly_as_before():
    """V.19 is a type change, not a behaviour change."""
    assert scope_condition('p', ALL) == 'TRUE'
    assert question_scope('v', ALL) == 'TRUE'
    assert pool_view('scorable', ALL) == 'v_scorable'

    assert scope_condition('p', 'mizoram-recruitment') == "p.exam_scope_id='mizoram-recruitment'"
    assert question_scope('v', 'mizoram-recruitment') == 'v.id IN (SELECT canonical_id FROM launch_question_ids)'
    assert pool_view('scorable', 'mizoram-recruitment') == 'v_launch_scorable'
    assert pool_view('mock_practice', 'mizoram-recruitment') == 'v_launch_mock_practice'


def test_a_registered_scope_without_launch_views_gets_a_correct_predicate():
    """`outside-mizoram` is a seeded row with no materialised views. It must filter
    by its own scope, not silently fall back to Mizoram's launch pool."""
    condition = scope_condition('p', 'outside-mizoram')
    assert condition == "p.exam_scope_id='outside-mizoram'"
    assert 'mizoram-recruitment' not in condition

    predicate = question_scope('v', 'outside-mizoram')
    assert 'launch_question_ids' not in predicate
    assert "p.exam_scope_id='outside-mizoram'" in predicate
    # Unmaterialised scopes read the global pool plus the predicate above.
    assert pool_view('scorable', 'outside-mizoram') == 'v_scorable'


def test_sql_aliases_are_still_validated():
    for bad_alias in ('p; DROP TABLE papers', 'a b', "x'"):
        with pytest.raises(ValueError):
            scope_condition(bad_alias, DEFAULT_SCOPE)
        with pytest.raises(ValueError):
            question_scope(bad_alias, DEFAULT_SCOPE)


def test_no_scope_value_reaching_sql_comes_from_outside_the_allowlist():
    """Every interpolated scope is a member of KNOWN_SCOPES, which is what makes
    building these strings safe."""
    for scope in KNOWN_SCOPES:
        for fragment in (scope_condition('p', scope), question_scope('v', scope)):
            quoted = re.findall(r"'([^']*)'", fragment)
            assert all(value in KNOWN_SCOPES for value in quoted), fragment
