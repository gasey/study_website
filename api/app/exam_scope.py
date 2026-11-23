"""Explicit learner exam-source filters. Never interpolate client text as SQL.

Phase V.19 (§VIII.3.1). This was `Literal["mizoram-recruitment", "all"]` — a
two-valued type threaded through ~207 call sites. Every month it survived, more
code got written against the assumption that there are exactly two scopes, and
§0.10 rule 1 ("exam identity is data, never schema or code branches") quietly
became harder to keep. Widening it is twenty lines now and a 207-call-site change
later, so it happens now, before a second exam body exists.

What this does **not** do: make a third exam system work end to end. That is V.24
and it is data work (`exam_scopes` rows, `exam_syllabus`, the lens cascade). What
it does is make the type open, make an unknown scope **fail loudly** rather than
silently behave as Mizoram, and give a registered scope without materialised
launch views a correct — if unoptimised — predicate instead of a wrong one.

The scope reaching SQL is always a member of `KNOWN_SCOPES`, never client text.
"""
from typing import Annotated

from pydantic import AfterValidator

#: Pseudo-scope meaning "do not filter by exam source at all".
ALL = "all"

#: The seeded rows of `exam_scopes` (migration 0046), plus `ALL`. Held here rather
#: than read from the database because these functions are synchronous and build
#: SQL: the allowlist is what makes the interpolation below safe. A new exam body
#: adds its id here **and** to `web/src/lib/examScope.ts`;
#: `test_exam_scope_drift.py` fails if the two disagree.
KNOWN_SCOPES = frozenset({ALL, "mizoram-recruitment", "outside-mizoram"})

#: Scopes with pre-materialised launch views (migration 0046). Any other
#: registered scope is served by an explicit predicate instead — correct, just not
#: pre-computed. Materialising a view for a new scope is a V.24 optimisation.
_LAUNCH_VIEW_SCOPES = frozenset({"mizoram-recruitment"})

DEFAULT_SCOPE = "mizoram-recruitment"

_POOLS = {"all": "v_all_questions", "practice": "v_practice",
          "scorable": "v_scorable", "mock_practice": "v_mock_practice"}
_LAUNCH_POOLS = {"all": "v_launch_all", "practice": "v_launch_practice",
                 "scorable": "v_launch_scorable", "mock_practice": "v_launch_mock_practice"}


def _known_scope(value: str) -> str:
    # Rejected at the request boundary, so an unrecognised scope can never reach
    # SQL and be silently treated as the default.
    if value not in KNOWN_SCOPES:
        raise ValueError("Unknown exam scope")
    return value


ExamScope = Annotated[str, AfterValidator(_known_scope)]


def _check(alias: str, exam_scope: str) -> None:
    # Aliases are internal source literals, not request arguments.
    if not alias.replace("_", "").isalnum():
        raise ValueError("Invalid internal SQL alias")
    if exam_scope not in KNOWN_SCOPES:
        raise ValueError("Unknown exam scope")


def pool_view(pool: str, exam_scope: ExamScope) -> str:
    if exam_scope not in KNOWN_SCOPES:
        raise ValueError("Unknown exam scope")
    if exam_scope == ALL:
        return _POOLS[pool]
    if exam_scope in _LAUNCH_VIEW_SCOPES:
        return _LAUNCH_POOLS[pool]
    # Registered but not materialised: callers pair this with question_scope(),
    # which supplies the per-scope predicate.
    return _POOLS[pool]


def scope_condition(alias: str, exam_scope: ExamScope) -> str:
    _check(alias, exam_scope)
    if exam_scope == ALL:
        return "TRUE"
    return alias + ".exam_scope_id='" + exam_scope + "'"


def question_scope(alias: str, exam_scope: ExamScope) -> str:
    _check(alias, exam_scope)
    if exam_scope == ALL:
        return "TRUE"
    if exam_scope in _LAUNCH_VIEW_SCOPES:
        return alias + ".id IN (SELECT canonical_id FROM launch_question_ids)"
    return (alias + ".id IN (SELECT a.canonical_id FROM appearances a"
            " JOIN papers p ON p.id=a.paper_id WHERE p.exam_scope_id='" + exam_scope + "')")
