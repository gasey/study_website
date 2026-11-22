"""Unscored map activity. Never writes attempts, mastery, queues, streaks or awards."""
from math import radians,sin,cos,asin,sqrt
from uuid import uuid4
from fastapi import HTTPException
from psycopg.types.json import Jsonb
MIN_SECONDS=3
from . import atlas_studio as studio,atlas_bindings as bindings


def drills(body):
    result=[]
    for layer in body['layers']:
        if layer['kind']!='vector' or not isinstance(layer['data'],dict):continue
        for f in layer['data']['features']:
            p=f.get('properties') or {}
            if f['geometry']['type']=='Point' and p.get('drillable') and f.get('id'):
                result.append({'id':'pin:'+layer['id']+':'+str(f['id']),'layer_id':layer['id'],'feature_id':str(f['id']),
                  'prompt':'Locate '+str(p.get(layer.get('labelKey','name')) or layer['name']),
                  'toleranceKm':p['toleranceKm'],'geometry':f['geometry']})
    for d in body.get('drills',[]):
        layer=next(l for l in body['layers'] if l['id']==d['layerId'])
        f=next(f for f in layer['data']['features'] if str(f.get('id'))==d['featureId'])
        result.append({'id':'custom:'+d['id'],'layer_id':d['layerId'],'feature_id':d['featureId'],
          'prompt':d['prompt'],'toleranceKm':d['toleranceKm'],'geometry':f['geometry']})
    return result


def distance(a,b):
    lon1,lat1,lon2,lat2=map(radians,[*a,*b]);h=sin((lat2-lat1)/2)**2+cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2
    return 6371*2*asin(sqrt(min(1,max(0,h))))


def geometry_distance(g,point):
    # Great-circle distance for pins. Lines use bounded local projection onto
    # each segment followed by spherical distance; suitable for illustrative maps.
    if g['type']=='Point':return distance(g['coordinates'],point)
    distances=[]
    for a,b in zip(g['coordinates'],g['coordinates'][1:]):
        scale=max(.01,cos(radians(point[1])));ax=(a[0]-point[0])*scale;ay=a[1]-point[1];bx=(b[0]-point[0])*scale;by=b[1]-point[1]
        dx,dy=bx-ax,by-ay;t=max(0,min(1,-(ax*dx+ay*dy)/(dx*dx+dy*dy))) if dx*dx+dy*dy else 0
        distances.append(distance([a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])],point))
    return min(distances)


async def source(cur,cid):
    # Same lock order as chapter publication, then account activity lock.
    await cur.execute('SELECT id FROM atlas_chapters WHERE id=%s FOR SHARE',(cid,))
    return await studio.published(cur,cid)


async def state(cur,user,cid):
    row=await studio.published(cur,cid);body=row['body'];available=drills(body)
    await cur.execute('SELECT viewed_layers FROM atlas_exploration WHERE user_id=%s AND chapter_id=%s AND body_hash=%s',(user,cid,row['body_hash']));seen=await cur.fetchone()
    layers=set(seen['viewed_layers'] if seen else [])
    await cur.execute('SELECT count(DISTINCT drill_id)::int AS n FROM atlas_drill_results WHERE user_id=%s AND chapter_id=%s AND body_hash=%s',(user,cid,row['body_hash']));n=(await cur.fetchone())['n']
    return {'chapter_id':cid,'body_hash':row['body_hash'],'viewed_layers':sorted(layers),'tried':n,'total_drills':len(available),
      'explored':set(l['id'] for l in body['layers'])<=layers and (not available or n>0),
      'drills':[{k:d[k] for k in ('id','prompt','layer_id')} for d in available]}


async def view(cur,user,cid,body_hash,layers):
    row=await source(cur,cid)
    if row['body_hash']!=body_hash:raise HTTPException(409,'Chapter changed. Reload before marking layers viewed')
    if not set(layers)<=set(l['id'] for l in row['body']['layers']):raise HTTPException(422,'Choose layers in this chapter')
    await cur.execute('''INSERT INTO atlas_exploration(user_id,chapter_id,body_hash,viewed_layers) VALUES(%s,%s,%s,%s)
      ON CONFLICT(user_id,chapter_id) DO UPDATE SET body_hash=EXCLUDED.body_hash,
       viewed_layers=ARRAY(SELECT DISTINCT unnest(CASE WHEN atlas_exploration.body_hash=EXCLUDED.body_hash THEN atlas_exploration.viewed_layers ELSE '{}'::text[] END||EXCLUDED.viewed_layers)),updated_at=clock_timestamp()''',(user,cid,body_hash,list(set(layers))))
    return await state(cur,user,cid)


