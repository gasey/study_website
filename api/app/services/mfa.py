"""RFC 6238 TOTP with encrypted, account-bound seeds and one-use recovery."""
import base64
import hashlib
import hmac
import json
import secrets
import struct
import time
from cryptography.fernet import Fernet,InvalidToken
from fastapi import HTTPException
from ..config import settings


def cipher():
    try:return Fernet(settings.mfa_encryption_key.encode())
    except (ValueError,TypeError):raise HTTPException(503,'Authenticator security is not configured') from None


def encrypt(user,seed):return cipher().encrypt(json.dumps({'user':user,'seed':seed}).encode()).decode()
def decrypt(user,value):
    try:
        data=json.loads(cipher().decrypt(value.encode()))
        if data['user']!=user:raise ValueError()
        return data['seed']
    except (InvalidToken,ValueError,KeyError,TypeError,AttributeError):
        raise HTTPException(503,'Authenticator security is temporarily unavailable') from None


def totp(seed,counter,digits=6):
    raw=base64.b32decode(seed+'='*((8-len(seed)%8)%8))
    mac=hmac.new(raw,struct.pack('>Q',counter),hashlib.sha1).digest();offset=mac[-1]&15
    return str((int.from_bytes(mac[offset:offset+4],'big')&0x7fffffff)%(10**digits)).zfill(digits)


def matching_counter(seed,code,now=None):
    if not isinstance(code,str) or len(code)!=6 or not code.isascii() or not code.isdigit():return None
    counter=int(time.time() if now is None else now)//30
    matches=[c for c in (max(0,counter-1),counter,counter+1) if hmac.compare_digest(totp(seed,c),code)]
    return max(matches) if matches else None


def code_hash(code):return hashlib.sha256(code.replace('-','').replace(' ','').upper().encode()).hexdigest()


async def consume(cur,user,code):
    await cur.execute('SELECT * FROM account_mfa WHERE user_id=%s FOR UPDATE',(user,));row=await cur.fetchone()
    if not row or not row['enabled_at']:return False
    counter=matching_counter(decrypt(user,row['secret_cipher']),code)
    if counter is not None and counter>row['last_counter']:
        await cur.execute('UPDATE account_mfa SET last_counter=%s,updated_at=now() WHERE user_id=%s',(counter,user));return True
    await cur.execute('UPDATE mfa_recovery_codes SET used_at=now() WHERE user_id=%s AND code_hash=%s AND used_at IS NULL RETURNING code_hash',(user,code_hash(code)))
    return bool(await cur.fetchone())


async def limit(user):
    # Commit failures too: this independent transaction precedes validation.
    from ..db import cursor
    async with cursor() as cur:
        await cur.execute("""INSERT INTO review_rate_buckets(bucket,count,expires_at) VALUES (%s,1,now()+interval '5 minutes')
           ON CONFLICT(bucket) DO UPDATE SET count=CASE WHEN review_rate_buckets.expires_at<=now() THEN 1 ELSE review_rate_buckets.count+1 END,
           expires_at=CASE WHEN review_rate_buckets.expires_at<=now() THEN now()+interval '5 minutes' ELSE review_rate_buckets.expires_at END RETURNING count""",('mfa:'+user,))
        count=(await cur.fetchone())['count']
    if count>10:raise HTTPException(429,'Too many authenticator attempts. Try again in five minutes.',headers={'Retry-After':'300'})


async def recovery(cur,user):
    codes=[secrets.token_hex(8).upper() for _ in range(10)]
    await cur.execute('UPDATE mfa_recovery_codes SET used_at=COALESCE(used_at,now()) WHERE user_id=%s',(user,))
    for code in codes:await cur.execute('INSERT INTO mfa_recovery_codes(user_id,code_hash) VALUES (%s,%s)',(user,code_hash(code)))
    return ['-'.join(code[i:i+4] for i in range(0,len(code),4)) for code in codes]
