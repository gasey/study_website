"""Reviewed editorial word practice; immutable evidence, shared dates, no per-card awards."""
from datetime import timedelta
from uuid import uuid4
from fastapi import HTTPException
from psycopg.types.json import Jsonb
from .curated_vocabulary import WordCard,word_key
from . import review_queue
from .vocabulary_scheduler import due_time,stage

# The published material, account entitlement and two-way block remain authority.
ACCESS="""NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE
 (b.user_id=%(user)s AND b.blocked_id=e.author_id) OR (b.user_id=e.author_id AND b.blocked_id=%(user)s))
 AND (e.access='free' OR e.author_id=%(user)s OR account_has_pro(%(user)s) OR EXISTS(
 SELECT 1 FROM review_grants g WHERE g.user_id=%(user)s AND g.role='owner' AND g.subject_id IS NULL AND g.revoked_at IS NULL))"""
SCOPE="(%(scope)s='all' OR e.exam_scope_id=%(scope)s)"
STALE="r.vocab_content_hash IS DISTINCT FROM e.content_hash"
MODES=('recognition','cloze','mizo-to-english','english-to-mizo')

async def clock(cur,user):
    await cur.execute('SELECT learning_habit_lock(%s)',(user,))
    await cur.execute("SELECT now() AS now,(now() AT TIME ZONE 'Asia/Kolkata')::date AS day")
    return await cur.fetchone()

async def available(cur,user,card,scope='all',lock=False):
    await cur.execute('SELECT e.* FROM v_curated_vocabulary e WHERE e.id=%(card)s AND '+ACCESS+' AND '+SCOPE,
                      {'user':user,'card':card,'scope':scope})
    row=await cur.fetchone()
    if not row:raise HTTPException(404,'This reviewed word card is not available for this account')
    if lock:
        # Serialize publication/archive against the final source check.
        await cur.execute('SELECT id FROM materials WHERE id=%s FOR SHARE',(row['deck_id'],))
        await cur.fetchone()
        return await available(cur,user,card,scope)
    return row

async def new_today(cur,user,day=None):
    await cur.execute("""SELECT (SELECT count(*) FROM vocabulary_state WHERE user_id=%s
      AND (first_review_at AT TIME ZONE 'Asia/Kolkata')::date=COALESCE(%s::date,(now() AT TIME ZONE 'Asia/Kolkata')::date))
      +(SELECT count(*) FROM vocab_exposures WHERE user_id=%s
      AND (first_review_at AT TIME ZONE 'Asia/Kolkata')::date=COALESCE(%s::date,(now() AT TIME ZONE 'Asia/Kolkata')::date)) AS n""",(user,day,user,day))
    return (await cur.fetchone())['n']

async def new_allowed(cur,user,exposure,day=None):
    if (not exposure or exposure['first_review_at'] is None) and await new_today(cur,user,day)>=5:
        raise HTTPException(409,'Today’s five new-card places are complete. Due reviews remain available.')


def supported(payload):
    card=WordCard.model_validate(payload)
    modes=['recognition','cloze']
    if card.language=='mizo-english':
        modes.append('mizo-to-english')
        if card.mizo_options:modes.append('english-to-mizo')
    return modes


def presentation(row,mode):
    card=WordCard.model_validate(row['payload'])
    if mode not in supported(row['payload']):raise HTTPException(422,'This reviewed card does not provide choices for that practice mode')
    if mode=='recognition':prompt='Which meaning matches “'+card.word+'”?';options=card.recognition_options;answer=card.meaning
    elif mode=='cloze':prompt=card.cloze_sentence.replace('{{word}}','_____');options=card.cloze_options;answer=card.word
    elif mode=='mizo-to-english':prompt='Choose the English word for “'+card.mizo_gloss+'”.';options=card.cloze_options;answer=card.word
    else:prompt='Choose the Mizo gloss for “'+card.word+'”.';options=card.mizo_options;answer=card.mizo_gloss
    index=next(i for i,x in enumerate(options) if word_key(x)==word_key(answer))
    return {'mode':mode,'prompt':prompt,'options':options,'answer_index':index,'answer_text':options[index],
            'card':card.model_dump(),'deck_title':row['deck_title'],'deck_id':row['deck_id'],'source':'reviewed-editorial'}

