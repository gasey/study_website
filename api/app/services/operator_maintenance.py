"""Trusted SSH maintenance, explicitly delegated by the owner; no HTTP endpoint.

Records operator identity rather than inventing sessions or peer approvals.
Ordinary community proposals and review requirements remain unchanged.
"""
from contextvars import ContextVar
from fastapi import HTTPException
from psycopg.types.json import Jsonb
from . import bank_review as review
from .review_identity import require_role
from .review_policy import Proposal,digest

OPERATOR='operator:owner-source-maintenance'
_source_batch=ContextVar('owner_source_batch',default=None)

SOURCE_KINDS={'transcription','source_reference','new_question','defect'}

async def intake_source(cur,owner,proposal,authorization):
    await require_role(cur,owner,roles=('owner',))
    if len(authorization.strip())<20:
        raise HTTPException(422,'Explicit owner authorization is required')
    p=Proposal.model_validate(proposal)
    if p.kind not in SOURCE_KINDS:
        raise HTTPException(422,'Owner source intake accepts only source maintenance kinds')
    c=await review.create(cur,owner,p,'operator-source:'+digest(p.model_dump(mode='json')),admin_attestation=True)
    await review.event(cur,c['id'],OPERATOR,'operator_source_intake',{'owner_id':owner,'authorization':authorization,'payload_hash':digest(p.model_dump(mode='json')),'no_peer_approvals':True})
    return {'id':c['id'],'state':c['state'],'payload_hash':digest(p.model_dump(mode='json'))}

async def queue_source(cur,owner,cid,payload_hash,paper_id,source_sha,reason,authorization,allow_rebase=False):
    await require_role(cur,owner,roles=('owner',))
    if len(reason.strip())<20 or len(authorization.strip())<20:
        raise HTTPException(422,'Explicit owner authorization and source review reason are required')
    c=await review.load(cur,cid,owner,review=True)
    if c['author_id']!=owner or c['kind']not in SOURCE_KINDS:
        raise HTTPException(422,'Only the owner’s specified source maintenance proposals can use this command')
    r=await review.revision(cur,c)
    if digest(r['payload'])!=payload_hash:raise HTTPException(409,'The reviewed proposal payload changed')
    p=Proposal.model_validate(r['payload'])
    target=(r['baseline'].get('paper')or{}).get('id')or p.patch.get('paperId')
    if target!=paper_id:raise HTTPException(409,'The source paper does not match the authorized paper')
    evidence=[e for e in p.evidence if e.kind=='paper'and e.sha256==source_sha and e.document_id]
    if not evidence:raise HTTPException(422,'Exact registered paper evidence is required')
    for e in evidence:
        await cur.execute("SELECT 1 FROM review_documents WHERE id=%s AND paper_id=%s AND sha256=%s AND kind='paper'",(e.document_id,paper_id,source_sha))
        if not await cur.fetchone():raise HTTPException(409,'The registered source changed')
    await cur.execute('SELECT id,state FROM bank_publications WHERE contribution_id=%s AND revision=%s',(cid,c['revision']))
    prior=await cur.fetchone()
    if prior:
        await cur.execute("SELECT 1 FROM contribution_events WHERE contribution_id=%s AND actor_id=%s AND action='operator_source_adjudication' AND detail->>'payload_hash'=%s AND detail->>'owner_id'=%s",(cid,OPERATOR,payload_hash,owner))
        if not await cur.fetchone():raise HTTPException(409,'An unrelated publication already exists')
        # Replay cannot silently re-export a failed/stale publication.
        return {'id':prior['id'],'state':prior['state'],'contribution_id':cid,'replayed':True}
    if c['state']not in ('draft','submitted','in_review','changes_requested','accepted'):
        raise HTTPException(409,'This proposal is not available for maintenance publication')
    await cur.execute('SELECT 1 FROM contribution_decisions WHERE contribution_id=%s AND revision=%s AND decision<>\'approve\'',(cid,c['revision']))
    if await cur.fetchone():raise HTTPException(409,'Resolve the existing reviewer objection first')
    current=await review.snapshot(cur,c['canonical_id'],c['appearance_id'])if c['canonical_id']else{}
    if digest(current)!=r['baseline_hash']:
        if not allow_rebase:raise HTTPException(409,'Source changed; inspect and explicitly rebase the proposal')
        # Only disjoint source changes can be rebased without a new payload.
        for key in p.patch:
            section='metadata'if key in ('sourceDefect','disputeNote')else'record'
            if current.get(section,{}).get(key)!=r['baseline'].get(section,{}).get(key):
                raise HTTPException(409,'A field being repaired changed; prepare a fresh proposal')
        await review.validate_evidence(cur,p,current)
        await cur.execute('INSERT INTO contribution_revisions(contribution_id,revision,payload,baseline,baseline_hash,actor_id) VALUES(%s,%s,%s,%s,%s,%s)',(cid,c['revision']+1,Jsonb(r['payload']),Jsonb(current),digest(current),OPERATOR))
        await cur.execute('UPDATE bank_contributions SET revision=revision+1 WHERE id=%s RETURNING *',(cid,));c=await cur.fetchone()
        r=await review.revision(cur,c)
        await review.event(cur,cid,OPERATOR,'operator_source_rebase',{'owner_id':owner,'reason':reason,'baseline_hash':r['baseline_hash']})
    await review.validate_evidence(cur,p,current)
    await cur.execute("SELECT id FROM bank_publications WHERE state='exported'")
    waiting=await cur.fetchall();batch=_source_batch.get()
    if any(row['id']not in(batch or set())for row in waiting):raise HTTPException(409,'Finish the outstanding bank publication first')
    await cur.execute('SELECT bank_checksum FROM sync_log WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1');sync=await cur.fetchone()
    if not sync:raise HTTPException(409,'A completed bank sync is required')
    await cur.execute('SELECT id,sha256,source_file,kind,paper_id FROM review_documents WHERE id=ANY(%s)',([e.document_id for e in p.evidence if e.document_id],));docs=await cur.fetchall()
    path=p.patch.get('classification')or current.get('record',{}).get('classification')or{}
    await cur.execute('SELECT * FROM review_taxonomy WHERE id=ANY(%s)',([v for v in path.values()if v],));nodes=await cur.fetchall()
    detail={'owner_id':owner,'authorization':authorization,'reason':reason,'revision':c['revision'],'payload_hash':payload_hash,'baseline_hash':r['baseline_hash'],'source_sha256':source_sha,'paper_id':paper_id}
    await review.event(cur,cid,OPERATOR,'operator_source_adjudication',detail)
    c=await review.update_state(cur,c,OPERATOR,'accepted',{'operator_maintenance':detail})
    pub=review.uid('pub')
    manifest={'schema':1,'id':pub,'contribution_id':cid,'revision':c['revision'],'author_id':owner,'subject_id':c['subject_id'],'bank_sha256':sync['bank_checksum'],'payload':r['payload'],'baseline':r['baseline'],'baseline_hash':r['baseline_hash'],'documents':docs,'taxonomy':nodes,'operator_maintenance':detail}
    await cur.execute('INSERT INTO bank_publications(id,contribution_id,revision,manifest,manifest_hash,exported_by) VALUES(%s,%s,%s,%s,%s,%s)',(pub,cid,c['revision'],Jsonb(manifest),digest(manifest),OPERATOR))
    await cur.execute("INSERT INTO review_outbox(event_key,kind,payload) VALUES(%s,'publication',%s)",(pub,Jsonb({'publication_id':pub})))
    await review.update_state(cur,c,OPERATOR,'publishing',{'publication':pub,'operator_maintenance':True})
    if _source_batch.get()is not None:_source_batch.get().add(pub)
    return {'id':pub,'state':'exported','contribution_id':cid,'replayed':False}


