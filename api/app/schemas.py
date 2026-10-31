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
    section_label: str | None = None
    paper_label: str | None = None  # Source-verified heading, not learning taxonomy.
    year: int | None = None
    exam: str | None = None
    paper: str | None = None
    qnum: str | None = None
    page: int | None = None
    series: str | None = None
    source_pdf_url: str | None = None
    figure_image_url: str | None = None
    direction: str | None = None
    question_markup: str | None = None
    options_markup: list[str | None] | None = None


class QuestionBase(BaseModel):
    id: str
    type: str
    question: str
    direction: str | None = None
    question_markup: str | None = None
    options_markup: list[str | None] | None = None
    passage: str | None = None
    # Some source scans omit one or more option strings. Keep the question
    # browsable while the client renders those positions as unavailable.
    options: list[str | None]
    subject: str | None = None
    topic: str | None = None
    # Deprecated compatibility field; never used for labels, filters or scoring.
    difficulty: str | None = Field(default=None, deprecated=True)
    taxonomy_subject_id: str | None = None
    taxonomy_subject: str | None = None
    taxonomy_topic_id: str | None = None
    taxonomy_topic: str | None = None
    taxonomy_subtopic_id: str | None = None
    taxonomy_subtopic: str | None = None
    classification_status: Literal["pending", "approved"] | None = None

    answer_source: str
    reviewed_derived: bool = False
    held: bool = False
    answer_status: Literal["official","verified","needs-review","unsolved","written"] | None = None
    #: True only for 'official'/'key'. The UI must label everything else as
    #: unverified — see rule 1 in CLAUDE.md.
    verified: bool
    #: Set when the same option text appears twice, so the answer cannot be
    #: identified by text. Such questions are excluded from scored play.
    source_defect: str | None = None
    #: The Commission's final key conflicts with the reviewed answer. Keep the
    #: derived answer usable in practice, but surface the conflict to learners.
    key_disputed: bool = False
    dispute_note: str | None = None

    times_asked: int
    first_year: int | None = None
    last_year: int | None = None
    figure_image_url: str | None = None
    has_diagram: bool = False


class QuestionListItem(QuestionBase):
    taxonomy_paths: list[dict] = Field(default_factory=list)
    # One representative printing, or the requested paper's printing. The
    # complete appearance list remains available on the detail endpoint.
    source_appearance: Appearance | None = None


class QuestionDetail(QuestionBase):
    appearances: list[Appearance] = Field(default_factory=list)


class QuestionPage(BaseModel):
    items: list[QuestionListItem]
    total: int
    limit: int
    offset: int


class QuestionPaperSummary(BaseModel):
    id: str
    exam: str | None = None
    exam_type: str
    year: int | None = None
    month: str | None = None
    paper_number: str | None = None
    source_file: str | None = None
    source_pdf_url: str | None = None
    questions: int
    answered: int
    scorable: int


class QuestionPaperPage(BaseModel):
    items: list[QuestionPaperSummary]
    total: int
    limit: int
    offset: int


class TaxonomyFacet(BaseModel):
    subject_questions: int | None = None
    subject_id: str
    subject: str
    topic_id: str | None = None
    topic: str | None = None
    questions: int


class AnswerSubmission(BaseModel):
    chosen_index: int = Field(ge=0, le=9)
    #: Where the answer was given. Only 'mock', 'duel' and 'cup' are scored
    #: competitively, and those draw from v_scorable, so an inferred answer
    #: can never reach them.
    context: Literal["practice", "mock", "duel", "cup", "review", "material"] = "practice"
    collection_id: str | None = Field(default=None, min_length=2, max_length=80)
    paper_id: str | None = Field(default=None, min_length=2, max_length=500)
    section_path: str | None = Field(default=None, min_length=2, max_length=160)


class AnswerResult(BaseModel):
    reward: dict | None = None
    correct: bool
    answer_index: int
    answer_text: str
    answer_source: str
    verified: bool
    explanation: str | None = None


class DailyActivity(BaseModel):
    day: str
    answered: int
    correct: int


class SubjectProgress(BaseModel):
    subject_id: str
    subject: str
    answered: int
    correct: int
    unique_questions: int


