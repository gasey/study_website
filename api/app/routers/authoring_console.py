"""Phase V.16 & V.17 (§VII.6.3, §VII.7, §VII.8, §VII.11):
- Symmetric bulk explanation apply (`POST /api/admin/bank/explanations/apply`)
- Symmetric bulk context/currency apply (`POST /api/admin/bank/contexts/apply`)
- Voice lint check (`POST /api/admin/bank/explanations/voice-check`)
- Prefetching authoring queue (`GET /api/admin/bank/authoring-queue`)
- Staff-only SSE batch progress stream (`GET /api/admin/bank/batches/{batch_id}/events`)
- Key-versus-solution conflicts triage (`GET /api/admin/bank/conflicts`,
  `GET /api/admin/bank/conflicts/{qid}`, `POST /api/admin/bank/conflicts/refresh`)

Every mutation preserves every existing bank guard (role, MFA, CSRF, advisory
locks, baseline_hash + source_version, active-assessment holds, immutable
contributions/publications) and routes through `admin_bank_edits.decide()` or
validated `bank_question_contexts` / `bank_paper_profiles` writes.
"""
from __future__ import annotations

import asyncio
import json
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..db import cursor
from ..services import bank_review as service
from ..services.admin_bank_edits import decide
from ..services.bank_organization import signature_sql
from ..services.editorial_access import source_version
from ..services.explanation_voice import check_explanation_voice
from ..services.question_stats import MIN_ATTEMPTS
from ..services.review_identity import Actor, identity, require_role
from ..services.review_policy import Proposal, digest
from .exam_inventory import no_store

router = APIRouter(prefix='/api/admin/bank', tags=['authoring console & conflicts'], dependencies=[Depends(no_store)])

CLUSTER_THRESHOLD = 5  # §VII.6.3 Step 4 #2: >5 conflicts in one paper flags a transcription offset check


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class VoiceCheckIn(StrictModel):
    explanation: str = Field(max_length=12000)


@router.post('/explanations/voice-check')
async def voice_check(body: VoiceCheckIn, actor: Annotated[Actor, Depends(identity)]) -> dict:
    async with cursor() as cur:
        await cur.execute('SELECT 1 FROM review_grants WHERE user_id=%s AND revoked_at IS NULL', (actor.id,))
        if not await cur.fetchone():
            raise HTTPException(403, 'Review permission required')
    warnings = check_explanation_voice(body.explanation)
    return {'warnings': warnings, 'clean': len(warnings) == 0}


class ExplanationTarget(StrictModel):
    question_id: str = Field(min_length=1, max_length=100)
    appearance_id: str = Field(min_length=1, max_length=200)
    baseline_hash: str = Field(pattern=r'^[0-9a-f]{64}$')
    source_version: str = Field(pattern=r'^[0-9a-f]{64}$')
    explanation: str = Field(min_length=20, max_length=12000)


class ExplanationApplyBatch(StrictModel):
    targets: list[ExplanationTarget] = Field(min_length=1, max_length=20)
    reason: str = Field(default='', max_length=4000)

    @model_validator(mode='after')
    def unique_targets(self):
        if len({t.question_id for t in self.targets}) != len(self.targets):
            raise ValueError('Choose each question once')
        self.reason = self.reason.strip()
        return self


