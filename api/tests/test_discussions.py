from test_account_hardening import headers as account_headers
"""Discussion gates, moderation, canonical identity and evidence handoff."""
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from psycopg.types.json import Jsonb

@pytest.fixture
def question(database):
    _,conn=database;qid='cq_disc_'+uuid4().hex[:12];aid='a_'+qid
    conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES(%s,'mcq','Synthetic discussion question?',%s,'B','derived')",(qid,Jsonb(['A','B','C','D'])))
    conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary,qnum,page) VALUES(%s,'paper-test','mcq','Synthetic discussion question?',%s,1,'derived',%s,true,'7',2)",(aid,Jsonb(['A','B','C','D']),qid))
    conn.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,taxonomy_version,source,review_status) VALUES(%s,'english','English','test','manual','approved')",(qid,))
    yield qid,conn

def answer(client,actor,qid,user):
    h=actor(user);r=client.post('/api/questions/'+qid+'/answer', headers=account_headers(client),json={'chosen_index':1});assert r.status_code==200,r.text
    return h

def create(client,h,qid,body='Why does this synthetic question use option B?',kind='doubt',parent=None,key=None,sources=None,context=None):
    return client.post('/api/community/questions/'+qid+'/discussion',headers={**h,'idempotency-key':key or uuid4().hex},json={'kind':kind,'body':body,'parent_id':parent,'sources':sources or [],'context':context or {}})

def approve(client,actor,pid):
    h=actor('owner');r=client.post(f'/api/community/admin/posts/{pid}/action',headers=h,json={'action':'approve'});assert r.status_code==200 or (r.status_code==409 and r.json()['detail']=='post is no longer awaiting approval'),r.text

def test_gate_first_posts_csrf_replay_and_mock(client,actor,question):
    qid,conn=question;h=actor('author')
    r=client.get(f'/api/community/questions/{qid}/discussion');assert not r.json()['allowed'];assert r.headers['cache-control']=='private, no-store'
    assert create(client,h,qid).status_code==403
    assert client.post(f'/api/community/questions/{qid}/discussion/open',headers=h,json={}).status_code==403
    h=answer(client,actor,qid,'author')
    assert create(client,{},qid).status_code==403
    key=uuid4().hex
    with ThreadPoolExecutor(max_workers=3) as pool:rs=list(pool.map(lambda _:create(client,h,qid,key=key),range(3)))
    assert all(r.status_code==201 for r in rs),[r.text for r in rs]
    pid=rs[0].json()['id'];assert len({r.json()['id'] for r in rs})==1
    assert create(client,h,qid,body='Another different body for replay conflict.',key=key).status_code==409
    assert client.get(f'/api/community/questions/{qid}/discussion').json()['items'][0]['needs_approval']
    answer(client,actor,qid,'outsider');assert not client.get(f'/api/community/questions/{qid}/discussion').json()['items']
    assert client.get(f'/api/community/posts/{pid}/replies').status_code==404
    approve(client,actor,pid);h=actor('author');assert client.get(f'/api/community/questions/{qid}/discussion').json()['items']
    cid='disc_'+uuid4().hex;mid='m_'+cid
    conn.execute("INSERT INTO collections(id,title,kind,visibility) VALUES(%s,'Synthetic discussion mock','exam','public')",(cid,))
    conn.execute('INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,\'author\',%s,%s,600)',(mid,cid,[qid]))
    try:
        assert client.get(f'/api/community/questions/{qid}/discussion').status_code==409
        assert client.get(f'/api/community/posts/{pid}/evidence').status_code==409
        assert create(client,h,qid).status_code==409
        assert qid not in [r['question_id'] for r in client.get('/api/community/feed').json()['items']]
        assert qid not in [r['question_id'] for r in client.get('/api/community/feed?tab=questions&discussion=unanswered').json()['items']]
    finally:conn.execute('DELETE FROM mock_sessions WHERE id=%s',(mid,))

