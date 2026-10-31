"""Account-owned inbox over durable notices and existing private desk channels."""
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Response, Request
from pydantic import BaseModel, ConfigDict, Field
from ..db import cursor
from ..services.review_identity import Actor, inbox_identity
from .study_desks import member, VISIBLE, enabled, messages as desk_messages

router = APIRouter(prefix='/api/inbox', tags=['inbox'])
async def inbox_actor(request: Request, actor: Annotated[Actor, Depends(inbox_identity)]):
    expected=request.headers.get('x-inbox-user')
    if (expected and expected != actor.id) or (request.method not in {'GET','HEAD','OPTIONS'} and expected != actor.id):
        raise HTTPException(409,'Your signed-in account changed. Reload before saving.')
    return actor

Account = Annotated[Actor, Depends(inbox_actor)]
Category = Literal['all','discussions','desks','calendar','contributions','materials','scores','system']
CATEGORIES = ['discussions','desks','calendar','contributions','materials','scores','system']
NOTICE_COLUMNS = 'corrected_question_id,question_change_id,id,message,category,silent,contribution_id,mock_id,material_id,calendar_event_id,study_desk_id,study_invite_id,discussion_post_id,discussion_question_id,read_at,created_at'

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')
class ReadState(Strict):
    read: bool
class ReadAll(Strict):
    through_id: int = Field(ge=0)
    category: Category = 'all'
class Preferences(Strict):
    discussions: bool = True
    desks: bool = True
    calendar: bool = True
    contributions: bool = True
    materials: bool = True
    scores: bool = True
    system: bool = True
class ThreadRead(Strict):
    through_id: int = Field(ge=0)

def private(response: Response):
    response.headers['Cache-Control'] = 'private, no-store'

@router.get('/notifications')
async def notices(actor: Account,response: Response,category: Category='all',unread: bool=False,
                  before: int|None=Query(None,ge=1),limit: int=Query(20,ge=1,le=50)):
    private(response)
    async with cursor() as cur:
        await cur.execute('SELECT COALESCE(max(id),0) AS snapshot_id FROM review_notifications WHERE user_id=%s',(actor.id,))
        snapshot = (await cur.fetchone())['snapshot_id']
        await cur.execute(f'''SELECT {NOTICE_COLUMNS} FROM review_notifications
          WHERE user_id=%s AND id<=%s AND (%s='all' OR category=%s)
          AND (NOT %s OR (read_at IS NULL AND NOT silent))
          AND (%s::bigint IS NULL OR id<%s) ORDER BY id DESC LIMIT %s''',
          (actor.id,snapshot,category,category,unread,before,before,limit+1))
        rows = await cur.fetchall()
        await cur.execute('''SELECT category,count(*)::int AS unread FROM review_notifications
          WHERE user_id=%s AND read_at IS NULL AND NOT silent GROUP BY category''',(actor.id,))
        counts = {r['category']:r['unread'] for r in await cur.fetchall()}
    return {'items':rows[:limit],'next_cursor':rows[limit-1]['id'] if len(rows)>limit else None,
            'snapshot_id':snapshot,'unread':sum(counts.values()),'unread_by_category':counts}

@router.post('/notifications/read-all')
async def read_all(body: ReadAll,actor: Account,response: Response):
    private(response)
    async with cursor() as cur:
        await cur.execute('''UPDATE review_notifications SET read_at=now() WHERE user_id=%s
          AND id<=%s AND read_at IS NULL AND (%s='all' OR category=%s)''',
          (actor.id,body.through_id,body.category,body.category))
        changed = cur.rowcount
    return {'updated':changed}

@router.post('/notifications/{nid}/read')
async def read_notice(nid: int,body: ReadState,actor: Account,response: Response):
    private(response)
    async with cursor() as cur:
        await cur.execute('''UPDATE review_notifications SET
          read_at=CASE WHEN %s THEN COALESCE(read_at,now()) ELSE NULL END,
          silent=CASE WHEN %s THEN silent ELSE false END WHERE id=%s AND user_id=%s RETURNING id''',
          (body.read,body.read,nid,actor.id))
        if not await cur.fetchone():raise HTTPException(404,'Notification not found')
    return {'read':body.read}

@router.get('/preferences')
async def preferences(actor: Account,response: Response):
    private(response)
    async with cursor() as cur:
        await cur.execute('SELECT in_app FROM inbox_preferences WHERE user_id=%s',(actor.id,))
        row=await cur.fetchone()
    return {'in_app':{**Preferences().model_dump(),**(row['in_app'] if row else {})},'push_available':False,'email_available':False}

