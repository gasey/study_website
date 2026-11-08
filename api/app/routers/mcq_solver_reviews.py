"""Private review data and draft creation; never exposes inference or publication."""
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, ConfigDict, Field

from ..db import cursor
from ..services.review_identity import Actor, identity
from ..services import mcq_solver_source_reviews as service

router = APIRouter(prefix='/api/admin/mcq-solver', tags=['private solver review'])
Account = Annotated[Actor, Depends(identity)]


class Stage(BaseModel):
    model_config = ConfigDict(extra='forbid')
    source_version: str = Field(pattern=r'^[0-9a-f]{64}$')
    question_version_hash: str = Field(pattern=r'^[0-9a-f]{64}$')


@router.get('/review')
async def review(actor: Account, response: Response):
    response.headers['Cache-Control'] = 'private, no-store'
    async with cursor() as cur:
        return await service.listing(cur, actor)


@router.post('/drafts/{appearance_id}', status_code=201)
async def draft(appearance_id: str, body: Stage, actor: Account, response: Response):
    response.headers['Cache-Control'] = 'private, no-store'
    async with cursor() as cur:
        return await service.stage(cur, actor, appearance_id, body.source_version, body.question_version_hash)
