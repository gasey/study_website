"""Dated editorial context. Never modifies canonical answers or scoring."""
from datetime import date
from typing import Annotated, Literal
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator
from psycopg.types.json import Jsonb
from ..db import cursor
from ..services.review_identity import Actor, identity, require_role, grants
from ..services.editorial_access import assigned, source_version
from ..services import bank_review
from ..services.answer_reveals import record_reveal
from ..services.review_policy import digest
from ..source_files import source_pdf_url
from .materials import private

router=APIRouter(prefix='/api/current-affairs',tags=['dated current affairs'],dependencies=[Depends(private)])
Account=Annotated[Actor,Depends(identity)]

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)


FactKind=Literal['general','officeholder','trade-ranking','production-ranking','statistic','report-ranking','scheme','award','record','event']
MEASURED_KINDS={'trade-ranking','production-ranking','statistic','report-ranking'}

class Comparison(Strict):
    kind:FactKind='general'
    subject:str|None=Field(default=None,min_length=3,max_length=200)
    metric:str|None=Field(default=None,min_length=3,max_length=200)
    basis:Literal['value','volume','rate','count','index-score','qualitative','other']|None=None
    unit:str|None=Field(default=None,min_length=1,max_length=100)
    population:str|None=Field(default=None,min_length=3,max_length=200)
    source_series:str|None=Field(default=None,min_length=3,max_length=250)
    methodology:str|None=Field(default=None,min_length=10,max_length=1000)
    @model_validator(mode='after')
    def complete_measure(self):
        if self.kind in MEASURED_KINDS and not all((self.subject,self.metric,self.basis,self.unit,self.population,self.source_series,self.methodology)):
            raise ValueError('Rankings/statistics need an exact subject, metric, value/volume basis, unit, comparison population, source series and methodology')
        return self

class Fact(Strict):
    value:str=Field(min_length=3,max_length=1000)
    period_label:str|None=Field(default=None,min_length=3,max_length=150)
    period_kind:Literal['unknown','calendar-year','financial-year','report-edition','event-edition','as-of-date']='unknown'
    period_start:date|None=None
    period_end:date|None=None
    edition:str|None=Field(default=None,min_length=2,max_length=150)
    effective_on:date|None=None
    effective_until:date|None=None  # Exclusive; never infer unknown dates.
    source_url:HttpUrl
    source_title:str=Field(min_length=5,max_length=300)
    source_date:date|None=None
    checked_on:date
    review_due:date
    @field_validator('source_url')
    @classmethod
    def https(cls,v):
        if v.scheme!='https':raise ValueError('Use an HTTPS primary source URL')
        return v
    @model_validator(mode='after')
    def dates(self):
        if self.period_start and self.period_end and self.period_end<self.period_start:raise ValueError('Reporting period end precedes its start')
        if self.period_kind!='unknown' and not self.period_label:raise ValueError('Give the reporting year, period or edition label')
        if self.checked_on>date.today():raise ValueError('Checked date cannot be in the future')
        if self.review_due<self.checked_on:raise ValueError('Review due must follow the checked date')
        if self.source_date and self.source_date>self.checked_on:raise ValueError('Source publication cannot follow its check')
        if self.effective_until and (not self.effective_on or self.effective_until<=self.effective_on):raise ValueError('Effective until must follow a known start date')
        return self

class SourceLink(Strict):
    canonical_id:str=Field(min_length=1,max_length=200)
    appearance_id:str=Field(min_length=1,max_length=600)
    source_version:str=Field(pattern=r'^[0-9a-f]{64}$')
    reference_date:date|None=None
    date_basis:str=Field(min_length=15,max_length=1000)
    context:str=Field(min_length=15,max_length=2000)
    period_label:str|None=Field(default=None,min_length=3,max_length=150)
    comparison_status:Literal['comparable','related-only','unclear']='unclear'
    comparison_note:str|None=Field(default=None,min_length=15,max_length=1500)
    relation:Literal['same-changing-fact','same-concept','later-question','revised-statistic']='same-changing-fact'