@router.post('/explanations/apply')
async def apply_explanations(
    body: ExplanationApplyBatch,
    actor: Annotated[Actor, Depends(identity)],
    idempotency_key: Annotated[str | None, Header()] = None,
) -> dict:
    if not idempotency_key or len(idempotency_key) > 60:
        raise HTTPException(422, 'A stable Idempotency-Key header is required')
    async with cursor() as cur:
        await require_role(cur, actor.id, roles=('owner', 'publisher'))
        from ..services.owner_workflow import is_owner
        owner = await is_owner(cur, actor.id)
        if not owner and len(body.reason) < 20:
            raise HTTPException(422, 'Explain the batch update in at least 20 characters')
        await cur.execute(
            'SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))',
            ('expl-batch:' + actor.id + ':' + idempotency_key,),
        )
        # The batch row is what lets the worker publish these together instead of running
        # one full sync-bank.sh per explanation (§VIII.5.2 #4). It also makes the batch
        # replay-safe as a whole: decide() is already idempotent per target, but the row's
        # UNIQUE(author_id, idempotency_key) would reject a retry without this check.
        await cur.execute(
            'SELECT * FROM bank_retag_batches WHERE author_id = %s AND idempotency_key = %s',
            (actor.id, idempotency_key),
        )
        prior = await cur.fetchone()
        request_hash = digest(body.model_dump(mode='json'))
        if prior:
            if prior['request_hash'] != request_hash:
                raise HTTPException(409, 'This request key belongs to a different batch')
            return {'contribution_ids': prior['contribution_ids'], 'warnings': {},
                    'count': len(prior['contribution_ids']), 'batch_id': prior['id'], 'replayed': True}
        from ..services.bank_publication import require_batch_slot
        await require_batch_slot(cur)
        contributions = []
        voice_warnings = {}
        for target in sorted(body.targets, key=lambda t: t.question_id):
            snap = await service.snapshot(cur, target.question_id, target.appearance_id)
            primary = snap['record']['classification']
            subject_id = primary.get('subject_id') or 'general-knowledge'
            rationale = (
                body.reason
                if len(body.reason) >= 20
                else 'Admin explanation voice cleanup applied via authoring console batch.'
            )
            proposal = Proposal(
                kind='explanation',
                canonical_id=target.question_id,
                appearance_id=target.appearance_id,
                subject_id=subject_id,
                title='Explanation edit: ' + snap['record']['question'][:140],
                patch={'explanation': target.explanation},
                rationale=rationale,
                evidence=[{'kind': 'reasoning', 'note': rationale[:4000]}],
            )
            res = await decide(
                cur,
                actor,
                proposal,
                idempotency_key + ':' + digest(target.question_id)[:12],
                target.baseline_hash,
                target.source_version,
                group_export=True,
            )
            await cur.execute(
                'UPDATE appearances SET explanation_human_edited = true WHERE id = %s',
                (target.appearance_id,),
            )
            contributions.append(res['contribution_id'])
            warns = check_explanation_voice(target.explanation)
            if warns:
                voice_warnings[target.question_id] = warns
        bid = 'expl_' + uuid4().hex
        await cur.execute(
            """INSERT INTO bank_retag_batches(id, author_id, idempotency_key, request_hash, contribution_ids)
               VALUES (%s, %s, %s, %s, %s)""",
            (bid, actor.id, idempotency_key, request_hash, contributions),
        )
    return {'contribution_ids': contributions, 'warnings': voice_warnings, 'count': len(contributions),
            'batch_id': bid, 'replayed': False}


class ContextTarget(StrictModel):
    question_id: str = Field(min_length=1, max_length=100)
    appearance_id: str = Field(min_length=1, max_length=200)
    source_version: str = Field(pattern=r'^[0-9a-f]{64}$')
    time_behavior: Literal['static', 'dated-event', 'changes-over-time', 'unknown'] = 'unknown'
    scheme_status: Literal['current', 'superseded', 'unknown'] = 'unknown'
    superseded_note: str = Field(default='', max_length=1000)
    region: str | None = Field(default=None, max_length=120)

    @model_validator(mode='after')
    def check_superseded(self):
        self.superseded_note = self.superseded_note.strip()
        if self.scheme_status == 'superseded' and len(self.superseded_note) < 20:
            raise ValueError('superseded_note requires at least 20 characters when scheme_status is superseded')
        return self


class ContextApplyBatch(StrictModel):
    targets: list[ContextTarget] = Field(min_length=1, max_length=20)
    paper_period: Literal['legacy', 'current', 'unknown'] | None = None
    reason: str = Field(default='', max_length=4000)

    @model_validator(mode='after')
    def unique_targets(self):
        if len({t.question_id for t in self.targets}) != len(self.targets):
            raise ValueError('Choose each question once')
        self.reason = self.reason.strip()
        return self


