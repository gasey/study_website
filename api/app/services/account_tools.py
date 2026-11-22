"""Owned data portability and account tombstones. Immutable history stays intact."""
import json
import secrets
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from psycopg import sql

# Explicit fields only: never export credentials, answer keys, scoring snapshots,
# other desk members' documents, moderator notes or authentication bearer tokens.
EXPORTS = {
 'audience':('account_audience','category,version,declared_at','user_id','user_id'),
 'privacy_requests':('privacy_requests','id,kind,state,version,created_at,updated_at','user_id','created_at,id'),
 'referral_invitation':('referral_codes','code,enabled,version,created_at','user_id','user_id'),
 'referral_signup':('referral_claims','created_at','referred_id','referred_id'),
 'referral_result':('referral_decisions','state,decided_at','referred_id','referred_id'),
 'extra_access':('billing_access_grants','days,starts_at,ends_at,source','user_id','id'),
 'review_digest_preferences':('review_digest_preferences','enabled,version,updated_at','user_id','user_id'),
 'review_digest_history':('review_digest_outbox','day,state,sent_at,attempts','user_id','day'),
 'atlas_activity':('atlas_drill_results','chapter_id,body_hash,drill_id,correct,choice,at','user_id','at,presentation_id'),
 'atlas_exploration':('atlas_exploration','chapter_id,body_hash,viewed_layers,updated_at','user_id','chapter_id'),
 'billing_price':('billing_account_rates','amount_paise,updated_at','user_id','user_id'),
 'billing_group_claims':('billing_rate_redemptions','code,amount_paise,created_at','user_id','created_at,code'),
 'attempts':('attempts','id,canonical_id,paper_id,chosen_text,correct,context,at','user_id','id'),
 'progress':('user_activity_daily','collection_key,section_key,subject_key,subject_label,day,answered,correct,last_active_at','user_id','day,collection_key,section_key,subject_key'),
 'mastery':('user_topic_mastery','subject_id,topic,state,distinct_attempted,distinct_correct_latest,last_verified_activity_at,proficient_at,mastered_at','user_id','subject_id,topic'),
 'review_schedule':('review_items','item_type,item_id,box,due_on,last_result,updated_at','user_id','item_type,item_id'),
 'posts':('posts','id,canonical_id,kind,parent_id,body,hidden,created_at','author_id','id'),
 'calendar':('calendar_entries','id,date,title,note,kind,recurrence,collection_id,desk_id,version','user_id','date,id'),
 'saved_exams':('user_exam_bookmarks','collection_id,is_primary,created_at','user_id','collection_id'),
 'focus_subjects':('user_focus_subjects','subject_id,position','user_id','position'),
 'wallet_history':('reward_ledger','id,kind,xp,points,note,created_at','user_id','id'),
 'avatar_items':('user_avatar_items','item_id,level_at_claim,created_at','user_id','item_id'),
 'private_desk':('personal_desks','document,version,updated_at','user_id','user_id'),
 'desk_notes':('study_desk_items','id,desk_id,kind,title,body,question_id,created_at,updated_at,deleted_at','author_id','id'),
}


def encoded(value):
    return json.dumps(jsonable_encoder(value),ensure_ascii=False,separators=(',',':'))


