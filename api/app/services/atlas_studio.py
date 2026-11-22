"""Atlas adapter for the reviewed-content lifecycle: drafts, immutable versions, CAS.

Existing site seeds have explicit legacy attribution. Owner publication does not
claim answer verification, independent review, mastery or economic credit.
"""
import hashlib,json,math,re
from fastapi import HTTPException
from psycopg.types.json import Jsonb


def invalid(field,message):
    raise HTTPException(422,[{'loc':['body','chapter',*field.split('.')],'msg':field+': '+message,'type':'value_error'}])


def validate(body):
    if not isinstance(body,dict):invalid('chapter','Use a chapter object')
    try: size=len(json.dumps(body,allow_nan=False).encode())
    except (ValueError,TypeError):invalid('chapter','Use finite JSON values')
    if size>1500000:invalid('chapter','Chapter exceeds 1.5 MB')
    def text(value,path,maximum=12000,required=False):
        if not isinstance(value,str) or len(value)>maximum or (required and not value.strip()):invalid(path,'Add text within the field limit')
    def identity(value,path):
        if not isinstance(value,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}',value):invalid(path,'Use a stable ID of 1–100 letters, digits, dashes or underscores')
    def point(value,path,geo=False):
        if not isinstance(value,list) or len(value)!=2:invalid(path,'A map position needs two coordinates')
        lat,lng=(value[1],value[0]) if geo else value
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (lat,lng)) or not -90<=lat<=90 or not -180<=lng<=180:invalid(path,'Position is outside the world bounds')
    def view(value,path):
        if not isinstance(value,dict):invalid(path,'Capture a map view')
        point(value.get('center'),path+'.center');z=value.get('zoom')
        if isinstance(z,bool) or not isinstance(z,(int,float)) or not math.isfinite(z) or not 2<=z<=18:invalid(path+'.zoom','Zoom must be between 2 and 18')
    if 'worldExtent' in body and not isinstance(body['worldExtent'],bool):invalid('worldExtent','Use the world-extent toggle')
    if 'tags' in body and (not isinstance(body['tags'],list) or len(body['tags'])>50 or any(not isinstance(t,str) or len(t)>100 for t in body['tags'])):invalid('tags','Use at most 50 short tags')
    for key in ('basemap',):
        if key in body:text(body[key],key,100)
    if 'theme' in body:
        if not isinstance(body['theme'],dict):invalid('theme','Use theme properties')
        for k,v in body['theme'].items():text(v,'theme.'+k,2000)
    identity(body.get('id'),'id')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,99}',body['id']):invalid('id','Chapter ID needs lowercase letters, digits and dashes')
    if body.get('subject') not in ('geography','history','polity'):invalid('subject','Choose an Atlas subject')
    for k,limit in [('title',180),('summary',3000),('focus',6000),('unit',100)]:text(body.get(k,''),k,limit,k in ('title','summary'))
    view(body.get('view'),'view')
    layers=body.get('layers')
    if not isinstance(layers,list) or not 1<=len(layers)<=80:invalid('layers','Add between 1 and 80 layers')
    ids=set();feature_ids=set();vertices=0
    def geometry(g,path):
        nonlocal vertices
        if not isinstance(g,dict):invalid(path,'Choose a supported map geometry')
        t=g.get('type');c=g.get('coordinates')
        if t=='Point':points=[c]
        elif t=='LineString':
            if not isinstance(c,list) or len(c)<2:invalid(path,'Lines need at least two vertices')
            points=c
        elif t=='Polygon':
            if not isinstance(c,list) or not c:invalid(path,'Areas need a closed outline')
            points=[]
            for ring in c:
                if not isinstance(ring,list) or len(ring)<4 or ring[0]!=ring[-1]:invalid(path,'Areas need at least three vertices and a closed outline')
                points+=ring
        elif t in ('MultiPoint','MultiLineString','MultiPolygon'):
            if not isinstance(c,list) or not c:invalid(path,'Add a nonempty geometry')
            for part in c:geometry({'type':{'MultiPoint':'Point','MultiLineString':'LineString','MultiPolygon':'Polygon'}[t],'coordinates':part},path)
            return
        else:invalid(path,'Use point, line or polygon GeoJSON')
        vertices+=len(points)
        if vertices>30000:invalid('layers','Chapter exceeds 30,000 vertices')
        for p in points:point(p,path,True)
    for i,l in enumerate(layers):
        p=f'layers.{i}'
        if not isinstance(l,dict):invalid(p,'Use a layer object')
        identity(l.get('id'),p+'.id')
        if l['id'] in ids:invalid(p+'.id','Layer IDs must be unique')
        if 'defaultOn' in l and not isinstance(l['defaultOn'],bool):invalid(p+'.defaultOn','Use the default visibility toggle')
        if 'labelKey' in l:text(l['labelKey'],p+'.labelKey',100,True)
        ids.add(l['id']);text(l.get('name'),p+'.name',180,True);text(l.get('description',''),p+'.description',5000)
        if l.get('kind')!='vector':invalid(p+'.kind','Use an inline vector layer in this editor')
        data=l.get('data')
        if not isinstance(data,dict) or data.get('type')!='FeatureCollection' or not isinstance(data.get('features'),list) or len(data['features'])>1500:invalid(p+'.data','Use a FeatureCollection of at most 1500 features')
        for j,f in enumerate(data['features']):
            fp=p+f'.data.features.{j}'
            if not isinstance(f,dict) or f.get('type')!='Feature':invalid(fp,'Use GeoJSON features')
            geometry(f.get('geometry'),fp+'.geometry')
            props=f.get('properties')
            if props is not None and not isinstance(props,dict):invalid(fp+'.properties','Use named feature properties')
            if len(json.dumps(props or {}))>12000:invalid(fp+'.properties','Feature properties are too long')
        style=l.get('style',{})
        if not isinstance(style,dict):invalid(p+'.style','Use layer styling controls')
        for k in ('color','fillColor'):
            if k in style and (not isinstance(style[k],str) or not re.fullmatch(r'#[0-9a-fA-F]{3,8}',style[k])):invalid(p+'.style.'+k,'Choose a palette colour')
        if 'dashArray' in style:text(style['dashArray'],p+'.style.dashArray',80)
        if 'pattern' in style and style['pattern'] not in ('dots','hatch','wave','cross'):invalid(p+'.style.pattern','Choose a supported pattern')
        for k in ('shadow','flow','glow'):
            if k in style and not isinstance(style[k],bool):invalid(p+'.style.'+k,'Use a style toggle')
        for k,low,high in [('weight',0,15),('fillOpacity',0,1),('markerRadius',1,30)]:
            if k in style and (isinstance(style[k],bool) or not isinstance(style[k],(int,float)) or not math.isfinite(style[k]) or not low<=style[k]<=high):invalid(p+'.style.'+k,'Styling value is out of range')
    authored=body.get('drills',[])
    if not isinstance(authored,list) or len(authored)>100:invalid('drills','Use at most 100 custom prompts')
    targets={};drill_count=0
    for i,l in enumerate(layers):
        seen_features=set()
        for j,f in enumerate(l['data']['features']):
            props=f.get('properties') or {};fid=f.get('id');p=f'layers.{i}.data.features.{j}'
            if fid is not None:
                if not isinstance(fid,(str,int)) or isinstance(fid,bool):invalid(p+'.id','Use a stable feature ID')
                if str(fid) in seen_features:invalid(p+'.id','Feature IDs must be unique in a layer')
                seen_features.add(str(fid));targets[(l['id'],str(fid))]=f
            if 'drillable' in props and not isinstance(props['drillable'],bool):invalid(p+'.properties.drillable','Use the drillable toggle')
            if props.get('drillable'):
                if not isinstance(fid,str):invalid(p+'.id','Drillable pins need a stable string ID')
                identity(fid,p+'.id')
                if f['geometry']['type']!='Point':invalid(p,'Automatic drills need a point feature')
                tolerance=props.get('toleranceKm')
                if isinstance(tolerance,bool) or not isinstance(tolerance,(int,float)) or not 0<tolerance<=1000:invalid(p+'.properties.toleranceKm','Tolerance must be positive and at most 1000 km')
                drill_count+=1
    seen_drills=set()
    for i,d in enumerate(authored):
        p=f'drills.{i}'
        if not isinstance(d,dict):invalid(p,'Use a custom map prompt')
        identity(d.get('id'),p+'.id');text(d.get('prompt'),p+'.prompt',500,True)
        if d['id'] in seen_drills:invalid(p+'.id','Custom drill IDs must be unique')
        seen_drills.add(d['id']);identity(d.get('layerId'),p+'.layerId');identity(d.get('featureId'),p+'.featureId');f=targets.get((d['layerId'],d['featureId']))
        if not f or f['geometry']['type'] not in ('Point','LineString'):invalid(p+'.featureId','Choose an existing pin or line')
        if f['geometry']['type']=='LineString' and len(f['geometry']['coordinates'])>1000:invalid(p+'.featureId','Drill lines support at most 1000 vertices')
        tol=d.get('toleranceKm')
        if isinstance(tol,bool) or not isinstance(tol,(int,float)) or not 0<tol<=1000:invalid(p+'.toleranceKm','Tolerance must be positive and at most 1000 km')
    if drill_count+len(authored)>300:invalid('drills','A chapter supports up to 300 authored drills')
    facts=body.get('facts')
    if not isinstance(facts,list) or len(facts)>200:invalid('facts','Use at most 200 facts')
    seen=set()
    for i,f in enumerate(facts):
        p=f'facts.{i}'
        if not isinstance(f,dict):invalid(p,'Use a fact object')
        identity(f.get('id'),p+'.id');text(f.get('text'),p+'.text',12000,True)
        if f['id'] in seen:invalid(p+'.id','Fact IDs must be unique')
        seen.add(f['id'])
        if f.get('linkedLayerId') and f['linkedLayerId'] not in ids:invalid(p+'.linkedLayerId','Choose an existing layer')
    events=body.get('events',[])
    if not isinstance(events,list) or len(events)>150:invalid('events','Use at most 150 events')
    seen=set()
    for i,e in enumerate(events):
        p=f'events.{i}'
        if not isinstance(e,dict):invalid(p,'Use an event object')
        identity(e.get('id'),p+'.id');text(e.get('label'),p+'.label',180,True);text(e.get('date'),p+'.date',40,True);text(e.get('description',''),p+'.description',6000)
        if e['id'] in seen:invalid(p+'.id','Event IDs must be unique')
        seen.add(e['id'])
        for key in ('showLayers','hideLayers'):
            if not isinstance(e.get(key,[]),list) or any(x not in ids for x in e.get(key,[])):invalid(p+'.'+key,'Events can only reference existing layers')
        if e.get('view'):view(e['view'],p+'.view')
    # Preserve legacy quiz data as content, but no drill activity/reward pipeline.
    if not isinstance(body.get('quiz'),list) or len(body['quiz'])>100:invalid('quiz','Use at most 100 legacy quiz items')
    for i,q in enumerate(body['quiz']):
        p=f'quiz.{i}'
        if not isinstance(q,dict):invalid(p,'Use a quiz item')
        identity(q.get('id'),p+'.id');text(q.get('question'),p+'.question',3000,True)
        if q.get('type')=='map_click':
            a=q.get('answer',{})
            if not isinstance(a,dict):invalid(p+'.answer','Use a map answer')
            point([a.get('lat'),a.get('lng')],p+'.answer')
            tol=a.get('toleranceKm')
            if isinstance(tol,bool) or not isinstance(tol,(int,float)) or not math.isfinite(tol) or not 0<tol<=20000:invalid(p+'.answer.toleranceKm','Tolerance must be positive and at most 20000 km')
        elif q.get('type')=='mcq':
            opts=q.get('options');a=q.get('answerIndex')
            if not isinstance(opts,list) or not 2<=len(opts)<=8 or any(not isinstance(x,str) or len(x)>3000 for x in opts) or isinstance(a,bool) or not isinstance(a,int) or not 0<=a<len(opts):invalid(p,'Choose valid MCQ options and answer')
        else:invalid(p+'.type','Choose a legacy map-click or MCQ item')
    from .atlas_context import validate_metadata
    validate_metadata(body,invalid)
    return body


