"""Nonblocking learner-assessment admission; no consent or age inference."""
from contextlib import asynccontextmanager
from fastapi import HTTPException
from ..config import settings
from . import audience


class Paused(HTTPException):
    def __init__(self):
        super().__init__(409,'Assessment processing is paused for this account.')


@asynccontextmanager
async def admission(cur,user):
    if not settings.audience_gate_enabled:
        yield
        return
    # Workers may already own a queue row. Never wait for the account lease:
    # a restriction can own its exclusive counterpart before touching queues.
    # A skipped savepoint releases the temporary lease and all partial writes.
    async with cur.connection.transaction():
        if not await audience.learning_processing_lock(cur,user):raise Paused()
        await cur.execute('''SELECT 1 FROM users u WHERE u.id=%s
          AND u.email IS NOT NULL AND u.closed_at IS NULL AND '''+audience.eligible_sql('u.id'),(user,))
        if not await cur.fetchone():raise Paused()
        yield