def test_sources_context_replies_accept_votes_notifications(client,actor,question):
    qid,conn=question;h=answer(client,actor,qid,'author');source={'url':'https://example.test/source','note':'Synthetic primary reference'}
    r=create(client,h,qid,sources=[source],context={'paper_id':'paper-test'});assert r.status_code==201,r.text;pid=r.json()['id'];approve(client,actor,pid)
    h=answer(client,actor,qid,'outsider');r=create(client,h,qid,kind='reply',parent=pid,body='The synthetic reference explains option B clearly.',sources=[source]);assert r.status_code==201,r.text;reply=r.json()['id']
    assert not conn.execute('SELECT 1 FROM review_notifications WHERE discussion_post_id=%s',(reply,)).fetchone()
    approve(client,actor,reply)
    assert conn.execute("SELECT count(*) FROM review_notifications WHERE discussion_post_id=%s AND user_id='author'",(reply,)).fetchone()[0]==1
    h=actor('outsider');assert client.post(f'/api/community/posts/{reply}/accept',headers=h,json={'enabled':True}).status_code==403
    h=actor('author');assert client.post(f'/api/community/posts/{reply}/accept',headers=h,json={'enabled':True}).status_code==200
    assert client.post(f'/api/community/posts/{pid}/helpful',headers=h,json={'enabled':True}).status_code==403
    before=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    for _ in range(2):assert client.post(f'/api/community/posts/{reply}/helpful',headers=h,json={'enabled':True}).status_code==200
    assert client.get(f'/api/community/posts/{pid}/replies').json()['items'][0]['accepted']
    assert client.get(f'/api/community/posts/{pid}/replies?focus={reply}').json()['focused']['id']==reply
    evidence=client.get(f'/api/community/posts/{reply}/evidence').json();assert evidence['source_links']==[source];assert evidence['source_context']['paper_id']=='paper-test';assert str(reply) in evidence['citation_path']
    feed=[p for p in client.get('/api/community/feed').json()['items'] if p['id']==pid];assert feed[0]['accepted_answer'].startswith('The synthetic reference')
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==before
    assert client.get(f'/api/community/questions/{qid}/discussion?focus={reply}').json()['focused']['id']==pid
    assert client.post(f'/api/community/posts/{reply}/accept',headers=h,json={'enabled':False}).status_code==200
    with pytest.raises(Exception,match='immutable'):
        with conn.transaction():conn.execute("UPDATE posts SET body='tampered content' WHERE id=%s",(pid,))

def test_unscored_descriptive_disclosure_guest_no_fake_attempt(client,actor,question):
    qid,conn=question;conn.execute('UPDATE canonical_questions SET answer_text=NULL,answer_source=\'none\' WHERE id=%s',(qid,))
    h=actor('author');before=conn.execute('SELECT count(*) FROM attempts WHERE canonical_id=%s',(qid,)).fetchone()[0]
    r=client.get(f'/api/community/questions/{qid}/discussion').json();assert r['can_disclose']
    assert client.post(f'/api/community/questions/{qid}/discussion/open',headers=h,json={}).status_code==200
    assert create(client,h,qid).status_code==201
    assert conn.execute('SELECT count(*) FROM attempts WHERE canonical_id=%s',(qid,)).fetchone()[0]==before
    conn.execute("UPDATE canonical_questions SET type='descriptive' WHERE id=%s",(qid,))
    assert client.get(f'/api/community/questions/{qid}/discussion').json()['allowed']
    client.cookies.clear();guest={'X-Device-Id':'11111111-1111-4111-8111-111111111111'}
    assert client.post(f'/api/community/questions/{qid}/discussion/open',headers=guest,json={}).status_code==401
    assert client.post(f'/api/community/questions/{qid}/discussion',headers=guest,json={}).status_code==401

