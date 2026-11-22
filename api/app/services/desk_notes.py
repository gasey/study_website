"""Question-linked notes: private projections and shared-link visibility."""
from copy import deepcopy
from html import escape
from fastapi import HTTPException
from . import audience


async def available_ids(cur,user,ids):
    if not ids:return set()
    from ..routers.learning import not_assessed
    await cur.execute('SELECT q.id FROM canonical_questions q WHERE q.id=ANY(%(ids)s) AND '+not_assessed(),{'ids':list(ids),'user':user})
    return {r['id'] for r in await cur.fetchall()}


async def document(cur,user,raw):
    result=deepcopy(raw)
    notes=result.get('notes',[])
    allowed=await available_ids(cur,user,{n['question_id'] for n in notes if n.get('question_id')})
    result['notes']=[n for n in notes if not n.get('question_id') or n['question_id'] in allowed]
    return result


async def preserve_locked(cur,user,previous,incoming):
    """A filtered full-document save must not erase hidden question notes."""
    result=deepcopy(incoming)
    old=previous.get('notes',[])
    allowed=await available_ids(cur,user,{n['question_id'] for n in old if n.get('question_id')})
    submitted={n['id']:n for n in result.get('notes',[])}
    for note in old:
        if note.get('question_id') and note['question_id'] not in allowed:
            if note['id'] in submitted and submitted[note['id']]!=note:
                raise HTTPException(409,'A question note is locked by an assessment; finish it before changing the note')
            if note['id'] not in submitted:result.setdefault('notes',[]).append(note)
    if len(result.get('notes',[]))>100:
        raise HTTPException(409,'Hidden question notes still occupy their saved slots; finish the assessment before adding more')
    return result


async def shared(cur,did,iid,user):
    # A note link carries no private document or stale body snapshot.
    await cur.execute('''SELECT x.id,x.desk_id,x.author_id,u.handle AS author,x.title,x.body,x.question_id,x.version,x.created_at
      FROM study_desk_items x JOIN users u ON u.id=x.author_id AND u.closed_at IS NULL
      JOIN study_desk_members m ON m.desk_id=x.desk_id AND m.user_id=x.author_id
       AND m.left_at IS NULL AND m.joined_at<=x.created_at
      WHERE '''+audience.subject_sql('x.author_id')+''' AND x.id=%s AND x.desk_id=%s AND x.kind='note' AND x.deleted_at IS NULL
      AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE
       (b.user_id=%s AND b.blocked_id=x.author_id) OR (b.user_id=x.author_id AND b.blocked_id=%s))''',(iid,did,user,user))
    note=await cur.fetchone()
    if not note:raise HTTPException(404,'Shared note is unavailable')
    if note['question_id'] and note['question_id'] not in await available_ids(cur,user,{note['question_id']}):
        raise HTTPException(409,'Finish your assessment before opening this question note')
    return note


def printable(notes,stamp,scope="Your private saved notes."):
    """Plain text only: no remote assets, markup execution or bank answer keys."""
    e=lambda value:escape(str(value or ''),quote=True)
    rows=''.join('<article><h2>'+e(n.get('title') or 'Untitled note')+'</h2>'+
      ('<p class="meta">Question: '+e(n['question_id'])+'</p>' if n.get('question_id') else '')+
      ('<p class="meta">'+e(n.get('subject'))+'</p>' if n.get('subject') else '')+
      '<div class="body">'+e(n.get('body'))+'</div></article>' for n in notes)
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Finna - my notes</title><style>
@page {size:A4;margin:18mm} *{box-sizing:border-box}body{font:15px/1.6 sans-serif;color:#111827;background:white;max-width:760px;margin:24px auto;padding:0 20px;overflow-wrap:anywhere}h1{font-size:28px;margin:0}h2{font-size:19px;line-height:1.35;break-after:avoid}article{border-top:1px solid #ccc;padding:16px 0}p{margin:8px 0}.meta{color:#475569;font-size:12px}.body{white-space:pre-wrap;orphans:3;widows:3}.instructions{padding:12px;background:#eef2ff}@media print{body{margin:0;padding:0;max-width:none}.instructions{display:none}}
</style></head><body><header><h1>My study notes</h1><p class="meta">Exported '''+e(stamp)+'''</p></header>
<p class="instructions">Use your browser's Print command and choose Save as PDF. This copy contains your saved notes. Notes linked to active assessments are omitted. Unsaved browser edits are not included.</p>
<p class="meta">'''+e(scope)+'''</p><p class="meta">Your own writing, not reviewed bank explanations. Question IDs retain their canonical reference.</p>'''+(rows or '<p>No notes are available to print.</p>')+'</body></html>'
