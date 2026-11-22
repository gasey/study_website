"""Text-only study notes. Every linked entity retains its own visibility rules."""
import re
from urllib.parse import quote
from fastapi import HTTPException
from ..source_files import source_pdf_url
from . import audience
from .community_policy import helpful_count,AUTHOR_TIER,AUTHOR_PROFILE

URL_TEXT=re.compile(r'(?i)(?:[a-z][a-z0-9+.-]*://|www\.|(?<!:)//|\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.[a-z]{2,63}\b|\]\s*\()')

def clean_body(value):
    if any(ord(c)<32 and c not in '\n\t' for c in value):raise ValueError('Unsupported control characters')
    if URL_TEXT.search(value):raise ValueError('Use the optional linked item instead of putting a URL in your note')
    return value

# Used in the mixed feed before LIMIT/OFFSET. Question gates are shared with
# canonical discussions by the outer query's q alias.
REFERENCE_VISIBLE="""(
 p.source_context->'study_reference' IS NULL
 OR p.source_context->'study_reference'->>'kind'='question'
 OR (p.source_context->'study_reference'->>'kind'='material' AND EXISTS(
   SELECT 1 FROM materials m WHERE m.id=p.source_context->'study_reference'->>'id'
   AND m.status='published' AND m.published_revision IS NOT NULL
   AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=%(user)s AND b.blocked_id=m.author_id) OR (b.user_id=m.author_id AND b.blocked_id=%(user)s))))
 OR (p.source_context->'study_reference'->>'kind'='paper' AND EXISTS(
   SELECT 1 FROM papers paper WHERE paper.id=p.source_context->'study_reference'->>'id'
   AND (%(scope)s='all' OR paper.exam_scope_id=%(scope)s)))
 OR (p.source_context->'study_reference'->>'kind'='exam' AND EXISTS(
   SELECT 1 FROM collections c WHERE c.id=p.source_context->'study_reference'->>'id'
   AND c.visibility='public' AND (%(scope)s='all' OR c.exam_scope_id=%(scope)s)))
)"""



def reference_visible():
    return REFERENCE_VISIBLE.replace("m.status='published'","m.status='published' AND "+audience.subject_sql('m.author_id',team=True))


async def reference(cur,link,user):
    if not link:return None
    kind,entity_id=link['kind'],link['id']
    if kind=='question':
        from ..routers.discussions import access
        state=await access(cur,entity_id,user)
        if not state['allowed']:raise HTTPException(403,'Check or show the linked question’s answer before reading this study note')
        await cur.execute("SELECT question AS label FROM canonical_questions WHERE id=%s AND status IN ('live','held')",(entity_id,))
        row=await cur.fetchone();url='/bank/'+quote(entity_id,safe='')
    elif kind=='material':
        await cur.execute("""SELECT r.payload->>'title' AS label,r.payload->>'access' AS access,r.payload->>'kind' AS format FROM materials m JOIN material_revisions r ON r.material_id=m.id AND r.revision=m.published_revision
          WHERE m.id=%s AND m.status='published' AND """+audience.subject_sql('m.author_id',team=True)+""" AND NOT EXISTS(SELECT 1 FROM creator_blocks b
            WHERE (b.user_id=%s AND b.blocked_id=m.author_id) OR (b.user_id=m.author_id AND b.blocked_id=%s))""",(entity_id,user,user))
        row=await cur.fetchone();url='/materials/'+quote(entity_id,safe='')
    elif kind=='paper':
        await cur.execute('SELECT id,exam_name AS label,source_file FROM papers WHERE id=%s OR source_file=%s ORDER BY (id=%s) DESC,id LIMIT 1',(entity_id,entity_id,entity_id))
        row=await cur.fetchone();url=source_pdf_url(row['source_file']) if row else None
        if row:entity_id=row['id']
    else:
        await cur.execute("SELECT title AS label FROM collections WHERE id=%s AND visibility='public'",(entity_id,))
        row=await cur.fetchone();url='/exams/'+quote(entity_id,safe='')
    if not row or not url:raise HTTPException(404,'Linked item is unavailable')
    return {'kind':kind,'id':entity_id,'label':row['label'],'url':url,**({'access':row['access'],'format':row['format']} if kind=='material' else {})}

async def visible(cur,pid,user):
    await cur.execute('''SELECT p.id,p.kind,p.parent_id,p.body,p.topic_tag,t.label AS topic_label,p.source_context,p.author_id,p.author_id=%s AS is_author,
      p.needs_approval,p.content_version,p.edited_at,p.edit_locked,p.created_at,u.avatar,COALESCE(u.handle,'Learner') AS author,'''+AUTHOR_TIER+''' AS author_tier,'''+AUTHOR_PROFILE+''' AS author_profile_id,'''+helpful_count()+''' AS helpful,
      EXISTS(SELECT 1 FROM post_votes WHERE post_id=p.id AND user_id=%s) AS voted
      FROM posts p LEFT JOIN users u ON u.id=p.author_id LEFT JOIN review_taxonomy t ON t.id=p.topic_tag
      WHERE p.id=%s AND p.kind IN ('study','material-share') AND NOT p.hidden AND NOT p.before_fix AND (NOT p.needs_approval OR p.author_id=%s)
      AND '''+audience.subject_sql('p.author_id',team=True)+''' AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=%s AND b.blocked_id=p.author_id) OR (b.user_id=p.author_id AND b.blocked_id=%s))''',(user,user,pid,user,user,user))
    row=await cur.fetchone()
    if not row:raise HTTPException(404,'Study note not found')
    if row['parent_id']:
        parent=await visible(cur,row['parent_id'],user)
        if parent['parent_id'] or parent['needs_approval']:raise HTTPException(404,'Published conversation not found')
    row['reference']=await reference(cur,row.pop('source_context').get('study_reference'),user)
    return row


async def conversation(cur,pid,user,*,lock=False):
    if lock:
        # Replies and parent withdrawal/moderation serialize on the same post.
        await cur.execute('SELECT id FROM posts WHERE id=%s FOR UPDATE',(pid,))
    parent=await visible(cur,pid,user)
    if parent['parent_id'] or parent['needs_approval']:
        raise HTTPException(409,'Replies open after the top-level post is published')
    return parent