def digest(body):return hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


async def catalog(cur):
    await cur.execute("SELECT c.id,c.lock_version,v.body,v.body_hash FROM atlas_chapters c JOIN atlas_chapter_versions v ON v.chapter_id=c.id AND v.revision=c.current_version WHERE c.status='published' ORDER BY c.position,c.id")
    return [{'id':r['id'],'title':r['body']['title'],'subject':r['body']['subject'],'unit':r['body'].get('unit'),'layers':[{'id':l['id'],'name':l['name']} for l in r['body']['layers']],'events':[{'id':e['id'],'label':e['label']} for e in r['body'].get('events',[])],'source_sha256':r['body_hash']} for r in await cur.fetchall()]


async def published(cur,cid):
    await cur.execute("SELECT v.body,v.body_hash,v.revision,v.attribution FROM atlas_chapters c JOIN atlas_chapter_versions v ON v.chapter_id=c.id AND v.revision=c.current_version WHERE c.id=%s AND c.status='published'",(cid,));row=await cur.fetchone()
    if not row:raise HTTPException(404,'Atlas chapter is unavailable')
    return row


async def event(cur,cid,actor,action,revision=None,detail=None):
    await cur.execute('INSERT INTO atlas_chapter_events(chapter_id,actor_id,action,revision,detail) VALUES(%s,%s,%s,%s,%s)',(cid,actor,action,revision,Jsonb(detail or {})))


