"""Explicit learner exam-source filters. Never interpolate client text as SQL."""
from typing import Literal

ExamScope = Literal["mizoram-recruitment", "all"]
DEFAULT_SCOPE = "mizoram-recruitment"

def pool_view(pool: str, exam_scope: ExamScope) -> str:
    views = {"all":"v_all_questions", "practice":"v_practice", "scorable":"v_scorable", "mock_practice":"v_mock_practice"}
    view = views[pool]
    return view if exam_scope == "all" else {"all":"v_launch_all", "practice":"v_launch_practice", "scorable":"v_launch_scorable", "mock_practice":"v_launch_mock_practice"}[pool]

def scope_condition(alias: str, exam_scope: ExamScope) -> str:
    # Aliases are internal source literals, not request arguments.
    if not alias.replace("_", "").isalnum():
        raise ValueError("Invalid internal SQL alias")
    return "TRUE" if exam_scope == "all" else alias + ".exam_scope_id='mizoram-recruitment'"

def question_scope(alias: str, exam_scope: ExamScope) -> str:
    if not alias.replace("_", "").isalnum():
        raise ValueError("Invalid internal SQL alias")
    return "TRUE" if exam_scope == "all" else alias + ".id IN (SELECT canonical_id FROM launch_question_ids)"
