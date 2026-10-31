"""Versioned, account-bound avatar editing with durable earned cosmetics."""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from psycopg.types.json import Jsonb
from ..db import cursor
from ..deps import current_user, require_account
from ..services import avatars
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
async def get_avatar(user: Annotated[str, Depends(current_user)]):
    async with cursor() as cur:
        row = await avatars.account(cur, user)
        if not row:
            raise HTTPException(404, "Account not found")
        catalog = await avatars.inventory(cur, row)
    return {**row, "catalog": catalog, "default": avatars.DEFAULT}


@router.post("")
async def save_avatar(
    body: Save, request: Request, user: Annotated[str, Depends(require_account)]
):
    await write_guard(request, user)
    if body.user_id != user:
        raise HTTPException(
            409, "Your signed-in account changed. Reload before saving."
        )
    look = body.look.model_dump() if body.look else None
    async with cursor() as cur:
        row = await avatars.account(cur, user, lock=True)
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
                        403, "This item unlocks at level " + str(item["level"])
                    )
            for item in catalog:
                if item["level"] > 1 and item["level"] <= row["level"]:
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
