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
import time
from review_bank_store import apply_manifest, bank_lock, digest, sha

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'api'))
from app.services.publication_verification import publication_mismatches
BANK_ROOT=ROOT.parent/'mpsc-question-bankv2'
BANK=BANK_ROOT/'bank/mpsc_bank_v2.json'
HOST=os.environ.get('ISM_HOST','ubuntu@152.67.31.231')
DB=os.environ.get('ISM_DB','mpsc')
WORKER_ID='oracle-bank-publisher' if os.environ.get('ISM_DB_TRANSPORT')=='local' else 'local-bank-publisher'
if not all(c.isalnum() or c=='_' for c in DB):raise SystemExit('Invalid database name')

def literal(value):return "'"+str(value).replace("'","''")+"'"
def remote(query,json_result=False):
    sql=('SELECT COALESCE(json_agg(result),\'[]\'::json) FROM ('+query+') result;' if json_result else query)
    transport=['sudo','-u','postgres','psql','-v','ON_ERROR_STOP=1','-qtA','-d',DB] if os.environ.get('ISM_DB_TRANSPORT')=='local' else ['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',HOST,'sudo','-u','postgres','psql','-v','ON_ERROR_STOP=1','-qtA','-d',DB]
    result=subprocess.run(transport,input=sql,text=True,capture_output=True,timeout=60)
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
          AND NOT EXISTS(SELECT 1 FROM admin_bank_decisions d WHERE d.contribution_id=bank_contributions.id)
          AND NOT EXISTS(SELECT 1 FROM contribution_events e WHERE e.contribution_id=bank_contributions.id AND e.actor_id='operator:owner-source-maintenance' AND e.action='operator_source_adjudication')
       ON CONFLICT(event_key) DO NOTHING;
      INSERT INTO review_notifications(user_id,contribution_id,event_key,message)
       SELECT author_id,id,'''+pid+'''||':notice','Your contribution is published' FROM bank_contributions WHERE id='''+cid+''' ON CONFLICT DO NOTHING;
      INSERT INTO contribution_events(contribution_id,actor_id,action,detail)
       SELECT '''+cid+''','operator:publication','published','''+r+'''::jsonb
       WHERE NOT EXISTS(SELECT 1 FROM contribution_events WHERE contribution_id='''+cid+''' AND action='published' AND detail->>'publication_id'='''+pid+''');
      WITH fixed AS (
        UPDATE content_reports cr SET status='fixed',resolved_by=d.actor_id,resolved_at=now()
        FROM admin_bank_report_links l JOIN admin_bank_decisions d ON d.id=l.decision_id
        JOIN bank_publications bp ON bp.contribution_id=d.contribution_id AND bp.revision=d.revision
        WHERE bp.id='''+pid+''' AND bp.state='applied' AND cr.id=l.report_id AND cr.canonical_id=d.canonical_id
          AND cr.status IN ('open','confirmed') AND cr.created_at<=d.created_at
          AND ((d.kind='taxonomy' AND cr.kind='subject') OR (d.kind='transcription' AND cr.kind='typo_ocr')
            OR (d.kind='source_reference' AND cr.kind='typo_ocr') OR (d.kind='explanation' AND cr.kind IN ('outdated','ambiguous'))
            OR (d.kind='defect' AND cr.kind='ambiguous'))
        RETURNING cr.id,cr.canonical_id,cr.resolved_by
      ) INSERT INTO contribution_events(actor_id,action,detail)
        SELECT resolved_by,'linked_report_fixed',jsonb_build_object('report_id',id,'question',canonical_id,'publication_id','''+pid+''') FROM fixed;
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
    query="SELECT a.id AS appearance_id,jsonb_build_object("+parts+",'classification',jsonb_build_object('subject_id',qc.subject_id,'topic_id',qc.topic_id,'subtopic_id',qc.subtopic_id)) AS record,a.is_primary,to_jsonb(c) AS canonical FROM appearances a JOIN canonical_questions c ON c.id=a.canonical_id LEFT JOIN question_classifications qc ON qc.question_id=c.id WHERE a.id IN("+','.join(literal(qid)for qid in appearance_ids)+")"
    rows=remote(query,True)
    related=remote("SELECT a.id AS appearance_id,l.subject_id,l.topic_id,l.subtopic_id FROM question_topic_links l JOIN appearances a ON a.canonical_id=l.question_id WHERE l.review_status='approved' AND a.id IN("+','.join(literal(qid)for qid in appearance_ids)+") ORDER BY a.id,l.subject_id,l.topic_id NULLS FIRST,l.subtopic_id NULLS FIRST",True)
    for row in rows:
        links=[{k:link[k]for k in ('subject_id','topic_id','subtopic_id')}for link in related if link['appearance_id']==row['appearance_id']]
        if links:row['record']['relatedClassifications']=links
    return rows


