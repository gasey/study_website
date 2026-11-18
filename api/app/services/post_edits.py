"""Versioned own-post edits. Visibility is rechecked before every read and write."""
import hashlib,json
from fastapi import HTTPException
from psycopg import errors
from psycopg.types.json import Jsonb
from .community_policy import account_lock,posting_guard

async def target(cur,pid,user):
    from .study_posts import visible
    from ..routers.discussions import post_visible,access
    await cur.execute('SELECT kind,author_id FROM posts WHERE id=%s',(pid,));row=await cur.fetchone()
    if not row:raise HTTPException(404,'Post not found')
    post=await (visible(cur,pid,user) if row['kind'] in {'study','material-share'} else post_visible(cur,pid,user))
    if row['author_id']!=user:raise HTTPException(403,'Only the author can edit this post or read its revision history')
    return post

async def history(cur,pid,user,before=None):
    await target(cur,pid,user)
    await cur.execute('SELECT version,body,source_links,created_at FROM post_revisions WHERE post_id=%s AND (%s::int IS NULL OR version<%s) ORDER BY version DESC LIMIT 21',(pid,before,before))
    rows=await cur.fetchall()
    return {'items':rows[:20],'has_more':len(rows)>20}

async def edit(cur,pid,user,body,key):
    from ..routers.discussions import event,access
    from .study_posts import clean_body
    await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('discussion:'+user,))
    await account_lock(cur,user)
    post=await target(cur,pid,user)
    await cur.execute('SELECT * FROM posts WHERE id=%s FOR UPDATE',(pid,));post=await cur.fetchone()
    # A withdrawal/hide may have committed while the first visibility read waited.
    await target(cur,pid,user)
    if post['canonical_id']:await access(cur,post['canonical_id'],user,write=True)
    if post['kind'] in {'study','material-share'}:
        try:clean_body(body.body)
        except ValueError as e:raise HTTPException(422,str(e))
        if body.sources:raise HTTPException(422,'Study posts keep their original linked item; source URLs are for question discussions')
    payload=body.model_dump();digest=hashlib.sha256(json.dumps({'post_id':pid,**payload},sort_keys=True).encode()).hexdigest()
    await cur.execute('SELECT post_id,version,request_hash FROM post_revisions WHERE actor_id=%s AND request_key=%s',(user,key));prior=await cur.fetchone()
    if prior:
        if prior['post_id']!=pid or prior['request_hash']!=digest:raise HTTPException(409,'This request key belongs to a different edit')
        return {'id':pid,'content_version':prior['version'],'needs_approval':post['needs_approval'],'replayed':True}
    if post['edit_locked'] or post['accepted']:raise HTTPException(409,'This reply was accepted and its content is permanently locked')
    if post['content_version']!=body.expected_version:raise HTTPException(409,'This post changed. Reload it before editing')
    sources=[s.model_dump() for s in body.sources]
    if post['body']==body.body and post['source_links']==sources:raise HTTPException(422,'Make a change before saving')
    await cur.execute("SELECT 1 FROM abuse_reports WHERE post_id=%s AND status='open'",(pid,))
    if await cur.fetchone():raise HTTPException(409,'Resolve the open conduct report before editing this post')
    # Edits consume the existing shared post/reply budget; every edit is reviewed.
    await posting_guard(cur,user,reply=post['parent_id'] is not None)
    try:
        await cur.execute('SELECT community_edit_post(%s,%s,%s,%s,%s,%s,%s) AS version',(pid,user,body.expected_version,body.body,Jsonb(sources),key,digest))
    except errors.InsufficientPrivilege:raise HTTPException(503,'Post editing is temporarily unavailable')
    version=(await cur.fetchone())['version']
    await event(cur,post['canonical_id'],user,'edited',pid,{'version':version,'needs_approval':True})
    return {'id':pid,'content_version':version,'needs_approval':True,'replayed':False}
