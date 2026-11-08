"""Explicit, versioned paper-library composition; never edits question content."""
from typing import Annotated
from copy import deepcopy
from decimal import Decimal
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field
from .review_policy import digest
from . import review_scope

SourceId=Annotated[str,Field(min_length=1,max_length=600)]
ModuleId=Annotated[str,Field(min_length=1,max_length=100)]

class Selection(BaseModel):
    model_config=ConfigDict(extra='forbid')
    papers:list[SourceId]=Field(default_factory=list,max_length=1000)
    modules:list[ModuleId]=Field(default_factory=list,max_length=30)
    excluded_papers:list[SourceId]=Field(default_factory=list,max_length=1000)

async def head(cur,collection,lock=False):
    await cur.execute('SELECT * FROM collections WHERE id=%s'+(' FOR UPDATE' if lock else ''),(collection,))
    row=await cur.fetchone()
    if not row or row['kind'] not in ('exam','practice'):raise HTTPException(404,'Exam module not found')
    if row['visibility']!='public' and (row['visibility']!='hidden' or row['live_version'] is not None):
        raise HTTPException(422,'Restricted modules cannot be made public through this editor')
    return row

async def snapshot(cur,collection,version):
    await cur.execute('SELECT * FROM collection_papers WHERE collection_id=%s AND version=%s ORDER BY paper_id',(collection,version))
    papers=await cur.fetchall()
    await cur.execute('SELECT * FROM collection_sections WHERE collection_id=%s AND version=%s ORDER BY position,path',(collection,version))
    return {'papers':papers,'sections':await cur.fetchall()}

async def seed(cur,h):
    old=await snapshot(cur,h['id'],h['live_version'])
    return {'papers':[p['paper_id'] for p in old['papers']], 'modules':[], 'excluded_papers':[]}

async def no_cycle(cur,target,sources):
    await cur.execute('''SELECT h.collection_id,h.payload FROM module_composition_history h
      JOIN collections c ON c.id=h.collection_id AND c.live_version=h.version''')
    graph={r['collection_id']:r['payload'].get('selection',{}).get('modules',[]) for r in await cur.fetchall()}
    graph[target]=sources
    visited=set()
    def visit(node,path):
        if node in path:raise HTTPException(422,'A module cannot include itself, directly or through another module')
        if node in visited:return
        if len(path)>100:raise HTTPException(422,'Module dependency chain is too deep')
        for child in graph.get(node,[]):visit(child,path|{node})
        visited.add(node)
    visit(target,set())

async def compile_selection(cur,h,selection):
    value=selection.model_dump()
    for key in value:
        if len(set(value[key]))!=len(value[key]):raise HTTPException(422,'Remove duplicate selections')
    await no_cycle(cur,h['id'],value['modules'])
    original=await snapshot(cur,h['id'],h['live_version'])
    config={p['paper_id']:p for p in original['papers']}
    selected=set(value['papers']);sources=[]
    for module in sorted(value['modules']):
        source=await head(cur,module)
        if source['visibility']!='public' or source['live_version'] is None:raise HTTPException(422,'Choose a published source module')
        if source['exam_scope_id']!=h['exam_scope_id']:raise HTTPException(422,'Source modules must use the same exam bank scope')
        snap=await snapshot(cur,module,source['live_version'])
        sources.append({'id':module,'title':source['title'],'version':source['live_version'],'snapshot_hash':digest(snap)})
        for p in snap['papers']:
            if p['allow_browse']:
                selected.add(p['paper_id']);config.setdefault(p['paper_id'],{**p,'as_mock':False})
    selected-=set(value['excluded_papers'])
    if not selected:raise HTTPException(422,'Keep at least one source paper')
    if len(selected)>1000:raise HTTPException(422,'A module may contain at most 1000 source papers')
    await cur.execute('SELECT id,exam_scope_id,exam_name,year,exam_type FROM papers WHERE id=ANY(%s) ORDER BY id',(sorted(selected),))
    metadata=await cur.fetchall()
    if len(metadata)!=len(selected):raise HTTPException(422,'One or more source papers no longer exist')
    if any(p['exam_scope_id']!=h['exam_scope_id'] for p in metadata):raise HTTPException(422,'Keep source papers in this module’s exam bank scope')
    papers=[]
    for p in metadata:
        previous=config.get(p['id'])
        # New sources are browse/practice entries, never silently official timed mocks.
        papers.append({**({k:v for k,v in previous.items() if k not in ('collection_id','version')} if previous else
          {'paper_id':p['id'],'as_mock':False,'section_path':'papers','display_title':None,'duration_minutes':None,
           'marks_correct':None,'marks_wrong':None,'instructions':None,'allow_browse':True,'allow_practice':True,'rule_source':'platform-default'})})
    for paper in papers:
        for key,item_value in paper.items():
            if isinstance(item_value,Decimal):paper[key]=float(item_value)
    sections=deepcopy(original['sections'])
    # Existing subject/curated sections retain their predicates and source boundaries.
    # Only the explicit paper-library section reflects new additions.
    removed=set(p['paper_id'] for p in original['papers'])-selected
    removed.update(value['excluded_papers'])
    await cur.execute('SELECT DISTINCT canonical_id FROM appearances WHERE paper_id=ANY(%s)',(sorted(removed),))
    removed_pins={r['canonical_id'] for r in await cur.fetchall()}
    all_papers=None
    for section in sections:
        section.pop('collection_id',None);section.pop('version',None)
        query=section['query']
        if 'paper_ids' in query:
            query['paper_ids']=sorted(set(query['paper_ids'])-removed)
        elif removed:
            if all_papers is None:
                await cur.execute('SELECT id FROM papers ORDER BY id')
                all_papers={r['id'] for r in await cur.fetchall()}
            query['paper_ids']=sorted(all_papers-removed)
        section['pins']=[q for q in section['pins'] if q not in removed_pins]
    library=next((s for s in sections if s['path']=='papers' and set(s['query'])<= {'paper_ids'} and not s['pins'] and not s['excludes']),None)
    if library:library['query']={'paper_ids':sorted(selected)}
    elif not sections:
        sections=[{'path':'papers','title':'Source papers','position':0,'formats':[],'query':{'paper_ids':sorted(selected)},'pins':[],'excludes':[],'note':None}]
    # Sections need not be added to existing specialised modules: library membership
    # already exists independently and must not erase their subject navigation.
    await cur.execute('''SELECT a.id,a.canonical_id,a.paper_id,q.status,q.key_disputed,q.source_defect
      FROM appearances a JOIN canonical_questions q ON q.id=a.canonical_id WHERE a.paper_id=ANY(%s)
      ORDER BY a.id''',(sorted(selected),))
    appearances=await cur.fetchall()
    paths={s['path'] for s in sections}
    for paper in papers:
        if paper['section_path'] not in paths:paper['section_path']='papers' if 'papers' in paths else None
    return {'selection':value,'sources':sources,'papers':papers,'sections':sections,'metadata':metadata,'appearances':appearances,'original':original}