def verify_live_rows(receipt,manifest,rows):
    if len(rows)!=1:raise ValueError('Live appearance does not match the publication receipt')
    live=rows[0]
    differences=publication_mismatches(receipt['after'],live['record'],live['canonical'],live['is_primary'],manifest['payload']['patch'])
    if differences:raise ValueError('Published learner content mismatch: '+', '.join(differences))

def verify_live(receipt,manifest):
    qid=receipt.get('appearance_id')
    if qid:verify_live_rows(receipt,manifest,fetch_live_records([qid]))


def verify_live_batch(receipts,manifests):
    """Two bounded read-only queries; every original per-record check still runs."""
    ids=[r['appearance_id']for r in receipts]
    rows=fetch_live_records(ids)
    for receipt in receipts:
        verify_live_rows(receipt,manifests[receipt['publication_id']],[r for r in rows if r['appearance_id']==receipt['appearance_id']])


def validate_admin_authority(pub):
    manifest=pub['manifest']
    decision=manifest.get('admin_edit') or manifest.get('admin_decision')
    if not decision:return
    table='admin_bank_decisions' if manifest.get('admin_edit') else 'admin_answer_decisions'
    rows=remote('SELECT d.*,c.revision AS current_revision FROM '+table+' d JOIN bank_contributions c ON c.id=d.contribution_id WHERE d.id='+literal(decision['id'])+' AND d.contribution_id='+literal(pub['contribution_id']),True)
    if len(rows)!=1:raise ValueError('The final admin decision is unavailable')
    d=rows[0]
    if (d['actor_id']!=decision['actor_id'] or d['revision']!=manifest['revision'] or d['current_revision']!=manifest['revision']
        or d['baseline_hash']!=manifest['baseline_hash'] or d['payload_hash']!=digest(manifest['payload'])):
        raise ValueError('The final admin decision no longer matches this publication')
    record=manifest.get('baseline',{}).get('record',{})
    patch=manifest['payload']['patch']
    subjects={manifest.get('subject_id'),record.get('classification',{}).get('subject_id')}
    if set(patch)&{'classification','relatedClassifications'}:
        subjects.add(patch.get('classification',record.get('classification',{})).get('subject_id'))
        subjects.update(p.get('subject_id') for p in [*record.get('relatedClassifications',[]),*patch.get('relatedClassifications',[])])
    roles=remote("SELECT role,subject_id FROM review_grants WHERE user_id="+literal(d['actor_id'])+" AND revoked_at IS NULL AND role IN ('owner','publisher')",True)
    if any(not any(g['subject_id'] is None or g['subject_id']==sid for g in roles) for sid in subjects):
        raise ValueError('Final administrator publication permission was revoked or no longer covers the subjects')


def promote_deferred():
    if os.environ.get('PUBLICATION_SERIAL_QUEUE','').lower() not in ('true','1'):return
    if os.environ.get('ISM_DB_TRANSPORT')!='local':raise ValueError('Deferred publication export requires the Oracle local operator')
    result=subprocess.run(['sudo','-u','postgres','env','PUBLICATION_SERIAL_QUEUE=true','ISM_DB_TRANSPORT=local',
      sys.executable,'/srv/api/promote-publication-queue.py','--database',DB],
      check=True,capture_output=True,text=True,timeout=60,cwd='/srv/api')
    data=json.loads(result.stdout)
    print('Publication queue: '+data['state'])
    return data


