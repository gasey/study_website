"""Transactional bank review operations. No function writes bank content."""
from uuid import uuid4
from contextvars import ContextVar
from fastapi import HTTPException
from psycopg.types.json import Jsonb
from .review_identity import grants, require_role
from . import module_intake
from .review_policy import Proposal, digest, validate_target, quorum
from ..source_files import source_pdf_url

# Set only inside the trusted SSH operator process for an explicitly authorized
# run and its exact canonical targets. HTTP requests always use the default.
owner_maintenance_quota_run = ContextVar('owner_maintenance_quota_run', default=None)


def maintenance_scope_allows(scope, actor, proposal):
    """SSH-only scope; taxonomy acceptance never opens a general quota bypass."""
    if (scope.get('owner_id') != actor or proposal.canonical_id not in scope.get('canonical_ids', ())
            or len(scope.get('authorization', '').strip()) < 20):
        return False
    if proposal.kind == 'taxonomy':
        return (scope.get('purpose') == 'owner-taxonomy-publication'
                and 1 <= len(scope['canonical_ids']) <= 100
                and bool(proposal.patch)
                and not set(proposal.patch) - {'classification', 'relatedClassifications'})
    return proposal.kind in ('answer','explanation','transcription','source_reference','defect')


def uid(prefix): return prefix+'_'+uuid4().hex

def conflict(message='This revision changed. Reload and compare before saving.'):
    raise HTTPException(409,message)

async def event(cur, cid, actor, action, detail=None):
    await cur.execute('INSERT INTO contribution_events(contribution_id,actor_id,action,detail) VALUES (%s,%s,%s,%s)',(cid,actor,action,Jsonb(detail or {})))

async def notify(cur, cid, user, key, message):
    await cur.execute('INSERT INTO review_notifications(user_id,contribution_id,event_key,message) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING',(user,cid,key,message))

async def protect_answer(cur,user,qid):
    if not qid: return
    await cur.execute('SELECT 1 FROM mock_sessions WHERE user_id=%s AND submitted_at IS NULL AND %s=ANY(question_ids)',(user,qid))
    if await cur.fetchone(): raise HTTPException(409,'Finish your active mock before opening answer-bearing review content for this question')
    await cur.execute("""SELECT 1 FROM game_members gm JOIN game_rooms gr ON gr.id=gm.room_id
      LEFT JOIN game_cups cup ON cup.id=gr.cup_id WHERE gm.user_id=%s
      AND ((gm.released_at IS NULL AND gr.state IN ('waiting','running')) OR cup.closes_at>now())
      AND gr.questions @> jsonb_build_array(jsonb_build_object('id',%s::text)) LIMIT 1""",(user,qid))
    if await cur.fetchone():raise HTTPException(409,'Finish your game; weekly cup answers unlock after the cup closes')

