#!/usr/bin/env python3
"""Resumable SSH-only acceptance of a frozen, explicitly authorized AI tag pass.

Uses final owner admin decisions, exact source guards, ordinary immutable exports
and the guarded Oracle publisher. It never invents editorial/answer inspections.
"""
import argparse,asyncio,copy,hashlib,json,os,subprocess,sys,tempfile,pwd,traceback
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

os.chdir('/tmp')
os.environ.setdefault('DATABASE_URL','postgresql:///mpsc')
os.environ['PUBLICATION_SERIAL_QUEUE']='true'
sys.path.insert(0,'/srv/api')
from app.services.review_policy import Proposal,digest
from app.services import bank_review as review
from app.services.review_identity import Actor,require_role
from app.services.admin_bank_edits import decide
from app.services.editorial_access import source_version
from app.services.taxonomy_review_progress import record as record_progress
from app.services.taxonomy_review_progress import existing_records
import psycopg
from psycopg.rows import dict_row

def save(path,data):
    path=Path(path);fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.taxonomy-')
    try:
        with os.fdopen(fd,'w')as stream:
            json.dump(data,stream,ensure_ascii=False,indent=2,default=str);stream.write('\n');stream.flush();os.fsync(stream.fileno())
        os.chmod(tmp,0o640);os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

RUN_CACHE={}

def load(directory):
    file=directory/'frozen.json'
    expected=(directory/'frozen.sha256').read_text().strip()
    with file.open('rb')as source:actual=hashlib.file_digest(source,'sha256').hexdigest()
    if actual!=expected:raise ValueError('Frozen owner scope changed')
    key=(str(directory.resolve()),expected)
    HASHES.update(json.loads((directory/'source-hashes.json').read_text()))
    if key in RUN_CACHE:return RUN_CACHE[key]
    run=json.loads(file.read_text())
    if len(run['authorization'].strip())<20 or run['review_kind']!='owner-delegated-ai-taxonomy':raise ValueError('Explicit owner scope required')
    items=run['items'];ids=[x['candidate']['canonical_id'] for x in items]
    if len(ids)!=len(set(ids)):raise ValueError('One frozen proposal per canonical question')
    HASHES.update(json.loads((directory/'source-hashes.json').read_text()))
    bindings=json.loads((directory/'document-bindings.json').read_text()) if (directory/'document-bindings.json').exists() else {}
    for item in run['items']:
        # Recover an omitted packet wrapper from the model's explicit registered
        # document evidence; never guess a page or manufacture an inspection.
        if not item.get('document'):
            evidence=item['candidate'].get('source_evidence')or item['candidate'].get('evidence')or{}
            docid=evidence.get('document_id')or evidence.get('source_document_id')
            checksum=evidence.get('sha256')or evidence.get('source_document_sha256')
            if docid and checksum:
                item['document']={'id':docid,'sha256':checksum,'paper_id':item['snapshot']['paper']['id'],'kind':'paper'}
                item['document_binding']={'basis':'Explicit document/hash in the frozen model source evidence','document_id':docid,'sha256':checksum}
        doc=item.get('document');binding=bindings.get(doc['id']) if doc else None
        if binding:
            if doc['sha256']!=binding['sha256'] or doc.get('paper_id')!=binding['paper_id']:
                raise ValueError('Source document reconciliation differs from frozen evidence')
            item['document']=binding
            item['document_binding']={'basis':'Exact same registered paper identity and PDF SHA256',
                                      'original_document_id':doc['id'],'registered_document_id':binding['id'],'sha256':binding['sha256']}
    RUN_CACHE[key]=run
    return run

async def owner_id(cur,run):
    await cur.execute('SELECT id FROM users WHERE lower(email)=lower(%s)',(run['owner_email'],))
    users=await cur.fetchall()
    if len(users)!=1:raise ValueError('Exactly one existing owner account required')
    owner=users[0]['id'];await require_role(cur,owner,roles=('owner',),lock=False);return owner

