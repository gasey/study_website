"""Assigned editors can inspect their exact source papers and propose corrections.

An assignment grants neither admin roles nor publication/independent approval.
Email matching alone never activates an invitation.
"""
from fastapi import HTTPException
from .review_policy import digest


async def assigned(cur, user, paper_id):
    await cur.execute('''SELECT e.id FROM editorial_assignments e
      JOIN users u ON u.id=e.user_id JOIN editorial_assignment_papers p ON p.assignment_id=e.id
      WHERE e.user_id=%s AND lower(u.email)=e.email AND e.state='active' AND p.paper_id=%s
      FOR SHARE OF e''', (user,paper_id))
    return bool(await cur.fetchone())


async def source_version(cur, qid, appearance_id=None, lock=False):
    # Transaction versions contain no answer values, unlike a digest of a hidden
    # answer snapshot. The token detects answer/text/options/source changes.
    await cur.execute('''SELECT c.id,c.xmin::text AS canonical_version,
      a.id AS appearance_id,a.xmin::text AS appearance_version,
      p.id AS paper_id,p.xmin::text AS paper_version
      FROM canonical_questions c JOIN appearances a ON a.canonical_id=c.id
      JOIN papers p ON p.id=a.paper_id
      WHERE c.id=%s AND (%s::text IS NULL OR a.id=%s)
      ORDER BY a.is_primary DESC,a.id LIMIT 1''' + (' FOR SHARE OF c,a,p' if lock else ''),
      (qid,appearance_id,appearance_id))
    row=await cur.fetchone()
    if not row: raise HTTPException(404,'Question appearance not found')
    await cur.execute('SELECT xmin::text AS version FROM question_classifications WHERE question_id=%s ORDER BY question_id'+(' FOR SHARE' if lock else ''),(qid,))
    primary=await cur.fetchall()
    await cur.execute('SELECT path_id,xmin::text AS version FROM question_topic_links WHERE question_id=%s ORDER BY path_id'+(' FOR SHARE' if lock else ''),(qid,))
    related=await cur.fetchall()
    return digest({'source':dict(row),'primary':primary,'related':related})


async def require_version(cur, qid, appearance_id, token):
    await cur.execute('''SELECT 1 FROM appearances a JOIN collection_papers cp ON cp.paper_id=a.paper_id
      JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version
      WHERE a.canonical_id=%s AND cp.collection_id IN ('udc','combined-prelims')
      AND cp.allow_browse LIMIT 1''',(qid,))
    protected=bool(await cur.fetchone())
    if not protected:
        await cur.execute('''SELECT 1 FROM appearances a JOIN editorial_assignment_papers ep ON ep.paper_id=a.paper_id
          JOIN editorial_assignments e ON e.id=ep.assignment_id AND e.state='active'
          WHERE a.canonical_id=%s LIMIT 1''',(qid,))
        protected=bool(await cur.fetchone())
    if not token:
        if protected: raise HTTPException(428,'Reopen this assigned question before saving a correction')
        return
    if token!=await source_version(cur,qid,appearance_id,True):
        raise HTTPException(409,'This question changed while you were editing. Reopen it and compare your correction again.')


async def source_versions(cur, paper_ids):
    """Bulk equivalent of source_version, including shared canonical/tag changes."""
    if not paper_ids:return {}
    await cur.execute('''SELECT c.id,c.xmin::text AS canonical_version,
      a.id AS appearance_id,a.xmin::text AS appearance_version,
      p.id AS paper_id,p.xmin::text AS paper_version
      FROM appearances a JOIN canonical_questions c ON c.id=a.canonical_id
      JOIN papers p ON p.id=a.paper_id WHERE a.paper_id=ANY(%s)''',(paper_ids,))
    sources=await cur.fetchall();qids=list({r['id'] for r in sources})
    if not qids:return {}
    await cur.execute('SELECT question_id,xmin::text AS version FROM question_classifications WHERE question_id=ANY(%s) ORDER BY question_id',(qids,))
    primary={r['question_id']:[{'version':r['version']}] for r in await cur.fetchall()}
    await cur.execute('SELECT question_id,path_id,xmin::text AS version FROM question_topic_links WHERE question_id=ANY(%s) ORDER BY question_id,path_id',(qids,))
    related={}
    for row in await cur.fetchall():related.setdefault(row['question_id'],[]).append({'path_id':row['path_id'],'version':row['version']})
    return {r['appearance_id']:digest({'source':dict(r),'primary':primary.get(r['id'],[]),'related':related.get(r['id'],[])}) for r in sources}


async def inspection_fingerprints(cur,paper_ids,appearance_ids=None):
    """Content-based inspection freshness; strict xmin save tokens remain separate."""
    if not paper_ids:return {}
    await cur.execute('''SELECT a.id,to_jsonb(a) AS appearance,to_jsonb(c) AS canonical,
      jsonb_build_object('id',p.id,'title',p.exam_name,'year',p.year,'source_file',p.source_file,'pdf_url',p.pdf_url) AS paper,
      COALESCE((SELECT jsonb_agg(jsonb_build_object('id',d.id,'hash',d.sha256,'kind',d.kind,'status',d.key_status) ORDER BY d.id)
        FROM review_documents d WHERE d.paper_id=p.id),'[]'::jsonb) AS documents
      FROM appearances a JOIN canonical_questions c ON c.id=a.canonical_id
      JOIN papers p ON p.id=a.paper_id WHERE p.id=ANY(%s)
      AND (%s::text[] IS NULL OR a.id=ANY(%s))''',(paper_ids,appearance_ids,appearance_ids))
    result={}
    for row in await cur.fetchall():
        a,c=row['appearance'],row['canonical']
        pick=lambda obj,keys:{k:obj.get(k) for k in keys.split()}
        source=digest({'v':1,'paper':row['paper'],'documents':[d for d in row['documents'] if d['kind']=='paper'],
          'appearance':pick(a,'id type question options direction question_markup options_markup passage page qnum has_diagram figure_image series'),
          'canonical':pick(c,'id type question options source_defect dispute_note')})
        answer=digest({'source':source,'keys':[d for d in row['documents'] if d['kind']=='official-key'],
          'appearance':pick(a,'answer_index answer_source answer_key_ref'),
          'canonical':pick(c,'answer_text answer_source answer_key_ref key_disputed status')})
        explanation=digest({'source':source,'answer':answer,'appearance':a.get('explanation'),'canonical':c.get('explanation')})
        result[row['id']]={'v':1,'source':source,'answer':answer,'explanation':explanation}
    return result


def changed_aspects(check,current_token,current_fingerprints):
    if not check:return []
    old=check.get('fingerprints')
    if not old or old.get('v')!=1:return ['source'] if check.get('source_version')!=current_token else []
    return [key for key in ('source','answer','explanation') if old.get(key)!= (current_fingerprints or {}).get(key)]
