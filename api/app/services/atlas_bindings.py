"""Owner-curated, source-bound topic lenses over existing static Atlas chapters."""
import json
from pathlib import Path
from fastapi import HTTPException
from psycopg.types.json import Jsonb

CATALOG=json.loads((Path(__file__).resolve().parents[1]/'data/atlas-static-catalog.json').read_text())
CHAPTERS={c['id']:c for c in CATALOG['chapters']}
HASHES=Jsonb({c['id']:c['source_sha256'] for c in CATALOG['chapters']})
# Every reader uses this predicate: holds, registry retirement/version drift and
# changed static chapter contents disappear in both directions immediately.
LIVE="""b.live IS NOT NULL AND EXISTS(SELECT 1 FROM atlas_chapters ac JOIN atlas_chapter_versions av
 ON av.chapter_id=ac.id AND av.revision=ac.current_version WHERE ac.id=b.live->>'chapter_id'
 AND ac.status='published' AND av.body_hash=b.live->>'chapter_hash')
 AND EXISTS(SELECT 1 FROM review_taxonomy t JOIN review_taxonomy s ON s.id=t.parent_id
 WHERE t.id=b.live->>'topic_id' AND s.id=b.live->>'subject_id' AND t.level='topic' AND s.level='subject'
 AND t.active AND s.active AND t.version=b.live->>'topic_version' AND s.version=b.live->>'subject_version')"""


def catalog_chapter(cid,layer=None,event=None):
    chapter=CHAPTERS.get(cid)
    if not chapter:raise HTTPException(422,'Choose a current Atlas chapter')
    if layer and layer not in {x['id'] for x in chapter['layers']}:raise HTTPException(422,'Choose a layer in this chapter')
    if event and event not in {x['id'] for x in chapter['events']}:raise HTTPException(422,'Choose a timeline event in this chapter')
    return chapter


async def current_chapter(cur,cid,layer=None,event=None):
    from .atlas_studio import published
    try:row=await published(cur,cid)
    except HTTPException as e:
        if e.status_code==404:raise HTTPException(422,'Choose a current published Atlas chapter')
        raise
    chapter=row['body']
    if layer and layer not in {x['id'] for x in chapter['layers']}:raise HTTPException(422,'Choose a layer in this chapter')
    if event and event not in {x['id'] for x in chapter.get('events',[])}:raise HTTPException(422,'Choose a timeline event in this chapter')
    return chapter|{'source_sha256':row['body_hash']}


async def validate(cur,payload,*,fresh=False):
    chapter=await current_chapter(cur,payload['chapter_id'],payload.get('layer_id'),payload.get('event_id'))
    await cur.execute("SELECT t.version AS topic_version,s.version AS subject_version FROM review_taxonomy t JOIN review_taxonomy s ON s.id=t.parent_id WHERE t.id=%s AND s.id=%s AND t.level='topic' AND s.level='subject' AND t.active AND s.active",(payload['topic_id'],payload['subject_id']))
    row=await cur.fetchone()
    if not row:raise HTTPException(422,'Choose a current approved subject/topic path')
    current=payload|dict(row)|{'chapter_hash':chapter['source_sha256']}
    if not fresh and current!=payload:raise HTTPException(409,'Chapter or taxonomy changed. Save and review the binding again.')
    return current


async def save(cur,bid,version,payload,actor,reason):
    await cur.execute("SELECT pg_advisory_xact_lock(hashtextextended('atlas-bindings-v1',0))")
    await cur.execute('SELECT * FROM atlas_topic_bindings WHERE id=%s FOR UPDATE',(bid,));old=await cur.fetchone()
    if (old['version'] if old else 0)!=version:raise HTTPException(409,'This binding changed. Reload before saving.')
    payload=await validate(cur,payload,fresh=True)
    if not old:
        await cur.execute('SELECT count(*) AS n FROM atlas_topic_bindings')
        if (await cur.fetchone())['n']>=2000:raise HTTPException(409,'Atlas supports up to 2000 binding records')
        await cur.execute('INSERT INTO atlas_topic_bindings(id,draft) VALUES(%s,%s) RETURNING *',(bid,Jsonb(payload)))
    else:
        await cur.execute('UPDATE atlas_topic_bindings SET draft=%s,version=version+1,updated_at=clock_timestamp() WHERE id=%s RETURNING *',(Jsonb(payload),bid))
    row=await cur.fetchone()
    await audit(cur,row,actor,'save',payload,reason)
    return row


