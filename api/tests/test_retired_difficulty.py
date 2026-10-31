from uuid import uuid4
from app.services.review_policy import Proposal
from test_bank_review import proposal
from psycopg.types.json import Jsonb
from app.services.review_policy import digest

def tags():
    p=proposal('taxonomy');p['patch']={'classification':{'subject_id':'mizo'}};p['subject_id']='mizo'
    return p

def test_subject_tags_work_without_difficulty_and_new_edits_reject(client,actor):
    h=actor('author');p=tags()
    r=client.post('/api/contributions',headers={**h,'Idempotency-Key':uuid4().hex},json=p)
    assert r.status_code==201,r.text
    cid=r.json()['id'];version=r.json()['lock_version']
    for value in ['easy','medium','hard',None]:
        old={**p,'patch':{**p['patch'],'difficulty':value}}
        # Historical payloads remain parseable, but cannot be authored anew.
        assert Proposal.model_validate(old).patch['difficulty']==value
        bad=client.post('/api/contributions',headers={**h,'Idempotency-Key':uuid4().hex},json=old)
        assert bad.status_code==422 and 'retired' in bad.text
        bad=client.post('/api/contributions/'+cid+'/revisions',headers=h,json={'expected_version':version,'proposal':old})
        assert bad.status_code==422 and 'retired' in bad.text
    detail=client.get('/api/contributions/'+cid).json()
    assert detail['revision']==1 and detail['current']['payload']['patch']==p['patch']
    good=client.post('/api/contributions/'+cid+'/revisions',headers=h,json={'expected_version':version,'proposal':p})
    assert good.status_code==200,good.text

def test_old_difficulty_revision_is_readable_but_must_be_revised(client,actor,database):
    h=actor('author');p=tags()
    r=client.post('/api/contributions',headers={**h,'Idempotency-Key':uuid4().hex},json=p);assert r.status_code==201,r.text
    cid=r.json()['id'];d=client.get('/api/contributions/'+cid).json();baseline=d['current']['baseline']
    old={**p,'patch':{**p['patch'],'difficulty':'hard'}}
    conn=database[1]
    conn.execute('INSERT INTO contribution_revisions(contribution_id,revision,payload,baseline,baseline_hash,actor_id) VALUES(%s,2,%s,%s,%s,%s)',(cid,Jsonb(old),Jsonb(baseline),digest(baseline),'author'))
    conn.execute('UPDATE bank_contributions SET revision=2 WHERE id=%s',(cid,))
    d=client.get('/api/contributions/'+cid).json();assert d['current']['payload']['patch']['difficulty']=='hard'
    r=client.post('/api/contributions/'+cid+'/submit',headers=h,json={'expected_version':d['lock_version']})
    assert r.status_code==422 and 'retired' in r.text
    r=client.post('/api/contributions/'+cid+'/revisions',headers=h,json={'expected_version':d['lock_version'],'proposal':p})
    assert r.status_code==200,r.text
    d=client.get('/api/contributions/'+cid).json();assert 'difficulty' not in d['current']['payload']['patch']
