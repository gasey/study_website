"""One source-aware review surface for assignments and published exam modules."""
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import Field
from psycopg.types.json import Jsonb
from ..db import cursor
from ..services import review_scope, editorial_status, bank_review
from ..services.review_identity import Actor, identity, require_role
from ..services.editorial_access import source_version,inspection_fingerprints
from ..services.review_policy import digest
from .editorial import QuickCheck, ATTESTATION

router=APIRouter()
Account=Annotated[Actor,Depends(identity)]

@router.get('/scopes')
async def scopes(actor:Account,search:str=Query('',max_length=200),offset:int=Query(0,ge=0,le=100000)):
    async with cursor() as cur:return await review_scope.catalog(cur,actor.id,search,offset)

@router.get('/scope')
async def overview(actor:Account,scope:str=Query(min_length=1,max_length=220)):
    async with cursor() as cur:
        meta,rows=await review_scope.rows(cur,scope,actor.id)
        state=await editorial_status.statuses(cur,rows)
        await cur.execute('''SELECT id,exam_name,exam_type,year,paper_number,paper_subject,source_file,pdf_url FROM papers
          WHERE id=ANY(%s) ORDER BY year DESC NULLS LAST,exam_name,id''',(sorted({r['paper_id'] for r in rows}),))
        papers=editorial_status.paper_summaries(await cur.fetchall(),rows,state,assignment=meta['assignment_id'],scope=scope)
        canonical={r['canonical_id'] for r in rows}
        # Corrections/reports belong to canonical questions, even across papers.
        unique={r['canonical_id']:state[r['id']] for r in rows}
        work={'inspections':sum(not s['checked'] for s in state.values()),
              'issue_appearances':sum(s['flagged'] for s in state.values()),
              'reports':sum(s['reports'] for s in unique.values()),
              'pending':sum(s['corrections']['pending'] for s in unique.values()),
              'failed':sum(s['corrections']['failed'] for s in unique.values())}
        return {'scope':meta,'items':papers,'work':work,'summary':{'appearances':len(rows),'questions':len(canonical),
          'held':sum(s['held'] for s in state.values()),'checked':sum(s['checked'] for s in state.values()),'reused':sum(p['reused'] for p in papers),
          'flagged':sum(s['flagged'] for s in state.values()),'recheck':sum(s['stale'] for s in state.values()),
          'complete':bool(rows and all(s['complete'] for s in state.values()))},
          'selection':{'description':'Published module sources and selections, intersected with your current access. Adding sources does not expand reviewer assignments.',
                       'definition_revision':meta['definition_revision'],'area':meta['area']}}

