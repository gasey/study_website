"""Owner-issued next-subscription discounts; no provider, access or reward writes."""
import hashlib,json,logging,secrets
from uuid import uuid4
from fastapi import HTTPException
from psycopg.types.json import Jsonb
from . import bulk_rate_release

async def lock(cur):
    await cur.execute("SELECT pg_advisory_xact_lock(hashtextextended('billing-bulk-rates',0))")

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,default=str).encode()).hexdigest()

async def amount(cur,user):
    await cur.execute('SELECT amount_paise FROM billing_account_rates WHERE user_id=%s',(user,));row=await cur.fetchone()
    return row['amount_paise'] if row else 10000

async def account_lock(cur,user):
    # Same checkout lock as manual pricing. Bulk/login hooks never hold an auth
    # transaction while acquiring the shared bulk lock.
    await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('billing-checkout:'+user,))
    await cur.execute('SELECT id,email,email_verified_at FROM users WHERE id=%s AND email IS NOT NULL AND closed_at IS NULL FOR SHARE',(user,))
    row=await cur.fetchone()
    if not row:raise HTTPException(404,'Account is no longer available')
    return row

async def assign(cur,user,actor,source,reference):
    before=await amount(cur,user)
    await cur.execute('''INSERT INTO billing_account_rates(user_id,amount_paise,updated_by) VALUES(%s,5000,%s)
      ON CONFLICT(user_id) DO UPDATE SET amount_paise=5000,updated_by=excluded.updated_by,updated_at=now()''',(user,actor))
    await cur.execute("INSERT INTO account_security_events(user_id,action,detail) VALUES(%s,'bulk_billing_rate_applied',%s)",
      (user,Jsonb({'actor_id':actor,'source':source,'reference':reference,'before_paise':before,'amount_paise':5000})))

async def apply_email(cur,user):
    if not bulk_rate_release.enabled():return False
    await lock(cur);account=await account_lock(cur,user)
    if not account['email_verified_at']:return False
    email=account['email'].strip().lower()
    await cur.execute('SELECT * FROM billing_rate_allowlist WHERE email_normalized=%s FOR UPDATE',(email,));row=await cur.fetchone()
    if not row or row['revoked_at'] or row['applied_user_id']:return False
    await assign(cur,user,row['added_by'],'email_allowlist',email)
    await cur.execute('UPDATE billing_rate_allowlist SET applied_user_id=%s,applied_at=now(),version=version+1 WHERE email_normalized=%s',(user,email))
    return True

async def after_identity_commit(user):
    """Best-effort optional pricing, outside sign-in/verification row locks.

    An unavailable optional assignment must not prevent login. Retained pending
    entries retry at a later successful login; no GET performs hidden writes.
    """
    from ..db import cursor
    try:
        async with cursor() as cur:await apply_email(cur,user)
    except Exception as exc:
        logging.getLogger(__name__).warning('Optional bulk rate deferred (%s)',type(exc).__name__)

async def preview(cur,emails,note):
    await cur.execute('SELECT email_normalized,version,revoked_at,applied_user_id FROM billing_rate_allowlist WHERE email_normalized=ANY(%s) ORDER BY email_normalized',(emails,));entries=await cur.fetchall()
    await cur.execute('''SELECT u.id,lower(u.email) AS email,u.email_verified_at IS NOT NULL AS verified,
      COALESCE(r.amount_paise,10000) AS amount_paise FROM users u LEFT JOIN billing_account_rates r ON r.user_id=u.id
      WHERE lower(u.email)=ANY(%s) AND u.closed_at IS NULL ORDER BY u.id''',(emails,));accounts=await cur.fetchall()
    return {'preview_hash':digest({'emails':emails,'note':note,'entries':entries,'accounts':accounts}),
      'total':len(emails),'already_listed':len(entries),'verified_accounts':sum(a['verified'] for a in accounts),
      'pending_verification_or_signup':len(emails)-sum(a['verified'] for a in accounts)}

async def add_emails(cur,actor,emails,note,key,expected):
    bulk_rate_release.require_writes();await lock(cur)
    fingerprint=digest({'emails':emails,'note':note,'expected':expected})
    await cur.execute('SELECT request_hash,result FROM billing_rate_batches WHERE actor_id=%s AND request_key=%s',(actor,key));old=await cur.fetchone()
    if old:
        if old['request_hash']!=fingerprint:raise HTTPException(409,'This batch request was already used for a different list')
        return old['result']
    await cur.execute('SELECT id FROM users WHERE lower(email)=ANY(%s) AND closed_at IS NULL ORDER BY id',(emails,));accounts=await cur.fetchall()
    for row in accounts:await account_lock(cur,row['id'])
    if (await preview(cur,emails,note))['preview_hash']!=expected:raise HTTPException(409,'The list or account prices changed. Preview this batch again.')
    added=0
    for email in emails:
        await cur.execute('''INSERT INTO billing_rate_allowlist(email_normalized,added_by,note) VALUES(%s,%s,%s)
          ON CONFLICT DO NOTHING RETURNING email_normalized''',(email,actor,note));added+=bool(await cur.fetchone())
    applied=0
    for row in accounts:applied+=await apply_email(cur,row['id'])
    result={'batch_id':uuid4().hex,'added':added,'already_listed':len(emails)-added,'applied':applied}
    await cur.execute('INSERT INTO billing_rate_batches(id,actor_id,request_key,request_hash,result) VALUES(%s,%s,%s,%s,%s)',(result['batch_id'],actor,key,fingerprint,Jsonb(result)))
    await cur.execute("INSERT INTO account_security_events(user_id,action,detail) VALUES(%s,'owner_bulk_rate_batch',%s)",(actor,Jsonb(result)))
    return result

