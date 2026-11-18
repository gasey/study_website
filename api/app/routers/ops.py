"""Owner-only operational reads. No worker control or account mutation."""
from typing import Annotated
from fastapi import APIRouter, Depends
from ..db import cursor, pool_status
from ..services.review_identity import Actor, identity, require_role
from ..services import ops
from .learning import private

router = APIRouter(prefix='/api/admin/ops', tags=['operations'], dependencies=[Depends(private)])


@router.get('')
async def overview(actor: Annotated[Actor, Depends(identity)]):
    async with cursor() as cur:
        await cur.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        await cur.execute("SET LOCAL statement_timeout='5s'")
        await require_role(cur, actor.id, roles=('owner',), lock=False)
        return await ops.snapshot(cur, pool_status())
