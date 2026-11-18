"""Isolated policy fixtures; real publication/sync/reversal flow lives in test_bank_review."""
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import psycopg
import pytest
from psycopg.types.json import Jsonb
from test_learning_habit import learner


def publication(conn,user,kind='explanation',reviewers=('reviewer1',),*,bad=None):
    cid='contribution-'+uuid4().hex;pid='publication-'+uuid4().hex
    patch={'answerIndex':2} if kind=='answer' else {'page':2} if kind=='source_reference' else {'explanation':'Synthetic source-supported correction'}
    payload={'patch':patch};baseline={'record':{'answerSource':'official' if bad=='no_senior' else 'derived'}};checksum='b'*64
    conn.execute("INSERT INTO sync_log(bank_checksum,questions_in,finished_at) VALUES(%s,1,now())",(checksum,))
    conn.execute("INSERT INTO bank_contributions(id,author_id,canonical_id,kind,subject_id,title,state,idempotency_key,request_hash) VALUES(%s,%s,'cq_test',%s,'english','Synthetic isolated publication','published',%s,'test')",(cid,user,kind,cid))
    conn.execute('INSERT INTO contribution_revisions(contribution_id,revision,payload,baseline,baseline_hash,actor_id) VALUES(%s,1,%s,%s,%s,%s)',(cid,Jsonb(payload),Jsonb(baseline),'c'*64,'reviewer1' if bad=='editor_review' else user))
    manifest={'payload':payload,'baseline':baseline};receipt={'publication_id':pid,'manifest_hash':'d'*64,'after':None if bad=='missing_receipt' else {'id':'appearance-test'},'output_sha256':'e'*64 if bad=='stale_sync' else checksum}
    conn.execute("INSERT INTO bank_publications(id,contribution_id,revision,manifest,manifest_hash,exported_by,state,receipt,finished_at) VALUES(%s,%s,1,%s,%s,'owner',%s,%s,clock_timestamp()-make_interval(days=>%s))",(pid,cid,Jsonb(manifest),'d'*64,'exported' if bad=='not_applied' else 'applied',Jsonb(receipt),1 if bad=='historical' else 0))
    for r in reviewers:
        conn.execute("INSERT INTO contribution_decisions(contribution_id,revision,reviewer_id,decision,rationale) VALUES(%s,1,%s,%s,'Synthetic policy fixture only')",(cid,r,'reject' if bad=='rejected' and r=='reviewer2' else 'approve'))
    return cid,pid


def credit(conn,user,cid,pid,key=None,amount=10):
    return conn.execute("INSERT INTO contribution_credit(user_id,contribution_id,publication_id,amount,event_key,reason,subject_id) VALUES(%s,%s,%s,%s,%s,'Synthetic policy credit','english') ON CONFLICT DO NOTHING RETURNING id",(user,cid,pid,amount,key or pid+':credit')).fetchone()


