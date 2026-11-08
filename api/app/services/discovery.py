"""Answer-free discovery; only aggregate public signals are cached."""
import asyncio
import copy
import time
from datetime import date, datetime, timezone
from urllib.parse import quote
from fastapi import HTTPException
from .study_series import study_series_pool
from .review_policy import digest

COLLECTIONS=('udc','combined-prelims')
_cache={}
_lock=asyncio.Lock()

def clear_cache():
    _cache.clear()

async def members(cur,collection):
    clause="""WHERE v.status='live' AND NOT v.key_disputed
      AND COALESCE(v.source_defect,'') NOT IN ('duplicate-options','unresolved-source')
      AND EXISTS(SELECT 1 FROM appearances a JOIN collection_papers cp ON cp.paper_id=a.paper_id
        JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version
        WHERE a.canonical_id=v.id AND cp.collection_id=%(series_collection)s AND c.visibility='public')"""
    sql=study_series_pool('v_launch_practice',clause,members=True)
    await cur.execute('SELECT id,study_series_key FROM '+sql+' pool',{'series_collection':collection,'series_user':''})
    return await cur.fetchall()

async def ranking(cur,collection):
    # Key includes publication/moderation changes, including writes outside HTTP.
    await cur.execute("""SELECT (SELECT max(id) FROM sync_log WHERE finished_at IS NOT NULL) AS sync,
      (SELECT max(id) FROM mod_actions) AS moderation""")
    version=await cur.fetchone()
    key=(collection,digest(version))
    async with _lock:
        cached=_cache.get(key)
        if cached and cached[0]>time.monotonic():return copy.deepcopy(cached[1])
        rows=await members(cur,collection)
        groups={r['id']:digest(r['study_series_key']) for r in rows}
        await cur.execute("""SELECT a.canonical_id,a.user_id,'answer' AS kind FROM attempts a
          JOIN users u ON u.id=a.user_id AND u.email IS NOT NULL AND u.email NOT LIKE '%%.test' AND u.id NOT LIKE 'synthetic_%%' AND u.id<>'team'
          WHERE a.at>now()-interval '7 days' AND a.context='practice' AND a.canonical_id=ANY(%s)
          UNION SELECT p.canonical_id,p.author_id,'discussion' FROM posts p
          JOIN users u ON u.id=p.author_id AND u.email IS NOT NULL AND u.email NOT LIKE '%%.test' AND u.id NOT LIKE 'synthetic_%%' AND u.id<>'team'
          WHERE p.created_at>now()-interval '7 days' AND NOT p.hidden AND NOT p.needs_approval AND NOT p.before_fix
            AND p.canonical_id=ANY(%s)""",(list(groups),list(groups)))
        signals={}
        for r in await cur.fetchall():
            g=groups[r['canonical_id']];s=signals.setdefault(g,{'answer':set(),'discussion':set()})
            s[r['kind']].add(r['user_id'])
        values={g:{'participants':len(s['answer']|s['discussion']),'score':2*len(s['answer'])+len(s['discussion'])} for g,s in signals.items()}
        data={'groups':groups,'scores':values,'generated_at':datetime.now(timezone.utc).isoformat()}
        if len(_cache)>8:_cache.clear()
        _cache[key]=(time.monotonic()+900,copy.deepcopy(data))
        return data

async def fact_current(cur,rid):
    if rid is None:return True
    from ..routers.current_affairs import Proposal,source_fingerprint
    await cur.execute("""SELECT r.payload FROM current_affairs_revisions r
      JOIN current_affairs_entities e ON e.live_revision=r.id WHERE r.id=%s AND r.state='published'""",(rid,))
    r=await cur.fetchone()
    if not r:return False
    p=Proposal(**r['payload'])
    if any(f.review_due<date.today() for f in p.facts):return False
    await cur.execute('SELECT appearance_id,source_fingerprint FROM current_affairs_links WHERE revision_id=%s',(rid,))
    fingerprints={x['appearance_id']:x['source_fingerprint'] for x in await cur.fetchall()}
    for link in p.links:
        try:
            if fingerprints.get(link.appearance_id)!=await source_fingerprint(cur,link):return False
        except HTTPException:return False
    return True

async def hot_picks(cur,collection):
    await cur.execute("""SELECT d.*,t.label AS topic,t.level AS topic_level FROM discovery_picks d
      JOIN review_taxonomy t ON t.id=d.taxonomy_id AND t.active
      JOIN collections c ON c.id=d.collection_id AND c.visibility='public'
      WHERE d.collection_id=%s AND d.state='published' AND d.expires_at>now()
      ORDER BY d.published_at DESC,d.id""",(collection,))
    rows=await cur.fetchall()
    return [r for r in rows if await fact_current(cur,r['fact_revision_id'])]

async def cards(cur,collection,limit):
    rank=await ranking(cur,collection)
    # Recheck current eligibility/source and collection membership on every read.
    current=await members(cur,collection)
    candidates={r['id']:digest(r['study_series_key']) for r in current}
    await cur.execute("""SELECT q.id,a.question,a.id AS appearance_id,a.paper_id,a.qnum,p.exam_name,p.year
      FROM canonical_questions q JOIN LATERAL (
        SELECT a.* FROM appearances a JOIN collection_papers cp ON cp.paper_id=a.paper_id
        JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version
        WHERE a.canonical_id=q.id AND cp.collection_id=%s AND c.visibility='public'
        ORDER BY a.is_primary DESC,a.id LIMIT 1
      ) a ON true JOIN papers p ON p.id=a.paper_id
      WHERE q.id=ANY(%s) ORDER BY p.year DESC NULLS LAST,q.id""",(collection,list(candidates)))
    groups={};popular=[]
    for r in await cur.fetchall():
        g=candidates[r['id']]
        if g in groups:continue
        r['url']='/bank/'+r['id']+'?exam='+collection+'&paper='+quote(r['paper_id'],safe='')
        r['score']=0;r['participants']=0
        if rank['groups'].get(r['id'])==g:r.update(rank['scores'].get(g,{}))
        groups[g]=r
        if r['participants']>=5:popular.append(r)
    popular.sort(key=lambda r:(-r['score'],r['id']))
    # Only explicit, previously inspected source lists provide editorial fallback.
    await cur.execute('SELECT canonical_ids FROM topic_trail_packs WHERE collection_id=%s AND active AND canonical_ids IS NOT NULL ORDER BY id',(collection,))
    approved={qid for p in await cur.fetchall() for qid in p['canonical_ids']}
    used={r['id'] for r in popular[:limit]}
    recommended=[r for r in groups.values() if r['id'] in approved and r['id'] not in used][:limit]
    hot=[{'id':p['id'],'title':p['title'],'why_now':p['why_now'],'topic':p['topic'],
      'sources':p['sources'],'expires_at':p['expires_at'],'published_at':p['published_at'],
      'url':'/exams/'+collection+'?view=browse&'+('subtopic_id' if p['topic_level']=='subtopic' else 'topic_id')+'='+p['taxonomy_id']+'#exam-question-browser'} for p in await hot_picks(cur,collection)]
    return {'popular':popular[:limit],'recommended':recommended,'hot':hot[:limit],
      'generated_at':rank['generated_at'],'window_days':7}