def once(dry_run=False):
    if not dry_run:
        from bank_authority import require_writable
        require_writable(BANK)
    remote("INSERT INTO review_worker_health(worker_id,status) VALUES ("+literal(WORKER_ID)+",'online') ON CONFLICT(worker_id) DO UPDATE SET seen_at=now(),status='online';")
    with bank_lock(BANK):
        pubs=remote("SELECT * FROM bank_publications WHERE state='exported' ORDER BY created_at LIMIT 1",True)
        if not pubs and not dry_run:
            # A stale/cancelled intent must not hold up unrelated valid work for
            # another timer cycle. Keep the scan bounded and preserve each error.
            for _ in range(5):
                promoted=promote_deferred()
                pubs=remote("SELECT * FROM bank_publications WHERE state='exported' ORDER BY created_at LIMIT 1",True)
                if pubs or not promoted or promoted['state'] not in ('failed','cancelled'):break
        if not pubs:print('Publication queue empty');return False
        pub=pubs[0]
        try:
            group=None
            if pub['manifest'].get('admin_edit',{}).get('kind')=='taxonomy':
                groups=remote('SELECT contribution_ids FROM bank_retag_batches WHERE '+literal(pub['contribution_id'])+'=ANY(contribution_ids)',True)
                if groups:
                    ids=groups[0]['contribution_ids']
                    pubs=remote('SELECT * FROM bank_publications WHERE contribution_id IN('+','.join(literal(i) for i in ids)+') ORDER BY id',True)
                    if len(pubs)!=len(ids) or any(p['state'] not in ('exported','applied') for p in pubs):
                        raise ValueError('Every tag batch publication must be queued or already applied; retry the batch together')
                    for item in pubs:validate_admin_authority(item)
                    from admin_tag_batch import apply_admin_tag_batch
                    group=apply_admin_tag_batch(BANK,BANK_ROOT,pubs,dry_run=dry_run,locked=True)
            if not group:
                validate_admin_authority(pub)
                receipt=apply_manifest(BANK,BANK_ROOT,pub['manifest'],pub['manifest_hash'],dry_run=dry_run,locked=True)
            else:receipt=group['receipts'][0]
            if dry_run:print(json.dumps(group or receipt));return
            env={**os.environ,'ISM_BANK_LOCK_HELD':'1'}
            subprocess.run([str(ROOT/'scripts/sync-bank.sh')],cwd=ROOT,env=env,check=True,timeout=180)
            if sha(BANK)!=receipt['output_sha256']:raise ValueError('Bank changed while publishing; reconciliation required')
            # Verify changed values live, not just an old historical sync hash.
            live=remote('SELECT bank_checksum FROM sync_log WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1',True)
            if not live or live[0]['bank_checksum']!=receipt['output_sha256']:raise ValueError('Live bank checksum mismatch')
            if group:
                verify_live_batch(group['receipts'],{p['id']:p['manifest'] for p in pubs})
                for item in pubs:
                    if item['state']!='applied':
                        acknowledge(item,next(r for r in group['receipts'] if r['publication_id']==item['id']))
                print('Published admin tag batch '+group['batch_id'])
            else:
                verify_live(receipt,pub['manifest'])
                acknowledge(pub,receipt)
                print('Published '+pub['id'])
            return True
        except Exception as exc:
            error=str(exc)[-1500:] if isinstance(exc,ValueError) else 'Publication could not complete. Operator diagnostics are available in the worker log.'
            remote("UPDATE review_worker_health SET seen_at=now(),status='publication failed' WHERE worker_id="+literal(WORKER_ID)+";")
            for item in pubs:
                if item['state']=='applied':continue
                remote('BEGIN; UPDATE bank_publications SET state=\'failed\',error='+literal(error)+' WHERE id='+literal(item['id'])+'; UPDATE bank_contributions SET state=\'publication_failed\',lock_version=lock_version+1 WHERE id='+literal(item['contribution_id'])+"; UPDATE review_outbox SET attempts=attempts+1,last_error="+literal(error)+' WHERE event_key='+literal(item['id'])+'; COMMIT;')
            raise

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    boot=sub.add_parser('bootstrap');boot.add_argument('--owner-email')
    run=sub.add_parser('once');run.add_argument('--dry-run',action='store_true')
    key=sub.add_parser('register-key');key.add_argument('--file',required=True);key.add_argument('--paper',required=True);key.add_argument('--title',required=True);key.add_argument('--status',choices=['provisional','final'],required=True)
    args=parser.parse_args()
    if args.command=='bootstrap':bootstrap(args.owner_email)
    elif args.command=='register-key':register_key(args)
    else:
        limit=5 if not args.dry_run and os.environ.get('PUBLICATION_SERIAL_QUEUE','').lower() in ('true','1') else 1
        end=time.monotonic()+180
        for _ in range(limit):
            if not once(args.dry_run) or time.monotonic()>=end:break
if __name__=='__main__':main()
