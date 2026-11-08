#!/usr/bin/env python3
"""Publish explicit owner-adjudicated repairs through guarded bank sync.

Each existing immutable manifest, source baseline and receipt remains independent.
Only distinct existing questions with already-exported owner decisions qualify.
Written questions accept source locators/context and taxonomy; answers stay MCQ-only.
Default batches remain bounded to 100. An exact SHA-bound taxonomy run may compose
up to ten independently validated 100-item groups into one atomic sync. Source,
owner-decision, immutable receipt and protected-record checks remain mandatory.
The prepared batch journal permits recovery after file replacement/sync/ack failure.
No decisions, permissions, peer votes or reward credits are created here.
"""
import argparse,gzip,hashlib,importlib.util,json,os,subprocess
from pathlib import Path
from review_bank_store import atomic,bank_lock,digest,record,sha,transform
from editorial_protection import check_candidate,prepare_publication,finish_publication
SPEC=importlib.util.spec_from_file_location('bank_worker',Path(__file__).with_name('bank-review-worker.py'))
w=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(w)


def prepare(bank,publications,input_sha,root,registered_final_keys=None,*,compute_output_hash=True):
    if not 1<=len(publications)<=100:raise ValueError('Choose 1–100 explicit source/answer publications')
    by_id={q['id']:q for q in bank['questions']};targets=set();changes={};receipts=[]
    batch_id='review_batch_'+digest(sorted(p['id']for p in publications))[:32]
    for pub in publications:
        m=pub['manifest'];p=m['payload'];target=m['baseline']['record']['id']
        if digest(m)!=pub['manifest_hash']or m.get('schema')!=1 or m['id']!=pub['id']:raise ValueError('Invalid immutable manifest')
        if m['bank_sha256']!=input_sha:raise ValueError('All decisions must refer to this exact original bank')
        if p['kind']=='taxonomy':
            if (m.get('admin_edit',{}).get('kind')!='taxonomy'
                    or m['admin_edit'].get('actor_id')!=m['author_id']
                    or not p['patch'] or set(p['patch'])-{'classification','relatedClassifications'}):
                raise ValueError('Taxonomy batches require exact final owner admin tag decisions')
        elif p['kind']=='answer':
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
            explanation=(p['patch'].get('explanation')or'').strip()
            if (mode=='verified' or explanation) and len(explanation)<20:raise ValueError('A worked explanation is required')
        elif p['kind']=='explanation':
            baseline=m.get('baseline',{});before=baseline.get('record',{});patch=p.get('patch',{})
            opts=before.get('options')or[];ai=before.get('answerIndex');source=before.get('answerSource')
            evidence=p.get('evidence',[]);documents=m.get('documents',[])
            exact_paper=any(e.get('kind')=='paper' and e.get('document_id') and e.get('sha256')
                and type(e.get('page'))is int and e.get('page')>=1
                and any(d.get('id')==e.get('document_id') and d.get('kind')=='paper'
                    and d.get('paper_id')==before.get('paperId') and d.get('sha256')==e.get('sha256') for d in documents)
                for e in evidence)
            explanation=patch.get('explanation')
            if (m.get('operator_maintenance',{}).get('owner_id')!=m.get('author_id')
                    or set(patch)!={'explanation'} or not isinstance(explanation,str) or len(explanation.strip())<20
                    or before.get('type')!='mcq' or type(ai)is not int or not 0<=ai<len(opts)
                    or source not in {'official','key','derived'} or not 2<=len(opts)<=8
                    or any(not isinstance(o,str)or not o.strip()for o in opts)
                    or len({o.strip()for o in opts})!=len(opts)
                    or before.get('hasDiagram') and not before.get('figureImage')
                    or baseline.get('metadata',{}).get('sourceDefect') in {'duplicate-options','unresolved-source'}
                    or not exact_paper):
                raise ValueError('Explanation batches require an owner-adjudicated, source-evidenced usable answer and an explanation-only patch')
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
            clear_reviewed=(p['patch'].get('sourceDefect')is None
                and m['baseline'].get('metadata',{}).get('sourceDefect')=='unresolved-source'
                and m['baseline']['record'].get('answerIndex')is None
                and (not m['baseline']['record'].get('hasDiagram') or m['baseline']['record'].get('figureImage'))
                and any(e.get('kind')=='paper'and e.get('document_id')and e.get('sha256')and e.get('page')
                        for e in p.get('evidence',[])))
            if (m.get('operator_maintenance',{}).get('owner_id')!=m['author_id']
                    or set(p['patch'])!={'sourceDefect','disputeNote'}
                    or not(clear_obsolete or clear_reviewed or flag_unresolved)
                    or len((p['patch']['disputeNote']or'').strip())<20
                    or not 2<=len(opts)<=8 or any(not isinstance(o,str)or not o.strip()for o in opts)
                    or len({o.strip()for o in opts})!=len(opts)):
                raise ValueError('Defect batches require a source-evidenced unanswered item or an obsolete duplicate flag')
        else:raise ValueError('Only bounded owner source/answer repairs qualify')
        if target in targets or target not in by_id:raise ValueError('Targets must be distinct existing appearances')
        targets.add(target);original=by_id[target]
        if original.get('type')!='mcq':
            if original.get('type')!='descriptive' or p['kind'] not in ('transcription','source_reference','taxonomy'):
                raise ValueError('Written questions accept source locators and context only')
            if p['kind']!='taxonomy' and set(p['patch'])-{'question','direction','questionMarkup','passage','page','qnum'}:
                raise ValueError('Written source repairs cannot change options, answers or provenance')
        for doc in m['documents']:
            path=(root/doc['source_file']).resolve()
            if not path.is_relative_to(root)or not path.is_file()or sha(path)!=doc['sha256']:raise ValueError('Registered source changed')
        if p['patch'].get('figureImage'):
            asset=(root/p['patch']['figureImage']).resolve()
            if not asset.is_relative_to(root/'images')or not asset.is_file():raise ValueError('Figure asset is absent')
        # Reuse the existing publication validator on the exact target. The restricted
        # source/answer patch kinds cannot change other questions or taxonomy.
        # Taxonomy patches cannot read or change papers. The final output below
        # retains the original paper table; avoid deep-copying all 1,979 papers
        # for each individual tag correction inside the shared transformer.
        branch,qid=transform({'questions':[original],'papers':[] if p['kind']=='taxonomy' else bank['papers']},m)
        changed=branch['questions'][0];opts=changed.get('options',[])
        if p['kind']=='taxonomy':
            # The shared transformer normalizes the old unanswered -1 sentinel.
            # A taxonomy-only run preserves even that legacy representation;
            # record()/CSV still expose it as an unanswered question.
            if original.get('answerIndex')==-1 and changed.get('answerIndex') is None:
                changed['answerIndex']=-1
            untouched=lambda q:{k:v for k,v in q.items() if k not in ('classifications','relatedClassifications','reviewPublicationId')}
            if untouched(changed)!=untouched(original):raise ValueError('Taxonomy publication cannot change content, answers or provenance')
        if p['kind']=='explanation' and any(changed.get(k)!=original.get(k) for k in ('answerIndex','answerSource','answerKeyRef')):
            raise ValueError('Explanation publication cannot change answer or provenance')
        if p['kind']=='answer'and(not 2<=len(opts)<=8 or any(not isinstance(o,str)or not o.strip()for o in opts)or len({o.strip()for o in opts})!=len(opts)):raise ValueError('Repair malformed options before verifying')
        ai=changed.get('answerIndex')
        if p['kind']=='answer'and(type(ai)is not int or not 0<=ai<len(opts)):raise ValueError('A usable answer is required')
        changes[qid]=changed
        receipts.append({'publication_id':pub['id'],'manifest_hash':pub['manifest_hash'],'input_sha256':input_sha,'appearance_id':qid,'before':m['baseline']['record'],'before_fields':{k:original.get(k)for k in p['patch']},'after':record(changed),'batch_id':batch_id})
    result={**bank,'questions':[changes.get(q['id'],q)for q in bank['questions']]}
    output_sha=(hashlib.sha256((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode()).hexdigest() if compute_output_hash else None)
    for receipt in receipts:receipt['output_sha256']=output_sha
    return result,{'schema':1,'batch_id':batch_id,'input_sha256':input_sha,'output_sha256':output_sha,'receipts':receipts}


def check_live_explanation_targets(pubs):
    targets={p['manifest']['payload']['canonical_id'] for p in pubs
             if p['state']=='exported' and p['manifest']['payload']['kind']=='explanation'}
    if not targets:return
    rows=w.remote("SELECT id FROM canonical_questions WHERE id IN("+
        ','.join(w.literal(qid)for qid in sorted(targets))+
        ") AND status='live' AND NOT key_disputed AND (source_defect IS NULL OR source_defect NOT IN ('duplicate-options','unresolved-source'))",True)
    if {row['id']for row in rows}!=targets:
        raise ValueError('An explanation target became held, disputed or source-defective after review')


def require_recoverable_failures(pubs,journal,current):
    if any(p['state']=='failed' for p in pubs) and (not journal or current!=journal['output_sha256']):
        raise ValueError('Failed publications require the exact already-written prepared batch output')


def taxonomy_scope(publications,scope):
    """A larger sync may compose bounded groups only within an exact frozen run."""
    if scope.get('review_kind')!='owner-delegated-ai-taxonomy' or len(scope.get('authorization','').strip())<20:
        raise ValueError('Explicit frozen owner taxonomy scope required')
    targets={i['candidate']['canonical_id']:i for i in scope['items']}
    for pub in publications:
        m=pub['manifest'];p=m['payload'];item=targets.get(p['canonical_id'])
        if (p['kind']!='taxonomy' or not item or digest(m['baseline'])!=item['source_fingerprint']
                or p['patch'].get('classification')!=item['primary']
                or set(p['patch'])-{'classification','relatedClassifications'}):
            raise ValueError('Publication is outside the frozen taxonomy proposal/source scope')
        related=item.get('related')
        if related is None:related=m['baseline']['record'].get('relatedClassifications',[])
        related=[r for r in related if r!=item['primary']]
        normal=lambda paths:sorted(paths,key=lambda r:(r.get('subject_id') or '',r.get('topic_id') or '',r.get('subtopic_id') or ''))
        if normal(p['patch'].get('relatedClassifications',[]))!=normal(related):raise ValueError('Related tags differ from the frozen proposal')
        if item['primary'].get('topic_id')=='general-studies/current-affairs':
            context=item['candidate'].get('context_candidate')or{}
            if not context.get('reference_period') or context.get('reference_basis')not in ('printed','exam-date','reviewed-source'):
                raise ValueError('Current Affairs publication needs a supported historical reference period')


def prepare_taxonomy_groups(bank,publications,input_sha,root,scope):
    if not 1<=len(publications)<=1000:raise ValueError('Compose at most ten bounded taxonomy groups')
    taxonomy_scope(publications,scope)
    changes={};receipts=[];targets=set()
    for start in range(0,len(publications),100):
        subset=publications[start:start+100]
        # Validate every bounded group, then hash the actual combined bank once.
        branch,journal=prepare(bank,subset,input_sha,root,compute_output_hash=False)
        ids={r['appearance_id'] for r in journal['receipts']}
        if ids&targets:raise ValueError('Repeated target across taxonomy groups')
        targets.update(ids)
        changes.update({q['id']:q for q in branch['questions'] if q['id']in ids})
        receipts.extend(journal['receipts'])
    output={**bank,'questions':[changes.get(q['id'],q)for q in bank['questions']]}
    checksum=hashlib.sha256((json.dumps(output,ensure_ascii=False,indent=2)+'\n').encode()).hexdigest()
    bid='review_batch_'+digest(sorted(p['id']for p in publications))[:32]
    for r in receipts:r.update(batch_id=bid,output_sha256=checksum)
    return output,{'schema':1,'batch_id':bid,'input_sha256':input_sha,'output_sha256':checksum,'receipts':receipts}


def validate_taxonomy_admins(pubs):
    tagged=[p for p in pubs if p['manifest']['payload']['kind']=='taxonomy']
    if not tagged:return
    quoted=','.join(w.literal(p['contribution_id'])for p in tagged)
    rows=w.remote('SELECT d.*,c.revision AS current_revision FROM admin_bank_decisions d JOIN bank_contributions c ON c.id=d.contribution_id WHERE d.contribution_id IN('+quoted+')',True)
    by_id={r['id']:r for r in rows}
    for pub in tagged:
        m=pub['manifest'];decision=m.get('admin_edit',{});d=by_id.get(decision.get('id'))
        if (not d or d['actor_id']!=decision.get('actor_id') or d['actor_id']!=m['author_id']
                or d['contribution_id']!=pub['contribution_id'] or d['revision']!=m['revision']
                or d['current_revision']!=m['revision'] or d['baseline_hash']!=m['baseline_hash']
                or d['payload_hash']!=digest(m['payload'])):
            raise ValueError('Exact final owner taxonomy decision no longer matches')


def recover_failed_ack_sql(pub,batch_id):
    # Caller must first verify every immutable receipt against synced live rows.
    pid=w.literal(pub['id']);cid=w.literal(pub['contribution_id'])
    detail=w.literal(json.dumps({'batch_id':batch_id,'publication_id':pub['id'],'reason':'Exact prepared output, immutable manifest and live readback verified after acknowledgment failure.'}))
    return "BEGIN; UPDATE bank_publications SET state='exported',error=NULL WHERE id="+pid+" AND state='failed'; UPDATE bank_contributions SET state='publishing' WHERE id="+cid+" AND state='publication_failed'; INSERT INTO contribution_events(contribution_id,actor_id,action,detail) VALUES("+cid+",'operator:owner-source-maintenance','prepared_batch_ack_reconciled',"+detail+"::jsonb); COMMIT;"


def publish(ids,dry_run=False,taxonomy_run=None):
    if not dry_run:
        from bank_authority import require_writable
        require_writable(w.BANK)
    scope=None
    if taxonomy_run:
        taxonomy_run=Path(taxonomy_run)
        if hashlib.sha256(taxonomy_run.read_bytes()).hexdigest()!=taxonomy_run.with_suffix('.sha256').read_text().strip():raise ValueError('Frozen taxonomy run changed')
        scope=json.loads(taxonomy_run.read_text())
    if len(ids)!=len(set(ids))or not 1<=len(ids)<=(1000 if scope else 100):raise ValueError('Choose bounded unique explicit publication IDs')
    quoted=','.join(w.literal(x)for x in ids)
    with bank_lock(w.BANK):
        check_candidate(w.BANK)
        pubs=w.remote('SELECT * FROM bank_publications WHERE id IN('+quoted+')ORDER BY id',True)
        if any(digest(p['manifest'])!=p['manifest_hash']for p in pubs):raise ValueError('Immutable manifest changed')
        if len(pubs)!=len(ids)or any(p['state']not in('exported','applied','failed')for p in pubs):raise ValueError('Every requested publication must exist and be exported/applied, or have a recoverable prepared receipt')
        if scope:taxonomy_scope(pubs,scope)
        check_live_explanation_targets(pubs)
        other=w.remote("SELECT id FROM bank_publications WHERE state='exported'AND id NOT IN("+quoted+')LIMIT 1',True)
        if other:raise ValueError('An unrelated publication is waiting; reconcile it first')
        # Avoid ambiguous overlapping canonical targets, including alternate prints.
        canonical=[p['manifest']['payload']['canonical_id']for p in pubs]
        if len(canonical)!=len(set(canonical)):raise ValueError('One decision per canonical question per batch')
        allowed=w.remote("SELECT p.id FROM bank_publications p WHERE p.id IN("+quoted+")AND EXISTS(SELECT 1 FROM review_grants g WHERE g.user_id=p.manifest->>'author_id'AND g.role='owner'AND g.subject_id IS NULL AND g.revoked_at IS NULL)AND EXISTS(SELECT 1 FROM contribution_events e WHERE e.contribution_id=p.contribution_id AND e.actor_id='operator:owner-source-maintenance'AND e.action IN('operator_answer_completed','operator_source_adjudication','operator_taxonomy_authorization'))",True)
        if {p['id']for p in allowed}!=set(ids):raise ValueError('Existing owner-delegated audited decisions required')
        validate_taxonomy_admins(pubs)
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
        require_recoverable_failures(pubs,journal,current)
        if not journal or current==journal['input_sha256']:
            raw=w.BANK.read_bytes();bank=json.loads(raw)
            output,prepared=(prepare_taxonomy_groups(bank,pubs,current,w.BANK_ROOT.resolve(),scope) if scope else prepare(bank,pubs,current,w.BANK_ROOT.resolve(),final_keys))
            if journal and prepared!=journal:raise ValueError('Prepared output changed')
            journal=prepared
            if dry_run:print(json.dumps({'dry_run':True,**journal},indent=2));return
            compressed=all(p['manifest']['payload']['kind']=='taxonomy' for p in pubs)
            backup=w.BANK.parent/'review-backups'/(current+('.json.gz' if compressed else '.json'));backup.parent.mkdir(exist_ok=True)
            if not backup.exists():
                fd=os.open(backup,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
                with os.fdopen(fd,'wb')as stream:
                    if compressed:
                        with gzip.GzipFile(fileobj=stream,mode='wb',compresslevel=3)as zipped:zipped.write(raw)
                    else:stream.write(raw)
                    stream.flush();os.fsync(stream.fileno())
            journal_path.parent.mkdir(exist_ok=True);atomic(journal_path,journal)
            receipt_dir=w.BANK.parent/'review-receipts';receipt_dir.mkdir(exist_ok=True)
            for receipt in journal['receipts']:atomic(receipt_dir/(receipt['publication_id']+'.json'),receipt)
            if sha(w.BANK)!=current:raise ValueError('Concurrent bank writer detected')
            prepare_publication(w.BANK,bank,output,[p['manifest'] for p in pubs])
            atomic(w.BANK,output)
        elif dry_run:print(json.dumps({'dry_run':True,'prepared':True,**journal},indent=2));return
        if sha(w.BANK)!=journal['output_sha256']:raise ValueError('Batch output hash mismatch')
        finish_publication(w.BANK)
        live=w.remote('SELECT bank_checksum FROM sync_log WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1',True)
        if not live or live[0]['bank_checksum']!=journal['output_sha256']:
            subprocess.run([str(w.ROOT/'scripts/sync-bank.sh')],cwd=w.ROOT,env={**os.environ,'ISM_BANK_LOCK_HELD':'1'},check=True,timeout=180)
        live=w.remote('SELECT bank_checksum FROM sync_log WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1',True)
        if not live or live[0]['bank_checksum']!=journal['output_sha256']:raise ValueError('Live bank checksum mismatch')
        # Verify every appearance, canonical answer and related classification
        # against its immutable receipt before acknowledging any publication.
        manifests={p['id']:p['manifest']for p in pubs}
        for start in range(0,len(journal['receipts']),100):
            w.verify_live_batch(journal['receipts'][start:start+100],manifests)
        # Only after exact output hash, current authority, sync and live content
        # verification may an ack failure return to the ordinary ack path.
        for pub in pubs:
            if pub['state']=='failed':
                w.remote(recover_failed_ack_sql(pub,batch_id))
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
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--publications',type=Path,required=True);parser.add_argument('--dry-run',action='store_true');parser.add_argument('--taxonomy-run',type=Path);args=parser.parse_args();publish(json.loads(args.publications.read_text()),args.dry_run,args.taxonomy_run)
