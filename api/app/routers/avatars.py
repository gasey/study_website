"""Versioned, account-bound avatar editing with durable earned cosmetics."""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel, ConfigDict, Field
from psycopg.types.json import Jsonb
from ..db import cursor
from ..deps import current_user, require_account
from ..services import avatars
from ..services.cosmetic_shop import purchase
from .materials import private, write_guard

router = APIRouter(
    prefix="/api/me/avatar", tags=["avatar"], dependencies=[Depends(private)]
)


class Save(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str = Field(min_length=1, max_length=100)
    expected_version: int = Field(ge=0)
    look: avatars.Look | None


@router.get("")
async def get_avatar(user: Annotated[str, Depends(current_user)], catalog_version:int=Query(1,ge=1,le=2)):
    async with cursor() as cur:
        row = await avatars.account(cur, user)
        if not row:
            raise HTTPException(404, "Account not found")
        catalog = await avatars.inventory(cur, row)
        await cur.execute('SELECT COALESCE(sum(points),0)::int AS balance FROM reward_ledger WHERE user_id=%s',(user,))
        balance=(await cur.fetchone())['balance']
        if catalog_version==1:
            catalog=[i for i in catalog if i['level'] is not None]
    return {**row, "catalog": catalog, "default": avatars.DEFAULT,"points":balance,"catalog_sha256":avatars.CATALOG_SHA256,"catalog_version":catalog_version,"requires_web_editor":catalog_version==1 and avatars.needs_current_renderer(row["avatar"])}


@router.post("")
async def save_avatar(
    body: Save, request: Request, user: Annotated[str, Depends(require_account)],
    catalog_version:int=Query(1,ge=1,le=2)
):
    await write_guard(request, user)
    if catalog_version == 2:
        from ..services.v5_release import require_writes
        require_writes()
    if body.user_id != user:
        raise HTTPException(
            409, "Your signed-in account changed. Reload before saving."
        )
    look = body.look.model_dump() if body.look else None
    async with cursor() as cur:
        row = await avatars.account(cur, user, lock=True)
        if catalog_version==1 and (avatars.needs_current_renderer(row['avatar']) or avatars.needs_current_renderer(look)):
            raise HTTPException(409,'This look uses newer cosmetics. Open the avatar editor on the website to change it.')
        if row["avatar_version"] != body.expected_version:
            # A repeated successful save returns the current version without another event.
            if row["avatar"] == look:
                return {
                    "avatar": look,
                    "avatar_version": row["avatar_version"],
                    "replayed": True,
                }
            raise HTTPException(
                409,
                "Your avatar changed on another device. Reload the saved look before replacing it.",
            )
        catalog = await avatars.inventory(cur, row)
        if look is not None:
            for category, value in look.items():
                item = next(
                    i
                    for i in catalog
                    if i["category"] == category and i["value"] == value
                )
                if not item["available"]:
                    raise HTTPException(
                        403, "Buy this item with points first" if item.get("price_points") else "This item unlocks at level " + str(item["level"])
                    )
            for item in catalog:
                if item["level"] is not None and item["level"] > 1 and item["level"] <= row["level"]:
                    await cur.execute(
                        "INSERT INTO user_avatar_items(user_id,item_id,level_at_claim) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING",
                        (user, item["id"], row["level"]),
                    )
        await cur.execute(
            "UPDATE users SET avatar=%s,avatar_version=avatar_version+1 WHERE id=%s RETURNING avatar_version",
            (Jsonb(look) if look else None, user),
        )
        version = (await cur.fetchone())["avatar_version"]
        await cur.execute(
            "INSERT INTO avatar_events(user_id,action,version,detail) VALUES(%s,%s,%s,%s)",
            (user, "saved" if look else "reset", version, Jsonb({"look": look})),
        )
    return {"avatar": look, "avatar_version": version, "replayed": False}


class Purchase(BaseModel):
    model_config=ConfigDict(extra='forbid')
    user_id:str=Field(min_length=1,max_length=100)
    item_id:str=Field(min_length=1,max_length=100)
    catalog_sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
    price_points:int=Field(ge=1,le=10000)

@router.post('/purchase')
async def buy(body:Purchase,request:Request,user:Annotated[str,Depends(require_account)]):
    await write_guard(request,user)
    if body.user_id!=user:raise HTTPException(409,'Your account changed. Reload before buying.')
    async with cursor() as cur:
        return await purchase(cur,user,body.item_id,body.catalog_sha256,body.price_points)