@router.post('/contexts/apply')
async def apply_contexts(
    body: ContextApplyBatch,
    actor: Annotated[Actor, Depends(identity)],
    idempotency_key: Annotated[str | None, Header()] = None,
) -> dict:
    if not idempotency_key or len(idempotency_key) > 60:
        raise HTTPException(422, 'A stable Idempotency-Key header is required')
    async with cursor() as cur:
        await require_role(cur, actor.id, roles=('owner', 'publisher'))
        await cur.execute(
            'SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))',
            ('ctx-batch:' + actor.id + ':' + idempotency_key,),
        )
        updated: list[str] = []
        touched_papers: set[str] = set()
        for target in sorted(body.targets, key=lambda t: t.question_id):
            await service.protect_answer(cur, actor.id, target.question_id)
            live_ver = await source_version(cur, target.question_id, target.appearance_id, True)
            if live_ver != target.source_version:
                raise HTTPException(409, f'Question {target.question_id} changed; refresh before applying context')
            await cur.execute(
                f"""SELECT a.paper_id, {signature_sql('a', 'c', 'p')} AS sig
                      FROM appearances a
                      JOIN canonical_questions c ON c.id = a.canonical_id
                      JOIN papers p ON p.id = a.paper_id
                     WHERE a.id = %s AND c.id = %s""",
                (target.appearance_id, target.question_id),
            )
            row = await cur.fetchone()
            if not row:
                raise HTTPException(404, f'Appearance not found for {target.question_id}')
            touched_papers.add(row['paper_id'])
            payload = {
                'time_behavior': target.time_behavior,
                'scheme_status': target.scheme_status,
                **({'superseded_note': target.superseded_note} if target.superseded_note else {}),
                **({'region': target.region} if target.region else {}),
            }
            await cur.execute(
                """INSERT INTO bank_question_contexts
                   (question_id, appearance_id, source_version, source_signature, payload, version, actor_id, updated_at)
                   VALUES (%s,%s,%s,%s,%s::jsonb,1,%s,now())
                   ON CONFLICT (question_id) DO UPDATE SET
                     appearance_id = EXCLUDED.appearance_id,
                     source_version = EXCLUDED.source_version,
                     source_signature = EXCLUDED.source_signature,
                     payload = bank_question_contexts.payload || EXCLUDED.payload,
                     version = bank_question_contexts.version + 1,
                     actor_id = EXCLUDED.actor_id,
                     updated_at = now()""",
                (target.question_id, target.appearance_id, live_ver, row['sig'], json.dumps(payload), actor.id),
            )
            updated.append(target.question_id)

        if body.paper_period and touched_papers:
            for pid in sorted(touched_papers):
                await cur.execute(
                    """INSERT INTO bank_paper_profiles
                       (paper_id, provider_id, period, context_fingerprint, actor_id)
                       VALUES (%s, 'mpsc', %s, %s, %s)
                       ON CONFLICT (paper_id) DO UPDATE SET
                         period = EXCLUDED.period,
                         version = bank_paper_profiles.version + 1,
                         actor_id = EXCLUDED.actor_id,
                         updated_at = now()""",
                    (pid, body.paper_period, digest({'paper_id': pid, 'period': body.paper_period}), actor.id),
                )
    return {'updated_question_ids': updated, 'updated_papers': sorted(touched_papers), 'count': len(updated)}


