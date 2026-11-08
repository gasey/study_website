"""One transactionally queued publication path for reviewed bank corrections."""
from fastapi import HTTPException
from psycopg.types.json import Jsonb
from . import bank_review as service
from .review_identity import require_role
from .review_policy import Proposal,digest
from ..config import settings


STALE_EXPORT_ERRORS={'Bank snapshot changed since review export','Bank snapshot changed since the tag preview; reopen the corrections'}

async def export_slot(cur,group=False,from_intent=False):
    if not settings.publication_serial_queue:return True
    await cur.execute("SELECT pg_try_advisory_xact_lock(hashtextextended('bank-publication-export',0)) AS acquired")
    if not (await cur.fetchone())['acquired']:return False
    await cur.execute("SELECT 1 FROM bank_publications WHERE state='exported' LIMIT 1")
    if await cur.fetchone():return False
    if not from_intent:
        await cur.execute("SELECT 1 FROM review_outbox WHERE kind='publication-intent' AND finished_at IS NULL LIMIT 1")
        if await cur.fetchone():return False
    return True

async def require_batch_slot(cur):
    if not await export_slot(cur,group=True):
        service.conflict('Another publication is ahead of this tag batch. Wait for it to finish, then apply the batch.')

async def defer(cur,c,actor_id,extra):
    if extra is None:
        await cur.execute("""SELECT payload FROM review_outbox WHERE kind='publication-intent'
          AND payload->>'contribution_id'=%s AND (payload->>'revision')::int=%s
          ORDER BY id DESC LIMIT 1""",(c['id'],c['revision']))
        prior=await cur.fetchone()
        if prior:extra=prior['payload'].get('extra')
    key='publication-intent:'+c['id']+':'+str(c['revision'])
    payload={'contribution_id':c['id'],'revision':c['revision'],'actor_id':actor_id,'extra':extra or {}}
    await cur.execute("""INSERT INTO review_outbox(event_key,kind,payload) VALUES(%s,'publication-intent',%s)
      ON CONFLICT(event_key) DO UPDATE SET finished_at=NULL,last_error=NULL,available_at=now(),payload=EXCLUDED.payload
      WHERE review_outbox.finished_at IS NOT NULL RETURNING id""",(key,Jsonb(payload)))
    if await cur.fetchone():
        await service.event(cur,c['id'],actor_id,'publication_waiting_for_slot',{'revision':c['revision']})
    if c['state']!='accepted':await service.update_state(cur,c,actor_id,'accepted',{'waiting_for_export':key})
    return {'id':None,'state':'accepted'}

