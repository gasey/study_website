"""Curated cosmetics only. No uploads, external URLs, currency or XP writes."""

import json
from pathlib import Path
from pydantic import BaseModel, ConfigDict, model_validator

CATALOG = json.loads(
    (Path(__file__).resolve().parents[1] / "data/avatar_catalog.json").read_text()
)
DEFAULT = {
    "skin": "#D9A47C",
    "hair": "Bun",
    "hairC": "#1D1B18",
    "top": "Vermilion",
    "acc": "None",
    "bg": "#F6E7C6",
    "frame": "None",
}


class Look(BaseModel):
    model_config = ConfigDict(extra="forbid")
    skin: str
    hair: str
    hairC: str
    top: str
    acc: str
    bg: str
    frame: str

    @model_validator(mode="after")
    def curated(self):
        for field, value in self.model_dump().items():
            if not any(i["category"] == field and i["value"] == value for i in CATALOG):
                raise ValueError("Choose a current " + field + " item")
        return self


async def account(cur, user, lock=False):
    await cur.execute(
        "SELECT id AS user_id,name,handle,email IS NOT NULL AS registered,avatar,avatar_version,GREATEST(1,floor(sqrt(GREATEST(0,COALESCE((SELECT sum(xp) FROM reward_ledger WHERE user_id=users.id),0))/40.0)))::int AS level FROM users WHERE id=%s"
        + (" FOR UPDATE" if lock else ""),
        (user,),
    )
    return await cur.fetchone()


async def inventory(cur, row):
    await cur.execute(
        "SELECT item_id FROM user_avatar_items WHERE user_id=%s", (row["user_id"],)
    )
    owned = {r["item_id"] for r in await cur.fetchall()}
    return [
        {
            **i,
            "available": i["level"] <= row["level"] or i["id"] in owned,
            "claimed": i["level"] == 1 or i["id"] in owned,
        }
        for i in CATALOG
    ]