async def queue_source_batch(cur,owner,items,authorization):
    """Trusted SSH-only bounded intake, atomically exporting disjoint source repairs.

    The context contains only publication IDs made inside this transaction; it
    cannot whitelist unrelated waiting publications or leak into HTTP requests.
    Every item still passes the ordinary source/evidence/owner/objection guards.
    """
    await require_role(cur,owner,roles=('owner',))
    if not 1<=len(items)<=100:raise HTTPException(422,'Choose 1–100 explicit source repairs')
    targets=[x['proposal'].get('appearance_id')for x in items]
    if None in targets or len(set(targets))!=len(targets):raise HTTPException(422,'Choose distinct existing appearances')
    await cur.execute("SELECT 1 FROM bank_publications WHERE state='exported'LIMIT 1")
    if await cur.fetchone():raise HTTPException(409,'Finish the outstanding bank publication first')
    token=_source_batch.set(set())
    try:
        results=[]
        for item in items:
            if item['proposal'].get('kind')not in('transcription','source_reference','defect'):raise HTTPException(422,'This batch accepts source repairs only')
            if item['proposal'].get('kind')=='defect':
                current=await review.snapshot(cur,item['proposal']['canonical_id'],item['proposal']['appearance_id'])
                patch=item['proposal']['patch'];opts=current['record'].get('options',[])
                old_flag=current.get('metadata',{}).get('sourceDefect')
                reviewed_unresolved=(old_flag=='unresolved-source'
                    and current['record'].get('answerIndex') is None
                    and item.get('expected_source')==current['record']
                    and (not current['record'].get('hasDiagram') or current['record'].get('figureImage')))
                if (set(patch)!={'sourceDefect','disputeNote'} or patch['sourceDefect']is not None
                        or not(old_flag=='duplicate-options' or reviewed_unresolved)
                        or len((patch['disputeNote']or'').strip())<20
                        or not 2<=len(opts)<=8 or any(not isinstance(o,str)or not o.strip()for o in opts)
                        or len({o.strip()for o in opts})!=len(opts)):
                    raise HTTPException(422,'Defect clearance needs distinct source choices and an obsolete duplicate flag or an exact reviewed unanswered source baseline')
            expected=item.get('expected_source')
            if expected is not None:
                current=await review.snapshot(cur,item['proposal']['canonical_id'],item['proposal']['appearance_id'])
                if any(current['record'].get(k)!=v for k,v in expected.items()):
                    raise HTTPException(409,'Reviewed source changed; inspect the current source before restoring it')
            intake=await intake_source(cur,owner,item['proposal'],authorization)
            result=await queue_source(cur,owner,intake['id'],intake['payload_hash'],item['paper_id'],item['source_sha'],item['reason'],authorization)
            results.append(result)
        return {'publications':results}
    finally:_source_batch.reset(token)