async def queue(cur,c,actor_id,extra=None,*,group_export=False,from_intent=False):
    await require_role(cur,actor_id,c['subject_id'],('owner','publisher'))
    if c['canonical_id']:await service.protect_answer(cur,actor_id,c['canonical_id'])
    if c['state'] not in {'accepted','publication_failed'}:
        service.conflict('Only accepted work can be published')
    if c['state']=='publication_failed':
        await cur.execute('''SELECT b.id FROM bank_retag_batches b JOIN admin_bank_decisions d ON d.contribution_id=ANY(b.contribution_ids)
          WHERE d.contribution_id=%s''',(c['id'],))
        batch=await cur.fetchone()
        if batch:service.conflict('Retry this tag batch together: '+batch['id'])
    r=await service.revision(cur,c)
    if not await service.eligible_reviews(cur,c,r):
        service.conflict('The current review or admin decision is no longer eligible')
    await cur.execute('''SELECT 1 FROM admin_answer_decisions WHERE contribution_id=%s AND revision=%s
      UNION ALL SELECT 1 FROM admin_bank_decisions WHERE contribution_id=%s AND revision=%s''',
      (c['id'],c['revision'],c['id'],c['revision']))
    direct=bool(await cur.fetchone())
    p=Proposal.model_validate(r['payload'])
    await service.validate_evidence(cur,p,r['baseline'],allow_noop=direct)
    if p.kind=='source_request' and not p.patch.get('paperId'):
        service.conflict('Register the source before publishing this request')
    if c['canonical_id']:
        current=await service.snapshot(cur,c['canonical_id'],c['appearance_id'])
        if digest(current)!=r['baseline_hash']:
            service.conflict('The question changed. Reopen and compare the correction.')
    path=p.patch.get('classification') or r['baseline'].get('record',{}).get('classification') or {}
    paths=[path,*p.patch.get('relatedClassifications',[]),*r['baseline'].get('record',{}).get('relatedClassifications',[])]
    if set(p.patch)&{'classification','relatedClassifications'}:
        for sid in {v['subject_id'] for v in paths if v.get('subject_id')}:
            await require_role(cur,actor_id,sid,('owner','publisher'))
    await cur.execute('SELECT id,state,error,manifest FROM bank_publications WHERE contribution_id=%s AND revision=%s',(c['id'],c['revision']))
    existing=await cur.fetchone()
    # Take the export slot BEFORE reading the sync/source. A preceding worker
    # can finish between statements; reading its old checksum before its exported
    # row disappears would recreate the stale-snapshot race.
    if settings.publication_serial_queue and not group_export and (not existing or existing['state']=='failed'):
        if not await export_slot(cur,from_intent=from_intent):
            if existing:service.conflict('Another publication is in progress. Retry after it finishes.')
            return await defer(cur,c,actor_id,extra)
    if c['canonical_id']:
        current=await service.snapshot(cur,c['canonical_id'],c['appearance_id'])
        if digest(current)!=r['baseline_hash']:
            service.conflict('The question changed. Reopen and compare the correction.')
    await cur.execute('SELECT bank_checksum FROM sync_log WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1')
    sync=await cur.fetchone()
    if not sync:raise HTTPException(503,'A completed bank sync is required')
    if existing:
        if existing['state']=='failed' and existing['error'] in STALE_EXPORT_ERRORS and existing['manifest']['bank_sha256']!=sync['bank_checksum']:
            service.conflict('This export uses an older bank snapshot. Reopen the current question and save a fresh decision; retrying this immutable export cannot apply it.')
        if existing['state'] not in ('failed','exported'):
            service.conflict('This publication is already completed or reverted. Refresh its status.')
        await cur.execute("UPDATE bank_publications SET state='exported',error=NULL WHERE id=%s AND state='failed'",(existing['id'],))
        await service.update_state(cur,c,actor_id,'publishing')
        return {'id':existing['id'],'state':'publishing'}
    if extra is None:
        # A retry before first export must retain the saved administrative binding.
        # The generic publish endpoint intentionally supplies no new authority.
        await cur.execute("""SELECT payload FROM review_outbox WHERE kind='publication-intent'
          AND payload->>'contribution_id'=%s AND (payload->>'revision')::int=%s
          ORDER BY id DESC LIMIT 1""",(c['id'],c['revision']))
        intent=await cur.fetchone()
        if intent:extra=intent['payload'].get('extra')
    await cur.execute('SELECT id,sha256,source_file,kind,paper_id FROM review_documents WHERE id=ANY(%s)',([e.document_id for e in p.evidence if e.document_id],))
    docs=await cur.fetchall()
    await cur.execute('SELECT * FROM review_taxonomy WHERE id=ANY(%s)',(list({v for path in paths for v in path.values() if v}),))
    nodes=await cur.fetchall();pub=service.uid('pub')
    manifest={'schema':1,'id':pub,'contribution_id':c['id'],'revision':c['revision'],
      'author_id':c['author_id'],'subject_id':c['subject_id'],'bank_sha256':sync['bank_checksum'],
      'payload':r['payload'],'baseline':r['baseline'],'baseline_hash':r['baseline_hash'],
      'documents':docs,'taxonomy':nodes,**(extra or {})}
    await cur.execute('''INSERT INTO bank_publications(id,contribution_id,revision,manifest,manifest_hash,exported_by)
      VALUES(%s,%s,%s,%s,%s,%s)''',(pub,c['id'],c['revision'],Jsonb(manifest),digest(manifest),actor_id))
    await cur.execute("INSERT INTO review_outbox(event_key,kind,payload) VALUES(%s,'publication',%s)",(pub,Jsonb({'publication_id':pub})))
    await service.update_state(cur,c,actor_id,'publishing',{'publication':pub})
    return {'id':pub,'state':'publishing'}


async def promote_one(cur):
    """Trusted worker exports a previously authorised intent against the current sync.

    No manifest, baseline or approval is rebased. All queue checks run again.
    """
    if not settings.publication_serial_queue:return {'state':'disabled'}
    await cur.execute("""SELECT * FROM review_outbox WHERE kind='publication-intent'
      AND finished_at IS NULL AND available_at<=now() ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED""")
    intent=await cur.fetchone()
    if not intent:return {'state':'empty'}
    data=intent['payload']
    await cur.execute('SELECT * FROM bank_contributions WHERE id=%s FOR UPDATE',(data['contribution_id'],))
    c=await cur.fetchone()
    if not c or c['revision']!=data['revision'] or c['state']!='accepted':
        await cur.execute("UPDATE review_outbox SET finished_at=now(),last_error='Intent no longer matches an accepted revision' WHERE id=%s",(intent['id'],))
        return {'state':'cancelled'}
    try:
        result=await queue(cur,c,data['actor_id'],data['extra'],from_intent=True)
    except HTTPException as exc:
        message=str(exc.detail)[:1500]
        await service.update_state(cur,c,'operator:publication-queue','publication_failed',{'reason':message,'revision':c['revision']})
        await cur.execute('UPDATE review_outbox SET finished_at=now(),attempts=attempts+1,last_error=%s WHERE id=%s',(message,intent['id']))
        return {'state':'failed','contribution_id':c['id'],'error':message}
    if result['id']:
        await cur.execute('UPDATE review_outbox SET finished_at=now(),last_error=NULL WHERE id=%s',(intent['id'],))
    return result


async def receipt(cur,cid):
    await cur.execute("""SELECT p.id,p.state,p.error FROM bank_publications p
      JOIN bank_contributions c ON c.id=p.contribution_id AND c.revision=p.revision
      WHERE c.id=%s ORDER BY p.created_at DESC,p.id DESC LIMIT 1""",(cid,))
    pub=await cur.fetchone()
    if pub:return pub
    await cur.execute('SELECT state FROM bank_contributions WHERE id=%s',(cid,))
    c=await cur.fetchone()
    return {'id':None,'state':c['state'],'error':None}
