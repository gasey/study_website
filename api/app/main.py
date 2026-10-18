from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import close_pool, cursor, open_pool
from .routers import collections, me, mocks, questions
from .schemas import ScoringFacts


@asynccontextmanager
async def lifespan(_: FastAPI):
    await open_pool()
    try:
        yield
    finally:
        await close_pool()


app = FastAPI(title="India Study Map API", version="0.1.0", lifespan=lifespan)

# Production is same-origin behind Caddy, so this only matters in dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(questions.router)
app.include_router(me.router)
app.include_router(collections.router)
app.include_router(mocks.router)


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
async def scoring_facts() -> ScoringFacts:
    """Counts behind the scoring explainer. Served rather than hard-coded so
    the page cannot quietly become wrong as the bank changes."""
    async with cursor() as cur:
        await cur.execute(
            """SELECT (SELECT COUNT(*) FROM canonical_questions)::int AS total,
                      (SELECT COUNT(*) FROM v_scorable)::int            AS scorable,
                      (SELECT COUNT(*) FROM v_practice)::int            AS practice,
                      (SELECT COUNT(*) FROM canonical_questions
                        WHERE answer_source = 'official')::int          AS official,
                      (SELECT COUNT(*) FROM canonical_questions
                        WHERE answer_source = 'key')::int               AS transcribed,
                      (SELECT COUNT(*) FROM canonical_questions
                        WHERE source_defect = 'duplicate-options')::int AS dup_defect"""
        )
        row = await cur.fetchone() or {}
    return ScoringFacts(**row)
