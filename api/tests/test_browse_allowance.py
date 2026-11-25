"""Real PostgreSQL allowance, replay/cap, identity and transaction boundaries."""
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from app.services.browse_allowance import ACTION, allowance, power_filter, query_key
from test_learning_workflows import learner


@pytest.mark.parametrize('query,expected', [
    ({},False), ({'subject_id':'english','year_from':2020},False),
    ({'topic_id':'english/vocabulary'},False),
    ({'topic_id':['english/vocabulary'],'year_to':['2020']},True),
    ({'year_from':2020,'source':['official']},True),
    ({'topic_id':'english/vocabulary','pool':'practice'},False),
    ({'topic_id':'english/vocabulary','pool':'scorable'},True),
    ({'exam_scope':'all','subject_id':'english'},True),
    ({'exam_scope':'all','paper_id':'source'},False),
])
def test_power_categories(query,expected):
    assert power_filter(query)==expected


def test_keys_ignore_pagination_sort_and_equivalent_source_order():
    original={'topic_id':'english/vocabulary','year_from':2020,'source':['official','key'],'q':'Words'}
    assert query_key(original)==query_key({**original,'source':['key','official','key'],'q':'words',
        'offset':25,'limit':1,'seed':'other','order':'mixed','study_status':'answered'})
    assert query_key(original)!=query_key({**original,'year_from':2021})


def search(client,**extra):
    return client.get('/api/questions',params={'topic_id':'english/synthetic','year_from':2020,**extra})


def test_guest_exclusion_basic_reads_and_no_awards(client,database):
    conn=database[1];before=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    client.cookies.clear()
    assert client.get('/api/questions?subject_id=english&year_from=2020').status_code==200
    denied=search(client)
    assert denied.status_code==401 and 'Sign in' in denied.json()['detail']
    assert denied.headers['cache-control']=='private, no-store' and 'etag' not in denied.headers
    status=client.get('/api/me/browse-allowance').json()
    assert status['tier']=='guest' and status['remaining']==0
    assert conn.execute('SELECT count(*) FROM rate_limits').fetchone()[0]==0
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==before


def test_three_queries_retry_pagination_cap_and_account_isolation(client,actor,database):
    user,_=learner(database,actor)
    for i in range(3):
        result=search(client,q='combination-'+str(i))
        assert result.status_code==200,result.text
        assert result.json()['browse_allowance']['used']==i+1
        assert result.headers['cache-control']=='private, no-store' and 'etag' not in result.headers
    assert search(client,q='combination-extra').status_code==403
    replay=search(client,q='combination-0',limit=1,offset=25,order='mixed',seed='stable')
    assert replay.status_code==200 and replay.json()['browse_allowance']['used']==3
    assert client.get('/api/questions?subject_id=english&year_from=2020').status_code==200
    assert client.get('/api/questions/cq_test').status_code==200,'Opened questions remain readable after the cap'
    _,_=learner(database,actor)
    assert client.get('/api/me/browse-allowance').json()['used']==0
    assert search(client).status_code==200
    assert database[1].execute('SELECT cardinality(request_keys) FROM rate_limits WHERE user_id=%s',(user,)).fetchone()[0]==3


def test_concurrent_distinct_queries_cannot_exceed_cap(client,actor,database):
    user,_=learner(database,actor)
    with ThreadPoolExecutor(max_workers=6) as executor:
        responses=list(executor.map(lambda i:search(client,q='concurrent-'+str(i)),range(6)))
    assert sorted(r.status_code for r in responses)==[200,200,200,403,403,403]
    assert client.get('/api/me/browse-allowance').json()['used']==3
    assert database[1].execute('SELECT cardinality(request_keys) FROM rate_limits WHERE user_id=%s',(user,)).fetchone()[0]==3


def test_concurrent_replay_costs_once(client,actor,database):
    learner(database,actor)
    with ThreadPoolExecutor(max_workers=5) as executor:
        responses=list(executor.map(lambda _:search(client),range(5)))
    assert all(r.status_code==200 for r in responses)
    assert client.get('/api/me/browse-allowance').json()['used']==1


def test_ist_day_reset_and_granted_pro_share_billing_truth(client,actor,database):
    user,_=learner(database,actor);conn=database[1]
    conn.execute("""INSERT INTO rate_limits(user_id,action,ist_date,request_keys)
        VALUES(%s,%s,(now() AT TIME ZONE 'Asia/Kolkata')::date-1,ARRAY['a','b','c'])""",(user,ACTION))
    assert client.get('/api/me/browse-allowance').json()['used']==0
    assert search(client).json()['browse_allowance']['used']==1
    conn.execute('''INSERT INTO billing_access_grants(user_id,granted_by,idempotency_key,days,starts_at,ends_at)
        VALUES(%s,'owner',%s,1,now(),now()+interval '1 day')''',(user,uuid4().hex))
    for i in range(5):assert search(client,q='pro-'+str(i)).status_code==200
    status=client.get('/api/me/browse-allowance').json()
    assert status['unlimited'] and status['tier']=='pro' and status['limit'] is None
    assert status['used']==1,'Pro does not consume the free allowance'
    assert conn.execute('SELECT plan_code FROM users WHERE id=%s',(user,)).fetchone()[0]=='free'


def test_invalid_queries_and_rolled_back_reads_do_not_consume(client,actor,database):
    user,_=learner(database,actor)
    assert search(client,order='mixed',seed='bad;seed').status_code==422
    assert client.get('/api/me/browse-allowance').json()['used']==0
    async def fail():
        from app.db import cursor
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            result=await allowance(cur,user,request_key='synthetic-rollback')
            assert result['used']==1
            raise RuntimeError('Abort the read transaction')
    with pytest.raises(RuntimeError):client.portal.call(fail)
    assert client.get('/api/me/browse-allowance').json()['used']==0