def test_standard_and_two_review_answer_source_tariffs_exempt_study_cap(client,actor,database):
    conn=database[1];user,_=learner(database,actor)
    conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,points,note) VALUES(%s,%s,'study',25,'Synthetic full study budget')",(user,uuid4().hex))
    for kind,reviews,expected in [('explanation',('reviewer1',),(20,5)),('answer',('reviewer1','reviewer2'),(40,10)),('source_reference',('reviewer1','reviewer2'),(40,10))]:
        cid,pid=publication(conn,user,kind,reviews)
        with conn.transaction():
            conn.execute('SET LOCAL ROLE mpsc');c=credit(conn,user,cid,pid)
        assert conn.execute('SELECT xp,points FROM reward_ledger WHERE event_key=%s',('contribution-credit:'+str(c[0]),)).fetchone()==expected
        assert credit(conn,user,cid,pid) is None
    assert conn.execute('SELECT sum(points) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()[0]==50
    assert conn.execute('SELECT points FROM reward_daily_counters WHERE user_id=%s',(user,)).fetchone()[0]==25


def test_three_credited_per_day_under_concurrency(client,actor,database):
    name,conn=database;user,_=learner(database,actor)
    pubs=[publication(conn,user) for _ in range(6)]
    def write(pair):
        with psycopg.connect('dbname='+name) as c:
            c.execute('SET LOCAL ROLE mpsc');credit(c,user,*pair)
    with ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(write,pubs))
    assert conn.execute('SELECT count(*) FROM contribution_reward_claims WHERE user_id=%s',(user,)).fetchone()[0]==3
    assert conn.execute('SELECT sum(xp),sum(points) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()==(60,15)


@pytest.mark.parametrize('bad', ['no_reviews','one_answer_review','self_review','editor_review','past_editor_review','not_applied','historical','stale_sync','missing_receipt','revoked','wrong_scope','no_senior','rejected'])
def test_publication_independence_quorum_and_live_gates(client,actor,database,bad):
    conn=database[1];user,_=learner(database,actor)
    reviews=() if bad=='no_reviews' else (user,) if bad=='self_review' else ('reviewer1','reviewer2') if bad=='rejected' else ('reviewer1',)
    if bad=='self_review':conn.execute("INSERT INTO review_grants(user_id,role,subject_id,granted_by,reason) VALUES(%s,'reviewer','english','test','Synthetic self-review exclusion')",(user,))
    if bad in ('revoked','wrong_scope','no_senior'):
        independent=[]
        for _ in range(2 if bad=='no_senior' else 1):
            reviewer='isolated-reviewer-'+uuid4().hex;independent.append(reviewer)
            conn.execute('INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)',(reviewer,reviewer,reviewer+'@example.test'))
            conn.execute("INSERT INTO review_grants(user_id,role,subject_id,granted_by,reason,revoked_at) VALUES(%s,'reviewer',%s,'test','Synthetic review boundary',CASE WHEN %s THEN now() ELSE NULL END)",(reviewer,'mizo' if bad=='wrong_scope' else 'english',bad=='revoked'))
        reviews=tuple(independent)
    cid,pid=publication(conn,user,'answer' if bad in ('one_answer_review','no_senior') else 'explanation',reviews,bad=bad)
    if bad=='past_editor_review':
        conn.execute("INSERT INTO contribution_revisions(contribution_id,revision,payload,baseline,baseline_hash,actor_id) VALUES(%s,0,'{}','{}',%s,'reviewer1')",(cid,'a'*64))
    credit(conn,user,cid,pid)
    assert conn.execute('SELECT count(*) FROM contribution_reward_claims WHERE user_id=%s',(user,)).fetchone()[0]==0
    assert conn.execute('SELECT count(*) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()[0]==0


@pytest.mark.parametrize('legacy',[False,True])
def test_reversal_negates_exact_original_once_without_refunding_daily_slot(client,actor,database,legacy):
    conn=database[1];user,_=learner(database,actor)
    cid,pid=publication(conn,user,reviewers=() if legacy else ('reviewer1',))
    cc=credit(conn,user,cid,pid)[0]
    if legacy:conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note,rule_version) VALUES(%s,%s,'contribution',10,10,'Synthetic pre-v2 credit','learning-v1')",(user,'contribution-credit:'+str(cc)))
    original=conn.execute('SELECT id,xp,points FROM reward_ledger WHERE event_key=%s',('contribution-credit:'+str(cc),)).fetchone()
    rid='reversal-'+uuid4().hex
    conn.execute("INSERT INTO bank_publications(id,contribution_id,revision,manifest,manifest_hash,exported_by) VALUES(%s,%s,2,%s,%s,'owner')",(rid,cid,Jsonb({'payload':{'reverts_publication':pid}}),'f'*64))
    with conn.transaction():
        conn.execute('SET LOCAL ROLE mpsc');reversed_credit=credit(conn,user,cid,rid,key=rid+':reversal:'+pid,amount=-10)[0]
    assert conn.execute('SELECT xp,points,reverses_id FROM reward_ledger WHERE event_key=%s',('contribution-credit:'+str(reversed_credit),)).fetchone()==(-original[1],-original[2],original[0])
    # A second reversal publication of the same source receipt cannot remint debt.
    other=rid+'-retry'
    conn.execute("INSERT INTO bank_publications(id,contribution_id,revision,manifest,manifest_hash,exported_by) VALUES(%s,%s,3,%s,%s,'owner')",(other,cid,Jsonb({'payload':{'reverts_publication':pid}}),'f'*64))
    credit(conn,user,cid,other,key=other+':reversal:'+pid,amount=-10)
    assert conn.execute('SELECT sum(xp),sum(points) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()==(0,0)
    assert conn.execute('SELECT count(*) FROM contribution_reward_reversals WHERE original_ledger_id=%s',(original[0],)).fetchone()[0]==1
    for _ in range(3):
        later_cid,later_pid=publication(conn,user);credit(conn,user,later_cid,later_pid)
    assert conn.execute("SELECT count(*) FROM reward_ledger WHERE user_id=%s AND kind='contribution' AND points>0",(user,)).fetchone()[0]==3
    assert conn.execute('SELECT sum(xp),sum(points) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()==(40,10)


def test_already_reversed_v1_receipt_cannot_be_reversed_again_after_cutover(client,actor,database):
    conn=database[1];user,_=learner(database,actor);cid,pid=publication(conn,user,reviewers=())
    cc=credit(conn,user,cid,pid)[0]
    conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note,rule_version) VALUES(%s,%s,'contribution',10,10,'Synthetic v1 credit','learning-v1')",(user,'contribution-credit:'+str(cc)))
    old='old-reversal-'+uuid4().hex;new='new-reversal-'+uuid4().hex
    for revision,rid in [(2,old),(3,new)]:
        conn.execute("INSERT INTO bank_publications(id,contribution_id,revision,manifest,manifest_hash,exported_by) VALUES(%s,%s,%s,%s,%s,'owner')",(rid,cid,revision,Jsonb({'payload':{'reverts_publication':pid}}),'f'*64))
    with conn.transaction():
        conn.execute('ALTER TABLE contribution_credit DISABLE TRIGGER award_contribution_rewards')
        old_credit=credit(conn,user,cid,old,key=old+':reversal:'+pid,amount=-10)[0]
        conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note,rule_version) VALUES(%s,%s,'contribution',-10,-10,'Synthetic v1 reversal','learning-v1')",(user,'contribution-credit:'+str(old_credit)))
        conn.execute('ALTER TABLE contribution_credit ENABLE TRIGGER award_contribution_rewards')
    credit(conn,user,cid,new,key=new+':reversal:'+pid,amount=-10)
    assert conn.execute('SELECT count(*),sum(xp),sum(points) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()==(2,0,0)
