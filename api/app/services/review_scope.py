"""Registered review scopes; a module view never grants source access."""
from fastapi import HTTPException
from .review_policy import digest
from .group_b_study import GROUP_B_COLLECTIONS, PAPER_ROLES, study_membership, general_science_source

AREAS=('common','english','gk-gs','technical')


def permission_sql(inspection=False):
    roles=" AND rg.role IN ('owner','publisher')" if inspection else ''
    return f'''(EXISTS (SELECT 1 FROM review_grants rg WHERE rg.user_id=%(review_user)s AND rg.revoked_at IS NULL
      AND (rg.subject_id IS NULL OR rg.subject_id=qc.subject_id){roles}) OR EXISTS (
      SELECT 1 FROM editorial_assignments e JOIN editorial_assignment_papers ep ON ep.assignment_id=e.id
      JOIN users eu ON eu.id=e.user_id WHERE e.user_id=%(review_user)s AND e.state='active'
      AND e.email=lower(eu.email) AND ep.paper_id=a.paper_id))'''


async def definition(cur, scope, actor_id):
    params={'review_user':actor_id}
    if scope.startswith('assignment:'):
        aid=scope.removeprefix('assignment:')
        await cur.execute('''SELECT e.*,coalesce(e.title,c.title) AS title FROM editorial_assignments e
          LEFT JOIN collections c ON c.id=e.collection_id JOIN users u ON u.id=e.user_id
          WHERE e.id=%s AND e.user_id=%s AND e.state='active' AND e.email=lower(u.email)''',(aid,actor_id))
        row=await cur.fetchone()
        if not row:raise HTTPException(404,'Active assignment not found')
        params['review_assignment']=aid
        await cur.execute('SELECT paper_id FROM editorial_assignment_papers WHERE assignment_id=%s',(aid,))
        params['candidate_papers']=[p['paper_id'] for p in await cur.fetchall()]
        condition='EXISTS (SELECT 1 FROM editorial_assignment_papers ep WHERE ep.assignment_id=%(review_assignment)s AND ep.paper_id=a.paper_id)'
        meta={'id':scope,'title':row['title'],'assignment_id':aid,'collection_id':row['collection_id'],
              'definition_revision':str(row['version']),'kind':'assignment','area':None}
    elif scope.startswith('module:'):
        name=scope.removeprefix('module:');parts=name.split(':')
        collection=parts[0];area=parts[1] if len(parts)==2 else None
        if len(parts)>2 or (area and (collection not in (*GROUP_B_COLLECTIONS,'group-b') or area not in AREAS)):
            raise HTTPException(422,'Choose a registered module and learning area')
        ids=list(GROUP_B_COLLECTIONS) if collection=='group-b' else [collection]
        await cur.execute("SELECT id,title,live_version FROM collections WHERE id=ANY(%s) AND visibility='public' ORDER BY id",(ids,))
        modules=await cur.fetchall()
        if len(modules)!=len(ids):raise HTTPException(404,'Published module not found')
        params['review_collections']=ids
        await cur.execute('''SELECT cs.query FROM collection_sections cs JOIN collections c
          ON c.id=cs.collection_id AND c.live_version=cs.version WHERE cs.collection_id=ANY(%s)''',(ids,))
        bounded=all('paper_ids' in s['query'] for s in await cur.fetchall())
        if bounded or area:
            await cur.execute('''WITH sections AS MATERIALIZED (SELECT cs.* FROM collection_sections cs
              JOIN collections c ON c.id=cs.collection_id AND c.live_version=cs.version WHERE cs.collection_id=ANY(%s))
              SELECT cp.paper_id FROM collection_papers cp JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version
                WHERE cp.collection_id=ANY(%s) AND cp.allow_browse
              UNION SELECT jsonb_array_elements_text(query->'paper_ids') FROM sections
              UNION SELECT a.paper_id FROM appearances a JOIN sections s ON a.canonical_id=ANY(s.pins)''',(ids,ids))
            params['candidate_papers']=[p['paper_id'] for p in await cur.fetchall()]

        title='Group B shared study' if collection=='group-b' else modules[0]['title']
        # Full source-library membership plus section selections (pins/excludes retained).
        condition='''(EXISTS (SELECT 1 FROM collection_papers cp JOIN collections c ON c.id=cp.collection_id
          AND c.live_version=cp.version WHERE cp.collection_id=ANY(%(review_collections)s) AND cp.allow_browse AND cp.paper_id=a.paper_id)
          OR EXISTS (SELECT 1 FROM collection_sections cs JOIN collections c ON c.id=cs.collection_id AND c.live_version=cs.version
            WHERE cs.collection_id=ANY(%(review_collections)s) AND a.canonical_id<>ALL(cs.excludes)
            AND (a.canonical_id=ANY(cs.pins) OR (
              (NOT(cs.query ? 'paper_ids') OR a.paper_id IN (SELECT jsonb_array_elements_text(cs.query->'paper_ids')))
              AND (cs.query->>'subject_id' IS NULL OR EXISTS (SELECT 1 FROM v_question_paths qp WHERE qp.question_id=a.canonical_id AND qp.review_status='approved' AND qp.subject_id=cs.query->>'subject_id'))
              AND (cs.query->>'topic_id' IS NULL OR EXISTS (SELECT 1 FROM v_question_paths qp WHERE qp.question_id=a.canonical_id AND qp.review_status='approved' AND qp.topic_id=cs.query->>'topic_id'))))))'''
        if area:
            membership,area_params=study_membership(area,collection,'all');params.update(area_params)
            source_area='''EXISTS (SELECT 1 FROM collection_papers cp JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version
              WHERE cp.collection_id=ANY(%(review_collections)s) AND cp.allow_browse AND cp.paper_id=a.paper_id)'''
            if area=='technical':source_area+=' AND a.paper_id=ANY(%(gb_technical_papers)s)'
            if area in ('common','gk-gs'):source_area+=" AND (qc.subject_id<>'science' OR "+general_science_source('a')+')'
            condition=f'a.canonical_id IN ({membership}) AND ({source_area})'
            title+=' · '+{'common':'Common subjects','english':'English','gk-gs':'GK / GS','technical':'Technical papers'}[area]
        meta={'id':scope,'title':title,'assignment_id':None,'collection_id':collection,'area':area,'kind':'module',
              'definition_revision':digest({'collections':modules,'roles':PAPER_ROLES if area else None})}
    else:raise HTTPException(422,'Choose a registered review scope')
    return meta,condition,params