async def exposure(cur,user,card,lock=False):
    await cur.execute('SELECT * FROM vocab_exposures WHERE user_id=%s AND card_id=%s'+(' FOR UPDATE' if lock else ''),(user,card))
    return await cur.fetchone()

async def schedule(cur,user,card,lock=False):
    await cur.execute("SELECT * FROM review_items WHERE user_id=%s AND item_type='vocab' AND item_id=%s"+(' FOR UPDATE' if lock else ''),(user,card))
    return await cur.fetchone()

async def safe_card(cur,row):
    own=await exposure(cur,row['user_id'],row['card_id']);queued=await schedule(cur,row['user_id'],row['card_id'])
    snap=row['snapshot']
    return {'id':row['id'],'card_id':row['card_id'],'deck_id':snap['deck_id'],'deck_title':snap['deck_title'],
      'mode':row['mode'],'prompt':snap['prompt'],'options':snap['options'],'expires_at':row['expires_at'],
      'stage':stage(queued),'started':queued is not None,'source':'reviewed-editorial','seen':own['seen'] if own else 0}

async def issue(cur,user,row,mode):
    await cur.execute('INSERT INTO vocab_exposures(user_id,card_id,content_hash) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING',(user,row['id'],row['content_hash']))
    own=await exposure(cur,user,row['id'],True)
    if own['content_hash']!=row['content_hash']:
        await cur.execute('UPDATE vocab_exposures SET content_hash=%s,version=version+1,last_exposure_at=clock_timestamp() WHERE user_id=%s AND card_id=%s RETURNING *',(row['content_hash'],user,row['id']))
        own=await cur.fetchone()
        await cur.execute("UPDATE review_items SET box=1,due_on=(now() AT TIME ZONE 'Asia/Kolkata')::date,last_result=false,vocab_content_hash=%s WHERE user_id=%s AND item_type='vocab' AND item_id=%s",(row['content_hash'],user,row['id']))
    pid='vp_'+uuid4().hex;snap=presentation(row,mode)
    await cur.execute('''INSERT INTO vocab_presentations(id,user_id,card_id,revision,content_hash,state_version,mode,snapshot)
      VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *''',(pid,user,row['id'],row['revision'],row['content_hash'],own['version'],mode,Jsonb(snap)))
    return await cur.fetchone()

async def next_card(cur,user,deck=None,mode='recognition',card_id=None,resume=None,scope='all'):
    now=await clock(cur,user)
    if resume:
        await cur.execute('SELECT * FROM vocab_presentations WHERE id=%s AND user_id=%s',(resume,user));saved=await cur.fetchone()
        if not saved:raise HTTPException(404,'Word practice card not found')
        source=await available(cur,user,saved['card_id'],scope)
        if deck and source['deck_id']!=deck:raise HTTPException(409,'This saved card belongs to another deck')
        if saved['answered_at']:return {'card':await safe_card(cur,saved),'result':saved['result'],'restored':True}
    from .curated_release import require_writes
    require_writes()
    args={'user':user,'deck':deck,'card':card_id,'scope':scope,'new':await new_today(cur,user),'mode':mode}
    await cur.execute('''SELECT e.* FROM v_curated_vocabulary e
      LEFT JOIN review_items r ON r.user_id=%(user)s AND r.vocab_card_id=e.id
      WHERE '''+ACCESS+' AND '+SCOPE+''' AND (%(deck)s::text IS NULL OR e.deck_id=%(deck)s)
      AND (%(card)s::text IS NULL OR e.id=%(card)s)
      AND (%(mode)s IN ('recognition','cloze') OR (e.payload->>'language'='mizo-english'
        AND (%(mode)s='mizo-to-english' OR (%(mode)s='english-to-mizo' AND jsonb_array_length(COALESCE(e.payload->'mizo_options','[]'::jsonb))>0))))
      AND (r.item_id IS NULL OR r.due_on<=(now() AT TIME ZONE 'Asia/Kolkata')::date OR '''+STALE+''')
      AND (r.item_id IS NOT NULL OR %(new)s<5)
      ORDER BY (r.item_id IS NULL),r.due_on NULLS LAST,e.deck_id,e.position LIMIT 30''',args)
    for source in await cur.fetchall():
        if mode not in supported(source['payload']):continue
        await cur.execute('''SELECT p.* FROM vocab_presentations p JOIN vocab_exposures s ON s.user_id=p.user_id AND s.card_id=p.card_id
          WHERE p.user_id=%s AND p.card_id=%s AND p.mode=%s AND p.content_hash=%s
          AND p.state_version=s.version AND p.answered_at IS NULL AND p.expires_at>%s
          AND NOT EXISTS(SELECT 1 FROM vocab_review_session_items i WHERE i.presentation_id=p.id)
          ORDER BY p.issued_at DESC LIMIT 1''',(user,source['id'],mode,source['content_hash'],now['now']))
        pending=await cur.fetchone()
        if not pending:pending=await issue(cur,user,source,mode)
        return {'card':await safe_card(cur,pending)}
    return {'card':None,'message':'No due or new reviewed word cards are available in this deck and mode.'}