@router.get('/scope/questions')
async def questions(actor:Account,scope:str=Query(min_length=1,max_length=220),paper:str=Query(min_length=1,max_length=600),
                    offset:int=Query(0,ge=0,le=100000),queue:Literal['all','remaining','attention']='all',search:str=Query('',max_length=200),after:str=Query('',max_length=200),limit:int=Query(25,ge=1,le=100)):
    async with cursor() as cur:
        meta,rows=await review_scope.rows(cur,scope,actor.id,paper=paper)
        state=await editorial_status.statuses(cur,rows)
        tokens=search.lower().split()
        filtered=[r for r in rows if all(t in (r['question']+' '+(r['qnum'] or '')).lower() for t in tokens)
          and (queue=='all' or queue=='remaining' and not state[r['id']]['complete'] or queue=='attention' and (state[r['id']]['flagged'] or state[r['id']]['stale'] or state[r['id']]['corrections']['failed']))]
        target=None
        if after:
            # Seek in stable source order after refresh; saved rows may disappear
            # from the queue and page boundaries may shift. Wrap once, skip self.
            positions={r['id']:i for i,r in enumerate(rows)}
            anchor=positions.get(after,-1)
            candidates=[r for r in filtered if r['id']!=after]
            target=next((r for r in candidates if positions[r['id']]>anchor),candidates[0] if candidates else None)
            if target:offset=next(i for i,r in enumerate(filtered) if r['id']==target['id'])//limit*limit
        offset=min(offset,max(0,(len(filtered)-1)//limit*limit))
        return {'scope':meta,'total':len(filtered),'offset':offset,'next':{'appearance':target['id'],'question':target['canonical_id']} if target else None,'items':[
          {**r,'appearance_id':r['id'],**state[r['id']], 'unresolved_checks':[{**c,'note':''} for c in state[r['id']]['unresolved_checks']]} for r in filtered[offset:offset+limit]]}

@router.get('/scope/context')
async def context(actor:Account,scope:str=Query(min_length=1,max_length=220),appearance:str=Query(min_length=1,max_length=200)):
    async with cursor() as cur:
        meta,rows=await review_scope.rows(cur,scope,actor.id,appearance=appearance)
        if not rows:raise HTTPException(404,'Source is outside your accessible module scope')
        row=rows[0];await bank_review.protect_answer(cur,actor.id,row['canonical_id'])
        state=(await editorial_status.statuses(cur,rows))[appearance]
        await cur.execute("SELECT id,title FROM collections WHERE visibility='public' ORDER BY title,id")
        modules=[]
        for c in await cur.fetchall():
            _,condition,params=await review_scope.definition(cur,'module:'+c['id'],actor.id)
            params['context_id']=row['canonical_id']
            await cur.execute(f'''SELECT 1 FROM appearances a JOIN canonical_questions q ON q.id=a.canonical_id
              LEFT JOIN question_classifications qc ON qc.question_id=q.id AND qc.review_status='approved' AND qc.is_primary
              WHERE a.canonical_id=%(context_id)s AND ({condition}) AND {review_scope.permission_sql()} LIMIT 1''',params)
            if await cur.fetchone():modules.append(c)
        await cur.execute('''SELECT id,state,kind,updated_at FROM bank_contributions WHERE canonical_id=%s AND author_id=%s
          ORDER BY updated_at DESC,id LIMIT 10''',(row['canonical_id'],actor.id))
        mine=await cur.fetchall()
        await cur.execute('SELECT exam_type FROM papers WHERE id=%s',(row['paper_id'],));bank=await cur.fetchone()
        await cur.execute('''SELECT count(DISTINCT a.paper_id)::int AS count FROM appearances a LEFT JOIN question_classifications qc
          ON qc.question_id=a.canonical_id AND qc.review_status='approved' AND qc.is_primary
          WHERE a.canonical_id=%(context_id)s AND '''+review_scope.permission_sql(),{'context_id':row['canonical_id'],'review_user':actor.id})
        count=(await cur.fetchone())['count']
        return {'bank':'website' if bank['exam_type']=='Community' else 'mpsc','reviewers':[], 'modules':modules,
                'shared_papers':count,'corrections':[{'state':k,'count':v} for k,v in state['corrections'].items() if v],
                'mine':mine,'inspection':state,'scope':meta}

class SharedCheck(QuickCheck):
    scope:str=Field(min_length=1,max_length=220)
    scope_revision:str=Field(pattern=r'^[0-9a-f]{64}$')
    request_key:str=Field(min_length=8,max_length=80)
    resolve_checks:list[int]=Field(default_factory=list,max_length=20)
    resolution_reason:str=Field(default='',max_length=2000)

@router.post('/checks')
async def check(body:SharedCheck,actor:Account):
    async with cursor() as cur:
        # Resolve full scope so filtered paging cannot supply a different revision.
        meta,rows=await review_scope.rows(cur,body.scope,actor.id)
        row=next((r for r in rows if r['id']==body.appearance_id),None)
        if not row:raise HTTPException(404,'Source is outside your accessible module scope')
        await bank_review.protect_answer(cur,actor.id,row['canonical_id'])
        await cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",('inspection-request:'+actor.id+':'+body.request_key,))
        await cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",('shared-inspection:'+body.appearance_id,))
        await cur.execute('''SELECT e.id FROM editorial_assignments e JOIN users u ON u.id=e.user_id
          JOIN editorial_assignment_papers ep ON ep.assignment_id=e.id WHERE e.user_id=%s AND e.state='active'
          AND e.email=lower(u.email) AND ep.paper_id=%s ORDER BY e.id LIMIT 1 FOR SHARE OF e''',(actor.id,row['paper_id']))
        assignment=await cur.fetchone()
        if not assignment:await require_role(cur,actor.id,row['subject_id'],roles=('owner','publisher'))
        payload_hash=digest(body.model_dump())
        await cur.execute('SELECT id,created_at,request_hash FROM editorial_checks WHERE reviewer_id=%s AND request_key=%s',(actor.id,body.request_key))
        prior=await cur.fetchone()
        if prior:
            if prior['request_hash']!=payload_hash:raise HTTPException(409,'This save key was already used for a different inspection')
            return {'id':prior['id'],'created_at':prior['created_at'],'replayed':True}
        if body.scope_revision!=meta['revision']:raise HTTPException(409,'Module membership changed. Refresh the scope before saving; your draft is retained.')
        token=await source_version(cur,row['canonical_id'],body.appearance_id,True)
        if token!=body.source_version:raise HTTPException(409,'The source changed. Reopen and compare before saving.')
        await cur.execute('SELECT id FROM review_documents WHERE paper_id=%s FOR SHARE',(row['paper_id'],))
        fingerprints=(await inspection_fingerprints(cur,[row['paper_id']],[body.appearance_id]))[body.appearance_id]
        if digest(fingerprints)!=body.inspection_version:raise HTTPException(409,'Source evidence changed. Reopen and compare before saving.')
        if body.resolve_checks:
            await require_role(cur,actor.id,row['subject_id'],roles=('owner','publisher'))
            if body.outcome!='checked' or len(body.resolution_reason.strip())<15 or len(set(body.resolve_checks))!=len(body.resolve_checks):
                raise HTTPException(422,'Explain the exact issues resolved in at least 15 characters, while recording a current inspection')
            await cur.execute("SELECT id FROM editorial_checks WHERE appearance_id=%s AND id=ANY(%s) AND outcome<>'checked'",(body.appearance_id,body.resolve_checks))
            if len(await cur.fetchall())!=len(body.resolve_checks):raise HTTPException(422,'Resolve only unresolved inspection issues for this exact source')
        checked=body.outcome=='checked'
        flags={'source_checked':checked,'options_checked':checked if row['type']=='mcq' else None,
               'answer_checked':checked if row['type']=='mcq' else None,'explanation_checked':checked}
        await cur.execute('''INSERT INTO editorial_checks(assignment_id,origin_scope,scope_revision,appearance_id,canonical_id,
          reviewer_id,source_version,outcome,checklist,note,fingerprints,attestation,request_key,request_hash)
          VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id,created_at''',
          (meta['assignment_id'] or (assignment['id'] if assignment else None),body.scope,meta['revision'],body.appearance_id,row['canonical_id'],
           actor.id,token,body.outcome,Jsonb(flags),body.note or body.reason or '',Jsonb(fingerprints),
           ATTESTATION if checked else 'Unresolved: '+str(body.reason),body.request_key,payload_hash))
        result=await cur.fetchone()
        for cid in body.resolve_checks:
            await cur.execute('''INSERT INTO editorial_check_resolutions(check_id,resolution_check_id,actor_id,fingerprint,reason)
              VALUES(%s,%s,%s,%s,%s)''',(cid,result['id'],actor.id,digest(fingerprints),body.resolution_reason.strip()))
        return {**result,'message':'Inspection saved; other modules using this source reuse the attributed evidence'}

from .module_composition import router as module_setup_router
router.include_router(module_setup_router)