async def start(cur,user,cid,drill_id,body_hash,key):
    row=await source(cur,cid)
    await cur.execute("SELECT pg_advisory_xact_lock(hashtextextended('atlas-activity:'||%s,0))",(user,))
    if row['body_hash']!=body_hash:raise HTTPException(409,'Chapter changed. Reload the drill list')
    await cur.execute('SELECT * FROM atlas_drill_presentations WHERE user_id=%s AND request_key=%s',(user,key));old=await cur.fetchone()
    if old:
        if old['chapter_id']!=cid or old['body_hash']!=body_hash or old['drill_id']!=drill_id:raise HTTPException(409,'This start request belongs to another drill')
        return safe(old,row['body'])
    drill=next((d for d in drills(row['body']) if d['id']==drill_id),None)
    if not drill:raise HTTPException(422,'Choose an authored drill')
    await cur.execute("SELECT count(*) AS n FROM atlas_drill_presentations WHERE user_id=%s AND created_at>clock_timestamp()-interval '1 day'",(user,))
    if (await cur.fetchone())['n']>=200:raise HTTPException(429,'Today’s map activity limit is reached. Ordinary practice remains available.')
    await cur.execute('''INSERT INTO atlas_drill_presentations(id,user_id,chapter_id,revision,body_hash,drill_id,request_key,snapshot)
      VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *''',(uuid4(),user,cid,row['revision'],body_hash,drill_id,key,Jsonb(drill)))
    return safe(await cur.fetchone(),row['body'])


def safe(row,body):
    return {'id':str(row['id']),'chapter_id':row['chapter_id'],'body_hash':row['body_hash'],
      'drill_id':row['drill_id'],'prompt':row['snapshot']['prompt'],'view':body['view'],'expires_at':row['expires_at'],
      'source':'map-activity','xp':0,'points':0}


async def answer(cur,user,pid,choice):
    await cur.execute('SELECT * FROM atlas_drill_presentations WHERE id=%s AND user_id=%s',(pid,user));shown=await cur.fetchone()
    if not shown:raise HTTPException(404,'Map drill not found')
    row=await source(cur,shown['chapter_id'])
    await cur.execute("SELECT pg_advisory_xact_lock(hashtextextended('atlas-activity:'||%s,0))",(user,))
    if row['body_hash']!=shown['body_hash']:raise HTTPException(409,'Chapter changed. Start a current drill')
    await cur.execute('SELECT * FROM atlas_drill_results WHERE presentation_id=%s',(pid,));old=await cur.fetchone()
    if old:
        if old['choice']!=choice:raise HTTPException(409,'This map activity already has another saved choice')
        return old['result']
    await cur.execute("SELECT clock_timestamp()>=%s+(%s*interval '1 second') AS timed,clock_timestamp()>%s AS expired",(shown['created_at'],MIN_SECONDS,shown['expires_at']));clock=await cur.fetchone()
    if clock['expired']:raise HTTPException(409,'This drill expired. Start another drill')
    if not clock['timed']:raise HTTPException(409,'Take a moment to study the map before recording your choice')
    snap=shown['snapshot'];km=geometry_distance(snap['geometry'],[choice['lng'],choice['lat']]);correct=km<=snap['toleranceKm']
    # Queue only binding identities, never copy real questions or answer metadata.
    if not correct:
        await cur.execute('''INSERT INTO atlas_practice_suggestions(user_id,binding_id,source_hash)
         SELECT %(user)s,b.id,b.live->>'chapter_hash' FROM atlas_topic_bindings b WHERE '''+bindings.LIVE+'''
         AND b.live->>'chapter_id'=%(cid)s AND (b.live->>'layer_id' IS NULL OR b.live->>'layer_id'=%(layer)s)
         ON CONFLICT(user_id,binding_id) DO UPDATE SET source_hash=EXCLUDED.source_hash,created_at=clock_timestamp()''',{'user':user,'cid':shown['chapter_id'],'layer':snap['layer_id']})
    result={'correct':correct,'distance_km':round(km,2),'tolerance_km':snap['toleranceKm'],'target':snap['geometry'],
      'message':'Within the authored tolerance.' if correct else 'Outside the authored tolerance. Try real questions from this map’s linked topics.',
      'source':'map-activity','xp':0,'points':0,'mastery_credit':False}
    await cur.execute('''INSERT INTO atlas_drill_results(presentation_id,user_id,chapter_id,body_hash,drill_id,correct,choice,result)
      VALUES(%s,%s,%s,%s,%s,%s,%s,%s)''',(pid,user,shown['chapter_id'],shown['body_hash'],shown['drill_id'],correct,Jsonb(choice),Jsonb(result)))
    return result


