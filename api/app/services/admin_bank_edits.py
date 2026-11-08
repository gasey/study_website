"""Explicit final admin corrections; never a synthetic independent review."""
from fastapi import HTTPException
from . import bank_review as service
from .review_policy import digest
from .review_identity import require_role
from .editorial_access import source_version
from .bank_publication import queue,receipt

ALLOWED={'taxonomy','explanation','transcription','source_reference','defect'}
REPORT_KINDS={'taxonomy':{'subject'},'explanation':{'outdated','ambiguous'},
              'transcription':{'typo_ocr'},'source_reference':{'typo_ocr'},'defect':{'ambiguous'}}


async def permitted(cur,actor_id,p,baseline):
    old=baseline['record']['classification'].get('subject_id')
    await require_role(cur,actor_id,old,('owner','publisher'))
    paths=[p.patch.get('classification') or {'subject_id':p.subject_id}]
    if p.kind=='taxonomy':
        paths.extend(baseline['record'].get('relatedClassifications',[]))
        paths.extend(p.patch.get('relatedClassifications',[]))
    for sid in {x['subject_id'] for x in paths if x.get('subject_id')}:
        await require_role(cur,actor_id,sid,('owner','publisher'))


async def eligible(cur,c,r):
    await cur.execute('SELECT * FROM admin_bank_decisions WHERE contribution_id=%s AND revision=%s',(c['id'],c['revision']))
    d=await cur.fetchone()
    if not d:return None
    if d['baseline_hash']!=r['baseline_hash'] or d['payload_hash']!=digest(r['payload']):return False
    from .review_policy import Proposal
    try:await permitted(cur,d['actor_id'],Proposal.model_validate(r['payload']),r['baseline'])
    except HTTPException:return False
    return True


async def decide(cur,actor,p,key,baseline_hash,token,report_ids=(),*,group_export=False):
    if p.kind not in ALLOWED or not p.canonical_id or not p.appearance_id:
        raise HTTPException(422,'Use an existing source question; answer decisions have their own evidence form')
    if p.reverts_publication:raise HTTPException(422,'Use the publication reversal workflow')
    if len(p.rationale.strip())<20:raise HTTPException(422,'Explain the correction in at least 20 characters')
    if not key or len(key)>80:raise HTTPException(422,'A stable request key is required')
    request_hash=digest({'proposal':p.model_dump(mode='json'),'baseline':baseline_hash,'token':token,'reports':sorted(report_ids)})
    await cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',('admin-edit:'+actor.id+':'+key,))
    await cur.execute('SELECT * FROM admin_bank_decisions WHERE actor_id=%s AND request_key=%s',(actor.id,key))
    prior=await cur.fetchone()
    if prior:
        await service.protect_answer(cur,actor.id,prior['canonical_id'])
        await cur.execute('SELECT baseline FROM contribution_revisions WHERE contribution_id=%s AND revision=%s',(prior['contribution_id'],prior['revision']))
        await permitted(cur,actor.id,p,(await cur.fetchone())['baseline'])
        if request_hash!=prior['request_hash']:service.conflict('This request key was used for a different correction')
        return {'decision_id':prior['id'],'contribution_id':prior['contribution_id'],'publication':await receipt(cur,prior['contribution_id']),'replayed':True}
    # Serialise even different request keys aimed at the same shared question.
    await cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',('bank-question:'+p.canonical_id,))
    await service.protect_answer(cur,actor.id,p.canonical_id)
    if token!=await source_version(cur,p.canonical_id,p.appearance_id,True):
        service.conflict('This question changed. Refresh the comparison before saving.')
    snap=await service.snapshot(cur,p.canonical_id,p.appearance_id)
    await permitted(cur,actor.id,p,snap)
    if digest(snap)!=baseline_hash:service.conflict('The source changed. Reopen the correction.')
    if p.kind=='transcription' and 'answerIndex' in p.patch:
        if 'options' not in p.patch:
            raise HTTPException(422,'Use the answer decision form to change an answer; this field only remaps edited options')
        before=snap['record'];old_index=before.get('answerIndex');new_index=p.patch['answerIndex']
        old_answer=before['options'][old_index] if old_index is not None else None
        new_answer=p.patch['options'][new_index] if new_index is not None and new_index<len(p.patch['options']) else None
        if old_answer!=new_answer:
            await cur.execute('''SELECT a.is_primary,c.status,c.key_disputed,c.source_defect FROM appearances a
              JOIN canonical_questions c ON c.id=a.canonical_id WHERE a.id=%s''',(p.appearance_id,))
            state=await cur.fetchone()
            if not state['is_primary'] or state['status']!='live' or state['key_disputed'] or state['source_defect'] in ('duplicate-options','unresolved-source'):
                raise HTTPException(409,'Resolve the source/hold and use the primary appearance before changing the shared answer')
            if new_answer is None:raise HTTPException(422,'Use the answer decision form to clear a recorded answer')
            if not any(e.kind=='official-key' for e in p.evidence) and len(str(p.patch.get('explanation') or '').strip())<20:
                raise HTTPException(422,'A changed correct answer needs a worked explanation or mapped official-key evidence')
    await cur.execute("SELECT id FROM bank_contributions WHERE canonical_id=%s AND state IN ('accepted','publishing') LIMIT 1",(p.canonical_id,))
    pending=await cur.fetchone()
    if pending:service.conflict('A correction is already waiting for publication: '+pending['id'])
    await service.validate_evidence(cur,p,snap) # Reject no-op corrections.
    if report_ids:
        await cur.execute('''SELECT id,kind FROM content_reports WHERE id=ANY(%s) AND canonical_id=%s
          AND status IN ('open','confirmed') FOR SHARE''',(list(report_ids),p.canonical_id))
        reports=await cur.fetchall()
        if len(reports)!=len(report_ids) or any(r['kind'] not in REPORT_KINDS[p.kind] for r in reports):
            raise HTTPException(422,'Link only current matching reports for this correction')
    c=await service.create(cur,actor.id,p,'edit:'+key,expected_baseline_hash=baseline_hash,admin_attestation=True)
    r=await service.revision(cur,c);did=service.uid('adm')
    await cur.execute('''INSERT INTO admin_bank_decisions(id,actor_id,canonical_id,appearance_id,contribution_id,
      revision,kind,baseline_hash,payload_hash,reason,request_key,request_hash)
      VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
      (did,actor.id,p.canonical_id,p.appearance_id,c['id'],c['revision'],p.kind,r['baseline_hash'],digest(r['payload']),p.rationale,key,request_hash))
    for rid in report_ids:await cur.execute('INSERT INTO admin_bank_report_links(decision_id,report_id) VALUES(%s,%s)',(did,rid))
    c=await service.update_state(cur,c,actor.id,'accepted',{'admin_decision':did})
    pub=await queue(cur,c,actor.id,{'admin_edit':{'id':did,'actor_id':actor.id,'kind':p.kind}},group_export=group_export)
    return {'decision_id':did,'contribution_id':c['id'],'publication':pub,'replayed':False}
