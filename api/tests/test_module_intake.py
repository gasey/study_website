import csv,hashlib,importlib.util,json
from pathlib import Path
from uuid import uuid4
import pytest
from psycopg.types.json import Jsonb
from app.services.review_policy import Evidence
from test_bank_review import proposal
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('module_import',ROOT/'scripts/import-module-audits.py');imp=importlib.util.module_from_spec(spec);spec.loader.exec_module(imp)

@pytest.fixture
def intake(database,client,tmp_path):
    _,conn=database;conn.execute('DELETE FROM review_rate_buckets')
    bank=[]
    for stem,opts in [('Which signed value is -2?',['-2','2','3','4']),('An exact repeated question?',['a','b','c','d']),('An exact repeated question?',['a','b','c','d'])]:
        aid=uuid4().hex[:20];qid=imp.cid(aid)
        q={'id':aid,'paperId':'paper-test','type':'mcq','question':stem,'options':opts,'answerIndex':0,'answerSource':'derived'};bank.append(q)
        conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES(%s,'mcq',%s,%s,%s,'derived')",(qid,stem,Jsonb(opts),opts[0]))
        conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary,qnum,page) VALUES(%s,'paper-test','mcq',%s,%s,0,'derived',%s,true,'1',1)",(aid,stem,Jsonb(opts),qid))
        conn.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,taxonomy_version,source,review_status) VALUES(%s,'english','English','test','manual','approved')",(qid,))
    qs=[{'id':'unique','paperId':'old-paper',**{k:v for k,v in bank[0].items() if k in ['question','options']},'answerIndex':1,'answerSource':'legacy-derived'}, {'id':'ambiguous','paperId':'old-paper','question':bank[1]['question'],'options':bank[1]['options'],'answerIndex':0}, {'id':'sign-difference','paperId':'old-paper','question':bank[0]['question'].replace('-2','2'),'options':bank[0]['options'],'answerIndex':1}, {'id':'missing','paperId':'old-paper','question':'This has no bank source match.','options':['a','b'],'answerIndex':None}]
    source=tmp_path/'module.json';source.write_text(json.dumps({'questions':qs}));bp=tmp_path/'bank.json';bp.write_text(json.dumps({'questions':bank}));cw=tmp_path/'crosswalk.csv'
    with cw.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['legacy_question_id','legacy_paper_id','status','candidate_appearance_ids','source_appearance_id']);writer.writeheader()
        for q in qs:writer.writerow({'legacy_question_id':q['id'],'legacy_paper_id':'old-paper','status':'exact_unique' if q['id'] in {'unique','sign-difference'} else 'unmatched','candidate_appearance_ids':bank[0]['id'] if q['id'] in {'unique','sign-difference'} else ''})
    m=imp.prepare('udc-ldc',source,cw,bp);receipt=imp.import_manifest(conn,m,'synthetic-test')
    rows={i['legacy_id']:i for i in m['items']}
    return m,rows,bank,receipt

def test_import_replay_hashes_and_signed_identity(intake,database,client,actor):
    m,rows,bank,_=intake;_,conn=database
    assert imp.import_manifest(conn,m)['replayed']
    assert m['run']['counts']['exact_unique']==1 and m['run']['counts']['ambiguous_exact']==1
    assert rows['sign-difference']['match_status']=='unmatched' and not rows['sign-difference']['candidates'][0]['imported']['identity_exact']
    assert rows['unique']['comparison']=='conflict'
    altered=json.loads(json.dumps(m));altered['items'][0]['legacy']['question']='Changed file without changing hash'
    with pytest.raises(ValueError,match='hash mismatch'):imp.import_manifest(conn,altered)
    actor('outsider');assert client.get('/api/admin/bank/module-audits/runs').status_code==403
    actor('reviewer1');assert client.get('/api/admin/bank/module-audits/items').status_code==403
    actor('owner');r=client.get('/api/admin/bank/module-audits/items?run_id='+m['run']['id']);assert r.status_code==200,r.text
    assert r.json()['total']==4 and r.headers['cache-control']=='private, no-store'
    assert client.get('/api/admin/bank/module-audits/items?run_id='+m['run']['id']+'&comparison=conflict').json()['total']==1
    assert client.get('/api/admin/bank/module-audits/items?run_id='+m['run']['id']+'&offset=100').json()['total']==4
    with conn.transaction():
        conn.execute('SET LOCAL ROLE mpsc')
        assert imp.import_manifest(conn,m)['replayed']
        conn.execute("INSERT INTO module_audit_events(item_id,actor_id,action) VALUES(%s,'synthetic-test','grant_check')",(rows['unique']['id'],))
        conn.execute("UPDATE module_audit_triage SET reason='Synthetic grant check' WHERE item_id=%s",(rows['unique']['id'],))
    with pytest.raises(Exception,match='append-only'):
        with conn.transaction():conn.execute("UPDATE module_audit_items SET match_status='unmatched' WHERE id=%s",(rows['unique']['id'],))