async def snapshot(cur, canonical_id, appearance_id=None):
    await cur.execute('''SELECT a.id,a.paper_id,a.type,a.question,a.options,a.answer_index,a.answer_source,
        a.answer_key_ref,a.explanation,a.direction,a.question_markup,a.options_markup,a.passage,
        a.difficulty,a.page,a.qnum,a.has_diagram,a.figure_image,a.series,
        p.exam_name,p.year,p.source_file,p.pdf_url,c.source_defect,c.dispute_note,
        qc.subject_id,qc.topic_id,qc.subtopic_id
        FROM appearances a JOIN canonical_questions c ON c.id=a.canonical_id
        JOIN papers p ON p.id=a.paper_id
        LEFT JOIN question_classifications qc ON qc.question_id=c.id AND qc.review_status='approved'
        WHERE c.id=%s AND (%s::text IS NULL OR a.id=%s)
        ORDER BY a.is_primary DESC,a.id LIMIT 1''',(canonical_id,appearance_id,appearance_id))
    row=await cur.fetchone()
    if not row: raise HTTPException(404,'Question appearance not found')
    record={
        'id':row['id'],'paperId':row['paper_id'],'type':row['type'],'question':row['question'],
        'options':row['options'],'answerIndex':row['answer_index'],'answerSource':row['answer_source'],
        'answerKeyRef':row['answer_key_ref'],'explanation':row['explanation'] or None,
        'direction':row['direction'],'questionMarkup':row['question_markup'],'optionsMarkup':row['options_markup'],
        'passage':row['passage'],'difficulty':row['difficulty'],'page':row['page'],'qnum':row['qnum'],
        'hasDiagram':row['has_diagram'],'figureImage':row['figure_image'],
        'classification':{'subject_id':row['subject_id'],'topic_id':row['topic_id'],'subtopic_id':row['subtopic_id']},
    }
    await cur.execute("SELECT subject_id,topic_id,subtopic_id FROM question_topic_links WHERE question_id=%s AND review_status='approved' ORDER BY subject_id,topic_id NULLS FIRST,subtopic_id NULLS FIRST",(canonical_id,))
    related=await cur.fetchall()
    if related:record['relatedClassifications']=[dict(x) for x in related]
    return {'record':record,'metadata':{'sourceDefect':row['source_defect'],'disputeNote':row['dispute_note']},'paper':{'id':row['paper_id'],'title':row['exam_name'],'year':row['year'],
        'series':row['series'],'source_pdf_url':source_pdf_url(row['source_file'],row['pdf_url'])}}

