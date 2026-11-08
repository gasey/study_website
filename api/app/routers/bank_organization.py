"""Staff organisation tools and answer-free original-paper readiness."""
from pathlib import Path
import json
from typing import Annotated,Literal
from uuid import uuid4
from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import Field
from psycopg.types.json import Jsonb
from ..db import cursor
from ..services import bank_organization as service
from ..services.review_identity import Actor,identity
from ..services import bank_review
from ..services.editorial_access import source_version
from .exam_inventory import no_store,event,json_record,context_fingerprint,protect_paper

router=APIRouter(prefix='/api/admin/bank/organization',tags=['bank organisation'],dependencies=[Depends(no_store)])
public_router=APIRouter(prefix='/api/collections',tags=['paper readiness'])
Account=Annotated[Actor,Depends(identity)]


class Reason(service.Strict):
    reason:str=Field(min_length=20,max_length=4000)


class Provider(Reason):
    id:str=Field(pattern=r'^[a-z0-9][a-z0-9-]{1,99}$')
    label:str=Field(min_length=2,max_length=200)
    kind:Literal['exam-board','book','website','mock','other']='exam-board'
    url:str=Field(default='',max_length=2000)


@router.get('/providers')
async def providers(actor:Account):
    async with cursor() as cur:
        await service.access(cur,actor)
        await cur.execute('SELECT id,label,kind,url FROM bank_source_providers WHERE active ORDER BY label')
        return await cur.fetchall()


@router.post('/providers')
async def create_provider(body:Provider,actor:Account):
    service.web_url(body.url)
    async with cursor() as cur:
        await service.access(cur,actor,True)
        await cur.execute('SELECT * FROM bank_source_providers WHERE id=%s',(body.id,))
        if await cur.fetchone():raise HTTPException(409,'This source ID is already registered')
        await cur.execute('SELECT id FROM bank_source_providers WHERE lower(label)=lower(%s) AND active',(body.label,))
        if await cur.fetchone():raise HTTPException(409,'This source label is already registered; reuse its provider')
        await cur.execute('INSERT INTO bank_source_providers(id,label,kind,url,created_by) VALUES(%s,%s,%s,%s,%s)',(body.id,body.label,body.kind,body.url or None,actor.id))
        await event(cur,actor,'provider_registered',body.id,None,body.model_dump(),body.reason)
    return {'id':body.id}


@router.get('/schemes')
async def schemes(actor:Account):
    async with cursor() as cur:
        await service.access(cur,actor)
        await cur.execute('SELECT scheme_id,revision,payload,created_at FROM bank_scheme_revisions ORDER BY scheme_id,revision DESC LIMIT 2000')
        rows=await cur.fetchall()
    path=Path(__file__).resolve().parents[1]/'data/exam-scheme-templates.json'
    return {'items':rows,'templates':json.loads(path.read_text()) if path.exists() else []}


class SchemeSave(Reason):
    scheme_id:str=Field(pattern=r'^[a-z0-9][a-z0-9-]{1,99}$')
    expected_revision:int=Field(ge=0)
    scheme:service.Scheme


@router.post('/schemes')
async def save_scheme(body:SchemeSave,actor:Account):
    async with cursor() as cur:
        await service.access(cur,actor,True)
        await cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',('scheme:'+body.scheme_id,))
        await cur.execute('SELECT revision,payload FROM bank_scheme_revisions WHERE scheme_id=%s ORDER BY revision DESC LIMIT 1',(body.scheme_id,));old=await cur.fetchone()
        revision=old['revision'] if old else 0;payload=body.scheme.model_dump(mode='json')
        if revision!=body.expected_revision:raise HTTPException(409,'This scheme changed. Reload the latest revision.')
        if old and old['payload']==payload:raise HTTPException(422,'The scheme is unchanged')
        for paper in body.scheme.papers:
            for section in paper.sections:
                if section.paths:
                    await cur.execute('SELECT id FROM review_taxonomy WHERE id=ANY(%s) AND active',(section.paths,))
                    if {r['id'] for r in await cur.fetchall()}!=set(section.paths):raise HTTPException(422,'A blueprint path is not in the approved taxonomy')
        await cur.execute('INSERT INTO bank_scheme_revisions(scheme_id,revision,payload,actor_id,reason) VALUES(%s,%s,%s,%s,%s)',(body.scheme_id,revision+1,Jsonb(payload),actor.id,body.reason))
        await event(cur,actor,'scheme_revision_saved',body.scheme_id,old,payload,body.reason)
        return {'scheme_id':body.scheme_id,'revision':revision+1}