def test_moderation_blocks_reports_lock_withdraw(client,actor,question):
    qid,conn=question;h=answer(client,actor,qid,'author');r=create(client,h,qid);pid=r.json()['id'];approve(client,actor,pid)
    h=answer(client,actor,qid,'outsider');assert client.get('/api/community/admin/queue').status_code==403
    assert client.post(f'/api/community/posts/{pid}/report',headers=h,json={'reason':'spam','note':'Synthetic conduct report, not an answer judgement.'}).status_code==200
    assert client.post(f'/api/community/posts/{pid}/report',headers=h,json={'reason':'spam','note':'The same reporter cannot add weight twice.'}).status_code==200
    assert conn.execute('SELECT count(*) FROM abuse_reports WHERE post_id=%s',(pid,)).fetchone()[0]==1
    h=actor('owner');assert any(p['post_id']==pid for p in client.get('/api/community/admin/queue?tab=Reported').json()['items'])
    assert client.post(f'/api/community/admin/posts/{pid}/action',headers=h,json={'action':'hide','note':'Synthetic conduct violation confirmed.'}).status_code==200
    h=actor('outsider');assert client.get(f'/api/community/posts/{pid}/evidence').status_code==404
    h=actor('author');r=create(client,h,qid,body='Another synthetic topic with useful details.');pid2=r.json()['id'];approve(client,actor,pid2)
    h=actor('outsider');assert client.post('/api/creators/author/block',headers=h,json={'enabled':True}).status_code==200
    assert not client.get(f'/api/community/questions/{qid}/discussion').json()['items']
    assert client.get(f'/api/community/posts/{pid2}/replies').status_code==404
    assert qid not in [p['question_id'] for p in client.get('/api/community/feed').json()['items']]
    client.post('/api/creators/author/block',headers=h,json={'enabled':False})
    h=actor('owner');assert client.post(f'/api/community/admin/questions/{qid}/lock',headers=h,json={'enabled':True,'reason':'Pause this synthetic discussion for review.'}).status_code==200
    h=actor('author');assert create(client,h,qid).status_code==409
    assert client.get(f'/api/community/questions/{qid}/discussion').json()['locked']
    assert client.post(f'/api/community/posts/{pid2}/withdraw',headers=h,json={}).status_code==200
    assert not client.get(f'/api/community/questions/{qid}/discussion').json()['items']

def test_validation_pagination_and_cross_question(client,actor,question):
    qid,conn=question;h=answer(client,actor,qid,'author')
    assert create(client,h,qid,context={'paper_id':'not-a-paper'}).status_code==422
    assert create(client,h,qid,sources=[{'url':'javascript:alert(1)','note':'Unsafe source'}]).status_code==422
    assert create(client,h,qid,body='    ').status_code==422
    assert create(client,h,qid,parent=123).status_code==422
    pids=[create(client,h,qid,body='Synthetic pagination topic number '+str(i)).json()['id'] for i in range(3)]
    page=client.get(f'/api/community/questions/{qid}/discussion?limit=2').json();assert len(page['items'])==2 and page['has_more']
    second=client.get(f'/api/community/questions/{qid}/discussion?limit=2&offset=2').json();assert len(second['items'])==1 and not second['has_more']
    answer(client,actor,'cq_test','author')
    assert client.get(f'/api/community/questions/cq_test/discussion?focus={pids[0]}').status_code==404
    assert create(client,h,qid,kind='reply',parent=pids[0]).status_code==422
    assert client.post(f'/api/community/questions/{qid}/discussion',headers={**h,'idempotency-key':uuid4().hex},content='"'+'x'*70000+'"').status_code==413

