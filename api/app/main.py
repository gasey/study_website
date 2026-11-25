from .services.public_catalog_cache import InvalidatePublicCatalog
from .exam_scope import ExamScope, DEFAULT_SCOPE, pool_view, scope_condition, question_scope
from contextlib import asynccontextmanager
import asyncio
from contextlib import suppress
from .services.scoring_revisions import worker as assessment_worker
from .services.desk_retention import worker as desk_retention_worker
from .services.calendar_reminders import worker as calendar_worker
from .services.games import worker as game_worker
from .services.learning_rollups import worker as learning_worker

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import close_pool, cursor, open_pool
from .routers import auth, billing, collections, community, home, me, mocks, moderation, questions
from .routers import study_sessions
from .routers import editorial
from .routers import games,search,calendar,avatars,study_desks,discussions,bank_workspace,auth_mfa,rewards,materials,creators,admin_workflow,module_audits
from .services.review_limits import ReviewBodyLimit
from .schemas import ScoringFacts


@asynccontextmanager
async def lifespan(_: FastAPI):
    await open_pool()
    task=asyncio.create_task(assessment_worker())
    retention_task=asyncio.create_task(desk_retention_worker())
    from .services.account_retention import worker as account_retention_worker
    account_retention_task=asyncio.create_task(account_retention_worker())
    calendar_task=asyncio.create_task(calendar_worker())
    game_task=asyncio.create_task(game_worker())
    learning_task=asyncio.create_task(learning_worker())
    from .services.account_mail import worker as mail_worker
    mail_task=asyncio.create_task(mail_worker())
    try:
        yield
    finally:
        account_retention_task.cancel()
        with suppress(asyncio.CancelledError):await account_retention_task
        learning_task.cancel()
        with suppress(asyncio.CancelledError):await learning_task
        mail_task.cancel()
        with suppress(asyncio.CancelledError):await mail_task
        game_task.cancel()
        with suppress(asyncio.CancelledError):await game_task
        calendar_task.cancel()
        with suppress(asyncio.CancelledError):await calendar_task
        retention_task.cancel()
        with suppress(asyncio.CancelledError):await retention_task
        task.cancel()
        with suppress(asyncio.CancelledError):await task
        await close_pool()


app = FastAPI(title="Finna API", version="0.1.0", lifespan=lifespan)
from .routers import review_digest
app.include_router(review_digest.router)
from .routers import referrals
app.include_router(referrals.router)

# Production is same-origin behind Caddy, so this only matters in dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

from .services.account_boundary import AccountBoundary
app.add_middleware(AccountBoundary)
from .services.audience import AudienceBoundary
app.add_middleware(AudienceBoundary)
from .services.mobile_identity import MobileBoundary
app.add_middleware(MobileBoundary)
app.add_middleware(ReviewBodyLimit)
app.add_middleware(InvalidatePublicCatalog)
from .services.public_browse_cache import PublicBrowseCache
app.add_middleware(PublicBrowseCache)
app.include_router(bank_workspace.router)
from .routers import mcq_solver_reviews
app.include_router(mcq_solver_reviews.router)
app.include_router(questions.router)
app.include_router(study_sessions.router)
from .routers import learning_loop
app.include_router(learning_loop.router)
app.include_router(editorial.router)
app.include_router(home.router)
app.include_router(community.router)
app.include_router(discussions.router)
app.include_router(study_desks.router)
app.include_router(avatars.router)
app.include_router(calendar.router)
app.include_router(games.router)
app.include_router(search.router)
app.include_router(moderation.router)
app.include_router(auth.router)
app.include_router(auth_mfa.router)
app.include_router(billing.router)
app.include_router(rewards.router)
app.include_router(materials.router)
app.include_router(creators.router)
app.include_router(admin_workflow.router)
app.include_router(module_audits.router)
app.include_router(me.router)
app.include_router(collections.router)
app.include_router(mocks.router)
from .routers import ops
app.include_router(ops.router)
from .routers import account_privacy
app.include_router(account_privacy.router)
from .routers import account_viewer
app.include_router(account_viewer.router)
from .routers import site_notice
app.include_router(site_notice.router)
from .routers import guides
app.include_router(guides.router)
from .routers import authoring_console
app.include_router(authoring_console.router)
from .routers import vault
app.include_router(vault.router)
from .routers import leaderboard_picker
app.include_router(leaderboard_picker.router)


