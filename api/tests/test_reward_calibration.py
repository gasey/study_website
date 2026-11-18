"""Seven-day settlement fixtures, not a simulation of independent human review.

Controller eligibility is covered by test_completion_awards, test_learning_habit
and the real publication/sync flow in test_bank_review. Here historical source
receipts are composed explicitly, and the actual v2 ledger policy runs as mpsc.
"""
from datetime import datetime,timedelta,timezone
from decimal import Decimal
import json,os
from pathlib import Path
from uuid import uuid4
from psycopg.types.json import Jsonb
from test_contribution_rewards_v2 import publication,credit


def test_seeded_mixed_week_reconciles_to_owner_prices(client,actor,database):
    conn=database[1];tag=uuid4().hex
    heavy='heavy-'+tag;average='average-'+tag
    for user in (heavy,average):conn.execute('INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)',(user,user,user+'@example.test'))
    days=[datetime(2020,1,6,6,tzinfo=timezone.utc)+timedelta(days=i) for i in range(7)]
    def ledger(user,key,kind,xp,points,at,source=None):
        return conn.execute('''INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note,created_at,source_attempt_id)
          VALUES(%s,%s,%s,%s,%s,'Synthetic mixed-week settlement fixture',%s,%s) RETURNING id,xp,points''',(user,key,kind,xp,points,at,source)).fetchone()
    def question(user,at):
        q='calibration-'+uuid4().hex
        conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES(%s,'mcq','Synthetic calibration item','[\"A\",\"B\"]','B','official')",(q,))
        aid=conn.execute("INSERT INTO attempts(user_id,canonical_id,chosen_text,correct,context,scoring_snapshot,at) VALUES(%s,%s,'B',true,'game',%s,%s) RETURNING id",(user,q,Jsonb({'answer_text':'B','answer_source':'official'}),at)).fetchone()[0]
        conn.execute('INSERT INTO reward_question_claims(user_id,canonical_id,attempt_id) VALUES(%s,%s,%s)',(user,q,aid))
        ledger(user,'question:'+user+':'+q,'study',10,1,at)
        return q,aid
    def review(user,at,q,slot):
        sid='review-'+uuid4().hex;day=at.date()
        conn.execute("INSERT INTO practice_study_sessions(id,user_id,request_key,request_hash,requested_size,question_ids,paper_ids,filters,kind,created_at,finished_at) VALUES(%s,%s,%s,'test',10,%s,%s,'{}','review',%s,%s)",(sid,user,sid,[q],['paper-test'],at,at))
        receipt=ledger(user,f'review:{user}:{day}:{slot}','study',20,2,at)
        conn.execute('INSERT INTO review_session_rewards(session_id,user_id,day,slot,ledger_id) VALUES(%s,%s,%s,%s,%s)',(sid,user,day,slot,receipt[0]))
    def quest(user,at,key,xp,points):
        receipt=ledger(user,f'quest:{user}:{at.date()}:{key}','game',xp,points,at)
        conn.execute('INSERT INTO daily_quest_claims(user_id,ist_date,quest_key,xp_awarded,points_awarded,ledger_id) VALUES(%s,%s,%s,%s,%s,%s)',(user,at.date(),key,receipt[1],receipt[2],receipt[0]))
    def game(user,at,q,daily=False):
        rid='game-'+uuid4().hex;day=at.date();did=day.isoformat() if daily else None
        if daily:conn.execute("INSERT INTO game_dailies(id,opens_at,closes_at,questions) VALUES(%s,%s,%s,'[]') ON CONFLICT DO NOTHING",(did,at-timedelta(hours=6),at+timedelta(hours=18)))
        conn.execute("INSERT INTO game_rooms(id,owner_id,mode,state,capacity,questions,round_seconds,request_key,request_hash,finished_at,daily_id) VALUES(%s,%s,%s,'finished',1,%s,20,%s,'test',%s,%s)",(rid,user,'daily' if daily else 'speed',Jsonb([{'id':q}]),rid,at,did))
        if daily:conn.execute('INSERT INTO game_daily_entries(daily_id,user_id,room_id) VALUES(%s,%s,%s)',(did,user,rid))
        receipt=ledger(user,f'daily:{user}:{did}' if daily else f'game:{user}:{rid}','game',10 if daily else 15,1 if daily else 2,at)
        conn.execute('INSERT INTO game_completion_rewards(room_id,user_id,day,ledger_id) VALUES(%s,%s,%s,%s)',(rid,user,day,receipt[0]))
    with conn.transaction():
        conn.execute('SET LOCAL ROLE mpsc')
        for i,at in enumerate(days):
            for user in (heavy,average):
                for _ in range(12):q,aid=question(user,at)
                review(user,at,q,1);quest(user,at,'warmup_circuit',20,2)
                if user==heavy:
                    review(user,at,q,2);game(user,at,q);game(user,at,q);game(user,at,q,True)
                    quest(user,at,'review_ring',30,3);quest(user,at,'plan_ring',50,5)
                    # A valid extra discovery can still pay XP after12 Learn points.
                    _,heavy_aid=question(user,at)
                elif i<5:game(user,at,q,True)
            if i==0:
                mid='mock-'+uuid4().hex
                conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds,submitted_at,elapsed_seconds,n_correct,n_wrong,n_skipped,score) VALUES(%s,%s,'udc',%s,600,%s,60,1,0,0,1)",(mid,heavy,[q],at))
                receipt=ledger(heavy,f'mock:{heavy}:{mid}','study',30,3,at)
                conn.execute('INSERT INTO mock_completion_rewards(mock_id,user_id,day,ledger_id) VALUES(%s,%s,%s,%s)',(mid,heavy,at.date(),receipt[0]))
                topic='calibration/topic-'+tag
                receipt=ledger(heavy,f'mastery:{heavy}:{topic}:proficient','study',30,3,at,heavy_aid)
                conn.execute("INSERT INTO mastery_milestones(user_id,subject_id,topic,tier,origin,ledger_id,source_attempt_id) VALUES(%s,'english',%s,'proficient','activity',%s,%s)",(heavy,topic,receipt[0],heavy_aid))
    rows=conn.execute("SELECT user_id,(created_at AT TIME ZONE 'Asia/Kolkata')::date,sum(xp)::int,sum(points)::int FROM reward_ledger WHERE user_id=ANY(%s) AND kind IN ('study','game') GROUP BY user_id,2 ORDER BY user_id,2",([heavy,average],)).fetchall()
    heavy_rows=[r[2:] for r in rows if r[0]==heavy];average_rows=[r[2:] for r in rows if r[0]==average]
    assert heavy_rows==[(300,25)]*7
    assert average_rows==[(170,17)]*5+[(160,16)]*2
    # Two real current-day reviewed publication triggers and a true reversal
    # show that reviewed supply remains separate from the historical study week.
    cid,pid=publication(conn,heavy);first=credit(conn,heavy,cid,pid)[0]
    cid2,pid2=publication(conn,heavy,'answer',('reviewer1','reviewer2'));credit(conn,heavy,cid2,pid2)
    reversal='reversal-'+uuid4().hex
    conn.execute("INSERT INTO bank_publications(id,contribution_id,revision,manifest,manifest_hash,exported_by) VALUES(%s,%s,2,%s,%s,'owner')",(reversal,cid2,Jsonb({'payload':{'reverts_publication':pid2}}),'f'*64))
    credit(conn,heavy,cid2,reversal,key=reversal+':reversal:'+pid2,amount=-10)
    assert conn.execute("SELECT sum(xp),sum(points) FROM reward_ledger WHERE user_id=%s AND kind='contribution'",(heavy,)).fetchone()==(20,5)
    assert conn.execute('SELECT sum(points) FROM reward_ledger WHERE user_id=%s',(heavy,)).fetchone()[0]==180
    actor('owner')
    diagnostic=client.get('/api/admin/bank/reward-diagnostics')
    assert diagnostic.status_code==200,diagnostic.text
    integrity={k:v for k,v in diagnostic.json().items() if k not in ('account','legacy_receipts','mail_failed','mail_pending','mail_expired')}
    assert all(v==0 for v in integrity.values()),integrity
    month,week=1500,400
    assert {r[0]:r[1:] for r in conn.execute("SELECT id,points,pro_days,enabled FROM reward_catalog WHERE id IN ('pro-week','pro-month')").fetchall()}=={'pro-month':(month,30,False),'pro-week':(week,7,False)}
    mean=Decimal(117)/7
    report={'fixture':'isolated seven-day source settlement; controllers tested separately','days':7,
      'heavy':{'study_xp':2100,'study_points':175,'daily_points':25,'days_to_month':60,'monthly_rupee_value':50},
      'average':{'study_xp':1170,'study_points':117,'mean_daily_points':float(mean),'days_to_month':float(Decimal(month)/mean)},
      'contributions':{'gross_points':15,'reversed_points':10,'net_points':5,'study_budget_unchanged':True},
      'catalog':{'month_points':month,'week_points':week,'standard_month_paise':10000,'points_per_rupee':15},
      'diagnostics':integrity}
    assert Decimal(89)<Decimal(month)/mean<Decimal(91)
    if target:=os.environ.get('FINNA_CALIBRATION_REPORT'):
        Path(target).write_text(json.dumps(report,indent=2)+'\n')
