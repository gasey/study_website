from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from .config import settings

_pool: AsyncConnectionPool | None = None


async def open_pool() -> None:
    global _pool
    _pool = AsyncConnectionPool(
        settings.database_url,
        min_size=settings.pool_min,
        max_size=settings.pool_max,
        kwargs={"row_factory": dict_row},
        open=False,
    )
    await _pool.open(wait=True, timeout=10)


async def close_pool() -> None:
    if _pool is not None:
        await _pool.close()


@asynccontextmanager
async def cursor() -> AsyncIterator:
    """A cursor returning dict rows. The pool is opened at app startup, so a
    request never pays connection cost — which is most of the latency at this
    scale, where the queries themselves run in under a millisecond."""
    if _pool is None:
        raise RuntimeError("connection pool not open")
    async with _pool.connection() as conn, conn.cursor() as cur:
        yield cur
