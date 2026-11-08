"""Owner-only module setup, saved drafts and preview-bound atomic publication."""
from typing import Annotated
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from psycopg.types.json import Jsonb
from ..db import cursor
from ..services.review_identity import Actor, identity, require_role
from ..services import module_composition as composition
from ..services.public_catalog_cache import catalog_cache

router=APIRouter(prefix='/module-setup')
Account=Annotated[Actor,Depends(identity)]

async def owner(cur,actor):
    await require_role(cur,actor.id,roles=('owner',))

class Draft(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    revision:int=Field(ge=0)
    base_version:int|None=None
    selection:composition.Selection

class Publish(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    revision:int=Field(ge=1)
    token:str=Field(pattern=r'^[0-9a-f]{64}$')
    reason:str=Field(min_length=15,max_length=2000)
    request_key:str=Field(min_length=8,max_length=80)

class Create(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    id:str=Field(pattern=r'^[a-z][a-z0-9-]{2,70}$')
    title:str=Field(min_length=3,max_length=160)
    source_module:str=Field(min_length=1,max_length=100)

@router.get('/catalog')
async def catalog(actor:Account):
    async with cursor() as cur:
        await owner(cur,actor)
        await cur.execute("SELECT id,title,live_version,visibility FROM collections WHERE kind IN ('exam','practice') AND (visibility='public' OR (visibility='hidden' AND live_version IS NULL)) ORDER BY title,id")
        return {'items':await cur.fetchall()}

@router.post('/create')
async def create(body:Create,actor:Account):
    async with cursor() as cur:
        await owner(cur,actor)
        await cur.execute("SELECT pg_advisory_xact_lock(hashtextextended('module-composition',0))")
        source=await composition.head(cur,body.source_module)
        if source['visibility']!='public':raise HTTPException(422,'Choose a published source module')
        await cur.execute('SELECT 1 FROM collections WHERE id=%s',(body.id,))
        if await cur.fetchone():raise HTTPException(409,'That module ID already exists; choose another')
        await cur.execute('''INSERT INTO collections(id,title,kind,route,visibility,exam_scope_id)
          VALUES(%s,%s,'exam',%s,'hidden',%s)''',(body.id,body.title.strip(),'/exams/'+body.id,source['exam_scope_id']))
        selection={'papers':[],'modules':[body.source_module],'excluded_papers':[]}
        await cur.execute('''INSERT INTO module_composition_drafts(collection_id,payload,actor_id)
          VALUES(%s,%s,%s)''',(body.id,Jsonb(selection),actor.id))
    return {'id':body.id}

@router.get('/{collection}/papers')
async def papers(collection:str,actor:Account,search:str=Query('',max_length=200),offset:int=Query(0,ge=0,le=100000)):
    async with cursor() as cur:
        await owner(cur,actor);h=await composition.head(cur,collection)
        await cur.execute('''SELECT id,exam_name,year,paper_subject FROM papers WHERE exam_scope_id IS NOT DISTINCT FROM %s
          AND (exam_name||' '||coalesce(year::text,'')||' '||coalesce(paper_subject,'')||' '||id) ILIKE %s
          ORDER BY year DESC NULLS LAST,exam_name,id LIMIT 21 OFFSET %s''',(h['exam_scope_id'],'%'+search.strip()+'%',offset))
        rows=await cur.fetchall();return {'items':rows[:20],'has_more':len(rows)>20}

@router.get('/{collection}')
async def get_setup(collection:str,actor:Account):
    async with cursor() as cur:
        await owner(cur,actor);h=await composition.head(cur,collection)
        await cur.execute('SELECT * FROM module_composition_drafts WHERE collection_id=%s',(collection,));draft=await cur.fetchone()
        selection=draft['payload'] if draft else await composition.seed(cur,h)
        await cur.execute('SELECT id,exam_name,year FROM papers WHERE id=ANY(%s) ORDER BY year DESC NULLS LAST,exam_name,id',(selection['papers']+selection['excluded_papers'],));labels=await cur.fetchall()
        await cur.execute('''SELECT h.version,h.reason,h.created_at,u.handle AS actor,h.payload->'sources' AS sources
          FROM module_composition_history h JOIN users u ON u.id=h.actor_id
          WHERE collection_id=%s ORDER BY version DESC LIMIT 10''',(collection,))
        return {'module':h,'draft':{'revision':draft['revision'] if draft else 0,'base_version':draft['base_version'] if draft else h['live_version'],'selection':selection},'papers':labels,'history':await cur.fetchall()}

@router.post('/{collection}/draft')
async def save(collection:str,body:Draft,actor:Account):
    async with cursor() as cur:
        await owner(cur,actor)
        await cur.execute("SELECT pg_advisory_xact_lock(hashtextextended('module-composition',0))")
        h=await composition.head(cur,collection,True)
        await cur.execute('SELECT * FROM module_composition_drafts WHERE collection_id=%s FOR UPDATE',(collection,));old=await cur.fetchone()
        if (old['revision'] if old else 0)!=body.revision:raise HTTPException(409,'Another admin changed this draft. Reload before saving.')
        if h['live_version']!=body.base_version:raise HTTPException(409,'The published module changed. Reload and compare the new version.')
        await composition.compile_selection(cur,h,body.selection)
        await cur.execute('''INSERT INTO module_composition_drafts(collection_id,revision,base_version,payload,actor_id)
          VALUES(%s,1,%s,%s,%s) ON CONFLICT(collection_id) DO UPDATE SET revision=module_composition_drafts.revision+1,
          base_version=excluded.base_version,payload=excluded.payload,actor_id=excluded.actor_id,updated_at=now() RETURNING revision''',
          (collection,body.base_version,Jsonb(body.selection.model_dump()),actor.id))
        return await cur.fetchone()

async def saved(cur,collection):
    await cur.execute('SELECT * FROM module_composition_drafts WHERE collection_id=%s',(collection,));draft=await cur.fetchone()
    if not draft:raise HTTPException(409,'Save the draft before previewing')
    return draft

@router.post('/{collection}/preview')
async def preview(collection:str,actor:Account):
    async with cursor() as cur:
        await owner(cur,actor);h=await composition.head(cur,collection);draft=await saved(cur,collection)
        if h['live_version']!=draft['base_version']:raise HTTPException(409,'Published version changed; reload and compare before previewing')
        _,result=await composition.preview(cur,h,composition.Selection(**draft['payload']),actor.id)
        return {**result,'revision':draft['revision']}

@router.post('/{collection}/publish')
async def publish(collection:str,body:Publish,actor:Account):
    async with cursor() as cur:
        await owner(cur,actor)
        if len(body.reason.strip())<15:raise HTTPException(422,'Explain this selection change in at least 15 characters')
        await cur.execute("SELECT pg_advisory_xact_lock(hashtextextended('module-composition',0))")
        await cur.execute('SELECT collection_id,version,preview_hash,reason FROM module_composition_history WHERE actor_id=%s AND request_key=%s',(actor.id,body.request_key))
        prior=await cur.fetchone()
        if prior:
            if prior['collection_id']!=collection or prior['preview_hash']!=body.token or prior['reason']!=body.reason.strip():raise HTTPException(409,'Save key already used for another publication')
            return {'version':prior['version'],'replayed':True}
        h=await composition.head(cur,collection,True);draft=await saved(cur,collection)
        if draft['revision']!=body.revision or draft['base_version']!=h['live_version']:raise HTTPException(409,'Draft or published version changed. Preview again.')
        compiled,result=await composition.preview(cur,h,composition.Selection(**draft['payload']),actor.id)
        if result['token']!=body.token:raise HTTPException(409,'Sources or membership changed since preview. Preview again before publishing.')
        await cur.execute('''SELECT greatest(coalesce(%s,0),coalesce(max(version),0))+1 AS version FROM
          (SELECT version FROM collection_papers WHERE collection_id=%s UNION SELECT version FROM collection_sections WHERE collection_id=%s) v''',
          (h['live_version'],collection,collection));version=(await cur.fetchone())['version']
        for p in compiled['papers']:
            await cur.execute('''INSERT INTO collection_papers(collection_id,version,paper_id,as_mock,section_path,display_title,
              duration_minutes,marks_correct,marks_wrong,instructions,allow_browse,allow_practice,rule_source)
              VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
              (collection,version,*(p[k] for k in ('paper_id','as_mock','section_path','display_title','duration_minutes','marks_correct','marks_wrong','instructions','allow_browse','allow_practice','rule_source'))))
        for s in compiled['sections']:
            await cur.execute('''INSERT INTO collection_sections(collection_id,version,path,title,position,formats,query,pins,excludes,note)
              VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',(collection,version,s['path'],s['title'],s['position'],s['formats'],Jsonb(s['query']),s['pins'],s['excludes'],s['note']))
        await cur.execute('''INSERT INTO module_composition_history(collection_id,version,actor_id,reason,payload,preview_hash,request_key)
          VALUES(%s,%s,%s,%s,%s,%s,%s)''',(collection,version,actor.id,body.reason.strip(),Jsonb({k:compiled[k] for k in ('selection','sources','papers','sections')}),body.token,body.request_key))
        await cur.execute("UPDATE collections SET live_version=%s,visibility='public',updated_at=now() WHERE id=%s",(version,collection))
        # Keep a reusable draft and original source dependencies for the next revision.
        await cur.execute('UPDATE module_composition_drafts SET revision=revision+1,base_version=%s,updated_at=now() WHERE collection_id=%s',(version,collection))
    catalog_cache.clear()
    return {'version':version,'replayed':False}
