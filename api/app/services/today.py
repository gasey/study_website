"""One private composition of real plan inputs. Reads never create activity."""
from urllib.parse import urlencode
from . import mastery,review_queue


async def saved_exam(cur,user):
    await cur.execute('''SELECT c.id,c.title,b.is_primary FROM user_exam_bookmarks b JOIN collections c
      ON c.id=b.collection_id AND c.visibility='public' AND c.kind='exam'
      WHERE b.user_id=%s ORDER BY b.is_primary DESC,b.created_at DESC,c.id LIMIT 1''',(user,))
    return await cur.fetchone()


async def focus_subjects(cur,user,exam=None):
    await cur.execute('''SELECT s.id,s.label,EXISTS(SELECT 1 FROM user_focus_subjects f
      WHERE f.user_id=%(user)s AND f.subject_id=s.id) AS selected FROM review_taxonomy s
      WHERE s.active AND s.level='subject' AND (%(exam)s::text IS NULL OR EXISTS(
        SELECT 1 FROM question_classifications qc JOIN appearances a ON a.canonical_id=qc.question_id
        JOIN collection_papers cp ON cp.paper_id=a.paper_id JOIN collections c ON c.id=cp.collection_id
        AND c.live_version=cp.version AND c.visibility='public'
        WHERE cp.collection_id=%(exam)s AND qc.subject_id=s.id AND qc.review_status='approved')) ORDER BY s.label,s.id''',
      {'user':user,'exam':exam['id'] if exam else None})
    available=await cur.fetchall()
    await cur.execute('''SELECT f.subject_id,s.label FROM user_focus_subjects f JOIN review_taxonomy s
      ON s.id=f.subject_id AND s.active AND s.level='subject' WHERE user_id=%s ORDER BY position''',(user,))
    return {'items':await cur.fetchall(),'available':available,'limit':5}


async def weak_target(cur,user,exam):
    if not exam:return None
    await cur.execute('''SELECT m.subject_id,m.topic,COALESCE(s.label,m.subject_id) AS subject_label,
      COALESCE(t.label,m.topic) AS topic_label,available.n AS target FROM user_topic_mastery m
      LEFT JOIN review_taxonomy s ON s.id=m.subject_id LEFT JOIN review_taxonomy t ON t.id=m.topic
      CROSS JOIN LATERAL(SELECT count(*)::int AS n FROM (
        SELECT q.id FROM v_scorable q JOIN question_classifications qc ON qc.question_id=q.id
        AND qc.review_status='approved' AND qc.subject_id=m.subject_id AND qc.topic_id=m.topic
        WHERE EXISTS(SELECT 1 FROM appearances a JOIN collection_papers cp ON cp.paper_id=a.paper_id
          JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version AND c.visibility='public'
          WHERE a.canonical_id=q.id AND c.id=%(exam)s)
        AND NOT EXISTS(SELECT 1 FROM user_activity_questions aq WHERE aq.user_id=%(user)s AND aq.canonical_id=q.id)
        ORDER BY q.id LIMIT 10) limited) available
      WHERE m.user_id=%(user)s AND m.state IN ('practicing','proficient') AND available.n>0
      AND (NOT EXISTS(SELECT 1 FROM user_focus_subjects f JOIN review_taxonomy r ON r.id=f.subject_id AND r.active WHERE f.user_id=%(user)s)
        OR EXISTS(SELECT 1 FROM user_focus_subjects f JOIN review_taxonomy r ON r.id=f.subject_id AND r.active WHERE f.user_id=%(user)s AND f.subject_id=m.subject_id))
      ORDER BY 1.0*m.distinct_correct_latest/m.distinct_attempted,m.distinct_attempted,m.subject_id,m.topic LIMIT 1''',
      {'user':user,'exam':exam['id']})
    row=await cur.fetchone()
    if row:
        row['url']='/exams/'+exam['id']+'?'+urlencode({'subject_id':row['subject_id'],'topic_id':row['topic'],'study_status':'unseen','pool':'scorable','view':'practice'})
    return row


