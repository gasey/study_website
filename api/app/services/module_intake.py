"""Immutable module evidence integration with the normal contribution workflow."""
import hashlib,json,re,unicodedata
from fastapi import HTTPException
from psycopg.types.json import Jsonb

def normalize(v):return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',str(v or '')).casefold()).strip()
def identity(q):return normalize(q.get('question',q.get('text',''))),tuple(normalize(o) for o in q.get('options') or [])
def identity_sha(q):return hashlib.sha256(json.dumps(identity(q),sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def compare(a,b):return 'agree' if a is not None and a==b else 'conflict' if a is not None and b is not None else 'module_only' if a is not None else 'bank_only' if b is not None else 'neither'
async def validate_reference(cur,e,p,baseline):
    if e.kind!='reference':raise HTTPException(422,'Module records are reference evidence, not an official key')
    await cur.execute('SELECT i.*,r.manifest_sha256,r.module_url FROM module_audit_items i JOIN module_audit_runs r ON r.id=i.run_id WHERE i.id=%s',(e.module_item_id,));item=await cur.fetchone()
    if not item or item['manifest_sha256']!=e.module_run_sha256:raise HTTPException(422,'Module evidence reference or hash is invalid')
    if not p.canonical_id:
        if p.kind!='source_request' or item['match_status']!='unmatched':raise HTTPException(422,'Unlinked module records require a source request')
        return
    aid=baseline.get('record',{}).get('id')
    await cur.execute('SELECT 1 FROM module_audit_candidates WHERE item_id=%s AND appearance_id=%s AND canonical_id=%s',(item['id'],aid,p.canonical_id))
    if not await cur.fetchone():raise HTTPException(422,'Module evidence does not identify this question appearance')
    if identity(item['legacy'])!=identity(baseline['record']):raise HTTPException(409,'Question identity changed since module intake; reimport or review the source before linking this evidence')
async def link(cur,actor,p,cid,additional_items=()):
    for itemid in sorted({e.module_item_id for e in p.evidence if e.module_item_id}|set(additional_items)):
        await cur.execute('SELECT * FROM module_audit_triage WHERE item_id=%s FOR UPDATE',(itemid,));t=await cur.fetchone()
        if not t or t['state']=='dismissed':raise HTTPException(409,'Reopen the module intake record before linking a correction')
        await cur.execute('INSERT INTO module_audit_links(item_id,contribution_id,actor_id) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING RETURNING item_id',(itemid,cid,actor))
        if await cur.fetchone():
            await cur.execute("UPDATE module_audit_triage SET state='linked',version=version+1,updated_by=%s,updated_at=now() WHERE item_id=%s",(actor,itemid))
            await cur.execute("INSERT INTO module_audit_events(item_id,actor_id,action,detail) VALUES(%s,%s,'contribution_linked',%s)",(itemid,actor,Jsonb({'contribution_id':cid})))