async def export(cur,user):
    """A single read-only snapshot, with bounded server-side cursor batches."""
    await cur.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
    await cur.execute('SELECT clock_timestamp() AS exported_at')
    stamp=(await cur.fetchone())['exported_at']
    await cur.execute('SELECT id,handle,name,email,created_at,avatar FROM users WHERE id=%s',(user,))
    account=await cur.fetchone()
    yield '{"format_version":1,"assessment_note":"Records for questions in an active assessment are omitted until it ends. No answer keys or scoring snapshots are included.","exported_at":'+encoded(stamp)+',"account":'+encoded(account)
    for section,(table,fields,owner,order) in EXPORTS.items():
        yield ','+encoded(section)+':['
        query=sql.SQL('SELECT {} FROM {} WHERE {}=%s ORDER BY {}').format(
            sql.SQL(fields),sql.Identifier(table),sql.Identifier(owner),sql.SQL(order))
        # Named cursors avoid buffering an entire attempt/post history in memory.
        async with cur.connection.cursor(name='account_export_'+section) as stream:
            if section in ('attempts','posts','desk_notes','review_schedule'):
                from ..routers.learning import not_assessed
                canonical='question_id' if section=='desk_notes' else 'canonical_id'
                guard=not_assessed('held').replace('%(user)s','%s')
                query=sql.SQL('SELECT {} FROM {} x WHERE {}=%s AND NOT EXISTS(SELECT 1 FROM canonical_questions held WHERE held.id=x.{} AND NOT ({})) ORDER BY {}').format(sql.SQL(fields),sql.Identifier(table),sql.Identifier(owner),sql.Identifier(canonical),sql.SQL(guard),sql.SQL(order))
                await stream.execute(query,(user,user,user))
            else:await stream.execute(query,(user,))
            first=True
            while rows:=await stream.fetchmany(200):
                for row in rows:
                    if section=='private_desk':
                        from .desk_notes import document
                        row['document']=await document(cur,user,row['document'])
                    yield ('' if first else ',')+encoded(row);first=False
        yield ']'
    yield '}'


async def blockers(cur,user):
    reasons=[]
    await cur.execute('SELECT role,razorpay_subscription_id FROM users WHERE id=%s',(user,));row=await cur.fetchone()
    await cur.execute('SELECT 1 FROM review_grants WHERE user_id=%s AND revoked_at IS NULL LIMIT 1',(user,))
    if await cur.fetchone() or row['role']=='staff':reasons.append('Resolve staff access with the site owner before closing this account.')
    await cur.execute('SELECT 1 FROM study_desks WHERE owner_id=%s AND closed_at IS NULL LIMIT 1',(user,))
    if await cur.fetchone():reasons.append('Close your shared desks or transfer ownership in Study desk first.')
    await cur.execute("SELECT razorpay_subscription_id,status FROM billing_subscriptions WHERE user_id=%s",(user,))
    subscriptions=await cur.fetchall();terminal={'cancelled','completed','expired'}
    if any(s['status'] not in terminal for s in subscriptions) or (row['razorpay_subscription_id'] and not any(s['razorpay_subscription_id']==row['razorpay_subscription_id'] and s['status'] in terminal for s in subscriptions)):
        reasons.append('Cancel recurring billing in Plan & billing and wait for confirmed cancellation before closing this account.')
    return reasons


