"""Module composition only changes explicit versioned selection, not source work."""
from uuid import uuid4
from psycopg.types.json import Jsonb
from test_editorial_assignments import source

ROOT='/api/editorial/module-setup/'

def create(client,actor,name=None):
    h=actor('owner');name=name or 'test-'+uuid4().hex[:12]
    r=client.post(ROOT+'create',headers=h,json={'id':name,'title':'Synthetic compiled exam','source_module':'udc'})
    assert r.status_code==200,r.text
    return name,h

def save(client,h,name,papers,modules=None,excluded=None):
    d=client.get(ROOT+name).json()['draft']
    r=client.post(ROOT+name+'/draft',headers=h,json={**d,'selection':{'papers':papers,'modules':modules or [],'excluded_papers':excluded or []}})
    assert r.status_code==200,r.text
    r=client.post(ROOT+name+'/preview',headers=h,json={});assert r.status_code==200,r.text
    return r.json()

def publish(client,h,name,p):
    b={'revision':p['revision'],'token':p['token'],'reason':'Selected the exact source papers for this exam module.','request_key':uuid4().hex}
    r=client.post(ROOT+name+'/publish',headers=h,json=b);assert r.status_code==200,r.text
    return r,b

def test_create_preview_publish_and_idempotency(client,actor,source,database):
    name,h=create(client,actor);pid,qid,aid=source;c=database[1]
    before=c.execute('SELECT count(*) FROM editorial_checks').fetchone()[0]
    p=save(client,h,name,[pid]);assert p['before']['appearances']==0 and p['after']['appearances']==1
    assert c.execute('SELECT visibility FROM collections WHERE id=%s',(name,)).fetchone()[0]=='hidden'
    r,b=publish(client,h,name,p);assert r.json()['version']==1
    assert client.post(ROOT+name+'/publish',headers=h,json=b).json()['replayed']
    assert c.execute('SELECT count(*) FROM module_composition_history WHERE collection_id=%s',(name,)).fetchone()[0]==1
    scope=client.get('/api/editorial/scope',params={'scope':'module:'+name}).json()
    assert scope['summary']['appearances']==p['after']['appearances']
    assert c.execute('SELECT count(*) FROM editorial_checks').fetchone()[0]==before
    actor('outsider');assert client.get('/api/collections/'+name).status_code==200


def test_owner_permission_and_csrf(client,actor,source):
    h=actor('reviewer1');assert client.get(ROOT+'catalog').status_code==403
    assert client.post(ROOT+'create',headers=h,json={'id':'no-access','title':'No permission','source_module':'udc'}).status_code==403
    actor('owner');assert client.post(ROOT+'create',json={'id':'no-csrf','title':'No permission','source_module':'udc'}).status_code==403


def test_stale_draft_preview_and_key_rejected(client,actor,source,database):
    name,h=create(client,actor);p=save(client,h,name,[source[0]])
    d=client.get(ROOT+name).json()['draft'];assert client.post(ROOT+name+'/draft',headers=h,json=d).status_code==200
    b={'revision':p['revision'],'token':p['token'],'reason':'A meaningful explanation of this selection.','request_key':uuid4().hex}
    assert client.post(ROOT+name+'/publish',headers=h,json=b).status_code==409
    assert client.post(ROOT+name+'/draft',headers=h,json=d).status_code==409
    p=client.post(ROOT+name+'/preview',headers=h,json={}).json()
    database[1].execute("UPDATE appearances SET question='Changed preview source' WHERE id=%s",(source[2],))
    # Wording is source work, not membership: changing it does not certify it.
    r,b=publish(client,h,name,p)
    assert client.post(ROOT+name+'/publish',headers=h,json={**b,'reason':'Different publication reason requested'}).status_code==409


def test_membership_drift_requires_new_preview(client,actor,source,database):
    name,h=create(client,actor);p=save(client,h,name,[source[0]])
    c=database[1];c.execute("INSERT INTO appearances(id,paper_id,type,question,options,canonical_id) VALUES(%s,%s,'mcq','Extra source','[]',%s)",(uuid4().hex,source[0],source[1]))
    r=client.post(ROOT+name+'/publish',headers=h,json={'revision':p['revision'],'token':p['token'],'reason':'Selected sources for the new module.','request_key':uuid4().hex})
    assert r.status_code==409,r.text


def test_snapshot_sources_exclusions_and_cycles(client,actor,source,database):
    a,h=create(client,actor);publish(client,h,a,save(client,h,a,[source[0],'paper-test']))
    b,h=create(client,actor);p=save(client,h,b,[],[a],['paper-test']);assert p['after']['papers']==1
    publish(client,h,b,p)
    d=client.get(ROOT+a).json()['draft'];d['selection']={'papers':[source[0]],'modules':[b],'excluded_papers':[]}
    assert client.post(ROOT+a+'/draft',headers=h,json=d).status_code==422
    # Publishing a source change does not silently alter its existing compilation.
    publish(client,h,a,save(client,h,a,['paper-test']))
    c=database[1];version=c.execute('SELECT live_version FROM collections WHERE id=%s',(b,)).fetchone()[0]
    assert c.execute('SELECT paper_id FROM collection_papers WHERE collection_id=%s AND version=%s',(b,version)).fetchall()==[(source[0],)]