async def validate_evidence(cur, proposal, baseline, allow_noop=False):
    try: validate_target(proposal,baseline.get('record',{}),allow_noop=allow_noop)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc
    if 'difficulty' in proposal.patch and proposal.patch['difficulty']!=baseline.get('record',{}).get('difficulty'):
        raise HTTPException(422,'Difficulty labels are retired. Revise this proposal without a difficulty change.')
    if proposal.reverts_publication:
        await cur.execute("SELECT c.canonical_id,p.state FROM bank_publications p JOIN bank_contributions c ON c.id=p.contribution_id WHERE p.id=%s",(proposal.reverts_publication,))
        original=await cur.fetchone()
        if not original or original['state']!='applied' or original['canonical_id']!=proposal.canonical_id: raise HTTPException(422,'Reversal must target the same currently published question')
    tags_changed=bool(set(proposal.patch)&{'classification','relatedClassifications'})
    path=proposal.patch.get('classification') or (baseline.get('record',{}).get('classification') if tags_changed else None) or {'subject_id':proposal.subject_id}
    if path.get('subject_id')!=proposal.subject_id: raise HTTPException(422,'The taxonomy subject must match the proposal subject')
    related=proposal.patch.get('relatedClassifications',baseline.get('record',{}).get('relatedClassifications',[])) if tags_changed else []
    markers=set()
    for current in [path,*related]:
        marker=tuple(current.get(k) for k in ('subject_id','topic_id','subtopic_id'))
        if marker in markers:raise HTTPException(422,'Primary and related paths must be distinct')
        markers.add(marker)
        parent=None
        for key,level in [('subject_id','subject'),('topic_id','topic'),('subtopic_id','subtopic')]:
            tid=current.get(key)
            if not tid:
                if key=='topic_id' and current.get('subtopic_id'):raise HTTPException(422,'A subtopic requires its topic')
                continue
            await cur.execute('SELECT parent_id,level FROM review_taxonomy WHERE id=%s AND active',(tid,))
            node=await cur.fetchone()
            if not node or node['parent_id']!=parent or node['level']!=level:raise HTTPException(422,'Choose a current subject/topic/subtopic path')
            parent=tid
    for evidence in proposal.evidence:
        if evidence.module_item_id:await module_intake.validate_reference(cur,evidence,proposal,baseline)
        if evidence.document_id:
            await cur.execute('SELECT * FROM review_documents WHERE id=%s',(evidence.document_id,))
            doc=await cur.fetchone()
            if not doc or doc['sha256']!=evidence.sha256: raise HTTPException(422,'Source document is unregistered or its hash changed')
            if evidence.kind=='official-key' and (doc['kind']!='official-key' or doc['key_status']=='superseded'):
                raise HTTPException(422,'The key must be registered and not superseded')
            if evidence.kind=='paper' and baseline.get('paper') and doc['paper_id']!=baseline['paper']['id']:
                raise HTTPException(422,'Printed-paper evidence must match the target paper')
            if evidence.kind=='official-key' and baseline.get('paper'):
                if doc['paper_id']!=baseline['paper']['id'] or evidence.series!=(baseline['paper'].get('series') or None):
                    raise HTTPException(422,'Key evidence must map the exact paper and booklet series')
    if proposal.kind=='new_question':
        await cur.execute('SELECT id FROM canonical_questions WHERE stem_norm=norm_stem(%s) AND options @> %s::jsonb AND options <@ %s::jsonb LIMIT 1',(proposal.patch['question'],Jsonb(proposal.patch['options']),Jsonb(proposal.patch['options'])))
        if await cur.fetchone(): raise HTTPException(409,'This question already exists in the canonical bank; propose an improvement instead')
    if proposal.kind in {'new_question','source_request'} and proposal.patch.get('paperId'):
        await cur.execute('SELECT 1 FROM papers WHERE id=%s',(proposal.patch['paperId'],))
        if not await cur.fetchone(): raise HTTPException(422,'Register the source paper first')
        matching_paper=False
        for evidence in proposal.evidence:
            if evidence.kind=='paper' and evidence.document_id:
                await cur.execute("SELECT 1 FROM review_documents WHERE id=%s AND paper_id=%s AND kind='paper' AND sha256=%s",(evidence.document_id,proposal.patch['paperId'],evidence.sha256))
                matching_paper=matching_paper or bool(await cur.fetchone())
        if not matching_paper:raise HTTPException(422,'Link registered printed-paper evidence for this exact paper')
        if proposal.kind=='new_question':
            if not proposal.patch.get('qnum') or not proposal.patch.get('page'): raise HTTPException(422,'Printed questions require their original number and page')
            await cur.execute('SELECT 1 FROM appearances WHERE paper_id=%s AND qnum=%s',(proposal.patch['paperId'],proposal.patch['qnum']))
            if await cur.fetchone(): raise HTTPException(409,'That printed question is already registered')
    if proposal.kind=='duplicate':
        if proposal.patch.get('duplicateId')==proposal.canonical_id: raise HTTPException(422,'A question cannot duplicate itself')
        await cur.execute('SELECT 1 FROM canonical_questions WHERE id=%s',(proposal.patch.get('duplicateId'),))
        if not await cur.fetchone(): raise HTTPException(422,'Duplicate target not found')

async def load(cur,cid,actor,expected=None,review=False):
    await cur.execute('SELECT * FROM bank_contributions WHERE id=%s FOR UPDATE',(cid,))
    c=await cur.fetchone()
    if not c: raise HTTPException(404,'Contribution not found')
    if review: await require_role(cur,actor,c['subject_id'],('owner','publisher','senior','reviewer'))
    elif c['author_id']!=actor: raise HTTPException(404,'Contribution not found')
    if expected is not None and c['lock_version']!=expected: conflict()
    await protect_answer(cur,actor,c['canonical_id'])
    return c

async def revision(cur,c):
    await cur.execute('SELECT * FROM contribution_revisions WHERE contribution_id=%s AND revision=%s',(c['id'],c['revision']))
    return await cur.fetchone()

async def update_state(cur,c,actor,state,detail=None):
    await cur.execute('UPDATE bank_contributions SET state=%s,lock_version=lock_version+1,updated_at=now() WHERE id=%s RETURNING *',(state,c['id']))
    updated=await cur.fetchone()
    if state in ('accepted','publishing'):
        # PostgreSQL delivers this only when the save transaction commits.
        await cur.execute("SELECT pg_notify('ism_bank_publication','')")
    await event(cur,c['id'],actor,state,detail)
    await notify(cur,c['id'],c['author_id'],f"{c['id']}:{updated['lock_version']}",f"{c['title']}: {state.replace('_',' ')}")
    return updated