@app.get("/api/health")
async def health() -> dict:
    """Liveness plus a real query, so this fails when the database is gone
    rather than cheerfully reporting OK while every request 500s."""
    async with cursor() as cur:
        await cur.execute(
            "SELECT (SELECT COUNT(*) FROM canonical_questions) AS questions,"
            "       (SELECT COUNT(*) FROM v_scorable) AS scorable"
        )
        row = await cur.fetchone()
    return {"status": "ok", **(row or {})}


@app.get("/api/scoring-facts", response_model=ScoringFacts)
async def scoring_facts(exam_scope: ExamScope = DEFAULT_SCOPE) -> ScoringFacts:
    """Counts behind the scoring explainer. Served rather than hard-coded so
    the page cannot quietly become wrong as the bank changes."""
    async with cursor() as cur:
        await cur.execute(
            f"""SELECT (SELECT COUNT(*) FROM canonical_questions WHERE {question_scope('canonical_questions', exam_scope)})::int AS total,
                      (SELECT COUNT(*) FROM {pool_view('scorable', exam_scope)})::int            AS scorable,
                      (SELECT COUNT(*) FROM {pool_view('practice', exam_scope)})::int            AS practice,
                      (SELECT COUNT(*) FROM canonical_questions
                        WHERE {question_scope('canonical_questions', exam_scope)} AND answer_source = 'official')::int          AS official,
                      (SELECT COUNT(*) FROM canonical_questions
                        WHERE {question_scope('canonical_questions', exam_scope)} AND answer_source = 'key')::int               AS transcribed,
                      (SELECT COUNT(*) FROM canonical_questions
                        WHERE {question_scope('canonical_questions', exam_scope)} AND source_defect = 'duplicate-options')::int AS dup_defect"""
        )
        row = await cur.fetchone() or {}
    return ScoringFacts(**row)

from .routers import library
app.include_router(library.router)

from .routers import inbox
app.include_router(inbox.router)

from .routers import vocabulary
app.include_router(vocabulary.router)

from .routers import exam_inventory
app.include_router(exam_inventory.router)

from .routers import learning, paper_intake
app.include_router(learning.router)
app.include_router(paper_intake.router)

from .routers import admin_answers
app.include_router(admin_answers.router)

from .routers import source_identities, retagging
app.include_router(source_identities.router)
app.include_router(retagging.router)

from .routers import account_recovery
app.include_router(account_recovery.router)

from .routers import current_affairs
app.include_router(current_affairs.router)

from .routers import paper_workbench
app.include_router(paper_workbench.router)
from .routers import topic_trail
app.include_router(topic_trail.router)

from .routers import discovery
app.include_router(discovery.router)

from .routers import learning_catalog
app.include_router(learning_catalog.router)

from .routers import google_auth
app.include_router(google_auth.router)

from .routers import pdf_library
app.include_router(pdf_library.router)

from .routers import bank_organization
app.include_router(bank_organization.router)
app.include_router(bank_organization.public_router)

from .routers import shareable_tests
app.include_router(shareable_tests.router)

from .routers import mobile
app.include_router(mobile.router)

from .routers import stats
app.include_router(stats.router)
app.add_middleware(stats.StatsBodyLimit)

from .routers import youtube_current_affairs
app.include_router(youtube_current_affairs.router)
app.add_middleware(youtube_current_affairs.YouTubeBodyLimit)

from .routers import atlas
app.include_router(atlas.router)