async def exam_preparation(cur,user,exam,day):
    # Owned targets are the only input; official dates never silently opt a learner in.
    await cur.execute("""SELECT e.id,e.date,e.title,e.collection_id FROM calendar_entries e
      LEFT JOIN collections c ON c.id=e.collection_id AND c.visibility='public' AND c.kind='exam'
      WHERE e.user_id=%s AND e.kind='exam-target' AND e.date>=%s
        AND (e.collection_id IS NULL OR (e.collection_id=%s AND c.id IS NOT NULL))
      ORDER BY e.date,e.id LIMIT 1""",(user,day,exam['id'] if exam else None))
    target=await cur.fetchone()
    if not target:return None
    remaining=(target['date']-day).days
    limit=0 if remaining<=7 else 3 if remaining<=14 else 5 if remaining<=28 else 10
    return {'id':str(target['id']),'date':target['date'].isoformat(),'title':target['title'],
            'days_remaining':remaining,'new_limit':limit,
            'phase':'review' if remaining<=7 else 'consolidate' if remaining<=28 else 'build',
            'mock_url':'/exams/'+exam['id']+'/mock' if exam and remaining<=28 else None}


def taper(target,preparation):
    if not target or not preparation:return target
    limit=min(target['target'],preparation['new_limit'])
    return {**target,'target':limit} if limit else None


async def compose(cur,user,include_curated=True,include_atlas=True):
    registered=await mastery.account(cur,user)
    await cur.execute("SELECT (now() AT TIME ZONE 'Asia/Kolkata')::date AS today")
    day=(await cur.fetchone())['today']
    exam=await saved_exam(cur,user) if registered else None
    reviews=await review_queue.queue(cur,user,1,include_curated=include_curated) if registered else {'due_count':0,'scheduled_count':0}
    focus=await focus_subjects(cur,user,exam) if registered else {'items':[],'available':[],'limit':5}
    await cur.execute('''SELECT r.id,r.state FROM game_daily_entries e JOIN game_rooms r ON r.id=e.room_id
      WHERE e.user_id=%s AND e.daily_id=%s''',(user,day.isoformat()))
    entry=await cur.fetchone()
    from .learning_rewards import daily_quests_status
    quests=await daily_quests_status(cur,user) if registered else {'quests':[],'week_strip':[],'ist_date':day.isoformat()}
    fixed=quests.get('plan',{'started':False})
    preparation=(fixed.get('exam_preparation') if fixed['started'] else
                 await exam_preparation(cur,user,exam,day)) if registered else None
    target=(fixed.get('new_target') if fixed['started'] else
            taper(await weak_target(cur,user,exam),preparation)) if registered else None
    from .weekly_recap import compose as recap
    weekly_recap=await recap(cur,user) if registered else None
    from .vocabulary_scheduler import today as vocabulary_today
    vocabulary=await vocabulary_today(cur,user,include_curated=include_curated) if registered else None
    from .atlas_drills import suggestions as atlas_suggestions
    atlas=await atlas_suggestions(cur,user,exam) if registered and include_atlas else []
    return {'atlas_suggestions':atlas,'vocabulary':vocabulary,'exam_preparation':preparation,'weekly_recap':weekly_recap,'ist_date':day.isoformat(),'account':registered,'exam':exam,'focus':focus,
      'due_count':reviews['due_count'],'scheduled_count':reviews['scheduled_count'],
      'new_questions':target,
      'plan_status':fixed,
      'daily_five':{'status':entry['state'] if entry else 'not_started','url':'/games/'+entry['id'] if entry else '/games?mode=daily'},
      'quests':quests['quests'],'week_strip':quests['week_strip'],
      'empty_reason':'Use this final week for due reviews and an optional normal mock.' if preparation and preparation['new_limit']==0 else 'Choose a saved exam to get a study target.' if not exam else 'Build topic practice to get a new-question target.'}