def proposal(item):
    snap=item['snapshot'];row=item['candidate'];primary=item['primary']
    if not primary or not primary.get('subject_id'):raise ValueError('Missing proposed primary path')
    related=item['related']
    before=snap['record'].get('relatedClassifications',[])
    if related is None:related=before
    # Missing fields or abbreviated secondary lists must not delete valid links.
    if any(x not in related and x!=primary for x in before):raise ValueError('Existing related path removal needs explicit separate review')
    related=[x for x in related if x!=primary]
    reason=item['reason'].strip()
    if len(reason)<20:raise ValueError('Missing specific model rationale')
    doc=item['document'];page=item['physical_page']
    if not doc or type(page)is not int or page<1:raise ValueError('Missing exact registered source document/page')
    attribution='Owner delegated acceptance of saved AI tagging review; no independent human or answer verification. '
    return Proposal(kind='taxonomy',canonical_id=row['canonical_id'],appearance_id=row['appearance_id'],
        subject_id=primary['subject_id'],title='Reviewed learning tags: '+snap['record']['question'][:140],
        patch={'classification':primary,'relatedClassifications':related},
        rationale=(attribution+reason+' Source review: '+item['candidate_file'])[:8000],
        evidence=[{'kind':'paper','document_id':doc['id'],'sha256':doc['sha256'],'page':page,
                   'note':(attribution+'Saved source context and model rationale: '+reason)[:4000]},
                  {'kind':'reasoning','note':(reason+'; source proposal '+item['candidate_signature'])[:4000]}])

def context_blocker(item):
    primary=item.get('primary')or{};context=item['candidate'].get('context_candidate')or{}
    paths=[primary,*(item.get('related')or[])]
    ca=any(p.get('topic_id')=='general-studies/current-affairs'for p in paths)
    changing=context.get('time_behavior')in('dated-event','changes-over-time','dynamic')
    if ca or changing:
        if not context.get('reference_period') or context.get('reference_basis')not in ('printed','exam-date','reviewed-source'):
            return ('Current Affairs' if ca else 'Changing-fact')+' review lacks a supported historical reference period/basis'
    return None

async def inspect(cur,owner,item):
    row=item['candidate'];qid=row['canonical_id'];aid=row['appearance_id']
    if row['action']=='hold':raise ValueError('Saved routing hold: '+str(row.get('owner_question') or row.get('alternatives') or item['reason']))
    if context_blocker(item):raise ValueError(context_blocker(item))
    current=await review.snapshot(cur,qid,aid)
    if digest(current)!=item['source_fingerprint'] or digest(item['snapshot'])!=item['source_fingerprint']:
        raise ValueError('Source changed since the saved model review')
    if row.get('current_primary')!=current['record']['classification']:raise ValueError('Saved baseline path differs')
    p=proposal(item)
    await review.protect_answer(cur,owner,qid)
    await review.validate_evidence(cur,p,current,allow_noop=True)
    doc=item['document']
    if HASHES.get(doc['id'])!=doc['sha256']:raise ValueError('Registered source bytes changed or original is missing')
    old=current['record'];unchanged=(old['classification']==p.patch['classification'] and old.get('relatedClassifications',[])==p.patch['relatedClassifications'])
    if row['action']=='keep' and not unchanged:raise ValueError('Keep candidate proposes a different path')
    if old['type']=='descriptive' and 'literature' in item['reason'].lower() and p.patch['classification'].get('subtopic_id')=='english/writing/essay':
        raise ValueError('Specialist literature analysis cannot be certified as composition solely because it is written')
    if old['type']=='mcq' and old.get('answerIndex') is not None and not 0<=old['answerIndex']<len(old.get('options') or []):
        raise ValueError('Existing source has an invalid answer index; taxonomy-only publication must preserve answers')
    return p,current,unchanged

HASHES={}

async def preflight(directory,targets=None):
    run=load(directory);results=[]
    items=run['items']
    if targets:
        selected=set(json.loads(targets.read_text()))
        if not selected.issubset({i['candidate']['canonical_id']for i in items}):raise ValueError('Supplemental targets are outside the frozen run')
        items=[i for i in items if i['candidate']['canonical_id']in selected]
    async with await psycopg.AsyncConnection.connect('dbname=mpsc',row_factory=dict_row,options='-c jit=off') as conn:
        async with conn.cursor() as cur:
            await cur.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            owner=await owner_id(cur,run)
            for n,item in enumerate(items,1):
                row=item['candidate'];result={'canonical_id':row['canonical_id'],'appearance_id':row['appearance_id']}
                try:
                    _,_,unchanged=await inspect(cur,owner,item)
                    result.update(status='confirmed' if unchanged else 'ready')
                except Exception as exc:result.update(status='blocked',reason=str(getattr(exc,'detail',str(exc))))
                results.append(result)
                if n%500==0:print(json.dumps({'preflight':n,'total':len(items)}),flush=True)
    save(directory/'preflight.json',{'at':datetime.now(timezone.utc).isoformat(),'results':results,'counts':dict(Counter(r['status']for r in results))})
    print(json.dumps({'preflight_complete':dict(Counter(r['status']for r in results))}),flush=True)