async def workspace(cur,cid,user):
    await cur.execute('SELECT * FROM atlas_chapters WHERE id=%s',(cid,));row=await cur.fetchone()
    if not row:raise HTTPException(404,'Atlas chapter not found')
    await cur.execute('SELECT * FROM atlas_drafts WHERE chapter_id=%s AND user_id=%s',(cid,user));draft=await cur.fetchone()
    await cur.execute('SELECT revision,body_hash,authored_by,attribution,note,created_at FROM atlas_chapter_versions WHERE chapter_id=%s ORDER BY revision DESC LIMIT 100',(cid,));versions=await cur.fetchall()
    await cur.execute('SELECT action,actor_id,revision,detail,created_at FROM atlas_chapter_events WHERE chapter_id=%s ORDER BY id DESC LIMIT 100',(cid,));events=await cur.fetchall()
    if draft:body=draft['body']
    elif row['current_version']:
        await cur.execute('SELECT body FROM atlas_chapter_versions WHERE chapter_id=%s AND revision=%s',(cid,row['current_version']));body=(await cur.fetchone())['body']
    else:body=None
    return row|{'body':body,'draft_version':draft['version'] if draft else 0,'draft_base':draft['base_version'] if draft else row['lock_version'],'versions':versions,'events':events}


async def save(cur,cid,user,expected,base,body):
    validate(body)
    if body['id']!=cid:invalid('id','Chapter identity cannot change')
    await cur.execute("SELECT pg_advisory_xact_lock(hashtextextended('atlas-chapters-v1',0))")
    await cur.execute('SELECT * FROM atlas_chapters WHERE id=%s FOR UPDATE',(cid,));chapter=await cur.fetchone()
    if not chapter:
        if expected or base:raise HTTPException(409,'Chapter changed. Reopen the workspace')
        await cur.execute('SELECT count(*) AS n FROM atlas_chapters')
        if (await cur.fetchone())['n']>=500:raise HTTPException(409,'Atlas supports up to 500 chapters')
        await cur.execute('INSERT INTO atlas_chapters(id) VALUES(%s) RETURNING *',(cid,));chapter=await cur.fetchone();base=chapter['lock_version']
    if chapter['lock_version']!=base:raise HTTPException(409,'Published chapter changed. Reload and reconcile your draft')
    await cur.execute('SELECT version FROM atlas_drafts WHERE chapter_id=%s AND user_id=%s FOR UPDATE',(cid,user));old=await cur.fetchone()
    if (old['version'] if old else 0)!=expected:raise HTTPException(409,'Your draft changed in another tab. Reload before saving')
    await cur.execute('INSERT INTO atlas_drafts(chapter_id,user_id,body,base_version) VALUES(%s,%s,%s,%s) ON CONFLICT(chapter_id,user_id) DO UPDATE SET body=EXCLUDED.body,version=atlas_drafts.version+1,updated_at=clock_timestamp(),base_version=EXCLUDED.base_version',(cid,user,Jsonb(body),base))
    await event(cur,cid,user,'save',detail={'draft_version':expected+1,'body_hash':digest(body)})
    return await workspace(cur,cid,user)


