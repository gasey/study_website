"""Named learning areas, strict shared pools and frozen, consented game contexts."""
import hashlib,json
from typing import Literal
from fastapi import HTTPException
from pydantic import BaseModel,ConfigDict,Field
from ..source_files import figure_image_url,source_pdf_url
from . import games as g

CURATED_TOPICS=('english/grammar','english/vocabulary','english/comprehension','english/sentence-correction','reasoning-and-aptitude/numerical-ability','reasoning-and-aptitude/verbal-reasoning','reasoning-and-aptitude/series','reasoning-and-aptitude/data-interpretation')

PILLAR_LABELS={
    'gk_gs':'GK & General Studies',
    'everyday_math':'Everyday Maths & Reasoning',
    'english':'General English',
}

PILLAR_MATCH_IDS={
    'gk_gs':(
        'general-studies',
        'general-knowledge',
        'science/biology',
        'science/physics',
        'science/chemistry',
        'environment-and-ecology',
    ),
    'everyday_math':(
        'mathematics/arithmetic',
        'mathematics/arithmetic/averages',
        'mathematics/arithmetic/percentages',
        'mathematics/arithmetic/profit-and-loss',
        'mathematics/arithmetic/ratio-and-proportion',
        'mathematics/mensuration',
        'mathematics/mensuration/area',
        'mathematics/mensuration/volume',
        'mathematics/geometry',
        'mathematics/geometry/circles',
        'mathematics/geometry/lines-and-angles',
        'mathematics/geometry/triangles',
        'mathematics/algebra',
        'mathematics/algebra/algebraic-expressions',
        'mathematics/algebra/linear-equations',
        'mathematics/algebra/quadratic-equations',
        'reasoning-and-aptitude',
        'reasoning-and-aptitude/numerical-ability',
        'reasoning-and-aptitude/verbal-reasoning',
        'reasoning-and-aptitude/series',
        'reasoning-and-aptitude/data-interpretation',
    ),
    'english':(
        'english/grammar',
        'english/vocabulary',
        'english/sentence-correction',
        'english/comprehension',
    ),
}

FOUNDATION_PRESETS={
    'arts-comfort':{
        'id':'arts-comfort',
        'title':'Humanities & Arts Comfort Mix',
        'badge':'Arts · Humanities · Law Stream',
        'subtitle':'50% GK/GS · 30% General English · 20% Everyday Maths (45s math clock)',
        'quotas':{'gk_gs':5,'english':3,'everyday_math':2},
        'math_round_seconds':45,
        'courage_pillar':'everyday_math',
    },
    'science-bridge':{
        'id':'science-bridge',
        'title':'Science & Tech GK Bridge',
        'badge':'Science · Engineering · Medical Stream',
        'subtitle':'60% GK/GS (Polity, History, Mizoram) · 20% English · 20% Everyday Maths',
        'quotas':{'gk_gs':6,'english':2,'everyday_math':2},
        'math_round_seconds':35,
        'courage_pillar':'gk_gs',
    },
    'balanced-core':{
        'id':'balanced-core',
        'title':'Balanced MPSC Common Core',
        'badge':'All Streams · Standard Prelims & UDC Blueprint',
        'subtitle':'40% GK/GS · 30% General English · 30% Everyday Maths (40s math clock)',
        'quotas':{'gk_gs':4,'english':3,'everyday_math':3},
        'math_round_seconds':40,
        'courage_pillar':'everyday_math',
    },
    'commerce-core':{
        'id':'commerce-core',
        'title':'Commerce & Accounts Core',
        'badge':'Commerce · JAO · Accounts Stream',
        'subtitle':'40% GK/GS & Economy · 30% Everyday Arithmetic & DI · 30% English',
        'quotas':{'gk_gs':4,'english':3,'everyday_math':3},
        'math_round_seconds':40,
        'courage_pillar':'gk_gs',
    },
    'gk-foundation':{
        'id':'gk-foundation',
        'title':'GK & General Studies Pillar',
        'badge':'Single Pillar · Non-Technical',
        'subtitle':'100% Polity, History, Geography, Economy, Mizoram GK & Everyday Science',
        'quotas':{'gk_gs':10,'english':0,'everyday_math':0},
        'math_round_seconds':25,
        'courage_pillar':None,
    },
    'math-foundation':{
        'id':'math-foundation',
        'title':'Everyday Maths & Reasoning Pillar',
        'badge':'Single Pillar · Non-Technical Quant',
        'subtitle':'100% Simple Arithmetic, Percentages, Ratio, Mensuration & Reasoning (45s clock)',
        'quotas':{'gk_gs':0,'english':0,'everyday_math':10},
        'math_round_seconds':45,
        'courage_pillar':'everyday_math',
    },
    'english-foundation':{
        'id':'english-foundation',
        'title':'General English Pillar',
        'badge':'Single Pillar · Grammar & Usage',
        'subtitle':'100% Grammar, Vocabulary, Idioms, Prepositions & Sentence Correction',
        'quotas':{'gk_gs':0,'english':10,'everyday_math':0},
        'math_round_seconds':25,
        'courage_pillar':None,
    },
}