@router.get('/paper')
async def get_paper(actor:Account,paper_id:str=Query(min_length=1,max_length=600)):
    async with cursor() as cur:
        await service.access(cur,actor);await protect_paper(cur,actor,paper_id)
        await cur.execute('SELECT p.id,p.exam_name,p.paper_subject,p.year,p.exam_type,p.source_file,p.pdf_url,'+service.provider_expression()+' AS provider_id FROM papers p LEFT JOIN bank_paper_profiles bp ON bp.paper_id=p.id WHERE p.id=%s',(paper_id,));paper=await cur.fetchone()
        if not paper:raise HTTPException(404,'Paper not found')
        await cur.execute('SELECT * FROM bank_paper_profiles WHERE paper_id=%s',(paper_id,));saved=await cur.fetchone()
        rows=await service.paper_rows(cur,paper_id)
        return {'paper':paper,'saved':saved,'context':await service.paper_context(cur,paper_id),
          'appearances':[{k:r[k] for k in ('id','canonical_id','type','qnum','page')} for r in rows],
          'readiness':await service.readiness(cur,paper_id)}


class ProfileSave(Reason):
    paper_id:str=Field(min_length=1,max_length=600)
    expected_version:int=Field(ge=0)
    expected_context:str=Field(pattern=r'^[a-f0-9]{64}$')
    profile:service.PaperProfile


@router.post('/paper')
async def save_paper(body:ProfileSave,actor:Account):
    async with cursor() as cur:
        await service.access(cur,actor,True);await protect_paper(cur,actor,body.paper_id)
        await cur.execute('SELECT id,source_file,pdf_url FROM papers WHERE id=%s FOR UPDATE',(body.paper_id,));paper=await cur.fetchone()
        if not paper:raise HTTPException(404,'Paper not found')
        current=await service.paper_context(cur,body.paper_id)
        if current!=body.expected_context:raise HTTPException(409,'The printed source changed. Inspect its current layout.')
        await cur.execute('SELECT * FROM bank_paper_profiles WHERE paper_id=%s FOR UPDATE',(body.paper_id,));old=await cur.fetchone()
        if body.expected_version!=(old['version'] if old else 0):raise HTTPException(409,'Another editor changed this paper configuration')
        profile=body.profile;payload=profile.model_dump(mode='json')
        await cur.execute('SELECT id FROM bank_source_providers WHERE id=%s AND active',(profile.provider_id,))
        if not await cur.fetchone():raise HTTPException(422,'Choose a registered source provider')
        spec=None
        if profile.scheme_id:
            await cur.execute('SELECT payload FROM bank_scheme_revisions WHERE scheme_id=%s AND revision=%s',(profile.scheme_id,profile.scheme_revision));scheme=await cur.fetchone()
            if not scheme:raise HTTPException(422,'Scheme revision not found')
            spec=next((p for p in scheme['payload']['papers'] if p['key']==profile.scheme_paper_key),None)
            if not spec:raise HTTPException(422,'Choose a paper in that exact scheme revision')
        rows=await service.paper_rows(cur,body.paper_id);ids={r['id'] for r in rows}
        if profile.appearance_order and set(profile.appearance_order)!=ids:raise HTTPException(422,'Printed order must contain every current appearance exactly once')
        if any(a not in ids for values in profile.section_appearances.values() for a in values):raise HTTPException(422,'A section contains a question from another paper')
        if profile.section_appearances and (not spec or not set(profile.section_appearances)<={s['key'] for s in spec['sections']}):raise HTTPException(422,'Choose section keys from the linked scheme paper')
        if profile.source_checked and not service.source_pdf_url(paper['source_file'],paper['pdf_url']):raise HTTPException(422,'A linked original PDF is needed to confirm the layout')
        await cur.execute('''INSERT INTO bank_paper_profiles(paper_id,provider_id,corpus,period,scheme_id,scheme_revision,scheme_paper_key,payload,context_fingerprint,actor_id)
          VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(paper_id) DO UPDATE SET provider_id=excluded.provider_id,
          corpus=excluded.corpus,period=excluded.period,scheme_id=excluded.scheme_id,scheme_revision=excluded.scheme_revision,
          scheme_paper_key=excluded.scheme_paper_key,payload=excluded.payload,context_fingerprint=excluded.context_fingerprint,
          actor_id=excluded.actor_id,version=bank_paper_profiles.version+1,updated_at=now() RETURNING version''',
          (body.paper_id,profile.provider_id,profile.corpus,profile.period,profile.scheme_id,profile.scheme_revision,profile.scheme_paper_key,Jsonb(payload),current,actor.id))
        version=(await cur.fetchone())['version'];await event(cur,actor,'paper_profile_saved',body.paper_id,json_record(old),payload,body.reason)
        return {'version':version,'readiness':await service.readiness(cur,body.paper_id)}


