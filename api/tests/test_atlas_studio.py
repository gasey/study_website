"""Chapter publication races, author isolation, exact seed and no economic writes."""
from contextlib import asynccontextmanager
from copy import deepcopy
from pathlib import Path
from uuid import uuid4
import hashlib,json,subprocess
import pytest
from psycopg.types.json import Jsonb

@pytest.fixture(autouse=True)
def case(database,client,monkeypatch):
    from app.db import cursor
    from app.routers import atlas,questions
    @asynccontextmanager
    async def role_cursor():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc');yield cur
    monkeypatch.setattr(atlas,'cursor',role_cursor);monkeypatch.setattr(questions,'cursor',role_cursor)
    return database[1]

def doc():return {'id':'synthetic-'+uuid4().hex,'title':'Synthetic Studio chapter','subject':'geography','unit':'Synthetic QA','summary':'Disposable synthetic chapter for lifecycle tests.','view':{'center':[23,80],'zoom':4},'layers':[{'id':'pins','name':'Synthetic pins','kind':'vector','data':{'type':'FeatureCollection','features':[{'type':'Feature','properties':{'name':'Synthetic pin'},'geometry':{'type':'Point','coordinates':[80,23]}}]},'defaultOn':True}],'facts':[{'id':'fact','text':'Synthetic fixture only'}],'quiz':[],'events':[]}
def save(c,a,d,expected=0,base=0,user='owner'):return c.post('/api/admin/atlas/chapters/'+d['id']+'/draft',headers=a(user),json={'chapter':d,'expected_version':expected,'base_version':base})
def preview(c,a,row,user='owner'):return c.post('/api/admin/atlas/chapters/'+row['id']+'/preview',headers=a(user),json={'expected_version':row['lock_version'],'draft_version':row['draft_version']})
def decision(c,a,row,action='publish',**kw):return c.post('/api/admin/atlas/chapters/'+row['id']+'/decision',headers=a('owner'),json={'expected_version':row['lock_version'],'action':action,'reason':'Synthetic owner publication fixture','draft_version':row['draft_version'],**kw})
def publish(c,a,row):
    p=preview(c,a,row);assert p.status_code==200,p.text
    r=decision(c,a,row,preview_hash=p.json()['body_hash']);assert r.status_code==200,r.text
    return r.json()


def test_exact_26_seed_attribution_no_topic_inference_and_immutable_history(client,actor,case):
    root=Path(__file__).resolve().parents[2]
    subprocess.run(['node',str(root/'scripts/export-atlas-seed.cjs'),'--check'],check=True,capture_output=True)
    manifest=json.loads((root/'api/app/data/atlas-static-catalog.json').read_text())
    seeded=case.execute("SELECT body,body_hash,authored_by,attribution FROM atlas_chapter_versions WHERE revision=1 AND attribution='current-site-content'").fetchall()
    assert len(seeded)==26
    hashes={c['id']:c['source_sha256'] for c in manifest['chapters']}
    from app.services.atlas_studio import validate
    for body,h,author,attribution in seeded:
        assert validate(deepcopy(body))==body and h==hashes[body['id']] and author is None
    assert case.execute('SELECT count(*) FROM atlas_topic_bindings').fetchone()[0]==0
    for table in ('atlas_chapter_versions','atlas_chapter_events'):
        with pytest.raises(Exception,match='immutable'):case.execute('UPDATE '+table+' SET chapter_id=chapter_id')
    assert len(client.get('/api/atlas/chapters').json()['items'])==26
    r=client.get('/api/atlas/chapters/rivers-of-india');assert r.status_code==200 and r.json()['attribution']=='current-site-content'
    assert r.headers['cache-control']=='no-store'


def test_draft_private_autosave_cas_preview_publish_hold_restore_without_rewards(client,actor,case):
    before=case.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    d=doc();r=save(client,actor,d);assert r.status_code==200,r.text;row=r.json()
    assert client.get('/api/atlas/chapters/'+d['id']).status_code==404
    assert save(client,actor,d).status_code==409
    assert decision(client,actor,row,preview_hash='0'*64).status_code==409
    p=preview(client,actor,row);assert p.status_code==200
    d['title']='Updated private draft';row=save(client,actor,d,1,1).json()
    assert decision(client,actor,row,preview_hash=p.json()['body_hash']).status_code==409
    row=publish(client,actor,row);assert row['current_version']==1 and row['lock_version']==2
    assert client.get('/api/atlas/chapters/'+d['id']).json()['body']==d
    d['title']='Unpublished changed title';row=save(client,actor,d,row['draft_version'],row['lock_version']).json()
    assert client.get('/api/atlas/chapters/'+d['id']).json()['body']['title']=='Updated private draft'
    row=publish(client,actor,row);assert row['current_version']==2
    held=decision(client,actor,row,'hold');assert held.status_code==200;row=held.json()
    assert client.get('/api/atlas/chapters/'+d['id']).status_code==404
    assert all(x['id']!=d['id'] for x in client.get('/api/atlas/chapters').json()['items'])
    restored=decision(client,actor,row,'rollback',revision=1);assert restored.status_code==200
    assert client.get('/api/atlas/chapters/'+d['id']).json()['body']['title']=='Updated private draft'
    assert decision(client,actor,row,'rollback',revision=2).status_code==409
    assert case.execute('SELECT count(*) FROM atlas_chapter_versions WHERE chapter_id=%s',(d['id'],)).fetchone()[0]==2
    assert case.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==before