@router.get('/authoring-queue')
async def authoring_queue(
    actor: Annotated[Actor, Depends(identity)],
    queue: Literal['untagged', 'legacy', 'reported', 'conflicts', 'missed'] = 'untagged',
    limit: int = Query(50, ge=1, le=50),
    offset: int = Query(0, ge=0, le=100000),
) -> dict:
    """Prefetched authoring queue (§VII.11.2): returns question text, options,
    explanation, primary/related classification, context payload, baseline_hash
    and source_version in one round-trip so moving between rows needs zero API calls."""
    async with cursor() as cur:
        await require_role(cur, actor.id, roles=('owner', 'publisher', 'senior', 'reviewer'))
        if queue == 'conflicts':
            await cur.execute(
                """SELECT vc.canonical_id AS id, a.id AS appearance_id, a.paper_id, a.qnum,
                          c.question, c.options, c.explanation,
                          vc.shape, vc.official_answer, vc.solution_answer,
                          qc.subject_id, qc.topic_id, qc.subtopic_id,
                          COALESCE(bp.period, 'unknown') AS period,
                          COALESCE(ctx.payload->>'time_behavior', 'unknown') AS time_behavior,
                          COALESCE(ctx.payload->>'scheme_status', 'unknown') AS scheme_status,
                          COALESCE(ctx.payload->>'superseded_note', '') AS superseded_note
                     FROM v_answer_conflicts vc
                     JOIN canonical_questions c ON c.id = vc.canonical_id
                     JOIN appearances a ON a.canonical_id = c.id AND a.is_primary
                     LEFT JOIN question_classifications qc ON qc.question_id = c.id AND qc.review_status = 'approved'
                     LEFT JOIN bank_paper_profiles bp ON bp.paper_id = a.paper_id
                     LEFT JOIN bank_question_contexts ctx ON ctx.question_id = c.id
                    ORDER BY vc.paper_id, a.qnum_seq NULLS LAST, c.id
                    LIMIT %s OFFSET %s""",
                (limit, offset),
            )
        else:
            # `missed` is exposure ranking (§VII.18.9): the questions learners actually
            # hit and get wrong are far likelier to carry a bad key or a broken
            # transcription than one nobody has opened, so this is the triage list for
            # the V.20 correction loop. It reads `v_question_stats`, which migration
            # 0003 created and indexed and which nothing has read since. MIN_ATTEMPTS
            # is the same population gate the learner-facing bars use.
            where = {
                'untagged': 'qc.subject_id IS NULL',
                'legacy': "COALESCE(bp.period, 'unknown') = 'legacy'",
                'reported': "EXISTS (SELECT 1 FROM content_reports cr WHERE cr.canonical_id = c.id AND cr.status IN ('open','confirmed'))",
                'missed': f'st.attempts >= {MIN_ATTEMPTS} AND st.accuracy <= 0.5',
            }[queue]
            # LATERAL rather than a plain join on the view: correlating it lets the
            # planner reach idx_attempts_canonical per row instead of aggregating the
            # whole attempts table, which is the shape migration 0138 found mattered.
            # Measure on a clone before claiming a number for it (§VII.16).
            order = ('st.attempts DESC NULLS LAST, c.id' if queue == 'missed'
                     else 'a.paper_id, a.qnum_seq NULLS LAST, c.id')
            await cur.execute(
                f"""SELECT c.id, a.id AS appearance_id, a.paper_id, a.qnum,
                           c.question, c.options, c.explanation,
                           qc.subject_id, qc.topic_id, qc.subtopic_id,
                           st.attempts, st.accuracy,
                           COALESCE(bp.period, 'unknown') AS period,
                           COALESCE(ctx.payload->>'time_behavior', 'unknown') AS time_behavior,
                           COALESCE(ctx.payload->>'scheme_status', 'unknown') AS scheme_status,
                           COALESCE(ctx.payload->>'superseded_note', '') AS superseded_note
                      FROM canonical_questions c
                      JOIN appearances a ON a.canonical_id = c.id AND a.is_primary
                      LEFT JOIN question_classifications qc ON qc.question_id = c.id AND qc.review_status = 'approved'
                      LEFT JOIN bank_paper_profiles bp ON bp.paper_id = a.paper_id
                      LEFT JOIN bank_question_contexts ctx ON ctx.question_id = c.id
                      LEFT JOIN LATERAL (SELECT s.attempts, s.accuracy FROM v_question_stats s
                                          WHERE s.canonical_id = c.id) st ON true
                     WHERE c.status = 'live' AND {where}
                     ORDER BY {order}
                     LIMIT %s OFFSET %s""",
                (limit, offset),
            )
        rows = await cur.fetchall()
        enriched = []
        for row in rows:
            snap = await service.snapshot(cur, row['id'], row['appearance_id'])
            ver = await source_version(cur, row['id'], row['appearance_id'])
            # Serve the appearance-level record the correction is diffed against
            # (§VIII.5.1). The list query above reads canonical text, but a
            # transcription/source_reference patch is validated against this
            # snapshot in decide(); the console must edit the same bytes or its
            # no-op and baseline checks disagree with the server. answer_index /
            # answer_source ride along so option edits can re-map the answer, which
            # review_policy.validate_target requires. No extra query: the snapshot
            # was already being fetched to compute baseline_hash.
            rec = snap['record']
            enriched.append({
                **row,
                'question': rec.get('question'),
                'options': rec.get('options') or [],
                'explanation': rec.get('explanation'),
                'answer_index': rec.get('answerIndex'),
                'answer_source': rec.get('answerSource'),
                'qnum': rec.get('qnum'),
                'page': rec.get('page'),
                'baseline_hash': digest(snap),
                'source_version': ver,
                'voice_warnings': check_explanation_voice(rec.get('explanation')),
            })
    return {'queue': queue, 'items': enriched, 'limit': limit, 'offset': offset}