async def queue(directory,chunk):
    run=load(directory);items={i['candidate']['canonical_id']:i for i in run['items']}
    ids=json.loads(chunk.read_text());all_targets=[items[qid] for qid in ids]
    if not 1<=len(all_targets)<=100:raise ValueError('Choose at most 100 exact run targets')
    blocked=[i for i in all_targets if context_blocker(i)];targets=[i for i in all_targets if not context_blocker(i)]
    output=chunk.with_suffix('.queued.json')
    if output.exists():print(json.dumps({'queue_reused':len(json.loads(output.read_text())['publications']),'chunk':chunk.name}));return
    async with await psycopg.AsyncConnection.connect('dbname=mpsc',row_factory=dict_row,options='-c jit=off') as conn:
        async with conn.cursor() as cur:
            owner=await owner_id(cur,run)
            for item in blocked:await record_progress(cur,owner,run,item,'blocked',context_blocker(item))
            if not targets:
                save(output,{'publications':[],'targets':[],'blocked':[i['candidate']['canonical_id']for i in blocked]})
                save(chunk.with_suffix('.publications.json'),[]);return
            keys=['tax-run:'+digest([run['run_id'],i['candidate_signature']])[:55] for i in targets]
            await cur.execute('''SELECT p.*,d.request_key FROM admin_bank_decisions d
              JOIN bank_publications p ON p.contribution_id=d.contribution_id AND p.revision=d.revision
              WHERE d.actor_id=%s AND d.request_key=ANY(%s)''',(owner,keys))
            existing=await cur.fetchall()
            if existing:
                by_id={i['candidate']['canonical_id']:i for i in targets}
                if len(existing)!=len(targets):raise ValueError('Partially recorded decision set requires explicit reconciliation')
                recovered=[]
                for pub in existing:
                    m=pub['manifest'];qid=m['payload']['canonical_id'];item=by_id.get(qid)
                    if (not item or m['payload']!=proposal(item).model_dump(mode='json')
                            or digest(m['baseline'])!=item['source_fingerprint'] or digest(m)!=pub['manifest_hash']):
                        raise ValueError('Existing decisions differ from frozen owner scope')
                    recovered.append({'canonical_id':qid,'contribution_id':pub['contribution_id'],'publication_id':pub['id']})
                save(output,{'publications':[x['publication_id']for x in recovered],'targets':recovered})
                save(chunk.with_suffix('.publications.json'),[x['publication_id']for x in recovered])
                print(json.dumps({'recovered_queued':len(recovered)}),flush=True);return
            await cur.execute("""SELECT 1 FROM bank_publications p WHERE p.state='exported'
              AND NOT EXISTS(SELECT 1 FROM contribution_events e WHERE e.contribution_id=p.contribution_id
                AND e.actor_id='operator:owner-source-maintenance' AND e.action='operator_taxonomy_authorization'
                AND e.detail->>'run_id'=%s AND e.detail->>'owner_id'=%s) LIMIT 1""",(run['run_id'],owner))
            if await cur.fetchone():raise ValueError('Finish unrelated exports before starting this chunk')
            await cur.execute("SELECT 1 FROM review_outbox WHERE kind='publication-intent' AND finished_at IS NULL LIMIT 1")
            if await cur.fetchone():raise ValueError('Finish outstanding publication intents first')
            scope={'owner_id':owner,'run_id':run['run_id'],'canonical_ids':frozenset(ids),
                   'purpose':'owner-taxonomy-publication','authorization':run['authorization']}
            token=review.owner_maintenance_quota_run.set(scope)
            pubs=[];contributions=[]
            try:
                # All sources are checked before any decision; the final admin
                # service independently rechecks each locked baseline/version.
                prepared=[]
                for item in targets:
                    p,snap,same=await inspect(cur,owner,item)
                    if same:raise ValueError('A queued correction unexpectedly became unchanged')
                    prepared.append((item,p,snap,await source_version(cur,p.canonical_id,p.appearance_id,True)))
                for item,p,snap,source_token in prepared:
                    key='tax-run:'+digest([run['run_id'],item['candidate_signature']])[:55]
                    result=await decide(cur,Actor(owner,'',False,False),p,key,digest(snap),source_token,group_export=True)
                    pub=result['publication']
                    if not pub.get('id'):raise ValueError('Batch did not export a concrete publication')
                    await review.event(cur,result['contribution_id'],'operator:owner-source-maintenance','operator_taxonomy_authorization',
                        {'owner_id':owner,'authorization':run['authorization'],'run_id':run['run_id'],
                         'candidate_file':item['candidate_file'],'candidate_signature':item['candidate_signature'],
                         'source_document_binding':item.get('document_binding'),
                         'review_kind':run['review_kind'],'independent_human_review':False,'no_answer_verification':True})
                    pubs.append(pub['id']);contributions.append({'canonical_id':p.canonical_id,'contribution_id':result['contribution_id'],'publication_id':pub['id']})
            finally:review.owner_maintenance_quota_run.reset(token)
    data={'publications':pubs,'targets':contributions,'blocked':[i['candidate']['canonical_id']for i in blocked]};save(output,data)
    save(chunk.with_suffix('.publications.json'),pubs)
    print(json.dumps({'queued':len(pubs),'file':str(output)}),flush=True)

