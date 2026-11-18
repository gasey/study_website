"""Frozen editorial items in the existing Smart Review session and award ledger."""
from fastapi import HTTPException
from psycopg.types.json import Jsonb
from . import curated_practice as words
from .curated_release import enabled as practice_enabled


def supports_words(request):
    return not bool(getattr(request.state,'mobile_session',None)) and getattr(request,'headers',{}).get('x-finna-review-items')=='curated-v1'

def native_guard(row,request):
    if (row.get('filters') or {}).get('has_curated') and getattr(request.state,'mobile_session',None):
        raise HTTPException(403,'This saved set includes reviewed word cards. Continue it on the website; native word-card support is not enabled.')
    if (row.get('filters') or {}).get('has_curated') and not supports_words(request):
        raise HTTPException(409,'This saved set needs the updated word-card reader. Your grades are saved. Reload the website or use bank-only reviews until word-card support is available.')

async def freeze(cur,user,sid,item,first=False):
    source=await words.available(cur,user,item['item_id'])
    old=await words.schedule(cur,user,item['item_id'])
    mode='cloze' if item['box']>=3 else 'recognition'
    shown=await words.issue(cur,user,source,mode)
    await cur.execute("SELECT (now() AT TIME ZONE 'Asia/Kolkata')::date AS day")
    day=(await cur.fetchone())['day']
    was_due=bool(old and old['due_on'] and old['due_on']<=day and old['vocab_content_hash']==source['content_hash'])
    await cur.execute('''INSERT INTO vocab_review_session_items(session_id,card_id,due_on,was_due,revision,content_hash,presentation_id,opened_at)
      VALUES(%s,%s,%s,%s,%s,%s,%s,CASE WHEN %s THEN clock_timestamp() END)''',
      (sid,item['item_id'],item['due_on'],was_due,source['revision'],source['content_hash'],shown['id'],first))

async def receipts(cur,row):
    await cur.execute('''SELECT a.*,r.request_key,r.response,p.snapshot,e.content_hash AS current_hash
      FROM vocab_practice_receipts r JOIN vocab_attempts a ON a.id=r.attempt_id AND a.user_id=r.user_id
      JOIN vocab_presentations p ON p.id=a.presentation_id
      JOIN v_curated_vocabulary e ON e.id=a.card_id
      WHERE a.session_id=%(sid)s AND a.user_id=%(user)s AND '''+words.ACCESS+'''
      AND a.at>=%(start)s AND (%(finish)s::timestamptz IS NULL OR a.at<=%(finish)s)''',
      {'sid':row['id'],'user':row['user_id'],'start':row['created_at'],'finish':row['finished_at']})
    from ..routers.study_sessions import receipt_key
    checked={}
    for item in await cur.fetchall():
        cid=item['card_id']
        if cid not in row['question_ids'] or item['request_key']!=receipt_key(row['id'],cid):continue
        checked[cid]={'result':item['response'],'chosen_index':item['chosen_index'],'snapshot':item['snapshot'],
                      'updated_fields':['reviewed word content'] if item['content_hash']!=item['current_hash'] else []}
    return checked

async def questions(cur,row):
    await cur.execute('''SELECT i.*,p.snapshot,p.result,p.action,e.content_hash AS current_hash
      FROM vocab_review_session_items i JOIN vocab_presentations p ON p.id=i.presentation_id AND p.user_id=%(user)s
      JOIN v_curated_vocabulary e ON e.id=i.card_id WHERE i.session_id=%(sid)s AND '''+words.ACCESS,
      {'sid':row['id'],'user':row['user_id']})
    result=[]
    for item in await cur.fetchall():
        snap=item['snapshot']
        result.append({'id':item['card_id'],'type':'mcq','question':snap['prompt'],'options':snap['options'],
          'direction':None,'question_markup':None,'options_markup':None,'passage':None,'subject':'Reviewed vocabulary','topic':None,
          'taxonomy_subject_id':None,'taxonomy_subject':None,'taxonomy_topic_id':None,'taxonomy_topic':None,'taxonomy_subtopic_id':None,'taxonomy_subtopic':None,
          'classification_status':None,'source_defect':None,'key_disputed':False,'dispute_note':None,'times_asked':0,'first_year':None,'last_year':None,
          'answer_source':'editorial','verified':False,'subject_label':'Reviewed vocabulary',
          'curated':{'card_id':item['card_id'],'presentation_id':item['presentation_id'],'mode':snap.get('mode'),
                     'deck_id':snap['deck_id'],'deck_title':snap['deck_title'],
                     'revealed_result':item['result'] if item['action']=='reveal' else None,
                     'practice_enabled':practice_enabled(),
                     'source_changed':item['content_hash']!=item['current_hash']}})
    return result