class ScopeProgress(BaseModel):
    scope_id: str
    label: str
    answered: int
    correct: int
    unique_questions: int
    accuracy: float = 0


class Progress(BaseModel):
    answered: int
    correct: int
    #: Distinct questions seen, which differs from `answered` once a question
    #: has been retried.
    unique_questions: int
    accuracy: float = 0
    current_streak: int = 0
    active_days_30: int = 0
    last_active_at: datetime | None = None
    daily_activity: list[DailyActivity] = Field(default_factory=list)
    subjects: list[SubjectProgress] = Field(default_factory=list)
    collections: list[ScopeProgress] = Field(default_factory=list)
    sections: list[ScopeProgress] = Field(default_factory=list)


class LearningProgressItem(BaseModel):
    item_id: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9][a-z0-9-]*$")
    visited: bool = True
    correct: bool | None = None
    updated_at: datetime | None = None


class LearningProgressUpdate(BaseModel):
    items: list[LearningProgressItem] = Field(max_length=100)


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=60)


class PrivateProfile(BaseModel):
    avatar: dict[str,str] | None = None
    avatar_version: int = 0
    name: str | None = None
    handle: str
    role: str
    level: int
    created_at: datetime
    account_type: Literal["browser", "account"] = "browser"
    email: str | None = None
    plan_code: str = "free"
    plan_status: str = "free"
    trial_ends_at: datetime | None = None
    plan_ends_at: datetime | None = None
    progress: Progress


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
    questions: int = 0


class CollectionSection(BaseModel):
    path: str
    title: str
    position: int
    formats: list[str] = Field(default_factory=list)
    papers: int
    scorable: int
    questions: int = 0
    note: str | None = None


class CollectionDetail(CollectionSummary):
    practice_count: int = 0
    answerable_count: int = 0
    needs_review: int = 0
    unsolved: int = 0
    section_list: list[CollectionSection] = Field(default_factory=list)
    paper_list: list["CollectionPaper"] = Field(default_factory=list)


class CollectionPaper(BaseModel):
    paper_label: str | None = None
    instructions: str | None = None
    practice_count: int = 0
    answerable_count: int = 0
    verified_solutions: int = 0
    needs_review: int = 0
    unsolved: int = 0
    missing_explanations: int = 0
    blocked_count: int = 0
    id: str
    title: str
    year: int | None = None
    exam: str | None = None
    paper_number: str | None = None
    subject: str | None = None
    source_file: str | None = None
    source_pdf_url: str | None = None
    section_path: str | None = None
    questions: int
    scorable: int
    descriptive: int = 0
    allow_browse: bool
    allow_practice: bool
    allow_timed_test: bool
    duration_minutes: int | None = None
    marks_correct: float | None = None
    marks_wrong: float | None = None
    rule_source: str


class PaperQuestion(BaseModel):
    id: str
    appearance_id: str
    qnum: str | None = None
    page: int | None = None
    year: int | None = None
    series: str | None = None
    type: str
    question: str
    direction: str | None = None
    question_markup: str | None = None
    options_markup: list[str | None] | None = None
    passage: str | None = None
    marks: float | None = None
    essay_kind: str | None = None
    options: list[str | None]
    option_order: list[int] | None = None
    answer_source: str
    verified: bool
    reviewed_derived: bool = False
    held: bool = False
    answer_status: Literal['official','verified','needs-review','unsolved','written'] | None = None
    source_defect: str | None = None
    key_disputed: bool = False
    dispute_note: str | None = None
    taxonomy_subject_id: str | None = None
    taxonomy_subject: str | None = None
    taxonomy_topic_id: str | None = None
    taxonomy_topic: str | None = None
    figure_image_url: str | None = None


class PaperQuestionPage(BaseModel):
    items: list[PaperQuestion]
    total: int
    practice_count: int = 0
    limit: int
    offset: int


class MockStart(BaseModel):
    collection_id: str
    section_path: str | None = None
    paper_id: str | None = None
    answer_mode: Literal["official", "derived-practice"] = "official"
    count: int = Field(20, ge=1, le=200)
    duration_minutes: int = Field(20, ge=1, le=240)
    marks_correct: float = Field(1, ge=0, le=10)
    #: Deduction per wrong answer. 0 = no negative marking, which is what
    #: several Mizoram PSC papers actually use.
    marks_wrong: float = Field(0, ge=0, le=10)