async def record(directory,chunk=None):
    run=load(directory);items={i['candidate']['canonical_id']:i for i in run['items']}
    async with await psycopg.AsyncConnection.connect('dbname=mpsc',row_factory=dict_row,options='-c jit=off') as conn:
        async with conn.cursor() as cur:
            owner=await owner_id(cur,run)
            known=await existing_records(cur,run['run_id'])
            if chunk:
                queued=json.loads(chunk.with_suffix('.queued.json').read_text())
                await cur.execute("SELECT id FROM bank_publications WHERE id=ANY(%s) AND state='applied'",(queued['publications'],))
                if len(await cur.fetchall())!=len(queued['publications']):raise ValueError('Every receipt must be applied before marking completion')
                for target in queued['targets']:
                    item=items[target['canonical_id']];p=proposal(item)
                    expected=copy.deepcopy(item['snapshot']);expected['record'].update(p.patch)
                    if not expected['record'].get('relatedClassifications'):expected['record'].pop('relatedClassifications',None)
                    current=await review.snapshot(cur,target['canonical_id'],item['candidate']['appearance_id'])
                    if digest(expected)!=digest(current):
                        await record_progress(cur,owner,run,item,'blocked','Source changed after publication; recheck required',target['contribution_id'],known_records=known)
                    else:await record_progress(cur,owner,run,item,'published',contribution_id=target['contribution_id'],known_records=known)
            else:
                pre=json.loads((directory/'preflight.json').read_text())
                for result in pre['results']:
                    if result['status']=='ready':continue
                    item=items[result['canonical_id']]
                    if result['status']=='confirmed':
                        try:
                            _,_,same=await inspect(cur,owner,item)
                            if not same:raise ValueError('Saved keep is no longer unchanged')
                        except Exception as exc:
                            await record_progress(cur,owner,run,item,'blocked',str(getattr(exc,'detail',str(exc))),known_records=known);continue
                    await record_progress(cur,owner,run,item,result['status'],result.get('reason',''),known_records=known)
    if not chunk:save(directory/'keeps.complete.json',{'at':datetime.now(timezone.utc).isoformat()})
    print(json.dumps({'progress_recorded':str(chunk or 'keeps-and-blockers')}),flush=True)

async def record_context_blockers(directory):
    run=load(directory);count=0
    async with await psycopg.AsyncConnection.connect('dbname=mpsc',row_factory=dict_row,options='-c jit=off')as conn:
        async with conn.cursor()as cur:
            owner=await owner_id(cur,run)
            for item in run['items']:
                if context_blocker(item):
                    await record_progress(cur,owner,run,item,'blocked',context_blocker(item));count+=1
    print(json.dumps({'context_blockers_recorded':count}),flush=True)

def child(mode,directory,chunk=None):
    # Fork the serial root coordinator's verified immutable scope, not its DB
    # connections (there are none in the parent). Every child still hashes the
    # frozen file, drops all privileges to postgres and opens fresh connections.
    # Avoid parsing the 244 MB scope twice for each 100-target chunk.
    if os.geteuid()!=0:raise ValueError('Operator child requires the root coordinator')
    sys.stdout.flush();sys.stderr.flush()
    pid=os.fork()
    if pid==0:
        try:
            account=pwd.getpwnam('postgres')
            os.initgroups(account.pw_name,account.pw_gid);os.setgid(account.pw_gid);os.setuid(account.pw_uid)
            if mode=='--preflight':asyncio.run(preflight(directory))
            elif mode=='--queue':asyncio.run(queue(directory,chunk))
            elif mode=='--record':asyncio.run(record(directory,chunk))
            else:raise ValueError('Unsupported operator child mode')
            sys.stdout.flush();sys.stderr.flush();os._exit(0)
        except BaseException:
            traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
    _,status=os.waitpid(pid,0)
    code=os.waitstatus_to_exitcode(status)
    if code:raise subprocess.CalledProcessError(code,[mode,str(directory),str(chunk)])