def test_report_auto_hide_and_muted_accounts(client,actor,question):
    qid,conn=question;h=answer(client,actor,qid,'author');pid=create(client,h,qid).json()['id'];approve(client,actor,pid)
    for user in ['outsider','reviewer1','reviewer2','owner']:
        h=answer(client,actor,qid,user)
        assert client.post(f'/api/community/posts/{pid}/report',headers=h,json={'reason':'spam','note':'Independent synthetic conduct report.'}).status_code==200
    conn.execute("INSERT INTO users(id,handle,email) VALUES('discussion-report5','discussion-report5','discussion-report5@example.test') ON CONFLICT DO NOTHING")
    conn.execute("INSERT INTO abuse_reports(post_id,reason,reporter_id,weight,note) VALUES(%s,'spam','discussion-report5',1,'Fifth independent synthetic report')",(pid,))
    assert conn.execute('SELECT hidden FROM posts WHERE id=%s',(pid,)).fetchone()[0]
    assert client.get(f'/api/community/posts/{pid}/replies').status_code==404
    h=actor('owner');assert client.post(f'/api/community/admin/posts/{pid}/action',headers=h,json={'action':'dismiss','note':'Synthetic evidence shows no conduct violation.'}).status_code==200
    assert not conn.execute('SELECT hidden FROM posts WHERE id=%s',(pid,)).fetchone()[0]
    action=conn.execute("INSERT INTO mod_actions(actor_id,action,target_user,note) VALUES('owner','mute','outsider','Synthetic restriction') RETURNING id").fetchone()[0]
    conn.execute("INSERT INTO sanctions(user_id,kind,step,ends_at,action_id) VALUES('outsider','mute',1,now()+interval '1 hour',%s)",(action,))
    try:
        h=actor('outsider');assert create(client,h,qid).status_code==403
        assert client.post(f'/api/community/posts/{pid}/helpful',headers=h,json={'enabled':True}).status_code==403
        assert client.get(f'/api/community/questions/{qid}/discussion').status_code==200
    finally:conn.execute('DELETE FROM sanctions WHERE action_id=%s',(action,))

def test_internal_citation_draft_and_database_privileges(client,actor,question):
    qid,conn=question;h=answer(client,actor,qid,'author');pid=create(client,h,qid,sources=[{'url':'https://example.test/source','note':'A synthetic supporting citation'}]).json()['id'];approve(client,actor,pid)
    h=actor('author');r=client.get(f'/api/community/posts/{pid}/evidence');assert r.status_code==200
    p=r.json();from test_bank_review import proposal
    doc=proposal(kind='explanation');doc['canonical_id']=qid;doc['appearance_id']='a_'+qid;doc['patch']={'explanation':'Synthetic reasoning cited from the shared question discussion.'};doc['evidence']=[{'kind':'reference','url':'https://study.hawayu.in'+p['citation_path'],'note':p['citation_note']},*({'kind':'reference',**x} for x in p['source_links'])]
    r=client.post('/api/contributions',headers={**h,'Idempotency-Key':uuid4().hex},json=doc);assert r.status_code==201,r.text
    detail=client.get('/api/contributions/'+r.json()['id']).json();assert detail['state']=='draft';assert len(detail['current']['payload']['evidence'])==2
    assert not detail['decisions'];assert conn.execute('SELECT answer_text FROM canonical_questions WHERE id=%s',(qid,)).fetchone()[0]=='B'
    with conn.transaction():
        conn.execute('SET LOCAL ROLE mpsc');conn.execute('SELECT * FROM discussion_events LIMIT 1');conn.execute('SELECT * FROM discussion_disclosures LIMIT 1')
    with pytest.raises(Exception,match='append-only'):
        with conn.transaction():conn.execute("UPDATE discussion_events SET action='tampered' WHERE post_id=%s",(pid,))