async def eligible_reviews(cur,c,r):
    from .admin_bank_edits import eligible
    admin_edit=await eligible(cur,c,r)
    if admin_edit is not None:return admin_edit
    await cur.execute('SELECT * FROM admin_answer_decisions WHERE contribution_id=%s AND revision=%s',(c['id'],c['revision']))
    admin=await cur.fetchone()
    if admin:
        return admin['baseline_hash']==r['baseline_hash'] and admin['payload_hash']==digest(r['payload']) and bool(set(await grants(cur,admin['actor_id'],c['subject_id'],True))&{'owner','publisher'})
    # Trusted SSH maintenance is explicitly recorded, never peer approval.
    await cur.execute("SELECT detail FROM contribution_events WHERE contribution_id=%s AND actor_id='operator:owner-source-maintenance' AND action='operator_source_adjudication' AND detail->>'revision'=%s ORDER BY id DESC LIMIT 1",(c['id'],str(c['revision'])))
    operator=await cur.fetchone()
    if operator:
        d=operator['detail']
        return d.get('baseline_hash')==r['baseline_hash'] and d.get('payload_hash')==digest(r['payload']) and 'owner'in await grants(cur,d.get('owner_id'),None,True)
    await cur.execute('SELECT * FROM contribution_decisions WHERE contribution_id=%s AND revision=%s ORDER BY id',(c['id'],c['revision']))
    eligible=[]
    for d in await cur.fetchall():
        if d['reviewer_id']==c['author_id']: continue
        roles=await grants(cur,d['reviewer_id'],c['subject_id'],True)
        target_subject=r['payload']['patch'].get('classification',{}).get('subject_id',c['subject_id'])
        target_roles=await grants(cur,d['reviewer_id'],target_subject,True) if target_subject!=c['subject_id'] else roles
        related_subjects=set()
        if set(r['payload']['patch'])&{'classification','relatedClassifications'}:
            related_subjects.update(x['subject_id'] for x in r['payload']['patch'].get('relatedClassifications',[]))
            related_subjects.update(x['subject_id'] for x in r['baseline'].get('record',{}).get('relatedClassifications',[]))
        related_ok=True
        for sid in related_subjects:
            if not set(await grants(cur,d['reviewer_id'],sid,True))&{'owner','senior','reviewer'}:related_ok=False
        if set(roles)&{'owner','senior','reviewer'} and set(target_roles)&{'owner','senior','reviewer'} and related_ok: eligible.append((d,roles))
    needed,senior_needed=quorum(c['kind'],r['baseline'].get('record',{}),r['payload']['patch'])
    approvals=[(d,roles) for d,roles in eligible if d['decision']=='approve']
    has_senior=any(set(roles)&{'owner','senior'} for d,roles in approvals)
    return len(approvals)>=needed and (not senior_needed or has_senior) and not any(d['decision']!='approve' for d,roles in eligible)

def require_current_patch(p):
    # Retain the old schema for immutable revisions and idempotent replays.
    # New authoring must never carry or update the retired difficulty field.
    if 'difficulty' in p.patch:
        raise HTTPException(422,'Difficulty labels are retired. Update subject and topic tags only.')

