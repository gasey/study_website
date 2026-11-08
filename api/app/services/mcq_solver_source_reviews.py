"""Source-inspected pilot notes, separate from original and published answers."""
import json
from pathlib import Path

from fastapi import HTTPException

from . import bank_review as review
from . import mcq_solver_drafts as solver
from .review_identity import require_role
from .review_policy import Proposal, digest


def catalog():
    return json.loads((Path(__file__).resolve().parents[1] / 'data/mcq-solver-source-review-20261106.json').read_text())


async def current(cur, actor, item):
    source = await solver._capture(cur, actor, item['canonical_id'], item['id'])
    record = source['snapshot']['record']
    expected = item['expected']
    matches = all(record.get(key) == expected.get(key) for key in ('id', 'paperId', 'question', 'options', 'page'))
    matches = matches and str(record.get('qnum')) == str(expected.get('qnum'))
    matches = matches and any(d['id'] == item['document_id'] and d['sha256'] == item['source_sha256'] and d['kind'] == 'paper' for d in source['documents'])
    return source, matches


async def listing(cur, actor):
    from .mfa import staff_exempt
    await require_role(cur, actor.id, roles=('owner', 'publisher'))
    report = catalog()
    items = []
    for item in report['items']:
        try:
            source, matches = await current(cur, actor, item)
            versions = {'source_version': source['source_version'], 'question_version_hash': digest(source)}
            source_url = source['snapshot']['paper']['source_pdf_url']
        except HTTPException as error:
            if error.status_code not in (404, 422):
                raise
            matches, source_url, versions = False, None, {}
        # Original raw model drafts are retained in the private ledger, not sent
        # as recommendations in the source-reviewed page.
        safe = {k: v for k, v in item.items() if k != 'initial_draft'}
        items.append({**safe, **versions, 'source_url': source_url, 'stale': not matches})
    return {'id': report['id'], 'reviewed_on': report['reviewed_on'],
            'review_kind': 'ai_source_inspection', 'human_approval': None,
            'can_save': bool((actor.mfa_verified or staff_exempt(actor.id)) and actor.recent), 'items': items}


async def stage(cur, actor, appearance_id, source_token, question_hash):
    await solver.authorize(cur, actor)
    report = catalog()
    item = next((i for i in report['items'] if i['id'] == appearance_id), None)
    if not item:
        raise HTTPException(404, 'Pilot source not found')
    key = 'mcq-source:' + digest([report['id'], item, source_token, question_hash])
    await cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))', (actor.id + ':' + key,))
    await cur.execute('SELECT id,state FROM bank_contributions WHERE author_id=%s AND idempotency_key=%s', (actor.id, key))
    prior = await cur.fetchone()
    if prior:
        return {'contribution_id': prior['id'], 'state': prior['state'], 'published_by_worker': False}
    source, matches = await current(cur, actor, item)
    if not matches or source_token != source['source_version'] or question_hash != digest(source):
        raise HTTPException(409, 'This source changed after inspection. Reload and compare before saving a draft.')
    if item['decision'] == 'source_checked_draft':
        selected = item['selected_option_id']
        if selected not in {str(i) for i in range(len(source['snapshot']['record']['options']))}:
            raise HTTPException(422, 'Inspected answer does not map to this source')
        kind = 'answer'
        patch = {'answerIndex': int(selected), 'answerSource': 'derived', 'explanation': item['draft_explanation']}
    else:
        kind = 'defect'
        patch = {'sourceDefect': 'unresolved-source', 'disputeNote': item['finding']}
    proposal = Proposal(kind=kind, canonical_id=item['canonical_id'], appearance_id=item['id'],
        subject_id=source['snapshot']['record']['classification']['subject_id'],
        title='Source-inspected AI draft: ' + item['title'], patch=patch,
        rationale='AI-assisted source inspection; no independent human approval. ' + item['finding'] + '\nProposed next step: ' + item['repair'],
        evidence=[{'kind': 'paper', 'document_id': item['document_id'], 'sha256': item['source_sha256'],
                   'page': item['expected']['page'], 'note': 'Compared the original physical page and printed question format; source-backed AI review retained as a draft.'}])
    contribution = await review.create(cur, actor.id, proposal, key,
        expected_baseline_hash=digest(source['snapshot']), source_token=source_token, require_source_version=True)
    await review.event(cur, contribution['id'], actor.id, 'mcq_solver_source_draft', {
        'review_id': report['id'], 'review_kind': 'ai_source_inspection', 'human_approval': None,
        'decision': item['decision'], 'source_sha256': item['source_sha256']})
    return {'contribution_id': contribution['id'], 'state': contribution['state'], 'published_by_worker': False}
