"""Read-only explanations for the existing transactional award writer."""
RULE_VERSION='learning-v1'

def level_bounds(xp):
    from math import isqrt
    level=max(1,isqrt(max(0,xp)//40))
    return {'level':level,'level_floor_xp':0 if level==1 else 40*level**2,'next_level_xp':40*(level+1)**2}

async def attempt_reward(cur,user,question,attempt,correct,source,context):
    await cur.execute('SELECT email IS NOT NULL AS account FROM users WHERE id=%s',(user,))
    account=(await cur.fetchone())['account']
    reason='guest' if not account else 'incorrect' if not correct else 'unofficial' if source not in ('official','key') else 'ineligible'
    await cur.execute('''SELECT c.attempt_id,l.id,l.xp,l.points,l.rule_version FROM reward_question_claims c
      JOIN reward_ledger l ON l.event_key='question:'||c.user_id||':'||c.canonical_id
      WHERE c.user_id=%s AND c.canonical_id=%s''',(user,question))
    receipt=await cur.fetchone()
    if receipt and receipt['attempt_id']==attempt:
        return {'status':'awarded','xp':receipt['xp'],'points':receipt['points'],'receipt_id':receipt['id'],'rule_version':receipt['rule_version']}
    if account and correct and source in ('official','key'):
        if receipt:reason='already_rewarded'
        elif context=='practice':
            await cur.execute("SELECT COALESCE(sum(xp),0)::int AS n FROM reward_ledger WHERE user_id=%s AND kind IN ('study','game') AND created_at>=(date_trunc('day',now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata')",(user,))
            if (await cur.fetchone())['n']>=300:reason='daily_cap'
    return {'status':reason,'xp':0,'points':0,'receipt_id':receipt['id'] if receipt else None,'rule_version':RULE_VERSION}