def test_other_owner_drafts_are_private_and_publication_conflict_does_not_overwrite(client,actor,case):
    case.execute("INSERT INTO review_grants(user_id,role,granted_by,reason) VALUES('outsider','owner','test','Synthetic second owner') ON CONFLICT DO NOTHING")
    d=doc();row=save(client,actor,d).json()
    other=client.get('/api/admin/atlas/chapters/'+d['id'],headers=actor('outsider')).json();assert other['body'] is None and other['draft_version']==0
    d2=deepcopy(d);d2['title']='Other owner draft';other=save(client,actor,d2,base=1,user='outsider').json()
    row=publish(client,actor,row)
    assert save(client,actor,d2,1,1,user='outsider').status_code==409
    r=client.get('/api/admin/atlas/chapters/'+d['id'],headers=actor('outsider')).json();assert r['body']['title']=='Other owner draft' and r['draft_base']==1 and r['lock_version']==2
    assert preview(client,actor,r,user='outsider').status_code==409
    # Explicit reconciliation can save the preserved draft against the new base.
    assert save(client,actor,d2,1,2,user='outsider').status_code==200


def test_chapter_change_and_hold_hide_both_binding_directions_new_ids_supported(client,actor,case):
    d=doc();row=publish(client,actor,save(client,actor,d).json())
    topic='english/studio-'+uuid4().hex;case.execute("INSERT INTO review_taxonomy(id,label,parent_id,level,version) VALUES(%s,'Synthetic bound topic','english','topic','test')",(topic,))
    case.execute("UPDATE question_classifications SET topic_id=%s,review_status='approved' WHERE question_id='cq_test'",(topic,))
    bid=str(uuid4());binding={'chapter_id':d['id'],'layer_id':'pins','subject_id':'english','topic_id':topic}
    url='/api/admin/atlas/bindings/'+bid
    assert client.post(url,headers=actor('owner'),json={'expected_version':0,'binding':binding,'reason':'Synthetic binding fixture'}).status_code==200
    assert client.post(url+'/decision',headers=actor('owner'),json={'expected_version':1,'action':'publish','reason':'Synthetic binding fixture'}).status_code==200
    assert client.get('/api/questions',params={'atlas_chapter':d['id'],'atlas_layer':'pins'}).json()['total']==1
    assert client.get('/api/atlas/questions/cq_test/links').json()['items'][0]['title']==d['title']
    held=decision(client,actor,row,'hold').json()
    assert client.get('/api/atlas/questions/cq_test/links').json()['items']==[]
    row=decision(client,actor,held,'rollback',revision=1).json()
    assert client.get('/api/atlas/questions/cq_test/links').json()['items']
    d['title']='Changed map content';row=save(client,actor,d,row['draft_version'],row['lock_version']).json();row=publish(client,actor,row)
    assert client.get('/api/questions',params={'atlas_chapter':d['id']}).json()['total']==0
    assert client.get('/api/atlas/questions/cq_test/links').json()['items']==[]


@pytest.mark.parametrize('change,field',[
    (lambda d:d.update(title=''),'title'),(lambda d:d.update(layers=[]),'layers'),
    (lambda d:d['view'].update(center=[100,0]),'view'),
    (lambda d:d['layers'][0]['data']['features'][0]['geometry'].update(coordinates=[181,0]),'geometry'),
    (lambda d:d.update(events=[{'id':'ev','label':'Event','date':'2026','showLayers':['missing']}]),'showLayers'),
    (lambda d:d.update(facts=[None]),'facts'),(lambda d:d.pop('facts'),'facts'),
    (lambda d:d.update(quiz=[{'id':'quiz','type':'map_click','question':'Locate','answer':{'lat':23,'lng':80,'toleranceKm':0}}]),'toleranceKm'),
    (lambda d:d['layers'][0].update(style={'color':'url(https://example.test)'}),'color'),
])
def test_validation_has_field_errors_and_cannot_publish_malformed_geometry(client,actor,case,change,field):
    d=doc();change(d);r=save(client,actor,d);assert r.status_code==422,r.text
    assert field in r.text
    assert not case.execute('SELECT 1 FROM atlas_chapters WHERE id=%s',(d['id'],)).fetchone()


def test_auth_mfa_csrf_native_and_owner_attribution(client,actor,case,monkeypatch):
    for user in ('author','reviewer1','reviewer2'):
        assert client.get('/api/admin/atlas/chapters',headers=actor(user)).status_code==403
    actor('owner');d=doc()
    assert client.post('/api/admin/atlas/chapters/'+d['id']+'/draft',json={'chapter':d,'expected_version':0,'base_version':0}).status_code==403
    from app.config import settings
    monkeypatch.setattr(settings,'mfa_enforce_staff',True);monkeypatch.setattr(settings,'staff_mfa_exempt_user_ids','')
    assert client.get('/api/admin/atlas/chapters',headers=actor('owner')).status_code==403
    monkeypatch.setattr(settings,'staff_mfa_exempt_user_ids','owner')
    assert client.get('/api/admin/atlas/chapters',headers=actor('owner')).status_code==200
    row=publish(client,actor,save(client,actor,d).json())
    assert row['versions'][0]['attribution']=='owner' and row['versions'][0]['authored_by']=='owner'
    from app.services.mobile_identity import allowed
    for method,path in [('GET','/api/atlas/chapters'),('GET','/api/atlas/chapters/'+d['id']),('POST','/api/admin/atlas/chapters/'+d['id']+'/draft')]:assert not allowed(method,path)