class Proposal(Strict):
    request_key:str=Field(pattern=r'^[a-zA-Z0-9_-]{16,100}$')
    entity_id:str|None=Field(default=None,max_length=100)
    base_version:int=Field(default=0,ge=0)
    name:str=Field(min_length=5,max_length=200)
    jurisdiction:str=Field(min_length=2,max_length=150)
    predicate:str=Field(min_length=3,max_length=100)
    comparison:Comparison=Field(default_factory=Comparison)
    facts:list[Fact]=Field(min_length=1,max_length=12)
    links:list[SourceLink]=Field(min_length=1,max_length=20)
    reason:str=Field(min_length=20,max_length=2000)
    @model_validator(mode='after')
    def consistent(self):
        if len({l.appearance_id for l in self.links})!=len(self.links):raise ValueError('Link each source appearance only once')
        if self.comparison.kind in MEASURED_KINDS:
            if any(not f.period_label for f in self.facts):raise ValueError('Every ranking/statistic needs an explicit reporting period, or a label explaining that it is unknown')
            if any(not l.comparison_note or (l.comparison_status=='comparable' and not l.period_label) for l in self.links):raise ValueError('Explain each question’s measure comparability and give its reporting period when comparable')
        period_keys=[(f.period_kind,f.period_label,f.edition) for f in self.facts if f.period_label]
        if len(period_keys)!=len(set(period_keys)):raise ValueError('Resolve competing claims for the same reporting period/edition before publication')
        known=sorted((f for f in self.facts if f.effective_on and self.comparison.kind in {'general','officeholder','scheme'}),key=lambda f:f.effective_on)
        for a,b in zip(known,known[1:]):
            if not a.effective_until or a.effective_until>b.effective_on:raise ValueError('Dated fact periods overlap; close the earlier interval or resolve the conflict')
        return self

class Decision(Strict):
    expected_version:int=Field(ge=0)
    action:Literal['publish','reject','retract']
    reason:str=Field(min_length=20,max_length=2000)

class View(Strict):
    canonical_id:str=Field(min_length=1,max_length=200)
    paper_id:str|None=Field(default=None,max_length=600)

async def no_assessment(cur,user):
    # Withhold the entire feature during any active assessment, including a cup
    # entry whose room finished but whose answer-release window is still closed.
    await cur.execute('''SELECT 1 FROM mock_sessions WHERE user_id=%s AND submitted_at IS NULL LIMIT 1''',(user,))
    if await cur.fetchone():raise HTTPException(409,'Finish your active mock before opening dated updates or related questions')
    await cur.execute('''SELECT 1 FROM game_members m JOIN game_rooms r ON r.id=m.room_id
      LEFT JOIN game_cups c ON c.id=r.cup_id WHERE m.user_id=%s
      AND ((m.released_at IS NULL AND r.state IN ('waiting','running')) OR c.closes_at>now()) LIMIT 1''',(user,))
    if await cur.fetchone():raise HTTPException(409,'Dated updates unlock after your game and any weekly cup answer-release window')

async def source_fingerprint(cur,link):
    # Long-lived semantic evidence hash; xmin remains the short-lived edit token.
    snapshot=await bank_review.snapshot(cur,link.canonical_id,link.appearance_id)
    await cur.execute('''SELECT type,question,options,answer_text,answer_source,answer_key_ref,
      explanation,status,source_defect,key_disputed,dispute_note,merged_into
      FROM canonical_questions WHERE id=%s''',(link.canonical_id,))
    return digest({'source':snapshot,'canonical':await cur.fetchone()})

async def link_access(cur,user,link):
    await cur.execute('''SELECT a.paper_id,qc.subject_id FROM appearances a
      LEFT JOIN question_classifications qc ON qc.question_id=a.canonical_id AND qc.review_status='approved'
      WHERE a.id=%s AND a.canonical_id=%s''',(link.appearance_id,link.canonical_id))
    row=await cur.fetchone()
    if not row:raise HTTPException(422,'Question and source appearance do not match')
    if not await assigned(cur,user,row['paper_id']):await require_role(cur,user,row['subject_id'])
    if link.source_version!=await source_version(cur,link.canonical_id,link.appearance_id,True):raise HTTPException(409,'A linked source changed. Reopen it and review this proposal again.')