async def position(cur,sid,cid):
    await cur.execute('UPDATE vocab_review_session_items SET opened_at=clock_timestamp() WHERE session_id=%s AND card_id=%s AND attempt_id IS NULL',(sid,cid))

async def check(cur,row,cid,index):
    await cur.execute('SELECT presentation_id FROM vocab_review_session_items WHERE session_id=%s AND card_id=%s',(row['id'],cid))
    item=await cur.fetchone()
    if not item:return False
    await words.grade(cur,row['user_id'],item['presentation_id'],'answer',index,session=row['id'])
    return True

async def reveal(cur,row,cid):
    await cur.execute('SELECT presentation_id FROM vocab_review_session_items WHERE session_id=%s AND card_id=%s',(row['id'],cid))
    item=await cur.fetchone()
    if not item:raise HTTPException(404,'Word card is not in this saved set')
    return await words.grade(cur,row['user_id'],item['presentation_id'],'reveal',None,session=row['id'])

async def was_revealed(cur,row,cid):
    await cur.execute("SELECT 1 FROM vocab_review_session_items i JOIN vocab_presentations p ON p.id=i.presentation_id AND p.user_id=%s WHERE i.session_id=%s AND i.card_id=%s AND p.action='reveal' AND p.answered_at IS NOT NULL",(row['user_id'],row['id'],cid))
    return bool(await cur.fetchone())

async def is_card(cur,sid,cid):
    await cur.execute('SELECT 1 FROM vocab_review_session_items WHERE session_id=%s AND card_id=%s',(sid,cid))
    return bool(await cur.fetchone())

async def finish_checks(cur,row):
    await cur.execute('''SELECT a.id,a.card_id AS canonical_id,CASE WHEN a.correct THEN 'correct' ELSE 'wrong' END AS outcome,
      i.due_on,i.was_due,a.at>=i.opened_at+interval '3 seconds' AS timed,true AS curated
      FROM vocab_review_session_items i JOIN practice_study_sessions s ON s.id=i.session_id AND s.user_id=%(user)s AND s.kind='review'
      JOIN vocab_attempts a ON a.id=i.attempt_id AND a.session_id=s.id AND a.user_id=s.user_id AND a.card_id=i.card_id
      JOIN vocab_presentations p ON p.id=a.presentation_id AND p.id=i.presentation_id AND p.user_id=s.user_id
      JOIN vocab_practice_receipts r ON r.attempt_id=a.id AND r.user_id=a.user_id
        AND r.request_key='study:'||s.id||':'||left(encode(sha256(convert_to(a.card_id,'UTF8')),'hex'),32)
      JOIN v_curated_vocabulary e ON e.id=a.card_id AND e.content_hash=a.content_hash AND e.content_hash=i.content_hash
      WHERE s.id=%(sid)s AND s.finished_at IS NOT NULL AND s.collection_id IS NULL
      AND a.card_id=ANY(s.question_ids) AND s.paper_ids[array_position(s.question_ids,a.card_id)] IS NULL
      AND i.revision=a.revision AND a.at BETWEEN s.created_at AND s.finished_at
      AND i.opened_at IS NOT NULL AND p.action='answer' AND p.answered_at=a.at
      AND p.card_id=a.card_id AND p.content_hash=a.content_hash AND p.revision=a.revision AND p.mode=a.mode
      AND p.chosen_index=a.chosen_index AND p.snapshot->'options'->>a.chosen_index=a.chosen_text
      AND ((p.snapshot->>'answer_index')::int=a.chosen_index) IS NOT DISTINCT FROM a.correct
      AND p.result=r.response AND (r.response->>'correct')::boolean=a.correct
      AND '''+words.ACCESS,{'user':row['user_id'],'sid':row['id']})
    # Both records bind the same server grading instant and committed choice;
    # a client acknowledgement cannot stand in for an immutable grade.
    return await cur.fetchall()

async def total_due(cur,row):
    await cur.execute('''SELECT count(*)::int AS n FROM vocab_review_session_items i JOIN v_curated_vocabulary e
      ON e.id=i.card_id AND e.content_hash=i.content_hash WHERE i.session_id=%(sid)s AND i.was_due AND '''+words.ACCESS,
      {'user':row['user_id'],'sid':row['id']})
    return (await cur.fetchone())['n']