async def preview(cur,h,selection,actor):
    compiled=await compile_selection(cur,h,selection)
    before=[]
    if h['live_version'] is not None and h['visibility']=='public':
        _,before=await review_scope.rows(cur,'module:'+h['id'],actor)
    # Full paper library includes only browse-enabled entries; retained sections
    # can also select sources whose full-paper browsing was disabled.
    browse={p['paper_id'] for p in compiled['papers'] if p['allow_browse']}
    # Use the same scope predicate against proposed sections in a parameterised CTE.
    # This also preserves curated pins/excludes instead of approximating counts.
    from psycopg.types.json import Jsonb
    await cur.execute('''WITH sections AS (SELECT * FROM jsonb_to_recordset(%(sections)s)
      AS s(query jsonb,pins text[],excludes text[]))
      SELECT DISTINCT a.id,a.canonical_id,a.paper_id FROM appearances a
      WHERE (a.paper_id=ANY(%(browse)s) OR EXISTS (
        SELECT 1 FROM sections s WHERE a.canonical_id<>ALL(s.excludes) AND
        (a.canonical_id=ANY(s.pins) OR ((NOT(s.query ? 'paper_ids') OR a.paper_id IN
          (SELECT jsonb_array_elements_text(s.query->'paper_ids')))
          AND (s.query->>'subject_id' IS NULL OR EXISTS (SELECT 1 FROM v_question_paths qp
            WHERE qp.question_id=a.canonical_id AND qp.review_status='approved' AND qp.subject_id=s.query->>'subject_id'))
          AND (s.query->>'topic_id' IS NULL OR EXISTS (SELECT 1 FROM v_question_paths qp
            WHERE qp.question_id=a.canonical_id AND qp.review_status='approved' AND qp.topic_id=s.query->>'topic_id')))))) ORDER BY a.id''',
      {'sections':Jsonb(compiled['sections']),'selected':[p['paper_id'] for p in compiled['papers']],'browse':sorted(browse)})
    after=await cur.fetchall();old_ids={r['id'] for r in before};new_ids={r['id'] for r in after}
    old_papers={p['paper_id'] for p in compiled['original']['papers']};new_papers={p['paper_id'] for p in compiled['papers']}
    await cur.execute('SELECT id,exam_name,year FROM papers WHERE id=ANY(%s) ORDER BY year DESC NULLS LAST,exam_name,id',(sorted(old_papers^new_papers),))
    changed=await cur.fetchall()
    token=digest({'head':h,'compiled':compiled,'before':sorted(old_ids),'after':sorted(new_ids)})
    return compiled,{'token':token,'before':{'papers':len(old_papers),'appearances':len(old_ids),'questions':len({r['canonical_id'] for r in before})},
      'after':{'papers':len(new_papers),'appearances':len(new_ids),'questions':len({r['canonical_id'] for r in after})},
      'added_appearances':len(new_ids-old_ids),'removed_appearances':len(old_ids-new_ids),
      'added_papers':[p for p in changed if p['id'] in new_papers], 'removed_papers':[p for p in changed if p['id'] in old_papers],
      'sources':compiled['sources'],'retained_sections':len(compiled['sections']),
      'notice':'This changes the module’s source-paper library. Existing subject filters and scoring restrictions remain. It does not retag questions, expand assignments or change other modules. Imported module libraries are versioned snapshots.'}