async def close(cur,user,version,mfa_verified=False):
    from .v5_release import require_writes
    require_writes()
    from .account_identity import lock_email_ownership
    await cur.execute('SELECT email FROM users WHERE id=%s',(user,));email_row=await cur.fetchone()
    if email_row and email_row['email']:
        await lock_email_ownership(cur,email_row['email'])
    from .audience import learning_processing_lock
    await learning_processing_lock(cur,user,restricting=True)
    # Match graph -> billing -> rewards -> user ordering of existing mutations.
    await cur.execute("SELECT pg_advisory_xact_lock(hashtextextended('creator-graph-v1',0))")
    await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('billing-checkout:'+user,))
    await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('rewards:'+user,))
    await cur.execute('SELECT identity_version,closed_at,email,email_verified_at,handle,name,avatar FROM users WHERE id=%s FOR UPDATE',(user,));row=await cur.fetchone()
    if row['closed_at']:raise HTTPException(409,'This account is already closed.')
    if row['identity_version']!=version:raise HTTPException(409,'Your profile changed. Reload before closing your account.')
    await cur.execute('SELECT enabled_at FROM account_mfa WHERE user_id=%s',(user,));factor=await cur.fetchone()
    if factor and factor['enabled_at'] and not mfa_verified:raise HTTPException(403,'Verify your authenticator in Account security before closing your account.')
    reasons=await blockers(cur,user)
    if reasons:raise HTTPException(409,' '.join(reasons))
    # Reopening is available only to accounts with an address verified before
    # closure. Keep the minimal identity envelope encrypted for the selected
    # grace period; the keyed email digest reserves that address without storing
    # it in searchable plaintext.
    if row['email'] and row['email_verified_at']:
        from . import mfa
        from .account_identity import closure_email_hash
        email_hash=closure_email_hash(row['email'])
        if not email_hash:raise HTTPException(503,'Secure account reopening is unavailable. Try again later or contact support.')
        envelope=json.dumps({'email':row['email'],'handle':row['handle'],'name':row['name'],'avatar':row['avatar']},ensure_ascii=False,separators=(',',':'))
        await cur.execute('DELETE FROM account_closure_recovery WHERE email_hash=%s AND expires_at<=clock_timestamp()',(email_hash,))
        await cur.execute('''INSERT INTO account_closure_recovery(user_id,email_hash,identity_cipher,expires_at)
          VALUES(%s,%s,%s,clock_timestamp()+interval '30 days')''',(user,email_hash,mfa.encrypt(user,envelope)))
    await cur.execute('UPDATE auth_sessions SET revoked_at=clock_timestamp() WHERE user_id=%s AND revoked_at IS NULL',(user,))
    await cur.execute('UPDATE mobile_sessions SET revoked_at=clock_timestamp() WHERE user_id=%s AND revoked_at IS NULL',(user,))
    await cur.execute('SELECT subject FROM google_identities WHERE user_id=%s',(user,));google=await cur.fetchone()
    await cur.execute('DELETE FROM google_auth_flows WHERE link_user_id=%s OR subject=%s',(user,google['subject'] if google else None))
    await cur.execute('DELETE FROM google_identities WHERE user_id=%s',(user,))
    await cur.execute('UPDATE account_email_tokens SET consumed_at=COALESCE(consumed_at,now()) WHERE user_id=%s',(user,))
    # Pending encrypted email links must not survive closure or remain deliverable.
    await cur.execute('DELETE FROM account_mail_outbox WHERE user_id=%s AND sent_at IS NULL',(user,))
    await cur.execute('DELETE FROM review_digest_outbox WHERE user_id=%s',(user,))
    await cur.execute('DELETE FROM review_digest_preferences WHERE user_id=%s',(user,))
    await cur.execute('UPDATE referral_codes SET enabled=false,version=version+1 WHERE user_id=%s AND enabled',(user,))
    await cur.execute('UPDATE account_mfa SET secret_cipher=NULL,pending_cipher=NULL,pending_until=NULL,enabled_at=NULL,last_counter=-1 WHERE user_id=%s',(user,))
    await cur.execute('DELETE FROM mfa_recovery_codes WHERE user_id=%s',(user,))
    await cur.execute('DELETE FROM calendar_entries WHERE user_id=%s',(user,))
    await cur.execute('UPDATE calendar_feed_tokens SET token_hash=NULL,revoked_at=clock_timestamp(),version=version+1 WHERE user_id=%s',(user,))
    await cur.execute('DELETE FROM personal_desks WHERE user_id=%s',(user,))
    await cur.execute("UPDATE creator_profiles SET public=false,bio='',bio_hidden=true,bio_needs_approval=false,bio_version=bio_version+1 WHERE user_id=%s",(user,))
    await cur.execute('DELETE FROM creator_follows WHERE follower_id=%s OR creator_id=%s',(user,user))
    await cur.execute('UPDATE reward_profiles SET board_public=false WHERE user_id=%s',(user,))
    await cur.execute("UPDATE study_desk_members SET left_at=COALESCE(left_at,now()),sharing='{}'::jsonb WHERE user_id=%s",(user,))
    await cur.execute("UPDATE study_desk_invites SET state='cancelled' WHERE state='pending' AND (sender_id=%s OR recipient_id=%s)",(user,user))
    await cur.execute("UPDATE users SET closed_at=clock_timestamp(),email=NULL,email_verified_at=NULL,password_hash=NULL,name=NULL,avatar=NULL,avatar_version=avatar_version+1,identity_version=identity_version+1,handle=%s,contribution_public=false WHERE id=%s RETURNING closed_at",('deleted-'+secrets.token_hex(16),user))
    closed_at=(await cur.fetchone())['closed_at']
    if row['email'] and row['email_verified_at']:
        await cur.execute("UPDATE account_closure_recovery SET expires_at=%s+interval '30 days' WHERE user_id=%s",(closed_at,user))
    await cur.execute("INSERT INTO account_security_events(user_id,action) VALUES(%s,'account_closed')",(user,))
    return {'closed':True}