async def list_admin(cur,query=''):
    pattern='%'+query+'%'
    await cur.execute('SELECT * FROM billing_rate_allowlist WHERE email_normalized ILIKE %s OR note ILIKE %s ORDER BY created_at DESC,email_normalized LIMIT 101',(pattern,pattern));rows=await cur.fetchall()
    await cur.execute('SELECT * FROM billing_rate_codes WHERE code ILIKE %s OR note ILIKE %s ORDER BY created_at DESC,code LIMIT 51',(pattern,pattern));codes=await cur.fetchall()
    return {'enabled':bulk_rate_release.enabled(),'emails':rows[:100],'emails_has_more':len(rows)>100,'codes':codes[:50],'codes_has_more':len(codes)>50}

async def email_state(cur,actor,email,version,revoked):
    bulk_rate_release.require_writes();await lock(cur)
    await cur.execute('SELECT * FROM billing_rate_allowlist WHERE email_normalized=%s FOR UPDATE',(email,));row=await cur.fetchone()
    if not row:raise HTTPException(404,'Email entry not found')
    if row['version']!=version:raise HTTPException(409,'This email entry changed. Reload before saving.')
    await cur.execute('UPDATE billing_rate_allowlist SET revoked_at=CASE WHEN %s THEN now() ELSE NULL END,version=version+1 WHERE email_normalized=%s',(revoked,email))
    await cur.execute("INSERT INTO account_security_events(user_id,action,detail) VALUES(%s,'owner_bulk_email_state',%s)",(actor,Jsonb({'email':email,'revoked':revoked,'previous_version':version})))
    return {'saved':True}

async def create_code(cur,actor,note,uses,days,key):
    bulk_rate_release.require_writes();await lock(cur);fingerprint=digest({'note':note,'uses':uses,'days':days})
    await cur.execute('SELECT * FROM billing_rate_codes WHERE created_by=%s AND request_key=%s',(actor,key));old=await cur.fetchone()
    if old:
        if old['request_hash']!=fingerprint:raise HTTPException(409,'This request already created a different group code')
        return old
    code=secrets.token_hex(12).upper()
    await cur.execute('''INSERT INTO billing_rate_codes(code,created_by,note,max_uses,expires_at,request_key,request_hash)
      VALUES(%s,%s,%s,%s,now()+make_interval(days=>%s),%s,%s) RETURNING *''',(code,actor,note,uses,days,key,fingerprint));row=await cur.fetchone()
    await cur.execute("INSERT INTO account_security_events(user_id,action,detail) VALUES(%s,'owner_bulk_code_created',%s)",(actor,Jsonb({'code':code,'max_uses':uses,'days':days})))
    return row

async def revoke_code(cur,actor,code,version):
    bulk_rate_release.require_writes();await lock(cur)
    await cur.execute('UPDATE billing_rate_codes SET revoked_at=COALESCE(revoked_at,now()),version=version+1 WHERE code=%s AND version=%s RETURNING code',(code,version))
    if not await cur.fetchone():raise HTTPException(409,'This group code changed or is missing. Reload before revoking.')
    await cur.execute("INSERT INTO account_security_events(user_id,action,detail) VALUES(%s,'owner_bulk_code_revoked',%s)",(actor,Jsonb({'code':code,'previous_version':version})))
    return {'saved':True}

async def redeem(cur,user,code,expected):
    bulk_rate_release.require_writes();await lock(cur);await account_lock(cur,user)
    await cur.execute('SELECT 1 FROM billing_rate_redemptions WHERE code=%s AND user_id=%s',(code,user))
    if await cur.fetchone():return {'saved':False,'already_redeemed':True,'amount_paise':await amount(cur,user)}
    await cur.execute('SELECT * FROM billing_rate_codes WHERE code=%s AND revoked_at IS NULL AND expires_at>now() AND uses<max_uses FOR UPDATE',(code,));row=await cur.fetchone()
    if not row:raise HTTPException(404,'This group code is unavailable, expired or fully claimed')
    if await amount(cur,user)!=expected:raise HTTPException(409,'Your account price changed. Reload billing before claiming.')
    await cur.execute('INSERT INTO billing_rate_redemptions(code,user_id) VALUES(%s,%s)',(code,user))
    await assign(cur,user,row['created_by'],'group_code',code)
    return {'saved':True,'already_redeemed':False,'amount_paise':5000}

async def claim_receipts(cur,code,after=''):
    """Owner audit, including revoked/expired codes and anonymous closed accounts."""
    await cur.execute('SELECT 1 FROM billing_rate_codes WHERE code=%s',(code,))
    if not await cur.fetchone():raise HTTPException(404,'Group code not found')
    await cur.execute('''SELECT r.user_id,r.amount_paise,r.created_at,u.email,u.handle,
      u.email_verified_at IS NOT NULL AS email_verified,u.closed_at IS NOT NULL AS closed
      FROM billing_rate_redemptions r JOIN users u ON u.id=r.user_id
      WHERE r.code=%s AND r.user_id>%s ORDER BY r.user_id LIMIT 51''',(code,after))
    rows=await cur.fetchall()
    return {'items':rows[:50],'next_cursor':rows[49]['user_id'] if len(rows)>50 else None}
