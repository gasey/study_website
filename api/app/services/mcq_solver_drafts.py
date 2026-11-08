"""Narrow, authenticated solver integration. Creates review drafts only.

There is intentionally no HTTP route, standalone database credential or publication
operation here. An eventual caller must supply the real MFA-authenticated Actor;
neither an inference model nor a worker-provided actor ID is authorization.
An explicit operator-managed account MFA exception is also honoured; recent
sign-in and the owner/publisher role remain required.
"""
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field

from . import bank_review as review
from .editorial_access import source_version
from .review_identity import Actor, require_role
from .review_policy import Proposal, digest


class DraftResult(BaseModel):
    model_config = ConfigDict(extra='forbid')
    canonical_id: str = Field(min_length=1, max_length=100)
    appearance_id: str = Field(min_length=1, max_length=200)
    source_version: str = Field(pattern=r'^[0-9a-f]{64}$')
    question_version_hash: str = Field(pattern=r'^[0-9a-f]{64}$')
    selected_option_id: str | None = Field(max_length=2)
    explanation: str = Field(min_length=40, max_length=12000)
    certainty: Literal['confident', 'uncertain', 'cannot_determine']
    review_reasons: list[str] = Field(max_length=20)
    model_id: str = Field(min_length=1, max_length=100)
    reasoning: str = Field(min_length=1, max_length=40)
    prompt_version: str = Field(min_length=1, max_length=100)
    solver_run_id: str = Field(min_length=1, max_length=100)


async def authorize(cur, actor):
    from .mfa import staff_exempt
    if not isinstance(actor, Actor) or not (actor.mfa_verified or staff_exempt(actor.id)) or not actor.recent:
        raise HTTPException(403, 'A recent owner sign-in and the account security requirement are needed')
    await require_role(cur, actor.id, roles=('owner', 'publisher'))


async def _capture(cur, actor, canonical_id, appearance_id):
    await review.protect_answer(cur, actor.id, canonical_id)
    version = await source_version(cur, canonical_id, appearance_id, lock=True)
    snap = await review.snapshot(cur, canonical_id, appearance_id)
    await cur.execute('SELECT to_jsonb(c) AS record FROM canonical_questions c WHERE id=%s', (canonical_id,))
    canonical = (await cur.fetchone())['record']
    if canonical['status'] in ('merged', 'withdrawn') or snap['record']['type'] != 'mcq':
        raise HTTPException(422, 'Select an existing MCQ that is neither merged nor withdrawn')
    if not snap['record']['classification'].get('subject_id'):
        raise HTTPException(422, 'An approved subject is required before creating a solver draft')
    opts = snap['record']['options']
    if not isinstance(opts, list) or not 2 <= len(opts) <= 8 or any(not isinstance(o, str) or not o.strip() for o in opts):
        raise HTTPException(422, 'Incomplete printed options need source repair first')
    await cur.execute('SELECT id,sha256,kind,key_status FROM review_documents WHERE paper_id=%s ORDER BY id FOR SHARE', (snap['paper']['id'],))
    documents = await cur.fetchall()
    return {'canonical_id': canonical_id, 'appearance_id': snap['record']['id'],
            'snapshot': snap, 'canonical': canonical, 'documents': documents,
            'source_version': version}


async def capture(cur, actor: Actor, canonical_id: str, appearance_id: str):
    """Authoritative comparison record. Do not send its keys to blind inference."""
    await authorize(cur, actor)
    result = await _capture(cur, actor, canonical_id, appearance_id)
    return {**result, 'question_version_hash': digest(result)}


def proposal_for(data: DraftResult, source):
    record = source['snapshot']['record']
    options = record['options']
    if data.selected_option_id is None or data.certainty == 'cannot_determine':
        raise HTTPException(422, 'Unsolved output stays in the local review queue')
    valid = {str(i): i for i in range(len(options))}
    if data.selected_option_id not in valid:
        raise HTTPException(422, 'The selected option does not match this printed appearance')
    if any(len(reason) < 3 or len(reason) > 1000 for reason in data.review_reasons):
        raise HTTPException(422, 'Review reasons must be substantive and bounded')
    selected = valid[data.selected_option_id]
    same_official = record.get('answerSource') in ('official', 'key') and record.get('answerIndex') == selected
    kind = 'explanation' if same_official else 'answer'
    patch = {'explanation': data.explanation}
    if kind == 'answer':
        patch.update(answerIndex=selected, answerSource='derived')
    disagreement = record.get('answerSource') in ('official', 'key') and record.get('answerIndex') is not None and record['answerIndex'] != selected
    rationale = (f'Unreviewed AI solver draft; human approval is pending. Reported model: {data.model_id}; '
                 f'reasoning: {data.reasoning}; prompt: {data.prompt_version}; run: {data.solver_run_id}. '
                 f'Certainty: {data.certainty}. Official-key disagreement: {disagreement}. '
                 + 'Review reasons: ' + '; '.join(data.review_reasons))
    return Proposal(kind=kind, canonical_id=data.canonical_id, appearance_id=data.appearance_id,
                    subject_id=record['classification']['subject_id'], title='AI solver draft awaiting source review',
                    patch=patch, rationale=rationale[:8000],
                    evidence=[{'kind': 'reasoning', 'note': 'AI-generated explanation retained for human inspection; no independent source or reasoning verification has been asserted.'}])


async def save(cur, actor: Actor, data: DraftResult):
    """At most one immutable contribution per exact result; never submits it."""
    await authorize(cur, actor)
    key = 'mcq-solver:' + digest(data.model_dump(mode='json'))
    await cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))', (actor.id + ':' + key,))
    # Reconcile an exact saved result even if its source has since changed. This
    # path returns a receipt only; it never makes another draft or edits history.
    await cur.execute('SELECT id,state,revision FROM bank_contributions WHERE author_id=%s AND idempotency_key=%s', (actor.id, key))
    prior = await cur.fetchone()
    if prior:
        return {'contribution_id': prior['id'], 'state': prior['state'], 'replayed': True, 'published_by_worker': False}
    source = await _capture(cur, actor, data.canonical_id, data.appearance_id)
    if source['source_version'] != data.source_version or digest(source) != data.question_version_hash:
        raise HTTPException(409, 'The exact source changed; discard the stale solver output')
    proposal = proposal_for(data, source)
    c = await review.create(cur, actor.id, proposal, key,
                            expected_baseline_hash=digest(source['snapshot']),
                            source_token=data.source_version, require_source_version=True)
    # review.create alone leaves this in draft. No human attestations, decisions,
    # quota exemptions, submit transitions or publication jobs are created.
    await review.event(cur, c['id'], actor.id, 'mcq_solver_unreviewed_draft', {
        'question_version_hash': data.question_version_hash, 'model_id': data.model_id,
        'reasoning': data.reasoning, 'prompt_version': data.prompt_version,
        'solver_run_id': data.solver_run_id, 'certainty': data.certainty,
        'review_reasons': data.review_reasons, 'human_approval': None})
    return {'contribution_id': c['id'], 'state': c['state'], 'replayed': False, 'published_by_worker': False}
