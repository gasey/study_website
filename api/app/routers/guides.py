"""Phase V.15 (§VII.5, §VII.16.5): First-party Guides reading library API.

Strictly separate from user-generated `materials`. Public reads return only
`status='published'` guides (free to read); owner/editorial mutations require
staff identity + owner role. Includes Postgres full-text search over guides and
chapters (`tsvector` GIN indexes from migration 0136).
"""
from __future__ import annotations

from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from ..db import cursor
from ..services.review_identity import Actor, identity, require_role

router = APIRouter(prefix='/api/guides', tags=['guides'])


class GuideChapterIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    ord: int = Field(ge=1, le=500)
    anchor: str = Field(pattern=r'^[a-z0-9][a-z0-9-]{0,80}$')
    heading: str = Field(min_length=2, max_length=240)
    body_markdown: str = Field(min_length=10, max_length=80000)
    question_ids: list[str] = Field(default_factory=list, max_length=200)


class GuideUpsert(BaseModel):
    model_config = ConfigDict(extra='forbid')
    slug: str = Field(pattern=r'^[a-z0-9][a-z0-9-]{1,100}$')
    title: str = Field(min_length=2, max_length=200)
    subject_id: str | None = Field(default=None, max_length=100)
    topic_id: str | None = Field(default=None, max_length=160)
    exam_scope: list[str] = Field(default_factory=list, max_length=20)
    summary: str = Field(min_length=10, max_length=1000)
    reading_minutes: int = Field(default=5, ge=1, le=240)
    status: Literal['draft', 'published', 'archived'] = 'draft'
    chapters: list[GuideChapterIn] = Field(min_length=1, max_length=100)


@router.get('')
async def list_guides(
    q: str = Query('', max_length=160),
    subject_id: str = Query('', max_length=100),
    exam: str = Query('', max_length=80),
) -> dict:
    search = q.strip()
    async with cursor() as cur:
        await cur.execute(
            """SELECT g.id, g.slug, g.title, g.subject_id, g.topic_id, g.exam_scope,
                      g.summary, g.reading_minutes, g.status, g.version, g.updated_at,
                      (SELECT count(*)::int FROM guide_chapters gc WHERE gc.guide_id = g.id) AS chapter_count,
                      (SELECT count(*)::int FROM guide_questions gq WHERE gq.guide_id = g.id) AS question_count
                 FROM guides g
                WHERE g.status = 'published'
                  AND (%s = '' OR g.subject_id = %s)
                  AND (%s = '' OR %s = ANY(g.exam_scope))
                  AND (
                    %s = ''
                    OR g.search @@ plainto_tsquery('english', %s)
                    OR EXISTS (
                      SELECT 1 FROM guide_chapters gc
                       WHERE gc.guide_id = g.id
                         AND gc.search @@ plainto_tsquery('english', %s)
                    )
                  )
                ORDER BY g.updated_at DESC, g.title""",
            (subject_id, subject_id, exam, exam, search, search, search),
        )
        items = await cur.fetchall()
    return {'items': items}


@router.get('/{slug}')
async def get_guide(slug: str) -> dict:
    async with cursor() as cur:
        await cur.execute(
            """SELECT id, slug, title, subject_id, topic_id, exam_scope,
                      summary, reading_minutes, status, version, review_due, updated_at
                 FROM guides
                WHERE slug = %s AND status = 'published'""",
            (slug,),
        )
        guide = await cur.fetchone()
        if not guide:
            raise HTTPException(404, 'Guide not found')
        await cur.execute(
            """SELECT ord, anchor, heading, body_markdown
                 FROM guide_chapters
                WHERE guide_id = %s
                ORDER BY ord""",
            (guide['id'],),
        )
        chapters = await cur.fetchall()
        await cur.execute(
            """SELECT gq.chapter_anchor, gq.question_id, gq.ord
                 FROM guide_questions gq
                 JOIN canonical_questions cq ON cq.id = gq.question_id AND cq.status = 'live'
                WHERE gq.guide_id = %s
                ORDER BY gq.chapter_anchor, gq.ord""",
            (guide['id'],),
        )
        q_rows = await cur.fetchall()
    by_anchor: dict[str, list[str]] = {}
    for row in q_rows:
        by_anchor.setdefault(row['chapter_anchor'], []).append(row['question_id'])
    return {
        **guide,
        'chapters': [
            {**ch, 'question_ids': by_anchor.get(ch['anchor'], [])}
            for ch in chapters
        ],
    }


@router.post('/admin')
async def upsert_guide(body: GuideUpsert, actor: Annotated[Actor, Depends(identity)]) -> dict:
    async with cursor() as cur:
        await require_role(cur, actor.id, roles=('owner',))
        # Validate every linked question exists and is live.
        all_qids = list({qid for ch in body.chapters for qid in ch.question_ids})
        if all_qids:
            await cur.execute(
                "SELECT id FROM canonical_questions WHERE id = ANY(%s) AND status = 'live'",
                (all_qids,),
            )
            found = {row['id'] for row in await cur.fetchall()}
            missing = sorted(set(all_qids) - found)
            if missing:
                raise HTTPException(422, f'Unknown or non-live guide questions: {", ".join(missing[:5])}')

        await cur.execute('SELECT id, version FROM guides WHERE slug = %s FOR UPDATE', (body.slug,))
        existing = await cur.fetchone()
        if existing:
            guide_id = existing['id']
            new_version = existing['version'] + 1
            await cur.execute(
                """UPDATE guides
                      SET title = %s, subject_id = %s, topic_id = %s, exam_scope = %s,
                          summary = %s, reading_minutes = %s, status = %s,
                          version = %s, updated_by = %s, updated_at = now()
                    WHERE id = %s""",
                (
                    body.title, body.subject_id, body.topic_id, body.exam_scope,
                    body.summary, body.reading_minutes, body.status,
                    new_version, actor.id, guide_id,
                ),
            )
            await cur.execute('DELETE FROM guide_chapters WHERE guide_id = %s', (guide_id,))
        else:
            guide_id = 'guide_' + uuid4().hex[:16]
            new_version = 1
            await cur.execute(
                """INSERT INTO guides
                   (id, slug, title, subject_id, topic_id, exam_scope, summary,
                    reading_minutes, status, version, created_by, updated_by)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,1,%s,%s)""",
                (
                    guide_id, body.slug, body.title, body.subject_id, body.topic_id,
                    body.exam_scope, body.summary, body.reading_minutes, body.status,
                    actor.id, actor.id,
                ),
            )

        for ch in body.chapters:
            await cur.execute(
                """INSERT INTO guide_chapters(guide_id, ord, anchor, heading, body_markdown)
                   VALUES (%s,%s,%s,%s,%s)""",
                (guide_id, ch.ord, ch.anchor, ch.heading, ch.body_markdown),
            )
            for idx, qid in enumerate(dict.fromkeys(ch.question_ids), start=1):
                await cur.execute(
                    """INSERT INTO guide_questions(guide_id, chapter_anchor, question_id, ord)
                       VALUES (%s,%s,%s,%s)""",
                    (guide_id, ch.anchor, qid, idx),
                )
    return {'id': guide_id, 'slug': body.slug, 'version': new_version, 'status': body.status}