@router.get('/questions/{qid}/context')
async def get_context(qid:str,actor:Account,appearance_id:str=Query(min_length=1,max_length=600)):
    async with cursor() as cur:
        await service.question_access(cur,actor,qid);await bank_review.protect_answer(cur,actor.id,qid)
        token=await source_version(cur,qid,appearance_id)
        await cur.execute('SELECT * FROM bank_question_contexts WHERE question_id=%s',(qid,));saved=await cur.fetchone()
        await cur.execute('SELECT * FROM bank_tag_resolutions WHERE question_id=%s',(qid,));resolution=await cur.fetchone()
        return {'saved':saved,'source_version':token,'current':bool(saved and saved['appearance_id']==appearance_id and saved['source_version']==token),'resolution':resolution}


class ContextSave(Reason):
    appearance_id:str=Field(min_length=1,max_length=600)
    source_version:str=Field(pattern=r'^[a-f0-9]{64}$')
    expected_version:int=Field(ge=0)
    context:service.LearningContext


@router.post('/questions/{qid}/context')
async def save_context(qid:str,body:ContextSave,actor:Account):
    async with cursor() as cur:
        await service.question_access(cur,actor,qid,True);await bank_review.protect_answer(cur,actor.id,qid)
        await cur.execute('SELECT id FROM canonical_questions WHERE id=%s FOR UPDATE',(qid,))
        if not await cur.fetchone():raise HTTPException(404,'Question not found')
        token=await source_version(cur,qid,body.appearance_id)
        if token!=body.source_version:raise HTTPException(409,'The source changed. Reload before saving context')
        await cur.execute('SELECT * FROM bank_question_contexts WHERE question_id=%s FOR UPDATE',(qid,));old=await cur.fetchone()
        if body.expected_version!=(old['version'] if old else 0):raise HTTPException(409,'Another editor changed this context')
        payload=body.context.model_dump(mode='json')
        signature=await service.source_signature(cur,qid,body.appearance_id)
        await cur.execute('''INSERT INTO bank_question_contexts(question_id,appearance_id,source_version,source_signature,payload,actor_id) VALUES(%s,%s,%s,%s,%s,%s)
          ON CONFLICT(question_id) DO UPDATE SET appearance_id=excluded.appearance_id,source_version=excluded.source_version,source_signature=excluded.source_signature,payload=excluded.payload,
          actor_id=excluded.actor_id,version=bank_question_contexts.version+1,updated_at=now() RETURNING version''',(qid,body.appearance_id,token,signature,Jsonb(payload),actor.id))
        version=(await cur.fetchone())['version']
        await cur.execute("SELECT subject_id,topic_id,subtopic_id FROM question_classifications WHERE question_id=%s AND review_status='approved'",(qid,));path=await cur.fetchone()
        if body.context.broad_subject_intentional:
            if not path or path['topic_id']:raise HTTPException(422,'Broad-subject resolution is only for an approved subject without a topic')
            await cur.execute('''INSERT INTO bank_tag_resolutions(question_id,classification,appearance_id,source_signature,reason,actor_id) VALUES(%s,%s,%s,%s,%s,%s)
              ON CONFLICT(question_id) DO UPDATE SET classification=excluded.classification,appearance_id=excluded.appearance_id,source_signature=excluded.source_signature,reason=excluded.reason,actor_id=excluded.actor_id,updated_at=now()''',(qid,Jsonb(path),body.appearance_id,signature,body.reason,actor.id))
        else:await cur.execute("UPDATE bank_tag_resolutions SET classification='{}'::jsonb,reason=%s,actor_id=%s,updated_at=now() WHERE question_id=%s",(body.reason,actor.id,qid))
        await event(cur,actor,'learning_context_saved',qid,json_record(old),payload,body.reason)
        return {'version':version}


