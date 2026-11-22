"""Map activity is never a scored canonical attempt or a reward source."""
from copy import deepcopy
from contextlib import asynccontextmanager
from uuid import uuid4
import pytest
from psycopg.types.json import Jsonb
from test_atlas_studio import doc,save,publish,decision

@pytest.fixture(autouse=True)
def case(database,client,monkeypatch):
    from app.db import cursor
    from app.routers import atlas,learning_loop,rewards
    from app.services import atlas_drills
    @asynccontextmanager
    async def role_cursor():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc');yield cur
    monkeypatch.setattr(atlas,'cursor',role_cursor);monkeypatch.setattr(learning_loop,'cursor',role_cursor);monkeypatch.setattr(rewards,'cursor',role_cursor)
    monkeypatch.setattr(atlas_drills,'MIN_SECONDS',0)
    return database[1]

def headers(actor,user='author'):return actor(user)|{'x-learning-user':user}
def authored(client,actor,n=1,line=False):
    d=doc();features=[]
    for i in range(n):features.append({'type':'Feature','id':'pin-'+str(i),'properties':{'name':'Synthetic pin '+str(i),'drillable':True,'toleranceKm':25},'geometry':{'type':'Point','coordinates':[80+i*.01,23]}})
    d['layers'][0]['data']['features']=features
    if line:
        d['layers'][0]['data']['features'].append({'type':'Feature','id':'route','properties':{'name':'Synthetic line'},'geometry':{'type':'LineString','coordinates':[[80,23],[81,23]]}})
        d['drills']=[{'id':'route-drill','layerId':'pins','featureId':'route','prompt':'Find the synthetic route','toleranceKm':20}]
    row=publish(client,actor,save(client,actor,d).json());body=client.get('/api/atlas/chapters/'+d['id']).json()
    return d,row,body['body_hash']

def state(client,actor,d,user='author'):return client.get('/api/atlas/chapters/'+d['id']+'/activity',headers=headers(actor,user))
def start(client,actor,d,h,did=None,key=None,user='author'):
    did=did or 'pin:pins:pin-0';key=key or str(uuid4())
    return client.post('/api/atlas/chapters/'+d['id']+'/drills',headers=headers(actor,user),json={'body_hash':h,'drill_id':did,'request_key':key})
def answer(client,actor,p,lat=23,lng=80,user='author'):return client.post('/api/atlas/drills/'+p['id']+'/answer',headers=headers(actor,user),json={'lat':lat,'lng':lng})
def viewed(client,actor,d,h,layers=['pins']):return client.post('/api/atlas/chapters/'+d['id']+'/viewed',headers=headers(actor),json={'body_hash':h,'layers':layers})
def economic(conn):return tuple(conn.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['attempts','user_topic_mastery','reward_ledger','user_learning_days','review_items','daily_learning_plans','daily_quest_claims'])

def test_issued_presentation_replay_spherical_pin_line_and_no_economic_credit(client,actor,case):
    d,row,h=authored(client,actor,line=True);before=economic(case)
    s=state(client,actor,d);assert s.status_code==200 and len(s.json()['drills'])==2
    assert not {'geometry','answer','target'}&s.json()['drills'][0].keys()
    key=str(uuid4());r=start(client,actor,d,h,key=key);assert r.status_code==200,r.text;p=r.json()
    assert not {'geometry','answer','target'}&p.keys()
    assert start(client,actor,d,h,key=key).json()['id']==p['id']
    assert start(client,actor,d,h,'custom:route-drill',key=key).status_code==409
    assert answer(client,actor,p,user='outsider').status_code==404
    r=answer(client,actor,p);assert r.status_code==200,r.text
    assert r.json()['correct'] and r.json()['xp']==r.json()['points']==0 and not r.json()['mastery_credit']
    assert answer(client,actor,p).json()==r.json()
    assert answer(client,actor,p,lng=82).status_code==409
    line=start(client,actor,d,h,'custom:route-drill').json();assert answer(client,actor,line,lng=80.5).json()['correct']
    assert economic(case)==before
    for table in ('atlas_drill_presentations','atlas_drill_results'):
        with pytest.raises(Exception,match='immutable'):case.execute('UPDATE '+table+' SET user_id=user_id')


