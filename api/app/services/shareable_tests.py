"""Published timed learning collections; private keys never enter public metadata."""
from typing import Literal
from fastapi import HTTPException
from pydantic import BaseModel,ConfigDict,Field
from psycopg.types.json import Jsonb
from .scoring_revisions import capture_mock_questions
from .repeat_selection import distinct_candidates


class TestConfig(BaseModel):
    model_config=ConfigDict(extra='forbid')
    duration_minutes:int=Field(default=20,ge=1,le=240)
    marks_correct:float=Field(default=1,gt=0,le=10,allow_inf_nan=False)
    marks_wrong:float=Field(default=0,ge=0,le=10,allow_inf_nan=False)
    answer_mode:Literal['official','derived-practice']='official'


async def capture(cur,payload):
    ids=payload['question_ids']
    if not ids:raise HTTPException(422,'Add at least one question to the test')
    await cur.execute('SELECT id FROM canonical_questions WHERE id=ANY(%s) ORDER BY id FOR SHARE',(ids,))
    await cur.fetchall()
    if len(await distinct_candidates(cur,ids))!=len(ids):
        raise HTTPException(422,'This test contains a reviewed repeat. Keep one of the matching questions.')
    rows=await capture_mock_questions(cur,ids,[None]*len(ids),payload['test_config']['answer_mode'])
    if len(rows)!=len(ids) or any(r['snapshot'].get('has_diagram') and not r['snapshot'].get('figure_image') for r in rows):
        raise HTTPException(422,'Every test question needs an eligible key or reviewed solution and complete source options/context. Check the selected answer mode.')
    return rows


async def freeze(cur,eid,revision,payload,actor_id):
    rows=await capture(cur,payload)
    await cur.execute('''INSERT INTO learning_test_publications(entry_id,revision,payload,questions,published_by)
       VALUES(%s,%s,%s,%s,%s)''',(eid,revision,Jsonb(payload),Jsonb(rows),actor_id))


async def published(cur,eid,lock=False):
    await cur.execute('''SELECT p.entry_id,p.revision,p.payload,p.questions,p.published_at
      FROM learning_catalog c JOIN learning_test_publications p ON p.entry_id=c.id AND p.revision=c.live_test_version
      WHERE c.id=%s AND c.live_payload IS NOT NULL'''+(' FOR SHARE OF c' if lock else ''),(eid,))
    row=await cur.fetchone()
    if not row:raise HTTPException(404,'This test is not published or has been withdrawn')
    return row


async def for_start(cur,eid,revision,user_id):
    row=await published(cur,eid,True)
    if row['revision']!=revision:raise HTTPException(409,'A new test edition is available. Return to the test page before starting.')
    await cur.execute('''SELECT count(*)::int AS n FROM mock_sessions WHERE user_id=%s
      AND learning_test_id=%s AND started_at>now()-interval '1 day' ''',(user_id,eid))
    if (await cur.fetchone())['n']>=3:raise HTTPException(429,'You can start this shared test three times in 24 hours. Your saved results remain available.')
    fresh=await capture(cur,row['payload'])
    if fresh!=row['questions']:raise HTTPException(409,'A source or key changed. The creator needs to submit an updated edition before new attempts can start.')
    return row


def metadata(row):
    p=row['payload']
    return {'id':row['entry_id'],'revision':row['revision'],'title':p['title'],
      'description':p['description'],'subject_id':p['subject_id'],'question_count':len(p['question_ids']),
      'config':p['test_config'],'published_at':row['published_at'],
      'path':'/tests/'+row['entry_id'],'share_path':'/api/tests/'+row['entry_id']+'/share'}
