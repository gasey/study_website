"""Small assigned-source review workspace; ordinary correction workflow publishes."""
from typing import Annotated, Literal
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator
from ..db import cursor
from ..services.review_identity import Actor, identity, require_role
from ..services import bank_review as service
from ..services.editorial_access import source_version, source_versions,inspection_fingerprints,changed_aspects
from ..services.review_policy import digest
from ..services.question_readiness import answer_status_sql
from ..source_files import source_pdf_url
from .materials import private

router=APIRouter(prefix='/api/editorial',tags=['assigned editorial review'],dependencies=[Depends(private)])
Account=Annotated[Actor,Depends(identity)]

class Invite(BaseModel):
    model_config=ConfigDict(extra='forbid')
    email:str=Field(min_length=5,max_length=254,pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    collection_id:str|None=Field(default=None,min_length=1,max_length=100)
    paper_ids:list[str]=Field(default_factory=list,max_length=100)
    title:str|None=Field(default=None,min_length=3,max_length=200)

    @field_validator('title','email','reason',mode='before')
    @classmethod
    def trim_text(cls,value):return value.strip() if isinstance(value,str) else value

    @model_validator(mode='after')
    def scope(self):
        if bool(self.collection_id)==bool(self.paper_ids):raise ValueError('Choose one module or an explicit set of papers')
        if self.paper_ids and not self.title:raise ValueError('Name the paper assignment')
        if len(set(self.paper_ids))!=len(self.paper_ids) or any(not p or len(p)>600 for p in self.paper_ids):raise ValueError('Choose distinct registered papers')
        return self
    reason:str=Field(min_length=15,max_length=2000)

class Change(BaseModel):
    model_config=ConfigDict(extra='forbid')
    expected_version:int=Field(ge=1)
    reason:str=Field(min_length=15,max_length=2000)

class Check(BaseModel):
    model_config=ConfigDict(extra='forbid')
    appearance_id:str=Field(min_length=1,max_length=200)
    source_version:str=Field(pattern=r'^[0-9a-f]{64}$')
    outcome:Literal['checked','needs_correction','cannot_verify']
    source_checked:bool
    options_checked:bool
    answer_checked:bool
    explanation_checked:bool
    note:str=Field(min_length=10,max_length=4000)

    @field_validator('note',mode='before')
    @classmethod
    def trim_note(cls,value):return value.strip() if isinstance(value,str) else value

async def access(cur,actor,assignment_id):
    await cur.execute('''SELECT e.*,coalesce(e.title,c.title) AS title FROM editorial_assignments e LEFT JOIN collections c ON c.id=e.collection_id
      JOIN users u ON u.id=e.user_id WHERE e.id=%s AND e.user_id=%s
      AND e.email=lower(u.email) AND e.state='active' FOR SHARE OF e''',(assignment_id,actor.id))
    row=await cur.fetchone()
    if not row: raise HTTPException(404,'Active assignment not found')
    return row

@router.get('/assignments')
async def mine(actor:Account):
    async with cursor() as cur:
        await cur.execute('''SELECT e.id,e.collection_id,coalesce(e.title,c.title) AS title,e.state,e.version,
          (SELECT count(*) FROM editorial_assignment_papers p WHERE p.assignment_id=e.id) AS papers
          FROM editorial_assignments e LEFT JOIN collections c ON c.id=e.collection_id JOIN users u ON u.id=%s
          WHERE (e.user_id=u.id OR e.state='pending' AND e.email=lower(u.email)) AND e.state<>'revoked'
          ORDER BY coalesce(e.title,c.title),e.id''',(actor.id,))
        return {'items':await cur.fetchall()}

@router.get('/manage')
async def manage(actor:Account):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute('''SELECT e.*,coalesce(e.title,c.title) AS title,EXISTS(SELECT 1 FROM users u WHERE lower(u.email)=e.email) AS account_exists
          FROM editorial_assignments e LEFT JOIN collections c ON c.id=e.collection_id ORDER BY e.created_at,e.id''')
        return {'items':await cur.fetchall()}

@router.post('/assignments',status_code=201)
async def invite(body:Invite,actor:Account):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        email=body.email.strip().lower()
        scope_key='collection:'+body.collection_id if body.collection_id else 'papers:'+digest(sorted(body.paper_ids))
        await cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",('editorial:'+email+':'+scope_key,))
        await cur.execute("SELECT * FROM editorial_assignments WHERE email=%s AND scope_key=%s AND state<>'revoked'",(email,scope_key))
        existing=await cur.fetchone()
        if existing:return existing
        if body.collection_id:
            await cur.execute('''SELECT cp.paper_id FROM collection_papers cp JOIN collections c
              ON c.id=cp.collection_id AND c.live_version=cp.version WHERE c.id=%s AND cp.allow_browse ORDER BY cp.paper_id''',(body.collection_id,))
            papers=await cur.fetchall()
            if not papers:raise HTTPException(409,'This module has no registered source papers')
        else:
            await cur.execute('SELECT id AS paper_id FROM papers WHERE id=ANY(%s) ORDER BY id',(body.paper_ids,))
            papers=await cur.fetchall()
            if len(papers)!=len(body.paper_ids):raise HTTPException(404,'One or more registered papers were not found')
        aid='edit_'+uuid4().hex
        await cur.execute('''INSERT INTO editorial_assignments(id,email,collection_id,created_by,reason,scope_key,title)
          VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING *''',(aid,email,body.collection_id,actor.id,body.reason,scope_key,body.title if not body.collection_id else None))
        row=await cur.fetchone()
        await cur.executemany('INSERT INTO editorial_assignment_papers(assignment_id,paper_id) VALUES(%s,%s)',[(aid,p['paper_id']) for p in papers])
        await service.event(cur,None,actor.id,'editorial_invited',{'assignment':aid,'email':email,'collection':body.collection_id,'papers':len(papers),'reason':body.reason})
        return row

@router.post('/assignments/{aid}/activate')
async def activate(aid:str,body:Change,actor:Account):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute('SELECT * FROM editorial_assignments WHERE id=%s FOR UPDATE',(aid,));row=await cur.fetchone()
        if not row:raise HTTPException(404,'Assignment not found')
        if row['version']!=body.expected_version or row['state']!='pending':raise HTTPException(409,'Assignment changed; refresh')
        await cur.execute('SELECT id FROM users WHERE lower(email)=%s FOR SHARE',(row['email'],));users=await cur.fetchall()
        if len(users)!=1:raise HTTPException(409,'The friend must create their own account before owner activation')
        await cur.execute("UPDATE editorial_assignments SET user_id=%s,state='active',version=version+1,activated_at=now() WHERE id=%s RETURNING *",(users[0]['id'],aid))
        result=await cur.fetchone()
        await service.event(cur,None,actor.id,'editorial_activated',{'assignment':aid,'user':users[0]['id'],'reason':body.reason})
        return result

@router.post('/assignments/{aid}/revoke')
async def revoke(aid:str,body:Change,actor:Account):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute("UPDATE editorial_assignments SET state='revoked',version=version+1 WHERE id=%s AND version=%s AND state<>'revoked' RETURNING id",(aid,body.expected_version))
        if not await cur.fetchone():raise HTTPException(409,'Assignment changed; refresh')
        await service.event(cur,None,actor.id,'editorial_revoked',{'assignment':aid,'reason':body.reason})
        return {'revoked':True}

@router.get('/assignments/{aid}/papers')
async def papers(aid:str,actor:Account):
    from ..services import review_scope, editorial_status
    async with cursor() as cur:
        await access(cur,actor,aid)
        meta,rows=await review_scope.rows(cur,'assignment:'+aid,actor.id)
        await cur.execute('''SELECT p.id,p.exam_name,p.exam_type,p.year,p.paper_number,p.paper_subject,p.source_file,p.pdf_url
          FROM editorial_assignment_papers ep JOIN papers p ON p.id=ep.paper_id
          WHERE ep.assignment_id=%s ORDER BY p.year DESC NULLS LAST,p.exam_name,p.id''',(aid,))
        papers=await cur.fetchall()
        state=await editorial_status.statuses(cur,rows)
        return {'items':editorial_status.paper_summaries(papers,rows,state,assignment=aid)}

@router.get('/assignments/{aid}/questions')
async def questions(aid:str,actor:Account,paper:str=Query(min_length=1,max_length=600),offset:int=Query(0,ge=0,le=100000),limit:int=Query(25,ge=1,le=100)):
    from ..services import review_scope, editorial_status
    async with cursor() as cur:
        await access(cur,actor,aid)
        await cur.execute('SELECT 1 FROM editorial_assignment_papers WHERE assignment_id=%s AND paper_id=%s',(aid,paper))
        if not await cur.fetchone():raise HTTPException(404,'Paper is outside this assignment')
        _,rows=await review_scope.rows(cur,'assignment:'+aid,actor.id,paper=paper)
        page=rows[offset:offset+limit];state=await editorial_status.statuses(cur,page)
        await cur.execute(f"SELECT q.id,{answer_status_sql('q')} AS answer_status FROM canonical_questions q WHERE q.id=ANY(%s)",(list({r['canonical_id'] for r in page}),))
        answer_statuses={r['id']:r['answer_status'] for r in await cur.fetchall()}
        return {'items':[{**r,'appearance_id':r['id'],'answer_status':answer_statuses.get(r['canonical_id']),'previous_check':state[r['id']]['previous_check'],
                          'unresolved_checks':[{**c,'note':''} for c in state[r['id']]['unresolved_checks']]} for r in page], 'total':len(rows),'offset':offset}

@router.post('/assignments/{aid}/checks')
async def check(aid:str,body:Check,actor:Account):
    async with cursor() as cur:
        await access(cur,actor,aid)
        await cur.execute('''SELECT a.canonical_id,a.paper_id FROM appearances a JOIN editorial_assignment_papers p
          ON p.paper_id=a.paper_id WHERE p.assignment_id=%s AND a.id=%s''',(aid,body.appearance_id));row=await cur.fetchone()
        if not row:raise HTTPException(404,'Question is outside this assignment')
        await service.protect_answer(cur,actor.id,row['canonical_id'])
        version=await source_version(cur,row['canonical_id'],body.appearance_id,True)
        if version!=body.source_version:raise HTTPException(409,'The source changed. Reopen and recheck this question.')
        flags={k:getattr(body,k) for k in ('source_checked','options_checked','answer_checked','explanation_checked')}
        if body.outcome=='checked' and not all(flags.values()):raise HTTPException(422,'Confirm all four checks before marking this source checked')
        from psycopg.types.json import Jsonb
        await cur.execute('''INSERT INTO editorial_checks(assignment_id,appearance_id,canonical_id,reviewer_id,source_version,outcome,checklist,note)
          VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id,created_at''',(aid,body.appearance_id,row['canonical_id'],actor.id,version,body.outcome,Jsonb(flags),body.note))
        return {**await cur.fetchone(),'message':'Editorial check saved. Answer provenance and scoring are unchanged.'}


ATTESTATION='I compared the question and context, applicable options and figures, recorded answer/evidence, and explanation or written marking guidance with the source.'

class QuickCheck(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    appearance_id:str=Field(min_length=1,max_length=200)
    source_version:str=Field(pattern=r'^[0-9a-f]{64}$')
    inspection_version:str=Field(pattern=r'^[0-9a-f]{64}$')
    attestation:Literal['source-review-v1']
    outcome:Literal['checked','cannot_verify']
    reason:Literal['missing_source','missing_key','unclear_source','disputed_answer','other']|None=None
    note:str=Field(default='',max_length=4000)

    @model_validator(mode='after')
    def meaningful(self):
        if self.outcome=='cannot_verify' and (not self.reason or self.reason=='other' and len(self.note)<10):
            raise ValueError('Choose a reason; describe other issues in at least 10 characters')
        if self.outcome=='checked' and self.reason:raise ValueError('A checked question cannot have an unresolved reason')
        return self

@router.post('/assignments/{aid}/quick-checks')
async def quick_check(aid:str,body:QuickCheck,actor:Account):
    from psycopg.types.json import Jsonb
    async with cursor() as cur:
        await access(cur,actor,aid)
        await cur.execute('''SELECT a.canonical_id,a.paper_id,a.type FROM appearances a JOIN editorial_assignment_papers ep
          ON ep.paper_id=a.paper_id WHERE ep.assignment_id=%s AND a.id=%s''',(aid,body.appearance_id))
        row=await cur.fetchone()
        if not row:raise HTTPException(404,'Question is outside this assignment')
        await service.protect_answer(cur,actor.id,row['canonical_id'])
        token=await source_version(cur,row['canonical_id'],body.appearance_id,True)
        if body.source_version!=token:raise HTTPException(409,'The source changed. Reopen and recheck this question.')
        await cur.execute('SELECT id FROM review_documents WHERE paper_id=%s FOR SHARE',(row['paper_id'],))
        fingerprints=(await inspection_fingerprints(cur,[row['paper_id']],[body.appearance_id]))[body.appearance_id]
        if digest(fingerprints)!=body.inspection_version:raise HTTPException(409,'The source evidence changed. Reopen and compare it before saving.')
        checked=body.outcome=='checked'
        flags={'source_checked':checked,'options_checked':checked if row['type']=='mcq' else None,
          'answer_checked':checked if row['type']=='mcq' else None,'explanation_checked':checked}
        await cur.execute('''INSERT INTO editorial_checks(assignment_id,appearance_id,canonical_id,reviewer_id,
          source_version,outcome,checklist,note,fingerprints,attestation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
          RETURNING id,created_at''',(aid,body.appearance_id,row['canonical_id'],actor.id,token,body.outcome,
          Jsonb(flags),body.note or (body.reason or ''),Jsonb(fingerprints),ATTESTATION if checked else 'Unresolved: '+str(body.reason)))
        return {**await cur.fetchone(),'message':'Inspection saved'}

class AddPapers(Change):
    paper_ids:list[str]=Field(min_length=1,max_length=100)

    @model_validator(mode='after')
    def exact_ids(self):
        if len(set(self.paper_ids))!=len(self.paper_ids) or any(not p or len(p)>600 for p in self.paper_ids):raise ValueError('Choose distinct registered papers')
        return self


@router.get('/catalog')
async def catalog(actor:Account,kind:Literal['modules','papers']='modules',search:str=Query('',max_length=200),offset:int=Query(0,ge=0,le=100000)):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        pattern='%'+search.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%'
        if kind=='modules':
            await cur.execute('''SELECT c.id,c.title,count(cp.paper_id)::int AS papers
              FROM collections c JOIN collection_papers cp ON cp.collection_id=c.id AND cp.version=c.live_version AND cp.allow_browse
              WHERE (c.title ILIKE %s OR c.id ILIKE %s) GROUP BY c.id ORDER BY c.title,c.id LIMIT 13 OFFSET %s''',(pattern,pattern,offset))
        else:
            await cur.execute('''SELECT p.id,p.exam_name AS title,p.paper_subject,p.year,
              CASE WHEN p.exam_type='Community' THEN 'website' ELSE 'mpsc' END AS bank
              FROM papers p WHERE (p.id ILIKE %s OR p.exam_name ILIKE %s OR coalesce(p.paper_subject,'') ILIKE %s OR p.year::text ILIKE %s)
              ORDER BY p.year DESC NULLS LAST,p.exam_name,p.id LIMIT 13 OFFSET %s''',(pattern,pattern,pattern,pattern,offset))
        rows=await cur.fetchall()
        return {'items':rows[:12],'has_more':len(rows)>12}


@router.get('/assignments/{aid}/available-papers')
async def available_papers(aid:str,actor:Account):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute("SELECT collection_id,version FROM editorial_assignments WHERE id=%s AND state<>'revoked'",(aid,))
        assignment=await cur.fetchone()
        if not assignment:raise HTTPException(404,'Assignment not found')
        if not assignment['collection_id']:
            await cur.execute('SELECT paper_id FROM editorial_assignment_papers WHERE assignment_id=%s ORDER BY paper_id',(aid,))
            return {'items':[],'version':assignment['version'],'assigned_ids':[p['paper_id'] for p in await cur.fetchall()]}
        await cur.execute('''SELECT p.id,p.exam_name AS title,p.year FROM collection_papers cp
          JOIN collections c ON c.id=cp.collection_id AND cp.version=c.live_version JOIN papers p ON p.id=cp.paper_id
          WHERE c.id=%s AND cp.allow_browse AND NOT EXISTS (SELECT 1 FROM editorial_assignment_papers ep WHERE ep.assignment_id=%s AND ep.paper_id=p.id)
          ORDER BY p.year DESC NULLS LAST,p.id''',(assignment['collection_id'],aid))
        return {'items':await cur.fetchall(),'version':assignment['version']}


@router.post('/assignments/{aid}/add-papers')
async def add_papers(aid:str,body:AddPapers,actor:Account):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute('SELECT * FROM editorial_assignments WHERE id=%s FOR UPDATE',(aid,))
        assignment=await cur.fetchone()
        if not assignment:raise HTTPException(404,'Assignment not found')
        if assignment['state']=='revoked' or assignment['version']!=body.expected_version:raise HTTPException(409,'Assignment changed; refresh')
        ids=sorted(set(body.paper_ids))
        if assignment['collection_id']:
            await cur.execute('''SELECT cp.paper_id AS id FROM collection_papers cp JOIN collections c
              ON c.id=cp.collection_id AND cp.version=c.live_version
              WHERE c.id=%s AND cp.allow_browse AND cp.paper_id=ANY(%s)''',(assignment['collection_id'],ids))
        else:await cur.execute('SELECT id FROM papers WHERE id=ANY(%s)',(ids,))
        if len(await cur.fetchall())!=len(ids):raise HTTPException(422,'Choose registered papers from this assignment’s module')
        await cur.execute('SELECT paper_id FROM editorial_assignment_papers WHERE assignment_id=%s AND paper_id=ANY(%s)',(aid,ids))
        existing={p['paper_id'] for p in await cur.fetchall()};ids=[p for p in ids if p not in existing]
        if not ids:raise HTTPException(409,'These papers are already assigned')
        await cur.executemany('INSERT INTO editorial_assignment_papers(assignment_id,paper_id) VALUES(%s,%s) ON CONFLICT DO NOTHING',[(aid,p) for p in ids])
        await cur.execute('UPDATE editorial_assignments SET version=version+1 WHERE id=%s RETURNING version',(aid,))
        result=await cur.fetchone()
        await service.event(cur,None,actor.id,'editorial_scope_expanded',{'assignment':aid,'papers':ids,'reason':body.reason})
        return result


@router.get('/assignments/{aid}/context')
async def context(aid:str,actor:Account,appearance:str=Query(min_length=1,max_length=200)):
    async with cursor() as cur:
        await access(cur,actor,aid)
        await cur.execute('''SELECT a.canonical_id,a.paper_id,p.exam_type FROM appearances a JOIN papers p ON p.id=a.paper_id
          JOIN editorial_assignment_papers ep ON ep.paper_id=a.paper_id WHERE ep.assignment_id=%s AND a.id=%s''',(aid,appearance))
        source=await cur.fetchone()
        if not source:raise HTTPException(404,'Question is outside this assignment')
        await service.protect_answer(cur,actor.id,source['canonical_id'])
        await cur.execute('''SELECT DISTINCT u.handle FROM editorial_assignments e
          JOIN users u ON u.id=e.user_id AND lower(u.email)=e.email JOIN editorial_assignment_papers ep ON ep.assignment_id=e.id
          WHERE ep.paper_id=%s AND e.state='active' ORDER BY u.handle''',(source['paper_id'],))
        reviewers=await cur.fetchall()
        await cur.execute('''SELECT DISTINCT c.id,c.title FROM collections c JOIN collection_papers cp ON cp.collection_id=c.id AND cp.version=c.live_version AND cp.allow_browse
          JOIN appearances a ON a.paper_id=cp.paper_id WHERE a.canonical_id=%s ORDER BY c.title,c.id''',(source['canonical_id'],))
        modules=await cur.fetchall()
        await cur.execute('SELECT count(DISTINCT paper_id)::int AS count FROM appearances WHERE canonical_id=%s',(source['canonical_id'],))
        shared=(await cur.fetchone())['count']
        # Private draft details/IDs are returned only to their author. Other
        # submitted work is represented by counts so exact-source access does not
        # accidentally become access to another person's private contribution.
        await cur.execute('''SELECT state,count(*)::int AS count FROM bank_contributions
          WHERE canonical_id=%s AND state IN ('submitted','in_review','accepted','publishing','publication_failed','published') GROUP BY state''',(source['canonical_id'],))
        corrections=await cur.fetchall()
        await cur.execute('''SELECT id,state,kind,updated_at FROM bank_contributions WHERE canonical_id=%s AND author_id=%s ORDER BY updated_at DESC,id LIMIT 10''',(source['canonical_id'],actor.id))
        mine=await cur.fetchall()
        return {'bank':'website' if source['exam_type']=='Community' else 'mpsc','reviewers':reviewers,'modules':modules,'shared_papers':shared,'corrections':corrections,'mine':mine}

# Additive shared-module routes retain all existing assignment URLs.
from .editorial_shared import router as shared_router
router.include_router(shared_router)