async def validate_links(cur,user,p):
    # Stable lock ordering for multi-source proposals.
    for link in sorted(p.links,key=lambda l:(l.canonical_id,l.appearance_id)):await link_access(cur,user,link)

@router.get('/manage')
async def manage(actor:Account,before:int|None=Query(None,ge=1)):
    async with cursor() as cur:
        await no_assessment(cur,actor.id)
        owner='owner' in await grants(cur,actor.id)
        await cur.execute('''SELECT r.*,e.name,e.jurisdiction,e.predicate,e.version AS entity_version,e.live_revision
          FROM current_affairs_revisions r JOIN current_affairs_entities e ON e.id=r.entity_id
          WHERE (%s OR r.author_id=%s) AND (%s::bigint IS NULL OR r.id<%s)
          ORDER BY r.id DESC LIMIT 21''',(owner,actor.id,before,before))
        rows=await cur.fetchall()
        return {'items':rows[:20],'next_cursor':rows[19]['id'] if len(rows)>20 else None,'can_publish':owner,'user_id':actor.id}

@router.post('/proposals',status_code=201)
async def propose(body:Proposal,actor:Account):
    payload=body.model_dump(mode='json')
    async with cursor() as cur:
        await no_assessment(cur,actor.id)
        await cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',('current-affairs:'+actor.id+':'+body.request_key,))
        await cur.execute('SELECT id,payload FROM current_affairs_revisions WHERE author_id=%s AND request_key=%s',(actor.id,body.request_key))
        replay=await cur.fetchone()
        if replay:
            if Proposal(**replay['payload']).model_dump(mode='json')!=payload:raise HTTPException(409,'Request already used for different content')
            return {'id':replay['id'],'replayed':True}
        if body.entity_id:
            await cur.execute('SELECT * FROM current_affairs_entities WHERE id=%s FOR UPDATE',(body.entity_id,))
            entity=await cur.fetchone()
            if not entity:raise HTTPException(404,'Entity not found')
            if (entity['name'],entity['jurisdiction'],entity['predicate'])!=(body.name,body.jurisdiction,body.predicate):raise HTTPException(422,'Use the existing exact entity identity')
        else:
            if body.base_version:raise HTTPException(422,'New entity starts at version zero')
            await cur.execute('''INSERT INTO current_affairs_entities(id,name,jurisdiction,predicate,created_by)
              VALUES(%s,%s,%s,%s,%s) ON CONFLICT(name,jurisdiction,predicate) DO NOTHING''',('ca_'+uuid4().hex,body.name,body.jurisdiction,body.predicate,actor.id))
            await cur.execute('SELECT * FROM current_affairs_entities WHERE name=%s AND jurisdiction=%s AND predicate=%s FOR UPDATE',(body.name,body.jurisdiction,body.predicate))
            entity=await cur.fetchone()
        await cur.execute('SELECT payload FROM current_affairs_revisions WHERE entity_id=%s ORDER BY id LIMIT 1',(entity['id'],))
        original=await cur.fetchone()
        if original and Proposal(**original['payload']).comparison!=body.comparison:
            raise HTTPException(422,'Comparison identity differs: use a separately named connection for another commodity, unit, metric, population or methodology')
        if entity['version']!=body.base_version:raise HTTPException(409,'Entity changed. Load its latest published revision before proposing a replacement.')
        await validate_links(cur,actor.id,body)
        await cur.execute('''INSERT INTO current_affairs_revisions(entity_id,author_id,request_key,base_version,payload)
          VALUES(%s,%s,%s,%s,%s) RETURNING id''',(entity['id'],actor.id,body.request_key,body.base_version,Jsonb(payload)))
        row=await cur.fetchone()
        fingerprints=[(row['id'],l.appearance_id,l.canonical_id,await source_fingerprint(cur,l)) for l in body.links]
        await cur.executemany('INSERT INTO current_affairs_links(revision_id,appearance_id,canonical_id,source_fingerprint) VALUES(%s,%s,%s,%s)',fingerprints)
        await bank_review.event(cur,None,actor.id,'current_affairs_proposed',{'revision':row['id'],'entity':entity['id'],'reason':body.reason})
        return row

