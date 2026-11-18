"""Real-role calendar composition and compatibility; synthetic data only."""
from datetime import date,timedelta
from uuid import uuid4
from contextlib import asynccontextmanager
import pytest
from app.db import cursor
from app.routers import learning_loop,rewards,games,avatars,calendar_owned
from app.services import calendar_schedule,learning_habit,mastery
from test_learning_loop import run,questions,attempt,due
from test_learning_workflows import learner
from test_owned_calendar import save
from test_profile_cosmetics import funds,buy
from app.services.avatars import DEFAULT

@pytest.fixture(autouse=True)
def mpsc(monkeypatch):
    @asynccontextmanager
    async def app_cursor():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            yield cur
    for module in (learning_loop,rewards,games,avatars,calendar_owned):monkeypatch.setattr(module,'cursor',app_cursor)


def test_legacy_board_selectors_are_empty_and_week_semantics_stay_explicit(client,actor,database):
    user,h=learner(database,actor)
    for path in ('/api/rewards/leaderboard?period=month','/api/rewards/leaderboard?period=all',
                 '/api/games/leaderboard?track=gk_gs','/api/games/leaderboard?track=english',
                 '/api/games/leaderboard?track=everyday_math','/api/games/leaderboard?period=month',
                 '/api/games/leaderboard?cohort=arts-comfort','/api/rewards/leaderboard?offset=20'):
        r=client.get(path,headers=h);assert r.status_code==200,r.text
        assert r.json()['items']==[] and r.json()['retired'] and not r.json()['has_more']
        assert 'private' in r.headers['cache-control']
    for prefix in ('/api/rewards/leaderboard','/api/games/leaderboard'):
        assert client.get(prefix+'?contract=2&period=month',headers=h).status_code==422
        r=client.get(prefix+'?contract=2',headers=h)
        assert r.status_code==200 and r.json()['period']=='week',r.text
        assert r.json()['period_start'] and r.json()['period_end']


def test_legacy_catalog_stays_numeric_and_cannot_replace_newer_saved_look(client,actor,database):
    from test_mobile_companion import connect
    user,h=learner(database,actor);funds(database[1],user,50)
    assert buy(client,h,user).status_code==200
    v2=client.get('/api/me/avatar?catalog_version=2',headers=h).json()
    assert len(v2['catalog'])==29 and len([i for i in v2['catalog'] if i['level'] is None])==3
    look=DEFAULT|{'top':'Plum'}
    assert client.post('/api/me/avatar?catalog_version=2',headers=h,json={'user_id':user,'expected_version':1,'look':look}).status_code==200
    mobile,_=connect(client,actor,user)
    v1=client.get('/api/me/avatar',headers=mobile).json()
    assert len(v1['catalog'])==26 and all(isinstance(i['level'],int) for i in v1['catalog'])
    assert v1['requires_web_editor'] and v1['avatar']==look
    for replacement in (DEFAULT,None,look):
        r=client.post('/api/me/avatar',headers=mobile,json={'user_id':user,'expected_version':2,'look':replacement})
        assert r.status_code==409,r.text
    assert client.get('/api/me/avatar',headers=mobile).json()['avatar_version']==2
    assert client.post('/api/me/avatar/purchase',headers=mobile,json={}).status_code==403


def test_cup_schedule_uses_ist_sundays_inclusive_bounds():
    rows=calendar_schedule.community(date(2026,11,16),date(2026,11,29))
    assert [r['day'] for r in rows]==[date(2026,11,22),date(2026,11,29)]
    for row in rows:
        assert row['starts_at'].hour==19 and row['ends_at']-row['starts_at']==timedelta(hours=1)
        assert row['starts_at'].utcoffset()==timedelta(hours=5,minutes=30)
    assert calendar_schedule.community(date(2026,11,23),date(2026,11,28))==[]
    assert len(calendar_schedule.community(date(2026,11,22),date(2026,11,22)))==1


def test_calendar_and_desk_share_read_projection_guests_official_only(client,actor,database):
    user,h=learner(database,actor);conn=database[1]
    before=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    path='/api/me/calendar-layers?start=2026-11-16&end=2026-11-29'
    for _ in range(2):
        result=client.get(path,headers=h);assert result.status_code==200,result.text
        assert len(result.json()['community'])==2 and result.json()['desk_schedule_available'] is False
    client.cookies.clear()
    guest=client.get(path).json()
    assert not guest['registered'] and guest['community']==[] and guest['occurrences']==[]
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==before


def test_exam_target_taper_scope_boundaries_full_due_and_frozen_plan(client,actor,database):
    user,h=learner(database,actor);conn=database[1];_,ids=questions(database,20)
    topic='taper-'+uuid4().hex
    conn.execute('UPDATE question_classifications SET topic_id=%s WHERE question_id=ANY(%s)',(topic,ids))
    for q in ids[:5]:attempt(conn,user,q,False)
    run(client,mastery.refresh,user);due(conn,user,ids[5:8])
    assert client.put('/api/me/exam-bookmarks/udc/primary',headers=h).status_code==200
    day=conn.execute("SELECT (now() AT TIME ZONE 'Asia/Kolkata')::date").fetchone()[0]
    base=client.get('/api/me/today',headers=h).json()
    assert base['new_questions']['target']==10 and base['exam_preparation'] is None
    cid='other-'+uuid4().hex
    conn.execute("INSERT INTO collections(id,title,kind,visibility) VALUES(%s,'Another exam','exam','public')",(cid,))
    assert save(client,h,kind='exam-target',collection_id=cid,date=(day+timedelta(days=1)).isoformat()).status_code==200
    assert client.get('/api/me/today',headers=h).json()['new_questions']['target']==10
    eid=str(uuid4())
    assert save(client,h,id=eid,kind='exam-target',collection_id='udc',date=(day+timedelta(days=29)).isoformat()).status_code==200
    before=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    for distance,expected in ((29,10),(28,5),(15,5),(14,3),(8,3),(7,0),(0,0)):
        conn.execute('UPDATE calendar_entries SET date=%s WHERE id=%s',(day+timedelta(days=distance),eid))
        p=client.get('/api/me/today',headers=h).json()
        assert p['exam_preparation']['days_remaining']==distance
        assert (p['new_questions']['target'] if p['new_questions'] else 0)==expected
        assert p['due_count']==base['due_count']>=3
    # Past dates and dates on hidden exam scopes must not shape today's plan.
    conn.execute('UPDATE calendar_entries SET date=%s WHERE id=%s',(day-timedelta(days=1),eid))
    assert client.get('/api/me/today',headers=h).json()['exam_preparation'] is None
    conn.execute('UPDATE calendar_entries SET date=%s WHERE id=%s',(day,eid))
    conn.execute("UPDATE collections SET visibility='hidden' WHERE id='udc'")
    assert client.get('/api/me/today',headers=h).json()['exam_preparation'] is None
    conn.execute("UPDATE collections SET visibility='public' WHERE id='udc'")
    run(client,learning_habit.capture_plan,user)
    fixed=client.get('/api/me/today',headers=h).json()
    assert fixed['plan_status']['started'] and fixed['new_questions'] is None
    conn.execute('DELETE FROM calendar_entries WHERE id=%s',(eid,))
    still=client.get('/api/me/today',headers=h).json()
    assert still['exam_preparation']==fixed['exam_preparation'] and still['new_questions'] is None
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==before
