#!/usr/bin/env python3
"""Rehearse one real missing-answer proposal using disposable dummy identities.

Runs the actual API, bank writer, sync SQL and acknowledgement against an
isolated local PostgreSQL database and a COPIED one-question bank. Never writes
production accounts, approvals, points or bank answers. Keeps evidence artifacts.
"""
from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'api/tests'),str(ROOT/'scripts')]
import conftest
from psycopg.rows import dict_row
from review_bank_store import sha,apply_manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proposal',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    bank_root=ROOT.parent/'mpsc-question-bankv2';source=bank_root/'bank/mpsc_bank_v2.json'
    original_sha=sha(source);data=json.loads(source.read_text());proposal=json.loads(args.proposal.read_text())
    source_q=next(q for q in data['questions'] if q['id']==proposal['appearance_id'])
    if source_q['id']!='081b677dfe860d7ce825':raise SystemExit('This first-case rehearsal is restricted to the verified fencing question')
    if source_q.get('answerIndex') not in {None,-1}:raise SystemExit('Rehearsal expects an unresolved real MCQ')
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
    bank=output/'rehearsal-bank.json'
    subset={'papers':[next(p for p in data['papers'] if p['id']==source_q['paperId'])],'questions':[copy.deepcopy(source_q)]}
    bank.write_text(json.dumps(subset,ensure_ascii=False,indent=2)+'\n')
    taxonomy=bank_root/'taxonomies/question-bank-v2.json';csv=output/'csv'
    subprocess.run([sys.executable,str(ROOT/'scripts/bank_to_csv.py'),str(bank),str(csv),str(taxonomy)],check=True,capture_output=True,text=True)
    script=(ROOT/'scripts/sync-bank.sh').read_text()
    setup=script.split("SQL=$(cat <<'EOSQL'\n",1)[1].split('\nEOSQL',1)[0].replace('/tmp/bank-csv',str(csv))
    sync=script.split("APPLY=$(cat <<'EOSQL'\n",1)[1].split('\nEOSQL',1)[0]
    dbs=conftest.database.__wrapped__();dbname,conn=next(dbs)
    clients=conftest.client.__wrapped__((dbname,conn));client=next(clients)
    stages=[]
    try:
        def sync_copy(checksum):
            sql=setup+'\n'+sync+"\nINSERT INTO sync_log(bank_checksum,questions_in,finished_at) VALUES ('"+checksum+"',1,now());\nCOMMIT;"
            result=subprocess.run(['psql','-v','ON_ERROR_STOP=1','-d',dbname],input=sql,text=True,capture_output=True)
            if result.returncode:raise RuntimeError(result.stderr)
        sync_copy(sha(bank))
        canonical=conn.execute('SELECT canonical_id FROM appearances WHERE id=%s',(source_q['id'],)).fetchone()[0]
        subject=proposal['subject_id'];tax=json.loads(taxonomy.read_text());subject_node=next(n for n in tax['subjects'] if n['id']==subject)
        conn.execute("INSERT INTO review_taxonomy(id,label,level,version) VALUES (%s,%s,'subject',%s) ON CONFLICT DO NOTHING",(subject,subject_node['label'],tax['taxonomy_version']))
        for user,role in [('reviewer1','reviewer'),('reviewer2','senior')]:
            conn.execute("INSERT INTO review_grants(user_id,role,subject_id,granted_by,reason) VALUES (%s,%s,%s,'demo:operator','Isolated rehearsal only; not an independent human review')",(user,role,subject))
        for user in ['author','reviewer1','reviewer2','owner']:
            conn.execute('UPDATE users SET name=%s WHERE id=%s',('DEMO '+user, user))
        for evidence in proposal['evidence']:
            if evidence.get('document_id'):
                path=bank_root/evidence.pop('local_source_file')
                if sha(path)!=evidence['sha256']:raise ValueError('Source hash mismatch')
                conn.execute("INSERT INTO review_documents(id,paper_id,title,source_file,sha256,kind,registered_by) VALUES (%s,%s,'Printed source paper',%s,%s,'paper','demo:operator')",(evidence['document_id'],source_q['paperId'],str(path.relative_to(bank_root)),sha(path)))
        proposal['canonical_id']=canonical
        def headers(user):
            token='test-session-'+user
            return {'Cookie':'ism_session='+token,'Origin':'https://study.hawayu.in','X-Review-CSRF':hashlib.sha256(('bank-review:'+token).encode()).hexdigest()}
        def post(path,payload,user):
            response=client.post('/api'+path,headers={**headers(user),'Idempotency-Key':'real-source-demo-20261021'},json=payload)
            if response.status_code not in {200,201}:raise RuntimeError(f'{path}: {response.status_code}: {response.text}')
            return response.json()
        contribution=post('/contributions',proposal,'author');cid=contribution['id'];stages.append({'state':'draft','id':cid})
        contribution=post('/contributions/'+cid+'/submit',{'expected_version':contribution['lock_version']},'author');stages.append({'state':contribution['state']})
        for user,reason in [('reviewer1','DEMO workflow decision only: perimeter is 2(70+50)=240 metres; dividing by five gives 48 posts.'),('reviewer2','DEMO workflow decision only: sides have 14,10,14,10 intervals; the closed boundary has 48 posts without a repeated endpoint.')]:
            contribution=post('/review/'+cid+'/decisions',{'expected_version':contribution['lock_version'],'decision':'approve','reason':reason},user);stages.append({'state':contribution['state'],'dummy_reviewer':user})
        pub_id=post('/admin/bank/contributions/'+cid+'/publish',{'expected_version':contribution['lock_version']},'owner')['id']
        with conn.cursor(row_factory=dict_row) as cur:pub=cur.execute('SELECT * FROM bank_publications WHERE id=%s',(pub_id,)).fetchone()
        receipt=apply_manifest(bank,bank_root,pub['manifest'],pub['manifest_hash'])
        subprocess.run([sys.executable,str(ROOT/'scripts/bank_to_csv.py'),str(bank),str(csv),str(taxonomy)],check=True,capture_output=True,text=True)
        sync_copy(receipt['output_sha256'])
        spec=importlib.util.spec_from_file_location('demo_worker',ROOT/'scripts/bank-review-worker.py');worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
        def local(query,json_result=False):
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(query);return cur.fetchall() if json_result else ''
        worker.remote=local;worker.verify_live(receipt,pub['manifest']);worker.acknowledge(pub,receipt);worker.acknowledge(pub,receipt)
        actor_headers=headers('owner')
        detail=client.get('/api/questions/'+canonical,headers=actor_headers)
        # DB verification is authoritative even if the public detail response
        # intentionally masks its key until an attempt is made.
        live=conn.execute('SELECT answer_text,answer_source FROM canonical_questions WHERE id=%s',(canonical,)).fetchone()
        assert live==('48','derived'),live
        counts=conn.execute('SELECT sum(amount),count(*) FROM contribution_credit WHERE publication_id=%s',(pub_id,)).fetchone();assert counts==(10,1),counts
        strict=conn.execute('SELECT count(*) FROM v_scorable WHERE id=%s',(canonical,)).fetchone()[0];assert strict==0
        stages.append({'state':'published','answer_text':live[0],'answer_source':live[1],'strict_official_pool':False,'dummy_credit':counts[0],'credit_entries_after_retry':counts[1]})
        report={'mode':'isolated rehearsal','real_independent_reviews':False,'production_published':False,'production_accounts_created':False,'source_appearance':source_q['id'],'canonical_id':canonical,'question':source_q['question'],'source_paper':source_q['paperId'],'page':source_q['page'],'printed_number':str(source_q['qnum']),'proposed_answer':'C. 48','stages':stages,'receipt':receipt,'source_bank_sha256_before':original_sha,'source_bank_sha256_after':sha(source),'database_removed_on_exit':True}
        assert report['source_bank_sha256_before']==report['source_bank_sha256_after']
        (output/'rehearsal-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
        (output/'reviewed-proposal.json').write_text(json.dumps(proposal,indent=2,ensure_ascii=False)+'\n')
        print(json.dumps({'mode':report['mode'],'answer':report['proposed_answer'],'stages':[s['state'] for s in stages],'real_bank_unchanged':True,'production_published':False,'evidence':str(output/'rehearsal-report.json')}))
    finally:
        try:next(clients)
        except StopIteration:pass
        try:next(dbs)
        except StopIteration:pass

if __name__=='__main__':main()
