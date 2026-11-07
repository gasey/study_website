"""Shared cookie identity. Device IDs are preferences, never ownership proof."""
import hashlib
import secrets
from fastapi import HTTPException, Request, Response
from psycopg.types.json import Jsonb
from ..db import cursor
from ..config import settings

GUEST_COOKIE = 'ism_guest'

def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()

def csrf_token(token):
    return digest('bank-review:' + token)

async def account_session(request):
    token = request.cookies.get('ism_session')
    if not token:
        return None
    async with cursor() as cur:
        await cur.execute('''SELECT s.user_id,s.expires_at,s.public_id,
          s.created_at>now()-interval '15 minutes' AS recent,
          s.mfa_verified_at>now()-interval '15 minutes' AS mfa_verified
          FROM auth_sessions s JOIN users u ON u.id=s.user_id
          WHERE token_hash=%s AND revoked_at IS NULL AND expires_at>now() AND u.email IS NOT NULL''', (digest(token),))
        return await cur.fetchone()

async def guest_identity(request, response, create=True):
    token = request.cookies.get(GUEST_COOKIE, '')
    if token:
        async with cursor() as cur:
            await cur.execute('''SELECT user_id FROM guest_credentials WHERE token_hash=%s
              AND expires_at>now() AND adopted_by IS NULL''', (digest(token),))
            row = await cur.fetchone()
        if row:
            return row['user_id']
    if not create:
        return None
    token = secrets.token_urlsafe(32)
    uid = 'guest_' + secrets.token_hex(16)
    async with cursor() as cur:
        await cur.execute("INSERT INTO users(id,handle,role) VALUES(%s,%s,'learner')", (uid, 'guest-' + uid[6:22]))
        await cur.execute('INSERT INTO guest_credentials(token_hash,user_id) VALUES(%s,%s)', (digest(token), uid))
    response.set_cookie(GUEST_COOKIE,token,max_age=180*86400,httponly=True,
                        secure=settings.public_origin.startswith('https://'),samesite='lax',path='/')
    return uid

async def transfer_guest(request, account):
    """Transfer only proven practice records. No publication, wallet or role transfer."""
    token = request.cookies.get(GUEST_COOKIE, '')
    if not token:
        return {'transferred':False,'counts':{}}
    async with cursor() as cur:
        await cur.execute('SELECT * FROM guest_credentials WHERE token_hash=%s AND expires_at>now() FOR UPDATE',(digest(token),))
        proof = await cur.fetchone()
        if not proof:
            raise HTTPException(409,'Guest progress proof expired. Your account is still signed in.')
        if proof['adopted_by']:
            if proof['adopted_by'] != account:
                raise HTTPException(409,'This browser progress has already been saved to another account')
            await cur.execute('SELECT counts FROM guest_transfer_receipts WHERE guest_id=%s',(proof['user_id'],))
            return {'transferred':True,'counts':(await cur.fetchone())['counts']}
        guest = proof['user_id']
        await cur.execute('SELECT id FROM users WHERE id=%s FOR UPDATE',(account,))
        counts = {}
        # Attempts are mutable ownership records; their immutable assessment
        # payloads and source snapshots are preserved. UPDATE fires no award trigger.
        await cur.execute('''UPDATE attempts SET user_id=%s WHERE user_id=%s AND
          (mock_id IS NULL OR NOT EXISTS(SELECT 1 FROM mock_sessions g WHERE g.id=attempts.mock_id
            AND g.submitted_at IS NULL AND EXISTS(SELECT 1 FROM mock_sessions a WHERE a.user_id=%s AND a.submitted_at IS NULL)))''',(account,guest,account))
        counts['attempts'] = cur.rowcount
        # Preserve the target's active mock. An unsubmitted conflicting guest
        # mock stays with the retired guest rather than violating uniqueness.
        await cur.execute('''UPDATE mock_sessions SET user_id=%s WHERE user_id=%s
          AND (submitted_at IS NOT NULL OR NOT EXISTS(SELECT 1 FROM mock_sessions WHERE user_id=%s AND submitted_at IS NULL))''',(account,guest,account))
        counts['mocks'] = cur.rowcount
        await cur.execute("UPDATE practice_study_sessions g SET request_key='adopted:'||g.id WHERE g.user_id=%s AND EXISTS(SELECT 1 FROM practice_study_sessions a WHERE a.user_id=%s AND a.request_key=g.request_key)",(guest,account))
        await cur.execute('UPDATE practice_study_sessions SET user_id=%s WHERE user_id=%s',(account,guest))
        counts['study_sessions'] = cur.rowcount
        await cur.execute('''INSERT INTO answer_reveals(user_id,canonical_id,revealed_at)
          SELECT %s,canonical_id,revealed_at FROM answer_reveals WHERE user_id=%s
          ON CONFLICT(user_id,canonical_id) DO UPDATE SET revealed_at=greatest(answer_reveals.revealed_at,EXCLUDED.revealed_at)''',(account,guest))
        counts['answer_views'] = cur.rowcount
        # Explicit, reviewed mutable progress tables; keep the most recently
        # server-updated checkpoint/draft, never replay client timestamps.
        for table,keys in [('exam_study_checkpoints',['collection_id']),('learning_checkpoints',['kind']),
                           ('module_learning_progress',['module_id','item_id']),('essay_drafts',['canonical_id'])]:
            match=' AND '.join('g.'+k+'=a.'+k for k in keys)
            await cur.execute(f'''DELETE FROM {table} a USING {table} g WHERE a.user_id=%s AND g.user_id=%s
              AND {match} AND g.updated_at>a.updated_at''',(account,guest))
            await cur.execute(f'''DELETE FROM {table} g USING {table} a WHERE g.user_id=%s AND a.user_id=%s AND {match}''',(guest,account))
            await cur.execute(f'UPDATE {table} SET user_id=%s WHERE user_id=%s',(account,guest))
            counts[table]=cur.rowcount
        await cur.execute('''INSERT INTO user_exam_bookmarks(user_id,collection_id)
          SELECT %s,collection_id FROM user_exam_bookmarks WHERE user_id=%s ON CONFLICT DO NOTHING''',(account,guest))
        counts['bookmarks']=cur.rowcount
        # Vocabulary, revision sessions and account-only content require account
        # identity already. They are not transferred by this bounded workflow.
        await cur.execute('UPDATE guest_credentials SET adopted_by=%s,adopted_at=now() WHERE token_hash=%s',(account,digest(token)))
        await cur.execute('INSERT INTO guest_transfer_receipts(guest_id,account_id,counts) VALUES(%s,%s,%s)',(guest,account,Jsonb(counts)))
        await cur.execute("INSERT INTO account_security_events(user_id,action,detail) VALUES(%s,'guest_progress_saved',%s)",(account,Jsonb(counts)))
    return {'transferred':True,'counts':counts}