class SavedView(service.Strict):
    id:str|None=Field(default=None,max_length=100)
    expected_version:int=Field(ge=0)
    title:str=Field(min_length=2,max_length=100)
    filters:dict[str,str]=Field(max_length=30)


@router.get('/views')
async def views(actor:Account):
    async with cursor() as cur:
        await cur.execute('SELECT 1 FROM review_grants WHERE user_id=%s AND revoked_at IS NULL',(actor.id,))
        if not await cur.fetchone():raise HTTPException(403,'Staff permission required')
        await cur.execute('SELECT id,title,filters,version,updated_at FROM bank_cleanup_views WHERE user_id=%s ORDER BY updated_at DESC',(actor.id,));return await cur.fetchall()


@router.post('/views')
async def save_view(body:SavedView,actor:Account):
    filters=service.safe_filters(body.filters)
    async with cursor() as cur:
        await cur.execute('SELECT 1 FROM review_grants WHERE user_id=%s AND revoked_at IS NULL',(actor.id,))
        if not await cur.fetchone():raise HTTPException(403,'Staff permission required')
        await cur.execute('SELECT id FROM users WHERE id=%s FOR UPDATE',(actor.id,))
        await cur.execute('SELECT * FROM bank_cleanup_views WHERE user_id=%s AND id=%s',(actor.id,body.id));old=await cur.fetchone()
        if body.id and not old:raise HTTPException(404,'Your saved view was not found')
        if body.expected_version!=(old['version'] if old else 0):raise HTTPException(409,'The saved view changed in another tab')
        await cur.execute('SELECT id FROM bank_cleanup_views WHERE user_id=%s AND title=%s AND id<>%s',(actor.id,body.title,body.id or ''))
        if await cur.fetchone():raise HTTPException(409,'Choose another saved-view name or update the existing view')
        if not old:
            await cur.execute('SELECT count(*) AS n FROM bank_cleanup_views WHERE user_id=%s',(actor.id,))
            if (await cur.fetchone())['n']>=30:raise HTTPException(422,'Update one of your 30 saved work views')
        vid=body.id or 'view_'+uuid4().hex
        await cur.execute('''INSERT INTO bank_cleanup_views(id,user_id,title,filters) VALUES(%s,%s,%s,%s)
          ON CONFLICT(id) DO UPDATE SET title=excluded.title,filters=excluded.filters,version=bank_cleanup_views.version+1,updated_at=now() RETURNING id,version''',(vid,actor.id,body.title,Jsonb(filters)))
        return await cur.fetchone()