class Selection(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    kind:Literal['mixed','area','exam','foundation']
    area_id:str|None=Field(default=None,max_length=120)
    collection_id:str|None=Field(default=None,max_length=120)
    section:str|None=Field(default=None,max_length=200)
    preset_id:str|None=Field(default=None,max_length=80)
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

def scaled_quotas(base_quotas:dict[str,int],total_questions:int)->dict[str,int]:
    scale=max(1,total_questions//10)
    scaled={k:v*scale for k,v in base_quotas.items()}
    diff=total_questions-sum(scaled.values())
    if diff>0:
        primary=max(base_quotas,key=lambda k:base_quotas[k])
        scaled[primary]+=diff
    return scaled

async def resolve(cur,selection,mode):
    sel=selection.model_dump();sel['excluded_areas']=sorted(set(sel['excluded_areas']))
    if sel['kind']!='foundation':sel.pop('preset_id',None)
    if sel['kind']=='mixed' and any(sel.get(k)for k in ['area_id','collection_id','section']):raise HTTPException(422,'Mixed subjects cannot contain a hidden area or exam filter')
    if sel['kind']=='area'and(not sel['area_id']or sel['collection_id']or sel['section']):raise HTTPException(422,'Choose one area')
    if sel['kind']=='exam'and not sel['collection_id']:raise HTTPException(422,'Choose an exam')
    if sel['kind']=='foundation':
        if not sel.get('preset_id') or sel['preset_id'] not in FOUNDATION_PRESETS or sel.get('area_id') or sel.get('collection_id') or sel.get('section'):
            raise HTTPException(422,'Choose one stream or foundation preset')
    if mode=='cup'and(sel['kind']!='mixed'or sel['excluded_areas']):raise HTTPException(422,'The weekly cup uses its fixed mixed set; personal exclusions do not apply')
    ctx={'schema':1,'source_scope':'mizoram-recruitment','source_label':'MPSC & Mizoram recruitment','selector':sel,'mode':mode,'rules':{'questions':g.MODES[mode][0],'round_seconds':g.MODES[mode][1],'total_seconds':60 if mode=='speed'else g.MODES[mode][0]*g.MODES[mode][1],'scoring':'official-key-v1'},'label':'Mixed subjects','match_ids':[],'excluded_match_ids':[],'excluded_labels':[],'paper_ids':None,'pins':[],'excludes':[],'section_subject':None,'section_topic':None}
    if sel['kind']=='foundation':
        preset=FOUNDATION_PRESETS[sel['preset_id']]
        need=g.MODES[mode][0]
        quotas=scaled_quotas(preset['quotas'],need)
        union_ids=[]
        for p_key,q_count in quotas.items():
            if q_count>0:union_ids.extend(PILLAR_MATCH_IDS[p_key])
        ctx['match_ids']=sorted(set(union_ids))
        ctx['foundation_quotas']=quotas
        ctx['foundation_preset']=preset['id']
        ctx['label']=f"{preset['title']} · Non-Technical Foundation"
        ctx['source_label']='MPSC Shared Non-Technical Core (GK/GS · English · Everyday Maths)'
        math_secs=15 if mode=='speed' else preset['math_round_seconds']
        base_secs=g.MODES[mode][1]
        total_secs=60 if mode=='speed' else sum((math_secs if p_key=='everyday_math' else base_secs)*cnt for p_key,cnt in quotas.items())
        ctx['rules']={
            'questions':need,
            'round_seconds':base_secs,
            'math_round_seconds':math_secs,
            'total_seconds':total_secs,
            'scoring':'foundation-competitive-v1',
            'courage_pillar':preset['courage_pillar'],
            'quotas':quotas,
        }
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
    if sel.get('area_id'):
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
    if ctx.get('trail_ids') is not None:
        sql.append('v.id=ANY(%s)');args.append(ctx['trail_ids'])
    if ctx.get('trail_short'):
        sql.append("length(v.question)<=600 AND NOT COALESCE(a.has_diagram,false) AND COALESCE(a.passage,v.passage,'')='' AND COALESCE(a.direction,v.direction,'')='' AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements_text(v.options) o WHERE length(o)>180)")
    sql.append('v.id<>ALL(%s)');args.append(ctx.get('excludes',[]))
    return (' AND '.join(sql),args)

async def candidates(cur,ctx,ids=None,full=False):
    where,args=clauses(ctx)
    source_filter='';source_args=[]
    if ctx.get('paper_ids')is not None:source_filter=' AND x.paper_id=ANY(%s)';source_args=[ctx['paper_ids']]
    fields='v.*,a.id AS appearance_id,a.direction AS appearance_direction,a.passage AS appearance_passage,a.question_markup AS appearance_question_markup,a.options_markup AS appearance_options_markup,a.has_diagram AS appearance_has_diagram,a.figure_image AS appearance_figure_image,a.paper_id,a.qnum,a.page,p.exam_name,p.year,p.source_file,p.pdf_url'if full else"v.id,a.id AS appearance_id,md5(concat_ws('|',v.question,v.options::text,v.answer_text,COALESCE(a.direction,v.direction),COALESCE(a.passage,v.passage),a.figure_image))AS eligibility_revision"
    if ctx.get('trail_short'):fields+=",md5(lower(regexp_replace(v.question,'[[:space:]]+',' ','g'))||'|'||v.options::text) AS trail_signature"
    extra=' AND v.id=ANY(%s)'if ids is not None else''
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
    if ctx.get('trail_short'):
        seen=set();unique=[]
        for row in rows:
            signature=row.pop('trail_signature')
            if signature not in seen:seen.add(signature);unique.append(row)
        rows=unique
    if full:
        for r in rows:
            for key in ['direction','passage','question_markup','options_markup']:r[key]=r.pop('appearance_'+key)or r.get(key)
            r['has_diagram']=bool(r.pop('appearance_has_diagram')or r.get('has_diagram'));r['figure_image']=r.pop('appearance_figure_image');r['figure_image_url']=figure_image_url(r['figure_image']);r['source_pdf_url']=source_pdf_url(r['source_file'],r['pdf_url'])
    return rows

async def classify_pillars(cur,qids:list[str])->dict[str,set[str]]:
    if not qids:return {'gk_gs':set(),'everyday_math':set(),'english':set()}
    await cur.execute('SELECT question_id,subject_id,topic_id,subtopic_id FROM v_question_paths WHERE question_id=ANY(%s)',(qids,))
    buckets={'gk_gs':set(),'everyday_math':set(),'english':set()}
    math_set=set(PILLAR_MATCH_IDS['everyday_math'])
    eng_set=set(PILLAR_MATCH_IDS['english'])
    gk_set=set(PILLAR_MATCH_IDS['gk_gs'])
    for r in await cur.fetchall():
        qid=r['question_id']
        nodes={r['subject_id'],r['topic_id'],r['subtopic_id']}
        if nodes & math_set:buckets['everyday_math'].add(qid)
        if nodes & eng_set:buckets['english'].add(qid)
        if nodes & gk_set:buckets['gk_gs'].add(qid)
    return buckets

async def preview(cur,selection,mode):
    ctx=await resolve(cur,selection,mode);rows=await candidates(cur,ctx)
    revision=g.digest([(r['id'],r['appearance_id'],r['eligibility_revision'])for r in rows]);ctx['pool_revision']=revision
    token=g.digest(ctx);count=len(rows);need=g.MODES[mode][0]
    public={k:ctx[k]for k in ['label','source_label','rules','excluded_labels','selector']}
    qids=[r['id']for r in rows]
    await cur.execute('SELECT p.subject_label AS title,count(DISTINCT p.question_id)::int AS questions FROM v_question_paths p WHERE p.question_id=ANY(%s)GROUP BY p.subject_label ORDER BY p.subject_label',(qids,))
    public['included_subjects']=await cur.fetchall()
    can_start=count>=need
    msg=f'{count} questions with official keys are ready; this game needs {need}.'if count<need else'Some questions may be new to you or repeat from earlier practice.'
    if ctx.get('foundation_quotas'):
        buckets=await classify_pillars(cur,qids)
        quotas=ctx['foundation_quotas']
        public['pillar_breakdown']=[
            {'pillar':k,'title':PILLAR_LABELS[k],'required':quotas[k],'available':len(buckets[k])}
            for k in ('gk_gs','english','everyday_math') if quotas.get(k,0)>0
        ]
        for item in public['pillar_breakdown']:
            if item['available']<item['required']:
                can_start=False
                msg=f"{item['title']} has {item['available']} eligible questions; this preset needs {item['required']}."
                break
    return {'context':ctx,'context_hash':token,'public':public,'available':count,'required':need,'can_start':can_start,'message':msg}

def interleave_pillars(picked_by_pillar:dict[str,list[str]])->list[tuple[str,str]]:
    queues={k:list(v)for k,v in picked_by_pillar.items() if v}
    order=['gk_gs','english','everyday_math']
    result:list[tuple[str,str]]=[]
    while any(queues.values()):
        for p in order:
            if queues.get(p):
                result.append((queues[p].pop(0),p))
    return result

async def draw(cur,ctx):
    rows=await candidates(cur,ctx);ids=[r['id']for r in rows];need=ctx['rules']['questions']
    if ctx.get('pool_revision')and g.digest([(r['id'],r['appearance_id'],r['eligibility_revision'])for r in rows])!=ctx['pool_revision']:raise HTTPException(409,'The question pool changed. Refresh the selection preview.')
    if len(ids)<need:raise HTTPException(409,'There are no longer enough eligible questions. Refresh the selection preview.')
    rng=g.secrets.SystemRandom()
    pillar_for_qid:dict[str,str]={}
    if ctx.get('foundation_quotas'):
        buckets=await classify_pillars(cur,ids)
        quotas=ctx['foundation_quotas']
        used:set[str]=set()
        picked_by_pillar:dict[str,list[str]]={'gk_gs':[],'english':[],'everyday_math':[]}
        # Allocate smallest pools first (everyday_math -> english -> gk_gs) so disjoint quotas never starve
        for p_key in ('everyday_math','english','gk_gs'):
            q_need=quotas.get(p_key,0)
            if q_need<=0:continue
            pool=[qid for qid in buckets[p_key] if qid not in used]
            if len(pool)<q_need:raise HTTPException(409,f'Not enough eligible questions in {PILLAR_LABELS[p_key]}. Refresh the preview.')
            rng.shuffle(pool)
            chosen=pool[:q_need]
            picked_by_pillar[p_key]=chosen
            used.update(chosen)
        interleaved=interleave_pillars(picked_by_pillar)
        picked=[qid for qid,_ in interleaved]
        pillar_for_qid={qid:p_key for qid,p_key in interleaved}
    else:
        rng.shuffle(ids)
        picked=ids[:need]
    full={r['id']:r for r in await candidates(cur,ctx,picked,True)}
    if len(full)!=need:raise HTTPException(409,'This set changed. Refresh the selection preview before starting.')
    if not pillar_for_qid:
        buckets=await classify_pillars(cur,picked)
        for qid in picked:
            if qid in buckets['everyday_math']:pillar_for_qid[qid]='everyday_math'
            elif qid in buckets['english']:pillar_for_qid[qid]='english'
            elif qid in buckets['gk_gs']:pillar_for_qid[qid]='gk_gs'
    fields=set(g.PUBLIC_FIELDS)|set(g.IDENTITY)|{'appearance_id','type','explanation'}
    out=[]
    rules=ctx.get('rules',{})
    base_secs=rules.get('round_seconds',20)
    math_secs=rules.get('math_round_seconds',base_secs)
    courage_pillar=rules.get('courage_pillar')
    for qid in picked:
        item={k:full[qid].get(k)for k in fields}
        pil=pillar_for_qid.get(qid)
        item['pillar']=pil
        item['pillar_label']=PILLAR_LABELS.get(pil) if pil else None
        item['round_seconds']=math_secs if pil=='everyday_math' else base_secs
        item['courage_eligible']=bool(courage_pillar and pil==courage_pillar)
        out.append(item)
    return out

async def catalog(cur,user):
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
    buckets=await classify_pillars(cur,ids)
    presets_out=[]
    for p in FOUNDATION_PRESETS.values():
        q=p['quotas']
        avail=sum(len(buckets[k]) for k,v in q.items() if v>0)
        presets_out.append({**p,'available':avail})
    return {
        'areas':[{k:v for k,v in a.items()if k!='match_ids'}for a in areas],
        'foundation_presets':presets_out,
        'pillar_counts':{k:len(v) for k,v in buckets.items()},
        'exams':exams,
        'suggestions':suggestions,
        'saved_selection':pref['selection']if pref else None,
        'source_label':'MPSC & Mizoram recruitment',
        'mixed_available':len(ids),
    }