@router.post('/revisions/{rid}/decision')
async def decide(rid:int,body:Decision,actor:Account):
    async with cursor() as cur:
        await no_assessment(cur,actor.id)
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute('SELECT entity_id FROM current_affairs_revisions WHERE id=%s',(rid,));found=await cur.fetchone()
        if not found:raise HTTPException(404,'Revision not found')
        await cur.execute('SELECT * FROM current_affairs_entities WHERE id=%s FOR UPDATE',(found['entity_id'],));entity=await cur.fetchone()
        await cur.execute('SELECT * FROM current_affairs_revisions WHERE id=%s FOR UPDATE',(rid,));row=await cur.fetchone()
        if entity['version']!=body.expected_version:raise HTTPException(409,'Entity changed. Refresh before deciding.')
        if body.action=='retract':
            if row['state']!='published' or entity['live_revision']!=rid:raise HTTPException(409,'Only the live revision can be retracted')
            state='retracted'
            await cur.execute('UPDATE current_affairs_entities SET live_revision=NULL,version=version+1 WHERE id=%s',(entity['id'],))
        else:
            if row['state']!='pending':raise HTTPException(409,'This proposal has already been decided')
            state='published' if body.action=='publish' else 'rejected'
            if body.action=='publish':
                if row['author_id']==actor.id:raise HTTPException(403,'An independent owner must publish; you cannot approve your own dated claims')
                if row['base_version']!=entity['version']:raise HTTPException(409,'This proposal is based on an older entity revision')
                p=Proposal(**row['payload'])
                await validate_links(cur,actor.id,p)
                # Author must retain exact permissions at publication as well.
                await validate_links(cur,row['author_id'],p)
                await cur.execute('SELECT appearance_id,source_fingerprint FROM current_affairs_links WHERE revision_id=%s',(rid,))
                stored={r['appearance_id']:r['source_fingerprint'] for r in await cur.fetchall()}
                for link in p.links:
                    if stored.get(link.appearance_id)!=await source_fingerprint(cur,link):
                        raise HTTPException(409,'Source evidence fingerprint is missing or changed. Prepare a new inspected proposal.')
                if entity['live_revision']:
                    await cur.execute("UPDATE current_affairs_revisions SET state='superseded' WHERE id=%s",(entity['live_revision'],))
                await cur.execute('UPDATE current_affairs_entities SET live_revision=%s,version=version+1 WHERE id=%s',(rid,entity['id']))
        await cur.execute('''UPDATE current_affairs_revisions SET state=%s,reviewer_id=%s,decision_reason=%s,decided_at=now() WHERE id=%s''',(state,actor.id,body.reason,rid))
        await bank_review.event(cur,None,actor.id,'current_affairs_'+state,{'revision':rid,'entity':entity['id'],'reason':body.reason})
        return {'state':state}

