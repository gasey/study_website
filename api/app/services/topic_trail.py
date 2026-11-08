"""Short source-checked solo trails sharing the existing assessment reservation."""
from datetime import timedelta
from fastapi import HTTPException
from . import games as g,game_selection as setup

async def context(cur,pack):
 ctx=await setup.resolve(cur,setup.Selection(kind='exam',collection_id=pack['collection_id']),'trail')
 ctx.update(match_ids=[pack['taxonomy_id']],label=pack['title'],trail_pack=pack['id'],trail_pack_version=pack['version'],trail_short=True)
 ctx['trail_ids']=pack.get('canonical_ids')
 ctx['rules'].update(scoring='topic-trail-v1',total_seconds=None,boost='One double-next token; choose before reveal')
 return ctx

async def preview(cur,pack):
 ctx=await context(cur,pack);rows=await setup.candidates(cur,ctx)
 ctx['pool_revision']=g.digest([(r['id'],r['appearance_id'],r['eligibility_revision']) for r in rows])
 return {'id':pack['id'],'title':pack['title'],'collection_id':pack['collection_id'],'taxonomy_id':pack['taxonomy_id'],'active':pack['active'],'version':pack['version'],'available':len(rows),'can_start':pack['active'] and len(rows)>=10,'context_hash':g.digest(ctx),'context':ctx}

async def advance(cur,r,now):
 await cur.execute('SELECT 1 FROM game_members WHERE room_id=%s AND left_at IS NULL',(r['id'],))
 if not await cur.fetchone() or now>=r['deadline']:
  await g.finish(cur,r,now);return await g.room(cur,r['id'])
 if r['trail_phase']=='question' and now>=r['round_ends_at']:
  await cur.execute('INSERT INTO game_answers(room_id,user_id,position,correct,elapsed_ms) VALUES(%s,%s,%s,false,20000) ON CONFLICT DO NOTHING',(r['id'],r['owner_id'],r['current_position']))
 if r['trail_phase']=='question':
  await cur.execute('SELECT 1 FROM game_answers WHERE room_id=%s AND user_id=%s AND position=%s',(r['id'],r['owner_id'],r['current_position']))
  if await cur.fetchone():
   await cur.execute("UPDATE game_rooms SET trail_phase='feedback',round_ends_at=deadline,version=version+1 WHERE id=%s",(r['id'],))
   # Context is now revealed, so the standard attempt exposure cooldown applies.
   await cur.execute('INSERT INTO answer_reveals(user_id,canonical_id) VALUES(%s,%s) ON CONFLICT(user_id,canonical_id) DO UPDATE SET revealed_at=now()',(r['owner_id'],r['questions'][r['current_position']]['id']))
 return await g.room(cur,r['id'])

async def decorate(cur,r,user,result):
 phase=r['trail_phase'];result.update(trail_phase=phase,boost_used=r['trail_boost_position'] is not None,boost_active=r['trail_boost_position']==r['current_position'],feedback=None)
 await cur.execute('SELECT position,chosen_index,correct,excluded FROM game_answers WHERE room_id=%s AND user_id=%s ORDER BY position',(r['id'],user));answers=await cur.fetchall()
 result['stones']=[{'position':a['position'],'correct':a['correct'],'excluded':a['excluded']} for a in answers]
 if r['state']=='running':
  result['question']=None if phase=='ready' else result['question']
  if result['question'] and phase=='question':
   for k in ('source_pdf_url','figure_image_url'):result['question'].pop(k,None)
  if phase=='feedback':
   raw=r['questions'][r['current_position']];live=(await g.current_questions(cur,[raw['id']],r['selection_context'])).get(raw['id'])
   valid=live and all(live.get(k)==raw.get(k) for k in g.IDENTITY)
   a=next(x for x in answers if x['position']==r['current_position'])
   if not valid:await cur.execute('UPDATE game_answers SET excluded=true WHERE room_id=%s AND user_id=%s AND position=%s',(r['id'],user,r['current_position']))
   result['feedback']={'correct':a['correct'] if valid else None,'excluded':not valid,'answer_index':raw['options'].index(raw['answer_text']) if valid else None,'explanation':raw.get('explanation') if valid else None,'source_pdf_url':raw.get('source_pdf_url') if valid else None,'page':raw.get('page') if valid else None}
 # Interim points are provisional until finish rechecks every source key.
 valid=[a for a in answers if not a['excluded']]
 result['trail_score']=sum((200 if a['position']==r['trail_boost_position'] else 100) for a in valid if a['correct'])
 streak=0
 for a in valid:
  streak=streak+1 if a['correct'] else 0
 result['streak']=streak
 if r['state']=='finished':
  player=next(p for p in result['players'] if p['user_id']==user)
  result['trail_score']=player['score'];correct=player['correct']
  result['trail_label']='Perfect trail' if correct==10 else 'Strong run' if correct>=7 else 'Finished' if len(answers)==10 else 'Run ended'
 return result
