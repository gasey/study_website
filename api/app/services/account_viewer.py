"""Explicit owner support reads; no answer, desk, credential or block identities."""
from fastapi import HTTPException
from . import community_policy, learning_habit, mastery


async def search(cur, query):
    # Email is exact; handles are literal prefixes. Wildcards are never supplied
    # by the caller, and an empty query cannot enumerate the account directory.
    query=query.strip().lower()
    if len(query)<3:raise HTTPException(422,'Enter at least three characters')
    prefix=query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%'
    await cur.execute('''SELECT id,email,handle FROM users WHERE email IS NOT NULL
      AND (lower(email)=%s OR lower(handle) LIKE %s)
      ORDER BY (lower(email)=%s) DESC,lower(handle),id LIMIT 21''',(query,prefix,query))
    rows=await cur.fetchall()
    return {'items':rows[:20],'more':len(rows)>20}


async def snapshot(cur,user):
    await cur.execute('''SELECT id,email,handle,role,created_at,email_verified_at,
      EXISTS(SELECT 1 FROM account_mfa WHERE user_id=u.id AND enabled_at IS NOT NULL) AS mfa_enabled,
      (SELECT count(*) FROM auth_sessions WHERE user_id=u.id AND revoked_at IS NULL AND expires_at>now()) AS web_sessions,
      (SELECT count(*) FROM mobile_sessions WHERE user_id=u.id AND revoked_at IS NULL AND expires_at>now()
        AND EXISTS(SELECT 1 FROM auth_sessions s WHERE s.token_hash=mobile_sessions.parent_session_hash AND s.revoked_at IS NULL AND s.expires_at>now())) AS mobile_sessions,
      greatest((SELECT max(created_at) FROM auth_sessions WHERE user_id=u.id),
        (SELECT max(created_at) FROM mobile_sessions WHERE user_id=u.id),
        (SELECT max(at) FROM attempts WHERE user_id=u.id),
        (SELECT max(at) FROM vocab_attempts WHERE user_id=u.id),
        (SELECT max(created_at) FROM account_security_events WHERE user_id=u.id AND action IN
          ('password_changed','password_recovered','sessions_revoked','guest_progress_saved','handle_changed','session_activity_retained'))) AS last_activity_at
      FROM users u WHERE id=%s AND email IS NOT NULL''',(user,))
    account=await cur.fetchone()
    if not account:raise HTTPException(404,'Registered account not found')
    await cur.execute('SELECT role,subject_id FROM review_grants WHERE user_id=%s AND revoked_at IS NULL ORDER BY role,subject_id NULLS FIRST',(user,))
    account['roles']=await cur.fetchall()
    # Identical billing status precedence and entitlement function. A recorded
    # discount does not grant access; future receipts are shown as scheduled.
    await cur.execute('''SELECT account_has_pro(id) AS has_pro,
      CASE WHEN EXISTS(SELECT 1 FROM reward_redemptions WHERE user_id=u.id AND starts_at<=now() AND ends_at>now()) THEN 'rewarded'
        WHEN EXISTS(SELECT 1 FROM billing_access_grants WHERE user_id=u.id AND starts_at<=now() AND ends_at>now()) THEN 'granted'
        WHEN NOT account_has_pro(id) THEN 'free' ELSE plan_status END AS status,
      COALESCE((SELECT amount_paise FROM billing_account_rates WHERE user_id=u.id),10000) AS amount_paise,
      trial_ends_at,plan_ends_at,razorpay_subscription_id AS subscription_reference
      FROM users u WHERE id=%s''',(user,))
    access=await cur.fetchone()
    for table,key,columns in [('billing_access_grants','grants','days,starts_at,ends_at'),
                              ('reward_redemptions','redemptions','catalog_id,points,starts_at,ends_at')]:
        await cur.execute('SELECT '+columns+',starts_at<=now() AS active FROM '+table+' WHERE user_id=%s AND ends_at>now() ORDER BY starts_at,id LIMIT 51',(user,))
        rows=await cur.fetchall();access[key]=rows[:50];access[key+'_more']=len(rows)>50
    await cur.execute('SELECT count(*) AS attempts FROM attempts WHERE user_id=%s',(user,));study=await cur.fetchone()
    await cur.execute("SELECT count(*) AS verified_correct FROM ("+mastery.VERIFIED_ACTIVITY+") e WHERE outcome='correct'",{'user':user})
    study.update(await cur.fetchone());study['streak']=await learning_habit.streak(cur,user)
    await cur.execute('SELECT state,count(*) AS topics FROM user_topic_mastery WHERE user_id=%s GROUP BY state ORDER BY state',(user,));study['mastery']=await cur.fetchall()
    await cur.execute('''SELECT c.id,c.title,b.is_primary FROM user_exam_bookmarks b JOIN collections c ON c.id=b.collection_id
      WHERE b.user_id=%s ORDER BY b.is_primary DESC,b.created_at,c.id LIMIT 51''',(user,))
    exams=await cur.fetchall();study['exams']=exams[:50];study['exams_more']=len(exams)>50
    await cur.execute('SELECT COALESCE(sum(points),0) AS points,COALESCE(sum(xp),0) AS xp FROM reward_ledger WHERE user_id=%s',(user,));economy=await cur.fetchone()
    # Event keys and free-text notes can identify individual study items. The
    # support ledger deliberately shows only type, amount and receipt time.
    await cur.execute('SELECT id,kind,xp,points,created_at FROM reward_ledger WHERE user_id=%s ORDER BY created_at DESC,id DESC LIMIT 20',(user,));economy['ledger']=await cur.fetchall()
    await cur.execute('''SELECT count(*) AS cap_days FROM reward_daily_counters WHERE user_id=%s
      AND day BETWEEN (now() AT TIME ZONE 'Asia/Kolkata')::date-29 AND (now() AT TIME ZONE 'Asia/Kolkata')::date
      AND (xp>=300 OR points>=25)''',(user,));economy.update(await cur.fetchone())
    await cur.execute('''SELECT count(*) FILTER(WHERE parent_id IS NULL) AS posts,
      count(*) FILTER(WHERE parent_id IS NOT NULL) AS replies,
      COALESCE(sum('''+community_policy.HELPFUL_COUNT+''') FILTER(WHERE NOT hidden AND NOT before_fix AND NOT needs_approval),0) AS helpful_received
      FROM posts p WHERE author_id=%s''',(user,));community=await cur.fetchone()
    await cur.execute('''SELECT
      (SELECT count(*) FROM creator_blocks WHERE user_id=%(user)s) AS blocks_given,
      (SELECT count(*) FROM creator_blocks WHERE blocked_id=%(user)s) AS blocks_received,
      (SELECT count(*) FROM abuse_reports r JOIN posts p ON p.id=r.post_id WHERE p.author_id=%(user)s AND r.status='open') AS post_reports,
      (SELECT count(*) FROM material_reports r JOIN materials m ON m.id=r.material_id WHERE m.author_id=%(user)s AND r.state='open') AS material_reports,
      (SELECT count(*) FROM creator_reports WHERE creator_id=%(user)s AND state='open') AS profile_reports''',{'user':user})
    community.update(await cur.fetchone());policy=await community_policy.policy(cur,user)
    community.update({key:policy[key] for key in ('display_tier','needs_approval','can_create','sanctioned','weighted_helpful')})
    await cur.execute('SELECT now() AS observed_at');observed=await cur.fetchone()
    return {**observed,'read_only':True,'account':account,'access':access,'study':study,'economy':economy,'community':community}
