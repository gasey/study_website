"""Prospective shared-study notices; original content and receipts stay stored."""
from .assessment_audience import admission,Paused


async def notify(cur,user,query,params):
    # Callers may own content/room locks. Admission never waits on an account
    # lease, so restriction/closure can safely take their exclusive lease first.
    # A suppressed immediate notice is not replayed on later age confirmation.
    try:
        async with admission(cur,user):
            await cur.execute(query,params)
        return True
    except Paused:
        return False