async def grade(cur,user,pid,action,index,session=None):
    await cur.execute('SELECT * FROM vocab_presentations WHERE id=%s AND user_id=%s',(pid,user));shown=await cur.fetchone()
    if not shown:raise HTTPException(404,'Word practice card not found')
    # CMS publication locks material before the author's reward/habit lock.
    # Keep that same order when an author studies their own reviewed deck.
    source=await available(cur,user,shown['card_id'],lock=True)
    now=await clock(cur,user)
    await cur.execute('SELECT * FROM vocab_presentations WHERE id=%s AND user_id=%s FOR UPDATE',(pid,user));shown=await cur.fetchone()
    if shown['answered_at']:
        if shown['action']!=action or shown['chosen_index']!=index:raise HTTPException(409,'This word card already has another saved choice')
        return shown['result']
    from .curated_release import require_writes
    require_writes()
    if (not session and shown['expires_at']<=now['now']) or source['content_hash']!=shown['content_hash']:
        raise HTTPException(409,'This word card expired or its reviewed source changed. Reload before answering; no grade was recorded.')
    await cur.execute('SELECT session_id FROM vocab_review_session_items WHERE presentation_id=%s',(pid,));bound=await cur.fetchone()
    if bound and bound['session_id']!=session:raise HTTPException(409,'Use this card’s saved review controls')
    own=await exposure(cur,user,shown['card_id'],True)
    if not own or (not session and own['version']!=shown['state_version']):raise HTTPException(409,'Another tab updated this word. Reload its current schedule.')
    if action not in ('answer','reveal','defer') or (action=='answer')!=(index is not None):raise HTTPException(422,'Choose an answer, reveal or defer')
    snap=shown['snapshot']
    if index is not None and (not 0<=index<len(snap['options'])):raise HTTPException(422,'Choose one of the displayed word choices')
    await new_allowed(cur,user,own)
    old=await schedule(cur,user,shown['card_id'],True)
    stale=bool(old and old['vocab_content_hash']!=source['content_hash'])
    correct=None if index is None else index==snap['answer_index']
    attempt=None
    if index is not None:
        from .learning_habit import capture_plan
        await capture_plan(cur,user)
        await cur.execute('''INSERT INTO vocab_attempts(user_id,card_id,revision,content_hash,mode,chosen_index,chosen_text,correct,presentation_id,session_id,at)
          VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id''',
          (user,shown['card_id'],shown['revision'],shown['content_hash'],shown['mode'],index,snap['options'][index],correct,pid,session,now['now']))
        attempt=(await cur.fetchone())['id']
        spaced=not own['last_exposure_at'] or now['now']-own['last_exposure_at']>=timedelta(hours=24)
        box,due=review_queue.step(None if stale else old,now['day'],correct,vocab=True,spaced=spaced)
    else:
        box=old['box'] if old and action=='defer' and not stale else 1
        due=max(old['due_on'],now['day']+timedelta(days=1)) if old and old['due_on'] and action=='defer' and not stale else now['day']+timedelta(days=1)
    last=bool(correct) if index is not None else bool(old and old['last_result'] and action=='defer' and not stale)
    await cur.execute('''INSERT INTO review_items(user_id,item_type,item_id,canonical_id,vocab_card_id,vocab_content_hash,box,due_on,last_result)
      VALUES(%s,'vocab',%s,NULL,%s,%s,%s,%s,%s) ON CONFLICT(user_id,item_type,item_id) DO UPDATE SET
      box=EXCLUDED.box,due_on=EXCLUDED.due_on,last_result=EXCLUDED.last_result,vocab_content_hash=EXCLUDED.vocab_content_hash,updated_at=clock_timestamp()''',
      (user,shown['card_id'],shown['card_id'],shown['content_hash'],box,due,last))
    await cur.execute('''UPDATE vocab_exposures SET version=version+1,seen=seen+1,first_review_at=COALESCE(first_review_at,%s),
      last_exposure_at=CASE WHEN %s THEN last_exposure_at ELSE %s END WHERE user_id=%s AND card_id=%s''',
      (now['now'],action=='defer',now['now'],user,shown['card_id']))
    result={'correct':correct,'outcome':action if index is None else 'correct' if correct else 'wrong',
      'answer_text':None if action=='defer' else snap['answer_text'],'answer_index':None if action=='defer' else snap['answer_index'],'explanation':None,'card':None if action=='defer' else snap['card'],
      'next_due':due_time(due).isoformat() if due else None,'stage':6 if due is None else box if last else 0,
      'graduated':due is None,'source':'reviewed-editorial','answer_source':'editorial','verified':False,'curated':True,
      'xp':0,'points':0,'policy':'curated-leitner-v1'}
    await cur.execute('UPDATE vocab_presentations SET answered_at=%s,action=%s,chosen_index=%s,result=%s WHERE id=%s',
                      (now['now'],action,index,Jsonb(result),pid))
    if attempt is not None:
        await cur.execute('SELECT touch_learning_streak(%s,%s)',(user,now['day']))
        if session:
            from ..routers.study_sessions import receipt_key
            await cur.execute('INSERT INTO vocab_practice_receipts(user_id,request_key,attempt_id,response) VALUES(%s,%s,%s,%s)',
                              (user,receipt_key(session,shown['card_id']),attempt,Jsonb(result)))
            await cur.execute('UPDATE vocab_review_session_items SET attempt_id=%s WHERE session_id=%s AND card_id=%s',(attempt,session,shown['card_id']))
    if attempt is not None:await refresh_mastery(cur,user,source['deck_id'])
    return result

