import copy
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from app.services.review_policy import Proposal,digest
from test_bank_review import proposal
from test_module_intake import intake,imp

@pytest.fixture
def research(intake,database,client,actor):
    original,rows,bank,_=intake;m=copy.deepcopy(original);m['run'].pop('manifest_sha256');m['run']['id']+='p'
    q=bank[0];p=proposal();p.update(canonical_id=imp.cid(q['id']),appearance_id=q['id'])
    p['patch']={'answerIndex':1,'answerSource':'derived','explanation':'Synthetic research proposes an alternative for independent review.'}
    p['evidence']=[{'kind':'reasoning','note':'Synthetic research reasoning. Not an approval.'},{'kind':'reference','url':'https://example.test/research','note':'Keep this separate primary source citation in the saved draft.'},{'kind':'reference','module_item_id':rows['unique']['id'],'module_run_sha256':original['run']['manifest_sha256'],'note':'Preserve the original module reference alongside the newer research run.'}]
    p=Proposal.model_validate(p).model_dump(mode='json');pid='map_'+digest(p)[:32]
    claim={'appearanceId':q['id'],'question':q['question'],'options':q['options'],'outcome':'propose_answer','rationale':p['rationale'],'reviewStatus':'prepared_independent_review_required','currentBankAnswerIndex':0,'currentBankAnswerSource':'derived','proposedAnswerIndex':1,'proposals':[{'id':pid,'payload':p,'payloadSha256':digest(p),'status':'prepared_not_submitted'}]}
    for row in m['items']:
        row['id']+='p';row['run_id']=m['run']['id']
        if row['legacy_id']=='unique':row['reviewed_packets']=[{'file':'synthetic-research.json','metadata':{'bankSha256AtReview':m['run']['bank_sha256']},'claim':claim}];item=row['id']
    alias=copy.deepcopy(next(row for row in m['items'] if row['id']==item));alias['id']+='a';alias['legacy_id']+='-alias';m['items'].append(alias)
    m['run']['counts']['exact_unique']+=1;m['run']['counts']['answer_conflict']+=1
    m['run']['manifest_sha256']=digest(m);imp.import_manifest(database[1],m,'synthetic-research')
    sync=database[1].execute('INSERT INTO sync_log(bank_checksum,questions_in,finished_at) VALUES(%s,3,now()) RETURNING id',(m['run']['bank_sha256'],)).fetchone()[0]
    h=actor('owner');d=client.get('/api/admin/bank/module-audits/items/'+item).json()
    try:yield {'url':'/api/admin/bank/module-audits/items/'+item+'/prepared/'+pid,'alias_url':'/api/admin/bank/module-audits/items/'+alias['id']+'/prepared/'+pid,'body':{'baseline_hash':d['bank_baseline_hash'],'payload_sha256':digest(p)},'headers':h,'payload':p,'item':item,'old_item':rows['unique']['id'],'question':q,'sync':sync,'proposal_id':pid}
    finally:database[1].execute('DELETE FROM sync_log WHERE id=%s',(sync,))

def test_prepared_draft_concurrent_replay_preserves_all_citations(research,client,database):
    x=research
    def create():return client.post(x['url'],headers=x['headers'],json=x['body'])
    with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(lambda _:create(),range(2)))
    assert all(r.status_code==201 for r in responses),[r.text for r in responses]
    assert len({r.json()['id'] for r in responses})==1
    cid=responses[0].json()['id'];d=client.get('/api/contributions/'+cid).json()
    assert d['state']=='draft' and not d['decisions'] and d['current']['payload']['evidence']==x['payload']['evidence']
    conn=database[1]
    assert conn.execute('SELECT count(*) FROM module_audit_links WHERE contribution_id=%s',(cid,)).fetchone()[0]==2
    assert conn.execute("SELECT count(*) FROM contribution_events WHERE contribution_id=%s AND action='prepared_research_draft'",(cid,)).fetchone()[0]==1
    assert conn.execute('SELECT answer_index FROM appearances WHERE id=%s',(x['question']['id'],)).fetchone()[0]==0
    assert create().json()['replayed']
    alias=client.post(x['alias_url'],headers=x['headers'],json=x['body']);assert alias.status_code==201,alias.text
    assert alias.json()['id']==cid and alias.json()['replayed']
    assert conn.execute('SELECT count(*) FROM module_audit_links WHERE contribution_id=%s',(cid,)).fetchone()[0]==3

def test_prepared_permissions_hashes_dismissal_and_stale_context(research,client,actor,database):
    x=research
    for role in ['outsider','reviewer1']:
        assert client.post(x['url'],headers=actor(role),json=x['body']).status_code==403
    h=actor('owner')
    assert client.post(x['url'],headers=h,json={**x['body'],'payload_sha256':'0'*64}).status_code==422
    assert client.post(x['url'],headers=h,json={**x['body'],'baseline_hash':'0'*64}).status_code==409
    conn=database[1];conn.execute("UPDATE appearances SET passage='A newly restored source context' WHERE id=%s",(x['question']['id'],))
    assert client.post(x['url'],headers=h,json=x['body']).status_code==409
    conn.execute('UPDATE appearances SET passage=NULL WHERE id=%s',(x['question']['id'],))
    conn.execute("UPDATE module_audit_triage SET state='dismissed' WHERE item_id=%s",(x['item'],))
    r=client.post(x['url'],headers=h,json=x['body']);assert r.status_code==409,r.text
    assert conn.execute('SELECT count(*) FROM module_audit_links WHERE item_id=%s',(x['old_item'],)).fetchone()[0]==0

def test_prepared_stale_bank_and_active_mock(research,client,database):
    x=research;conn=database[1]
    conn.execute('UPDATE sync_log SET bank_checksum=%s WHERE id=%s',('0'*64,x['sync']))
    r=client.post(x['url'],headers=x['headers'],json=x['body']);assert r.status_code==409,r.text
    cid='prepared-mock-'+uuid4().hex;mid='mock-'+uuid4().hex
    conn.execute("INSERT INTO collections(id,title,kind) VALUES(%s,'Synthetic research mock','exam')",(cid,))
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,'owner',%s,%s,600)",(mid,cid,[imp.cid(x['question']['id'])]))
    try:
        r=client.post(x['url'],headers=x['headers'],json=x['body']);assert r.status_code==409 and 'active mock' in r.text
    finally:conn.execute('UPDATE mock_sessions SET submitted_at=now(),elapsed_seconds=0,n_correct=0,n_wrong=0,n_skipped=1,score=0 WHERE id=%s',(mid,))