def test_viewed_union_explored_only_current_version_and_hold_privacy(client,actor,case):
    d,row,h=authored(client,actor)
    assert not state(client,actor,d).json()['explored']
    assert viewed(client,actor,d,h,['missing']).status_code==422
    assert viewed(client,actor,d,'0'*64).status_code==409
    assert not viewed(client,actor,d,h).json()['explored']
    p=start(client,actor,d,h).json();answer(client,actor,p)
    assert state(client,actor,d).json()['explored']
    assert client.get('/api/atlas/me/progress',headers=headers(actor)).json()['items'][0]['explored']
    assert client.get('/api/atlas/me/progress',headers=headers(actor,'outsider')).json()['items']==[]
    held=decision(client,actor,row,'hold').json()
    assert state(client,actor,d).status_code==404 and answer(client,actor,p).status_code==404
    assert client.get('/api/atlas/me/progress',headers=headers(actor)).json()['items']==[]
    row=decision(client,actor,held,'rollback',revision=1).json()
    d['summary']='A changed synthetic map body requires new exploration.'
    row=publish(client,actor,save(client,actor,d,row['draft_version'],row['lock_version']).json())
    assert answer(client,actor,p).status_code==409
    assert not state(client,actor,d).json()['explored']


def test_wrong_map_tap_suggests_only_live_bound_real_questions_and_embargo(client,actor,case):
    d,row,h=authored(client,actor)
    topic='english/drills-'+uuid4().hex
    case.execute("INSERT INTO review_taxonomy(id,label,parent_id,level,version) VALUES(%s,'Synthetic drill topic','english','topic','test')",(topic,))
    case.execute("UPDATE canonical_questions SET answer_source='official' WHERE id='cq_test'")
    case.execute("UPDATE appearances SET answer_source='official' WHERE canonical_id='cq_test'")
    case.execute("UPDATE question_classifications SET topic_id=%s,review_status='approved' WHERE question_id='cq_test'",(topic,))
    bid=str(uuid4());url='/api/admin/atlas/bindings/'+bid
    assert client.post(url,headers=actor('owner'),json={'expected_version':0,'binding':{'chapter_id':d['id'],'layer_id':'pins','subject_id':'english','topic_id':topic},'reason':'Synthetic fixture only'}).status_code==200
    assert client.post(url+'/decision',headers=actor('owner'),json={'expected_version':1,'action':'publish','reason':'Synthetic fixture only'}).status_code==200
    p=start(client,actor,d,h).json();r=answer(client,actor,p,lat=0,lng=0);assert r.status_code==200 and not r.json()['correct']
    route='/api/atlas/me/suggestions';items=client.get(route,headers=headers(actor)).json()['items'];assert len(items)==1,items
    from urllib.parse import unquote
    assert topic in unquote(items[0]['practice_url']) and items[0]['chapter_id']==d['id']
    assert client.get('/api/me/today',headers=actor('author')).json()['atlas_suggestions']
    mid=uuid4().hex;case.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,'author','udc',%s,600)",(mid,['cq_test']))
    assert client.get(route,headers=headers(actor)).json()['items']==[]
    case.execute('UPDATE mock_sessions SET submitted_at=now(),elapsed_seconds=0,score=0,n_correct=0,n_wrong=0,n_skipped=1 WHERE id=%s',(mid,))
    case.execute("UPDATE papers SET exam_scope_id='outside-mizoram' WHERE id='paper-test'")
    assert client.get(route,headers=headers(actor)).json()['items']==[]
    case.execute("UPDATE papers SET exam_scope_id='mizoram-recruitment' WHERE id='paper-test'")
    case.execute('UPDATE atlas_topic_bindings SET live=NULL WHERE id=%s',(bid,))
    assert client.get(route,headers=headers(actor)).json()['items']==[]


def test_ten_drills_fill_display_ring_but_chest_attempt_mastery_streak_stay_unchanged(client,actor,case):
    d,row,h=authored(client,actor,n=10);before=economic(case)
    for i in range(10):
        p=start(client,actor,d,h,'pin:pins:pin-'+str(i)).json();assert answer(client,actor,p).status_code==200
    r=client.get('/api/rewards/me',headers=actor('author'));assert r.status_code==200,r.text
    q=next(q for q in r.json()['daily_quests']['quests'] if q['key']=='warmup_circuit')
    assert q['progress']==10 and q['completed'] and q['activity_only'] and not q['reward_eligible']
    claim=client.post('/api/rewards/daily-quests/warmup_circuit/claim',headers=actor('author'),json={});assert claim.status_code==409
    assert economic(case)==before