def test_owner_mfa_mock_guard_and_self_review(client,actor,question):
    qid,conn=question;h=answer(client,actor,qid,'author');pid=create(client,h,qid).json()['id']
    h=actor('owner');cid='disc_owner_'+uuid4().hex;mid='m_'+cid
    conn.execute("INSERT INTO collections(id,title,kind,visibility) VALUES(%s,'Synthetic owner mock','exam','public')",(cid,))
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,'owner',%s,%s,600)",(mid,cid,[qid]))
    try:
        assert not any(i['canonical_id']==qid for i in client.get('/api/community/admin/queue').json()['items'])
        assert client.post(f'/api/community/admin/posts/{pid}/action',headers=h,json={'action':'approve'}).status_code==409
    finally:conn.execute('DELETE FROM mock_sessions WHERE id=%s',(mid,))
    from app.config import settings
    original=settings.mfa_enforce_staff;settings.mfa_enforce_staff=True
    try:assert client.post(f'/api/community/admin/questions/{qid}/lock',headers=h,json={'enabled':True,'reason':'A reason does not bypass staff MFA.'}).status_code==403
    finally:settings.mfa_enforce_staff=original
    h=answer(client,actor,qid,'owner');own=create(client,h,qid).json()['id']
    assert client.post(f'/api/community/admin/posts/{own}/action',headers=h,json={'action':'approve'}).status_code==403


def test_question_discovery_unanswered_visibility(client,actor,question):
    qid,conn=question
    h=answer(client,actor,qid,'author')
    root=create(client,h,qid);assert root.status_code==201,root.text
    pid=root.json()['id'];approve(client,actor,pid)
    def ids(mode='all'):
        r=client.get('/api/community/feed',params={'tab':'questions','discussion':mode})
        assert r.status_code==200,r.text
        assert r.headers['cache-control']=='private, no-store'
        return [p['id'] for p in r.json()['items']]
    actor('reviewer1');assert pid not in ids('unanswered') # no answer disclosure
    h=answer(client,actor,qid,'outsider')
    assert pid in ids('unanswered')
    reply=create(client,h,qid,kind='reply',parent=pid,body='A synthetic reply waiting for independent moderation.')
    assert reply.status_code==201,reply.text
    rid=reply.json()['id']
    assert pid in ids('unanswered') # private pending replies cannot reveal existence
    approve(client,actor,rid);actor('author')
    assert pid not in ids('unanswered')
    assert pid in ids('all') and pid in ids('doubts')
    conn.execute("INSERT INTO creator_blocks(user_id,blocked_id) VALUES('author','outsider') ON CONFLICT DO NOTHING")
    try:
        assert pid in ids('unanswered') # only blocked replies remain
    finally:conn.execute("DELETE FROM creator_blocks WHERE user_id='author' AND blocked_id='outsider'")
    conn.execute('UPDATE posts SET hidden=true WHERE id=%s',(rid,))
    assert pid in ids('unanswered')
    explanation=create(client,actor('author'),qid,kind='explanation',body='A separate synthetic explanation for discovery filtering.')
    assert explanation.status_code==201,explanation.text
    eid=explanation.json()['id'];approve(client,actor,eid);actor('author')
    assert eid in ids('all') and eid not in ids('doubts') and eid not in ids('unanswered')
    assert client.get('/api/community/feed?tab=questions&discussion=invalid').status_code==422

def test_held_official_can_open_discussion_without_impossible_answer(client,actor,question):
    qid,conn=question;h=actor('author')
    conn.execute("UPDATE canonical_questions SET status='held',answer_source='official' WHERE id=%s",(qid,))
    before=conn.execute('SELECT count(*) FROM attempts WHERE canonical_id=%s',(qid,)).fetchone()[0]
    base=f'/api/community/questions/{qid}/discussion'
    state=client.get(base).json();assert state['can_disclose']and not state['allowed']
    mid='held-disc-'+uuid4().hex
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds)VALUES(%s,'author','ldc',%s,60)",(mid,[qid]))
    assert client.post(base+'/open',headers=h,json={}).status_code==409
    conn.execute('DELETE FROM mock_sessions WHERE id=%s',(mid,))
    assert client.post(base+'/open',headers=h,json={}).status_code==200
    assert client.get(base).json()['allowed']
    assert conn.execute('SELECT count(*) FROM attempts WHERE canonical_id=%s',(qid,)).fetchone()[0]==before
