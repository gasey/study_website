#!/usr/bin/env python3
"""Publish an explicit, bounded set of owner-adjudicated source/answer repairs in one bank sync.

Each existing immutable manifest, source baseline and receipt remains independent.
Only distinct existing MCQs with already-exported owner decisions qualify.
The prepared batch journal permits recovery after file replacement/sync/ack failure.
No decisions, permissions, peer votes or reward credits are created here.
"""
import argparse,hashlib,importlib.util,json,os,subprocess
from pathlib import Path
from review_bank_store import atomic,bank_lock,digest,record,sha,transform
SPEC=importlib.util.spec_from_file_location('bank_worker',Path(__file__).with_name('bank-review-worker.py'))
w=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(w)


def prepare(bank,publications,input_sha,root,registered_final_keys=None):
    if not 1<=len(publications)<=100:raise ValueError('Choose 1–100 explicit source/answer publications')
    by_id={q['id']:q for q in bank['questions']};targets=set();changes={};receipts=[]
    batch_id='review_batch_'+digest(sorted(p['id']for p in publications))[:32]
    for pub in publications:
        m=pub['manifest'];p=m['payload'];target=m['baseline']['record']['id']
        if digest(m)!=pub['manifest_hash']or m.get('schema')!=1 or m['id']!=pub['id']:raise ValueError('Invalid immutable manifest')
        if m['bank_sha256']!=input_sha:raise ValueError('All decisions must refer to this exact original bank')
        if p['kind']=='answer':
            mode=m.get('admin_decision',{}).get('mode')
            if set(p['patch'])-{'answerIndex','answerSource','answerKeyRef','explanation'}:raise ValueError('Publish source repairs before answer decisions')
            if mode=='verified':
                if p['patch'].get('answerSource')!='derived'or p['patch'].get('answerKeyRef')is not None:raise ValueError('Do not turn solutions into official keys')
            elif mode=='official':
                ref=p['patch'].get('answerKeyRef');doc=(registered_final_keys or{}).get(ref)
                original=by_id.get(target,{})
                ai=p['patch'].get('answerIndex');opts=original.get('options',[])
                if (p['patch'].get('answerSource')!='official' or not doc
                        or doc.get('id')!=ref or doc.get('kind')!='official-key'
                        or doc.get('key_status')!='final' or doc.get('paper_id')!=original.get('paperId')
                        or original.get('qnum')is None or type(ai)is not int or not 0<=ai<len(opts)):
                    raise ValueError('Official batches require a current final registered key for the exact printed paper')
                matching_document=any(d.get('id')==ref and d.get('paper_id')==doc['paper_id']
                    and d.get('kind')=='official-key' and d.get('sha256')==doc['sha256']
                    and d.get('source_file')==doc['source_file'] for d in m['documents'])
                matching_cell=any(e.get('kind')=='official-key' and e.get('document_id')==ref
                    and e.get('sha256')==doc['sha256'] and type(e.get('page'))is int and e['page']>=1
                    and e.get('printed_question')==str(original['qnum'])
                    and e.get('answer_text')==opts[ai] for e in p.get('evidence',[]))
                if not matching_document or not matching_cell:raise ValueError('Missing exact key document, printed question or mapped answer-cell evidence')
            else:raise ValueError('Only verified solutions or exactly mapped final official answers qualify')
            if len((p['patch'].get('explanation')or'').strip())<20:raise ValueError('A worked explanation is required')
        elif p['kind']in('transcription','source_reference'):
            if m.get('operator_maintenance',{}).get('owner_id')!=m['author_id']:raise ValueError('Explicit owner source adjudication required')
            allowed={'page','qnum'}if p['kind']=='source_reference'else{'question','direction','questionMarkup','optionsMarkup','passage','options','hasDiagram','figureImage','answerIndex'}
            # A scan can expose an incomplete printed choice. An explicit
            # withdrawal may retain a source warning while clearing its answer;
            # it cannot certify a replacement answer or change provenance.
            if p['kind']=='transcription' and 'explanation'in p['patch']:
                if ('answerIndex'not in p['patch'] or p['patch']['answerIndex']is not None
                        or len((p['patch']['explanation']or'').strip())<20):
                    raise ValueError('A source warning requires explicit answer withdrawal')
                allowed=allowed|{'explanation'}
            if set(p['patch'])-allowed or p['patch'].get('answerIndex')is not None:raise ValueError('Source batches may clear an untrusted index but cannot assign answers or provenance')
        elif p['kind']=='defect':
            opts=m['baseline']['record'].get('options',[])
            flag_unresolved=(p['patch'].get('sourceDefect')=='unresolved-source'
                and m['baseline']['record'].get('answerIndex')is None
                and any(e.get('kind')=='paper'and e.get('document_id')and e.get('sha256')and e.get('page')
                        for e in p.get('evidence',[])))
            clear_obsolete=(p['patch'].get('sourceDefect')is None
                and m['baseline'].get('metadata',{}).get('sourceDefect')=='duplicate-options')
            if (m.get('operator_maintenance',{}).get('owner_id')!=m['author_id']
                    or set(p['patch'])!={'sourceDefect','disputeNote'}
                    or not(clear_obsolete or flag_unresolved)
                    or len((p['patch']['disputeNote']or'').strip())<20
                    or not 2<=len(opts)<=8 or any(not isinstance(o,str)or not o.strip()for o in opts)
                    or len({o.strip()for o in opts})!=len(opts)):
                raise ValueError('Defect batches require an obsolete duplicate flag or a source-evidenced unresolved item with its answer withdrawn')
        else:raise ValueError('Only bounded owner source/answer repairs qualify')
        if target in targets or target not in by_id:raise ValueError('Targets must be distinct existing appearances')
        targets.add(target);original=by_id[target]
        if original.get('type')!='mcq':raise ValueError('Only existing MCQs qualify')
        for doc in m['documents']:
            path=(root/doc['source_file']).resolve()
            if not path.is_relative_to(root)or not path.is_file()or sha(path)!=doc['sha256']:raise ValueError('Registered source changed')
        if p['patch'].get('figureImage'):
            asset=(root/p['patch']['figureImage']).resolve()
            if not asset.is_relative_to(root/'images')or not asset.is_file():raise ValueError('Figure asset is absent')
        # Reuse the existing publication validator on the exact target. The restricted
        # source/answer patch kinds cannot change other questions or taxonomy.
        branch,qid=transform({'questions':[original],'papers':bank['papers']},m)
        changed=branch['questions'][0];opts=changed.get('options',[])
        if p['kind']=='answer'and(not 2<=len(opts)<=8 or any(not isinstance(o,str)or not o.strip()for o in opts)or len({o.strip()for o in opts})!=len(opts)):raise ValueError('Repair malformed options before verifying')
        ai=changed.get('answerIndex')
        if p['kind']=='answer'and(type(ai)is not int or not 0<=ai<len(opts)):raise ValueError('A usable answer is required')
        changes[qid]=changed
        receipts.append({'publication_id':pub['id'],'manifest_hash':pub['manifest_hash'],'input_sha256':input_sha,'appearance_id':qid,'before':m['baseline']['record'],'before_fields':{k:original.get(k)for k in p['patch']},'after':record(changed),'batch_id':batch_id})
    result={**bank,'questions':[changes.get(q['id'],q)for q in bank['questions']]}
    output_sha=hashlib.sha256((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode()).hexdigest()
    for receipt in receipts:receipt['output_sha256']=output_sha
    return result,{'schema':1,'batch_id':batch_id,'input_sha256':input_sha,'output_sha256':output_sha,'receipts':receipts}


def publish(ids,dry_run=False):
    if len(ids)!=len(set(ids))or not 1<=len(ids)<=100:raise ValueError('Choose 1–100 unique explicit publication IDs')
    quoted=','.join(w.literal(x)for x in ids)
    with bank_lock(w.BANK):
        pubs=w.remote('SELECT * FROM bank_publications WHERE id IN('+quoted+')ORDER BY id',True)
        if any(digest(p['manifest'])!=p['manifest_hash']for p in pubs):raise ValueError('Immutable manifest changed')
        if len(pubs)!=len(ids)or any(p['state']not in('exported','applied')for p in pubs):raise ValueError('Every requested publication must exist and be exported/applied')
        other=w.remote("SELECT id FROM bank_publications WHERE state='exported'AND id NOT IN("+quoted+')LIMIT 1',True)
        if other:raise ValueError('An unrelated publication is waiting; reconcile it first')
        # Avoid ambiguous overlapping canonical targets, including alternate prints.
        canonical=[p['manifest']['payload']['canonical_id']for p in pubs]
        if len(canonical)!=len(set(canonical)):raise ValueError('One decision per canonical question per batch')
        allowed=w.remote("SELECT p.id FROM bank_publications p WHERE p.id IN("+quoted+")AND EXISTS(SELECT 1 FROM review_grants g WHERE g.user_id=p.manifest->>'author_id'AND g.role='owner'AND g.subject_id IS NULL AND g.revoked_at IS NULL)AND EXISTS(SELECT 1 FROM contribution_events e WHERE e.contribution_id=p.contribution_id AND e.actor_id='operator:owner-source-maintenance'AND e.action IN('operator_answer_completed','operator_source_adjudication'))",True)
        if {p['id']for p in allowed}!=set(ids):raise ValueError('Existing owner-delegated audited decisions required')
        refs={p['manifest']['payload']['patch'].get('answerKeyRef')for p in pubs
            if p['manifest'].get('admin_decision',{}).get('mode')=='official'}
        final_keys={}
        if refs:
            if None in refs:raise ValueError('Official answer is missing its registered key')
            final_keys={d['id']:d for d in w.remote("SELECT id,paper_id,source_file,sha256,kind,key_status FROM review_documents WHERE id IN("+','.join(w.literal(ref)for ref in sorted(refs))+") AND kind='official-key' AND key_status='final'",True)}
            if set(final_keys)!=refs:raise ValueError('A final official key changed or was superseded before publication')
        batch_id='review_batch_'+digest(sorted(ids))[:32]
        journal_path=w.BANK.parent/'review-batches'/(batch_id+'.json')
        current=sha(w.BANK);journal=json.loads(journal_path.read_text())if journal_path.exists()else None
        if journal:
            if {r['publication_id']for r in journal['receipts']}!=set(ids)or any(r['manifest_hash']!=next(p['manifest_hash']for p in pubs if p['id']==r['publication_id'])for r in journal['receipts']):raise ValueError('Prepared batch changed')
            if current not in(journal['input_sha256'],journal['output_sha256']):raise ValueError('Bank changed after batch preparation; reconcile explicitly')
        if not journal or current==journal['input_sha256']:
            raw=w.BANK.read_bytes();bank=json.loads(raw)
            output,prepared=prepare(bank,pubs,current,w.BANK_ROOT.resolve(),final_keys)
            if journal and prepared!=journal:raise ValueError('Prepared output changed')
            journal=prepared
            if dry_run:print(json.dumps({'dry_run':True,**journal},indent=2));return
            backup=w.BANK.parent/'review-backups'/(current+'.json');backup.parent.mkdir(exist_ok=True)
            if not backup.exists():
                fd=os.open(backup,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
                with os.fdopen(fd,'wb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
            journal_path.parent.mkdir(exist_ok=True);atomic(journal_path,journal)
            receipt_dir=w.BANK.parent/'review-receipts';receipt_dir.mkdir(exist_ok=True)
            for receipt in journal['receipts']:atomic(receipt_dir/(receipt['publication_id']+'.json'),receipt)
            if sha(w.BANK)!=current:raise ValueError('Concurrent bank writer detected')
            atomic(w.BANK,output)
        elif dry_run:print(json.dumps({'dry_run':True,'prepared':True,**journal},indent=2));return
        if sha(w.BANK)!=journal['output_sha256']:raise ValueError('Batch output hash mismatch')
        live=w.remote('SELECT bank_checksum FROM sync_log WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1',True)
        if not live or live[0]['bank_checksum']!=journal['output_sha256']:
            subprocess.run([str(w.ROOT/'scripts/sync-bank.sh')],cwd=w.ROOT,env={**os.environ,'ISM_BANK_LOCK_HELD':'1'},check=True,timeout=180)
        live=w.remote('SELECT bank_checksum FROM sync_log WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1',True)
        if not live or live[0]['bank_checksum']!=journal['output_sha256']:raise ValueError('Live bank checksum mismatch')
        # Verify every appearance, canonical answer and related classification
        # against its immutable receipt before acknowledging any publication.
        w.verify_live_batch(journal['receipts'],{p['id']:p['manifest']for p in pubs})
        statements=[]
        for receipt in journal['receipts']:
            pub=next(p for p in pubs if p['id']==receipt['publication_id'])
            if pub['state']!='applied':statements.append(w.acknowledge(pub,receipt,sql_only=True))
        # Reuse ordinary per-publication transactions, in one SSH round trip.
        # psql ON_ERROR_STOP permits explicit recovery after any partial ack.
        if statements:w.remote('\n'.join(statements))
        for pub in pubs:print('Published '+pub['id'],flush=True)
        print(json.dumps({'batch_id':batch_id,'publications':len(pubs),'bank_sha256':journal['output_sha256']}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--publications',type=Path,required=True);parser.add_argument('--dry-run',action='store_true');args=parser.parse_args();publish(json.loads(args.publications.read_text()),args.dry_run)
