"""Startup contract for the operator-controlled database audience policy."""
from ..config import settings


async def validate_policy(cur):
    await cur.execute('SELECT audience_database_gate_enabled() AS enabled')
    row=await cur.fetchone()
    if row['enabled'] != settings.audience_gate_enabled:
        raise RuntimeError('API and database audience policies differ; keep processing stopped until the guarded rollout is coordinated.')