async def audit(cur,row,actor,action,payload,reason):
    await cur.execute('INSERT INTO atlas_binding_versions(binding_id,revision,action,actor_id,payload,reason) VALUES(%s,%s,%s,%s,%s,%s)',(row['id'],row['version'],action,actor,Jsonb(payload) if payload is not None else None,reason))


async def decide(cur,bid,version,action,actor,reason,revision=None):
    await cur.execute("SELECT pg_advisory_xact_lock(hashtextextended('atlas-bindings-v1',0))")
    await cur.execute('SELECT * FROM atlas_topic_bindings WHERE id=%s FOR UPDATE',(bid,));row=await cur.fetchone()
    if not row:raise HTTPException(404,'Atlas binding not found')
    if row['version']!=version:raise HTTPException(409,'This binding changed. Reload before deciding.')
    payload=row['draft']
    if action=='rollback':
        await cur.execute("SELECT payload FROM atlas_binding_versions WHERE binding_id=%s AND revision=%s AND action IN ('publish','rollback')",(bid,revision));old=await cur.fetchone()
        if not old:raise HTTPException(422,'Choose a previously published binding revision')
        payload=old['payload']
    if action=='hold':
        if row['live'] is None:raise HTTPException(409,'This binding is already held or unpublished')
        payload=row['live'];live=None
    else:
        live=await validate(cur,payload)
        await cur.execute('''SELECT id FROM atlas_topic_bindings WHERE id<>%s AND live IS NOT NULL
          AND live->>'chapter_id'=%s AND COALESCE(live->>'layer_id','')=%s
          AND COALESCE(live->>'event_id','')=%s AND live->>'subject_id'=%s AND live->>'topic_id'=%s''',
          (bid,live['chapter_id'],live.get('layer_id') or '',live.get('event_id') or '',live['subject_id'],live['topic_id']))
        if await cur.fetchone():raise HTTPException(409,'This chapter/topic view already has a published binding')
    await cur.execute('UPDATE atlas_topic_bindings SET live=%s,version=version+1,updated_at=clock_timestamp() WHERE id=%s RETURNING *',(Jsonb(live) if live else None,bid));row=await cur.fetchone()
    await audit(cur,row,actor,action,payload,reason)
    return row


def membership():
    return """EXISTS(SELECT 1 FROM atlas_topic_bindings b JOIN v_question_paths ap
     ON ap.subject_id=b.live->>'subject_id' AND ap.topic_id=b.live->>'topic_id'
     JOIN atlas_chapters ac ON ac.id=b.live->>'chapter_id' JOIN atlas_chapter_versions av ON av.chapter_id=ac.id AND av.revision=ac.current_version
     WHERE ap.question_id=v.id AND """+LIVE+""" AND b.live->>'chapter_id'=%(atlas_chapter)s
     AND (%(atlas_layer)s::text IS NULL OR b.live->>'layer_id'=%(atlas_layer)s))"""


async def reverse(cur,ids,user):
    if not ids:return {}
    await cur.execute('SELECT EXISTS(SELECT 1 FROM atlas_topic_bindings b WHERE '+LIVE+') AS available',{'atlas_hashes':HASHES})
    if not (await cur.fetchone())['available']:return {}
    from ..routers.learning import not_assessed
    await cur.execute("""SELECT DISTINCT q.id,b.live,av.body->>'title' AS atlas_title,av.body->>'subject' AS atlas_subject FROM canonical_questions q
     JOIN v_question_paths ap ON ap.question_id=q.id JOIN atlas_topic_bindings b
     ON ap.subject_id=b.live->>'subject_id' AND ap.topic_id=b.live->>'topic_id'
     JOIN atlas_chapters ac ON ac.id=b.live->>'chapter_id' JOIN atlas_chapter_versions av ON av.chapter_id=ac.id AND av.revision=ac.current_version
     WHERE q.id=ANY(%(ids)s) AND q.status='live' AND """+not_assessed()+" AND "+LIVE+" ORDER BY q.id,b.live",{'ids':ids,'user':user,'atlas_hashes':HASHES})
    result={}
    for row in await cur.fetchall():
        p=row['live'];link={k:p.get(k) for k in ('chapter_id','layer_id','event_id')}
        link['title']=row['atlas_title'];link['subject']=row['atlas_subject']
        links=result.setdefault(row['id'],[])
        if link not in links and len(links)<8:links.append(link)
    return result