def execute(directory):
    if os.geteuid()!=0:raise ValueError('Guarded bank publication requires the Oracle operator')
    run=load(directory)
    if not (directory/'preflight.json').exists():child('--preflight',directory)
    pre=json.loads((directory/'preflight.json').read_text());ready=[r['canonical_id']for r in pre['results']if r['status']=='ready']
    if not (directory/'keeps.complete.json').exists():child('--record',directory)
    chunks=directory/'chunks';chunks.mkdir(exist_ok=True);os.chmod(chunks,0o2770)
    sys.path.insert(0,'/srv/study/workshop/india-study-map-app/scripts')
    from review_bank_store import sha
    bank=Path('/srv/study/workshop/mpsc-question-bankv2/bank/mpsc_bank_v2.json')
    files=[]
    for n,start in enumerate(range(0,len(ready),100),1):
        file=chunks/f'{n:04}.json'
        if not file.exists():save(file,ready[start:start+100])
        elif json.loads(file.read_text())!=ready[start:start+100]:raise ValueError('Frozen chunk membership changed')
        files.append(file)
    def states(ids):
        import importlib.util
        path=Path('/srv/study/workshop/india-study-map-app/scripts/bank-review-worker.py')
        spec=importlib.util.spec_from_file_location('taxonomy_worker',path);worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
        return worker.remote('SELECT id,state FROM bank_publications WHERE id IN('+','.join(worker.literal(i)for i in ids)+')',True)
    def complete(file):
        child('--record',directory,file)
        queued=json.loads(file.with_suffix('.queued.json').read_text())
        save(file.with_suffix('.complete.json'),{'at':datetime.now(timezone.utc).isoformat(),'count':len(queued['publications']),
             'processed':len(json.loads(file.read_text())),'blocked':len(queued.get('blocked',[])),'bank_sha256':sha(bank)})
    # Reconcile applied chunks after a crash between publication and local progress.
    for file in files:
        queued=file.with_suffix('.queued.json')
        if file.with_suffix('.complete.json').exists() or not queued.exists():continue
        ids=json.loads(queued.read_text())['publications'];rows=states(ids)
        if len(rows)==len(ids) and all(r['state']=='applied'for r in rows):complete(file)
    while pending:=[f for f in files if not f.with_suffix('.complete.json').exists()]:
        group_file=directory/'current-group.json'
        if group_file.exists():group=[chunks/name for name in json.loads(group_file.read_text())]
        else:
            group=pending[:10];save(group_file,[f.name for f in group])
        ids=[]
        for file in group:
            child('--queue',directory,file)
            ids.extend(json.loads(file.with_suffix('.publications.json').read_text()))
        publication_file=directory/'current-group-publications.json';save(publication_file,ids)
        command=[sys.executable,'/srv/study/workshop/india-study-map-app/scripts/publish-owner-review-batch.py',
                 '--publications',str(publication_file),'--taxonomy-run',str(directory/'frozen.json')]
        env={**os.environ,'ISM_DB_TRANSPORT':'local','PUBLICATION_SERIAL_QUEUE':'true'}
        if not (directory/'group-pilot-dry-run.json').exists():
            check=subprocess.run([*command,'--dry-run'],check=True,capture_output=True,text=True,env=env)
            save(directory/'group-pilot-dry-run.json',json.loads(check.stdout))
            print(json.dumps({'group_dry_run_passed':len(ids)}),flush=True)
        if ids:subprocess.run(command,check=True,env=env)
        for file in group:complete(file)
        group_file.unlink()
        done=sum(json.loads(f.with_suffix('.complete.json').read_text())['count']for f in files if f.with_suffix('.complete.json').exists())
        print(json.dumps({'published_so_far':done,'publish_total':len(ready)}),flush=True)
    print(json.dumps({'run_complete':True,'preflight_counts':pre['counts']}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    for mode in ('preflight','queue','record','run','context-blockers'):g.add_argument('--'+mode,type=Path)
    p.add_argument('--chunk',type=Path);p.add_argument('--targets',type=Path);a=p.parse_args()
    if a.run:execute(a.run)
    elif a.preflight:asyncio.run(preflight(a.preflight,a.targets))
    elif a.queue:asyncio.run(queue(a.queue,a.chunk))
    elif a.context_blockers:asyncio.run(record_context_blockers(a.context_blockers))
    else:asyncio.run(record(a.record,a.chunk))
