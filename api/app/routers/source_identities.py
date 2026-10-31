"""Explicit source-cover verification with optimistic locking and audit history."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field, model_validator
from psycopg.types.json import Jsonb
from ..db import cursor
from ..services.review_identity import Actor, identity
from ..services.source_identity import display_identity
from ..source_files import source_pdf_url
from .exam_inventory import no_store, Strict, access, event, json_record, context_fingerprint, protect_paper

router = APIRouter(prefix='/api/admin/bank/inventory', tags=['source identity'], dependencies=[Depends(no_store)])
Account = Annotated[Actor, Depends(identity)]


class Section(Strict):
    title: str = Field(min_length=2, max_length=200)
    qnum_from: int = Field(ge=1, le=100000)
    qnum_to: int = Field(ge=1, le=100000)


class SourceIdentity(Strict):
    paper_id: str = Field(min_length=1, max_length=600)
    expected_version: int = Field(ge=0)
    exam_title: str | None = Field(default=None, min_length=2, max_length=600)
    exam_year: int | None = Field(default=None, ge=1900, le=2100)
    paper_title: str = Field(min_length=2, max_length=600)
    sections: list[Section] = Field(default_factory=list, max_length=30)
    evidence_page: int = Field(ge=1, le=10000)
    reason: str = Field(min_length=20, max_length=4000)
    source_checked: bool
    expected_context: str = Field(pattern=r'^[a-f0-9]{64}$')

    @model_validator(mode='after')
    def validate_sections(self):
        if not self.source_checked:
            raise ValueError('Inspect the source PDF before confirming its identity')
        last = 0
        for section in sorted(self.sections, key=lambda x: x.qnum_from):
            if section.qnum_from <= last or section.qnum_to < section.qnum_from:
                raise ValueError('Section question ranges must be ordered and must not overlap')
            last = section.qnum_to
        return self


async def source_row(cur, pid, lock=False):
    await cur.execute('SELECT id,exam_name,year,source_file,pdf_url FROM papers WHERE id=%s'+(' FOR UPDATE' if lock else ''), (pid,))
    row = await cur.fetchone()
    if not row:
        raise HTTPException(404, 'Paper not found')
    return row


@router.get('/identity')
async def read_identity(actor: Account, paper_id: str = Query(min_length=1, max_length=600)):
    async with cursor() as cur:
        await access(cur, actor)
        await protect_paper(cur, actor, paper_id)
        paper = await source_row(cur, paper_id)
        await cur.execute('SELECT * FROM bank_paper_identities WHERE paper_id=%s', (paper_id,))
        saved = await cur.fetchone()
        context = await context_fingerprint(cur, paper_id)
    return {'saved': saved, 'context': context,
            'context_current': bool(saved and saved['context_fingerprint'] == context),
            'defaults': {'exam_title': paper['exam_name'], 'exam_year': paper['year'],
                         'paper_title': display_identity(paper_id, None, {})['paper_label'] or '',
                         'sections': [], 'evidence_page': 1}}


@router.post('/identity')
async def save_identity(body: SourceIdentity, actor: Account):
    async with cursor() as cur:
        await access(cur, actor, True)
        await protect_paper(cur, actor, body.paper_id)
        paper = await source_row(cur, body.paper_id, True)
        if not source_pdf_url(paper['source_file'],paper['pdf_url']):
            raise HTTPException(422, 'Link a source PDF before verifying its identity')
        # Lock the paper as well, so two first-time saves cannot race.
        await cur.execute('SELECT * FROM bank_paper_identities WHERE paper_id=%s FOR UPDATE', (body.paper_id,))
        before = await cur.fetchone()
        if body.expected_version != (before['version'] if before else 0):
            raise HTTPException(409, 'This identity changed. Reload it before saving.')
        context = await context_fingerprint(cur, body.paper_id)
        if context != body.expected_context:
            raise HTTPException(409, 'The source context changed. Reload and inspect it again.')
        metadata = body.model_dump(exclude={'paper_id', 'expected_version', 'expected_context', 'reason', 'source_checked'})
        metadata['sections'].sort(key=lambda s: s['qnum_from'])
        ref = {k: paper[k] for k in ('source_file', 'pdf_url')}
        await cur.execute('''INSERT INTO bank_paper_identities(paper_id,metadata,source_ref,context_fingerprint,updated_by)
            VALUES(%s,%s,%s,%s,%s) ON CONFLICT(paper_id) DO UPDATE SET metadata=excluded.metadata,
            source_ref=excluded.source_ref,context_fingerprint=excluded.context_fingerprint,
            updated_by=excluded.updated_by,updated_at=now(),version=bank_paper_identities.version+1 RETURNING *''',
            (body.paper_id, Jsonb(metadata), Jsonb(ref), context, actor.id))
        row = await cur.fetchone()
        await event(cur, actor, 'source_identity_verified', body.paper_id,
                    json_record(before), json_record(row), body.reason)
    return row