async def create(cur,actor,p,key,expected_baseline_hash=None,additional_module_items=(),admin_attestation=False,source_token=None,require_source_version=False):
    if not key or len(key)>100: raise HTTPException(422,'A stable Idempotency-Key is required')
    payload=p.model_dump(mode='json')
    await cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(actor+':'+key,))
    await cur.execute('SELECT * FROM bank_contributions WHERE author_id=%s AND idempotency_key=%s',(actor,key))
    prior=await cur.fetchone()
    if prior:
        if prior['request_hash']!=digest(payload): conflict('Idempotency key was already used for different content')
        return prior
    require_current_patch(p)
    if admin_attestation:
        # Direct staff maintenance is bounded separately from learner intake.
        # A caller cannot gain this budget merely by setting a Python flag.
        await require_role(cur,actor,p.subject_id,('owner','publisher'))
    await cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))",('review-author:'+actor,))
    await protect_answer(cur,actor,p.canonical_id)
    if p.canonical_id and require_source_version:
        from .editorial_access import require_version
        await require_version(cur,p.canonical_id,p.appearance_id,source_token)
    baseline=await snapshot(cur,p.canonical_id,p.appearance_id) if p.canonical_id else {}
    if expected_baseline_hash is not None and digest(baseline)!=expected_baseline_hash:
        raise HTTPException(409,'The bank changed since this comparison was opened. Refresh before creating the draft.')
    if baseline and baseline['record']['classification'].get('subject_id')!=p.subject_id:
        # Retagging can change the subject, but review permissions follow the old subject until publication.
        if p.kind!='taxonomy': raise HTTPException(422,'Use the question’s current subject')
    await validate_evidence(cur,p,baseline,allow_noop=admin_attestation)
    # An explicitly scoped operator taxonomy run has its own recorded allowance.
    # Do not let that run consume the normal browser editing budget.
    # Both trusted operator records are required; HTTP clients cannot create them.
    await cur.execute("""SELECT count(*)::int AS n FROM bank_contributions c
      WHERE c.author_id=%s AND c.created_at>now()-interval '1 day'
      AND NOT (c.kind='taxonomy' AND EXISTS(
        SELECT 1 FROM contribution_events x JOIN contribution_events a
          ON a.contribution_id=x.contribution_id
        WHERE x.contribution_id=c.id AND x.actor_id='operator:owner-source-maintenance'
          AND x.action='owner_maintenance_quota_exemption'
          AND x.detail->>'owner_id'=c.author_id
          AND a.actor_id='operator:owner-source-maintenance' AND a.action='operator_taxonomy_authorization'
          AND a.detail->>'owner_id'=c.author_id AND a.detail->>'run_id'=x.detail->>'run_id'))""",(actor,))
    limit=500 if admin_attestation else 30
    used=(await cur.fetchone())['n']
    exemption=owner_maintenance_quota_run.get() if admin_attestation else None
    if exemption:
        await require_role(cur,actor,roles=('owner',))
        if not maintenance_scope_allows(exemption,actor,p):
            raise HTTPException(403,'This maintenance target is outside the authorized quota exemption')
    if used>=limit and not exemption: raise HTTPException(429,'Daily staff maintenance limit reached' if admin_attestation else 'Daily contribution limit reached',headers={'Retry-After':'3600'})
    cid=uid('con')
    await cur.execute('''INSERT INTO bank_contributions(id,author_id,canonical_id,appearance_id,kind,subject_id,title,idempotency_key,request_hash)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *''',
        (cid,actor,p.canonical_id,baseline.get('record',{}).get('id'),p.kind,baseline.get('record',{}).get('classification',{}).get('subject_id') or p.subject_id,p.title,key,digest(payload)))
    c=await cur.fetchone()
    await cur.execute('INSERT INTO contribution_revisions(contribution_id,revision,payload,baseline,baseline_hash,actor_id) VALUES (%s,1,%s,%s,%s,%s)',(cid,Jsonb(payload),Jsonb(baseline),digest(baseline),actor))
    await module_intake.link(cur,actor,p,cid,additional_items=additional_module_items)
    await event(cur,cid,actor,'draft')
    if exemption:
        await event(cur,cid,'operator:owner-source-maintenance','owner_maintenance_quota_exemption',
                    {'owner_id':actor,'run_id':exemption['run_id'],'authorization':exemption['authorization'],
                     'canonical_id':p.canonical_id,'ordinary_daily_limit':limit,'observed_last24h':used})
    return c