@router.get('/batches/{batch_id}/events')
async def batch_events_sse(batch_id: str, actor: Annotated[Actor, Depends(identity)]):
    """One-way staff-only SSE stream replacing the 12-second batch poll (§VII.11.4)."""
    async with cursor() as cur:
        await require_role(cur, actor.id, roles=('owner', 'publisher', 'senior', 'reviewer'))
        await cur.execute('SELECT contribution_ids FROM bank_retag_batches WHERE id = %s', (batch_id,))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(404, 'Batch not found')
        contribution_ids = list(row['contribution_ids'] or [])

    async def stream():
        for _ in range(30):
            async with cursor() as cur:
                await cur.execute(
                    """SELECT state, count(*)::int AS n
                         FROM bank_contributions
                        WHERE id = ANY(%s)
                        GROUP BY state""",
                    (contribution_ids,),
                )
                counts = {r['state']: r['n'] for r in await cur.fetchall()}
            done = sum(counts.get(s, 0) for s in ('published', 'rejected', 'publication_failed'))
            payload = {'batch_id': batch_id, 'total': len(contribution_ids), 'done': done, 'states': counts}
            yield f'data: {json.dumps(payload)}\n\n'
            if done >= len(contribution_ids):
                break
            await asyncio.sleep(1.5)

    return StreamingResponse(stream(), media_type='text/event-stream')