class MockQuestion(BaseModel):
    figure_image_url: str | None = None
    id: str
    position: int
    question: str
    options: list[str | None]
    direction: str | None = None
    question_markup: str | None = None
    options_markup: list[str | None] | None = None
    passage: str | None = None
    page: int | None = None
    source_pdf_url: str | None = None
    # No answer field, deliberately: the key is revealed only by submit.


class MockSession(BaseModel):
    excluded_presentations: int = 0
    id: str
    collection_id: str
    answer_mode: Literal["official", "derived-practice"] = "official"
    section_path: str | None = None
    paper_id: str | None = None
    current_position: int = 0
    saved_answers: dict[str, int] = Field(default_factory=dict)
    marked_questions: list[str] = Field(default_factory=list)
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


class MockAnswerSave(BaseModel):
    question_id: str = Field(min_length=1, max_length=200)
    chosen_index: int | None = Field(default=None, ge=0, le=9)
    marked: bool = False
    position: int = Field(default=0, ge=0, le=500)


class MockReviewRow(BaseModel):
    figure_image_url: str | None = None
    direction: str | None = None
    question_markup: str | None = None
    passage: str | None = None
    position: int
    question_id: str
    question: str
    chosen_text: str | None
    answer_text: str | None
    correct: bool
    explanation: str | None = None
    answer_source: str | None = None


class MockResult(BaseModel):
    id: str
    collection_id: str | None = None
    answer_mode: Literal["official", "derived-practice"] = "official"
    n_correct: int
    n_wrong: int
    n_skipped: int
    score: float
    total: int
    elapsed_seconds: int
    #: Submitted after the window closed. Recorded, not rejected.
    late: bool
    review: list[MockReviewRow]
    score_breakdown: dict | None = None
    legacy_unversioned: bool = False


class MockSummary(BaseModel):
    id: str
    collection_id: str
    collection_title: str
    answer_mode: Literal["official", "derived-practice"] = "official"
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


class HomeCollection(BaseModel):
    id: str
    title: str
    kind: str
    route: str | None = None
    sections: int


class HomeResponse(BaseModel):
    total_questions: int
    scorable_questions: int
    practice_questions: int
    featured_question: QuestionListItem | None = None
    featured_source: str | None = None
    collections: list[HomeCollection] = Field(default_factory=list)


class CommunityFeedItem(BaseModel):
    avatar: dict[str,str] | None = None
    id: int
    question_id: str
    question: str
    kind: Literal["explanation", "doubt"]
    body: str
    author: str
    author_role: str
    created_at: datetime
    helpful: int
    pinned: bool = False
    accepted_answer: str | None = None
    source_context: str | None = None


class CommunityFeedResponse(BaseModel):
    tab: Literal["for-you", "following", "mcqs", "doubts", "questions", "materials"]
    available: bool
    message: str | None = None
    items: list[CommunityFeedItem] = Field(default_factory=list)
    has_more: bool = False


class ModerationSummary(BaseModel):
    open_reports: int
    pending_posts: int
    open_appeals: int
    handled_today: int


class ModerationItem(BaseModel):
    source_links: list[dict] = Field(default_factory=list)
    id: str
    item_type: Literal["reported", "new_user", "appeal", "action"]
    post_id: int | None = None
    appeal_id: int | None = None
    action_id: int | None = None
    canonical_id: str | None = None
    question: str | None = None
    body: str
    author: str
    author_role: str
    created_at: datetime
    reasons: list[str] = Field(default_factory=list)
    report_count: int = 0
    report_score: float = 0
    signal: str | None = None
    note: str | None = None
    action: str | None = None
    undone: bool = False
    before_state: dict | None = None


class ModerationQueueResponse(BaseModel):
    tab: Literal["Reported", "New users", "Appeals", "My actions"]
    counts: ModerationSummary
    items: list[ModerationItem] = Field(default_factory=list)


class ModerationActionRequest(BaseModel):
    action: Literal["approve", "reject", "hide", "dismiss", "grant_appeal", "deny_appeal", "restore"]
    note: str | None = Field(default=None, max_length=1000)
