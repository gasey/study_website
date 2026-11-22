"""Finnaplan 0.9.2: three distinct combined-filter searches per IST day.

Basic exam/year/subject filters and reading an opened question remain free.
Admission is transactional; repeated queries and pagination share one receipt.
"""
import hashlib
import json
from fastapi import HTTPException

LIMIT = 3
ACTION = 'power-filter-v1'
FILTERS = ('atlas_chapter','atlas_layer','pool', 'answer_status', 'q', 'year_from', 'year_to', 'source',
           'subject_id', 'topic_id', 'subtopic_id', 'study_area', 'shelf_id',
           'learning_entry', 'collection_id', 'section_path', 'paper_id',
           'essay_kind', 'repeats_only', 'origin', 'exam_scope')


def power_filter(query):
    """Accept parsed HTTP query lists or normalized router arguments."""
    def values(key):
        value = query.get(key)
        return value if isinstance(value, list) else [value]
    def present(key):
        return any(v is not None and v != '' for v in values(key))
    topic = present('topic_id') or present('subtopic_id') or present('atlas_chapter')
    year = present('year_from') or present('year_to')
    answer = (present('answer_status') or present('source')
              or any(v and v != 'all' for v in values('pool')))
    cross_exam = 'all' in values('exam_scope') and any(present(k) for k in
        ('subject_id', 'topic_id', 'subtopic_id', 'shelf_id','atlas_chapter'))
    return cross_exam or sum((topic, year, answer)) >= 2


def query_key(query):
    normalized = {key: value for key in FILTERS
                  if (value := query.get(key)) is not None and value != '' and value != []}
    normalized.update(pool=normalized.get('pool', 'all'), origin=normalized.get('origin', 'paper'),
                      exam_scope=normalized.get('exam_scope', 'mizoram-recruitment'))
    if 'source' in normalized:
        normalized['source'] = sorted(set(normalized['source']))
    if 'q' in normalized:
        normalized['q'] = normalized['q'].strip().casefold()
    return hashlib.sha256(json.dumps(normalized, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


async def allowance(cur, user, *, request_key=None):
    await cur.execute("""SELECT email IS NOT NULL AS account, account_has_pro(id) AS pro,
        (now() AT TIME ZONE 'Asia/Kolkata')::date AS today FROM users WHERE id=%s""", (user,))
    profile = await cur.fetchone()
    if not profile:
        raise HTTPException(401, 'Sign in to use combined filters. Basic filters remain free.')
    tier = 'pro' if profile['account'] and profile['pro'] else 'account' if profile['account'] else 'guest'
    today = profile['today']
    if request_key and tier == 'guest':
        raise HTTPException(401, 'Sign in for three combined-filter searches per day. Basic exam, year and subject filters remain free.')
    if request_key and tier == 'account':
        await cur.execute('''INSERT INTO rate_limits(user_id,action,ist_date) VALUES(%s,%s,%s)
            ON CONFLICT DO NOTHING''', (user, ACTION, today))
        await cur.execute('''SELECT request_keys FROM rate_limits WHERE user_id=%s AND action=%s
            AND ist_date=%s FOR UPDATE''', (user, ACTION, today))
        keys = (await cur.fetchone())['request_keys']
        if request_key not in keys:
            if len(keys) >= LIMIT:
                raise HTTPException(403, 'All three combined-filter searches are used today. Reopen an earlier combination, use basic filters, or return tomorrow. Pro includes unlimited combined filters.')
            keys = [*keys, request_key]
            await cur.execute('''UPDATE rate_limits SET request_keys=%s,updated_at=now()
                WHERE user_id=%s AND action=%s AND ist_date=%s''', (keys, user, ACTION, today))
    else:
        await cur.execute('''SELECT request_keys FROM rate_limits WHERE user_id=%s AND action=%s
            AND ist_date=%s''', (user, ACTION, today))
        row = await cur.fetchone()
        keys = row['request_keys'] if row else []
    return {'tier': tier, 'ist_date': today.isoformat(), 'used': len(keys),
            'limit': None if tier == 'pro' else LIMIT if tier == 'account' else 0,
            'remaining': None if tier == 'pro' else max(0, LIMIT - len(keys)) if tier == 'account' else 0,
            'unlimited': tier == 'pro'}