@router.post('/view')
async def view(body:View,actor:Account):
    async with cursor() as cur:
        await no_assessment(cur,actor.id)
        await cur.execute('''SELECT 1 WHERE EXISTS(SELECT 1 FROM answer_reveals WHERE user_id=%s AND canonical_id=%s)
          OR EXISTS(SELECT 1 FROM attempts WHERE user_id=%s AND canonical_id=%s)''',(actor.id,body.canonical_id,actor.id,body.canonical_id))
        if not await cur.fetchone():raise HTTPException(403,'Check or show this question’s answer before viewing related dated context')
        await cur.execute('''SELECT e.*,r.payload FROM current_affairs_entities e
          JOIN current_affairs_revisions r ON r.id=e.live_revision AND r.state='published'
          WHERE EXISTS(SELECT 1 FROM current_affairs_links l JOIN appearances a ON a.id=l.appearance_id
            WHERE l.revision_id=r.id AND l.canonical_id=%s AND (%s::text IS NULL OR a.paper_id=%s))
          ORDER BY e.id LIMIT 10 FOR SHARE OF e,r''',(body.canonical_id,body.paper_id,body.paper_id))
        entities=await cur.fetchall();items=[];exposed=set()
        for e in entities:
            p=Proposal(**e['payload'])
            # No stale source annotation is shown as if checked against new content.
            await cur.execute('SELECT appearance_id,source_fingerprint FROM current_affairs_links WHERE revision_id=%s',(e['live_revision'],))
            fingerprints={r['appearance_id']:r['source_fingerprint'] for r in await cur.fetchall()}
            stale=False
            for link in sorted(p.links,key=lambda l:(l.canonical_id,l.appearance_id)):
                await source_version(cur,link.canonical_id,link.appearance_id,True)
                if fingerprints.get(link.appearance_id)!=await source_fingerprint(cur,link):stale=True;break
            if stale:continue
            await cur.execute('''SELECT a.id AS appearance_id,a.canonical_id,a.paper_id,a.qnum,p.exam_name,p.year,p.source_file,p.pdf_url,a.page
              FROM appearances a JOIN papers p ON p.id=a.paper_id WHERE a.id=ANY(%s) ORDER BY p.year DESC NULLS LAST,a.id''',([l.appearance_id for l in p.links],))
            related=await cur.fetchall();contexts={l.appearance_id:l.model_dump(mode='json') for l in p.links}
            for r in related:
                r['source_pdf_url']=source_pdf_url(r.pop('source_file'),r.pop('pdf_url'))
                c=contexts[r['appearance_id']]
                r.update(reference_date=c['reference_date'],date_basis=c['date_basis'],context=c['context'],relation=c['relation'],period_label=c['period_label'],comparison_status=c['comparison_status'],comparison_note=c['comparison_note'])
                exposed.add(r['canonical_id'])
            facts=[{**f.model_dump(mode='json'),'recheck_due':f.review_due<date.today()} for f in p.facts]
            facts.sort(key=lambda f:(f['period_end'] or f['period_start'] or f['effective_on'] or '',f['source_date'] or ''),reverse=True)
            items.append({'id':e['id'],'name':e['name'],'jurisdiction':e['jurisdiction'],'predicate':e['predicate'],'version':e['version'],'comparison':p.comparison.model_dump(mode='json'),'facts':facts,'questions':related})
        for qid in sorted(exposed):await record_reveal(cur,actor.id,qid)
        return {'items':items,'message':'Dated context leaves historical answers and scoring unchanged. Linked questions enter the normal 30-minute review window.'}

@router.get('/sources')
async def find_sources(actor:Account,q:str=Query(min_length=4,max_length=150)):
    async with cursor() as cur:
        await no_assessment(cur,actor.id)
        text=q.strip()
        if len(text)<4:raise HTTPException(422,'Enter at least four search characters')
        pattern='%'+text.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%'
        await cur.execute('''SELECT a.id AS appearance_id,a.canonical_id,a.question,a.qnum,p.exam_name,p.year,p.id AS paper_id
          FROM appearances a JOIN papers p ON p.id=a.paper_id
          JOIN canonical_questions c ON c.id=a.canonical_id AND c.status IN ('live','held')
          LEFT JOIN question_classifications qc ON qc.question_id=c.id AND qc.review_status='approved'
          WHERE a.question ILIKE %s AND (
            EXISTS(SELECT 1 FROM review_grants g WHERE g.user_id=%s AND g.revoked_at IS NULL
              AND g.role IN ('owner','reviewer','senior') AND (g.subject_id IS NULL OR g.subject_id=qc.subject_id))
            OR EXISTS(SELECT 1 FROM editorial_assignments e JOIN users u ON u.id=e.user_id
              JOIN editorial_assignment_papers ep ON ep.assignment_id=e.id
              WHERE e.user_id=%s AND e.state='active' AND e.email=lower(u.email) AND ep.paper_id=a.paper_id))
          ORDER BY p.year DESC NULLS LAST,a.id LIMIT 20''',(pattern,actor.id,actor.id))
        return {'items':await cur.fetchall()}
