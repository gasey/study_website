"""Milestone latches: a rollup/worker can observe a tier without awarding it."""
RANK={'exploring':0,'practicing':1,'proficient':2,'mastered':3}


async def evidence(cur,user,attempt_ids,review_session):
    if not attempt_ids and not review_session:return {}
    from .learning_habit import QUALIFIED
    # The caller owns the job row before the live write. Current, original
    # provenance and adjusted eligibility must still qualify after that write.
    await cur.execute('''SELECT e.id,qc.subject_id,qc.topic_id AS topic FROM ('''+QUALIFIED+''') e
      JOIN question_classifications qc ON qc.question_id=e.canonical_id
      WHERE qc.review_status='approved' AND qc.topic_id IS NOT NULL
      AND e.outcome IN ('correct','wrong') AND e.at<=clock_timestamp()
      AND (e.at AT TIME ZONE 'Asia/Kolkata')::date=(now() AT TIME ZONE 'Asia/Kolkata')::date
      AND (e.id=ANY(%(ids)s) OR EXISTS(SELECT 1 FROM review_session_items i
        JOIN practice_study_sessions s ON s.id=i.session_id
        JOIN practice_request_receipts r ON r.attempt_id=i.attempt_id AND r.user_id=s.user_id
          AND r.request_key='study:'||s.id||':'||left(encode(sha256(convert_to(i.canonical_id,'UTF8')),'hex'),32)
        WHERE s.id=%(review)s AND s.user_id=%(user)s AND s.kind='review' AND s.finished_at IS NOT NULL
          AND i.attempt_id=e.id AND i.canonical_id=e.canonical_id AND e.context='review'
          AND e.collection_id IS NULL AND e.paper_id=s.paper_ids[array_position(s.question_ids,e.canonical_id)]
          AND e.at>=s.created_at AND e.at<=s.finished_at AND e.at>=i.opened_at+interval '3 seconds'))
      ORDER BY e.id''',{'user':user,'ids':list(attempt_ids),'review':review_session})
    result={}
    for r in await cur.fetchall():result.setdefault((r['subject_id'],r['topic']),(r['id'],review_session))
    return result


async def settle(cur,user,subject,topic,old_state,state,cause):
    for target,xp,points in [('proficient',30,3),('mastered',60,5)]:
        if RANK[state]<RANK[target]:continue
        await cur.execute('SELECT 1 FROM mastery_milestones WHERE user_id=%s AND topic=%s AND tier=%s',(user,topic,target))
        if await cur.fetchone():continue
        if cause and RANK.get(old_state,-1)<RANK[target]:
            await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('rewards:'+user,))
            await cur.execute('INSERT INTO reward_profiles(user_id) VALUES(%s) ON CONFLICT DO NOTHING',(user,))
            await cur.execute('''INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note,rule_version,source_attempt_id)
              VALUES(%s,%s,'study',%s,%s,%s,'learning-v2',%s) RETURNING id''',
              (user,f'mastery:{user}:{topic}:{target}',xp,points,'Topic reached '+target,cause[0]))
            ledger=(await cur.fetchone())['id']
            await cur.execute('''INSERT INTO mastery_milestones(user_id,subject_id,topic,tier,origin,ledger_id,source_attempt_id,review_session_id)
              VALUES(%s,%s,%s,%s,'activity',%s,%s,%s)''',(user,subject,topic,target,ledger,*cause))
        else:
            # Baseline, reconciliation and historical/correction-only changes
            # consume the milestone without creating an award row.
            await cur.execute('''INSERT INTO mastery_milestones(user_id,subject_id,topic,tier,origin)
              VALUES(%s,%s,%s,%s,'baseline') ON CONFLICT DO NOTHING''',(user,subject,topic,target))