async def progress(cur,user):
    await cur.execute("""SELECT c.id,v.body,v.body_hash,e.viewed_layers,
     (SELECT count(DISTINCT drill_id)::int FROM atlas_drill_results r WHERE r.user_id=%(user)s
       AND r.chapter_id=c.id AND r.body_hash=v.body_hash) AS tried
     FROM atlas_chapters c JOIN atlas_chapter_versions v ON v.chapter_id=c.id AND v.revision=c.current_version
     JOIN atlas_exploration e ON e.user_id=%(user)s AND e.chapter_id=c.id AND e.body_hash=v.body_hash
     WHERE c.status='published' ORDER BY c.id LIMIT 500""",{'user':user})
    items=[]
    for r in await cur.fetchall():
        total=len(drills(r['body']))
        items.append({'chapter_id':r['id'],'body_hash':r['body_hash'],'viewed_layers':r['viewed_layers'],
          'tried':r['tried'],'total_drills':total,'explored':set(l['id'] for l in r['body']['layers'])<=set(r['viewed_layers']) and (not total or r['tried']>0)})
    return {'items':items}


async def suggestions(cur,user,exam=None):
    from ..exam_scope import question_scope
    from ..routers.learning import not_assessed
    scope='all' if exam else 'mizoram-recruitment'
    await cur.execute('''SELECT DISTINCT b.live->>'chapter_id' AS chapter_id,b.live->>'layer_id' AS layer_id,
      b.live->>'subject_id' AS subject_id,b.live->>'topic_id' AS topic_id,v.body->>'title' AS title
      FROM atlas_topic_bindings b JOIN atlas_chapters c ON c.id=b.live->>'chapter_id'
      JOIN atlas_chapter_versions v ON v.chapter_id=c.id AND v.revision=c.current_version
      WHERE '''+bindings.LIVE+''' AND (EXISTS(SELECT 1 FROM atlas_practice_suggestions s WHERE s.user_id=%(user)s
        AND s.binding_id=b.id AND s.source_hash=b.live->>'chapter_hash') OR EXISTS(
        SELECT 1 FROM user_topic_mastery m WHERE m.user_id=%(user)s AND m.subject_id=b.live->>'subject_id'
        AND m.topic=b.live->>'topic_id' AND m.state IN ('practicing','proficient')))
      AND EXISTS(SELECT 1 FROM v_scorable q JOIN v_question_paths p ON p.question_id=q.id
       AND p.subject_id=b.live->>'subject_id' AND p.topic_id=b.live->>'topic_id'
       WHERE '''+question_scope('q',scope)+' AND '+not_assessed('q')+'''
       AND (%(exam)s::text IS NULL OR EXISTS(SELECT 1 FROM appearances a JOIN collection_papers cp ON cp.paper_id=a.paper_id
         JOIN collections ec ON ec.id=cp.collection_id AND ec.live_version=cp.version AND ec.visibility='public'
         WHERE a.canonical_id=q.id AND ec.id=%(exam)s))) ORDER BY chapter_id,layer_id LIMIT 5''',{'user':user,'exam':exam['id'] if exam else None})
    from urllib.parse import urlencode
    return [dict(r)|{'url':'/atlas?'+urlencode({'chapter':r['chapter_id'],**({'layer':r['layer_id']} if r['layer_id'] else {})}),
      'practice_url':('/exams/'+exam['id'] if exam else '/bank')+'?'+urlencode({'subject_id':r['subject_id'],'topic_id':r['topic_id'],'pool':'scorable','view':'practice'})} for r in await cur.fetchall()]