async def rows(cur, scope, actor_id, paper=None, appearance=None):
    meta,condition,params=await definition(cur,scope,actor_id)
    extra=''
    if paper:extra+=' AND a.paper_id=%(review_paper)s';params['review_paper']=paper
    if appearance:extra+=' AND a.id=%(review_appearance)s';params['review_appearance']=appearance
    # A bounded source set must be resolved before evaluating section/permission predicates.
    # Otherwise PostgreSQL probes every section for every question in the whole bank.
    prefix="WITH candidates AS MATERIALIZED (SELECT * FROM appearances WHERE paper_id=ANY(%(candidate_papers)s)) " if 'candidate_papers' in params else ''
    source='candidates' if prefix else 'appearances'
    await cur.execute(prefix+f'''SELECT DISTINCT {permission_sql(True)} AS can_check,a.id,a.canonical_id,a.paper_id,a.type,a.qnum,a.qnum_seq,a.page,a.question,
      q.status AS canonical_status,q.key_disputed,q.source_defect,qc.subject_id,qc.topic_id,qc.subtopic_id FROM {source} a
      JOIN canonical_questions q ON q.id=a.canonical_id
      LEFT JOIN question_classifications qc ON qc.question_id=q.id AND qc.is_primary AND qc.review_status='approved'
      WHERE ({condition}) AND {permission_sql()} {extra}
      ORDER BY a.paper_id,a.qnum_seq NULLS LAST,a.id''',params)
    result=await cur.fetchall()
    meta['revision']=digest({'scope':meta['definition_revision'],'members':[(r['id'],r['canonical_id']) for r in result]})
    return meta,result


async def catalog(cur,actor_id,search='',offset=0):
    await cur.execute('''SELECT 1 FROM review_grants WHERE user_id=%s AND revoked_at IS NULL
      UNION ALL SELECT 1 FROM editorial_assignments e JOIN users u ON u.id=e.user_id
      WHERE e.user_id=%s AND e.state='active' AND e.email=lower(u.email) LIMIT 1''',(actor_id,actor_id))
    if not await cur.fetchone():raise HTTPException(403,'Review access is required')
    await cur.execute('''SELECT e.id,coalesce(e.title,c.title) AS title,e.collection_id FROM editorial_assignments e
      LEFT JOIN collections c ON c.id=e.collection_id JOIN users u ON u.id=e.user_id
      WHERE e.user_id=%s AND e.state='active' AND e.email=lower(u.email) ORDER BY title,e.id''',(actor_id,))
    items=[{'id':'assignment:'+r['id'],'title':r['title'],'kind':'assignment','collection_id':r['collection_id']} for r in await cur.fetchall()]
    # Match module metadata only when a permitted appearance actually belongs to its source library/sections.
    await cur.execute("SELECT id,title FROM collections WHERE visibility='public' ORDER BY title,id")
    for c in await cur.fetchall():
        meta,condition,params=await definition(cur,'module:'+c['id'],actor_id)
        await cur.execute(f'''SELECT 1 FROM appearances a JOIN canonical_questions q ON q.id=a.canonical_id
          LEFT JOIN question_classifications qc ON qc.question_id=q.id AND qc.is_primary AND qc.review_status='approved'
          WHERE ({condition}) AND {permission_sql()} LIMIT 1''',params)
        if await cur.fetchone():
            items.append({'id':meta['id'],'title':c['title'],'kind':'module','collection_id':c['id']})
            if c['id'] in GROUP_B_COLLECTIONS:
                items.extend({'id':meta['id']+':'+area,'title':c['title']+' · '+label,'kind':'module','collection_id':c['id']}
                             for area,label in [('common','Common subjects'),('technical','Technical papers')])
    filtered=[r for r in items if all(word in (r['title']+' '+r['id']).lower() for word in search.lower().split())]
    return {'items':filtered[offset:offset+12],'has_more':len(filtered)>offset+12}
