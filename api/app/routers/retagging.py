"""Previewed taxonomy batches reuse immutable contribution revisions and review."""
from typing import Annotated
from uuid import uuid4
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import Field, model_validator
from psycopg.types.json import Jsonb
from ..db import cursor
from ..services import bank_review as service
from ..services.review_identity import Actor, identity, require_role
from ..services.review_policy import Proposal, digest
from ..services.source_identity import identities_for, display_identity
from .exam_inventory import no_store, Strict

router = APIRouter(prefix='/api/admin/bank/retag', tags=['retagging'], dependencies=[Depends(no_store)])
Account = Annotated[Actor, Depends(identity)]


class Target(Strict):
    question_id: str = Field(min_length=1, max_length=100)
    appearance_id: str = Field(min_length=1, max_length=200)


class Selection(Strict):
    targets: list[Target] = Field(min_length=1, max_length=20)

    @model_validator(mode='after')
    def distinct(self):
        if len({t.question_id for t in self.targets}) != len(self.targets):
            raise ValueError('Choose each canonical question only once')
        return self


class Path(Strict):
    subject_id: str = Field(min_length=2, max_length=100)
    topic_id: str | None = Field(default=None, max_length=160)
    subtopic_id: str | None = Field(default=None, max_length=160)


class CheckedTarget(Target):
    baseline_hash: str = Field(pattern=r'^[a-f0-9]{64}$')


class Batch(Strict):
    targets: list[CheckedTarget] = Field(min_length=1, max_length=20)
    classification: Path
    rationale: str = Field(min_length=20, max_length=4000)
    evidence_note: str = Field(min_length=20, max_length=4000)

    @model_validator(mode='after')
    def distinct(self):
        if len({t.question_id for t in self.targets}) != len(self.targets):
            raise ValueError('Choose each canonical question only once')
        return self


async def global_access(cur, actor, write=False):
    # Batch scope crosses papers/subjects. Subject-scoped reviewers retain the
    # existing individual contribution path rather than a broader batch grant.
    return await require_role(cur, actor.id, roles=('owner','publisher') if write else ('owner','publisher','senior','reviewer'))


def content_preview(snapshot):
    return {k: snapshot['record'].get(k) for k in (
        'question','options','classification','relatedClassifications','direction','passage','qnum','page')}


@router.post('/preview')
async def preview(body: Selection, actor: Account):
    async with cursor() as cur:
        await global_access(cur, actor)
        items = []
        for target in body.targets:
            await service.protect_answer(cur, actor.id, target.question_id)
            snap = await service.snapshot(cur, target.question_id, target.appearance_id)
            source = {**snap['paper'], **display_identity(snap['paper']['id'], snap['record']['qnum'],
                      await identities_for(cur, [snap['paper']['id']]))}
            items.append({**target.model_dump(), 'baseline_hash': digest(snap),
                          'record': content_preview(snap), 'source': source})
    return {'items': items}


@router.post('/proposals')
async def proposals(body: Batch, actor: Account, idempotency_key: Annotated[str | None, Header()] = None):
    if not idempotency_key or len(idempotency_key) > 80:
        raise HTTPException(422, 'A stable Idempotency-Key is required')
    async with cursor() as cur:
        await global_access(cur, actor, True)
        await cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))', ('retag:'+actor.id+':'+idempotency_key,))
        await cur.execute('SELECT * FROM bank_retag_batches WHERE author_id=%s AND idempotency_key=%s', (actor.id, idempotency_key))
        prior = await cur.fetchone()
        request_hash = digest(body.model_dump())
        if prior:
            if prior['request_hash'] != request_hash:
                raise HTTPException(409, 'This request key belongs to a different batch')
            return {'id': prior['id'], 'contribution_ids': prior['contribution_ids']}
        contributions = []
        path = body.classification.model_dump()
        marker = lambda p: tuple(p.get(k) for k in ('subject_id','topic_id','subtopic_id'))
        for target in body.targets:
            await service.protect_answer(cur, actor.id, target.question_id)
            snap = await service.snapshot(cur, target.question_id, target.appearance_id)
            if digest(snap) != target.baseline_hash:
                raise HTTPException(409, 'A selected question changed. Refresh the preview before submitting.')
            related = [p for p in snap['record'].get('relatedClassifications', []) if marker(p) != marker(path)]
            proposal = Proposal(kind='taxonomy', canonical_id=target.question_id,
                appearance_id=target.appearance_id, subject_id=path['subject_id'],
                title='Retag: '+snap['record']['question'][:150],
                patch={'classification': path, 'relatedClassifications': related},
                rationale=body.rationale,
                evidence=[{'kind':'reasoning','note':body.evidence_note}])
            # Reject no-op selections, even though the staff budget can allow
            # no-op attestations for other maintenance kinds.
            await service.validate_evidence(cur, proposal, snap)
            c = await service.create(cur, actor.id, proposal,
                idempotency_key+':'+digest(target.question_id)[:12],
                expected_baseline_hash=target.baseline_hash, admin_attestation=True)
            await service.update_state(cur, c, actor.id, 'submitted')
            contributions.append(c['id'])
        batch_id = 'retag_'+uuid4().hex
        await cur.execute('''INSERT INTO bank_retag_batches(id,author_id,idempotency_key,request_hash,contribution_ids)
            VALUES(%s,%s,%s,%s,%s)''', (batch_id,actor.id,idempotency_key,request_hash,contributions))
        return {'id': batch_id, 'contribution_ids': contributions}


@router.get('/batches')
async def batches(actor: Account):
    async with cursor() as cur:
        await global_access(cur, actor)
        await cur.execute('''SELECT id,author_id,created_at,cardinality(contribution_ids) AS questions
            FROM bank_retag_batches ORDER BY created_at DESC,id DESC LIMIT 30''')
        return await cur.fetchall()


@router.get('/batches/{bid}')
async def batch_detail(bid: str, actor: Account):
    async with cursor() as cur:
        roles = await global_access(cur, actor)
        await cur.execute('SELECT id,author_id,contribution_ids,created_at FROM bank_retag_batches WHERE id=%s', (bid,))
        batch = await cur.fetchone()
        if not batch:
            raise HTTPException(404, 'Batch not found')
        await cur.execute('''SELECT c.*,r.payload,r.baseline FROM bank_contributions c
            JOIN contribution_revisions r ON r.contribution_id=c.id AND r.revision=c.revision
            WHERE c.id=ANY(%s) ORDER BY c.id''', (batch['contribution_ids'],))
        items = []
        for c in await cur.fetchall():
            await service.protect_answer(cur, actor.id, c['canonical_id'])
            items.append({k: c[k] for k in ('id','title','state','lock_version','revision','author_id','canonical_id')} | {
                'record': content_preview(c['baseline']), 'source': c['baseline']['paper'],
                'classification': c['payload']['patch']['classification'],
                'rationale': c['payload']['rationale'], 'evidence': c['payload']['evidence'],
                'can_review': c['author_id'] != actor.id and bool(set(roles)&{'owner','senior','reviewer'}) and c['state'] in ('submitted','in_review'),
                'can_publish': bool(set(roles)&{'owner','publisher'}) and c['state'] in ('accepted','publication_failed')})
        return {**batch, 'items': items}