def test_csrf_exact_account_rate_native_validation_and_honest_legacy_empty(client,actor,case,monkeypatch):
    d,row,h=authored(client,actor);headers(actor)
    assert client.get('/api/atlas/chapters/'+d['id']+'/activity',headers={'x-learning-user':'owner'}).status_code==409
    assert client.post('/api/atlas/chapters/'+d['id']+'/viewed',headers={'x-learning-user':'author'},json={'body_hash':h,'layers':['pins']}).status_code==403
    p=start(client,actor,d,h).json()
    r=client.post('/api/atlas/drills/'+p['id']+'/answer',headers=headers(actor),json={'lat':91,'lng':0});assert r.status_code==422
    from app.services import atlas_drills
    monkeypatch.setattr(atlas_drills,'MIN_SECONDS',9999)
    assert answer(client,actor,p).status_code==409
    assert state(client,actor,{'id':'rivers-of-india'}).json()['total_drills']==0
    from app.services.mobile_identity import allowed
    for method,path in [('GET','/api/atlas/me/progress'),('POST','/api/atlas/drills/example/answer'),('GET','/api/atlas/chapters/example/activity')]:assert not allowed(method,path)


@pytest.mark.parametrize('change,field',[
 (lambda d:d['layers'][0]['data']['features'][0]['properties'].update(drillable=True,toleranceKm=0),'toleranceKm'),
 (lambda d:d.update(drills=[{'id':'custom','layerId':'missing','featureId':'missing','prompt':'Find','toleranceKm':20}]),'featureId'),
 (lambda d:d['layers'][0]['data']['features'][0].update(id=None),'id'),
])
def test_bad_drill_authoring_rejected(client,actor,case,change,field):
    d=doc();f=d['layers'][0]['data']['features'][0];f['id']='pin';f['properties'].update(drillable=True,toleranceKm=25);change(d)
    r=save(client,actor,d);assert r.status_code==422 and field in r.text


def test_verified_geography_context_current_binding_scope_and_no_answers(client,actor,case):
    d,row,h=authored(client,actor);topic='english/context-'+uuid4().hex
    case.execute("INSERT INTO review_taxonomy(id,label,parent_id,level,version) VALUES(%s,'Synthetic map context','english','topic','test')",(topic,))
    case.execute("UPDATE question_classifications SET topic_id=%s,review_status='approved' WHERE question_id='cq_test'",(topic,))
    case.execute("UPDATE canonical_questions SET answer_source='official' WHERE id='cq_test'")
    url='/api/admin/atlas/bindings/'+str(uuid4())
    assert client.post(url,headers=actor('owner'),json={'expected_version':0,'binding':{'chapter_id':d['id'],'subject_id':'english','topic_id':topic},'reason':'Synthetic context fixture'}).status_code==200
    assert client.post(url+'/decision',headers=actor('owner'),json={'expected_version':1,'action':'publish','reason':'Synthetic context fixture'}).status_code==200
    path='/api/atlas/questions/cq_test/context';r=client.get(path,headers=actor('author'));assert r.status_code==200,r.text
    assert any(i['body']['id']==d['id'] for i in r.json()['items']) and 'answer_text' not in r.text
    case.execute("UPDATE canonical_questions SET key_disputed=true WHERE id='cq_test'")
    assert client.get(path).json()['items']==[]
    case.execute("UPDATE canonical_questions SET key_disputed=false WHERE id='cq_test'")
    mid=uuid4().hex;case.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,'author','udc',%s,600)",(mid,['cq_test']))
    assert client.get(path).json()['items']==[]
    case.execute('UPDATE mock_sessions SET submitted_at=now(),elapsed_seconds=0,score=0,n_correct=0,n_wrong=0,n_skipped=1 WHERE id=%s',(mid,))
    held=decision(client,actor,row,'hold').json();actor('author')
    assert all(i['body']['id']!=d['id'] for i in client.get(path).json()['items'])