async def rows(cur,user,deck=None,scope='all'):
    await cur.execute('''SELECT e.*,r.box,r.due_on,r.last_result,r.vocab_content_hash,
      r.item_id IS NOT NULL AS started,s.first_review_at,s.last_exposure_at,
      a.id AS attempt_id,a.correct,a.at AS attempted_at
      FROM v_curated_vocabulary e LEFT JOIN review_items r ON r.user_id=%(user)s AND r.vocab_card_id=e.id
      LEFT JOIN vocab_exposures s ON s.user_id=%(user)s AND s.card_id=e.id
      LEFT JOIN LATERAL(SELECT id,correct,at FROM vocab_attempts WHERE user_id=%(user)s
        AND card_id=e.id AND content_hash=e.content_hash ORDER BY at DESC,id DESC LIMIT 1) a ON true
      WHERE '''+ACCESS+' AND '+SCOPE+' AND (%(deck)s::text IS NULL OR e.deck_id=%(deck)s) ORDER BY e.deck_id,e.position',
      {'user':user,'deck':deck,'scope':scope})
    return await cur.fetchall()

async def catalog(cur,user,scope='all',deck=None):
    from .mastery import tier
    now=await current_clock(cur)
    groups={};global_latest={};graduated=set()
    for row in await rows(cur,user,deck,scope):
        groups.setdefault(row['deck_id'],[]).append(row)
        key=word_key(row['payload']['word'])
        if row['attempt_id']:
            previous=global_latest.get(key)
            if previous is None or (row['attempted_at'],row['attempt_id'])>(previous['attempted_at'],previous['attempt_id']):global_latest[key]=row
            if row['correct'] and row['started'] and row['due_on'] is None and row['vocab_content_hash']==row['content_hash']:graduated.add(key)
    items=[]
    for did,members in groups.items():
        latest={};due=0;started=0;known=set();modes=set()
        for row in members:
            key=word_key(row['payload']['word']);modes.update(supported(row['payload']))
            started+=row['started'];stale=row['started'] and row['vocab_content_hash']!=row['content_hash']
            due+=bool(row['started'] and (stale or row['due_on'] and row['due_on']<=now['day']))
            if row['attempt_id']:
                prev=latest.get(key)
                if prev is None or (row['attempted_at'],row['attempt_id'])>(prev['attempted_at'],prev['attempt_id']):latest[key]=row
        for key,row in latest.items():
            if row['correct'] and row['started'] and row['due_on'] is None and row['vocab_content_hash']==row['content_hash']:known.add(key)
        attempted=len(latest);correct=sum(bool(r['correct']) for r in latest.values());last=max((r['attempted_at'] for r in latest.values()),default=None)
        await cur.execute('SELECT proficient_at FROM user_vocab_deck_mastery WHERE user_id=%s AND deck_id=%s',(user,did))
        mastery=await cur.fetchone();proficient=mastery['proficient_at'] if mastery else None
        reviewed=False
        if proficient:
            await cur.execute('''SELECT EXISTS(SELECT 1 FROM vocab_attempts a
              JOIN practice_study_sessions s ON s.id=a.session_id AND s.user_id=a.user_id AND s.kind='review' AND s.collection_id IS NULL
              JOIN vocab_review_session_items i ON i.session_id=s.id AND i.card_id=a.card_id AND i.attempt_id=a.id
              JOIN vocab_presentations p ON p.id=i.presentation_id AND p.id=a.presentation_id AND p.user_id=a.user_id
              JOIN v_curated_vocabulary e ON e.id=a.card_id AND e.content_hash=a.content_hash AND e.content_hash=i.content_hash
              JOIN vocab_practice_receipts r ON r.user_id=a.user_id AND r.attempt_id=a.id
                AND r.request_key='study:'||s.id||':'||left(encode(sha256(convert_to(a.card_id,'UTF8')),'hex'),32)
              WHERE a.user_id=%s AND e.deck_id=%s AND s.finished_at>=%s+interval '14 days'
                AND a.at>=%s+interval '14 days' AND a.at BETWEEN s.created_at AND s.finished_at
                AND a.card_id=ANY(s.question_ids) AND s.paper_ids[array_position(s.question_ids,a.card_id)] IS NULL
                AND p.content_hash=a.content_hash AND p.answered_at=a.at AND p.action='answer' AND p.result=r.response
                AND i.revision=a.revision AND p.chosen_index=a.chosen_index) AS yes''',
              (user,did,proficient,proficient))
            reviewed=(await cur.fetchone())['yes']
        state=tier(attempted,correct,reviewed)
        items.append({'id':did,'label':members[0]['deck_title'],'source':'curated','eligible_cards':len(members),
          'eligible_words':len({word_key(r['payload']['word']) for r in members}),'started':started,'due':due,
          'attempted':attempted,'correct_latest':correct,'known':len(known),'state':state,
          'rusty':bool(state in ('proficient','mastered') and last and now['now']-last>=timedelta(days=45)),
          'last_activity':last,'modes':[m for m in MODES if m in modes],
          'collection_id':members[0]['collection_id'],'subject_id':members[0]['subject_id'],
          'url':'/materials/'+did})
    from .curated_release import enabled
    return {'known_total':sum(bool(global_latest[k]['correct']) for k in graduated),'practice_enabled':enabled(),'items':items,'basis':'Distinct English words in current reviewed cards; latest checks and completed spaced reviews. No per-card points.'}

async def current_clock(cur):
    await cur.execute("SELECT clock_timestamp() AS now,(clock_timestamp() AT TIME ZONE 'Asia/Kolkata')::date AS day")
    return await cur.fetchone()

async def refresh_mastery(cur,user,deck):
    data=await catalog(cur,user,deck=deck)
    if not data['items']:return
    item=data['items'][0];proficient=item['attempted']>=20 and item['correct_latest']*100>=80*item['attempted']
    await cur.execute('''INSERT INTO user_vocab_deck_mastery(user_id,deck_id,proficient_at)
      VALUES(%s,%s,CASE WHEN %s THEN clock_timestamp() END) ON CONFLICT(user_id,deck_id) DO UPDATE SET
      proficient_at=CASE WHEN %s THEN COALESCE(user_vocab_deck_mastery.proficient_at,clock_timestamp()) ELSE NULL END''',
      (user,deck,proficient,proficient))
