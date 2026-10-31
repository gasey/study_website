#!/usr/bin/env python3
"""Trusted local operator: registry bootstrap and durable publication queue.

Uses the established SSH operator channel, never browser session credentials.
Only this fixed script can run sync-bank.sh; proposal text is never shell code.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from review_bank_store import apply_manifest, bank_lock, digest, sha

ROOT=Path(__file__).resolve().parents[1]
BANK_ROOT=ROOT.parent/'mpsc-question-bankv2'
BANK=BANK_ROOT/'bank/mpsc_bank_v2.json'
HOST=os.environ.get('ISM_HOST','ubuntu@152.67.31.231')
DB=os.environ.get('ISM_DB','mpsc')
if not all(c.isalnum() or c=='_' for c in DB):raise SystemExit('Invalid database name')

def literal(value):return "'"+str(value).replace("'","''")+"'"
def remote(query,json_result=False):
    sql=('SELECT COALESCE(json_agg(result),\'[]\'::json) FROM ('+query+') result;' if json_result else query)
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',HOST,'sudo','-u','postgres','psql','-v','ON_ERROR_STOP=1','-qtA','-d',DB],input=sql,text=True,capture_output=True,timeout=60)
    if result.returncode:raise RuntimeError(result.stderr[-1500:])
    return json.loads(result.stdout) if json_result else result.stdout

def bootstrap(email):
    bank=json.loads(BANK.read_text());taxonomy=json.loads((BANK_ROOT/'taxonomies/question-bank-v2.json').read_text())
    nodes=[]
    def visit(n,parent,level):
        nodes.append({'id':n['id'],'label':n['label'],'parent_id':parent,'level':level,'version':taxonomy['taxonomy_version']})
        for child in n.get('topics',[]):visit(child,n['id'],'topic')
        for child in n.get('subtopics',[]):visit(child,n['id'],'subtopic')
    for subject in taxonomy['subjects']:visit(subject,None,'subject')
    # Parents must precede children for foreign keys.
    values=[]
    for n in nodes:
        values.append('INSERT INTO review_taxonomy(id,label,parent_id,level,version) VALUES ('+','.join('NULL' if n[k] is None else literal(n[k]) for k in ['id','label','parent_id','level','version'])+
                      ') ON CONFLICT(id) DO UPDATE SET label=EXCLUDED.label,version=EXCLUDED.version;')
    docs=[]
    for p in bank['papers']:
        src=p.get('sourceFile')
        if not src:continue
        path=(BANK_ROOT/'pdfs'/src).resolve()
        if not path.is_relative_to(BANK_ROOT) or not path.is_file():continue
        docs.append({'id':'doc_'+hashlib.sha256(p['id'].encode()).hexdigest()[:24],'paper_id':p['id'],
            'title':p.get('examName') or src,'source_file':str(path.relative_to(BANK_ROOT)),'sha256':sha(path)})
    values.append('''INSERT INTO review_documents(id,paper_id,title,source_file,sha256,kind,registered_by)
      SELECT id,paper_id,title,source_file,sha256,'paper','operator:bootstrap' FROM jsonb_to_recordset('''+literal(json.dumps(docs))+'''::jsonb)
      AS x(id text,paper_id text,title text,source_file text,sha256 text)
      ON CONFLICT(id) DO UPDATE SET sha256=EXCLUDED.sha256,title=EXCLUDED.title;''')
    if email:
        users=remote('SELECT id FROM users WHERE lower(email)=lower('+literal(email)+')',True)
        if len(users)!=1:raise ValueError('Owner account must exist and match exactly one user')
        values.append('INSERT INTO review_grants(user_id,role,granted_by,reason) VALUES ('+literal(users[0]['id'])+",'owner','operator:bootstrap','Owner explicitly authorized in the implementation chat') ON CONFLICT DO NOTHING;")
        values.append("INSERT INTO contribution_events(actor_id,action,detail) VALUES ('operator:bootstrap','owner_grant',jsonb_build_object('user',"+literal(users[0]['id'])+"));")
    remote('BEGIN;\n'+'\n'.join(values)+'\nCOMMIT;')
    print(f'Registered {len(nodes)} taxonomy nodes and {len(docs)} paper documents; owner grant '+('configured' if email else 'unchanged'))

def register_key(args):
    path=Path(args.file).resolve()
    if not path.is_relative_to(BANK_ROOT) or path.suffix.lower()!='.pdf':raise ValueError('Key must be a local PDF under the bank repository')
    sid='key_'+hashlib.sha256((args.paper+'|'+sha(path)).encode()).hexdigest()[:24]
    remote('INSERT INTO review_documents(id,paper_id,title,source_file,sha256,kind,key_status,registered_by) VALUES ('+
        ','.join(literal(v) for v in [sid,args.paper,args.title,str(path.relative_to(BANK_ROOT)),sha(path),'official-key',args.status,'operator:key-registration'])+') ON CONFLICT(id) DO NOTHING;')
    print('Registered '+sid)

def acknowledge(pub,receipt,sql_only=False):
    # Receipt is only acknowledged after the exact output bank checksum is live.
    r=literal(json.dumps(receipt));pid=literal(pub['id']);cid=literal(pub['contribution_id'])
    statement='''BEGIN;
      SELECT id FROM bank_publications WHERE id='''+pid+''' FOR UPDATE;
      DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM sync_log WHERE bank_checksum='''+literal(receipt['output_sha256'])+''' AND finished_at IS NOT NULL)
      THEN RAISE EXCEPTION 'publication output is not live'; END IF; END $$;
      INSERT INTO contribution_credit(user_id,contribution_id,publication_id,amount,event_key,reason,subject_id,created_at)
       SELECT l.user_id,l.contribution_id,'''+pid+''',-l.amount,'''+pid+'''||':reversal:'||l.publication_id,
              'Reversed published contribution',l.subject_id,l.created_at
       FROM contribution_credit l JOIN bank_publications p ON p.id='''+pid+'''
       WHERE l.publication_id=p.manifest->'payload'->>'reverts_publication' AND l.amount>0
       ON CONFLICT(event_key) DO NOTHING;
      UPDATE bank_contributions c SET state='reverted',lock_version=lock_version+1,updated_at=now()
       FROM bank_publications original,bank_publications current_pub
       WHERE current_pub.id='''+pid+''' AND original.id=current_pub.manifest->'payload'->>'reverts_publication' AND c.id=original.contribution_id AND c.state<>'reverted';
      UPDATE bank_publications original SET state='reverted'
       FROM bank_publications current_pub WHERE current_pub.id='''+pid+''' AND original.id=current_pub.manifest->'payload'->>'reverts_publication';
      UPDATE bank_publications SET state='applied',receipt='''+r+'''::jsonb,error=NULL,finished_at=now() WHERE id='''+pid+''' AND state='exported';
      UPDATE bank_contributions c SET canonical_id=a.canonical_id,appearance_id=a.id
       FROM appearances a WHERE c.id='''+cid+''' AND c.kind='new_question' AND a.id='''+literal(receipt.get('appearance_id') or '')+''';
      INSERT INTO question_duplicate_links(left_id,right_id,contribution_id)
       SELECT LEAST(canonical_id,(manifest->'payload'->'patch'->>'duplicateId')),
              GREATEST(canonical_id,(manifest->'payload'->'patch'->>'duplicateId')),c.id
       FROM bank_contributions c JOIN bank_publications p ON p.contribution_id=c.id
       WHERE p.id='''+pid+''' AND c.kind='duplicate' ON CONFLICT DO NOTHING;
      UPDATE bank_contributions SET state='published',lock_version=lock_version+1,updated_at=now()
       WHERE id='''+cid+''' AND state='publishing';
      INSERT INTO contribution_credit(user_id,contribution_id,publication_id,amount,event_key,reason,subject_id)
       SELECT author_id,id,'''+pid+''',CASE WHEN (SELECT manifest->'payload'->>'reverts_publication' FROM bank_publications WHERE id='''+pid+''') IS NOT NULL THEN 0 WHEN kind='new_question' THEN 25 WHEN kind IN ('source_request','duplicate') THEN 0 ELSE 10 END,
          '''+pid+'''||':credit','Published reviewed contribution',subject_id FROM bank_contributions WHERE id='''+cid+''' AND NOT EXISTS(SELECT 1 FROM admin_answer_decisions d WHERE d.contribution_id=bank_contributions.id)
          AND NOT EXISTS(SELECT 1 FROM contribution_events e WHERE e.contribution_id=bank_contributions.id AND e.actor_id='operator:owner-source-maintenance' AND e.action='operator_source_adjudication')
       ON CONFLICT(event_key) DO NOTHING;
      INSERT INTO review_notifications(user_id,contribution_id,event_key,message)
       SELECT author_id,id,'''+pid+'''||':notice','Your contribution is published' FROM bank_contributions WHERE id='''+cid+''' ON CONFLICT DO NOTHING;
      INSERT INTO contribution_events(contribution_id,actor_id,action,detail)
       SELECT '''+cid+''','operator:publication','published','''+r+'''::jsonb
       WHERE NOT EXISTS(SELECT 1 FROM contribution_events WHERE contribution_id='''+cid+''' AND action='published' AND detail->>'publication_id'='''+pid+''');
      UPDATE review_outbox SET finished_at=now() WHERE event_key='''+pid+''';
      COMMIT;'''
    if sql_only:return statement
    remote(statement)

def fetch_live_records(appearance_ids):
    if not 1<=len(appearance_ids)<=100 or len(set(appearance_ids))!=len(appearance_ids):raise ValueError('Choose 1–100 distinct live appearances')
    columns={'id':'a.id','paperId':'a.paper_id','type':'a.type','question':'a.question','options':'a.options',
      'answerIndex':'a.answer_index','answerSource':'a.answer_source','answerKeyRef':'a.answer_key_ref',
      'explanation':"NULLIF(a.explanation,'')",'direction':'a.direction','questionMarkup':'a.question_markup',
      'optionsMarkup':'a.options_markup','passage':'a.passage','difficulty':'a.difficulty','page':'a.page',
      'qnum':'a.qnum','hasDiagram':'a.has_diagram','figureImage':'a.figure_image'}
    parts=','.join(literal(key)+','+value for key,value in columns.items())
    query="SELECT a.id AS appearance_id,jsonb_build_object("+parts+",'classification',jsonb_build_object('subject_id',qc.subject_id,'topic_id',qc.topic_id,'subtopic_id',qc.subtopic_id)) AS record,a.is_primary,c.answer_text,c.question AS canonical_question,c.options AS canonical_options,c.explanation AS canonical_explanation,c.difficulty AS canonical_difficulty,c.source_defect FROM appearances a JOIN canonical_questions c ON c.id=a.canonical_id LEFT JOIN question_classifications qc ON qc.question_id=c.id WHERE a.id IN("+','.join(literal(qid)for qid in appearance_ids)+")"
    rows=remote(query,True)
    related=remote("SELECT a.id AS appearance_id,l.subject_id,l.topic_id,l.subtopic_id FROM question_topic_links l JOIN appearances a ON a.canonical_id=l.question_id WHERE l.review_status='approved' AND a.id IN("+','.join(literal(qid)for qid in appearance_ids)+") ORDER BY a.id,l.subject_id,l.topic_id NULLS FIRST,l.subtopic_id NULLS FIRST",True)
    for row in rows:
        links=[{k:link[k]for k in ('subject_id','topic_id','subtopic_id')}for link in related if link['appearance_id']==row['appearance_id']]
        if links:row['record']['relatedClassifications']=links
    return rows


def verify_live_rows(receipt,manifest,rows):
    if len(rows)!=1 or rows[0]['record']!=receipt['after']:raise ValueError('Live appearance does not match the publication receipt')
    live=rows[0];expected=receipt['after']
    if live['is_primary']:
        ai=expected.get('answerIndex');answer=expected['options'][ai] if ai is not None else None
        if (live['canonical_question'],live['canonical_options'],live['answer_text'],live['canonical_explanation'] or None,live['canonical_difficulty'])!=(expected['question'],expected['options'],answer,expected['explanation'],None):
            raise ValueError('Canonical learner content does not match the publication receipt')
        if 'sourceDefect' in manifest['payload']['patch'] and live['source_defect']!=manifest['payload']['patch']['sourceDefect']:
            raise ValueError('Published defect did not reach the learner bank')

def verify_live(receipt,manifest):
    qid=receipt.get('appearance_id')
    if qid:verify_live_rows(receipt,manifest,fetch_live_records([qid]))


def verify_live_batch(receipts,manifests):
    """Two bounded read-only queries; every original per-record check still runs."""
    ids=[r['appearance_id']for r in receipts]
    rows=fetch_live_records(ids)
    for receipt in receipts:
        verify_live_rows(receipt,manifests[receipt['publication_id']],[r for r in rows if r['appearance_id']==receipt['appearance_id']])


def once(dry_run=False):
    remote("INSERT INTO review_worker_health(worker_id,status) VALUES ('local-bank-publisher','online') ON CONFLICT(worker_id) DO UPDATE SET seen_at=now(),status='online';")
    with bank_lock(BANK):
        pubs=remote("SELECT * FROM bank_publications WHERE state='exported' ORDER BY created_at LIMIT 1",True)
        if not pubs:print('Publication queue empty');return
        pub=pubs[0]
        try:
            receipt=apply_manifest(BANK,BANK_ROOT,pub['manifest'],pub['manifest_hash'],dry_run=dry_run,locked=True)
            if dry_run:print(json.dumps(receipt));return
            env={**os.environ,'ISM_BANK_LOCK_HELD':'1'}
            subprocess.run([str(ROOT/'scripts/sync-bank.sh')],cwd=ROOT,env=env,check=True,timeout=180)
            if sha(BANK)!=receipt['output_sha256']:raise ValueError('Bank changed while publishing; reconciliation required')
            # Verify changed values live, not just an old historical sync hash.
            live=remote('SELECT bank_checksum FROM sync_log WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1',True)
            if not live or live[0]['bank_checksum']!=receipt['output_sha256']:raise ValueError('Live bank checksum mismatch')
            verify_live(receipt,pub['manifest'])
            acknowledge(pub,receipt)
            print('Published '+pub['id'])
        except Exception as exc:
            error=str(exc)[-1500:] if isinstance(exc,ValueError) else 'Publication could not complete. Operator diagnostics are available in the worker log.'
            remote("UPDATE review_worker_health SET seen_at=now(),status='publication failed' WHERE worker_id='local-bank-publisher';")
            remote('BEGIN; UPDATE bank_publications SET state=\'failed\',error='+literal(error)+' WHERE id='+literal(pub['id'])+'; UPDATE bank_contributions SET state=\'publication_failed\',lock_version=lock_version+1 WHERE id='+literal(pub['contribution_id'])+"; UPDATE review_outbox SET attempts=attempts+1,last_error="+literal(error)+' WHERE event_key='+literal(pub['id'])+'; COMMIT;')
            raise

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    boot=sub.add_parser('bootstrap');boot.add_argument('--owner-email')
    run=sub.add_parser('once');run.add_argument('--dry-run',action='store_true')
    key=sub.add_parser('register-key');key.add_argument('--file',required=True);key.add_argument('--paper',required=True);key.add_argument('--title',required=True);key.add_argument('--status',choices=['provisional','final'],required=True)
    args=parser.parse_args()
    if args.command=='bootstrap':bootstrap(args.owner_email)
    elif args.command=='register-key':register_key(args)
    else:once(args.dry_run)
if __name__=='__main__':main()
