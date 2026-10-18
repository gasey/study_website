from datetime import datetime
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


class CollectionSummary(BaseModel):
    id: str
    title: str
    kind: str
    route: str | None = None
    visibility: str
    sections: int
    #: Counted from v_scorable, so a collection never advertises questions
    #: that mocks are not permitted to score.
    scorable: int


class CollectionSection(BaseModel):
    path: str
    title: str
    position: int
    formats: list[str] = Field(default_factory=list)
    papers: int
    scorable: int


class CollectionDetail(CollectionSummary):
    section_list: list[CollectionSection] = Field(default_factory=list)


class MockStart(BaseModel):
    collection_id: str
    section_path: str | None = None
    count: int = Field(20, ge=1, le=200)
    duration_minutes: int = Field(20, ge=1, le=240)
    marks_correct: float = Field(1, ge=0, le=10)
    #: Deduction per wrong answer. 0 = no negative marking, which is what
    #: several Mizoram PSC papers actually use.
    marks_wrong: float = Field(0, ge=0, le=10)


class MockQuestion(BaseModel):
    id: str
    position: int
    question: str
    options: list[str]
    # No answer field, deliberately: the key is revealed only by submit.


class MockSession(BaseModel):
    id: str
    collection_id: str
    section_path: str | None = None
    duration_seconds: int
    started_at: datetime
    #: Computed server-side. The client counts down from this for display,
    #: but the server recomputes elapsed time on submit regardless.
    seconds_remaining: int
    questions: list[MockQuestion]


class MockAnswer(BaseModel):
    question_id: str
    chosen_index: int = Field(ge=0, le=9)


class MockSubmission(BaseModel):
    answers: list[MockAnswer] = Field(default_factory=list)


class MockReviewRow(BaseModel):
    position: int
    question_id: str
    question: str
    chosen_text: str | None
    answer_text: str | None
    correct: bool
    explanation: str | None = None


class MockResult(BaseModel):
    id: str
    n_correct: int
    n_wrong: int
    n_skipped: int
    score: float
    total: int
    elapsed_seconds: int
    #: Submitted after the window closed. Recorded, not rejected.
    late: bool
    review: list[MockReviewRow]


class MockSummary(BaseModel):
    id: str
    collection_id: str
    collection_title: str
    section_path: str | None = None
    total: int
    n_correct: int | None = None
    n_wrong: int | None = None
    n_skipped: int | None = None
    score: float | None = None
    elapsed_seconds: int | None = None
    late: bool
    started_at: datetime
    #: None while the paper is still open.
    submitted_at: datetime | None = None


class Mistake(BaseModel):
    id: str
    question: str
    options: list[str]
    answer_text: str | None
    chosen_text: str | None
    explanation: str | None = None
    #: How many times this device has got it wrong in total, which is a
    #: better signal of a weak spot than a single miss.
    times_wrong: int
    last_attempt: datetime


class ScoringFacts(BaseModel):
    total: int
    scorable: int
    practice: int
    #: answer_source = 'official'
    official: int
    #: answer_source = 'key' — a key transcribed from the paper rather than
    #: published by the commission. Named for the UI label, not the column.
    transcribed: int
    #: Same option text printed twice, so the answer cannot be identified.
    dup_defect: int
