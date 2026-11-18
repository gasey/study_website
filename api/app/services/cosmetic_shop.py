"""Own-once points spend; serializes with every other wallet spending path."""
from fastapi import HTTPException
from psycopg.types.json import Jsonb
from . import avatars


async def purchase(cur,user,item_id,catalog_sha256,price_points):
    from .v5_release import require_writes
    require_writes()
    item=next((i for i in avatars.CATALOG if i['id']==item_id),None)
    if not item or not item.get('price_points'):raise HTTPException(422,'This item cannot be bought')
    await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('rewards:'+user,))
    row=await avatars.account(cur,user,lock=True)
    event_key=f'cosmetic:{user}:{item_id}'
    await cur.execute('SELECT id,points FROM reward_ledger WHERE user_id=%s AND event_key=%s',(user,event_key))
    receipt=await cur.fetchone()
    await cur.execute('SELECT 1 FROM user_avatar_items WHERE user_id=%s AND item_id=%s',(user,item_id))
    owned=await cur.fetchone()
    if receipt:
        if not owned or receipt['points']!=-price_points:raise HTTPException(409,'Purchase receipt differs. Reload your inventory.')
        return {'owned':True,'replayed':True,'points_spent':0,'original_points_spent':-receipt['points'],'ledger_id':receipt['id']}
    if owned:raise HTTPException(409,'This item is already owned; no points were spent')
    if not item.get('active',True):raise HTTPException(409,'This item is not currently offered')
    if catalog_sha256!=avatars.CATALOG_SHA256 or price_points!=item['price_points']:
        raise HTTPException(409,'The catalog changed. Reload before buying.')
    await cur.execute('SELECT COALESCE(sum(points),0)::int AS balance FROM reward_ledger WHERE user_id=%s',(user,))
    balance=(await cur.fetchone())['balance']
    if balance<price_points:raise HTTPException(409,'Not enough reward points')
    await cur.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note) VALUES(%s,%s,'redemption',0,%s,%s) RETURNING id",
                      (user,event_key,-price_points,'Cosmetic: '+item['label']))
    ledger_id=(await cur.fetchone())['id']
    await cur.execute('INSERT INTO user_avatar_items(user_id,item_id,level_at_claim) VALUES(%s,%s,%s)',(user,item_id,row['level']))
    await cur.execute('UPDATE users SET avatar_version=avatar_version+1 WHERE id=%s RETURNING avatar_version',(user,))
    version=(await cur.fetchone())['avatar_version']
    await cur.execute("INSERT INTO avatar_events(user_id,action,version,detail) VALUES(%s,'purchased',%s,%s)",
                      (user,version,Jsonb({'item_id':item_id,'points':price_points,'ledger_id':ledger_id,'catalog_sha256':catalog_sha256})))
    return {'owned':True,'replayed':False,'points_spent':price_points,'ledger_id':ledger_id,'balance':balance-price_points}


async def diagnostics(cur):
    """Read-only receipt/ownership reconciliation, independent of current prices."""
    valid="""e.user_id=l.user_id AND e.action='purchased' AND e.detail->>'ledger_id'=l.id::text
      AND l.event_key='cosmetic:'||e.user_id||':'||(e.detail->>'item_id')
      AND l.kind='redemption' AND l.xp=0 AND l.points<0
      AND e.detail->'points'=to_jsonb(-l.points)
      AND EXISTS(SELECT 1 FROM user_avatar_items i WHERE i.user_id=e.user_id AND i.item_id=e.detail->>'item_id')"""
    await cur.execute('''SELECT
      (SELECT count(*) FROM reward_ledger l WHERE l.event_key LIKE 'cosmetic:%%' AND NOT EXISTS
        (SELECT 1 FROM avatar_events e WHERE '''+valid+'''))::int AS cosmetic_ledger_mismatches,
      (SELECT count(*) FROM avatar_events e WHERE e.action='purchased' AND NOT EXISTS
        (SELECT 1 FROM reward_ledger l WHERE '''+valid+'''))::int AS cosmetic_audit_mismatches,
      (SELECT count(*) FROM (SELECT user_id,detail->>'item_id' FROM avatar_events WHERE action='purchased'
        GROUP BY user_id,detail->>'item_id' HAVING count(*)>1) d)::int AS duplicate_cosmetic_purchases''')
    return await cur.fetchone()
