from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import close_pool, cursor, open_pool
from .routers import collections, me, mocks, questions


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
