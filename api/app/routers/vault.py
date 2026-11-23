"""Personal Question Vault API.

Learner-owned safe for saving questions from any section of Finna, starring
favorites (Pro), crafting custom MCQ/flashcard questions with optional images
(Pro), Leitner mastery tracking, and sharing/cloning personal test packs.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import re
import secrets
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..db import cursor
from ..deps import current_user, require_account

router = APIRouter(prefix="/api/vault", tags=["personal vault"])

FREE_SAVED_LIMIT = 25
MAX_IMAGE_LEN = 680_000
HTTPS_RE = re.compile(r"^https://[^\s\"'<>]{4,1000}$", re.IGNORECASE)
DATA_IMG_RE = re.compile(
    r"^data:image/(?:png|jpeg|jpg|webp);base64,[A-Za-z0-9+/=]+$",
    re.IGNORECASE,
)
LEITNER_DAYS = {1: 1, 2: 3, 3: 7, 4: 14}


def _validate_image(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if len(cleaned) > MAX_IMAGE_LEN:
        raise ValueError("Image is too large (max ~500 KB).")
    if HTTPS_RE.match(cleaned) or DATA_IMG_RE.match(cleaned):
        return cleaned
    raise ValueError("Image must be an https:// URL or a PNG/JPEG/WebP upload.")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class VaultItemCreate(StrictModel):
    kind: Literal["saved", "custom"] = "saved"
    canonical_question_id: str | None = Field(default=None, max_length=120)
    folder: str = Field(default="General", min_length=1, max_length=60)
    subject: str = Field(default="General", min_length=1, max_length=80)
    question_type: Literal["mcq", "flashcard"] = "mcq"
    question: str = Field(min_length=3, max_length=4000)
    options: list[str] = Field(default_factory=list, max_length=6)
    answer_index: int | None = Field(default=None, ge=0, le=5)
    answer_text: str = Field(default="", max_length=2000)
    explanation: str = Field(default="", max_length=4000)
    mnemonic: str = Field(default="", max_length=1000)
    image_url: str | None = Field(default=None, max_length=MAX_IMAGE_LEN)
    image_alt: str = Field(default="", max_length=200)
    difficulty: Literal["easy", "medium", "hard", "trap"] = "medium"
    tags: list[str] = Field(default_factory=list, max_length=12)
    is_favorite: bool = False
    source_meta: dict = Field(default_factory=dict)

    @field_validator("image_url")
    @classmethod
    def check_image(cls, v: str | None) -> str | None:
        return _validate_image(v)


class VaultItemPatch(StrictModel):
    folder: str | None = Field(default=None, min_length=1, max_length=60)
    subject: str | None = Field(default=None, min_length=1, max_length=80)
    question: str | None = Field(default=None, min_length=3, max_length=4000)
    options: list[str] | None = Field(default=None, max_length=6)
    answer_index: int | None = Field(default=None, ge=0, le=5)
    answer_text: str | None = Field(default=None, max_length=2000)
    explanation: str | None = Field(default=None, max_length=4000)
    mnemonic: str | None = Field(default=None, max_length=1000)
    image_url: str | None = Field(default=None, max_length=MAX_IMAGE_LEN)
    image_alt: str | None = Field(default=None, max_length=200)
    difficulty: Literal["easy", "medium", "hard", "trap"] | None = None
    tags: list[str] | None = Field(default=None, max_length=12)
    is_favorite: bool | None = None
    clear_image: bool = False

    @field_validator("image_url")
    @classmethod
    def check_image(cls, v: str | None) -> str | None:
        return _validate_image(v)


class VaultReviewIn(StrictModel):
    correct: bool


class VaultShareCreate(StrictModel):
    title: str = Field(min_length=2, max_length=140)
    description: str = Field(default="", max_length=600)
    mode: Literal["practice", "timed", "flashcards"] = "practice"
    duration_minutes: int = Field(default=10, ge=1, le=180)
    item_ids: list[str] = Field(min_length=1, max_length=80)


async def _is_pro(cur, user_id: str) -> bool:
    await cur.execute(
        "SELECT account_has_pro(id) AS pro, role FROM users WHERE id=%s",
        (user_id,),
    )
    row = await cur.fetchone()
    if not row:
        return False
    return bool(row["pro"] or row.get("role") == "owner")


def _clean_tags(tags: list[str]) -> list[str]:
    seen: list[str] = []
    for raw in tags:
        t = raw.strip().lstrip("#")[:32]
        if t and t.lower() not in {x.lower() for x in seen}:
            seen.append(t)
    return seen[:12]


@router.get("")
async def list_vault(
    user_id: Annotated[str, Depends(current_user)],
    folder: str = Query("", max_length=60),
    kind: str = Query("", max_length=20),
    favorite: bool | None = Query(None),
    due_only: bool = Query(False),
    q: str = Query("", max_length=120),
) -> dict:
    async with cursor() as cur:
        pro = await _is_pro(cur, user_id)
        await cur.execute(
            """SELECT id, kind, canonical_question_id, folder, subject, question_type,
                      question, options, answer_index, answer_text, explanation, mnemonic,
                      image_url, image_alt, difficulty, tags, is_favorite, mastery_box,
                      review_count, correct_count, last_reviewed_at, next_review_at,
                      source_meta, created_at, updated_at
                 FROM personal_vault_items
                WHERE user_id = %s
                ORDER BY is_favorite DESC, updated_at DESC""",
            (user_id,),
        )
        all_items = await cur.fetchall()

    now = datetime.now(timezone.utc)
    folders_map: dict[str, int] = {}
    favorites_count = 0
    custom_count = 0
    saved_count = 0
    due_count = 0
    mastered_count = 0

    for item in all_items:
        f = item["folder"] or "General"
        folders_map[f] = folders_map.get(f, 0) + 1
        if item["is_favorite"]:
            favorites_count += 1
        if item["kind"] == "custom":
            custom_count += 1
        else:
            saved_count += 1
        if item["mastery_box"] >= 3:
            mastered_count += 1
        nra = item.get("next_review_at")
        if nra is None or nra <= now:
            due_count += 1

    needle = q.strip().lower()
    filtered = []
    for item in all_items:
        if folder and item["folder"] != folder:
            continue
        if kind in ("saved", "custom") and item["kind"] != kind:
            continue
        if favorite is True and not item["is_favorite"]:
            continue
        if due_only:
            nra = item.get("next_review_at")
            if nra is not None and nra > now:
                continue
        if needle:
            hay = " ".join(
                [
                    item["question"] or "",
                    item["subject"] or "",
                    item["folder"] or "",
                    item["mnemonic"] or "",
                    " ".join(item["tags"] or []),
                ]
            ).lower()
            if needle not in hay:
                continue
        filtered.append(item)

    return {
        "is_pro": pro,
        "limits": {
            "saved_max": None if pro else FREE_SAVED_LIMIT,
            "favorites_enabled": pro,
            "custom_craft_enabled": pro,
            "share_packs_enabled": pro,
        },
        "summary": {
            "total": len(all_items),
            "saved": saved_count,
            "custom": custom_count,
            "favorites": favorites_count,
            "due": due_count,
            "mastered": mastered_count,
        },
        "folders": [
            {"name": name, "count": count}
            for name, count in sorted(folders_map.items(), key=lambda x: (-x[1], x[0]))
        ],
        "items": filtered,
    }


@router.post("/items")
async def create_vault_item(
    body: VaultItemCreate,
    user_id: Annotated[str, Depends(require_account)],
) -> dict:
    async with cursor() as cur:
        pro = await _is_pro(cur, user_id)

        if body.kind == "custom" and not pro:
            raise HTTPException(
                402,
                "Crafting personal questions with images is a Pro Vault feature. Upgrade to Pro to unlock unlimited custom questions.",
            )
        if body.is_favorite and not pro:
            raise HTTPException(
                402,
                "Starring Favorites in the Gold Vault compartment is a Pro feature.",
            )

        if body.kind == "saved" and not pro:
            await cur.execute(
                "SELECT count(*)::int AS c FROM personal_vault_items WHERE user_id=%s AND kind='saved'",
                (user_id,),
            )
            count = (await cur.fetchone())["c"]
            if count >= FREE_SAVED_LIMIT:
                raise HTTPException(
                    402,
                    f"Free Vault holds up to {FREE_SAVED_LIMIT} saved questions. Upgrade to Pro for unlimited capacity.",
                )

        cleaned_options = [o.strip()[:500] for o in body.options if o.strip()]
        if body.question_type == "mcq" and body.kind == "custom" and len(cleaned_options) < 2:
            raise HTTPException(422, "MCQ questions need at least 2 answer options.")
        if body.answer_index is not None and cleaned_options and body.answer_index >= len(cleaned_options):
            raise HTTPException(422, "Correct answer index exceeds options length.")

        cleaned_tags = _clean_tags(body.tags)
        item_id = "vlt_" + uuid4().hex[:16]

        if body.canonical_question_id:
            await cur.execute(
                """INSERT INTO personal_vault_items
                   (id, user_id, kind, canonical_question_id, folder, subject, question_type,
                    question, options, answer_index, answer_text, explanation, mnemonic,
                    image_url, image_alt, difficulty, tags, is_favorite, source_meta)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s::jsonb)
                   ON CONFLICT (user_id, canonical_question_id)
                   WHERE canonical_question_id IS NOT NULL
                   DO UPDATE SET
                     folder = EXCLUDED.folder,
                     mnemonic = CASE WHEN EXCLUDED.mnemonic <> '' THEN EXCLUDED.mnemonic ELSE personal_vault_items.mnemonic END,
                     difficulty = EXCLUDED.difficulty,
                     is_favorite = personal_vault_items.is_favorite OR EXCLUDED.is_favorite,
                     updated_at = now()
                   RETURNING *""",
                (
                    item_id,
                    user_id,
                    body.kind,
                    body.canonical_question_id,
                    body.folder.strip(),
                    body.subject.strip(),
                    body.question_type,
                    body.question.strip(),
                    json.dumps(cleaned_options),
                    body.answer_index,
                    body.answer_text.strip(),
                    body.explanation.strip(),
                    body.mnemonic.strip(),
                    body.image_url,
                    body.image_alt.strip(),
                    body.difficulty,
                    json.dumps(cleaned_tags),
                    body.is_favorite,
                    json.dumps(body.source_meta),
                ),
            )
        else:
            await cur.execute(
                """INSERT INTO personal_vault_items
                   (id, user_id, kind, canonical_question_id, folder, subject, question_type,
                    question, options, answer_index, answer_text, explanation, mnemonic,
                    image_url, image_alt, difficulty, tags, is_favorite, source_meta)
                   VALUES (%s,%s,%s,NULL,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s::jsonb)
                   RETURNING *""",
                (
                    item_id,
                    user_id,
                    body.kind,
                    body.folder.strip(),
                    body.subject.strip(),
                    body.question_type,
                    body.question.strip(),
                    json.dumps(cleaned_options),
                    body.answer_index,
                    body.answer_text.strip(),
                    body.explanation.strip(),
                    body.mnemonic.strip(),
                    body.image_url,
                    body.image_alt.strip(),
                    body.difficulty,
                    json.dumps(cleaned_tags),
                    body.is_favorite,
                    json.dumps(body.source_meta),
                ),
            )
        row = await cur.fetchone()
    return {"item": row}


@router.patch("/items/{item_id}")
async def update_vault_item(
    item_id: str,
    body: VaultItemPatch,
    user_id: Annotated[str, Depends(require_account)],
) -> dict:
    async with cursor() as cur:
        await cur.execute(
            "SELECT * FROM personal_vault_items WHERE id=%s AND user_id=%s",
            (item_id, user_id),
        )
        existing = await cur.fetchone()
        if not existing:
            raise HTTPException(404, "Vault item not found")

        pro = await _is_pro(cur, user_id)
        if body.is_favorite is True and not pro:
            raise HTTPException(402, "Favorites in the Gold Vault require Pro.")

        next_folder = body.folder.strip() if body.folder is not None else existing["folder"]
        next_subject = body.subject.strip() if body.subject is not None else existing["subject"]
        next_question = (
            body.question.strip()
            if body.question is not None and existing["kind"] == "custom"
            else existing["question"]
        )
        next_options = (
            [o.strip()[:500] for o in body.options if o.strip()]
            if body.options is not None and existing["kind"] == "custom"
            else existing["options"]
        )
        next_answer_index = (
            body.answer_index
            if body.answer_index is not None and existing["kind"] == "custom"
            else existing["answer_index"]
        )
        next_answer_text = (
            body.answer_text.strip()
            if body.answer_text is not None and existing["kind"] == "custom"
            else existing["answer_text"]
        )
        next_explanation = (
            body.explanation.strip()
            if body.explanation is not None and existing["kind"] == "custom"
            else existing["explanation"]
        )
        next_mnemonic = body.mnemonic.strip() if body.mnemonic is not None else existing["mnemonic"]
        next_image = (
            None
            if body.clear_image
            else (body.image_url if body.image_url is not None else existing["image_url"])
        )
        next_image_alt = body.image_alt.strip() if body.image_alt is not None else existing["image_alt"]
        next_difficulty = body.difficulty if body.difficulty is not None else existing["difficulty"]
        next_tags = _clean_tags(body.tags) if body.tags is not None else existing["tags"]
        next_fav = body.is_favorite if body.is_favorite is not None else existing["is_favorite"]

        await cur.execute(
            """UPDATE personal_vault_items
                  SET folder=%s, subject=%s, question=%s, options=%s::jsonb,
                      answer_index=%s, answer_text=%s, explanation=%s, mnemonic=%s,
                      image_url=%s, image_alt=%s, difficulty=%s, tags=%s::jsonb,
                      is_favorite=%s, updated_at=now()
                WHERE id=%s AND user_id=%s
                RETURNING *""",
            (
                next_folder,
                next_subject,
                next_question,
                json.dumps(next_options),
                next_answer_index,
                next_answer_text,
                next_explanation,
                next_mnemonic,
                next_image,
                next_image_alt,
                next_difficulty,
                json.dumps(next_tags),
                next_fav,
                item_id,
                user_id,
            ),
        )
        row = await cur.fetchone()
    return {"item": row}


@router.delete("/items/{item_id}")
async def delete_vault_item(
    item_id: str,
    user_id: Annotated[str, Depends(require_account)],
) -> dict:
    async with cursor() as cur:
        await cur.execute(
            "DELETE FROM personal_vault_items WHERE id=%s AND user_id=%s RETURNING id",
            (item_id, user_id),
        )
        if not await cur.fetchone():
            raise HTTPException(404, "Vault item not found")
    return {"deleted": True, "id": item_id}


@router.post("/items/{item_id}/review")
async def review_vault_item(
    item_id: str,
    body: VaultReviewIn,
    user_id: Annotated[str, Depends(require_account)],
) -> dict:
    async with cursor() as cur:
        await cur.execute(
            "SELECT mastery_box, review_count, correct_count FROM personal_vault_items WHERE id=%s AND user_id=%s",
            (item_id, user_id),
        )
        row = await cur.fetchone()
        if not row:
            raise HTTPException(404, "Vault item not found")

        new_box = min(4, row["mastery_box"] + 1) if body.correct else 1
        next_due = datetime.now(timezone.utc) + timedelta(days=LEITNER_DAYS[new_box])
        await cur.execute(
            """UPDATE personal_vault_items
                  SET mastery_box=%s,
                      review_count=review_count+1,
                      correct_count=correct_count+%s,
                      last_reviewed_at=now(),
                      next_review_at=%s,
                      updated_at=now()
                WHERE id=%s AND user_id=%s
                RETURNING *""",
            (new_box, 1 if body.correct else 0, next_due, item_id, user_id),
        )
        updated = await cur.fetchone()
    return {"item": updated}


@router.post("/shares")
async def create_vault_share(
    body: VaultShareCreate,
    user_id: Annotated[str, Depends(require_account)],
) -> dict:
    async with cursor() as cur:
        pro = await _is_pro(cur, user_id)
        if len(body.item_ids) > 1 and not pro:
            raise HTTPException(
                402,
                "Sharing multi-question Vault test packs is a Pro feature. Free accounts can share individual questions.",
            )
        await cur.execute(
            """SELECT id, kind, canonical_question_id, folder, subject, question_type,
                      question, options, answer_index, answer_text, explanation, mnemonic,
                      image_url, image_alt, difficulty, tags
                 FROM personal_vault_items
                WHERE user_id=%s AND id = ANY(%s)""",
            (user_id, body.item_ids),
        )
        rows = await cur.fetchall()
        if not rows:
            raise HTTPException(404, "No matching Vault items found to share.")
        token = "vsh_" + secrets.token_urlsafe(12)
        await cur.execute(
            """INSERT INTO personal_vault_shares
               (token, owner_id, title, description, mode, duration_minutes, items)
               VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb)
               RETURNING token, title, description, mode, duration_minutes, clones_count, created_at""",
            (
                token,
                user_id,
                body.title.strip(),
                body.description.strip(),
                body.mode,
                body.duration_minutes,
                json.dumps(rows),
            ),
        )
        share = await cur.fetchone()
    return {
        "share": {
            **share,
            "item_count": len(rows),
            "path": f"/vault/share/{token}",
        }
    }


@router.get("/shares/{token}")
async def get_vault_share(token: str) -> dict:
    async with cursor() as cur:
        await cur.execute(
            """SELECT s.token, s.title, s.description, s.mode, s.duration_minutes,
                      s.items, s.clones_count, s.created_at,
                      COALESCE(NULLIF(u.name, ''), 'Finna Learner') AS author_name
                 FROM personal_vault_shares s
                 JOIN users u ON u.id = s.owner_id
                WHERE s.token = %s""",
            (token,),
        )
        row = await cur.fetchone()
    if not row:
        raise HTTPException(404, "Shared Vault pack not found.")
    return {"share": row}


@router.post("/shares/{token}/clone")
async def clone_vault_share(
    token: str,
    user_id: Annotated[str, Depends(require_account)],
) -> dict:
    async with cursor() as cur:
        pro = await _is_pro(cur, user_id)
        await cur.execute(
            "SELECT title, items FROM personal_vault_shares WHERE token=%s",
            (token,),
        )
        share = await cur.fetchone()
        if not share:
            raise HTTPException(404, "Shared Vault pack not found.")

        pack_items = share["items"] or []
        folder_name = (share["title"] or "Shared Pack")[:60]
        added = 0

        if not pro:
            await cur.execute(
                "SELECT count(*)::int AS c FROM personal_vault_items WHERE user_id=%s",
                (user_id,),
            )
            existing_count = (await cur.fetchone())["c"]
            remaining = max(0, FREE_SAVED_LIMIT - existing_count)
            pack_items = pack_items[:remaining]

        for item in pack_items:
            item_id = "vlt_" + uuid4().hex[:16]
            cid = item.get("canonical_question_id")
            kind = "saved" if cid or not pro else (item.get("kind") or "custom")
            if cid:
                await cur.execute(
                    """INSERT INTO personal_vault_items
                       (id, user_id, kind, canonical_question_id, folder, subject, question_type,
                        question, options, answer_index, answer_text, explanation, mnemonic,
                        image_url, image_alt, difficulty, tags)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                       ON CONFLICT (user_id, canonical_question_id)
                       WHERE canonical_question_id IS NOT NULL
                       DO NOTHING""",
                    (
                        item_id,
                        user_id,
                        kind,
                        cid,
                        folder_name,
                        item.get("subject") or "General",
                        item.get("question_type") or "mcq",
                        item.get("question") or "",
                        json.dumps(item.get("options") or []),
                        item.get("answer_index"),
                        item.get("answer_text") or "",
                        item.get("explanation") or "",
                        item.get("mnemonic") or "",
                        item.get("image_url"),
                        item.get("image_alt") or "",
                        item.get("difficulty") or "medium",
                        json.dumps(item.get("tags") or []),
                    ),
                )
            else:
                await cur.execute(
                    """INSERT INTO personal_vault_items
                       (id, user_id, kind, canonical_question_id, folder, subject, question_type,
                        question, options, answer_index, answer_text, explanation, mnemonic,
                        image_url, image_alt, difficulty, tags)
                       VALUES (%s,%s,%s,NULL,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)""",
                    (
                        item_id,
                        user_id,
                        kind,
                        folder_name,
                        item.get("subject") or "General",
                        item.get("question_type") or "mcq",
                        item.get("question") or "",
                        json.dumps(item.get("options") or []),
                        item.get("answer_index"),
                        item.get("answer_text") or "",
                        item.get("explanation") or "",
                        item.get("mnemonic") or "",
                        item.get("image_url"),
                        item.get("image_alt") or "",
                        item.get("difficulty") or "medium",
                        json.dumps(item.get("tags") or []),
                    ),
                )
            added += 1

        await cur.execute(
            "UPDATE personal_vault_shares SET clones_count = clones_count + 1 WHERE token=%s",
            (token,),
        )
    return {"cloned": added, "folder": folder_name}