def test_exact_candidate_reference_and_linked_draft(intake,client,actor,database):
    m,rows,bank,_=intake;row=rows['unique'];h=actor('owner')
    d=client.get('/api/admin/bank/module-audits/items/'+row['id']);assert d.status_code==200,d.text
    data=d.json();assert data['identity_matches'] and data['live_comparison']=='conflict' and data['selected']['appearance_id']==bank[0]['id']
    p=proposal();p['canonical_id']=imp.cid(bank[0]['id']);p['appearance_id']=bank[0]['id'];p['patch']={'answerIndex':1,'answerSource':'derived','explanation':'Synthetic independent reasoning for the proposed alternative.'};p['evidence']=[{'kind':'reference','module_item_id':row['id'],'module_run_sha256':m['run']['manifest_sha256'],'url':m['run']['module_url'],'note':'A module comparison is corroboration, not official-key proof.'}]
    key=uuid4().hex;r=client.post('/api/contributions',headers={**h,'Idempotency-Key':key},json=p);assert r.status_code==201,r.text
    cid=r.json()['id'];again=client.post('/api/contributions',headers={**h,'Idempotency-Key':key},json=p);assert again.json()['id']==cid
    detail=client.get('/api/admin/bank/module-audits/items/'+row['id']).json();assert detail['state']=='linked' and len(detail['links'])==1 and detail['version']==2
    assert client.get('/api/contributions/'+cid).json()['state']=='draft'
    bad=json.loads(json.dumps(p));bad['evidence'][0]['module_run_sha256']='0'*64
    assert client.post('/api/contributions',headers={**h,'Idempotency-Key':uuid4().hex},json=bad).status_code==422
    bad=json.loads(json.dumps(p));bad['patch']['answerSource']='official'
    assert client.post('/api/contributions',headers={**h,'Idempotency-Key':uuid4().hex},json=bad).status_code==422
    _,conn=database
    assert conn.execute('SELECT answer_index FROM appearances WHERE id=%s',(bank[0]['id'],)).fetchone()[0]==0
    # A linked ordinary author may reopen their cited evidence, but not the intake directory.
    conn.execute('UPDATE bank_contributions SET author_id=\'outsider\' WHERE id=%s',(cid,))
    actor('outsider');assert client.get('/api/admin/bank/module-audits/items/'+row['id']).status_code==200
    assert client.get('/api/admin/bank/module-audits/items').status_code==403

def test_ambiguous_stale_and_nonmember_candidates(intake,client,actor,database):
    m,rows,bank,_=intake;actor('owner')
    url='/api/admin/bank/module-audits/items/'+rows['ambiguous']['id']
    d=client.get(url).json();assert d['selected'] is None and len(d['candidates'])==2
    assert client.get(url+'?candidate='+bank[0]['id']).status_code==404
    d=client.get(url+'?candidate='+bank[1]['id']).json();assert d['identity_matches']
    hist=client.get('/api/admin/bank/module-audits/items/'+rows['sign-difference']['id']+'?candidate='+bank[0]['id']).json();assert hist['identity_matches'] is False and not hist['bank_changed']
    _,conn=database;conn.execute('UPDATE appearances SET answer_index=2 WHERE id=%s',(bank[1]['id'],))
    d=client.get(url+'?candidate='+bank[1]['id']).json();assert d['bank_changed'] and d['live_comparison']=='conflict'
    p=proposal();p['canonical_id']=imp.cid(bank[0]['id']);p['appearance_id']=bank[0]['id'];p['evidence']=[{'kind':'reference','module_item_id':rows['sign-difference']['id'],'module_run_sha256':m['run']['manifest_sha256'],'note':'Do not reuse a punctuation-stripped record mapping.'}]
    assert client.post('/api/contributions',headers={**actor('owner'),'Idempotency-Key':uuid4().hex},json=p).status_code==409

def test_triage_source_request_and_active_mock_protection(intake,client,actor,database):
    m,rows,bank,_=intake;h=actor('owner');mid=rows['missing']['id'];url='/api/admin/bank/module-audits/items/'+mid
    r=client.post(url+'/triage',headers=h,json={'expected_version':1,'action':'dismiss','reason':'Synthetic source evidence is not usable for a safe record mapping.'});assert r.status_code==200,r.text
    assert client.post(url+'/triage',headers=h,json={'expected_version':1,'action':'reopen','reason':'Synthetic source was inspected again.'}).status_code==409
    assert client.post(url+'/triage',headers=h,json={'expected_version':2,'action':'reopen','reason':'Synthetic source was inspected again.'}).status_code==200
    p={'kind':'source_request','canonical_id':None,'subject_id':'english','title':'Request synthetic module source','patch':{'sourceUrl':'https://map.hawayu.in/udc-ldc','explanation':'Register and inspect the printed source for this unmatched module record.'},'rationale':'The module record has no exact bank identity, so source registration is needed.','evidence':[{'kind':'reference','module_item_id':mid,'module_run_sha256':m['run']['manifest_sha256'],'note':'Unmatched record needs a source request, not a guessed canonical link.'}]}
    r=client.post('/api/contributions',headers={**h,'Idempotency-Key':uuid4().hex},json=p);assert r.status_code==201,r.text
    assert client.get(url).json()['state']=='linked'
    _,conn=database;collection='module-mock-'+uuid4().hex
    conn.execute("INSERT INTO collections(id,title,kind) VALUES(%s,'Synthetic module disclosure test','exam')",(collection,))
    mock='module-mock-'+uuid4().hex
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,'owner',%s,%s,600)",(mock,collection,[imp.cid(bank[0]['id'])]))
    try:
        assert client.get('/api/admin/bank/module-audits/items/'+rows['unique']['id']).status_code==409
        listed=client.get('/api/admin/bank/module-audits/items?run_id='+m['run']['id']).json()['items'];assert rows['unique']['id'] not in [i['id'] for i in listed]
    finally:conn.execute('UPDATE mock_sessions SET submitted_at=now(),elapsed_seconds=0,n_correct=0,n_wrong=0,n_skipped=1,score=0 WHERE id=%s',(mock,))

def test_reference_serialization_keeps_old_payload_shape():
    d=Evidence(kind='reasoning',note='An existing reasoning record.').model_dump()
    assert 'module_item_id' not in d and 'module_run_sha256' not in d