def test_unknown_cross_scope_and_empty_selection(client,actor,source,database):
    name,h=create(client,actor);d=client.get(ROOT+name).json()['draft']
    for selection in [{'papers':[]},{'papers':['missing-source']},{'modules':[name]},{'modules':['unknown-module']}]:
        r=client.post(ROOT+name+'/draft',headers=h,json={**d,'selection':selection});assert r.status_code in (404,422),r.text
    database[1].execute("INSERT INTO papers(id,exam_type,exam_name,exam_scope_id) VALUES ('cross-scope-composer','Community','Other bank',NULL)")
    assert client.post(ROOT+name+'/draft',headers=h,json={**d,'selection':{'papers':['cross-scope-composer']}}).status_code==422


def test_preserves_history_assignment_and_paper_rules(client,actor,source,database):
    name,h=create(client,actor);c=database[1];p=save(client,h,name,[source[0]])
    publish(client,h,name,p)
    c.execute('UPDATE collection_papers SET as_mock=false,marks_wrong=0.25,allow_practice=false WHERE collection_id=%s',(name,))
    before=c.execute('SELECT count(*) FROM editorial_assignment_papers').fetchone()[0]
    p=save(client,h,name,[source[0],'paper-test']);publish(client,h,name,p)
    rows=c.execute('SELECT version,marks_wrong,allow_practice FROM collection_papers WHERE collection_id=%s AND paper_id=%s ORDER BY version',(name,source[0])).fetchall()
    assert len(rows)==2 and all(float(r[1])==.25 and r[2] is False for r in rows)
    assert c.execute('SELECT count(*) FROM editorial_assignment_papers').fetchone()[0]==before


def test_section_filters_retained_and_preview_matches_scope(client,actor,source,database):
    name,h=create(client,actor);publish(client,h,name,save(client,h,name,[source[0],'paper-test']))
    c=database[1];c.execute("INSERT INTO collection_sections(collection_id,version,path,title,position,query,pins,excludes) VALUES(%s,1,'english','English',2,%s,%s,%s)",(name,Jsonb({'paper_ids':[source[0]],'subject_id':'english'}),[source[1]],['cq_test']))
    p=save(client,h,name,['paper-test']);publish(client,h,name,p)
    section=c.execute("SELECT query,pins,excludes FROM collection_sections WHERE collection_id=%s AND version=2 AND path='english'",(name,)).fetchone()
    assert section[0]['subject_id']=='english' and section[0]['paper_ids']==[] and section[1]==[] and section[2]==['cq_test']
    overview=client.get('/api/editorial/scope',params={'scope':'module:'+name}).json();assert overview['summary']['appearances']==p['after']['appearances']


def test_mfa_required_for_owner_mutations(client,actor):
    from app.config import settings
    h=actor('owner');prior=settings.mfa_enforce_staff
    try:
        settings.mfa_enforce_staff=True
        assert client.get(ROOT+'catalog').status_code==200
        r=client.post(ROOT+'create',headers=h,json={'id':'mfa-needed','title':'MFA required','source_module':'udc'})
        assert r.status_code==403 and 'authenticator' in r.text
    finally:settings.mfa_enforce_staff=prior


def test_removed_paper_not_reintroduced_by_shared_pin(client,actor,source,database):
    name,h=create(client,actor);publish(client,h,name,save(client,h,name,[source[0],'paper-test']))
    c=database[1]
    c.execute("INSERT INTO appearances(id,paper_id,type,question,options,canonical_id) VALUES(%s,'paper-test','mcq','Shared variant','[]',%s)",(uuid4().hex,source[1]))
    c.execute("INSERT INTO collection_sections(collection_id,version,path,title,position,query,pins) VALUES(%s,1,'curated','Curated',2,%s,%s)",(name,Jsonb({'paper_ids':[]}),[source[1]]))
    p=save(client,h,name,['paper-test']);publish(client,h,name,p)
    items=client.get('/api/editorial/scope',params={'scope':'module:'+name}).json()['items']
    assert all(x['id']!=source[0] for x in items)


def test_unchanged_filtered_sections_outside_library_preserved(client,actor,source,database):
    name,h=create(client,actor);publish(client,h,name,save(client,h,name,['paper-test']))
    c=database[1];c.execute("INSERT INTO collection_sections(collection_id,version,path,title,position,query,pins) VALUES(%s,1,'filtered','Selected English',2,%s,%s)",(name,Jsonb({'paper_ids':[source[0]],'subject_id':'english'}),[source[1]]))
    p=save(client,h,name,['paper-test']);assert p['added_appearances']==p['removed_appearances']==0
    publish(client,h,name,p)
    q,pins=c.execute("SELECT query,pins FROM collection_sections WHERE collection_id=%s AND version=2 AND path='filtered'",(name,)).fetchone()
    assert q['paper_ids']==[source[0]] and pins==[source[1]]
    c.execute("UPDATE collections SET visibility='pro' WHERE id=%s",(name,))
    assert client.get(ROOT+name).status_code==422
