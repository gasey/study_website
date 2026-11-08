"""Previewed taxonomy batches reuse immutable contribution revisions and review."""
from typing import Annotated,Literal
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


@router.get('/progress')
async def taxonomy_progress(actor:Account):
    from ..services.taxonomy_review_progress import progress
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner','publisher','senior','reviewer'),lock=False)
        return await progress(cur)


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
            from ..services.editorial_access import source_version
            items[-1]['source_version']=await source_version(cur,target.question_id,target.appearance_id)
            await cur.execute('SELECT count(*)::int AS n FROM appearances WHERE canonical_id=%s',(target.question_id,))
            items[-1]['shared_papers']=(await cur.fetchone())['n']
    return {'items': items}


class FinalTarget(CheckedTarget):
    source_version:str=Field(pattern=r'^[a-f0-9]{64}$')

class FinalBatch(Strict):
    targets:list[FinalTarget]=Field(min_length=1,max_length=20)
    classification:Path
    operation:Literal['replace_primary','add_related','remove_related']='replace_primary'
    reason:str=Field(default='',max_length=4000)

    @model_validator(mode='after')
    def unique(self):
        if len({t.question_id for t in self.targets})!=len(self.targets):raise ValueError('Choose each question once')
        self.reason=self.reason.strip()
        return self

@router.post('/apply')
async def apply_tags(body:FinalBatch,actor:Account,idempotency_key:Annotated[str|None,Header()]=None):
    from ..services.admin_bank_edits import decide
    if not idempotency_key or len(idempotency_key)>60:raise HTTPException(422,'A stable request key is required')
    async with cursor() as cur:
        await global_access(cur,actor,True)
        from ..services.owner_workflow import is_owner,change_summary
        owner=await is_owner(cur,actor.id)
        if not owner and len(body.reason)<20:raise HTTPException(422,'Explain the tag correction in at least 20 characters')
        await cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',('retag-final:'+actor.id+':'+idempotency_key,))
        await cur.execute('SELECT * FROM bank_retag_batches WHERE author_id=%s AND idempotency_key=%s',(actor.id,idempotency_key))
        prior=await cur.fetchone();request_hash=digest(body.model_dump())
        if prior:
            if prior['request_hash']!=request_hash:raise HTTPException(409,'This request key belongs to a different batch')
            return {'id':prior['id'],'contribution_ids':prior['contribution_ids'],'replayed':True}
        from ..services.bank_publication import require_batch_slot
        await require_batch_slot(cur)
        path=body.classification.model_dump();marker=lambda p:tuple(p.get(k) for k in ('subject_id','topic_id','subtopic_id'))
        contributions=[]
        # Deterministic lock order prevents cross-batch deadlocks; transaction rolls back all on failure.
        for target in sorted(body.targets,key=lambda t:t.question_id):
            snap=await service.snapshot(cur,target.question_id,target.appearance_id)
            related=snap['record'].get('relatedClassifications',[])
            primary=snap['record']['classification']
            if body.operation=='replace_primary':primary=path;related=[p for p in related if marker(p)!=marker(path)]
            elif body.operation=='add_related':related=[*related,path]
            else:
                if not any(marker(p)==marker(path) for p in related):raise HTTPException(422,'The selected related path is not present on every selected question')
                related=[p for p in related if marker(p)!=marker(path)]
            summary=change_summary(snap['record'],'taxonomy',{'classification':primary,'relatedClassifications':related})
            reason=(summary+(' Owner note: '+body.reason if body.reason else '')) if owner else body.reason
            p=Proposal(kind='taxonomy',canonical_id=target.question_id,appearance_id=target.appearance_id,
              subject_id=primary['subject_id'],title='Admin tags: '+snap['record']['question'][:140],
              patch={'classification':primary,'relatedClassifications':related},rationale=reason,
              evidence=[{'kind':'reasoning','note':reason[:4000]}])
            result=await decide(cur,actor,p,idempotency_key+':'+digest(target.question_id)[:12],target.baseline_hash,target.source_version,group_export=True)
            contributions.append(result['contribution_id'])
        bid='retag_'+uuid4().hex
        await cur.execute('''INSERT INTO bank_retag_batches(id,author_id,idempotency_key,request_hash,contribution_ids)
          VALUES(%s,%s,%s,%s,%s)''',(bid,actor.id,idempotency_key,request_hash,contributions))
        return {'id':bid,'contribution_ids':contributions,'replayed':False}


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

class RetryBatch(Strict):
    expected_versions:dict[str,int]=Field(min_length=1,max_length=20)

@router.post('/batches/{bid}/retry')
async def retry_batch(bid:str,body:RetryBatch,actor:Account):
    from ..services.admin_bank_edits import eligible
    async with cursor() as cur:
        await global_access(cur,actor,True)
        await cur.execute('SELECT contribution_ids FROM bank_retag_batches WHERE id=%s FOR UPDATE',(bid,))
        batch=await cur.fetchone()
        if not batch:raise HTTPException(404,'Tag batch not found')
        await cur.execute('SELECT * FROM bank_contributions WHERE id=ANY(%s) ORDER BY id FOR UPDATE',(batch['contribution_ids'],))
        items=await cur.fetchall()
        if {c['id']:c['lock_version'] for c in items}!=body.expected_versions:raise HTTPException(409,'Batch status changed. Refresh before retrying.')
        failed=[c for c in items if c['state']=='publication_failed']
        if not failed:raise HTTPException(409,'No failed publications to retry')
        for c in items:
            await service.protect_answer(cur,actor.id,c['canonical_id'])
            if not await eligible(cur,c,await service.revision(cur,c)):raise HTTPException(403,'A current final admin tag decision is required for every item')
        from ..services.bank_publication import require_batch_slot,STALE_EXPORT_ERRORS
        await cur.execute('SELECT bank_checksum FROM sync_log WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1')
        sync=await cur.fetchone()
        for c in failed:
            await cur.execute('SELECT error,manifest FROM bank_publications WHERE contribution_id=%s AND revision=%s',(c['id'],c['revision']))
            pub=await cur.fetchone()
            if pub and sync and pub['error'] in STALE_EXPORT_ERRORS and pub['manifest']['bank_sha256']!=sync['bank_checksum']:
                raise HTTPException(409,'This tag export uses an older bank snapshot. Reopen the current questions and save a fresh batch.')
        await require_batch_slot(cur)
        for c in failed:
            await cur.execute("UPDATE bank_publications SET state='exported',error=NULL WHERE contribution_id=%s AND revision=%s AND state='failed'",(c['id'],c['revision']))
            await cur.execute("UPDATE review_outbox SET finished_at=NULL,last_error=NULL WHERE event_key IN (SELECT id FROM bank_publications WHERE contribution_id=%s AND revision=%s)",(c['id'],c['revision']))
            await service.update_state(cur,c,actor.id,'publishing',{'batch':bid,'reason':'Retry the same immutable admin tag decisions; source and journal checks still apply.'})
        return {'id':bid,'state':'publishing'}


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
                'classification': c['payload']['patch'].get('classification',c['baseline']['record']['classification']),
                'relatedClassifications':c['payload']['patch'].get('relatedClassifications',[]),
                'rationale': c['payload']['rationale'], 'evidence': c['payload']['evidence'],
                'can_review': c['author_id'] != actor.id and bool(set(roles)&{'owner','senior','reviewer'}) and c['state'] in ('submitted','in_review'),
                'can_publish': bool(set(roles)&{'owner','publisher'}) and c['state'] in ('accepted','publication_failed')})
        return {**batch, 'items': items}