async def decide(cur,cid,user,version,action,note,draft_version=None,revision=None,preview_hash=None):
    await cur.execute("SELECT pg_advisory_xact_lock(hashtextextended('atlas-chapters-v1',0))")
    await cur.execute('SELECT * FROM atlas_chapters WHERE id=%s FOR UPDATE',(cid,));row=await cur.fetchone()
    if not row:raise HTTPException(404,'Atlas chapter not found')
    if row['lock_version']!=version:raise HTTPException(409,'Chapter changed. Reload before deciding')
    if action=='hold':
        if row['status']!='published':raise HTTPException(409,'Chapter is not published')
        target=row['current_version'];status='held'
    elif action=='rollback':
        await cur.execute('SELECT body FROM atlas_chapter_versions WHERE chapter_id=%s AND revision=%s',(cid,revision));target_body=await cur.fetchone()
        if not target_body:raise HTTPException(422,'Choose an existing published revision')
        validate(target_body['body'])
        from .atlas_context import check_references
        await check_references(cur,target_body['body'])
        target=revision;status='published'
    else:
        await cur.execute('SELECT * FROM atlas_drafts WHERE chapter_id=%s AND user_id=%s FOR UPDATE',(cid,user));draft=await cur.fetchone()
        if not draft or draft['version']!=draft_version or draft['base_version']!=version:raise HTTPException(409,'Save and preview your current draft before publishing')
        body=validate(draft['body']);body_hash=digest(body)
        from .atlas_context import check_references
        await check_references(cur,body)
        if preview_hash!=body_hash:raise HTTPException(409,'Preview this exact saved draft before publishing')
        await cur.execute("SELECT 1 FROM atlas_chapter_events WHERE chapter_id=%s AND actor_id=%s AND action='preview' AND detail->>'body_hash'=%s AND (detail->>'draft_version')::int=%s AND (detail->>'base_version')::int=%s",(cid,user,body_hash,draft_version,version))
        if not await cur.fetchone():raise HTTPException(409,'Preview the saved draft first')
        await cur.execute('SELECT COALESCE(max(revision),0)+1 AS n FROM atlas_chapter_versions WHERE chapter_id=%s',(cid,));target=(await cur.fetchone())['n']
        await cur.execute("INSERT INTO atlas_chapter_versions(chapter_id,revision,body,body_hash,authored_by,attribution,note) VALUES(%s,%s,%s,%s,%s,'owner',%s)",(cid,target,Jsonb(body),body_hash,user,note));status='published'
    await cur.execute('UPDATE atlas_chapters SET current_version=%s,status=%s,lock_version=lock_version+1,updated_at=clock_timestamp() WHERE id=%s',(target,status,cid))
    # Keep every author's draft. The publishing author's copy advances its base.
    if action=='publish':await cur.execute('UPDATE atlas_drafts SET base_version=%s WHERE chapter_id=%s AND user_id=%s',(version+1,cid,user))
    await event(cur,cid,user,action,target,{'reason':note})
    return await workspace(cur,cid,user)
