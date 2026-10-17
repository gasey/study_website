from typing import Literal

from pydantic import BaseModel, Field

# Answers are deliberately absent from every GET model below. The client
# receives the correct option only after it posts an answer, via AnswerResult.
# Shipping answer_text with the question would make the answer-before-reveal
# gate decorative — anyone could read it out of the network tab.


class Appearance(BaseModel):
    """One printing of a question in a paper."""

    paper_id: str
    year: int | None = None
    exam: str | None = None
    paper: str | None = None
    qnum: str | None = None
    page: int | None = None
    series: str | None = None


class QuestionBase(BaseModel):
    id: str
    type: str
    question: str
    options: list[str]
    subject: str | None = None
    topic: str | None = None
    difficulty: str | None = None

    answer_source: str
    #: True only for 'official'/'key'. The UI must label everything else as
    #: unverified — see rule 1 in CLAUDE.md.
    verified: bool
    #: Set when the same option text appears twice, so the answer cannot be
    #: identified by text. Such questions are excluded from scored play.
    source_defect: str | None = None

    times_asked: int
    first_year: int | None = None
    last_year: int | None = None


class QuestionListItem(QuestionBase):
    pass


class QuestionDetail(QuestionBase):
    appearances: list[Appearance] = Field(default_factory=list)


class QuestionPage(BaseModel):
    items: list[QuestionListItem]
    total: int
    limit: int
    offset: int


class AnswerSubmission(BaseModel):
    chosen_index: int = Field(ge=0, le=9)
    #: Where the answer was given. Only 'mock', 'duel' and 'cup' are scored
    #: competitively, and those draw from v_scorable, so an inferred answer
    #: can never reach them.
    context: Literal["practice", "mock", "duel", "cup", "review", "material"] = "practice"


class AnswerResult(BaseModel):
    correct: bool
    answer_index: int
    answer_text: str
    answer_source: str
    verified: bool
    explanation: str | None = None


class Progress(BaseModel):
    answered: int
    correct: int
    #: Distinct questions seen, which differs from `answered` once a question
    #: has been retried.
    unique_questions: int
