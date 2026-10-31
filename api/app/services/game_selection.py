"""Named learning areas, strict shared pools and frozen, consented game contexts."""
import hashlib,json
from typing import Literal
from fastapi import HTTPException
from pydantic import BaseModel,ConfigDict,Field
from ..source_files import figure_image_url,source_pdf_url
from . import games as g

CURATED_TOPICS=('english/grammar','english/vocabulary','english/comprehension','english/sentence-correction','reasoning-and-aptitude/numerical-ability','reasoning-and-aptitude/verbal-reasoning','reasoning-and-aptitude/series','reasoning-and-aptitude/data-interpretation')

class Selection(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    kind:Literal['mixed','area','exam']
    area_id:str|None=Field(default=None,max_length=120)
    collection_id:str|None=Field(default=None,max_length=120)
    section:str|None=Field(default=None,max_length=200)
    excluded_areas:list[str]=Field(default_factory=list,max_length=20)

async def area(cur,identifier):
    if identifier.startswith('shelf:'):
        await cur.execute('SELECT title,match_ids FROM library_shelves WHERE id=%s AND active',(identifier[6:],))
    elif identifier.startswith('subject:'):
        await cur.execute("SELECT label AS title,ARRAY[id]AS match_ids FROM review_taxonomy WHERE id=%s AND level='subject'",(identifier[8:],))
    elif identifier.startswith('topic:') and identifier[6:]in CURATED_TOPICS:
        await cur.execute("SELECT CASE WHEN id='reasoning-and-aptitude/numerical-ability' THEN 'Arithmetic (Numerical Ability)' ELSE label END AS title,ARRAY[id]AS match_ids FROM review_taxonomy WHERE id=%s AND level='topic'",(identifier[6:],))
    else:raise HTTPException(422,'Choose a listed subject or learning area')
    row=await cur.fetchone()
    if not row:raise HTTPException(409,'This learning area has changed. Choose an area again.')
    return row

async def resolve(cur,selection,mode):
    sel=selection.model_dump();sel['excluded_areas']=sorted(set(sel['excluded_areas']))
    if sel['kind']=='mixed' and any(sel[k]for k in ['area_id','collection_id','section']):raise HTTPException(422,'Mixed subjects cannot contain a hidden area or exam filter')
    if sel['kind']=='area'and(not sel['area_id']or sel['collection_id']or sel['section']):raise HTTPException(422,'Choose one area')
    if sel['kind']=='exam'and not sel['collection_id']:raise HTTPException(422,'Choose an exam')
    if mode=='cup'and(sel['kind']!='mixed'or sel['excluded_areas']):raise HTTPException(422,'The weekly cup uses its fixed mixed set; personal exclusions do not apply')
    ctx={'schema':1,'source_scope':'mizoram-recruitment','source_label':'MPSC & Mizoram recruitment','selector':sel,'mode':mode,'rules':{'questions':g.MODES[mode][0],'round_seconds':g.MODES[mode][1],'total_seconds':60 if mode=='speed'else g.MODES[mode][0]*g.MODES[mode][1],'scoring':'official-key-v1'},'label':'Mixed subjects','match_ids':[],'excluded_match_ids':[],'excluded_labels':[],'paper_ids':None,'pins':[],'excludes':[],'section_subject':None,'section_topic':None}
    if sel['kind']=='exam':
        await cur.execute("SELECT id,title,live_version FROM collections WHERE id=%s AND kind='exam' AND visibility='public' AND exam_scope_id='mizoram-recruitment'",(sel['collection_id'],));exam=await cur.fetchone()
        if not exam:raise HTTPException(409,'This exam is not available for Mizoram games')
        await cur.execute('SELECT paper_id FROM collection_papers WHERE collection_id=%s AND version=%s AND allow_browse ORDER BY paper_id',(exam['id'],exam['live_version']));ctx['paper_ids']=[x['paper_id']for x in await cur.fetchall()];ctx['collection_version']=exam['live_version'];ctx['label']=exam['title']+' · Mixed subjects from these exam papers';ctx['source_label']=exam['title']+' papers · MPSC & Mizoram recruitment'
        if sel['section']:
            await cur.execute('SELECT title,query,pins,excludes FROM collection_sections WHERE collection_id=%s AND version=%s AND path=%s',(exam['id'],exam['live_version'],sel['section']));section=await cur.fetchone()
            if not section:raise HTTPException(409,'This exam section has changed. Choose it again.')
            query=section['query'];ctx['label']=exam['title']+' · '+section['title'];ctx['pins']=sorted(section['pins']);ctx['excludes']=sorted(section['excludes']);ctx['section_subject']=query.get('subject_id');ctx['section_topic']=query.get('topic_id')
            if 'paper_ids'in query:ctx['paper_ids']=sorted(set(ctx['paper_ids'])&set(query['paper_ids']))
        if not ctx['paper_ids']:ctx['paper_ids']=[]
    if sel['area_id']:
        item=await area(cur,sel['area_id']);ctx['match_ids']=sorted(item['match_ids']);ctx['label']=item['title']+(' · '+exam['title']if sel['kind']=='exam'else'')+(' · '+section['title']if sel['kind']=='exam'and sel['section']else'')
    for aid in sel['excluded_areas']:
        item=await area(cur,aid);ctx['excluded_match_ids']+=item['match_ids'];ctx['excluded_labels'].append(item['title'])
    ctx['excluded_match_ids']=sorted(set(ctx['excluded_match_ids']))
    return ctx

def clauses(ctx):
    sql=[];args=[]
    if ctx.get('match_ids'):
        sql.append('EXISTS(SELECT 1 FROM v_question_paths m WHERE m.question_id=v.id AND (m.subject_id=ANY(%s)OR m.topic_id=ANY(%s)OR m.subtopic_id=ANY(%s)))');args += [ctx['match_ids']]*3
    if ctx.get('excluded_match_ids'):
        sql.append('v.id IN(SELECT question_id FROM v_question_paths) AND v.id NOT IN(SELECT m.question_id FROM v_question_paths m WHERE m.subject_id=ANY(%s)OR m.topic_id=ANY(%s)OR m.subtopic_id=ANY(%s))');args += [ctx['excluded_match_ids']]*3
    if ctx.get('section_subject')or ctx.get('section_topic'):
        sql.append('(v.id=ANY(%s)OR EXISTS(SELECT 1 FROM v_question_paths m WHERE m.question_id=v.id AND(%s::text IS NULL OR m.subject_id=%s)AND(%s::text IS NULL OR m.topic_id=%s)))');args += [ctx['pins'],ctx['section_subject'],ctx['section_subject'],ctx['section_topic'],ctx['section_topic']]
    sql.append('v.id<>ALL(%s)');args.append(ctx.get('excludes',[]))
    return (' AND '.join(sql),args)

async def candidates(cur,ctx,ids=None,full=False):
    where,args=clauses(ctx)
    source_filter='';source_args=[]
    if ctx.get('paper_ids')is not None:source_filter=' AND x.paper_id=ANY(%s)';source_args=[ctx['paper_ids']]
    fields='v.*,a.id AS appearance_id,a.direction AS appearance_direction,a.passage AS appearance_passage,a.question_markup AS appearance_question_markup,a.options_markup AS appearance_options_markup,a.has_diagram AS appearance_has_diagram,a.figure_image AS appearance_figure_image,a.paper_id,a.qnum,a.page,p.exam_name,p.year,p.source_file,p.pdf_url'if full else"v.id,a.id AS appearance_id,md5(concat_ws('|',v.question,v.options::text,v.answer_text,COALESCE(a.direction,v.direction),COALESCE(a.passage,v.passage),a.figure_image))AS eligibility_revision"
    extra=' AND v.id=ANY(%s)'if ids is not None else''
    # The displayed appearance enforces launch scope directly. Reusing v_launch_scorable
    # adds a redundant corpus-wide DISTINCT and caused >45s scans; v_scorable
    # retains identical answer rules with this explicit source constraint.
    # Preview and draw use this exact predicate, including displayed-appearance source/figure validity.
    await cur.execute(f"""SELECT {fields} FROM v_scorable v JOIN LATERAL(
     SELECT x.* FROM appearances x JOIN papers xp ON xp.id=x.paper_id
     WHERE x.canonical_id=v.id AND xp.exam_scope_id='mizoram-recruitment'
     AND x.question=v.question AND x.options=v.options {source_filter}
     AND (NOT COALESCE(x.has_diagram,false)OR x.figure_image ~ '^images/page-renders/[0-9a-f]{{20,64}}[.]png$')
     ORDER BY x.is_primary DESC,x.id LIMIT 1)a ON TRUE JOIN papers p ON p.id=a.paper_id
     WHERE jsonb_array_length(v.options)BETWEEN 2 AND 6
     AND v.options ? v.answer_text AND NOT EXISTS(SELECT 1 FROM appearances ca JOIN papers cp ON cp.id=ca.paper_id WHERE ca.canonical_id=v.id AND cp.exam_type='Community')
     AND {where}{extra} ORDER BY v.id""",source_args+args+([ids]if ids is not None else[]))
    rows=await cur.fetchall()
    if full:
        for r in rows:
            for key in ['direction','passage','question_markup','options_markup']:r[key]=r.pop('appearance_'+key)or r.get(key)
            r['has_diagram']=bool(r.pop('appearance_has_diagram')or r.get('has_diagram'));r['figure_image']=r.pop('appearance_figure_image');r['figure_image_url']=figure_image_url(r['figure_image']);r['source_pdf_url']=source_pdf_url(r['source_file'],r['pdf_url'])
    return rows

async def preview(cur,selection,mode):
    ctx=await resolve(cur,selection,mode);rows=await candidates(cur,ctx)
    # Counts/eligibility changes require a fresh visible confirmation, not silent widening.
    revision=g.digest([(r['id'],r['appearance_id'],r['eligibility_revision'])for r in rows]);ctx['pool_revision']=revision
    token=g.digest(ctx);count=len(rows);need=g.MODES[mode][0]
    public={k:ctx[k]for k in ['label','source_label','rules','excluded_labels','selector']}
    await cur.execute('SELECT p.subject_label AS title,count(DISTINCT p.question_id)::int AS questions FROM v_question_paths p WHERE p.question_id=ANY(%s)GROUP BY p.subject_label ORDER BY p.subject_label',([r['id']for r in rows],))
    public['included_subjects']=await cur.fetchall()
    return {'context':ctx,'context_hash':token,'public':public,'available':count,'required':need,'can_start':count>=need,'message':f'{count} questions with official keys are ready; this game needs {need}.'if count<need else'Some questions may be new to you or repeat from earlier practice.'}

async def draw(cur,ctx):
    rows=await candidates(cur,ctx);ids=[r['id']for r in rows];need=ctx['rules']['questions']
    if ctx.get('pool_revision')and g.digest([(r['id'],r['appearance_id'],r['eligibility_revision'])for r in rows])!=ctx['pool_revision']:raise HTTPException(409,'The question pool changed. Refresh the selection preview.')
    if len(ids)<need:raise HTTPException(409,'There are no longer enough eligible questions. Refresh the selection preview.')
    g.secrets.SystemRandom().shuffle(ids);picked=ids[:need];full={r['id']:r for r in await candidates(cur,ctx,picked,True)}
    if len(full)!=need:raise HTTPException(409,'This set changed. Refresh the selection preview before starting.')
    fields=set(g.PUBLIC_FIELDS)|set(g.IDENTITY)|{'appearance_id','type','explanation'}
    return [{k:full[qid].get(k)for k in fields}for qid in picked]

async def catalog(cur,user):
    # One strict pool census; aggregate approved mappings over these exact usable IDs.
    base=await resolve(cur,Selection(kind='mixed'),'speed');ids=[r['id']for r in await candidates(cur,base)]
    await cur.execute("""SELECT 'shelf:'||s.id AS id,s.title,s.match_ids,count(DISTINCT p.question_id)::int AS questions
      FROM library_shelves s LEFT JOIN v_question_paths p ON p.question_id=ANY(%s)AND(p.subject_id=ANY(s.match_ids)OR p.topic_id=ANY(s.match_ids)OR p.subtopic_id=ANY(s.match_ids))
      WHERE s.active GROUP BY s.id ORDER BY s.position,s.id""",(ids,));areas=await cur.fetchall()
    await cur.execute("SELECT 'subject:'||t.id AS id,t.label AS title,ARRAY[t.id]AS match_ids,count(DISTINCT p.question_id)::int AS questions FROM review_taxonomy t LEFT JOIN v_question_paths p ON p.subject_id=t.id AND p.question_id=ANY(%s) WHERE t.level='subject' GROUP BY t.id ORDER BY t.label",(ids,));areas+=await cur.fetchall()
    await cur.execute("SELECT 'topic:'||t.id AS id,CASE WHEN t.id='reasoning-and-aptitude/numerical-ability' THEN 'Arithmetic (Numerical Ability)' ELSE t.label END AS title,ARRAY[t.id]AS match_ids,count(DISTINCT p.question_id)::int AS questions FROM review_taxonomy t LEFT JOIN v_question_paths p ON p.topic_id=t.id AND p.question_id=ANY(%s) WHERE t.id=ANY(%s) GROUP BY t.id ORDER BY title",(ids,list(CURATED_TOPICS)));areas+=await cur.fetchall()
    seen=set();unique=[]
    for a in areas:
        signature=tuple(sorted(a['match_ids']))
        if signature not in seen:unique.append(a);seen.add(signature)
    areas=sorted(unique,key=lambda a:a['title'])
    await cur.execute("SELECT c.id,c.title,EXISTS(SELECT 1 FROM user_exam_bookmarks b WHERE b.collection_id=c.id AND b.user_id=%s)AS saved FROM collections c WHERE c.kind='exam'AND c.visibility='public'AND c.exam_scope_id='mizoram-recruitment' ORDER BY saved DESC,c.position,c.title",(user,));exams=await cur.fetchall()
    await cur.execute("SELECT canonical_id,max(at)AS latest FROM attempts WHERE user_id=%s AND at>now()-interval '90 days' GROUP BY canonical_id ORDER BY latest DESC LIMIT 100",(user,));recent=[r['canonical_id']for r in await cur.fetchall()]
    suggestions=[]
    if recent:
        await cur.execute('SELECT question_id,subject_id,topic_id,subtopic_id FROM v_question_paths WHERE question_id=ANY(%s)',(recent,));paths=await cur.fetchall()
        for a in areas:
            known={p['question_id']for p in paths if any(p[k]in a['match_ids']for k in ['subject_id','topic_id','subtopic_id'])}
            if len(known)>=3:suggestions.append({'area_id':a['id'],'title':a['title'],'reason':'You answered questions in this area recently.','evidence_count':len(known)})
        suggestions=sorted(suggestions,key=lambda a:(-a['evidence_count'],a['title']))[:3]
    await cur.execute('SELECT selection FROM game_preferences WHERE user_id=%s',(user,));pref=await cur.fetchone()
    return {'areas':[{k:v for k,v in a.items()if k!='match_ids'}for a in areas],'exams':exams,'suggestions':suggestions,'saved_selection':pref['selection']if pref else None,'source_label':'MPSC & Mizoram recruitment','mixed_available':len(ids)}