@router.get('/questions/{qid}/repeats')
async def repeats(qid:str,actor:Account):
    async with cursor() as cur:
        await service.question_access(cur,actor,qid);await bank_review.protect_answer(cur,actor.id,qid)
        await cur.execute('SELECT stem_norm FROM canonical_questions WHERE id=%s',(qid,));source=await cur.fetchone()
        if not source:raise HTTPException(404,'Question not found')
        # A candidate is never an approved merge. Exact stems are bounded and indexed.
        await cur.execute('''SELECT c.id,c.question,qc.subject_label,qc.topic_label,a.id AS appearance_id,a.paper_id,a.qnum,p.exam_name,p.year
          FROM canonical_questions c LEFT JOIN question_classifications qc ON qc.question_id=c.id AND qc.review_status='approved'
          JOIN LATERAL(SELECT id,paper_id,qnum FROM appearances WHERE canonical_id=c.id ORDER BY is_primary DESC,id LIMIT 1) a ON true
          JOIN papers p ON p.id=a.paper_id WHERE c.id<>%s AND c.status<>'merged' AND c.stem_norm=%s AND length(c.stem_norm)>=30
          AND EXISTS(SELECT 1 FROM review_grants g WHERE g.user_id=%s AND g.revoked_at IS NULL AND(g.subject_id IS NULL OR g.subject_id=qc.subject_id))
          ORDER BY p.year DESC NULLS LAST,c.id LIMIT 20''',(qid,source['stem_norm'],actor.id));candidates=await cur.fetchall()
        await cur.execute('SELECT DISTINCT ON(left_id,right_id) * FROM bank_repeat_relations WHERE left_id=%s OR right_id=%s ORDER BY left_id,right_id,revision DESC',(qid,qid));links=await cur.fetchall()
        # Remove relationships outside the current actor's grants; do not return other source tokens.
        visible=[]
        for link in links:
            other=link['right_id'] if link['left_id']==qid else link['left_id']
            try:await service.question_access(cur,actor,other)
            except HTTPException:continue
            link['current']=(link['left_version']==await source_version(cur,link['left_id'],link['left_appearance']) and link['right_version']==await source_version(cur,link['right_id'],link['right_appearance']))
            visible.append(link)
        return {'candidates':candidates,'relations':visible,'note':'Same wording is a candidate only. Inspect options, dates, passages and sources before linking.'}


class Relation(Reason):
    left_id:str=Field(min_length=1,max_length=100)
    right_id:str=Field(min_length=1,max_length=100)
    left_appearance:str=Field(min_length=1,max_length=600)
    right_appearance:str=Field(min_length=1,max_length=600)
    left_version:str=Field(pattern=r'^[a-f0-9]{64}$')
    right_version:str=Field(pattern=r'^[a-f0-9]{64}$')
    expected_revision:int=Field(ge=0)
    relation:Literal['same-question','same-concept','extraction-duplicate','keep-separate']


@router.post('/repeats')
async def save_relation(body:Relation,actor:Account):
    if body.left_id>=body.right_id:raise HTTPException(422,'Choose two distinct identities in ascending ID order')
    async with cursor() as cur:
        for qid,aid,token in [(body.left_id,body.left_appearance,body.left_version),(body.right_id,body.right_appearance,body.right_version)]:
            await service.question_access(cur,actor,qid,True);await bank_review.protect_answer(cur,actor.id,qid)
            await cur.execute('SELECT id FROM canonical_questions WHERE id=%s FOR UPDATE',(qid,))
            if token!=await source_version(cur,qid,aid):raise HTTPException(409,'A compared source changed. Inspect both again')
        await cur.execute('SELECT * FROM bank_repeat_relations WHERE left_id=%s AND right_id=%s ORDER BY revision DESC LIMIT 1',(body.left_id,body.right_id));old=await cur.fetchone()
        version=old['revision'] if old else 0
        if version!=body.expected_revision:raise HTTPException(409,'The relationship changed. Reload before deciding')
        await cur.execute('''INSERT INTO bank_repeat_relations(left_id,right_id,revision,relation,left_appearance,right_appearance,left_version,right_version,actor_id,reason)
          VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',(body.left_id,body.right_id,version+1,body.relation,body.left_appearance,body.right_appearance,body.left_version,body.right_version,actor.id,body.reason))
        await event(cur,actor,'repeat_relationship_reviewed',body.left_id,json_record(old),body.model_dump(),body.reason)
        return {'revision':version+1,'content_changed':False}


@public_router.get('/{collection_id}/paper-readiness')
async def paper_readiness(collection_id:str,paper_id:str=Query(min_length=1,max_length=600)):
    async with cursor() as cur:
        await cur.execute('''SELECT 1 FROM collection_papers cp JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version
          WHERE cp.collection_id=%s AND cp.paper_id=%s AND cp.allow_browse AND c.visibility='public' ''',(collection_id,paper_id))
        if not await cur.fetchone():raise HTTPException(404,'Paper not available in this collection')
        result=await service.readiness(cur,paper_id)
        if result['scheme'] and result['scheme']['state']!='verified':
            result['scheme']=None
        return result