@router.get('/conflicts')
async def list_conflicts(
    actor: Annotated[Actor, Depends(identity)],
    shape: Literal['all', 'key-won', 'solution-won'] = 'all',
    paper_id: str = Query('', max_length=300),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0, le=100000),
) -> dict:
    """Key-versus-solution conflict triage queue (§VII.6.3 Step 2 & cluster gate)."""
    async with cursor() as cur:
        await require_role(cur, actor.id, roles=('owner', 'publisher', 'senior', 'reviewer'))
        await cur.execute(
            """WITH exposure AS (
                 SELECT canonical_id, count(*)::int AS attempts
                   FROM attempts
                  WHERE canonical_id IN (SELECT canonical_id FROM v_answer_conflicts)
                  GROUP BY canonical_id
               ),
               paper_counts AS (
                 SELECT paper_id, count(*)::int AS paper_conflicts
                   FROM v_answer_conflicts
                  WHERE shape = 'key-won'
                  GROUP BY paper_id
               )
               SELECT vc.canonical_id, vc.paper_id, vc.qnum, vc.shape,
                      vc.official_answer, vc.solution_answer,
                      vc.solution_publication_id, vc.detected_from,
                      c.question,
                      COALESCE(e.attempts, 0)::int AS exposure_attempts,
                      COALESCE(pc.paper_conflicts, 0)::int AS paper_conflicts,
                      (COALESCE(pc.paper_conflicts, 0) > %s) AS cluster_flagged
                 FROM v_answer_conflicts vc
                 JOIN canonical_questions c ON c.id = vc.canonical_id
                 LEFT JOIN exposure e ON e.canonical_id = vc.canonical_id
                 LEFT JOIN paper_counts pc ON pc.paper_id = vc.paper_id
                WHERE (%s = 'all' OR vc.shape = %s)
                  AND (%s = '' OR vc.paper_id = %s)
                ORDER BY cluster_flagged DESC, exposure_attempts DESC, vc.paper_id, vc.canonical_id
                LIMIT %s OFFSET %s""",
            (CLUSTER_THRESHOLD, shape, shape, paper_id, paper_id, limit, offset),
        )
        items = await cur.fetchall()
        await cur.execute(
            """SELECT count(*) FILTER (WHERE shape = 'key-won')::int AS shape_b_count,
                      count(*) FILTER (WHERE shape = 'solution-won')::int AS shape_a_count,
                      count(*)::int AS total
                 FROM v_answer_conflicts"""
        )
        summary = await cur.fetchone()
        await cur.execute(
            """SELECT paper_id, count(*)::int AS conflicts
                 FROM v_answer_conflicts
                WHERE shape = 'key-won'
                GROUP BY paper_id
               HAVING count(*) > %s
                ORDER BY conflicts DESC, paper_id""",
            (CLUSTER_THRESHOLD,),
        )
        clustered_papers = await cur.fetchall()
    return {
        'summary': summary,
        'cluster_threshold': CLUSTER_THRESHOLD,
        'clustered_papers': clustered_papers,
        'items': items,
    }


@router.get('/conflicts/{qid}')
async def conflict_detail(qid: str, actor: Annotated[Actor, Depends(identity)]) -> dict:
    async with cursor() as cur:
        await require_role(cur, actor.id, roles=('owner', 'publisher', 'senior', 'reviewer'))
        await cur.execute(
            """SELECT vc.*, c.question, c.options, c.answer_text, c.answer_source,
                      c.key_disputed, c.dispute_note, c.explanation,
                      (SELECT count(*)::int FROM attempts a WHERE a.canonical_id = c.id) AS exposure_attempts
                 FROM v_answer_conflicts vc
                 JOIN canonical_questions c ON c.id = vc.canonical_id
                WHERE vc.canonical_id = %s""",
            (qid,),
        )
        rows = await cur.fetchall()
        if not rows:
            raise HTTPException(404, 'No active conflict found for this question')
        await cur.execute(
            """SELECT p.id, p.state, p.finished_at, p.manifest->'admin_decision' AS admin_decision
                 FROM bank_publications p
                 JOIN bank_contributions b ON b.id = p.contribution_id
                WHERE b.canonical_id = %s
                ORDER BY p.finished_at DESC NULLS LAST LIMIT 10""",
            (qid,),
        )
        publications = await cur.fetchall()
    return {'canonical_id': qid, 'conflicts': rows, 'publications': publications}


@router.post('/conflicts/refresh')
async def refresh_conflicts(actor: Annotated[Actor, Depends(identity)]) -> dict:
    """Refresh `v_answer_conflicts` and record heartbeat in `worker_heartbeats` (§VII.6.3 Step 4)."""
    async with cursor() as cur:
        await require_role(cur, actor.id, roles=('owner',))
        await cur.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY v_answer_conflicts')
        await cur.execute(
            """SELECT count(*) FILTER (WHERE shape = 'key-won')::int AS shape_b,
                      count(*) FILTER (WHERE shape = 'solution-won')::int AS shape_a
                 FROM v_answer_conflicts"""
        )
        counts = await cur.fetchone()
        note = f"shape_b={counts['shape_b']} shape_a={counts['shape_a']}"
        await cur.execute(
            """INSERT INTO worker_heartbeats(worker, last_beat, last_ok, note)
               VALUES ('answer-conflicts-refresh', now(), now(), %s)
               ON CONFLICT (worker) DO UPDATE SET last_beat = now(), last_ok = now(), note = EXCLUDED.note""",
            (note,),
        )
    return {'refreshed': True, **counts}
