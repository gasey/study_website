"""Owner Admin API for the Daily & Weekly Leaderboard Question-Picker microservice."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field

from ..db import cursor
from ..services import games as g
from ..services import leaderboard_picker as picker
from ..services.review_identity import Actor, identity, require_role

router = APIRouter(prefix="/api/admin/leaderboard-picker", tags=["leaderboard-picker"])


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class EnsureIn(StrictModel):
    days_ahead: int = Field(default=2, ge=1, le=7)
    daily_theme: picker.ThemeId = "balanced"
    cup_theme: picker.ThemeId | None = None


class RegenerateIn(StrictModel):
    kind: picker.SetKind
    set_id: str = Field(min_length=8, max_length=20)
    theme: picker.ThemeId = "balanced"


class SwapIn(StrictModel):
    kind: picker.SetKind
    set_id: str = Field(min_length=8, max_length=20)
    position: int = Field(ge=0, le=24)
    theme: picker.ThemeId = "balanced"


@router.get("/upcoming")
async def get_upcoming(
    actor: Annotated[Actor, Depends(identity)],
    days_ahead: int = Query(default=2, ge=1, le=7),
) -> dict:
    """Preview today's + upcoming Daily Five and Weekly Cup sets before go-live."""
    async with cursor() as cur:
        await require_role(cur, actor.id, roles=("owner",))
        now = await g.clock(cur)
        return await picker.list_upcoming_sets(cur, now, days_ahead=days_ahead)


@router.post("/ensure")
async def run_ensure(
    body: EnsureIn,
    actor: Annotated[Actor, Depends(identity)],
) -> dict:
    """Trigger the pre-generation worker on-demand for upcoming Daily & Weekly sets."""
    async with cursor() as cur:
        await require_role(cur, actor.id, roles=("owner",))
        now = await g.clock(cur)
        summary = await picker.ensure_upcoming_sets(
            cur,
            now,
            days_ahead=body.days_ahead,
            daily_theme=body.daily_theme,
            cup_theme=body.cup_theme,
        )
        upcoming = await picker.list_upcoming_sets(cur, now, days_ahead=body.days_ahead)
        return {"run": summary, "upcoming": upcoming}


@router.post("/regenerate")
async def regenerate(
    body: RegenerateIn,
    actor: Annotated[Actor, Depends(identity)],
) -> dict:
    """Re-roll an unplayed Daily Five or Weekly Cup set with a chosen subject theme."""
    async with cursor() as cur:
        await require_role(cur, actor.id, roles=("owner",))
        now = await g.clock(cur)
        updated = await picker.regenerate_set(cur, body.kind, body.set_id, theme=body.theme)
        return {
            "ok": True,
            "kind": body.kind,
            "id": updated["id"],
            "theme": body.theme,
            "question_count": len(updated.get("questions") or []),
            "upcoming": await picker.list_upcoming_sets(cur, now),
        }


@router.post("/swap")
async def swap_slot(
    body: SwapIn,
    actor: Annotated[Actor, Depends(identity)],
) -> dict:
    """Replace one question slot in an unplayed set with a fresh non-repeating MCQ."""
    async with cursor() as cur:
        await require_role(cur, actor.id, roles=("owner",))
        now = await g.clock(cur)
        updated = await picker.swap_question(
            cur,
            body.kind,
            body.set_id,
            body.position,
            theme=body.theme,
        )
        return {
            "ok": True,
            "kind": body.kind,
            "id": updated["id"],
            "position": body.position,
            "upcoming": await picker.list_upcoming_sets(cur, now),
        }