@router.post('/preferences')
async def save_preferences(body: Preferences,actor: Account,response: Response):
    private(response)
    from psycopg.types.json import Jsonb
    async with cursor() as cur:
        await cur.execute('''INSERT INTO inbox_preferences(user_id,in_app) VALUES(%s,%s)
          ON CONFLICT(user_id) DO UPDATE SET in_app=EXCLUDED.in_app,updated_at=now()''',(actor.id,Jsonb(body.model_dump())))
    return {'in_app':body.model_dump()}

@router.get('/threads')
async def threads(actor: Account,response: Response,offset: int=Query(0,ge=0,le=100000),limit: int=Query(20,ge=1,le=50),selected: str|None=Query(None,max_length=100)):
    private(response)
    # Same membership, join-time and bilateral block rules as the desk chat.
    enabled()
    async with cursor() as cur:
        await cur.execute('''SELECT d.id,d.name,d.goal,
          latest.body AS last_message,latest.author,latest.created_at AS last_at,
          (SELECT count(*)::int FROM study_desk_messages x
           WHERE x.desk_id=d.id AND x.deleted_at IS NULL AND x.created_at>=m.joined_at
             AND x.author_id<>%s AND x.id>COALESCE(r.last_message_id,0) AND '''+VISIBLE+''') AS unread
          FROM study_desks d JOIN study_desk_members m ON m.desk_id=d.id AND m.user_id=%s AND m.left_at IS NULL
          LEFT JOIN inbox_desk_reads r ON r.desk_id=d.id AND r.user_id=m.user_id
          LEFT JOIN LATERAL(SELECT x.body,u.handle AS author,x.created_at FROM study_desk_messages x JOIN users u ON u.id=x.author_id
            WHERE x.desk_id=d.id AND x.deleted_at IS NULL AND x.created_at>=m.joined_at AND '''+VISIBLE+'''
            ORDER BY x.id DESC LIMIT 1) latest ON true
          WHERE d.closed_at IS NULL AND (%s::text IS NULL OR d.id=%s) ORDER BY latest.created_at DESC NULLS LAST,d.name,d.id LIMIT %s OFFSET %s''',
          (actor.id,actor.id,actor.id,actor.id,actor.id,actor.id,selected,selected,limit+1,offset))
        rows=await cur.fetchall()
        return {'items':rows[:limit],'next_offset':offset+limit if len(rows)>limit else None}

@router.post('/threads/{did}/read')
async def read_thread(did: str,body: ThreadRead,actor: Account,response: Response):
    private(response)
    enabled()
    async with cursor() as cur:
        membership=await member(cur,did,actor.id,lock=True)
        await cur.execute('''SELECT COALESCE(max(x.id),0) AS through_id FROM study_desk_messages x
          WHERE x.desk_id=%s AND x.id<=%s AND x.created_at>=%s AND x.deleted_at IS NULL AND '''+VISIBLE,
          (did,body.through_id,membership['joined_at'],actor.id,actor.id))
        through=(await cur.fetchone())['through_id']
        await cur.execute('''INSERT INTO inbox_desk_reads(user_id,desk_id,last_message_id) VALUES(%s,%s,%s)
          ON CONFLICT(user_id,desk_id) DO UPDATE SET last_message_id=GREATEST(inbox_desk_reads.last_message_id,EXCLUDED.last_message_id),updated_at=now()''',
          (actor.id,did,through))
    return {'through_id':through}

@router.get('/threads/{did}/messages')
async def messages(did: str,actor: Account,response: Response,before: int|None=Query(None,ge=1),limit: int=Query(30,ge=1,le=50)):
    private(response)
    return await desk_messages(did=did,user=actor.id,before=before,limit=limit)

@router.get('/unread')
async def unread_count(actor: Account,response: Response):
    private(response)
    from ..config import settings
    async with cursor() as cur:
        await cur.execute('SELECT count(*)::int AS n FROM review_notifications WHERE user_id=%s AND read_at IS NULL AND NOT silent',(actor.id,))
        notifications=(await cur.fetchone())['n']
        conversations=0
        if settings.study_desks_private_enabled:
            await cur.execute('''SELECT count(*)::int AS n FROM study_desks d
              JOIN study_desk_members m ON m.desk_id=d.id AND m.user_id=%s AND m.left_at IS NULL
              LEFT JOIN inbox_desk_reads r ON r.desk_id=d.id AND r.user_id=m.user_id
              WHERE d.closed_at IS NULL AND EXISTS(SELECT 1 FROM study_desk_messages x
                WHERE x.desk_id=d.id AND x.deleted_at IS NULL AND x.created_at>=m.joined_at
                AND x.author_id<>%s AND x.id>COALESCE(r.last_message_id,0) AND '''+VISIBLE+')',(actor.id,actor.id,actor.id,actor.id))
            conversations=(await cur.fetchone())['n']
    return {'unread':notifications+conversations,'notifications':notifications,'conversations':conversations}
