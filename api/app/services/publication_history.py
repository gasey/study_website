"""Read-only, scoped history from immutable correction manifests and receipts."""
from fastapi import HTTPException
from .review_identity import require_role
from . import bank_review

FIELDS={'question':'Question text','options':'Answer options','answerIndex':'Correct option','answerSource':'Answer source',
 'answerKeyRef':'Official key reference','explanation':'Explanation','classification':'Subject & topic tags',
 'relatedClassifications':'Additional tags','page':'PDF page','qnum':'Printed question number','direction':'Instructions',
 'questionMarkup':'Question formatting','optionsMarkup':'Option formatting','passage':'Passage',
 'sourceDefect':'Source issue','disputeNote':'Review note','sourceUrl':'Source link','figureImage':'Question figure',
 'hasDiagram':'Has diagram','duplicateId':'Duplicate reference','paperId':'Paper','difficulty':'Legacy difficulty'}

async def listing(cur,actor_id,*,mine,q,state,kind,offset,limit):
    await cur.execute('SELECT 1 FROM review_grants WHERE user_id=%s AND revoked_at IS NULL LIMIT 1',(actor_id,))
    if not await cur.fetchone():raise HTTPException(403,'Staff access required')
    await cur.execute('''SELECT p.id,p.contribution_id,p.state,p.error,p.created_at,p.finished_at,p.revision,
      COALESCE(p.manifest->'payload'->>'title',c.title) AS title,c.kind,c.canonical_id,c.author_id,u.handle AS author,e.handle AS publisher,
      p.manifest->'baseline'->'paper'->>'title' AS paper_title,
      p.manifest->'baseline'->'record'->>'qnum' AS qnum,
      ARRAY(SELECT jsonb_object_keys(COALESCE(p.manifest->'payload'->'patch','{}'::jsonb))) AS fields
      FROM bank_publications p JOIN bank_contributions c ON c.id=p.contribution_id
      LEFT JOIN users u ON u.id=c.author_id LEFT JOIN users e ON e.id=p.exported_by
      WHERE EXISTS(SELECT 1 FROM review_grants g WHERE g.user_id=%s AND g.revoked_at IS NULL
        AND (g.subject_id IS NULL OR g.subject_id=c.subject_id))
      AND (%s=false OR c.author_id=%s OR p.exported_by=%s)
      AND (%s='' OR p.state=%s) AND (%s='' OR c.kind=%s)
      AND (%s='' OR COALESCE(p.manifest->'payload'->>'title',c.title) ILIKE %s OR c.canonical_id=%s OR p.id=%s
        OR p.manifest->'baseline'->'paper'->>'title' ILIKE %s)
      ORDER BY p.created_at DESC,p.id DESC LIMIT %s OFFSET %s''',
      (actor_id,mine,actor_id,actor_id,state,state,kind,kind,q,'%'+q+'%',q,q,'%'+q+'%',limit+1,offset))
    rows=await cur.fetchall()
    for row in rows:row['fields']=[FIELDS.get(field,field) for field in row['fields']]
    return {'items':rows[:limit],'next_offset':offset+limit if len(rows)>limit else None}

async def detail(cur,actor_id,publication_id):
    await cur.execute('''SELECT p.*,c.subject_id,c.canonical_id FROM bank_publications p
      JOIN bank_contributions c ON c.id=p.contribution_id WHERE p.id=%s''',(publication_id,))
    p=await cur.fetchone()
    if not p:raise HTTPException(404,'Publication not found')
    await require_role(cur,actor_id,p['subject_id'],('owner','publisher','senior','reviewer'),lock=False)
    if p['canonical_id']:
        await bank_review.protect_answer(cur,actor_id,p['canonical_id'])
        await cur.execute("SELECT subject_id FROM question_classifications WHERE question_id=%s AND review_status='approved'",(p['canonical_id'],))
        current=await cur.fetchone()
        if current:await require_role(cur,actor_id,current['subject_id'],('owner','publisher','senior','reviewer'),lock=False)
    manifest=p['manifest'] or {};payload=manifest.get('payload') or {};baseline=manifest.get('baseline') or {}
    patch=payload.get('patch') or {};receipt=p['receipt'] or {};before=receipt.get('before') or baseline.get('record') or {}
    # Receipt values describe historical publication, not today's edited question.
    after=receipt.get('after') or {};before_fields=receipt.get('before_fields') or {}
    changes=[]
    for key,value in patch.items():
        if key not in FIELDS:continue
        changes.append({'field':key,'label':FIELDS[key],
          'before':before_fields[key] if key in before_fields else before.get(key),
          'after':after[key] if key in after else value,
          'recorded_after':key in after,'before_available':key in before_fields or key in before})
    return {'id':p['id'],'state':p['state'],'reason':payload.get('rationale') or '',
      'changes':changes,'has_receipt':bool(receipt),'paper':baseline.get('paper') or {}}
