"""Guarded, replayable publication to the canonical local JSON bank.

Pure file operations are isolated here for tests using temporary synthetic banks.
No network requests or subprocess execution are derived from manifest content.
"""
import copy
import gzip
import shutil
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
from contextlib import contextmanager, nullcontext
from editorial_protection import check_candidate, prepare_publication, finish_publication

FIELDS={'question','direction','questionMarkup','optionsMarkup','passage','options','answerIndex',
 'answerSource','answerKeyRef','explanation','difficulty','page','qnum','hasDiagram','figureImage',
 'sourceDefect','disputeNote','classification','relatedClassifications','sourceUrl'}

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),default=str).encode()).hexdigest()

@contextmanager
def bank_lock(path):
    with open(str(path)+'.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        yield

def atomic(path,data):
    path=Path(path)
    fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.review-')
    try:
        with os.fdopen(fd,'w') as stream:
            json.dump(data,stream,ensure_ascii=False,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
        os.replace(tmp,path)
        directory=os.open(path.parent,os.O_DIRECTORY)
        try:os.fsync(directory)
        finally:os.close(directory)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def record(q):
    c=next((c for c in q.get('classifications',[]) if c.get('is_primary')), {})
    keys=['id','paperId','type','question','options','answerIndex','answerSource','answerKeyRef',
          'explanation','direction','questionMarkup','optionsMarkup','passage','difficulty','page','qnum','hasDiagram','figureImage']
    result={key:q.get(key) for key in keys}
    if result['qnum'] is not None: result['qnum']=str(result['qnum'])
    if result['answerIndex'] is not None and result['answerIndex']<0:result['answerIndex']=None
    result['explanation']=result['explanation'] or None
    result['hasDiagram']=bool(result['hasDiagram'])
    result['classification']={key:c.get(key) for key in ('subject_id','topic_id','subtopic_id')}
    related=[c for c in q.get('relatedClassifications',[]) if c.get('review_status')=='approved']
    if related:result['relatedClassifications']=sorted([{k:c.get(k) for k in ('subject_id','topic_id','subtopic_id')} for c in related if c.get('review_status')=='approved'],key=lambda c:(c['subject_id'],c.get('topic_id') or '',c.get('subtopic_id') or ''))
    return result

def transform(bank,manifest):
    """Validate all effects before returning a separate bank value."""
    out=copy.deepcopy(bank)
    p=manifest['payload'];patch=copy.deepcopy(p['patch']);kind=p['kind']
    if kind in {'duplicate','source_request'}:return out,None
    if kind=='new_question':
        qid='community_'+manifest['contribution_id'].removeprefix('con_')
        if any(q['id']==qid for q in out['questions']):raise ValueError('New question already exists without a valid receipt')
        paper=patch.pop('paperId',None) or 'Community/'+manifest['author_id']
        if not any(x['id']==paper for x in out['papers']):
            if not paper.startswith('Community/'):raise ValueError('Paper must be registered before publication')
            out['papers'].append({'id':paper,'examType':'Community','examName':'Community-authored practice',
                'kind':'mcq','sourceFile':None,'year':None,'examScopeId':'mizoram-recruitment'})
        q={'id':qid,'paperId':paper,'type':'mcq','qnum':None,'page':None,'options':[],
            'answerSource':'derived','hasDiagram':False,'classifications':[],'origin':'community',
            'contributionId':manifest['contribution_id']}
        out['questions'].append(q)
    else:
        target=manifest['baseline']['record']['id']
        q=next((q for q in out['questions'] if q['id']==target),None)
        if q is None or record(q)!=manifest['baseline']['record']:raise ValueError('Target changed; rebase and obtain new reviews')
    if set(patch)-FIELDS:raise ValueError('Manifest contains unsupported fields')
    classification=patch.pop('classification',None)
    related=patch.pop('relatedClassifications',None)
    q.update(patch)
    if classification:
        nodes={n['id']:n for n in manifest.get('taxonomy',[])}
        parent=None
        for key in ('subject_id','topic_id','subtopic_id'):
            value=classification.get(key)
            if not value:continue
            if value not in nodes or nodes[value]['parent_id']!=parent:raise ValueError('Invalid published taxonomy path')
            parent=value
        q['classifications']=[{**classification,'is_primary':True,'source':'manual',
            'review_status':'approved','confidence':1,'evidence':'Published review '+manifest['contribution_id'],
            'taxonomy_version':next(iter(nodes.values()))['version']}]
    if related is not None:
        nodes={n['id']:n for n in manifest.get('taxonomy',[])}
        if not isinstance(related,list) or len(related)>12:raise ValueError('Too many related paths')
        seen={tuple((classification or record(q)['classification']).get(k) for k in ('subject_id','topic_id','subtopic_id'))}
        cleaned=[]
        for path in related:
            if not isinstance(path,dict) or set(path)-{'subject_id','topic_id','subtopic_id'} or not path.get('subject_id'):raise ValueError('Invalid related path')
            marker=tuple(path.get(k) for k in ('subject_id','topic_id','subtopic_id'))
            if marker in seen:raise ValueError('Duplicate related path')
            seen.add(marker);parent=None
            for key,level in [('subject_id','subject'),('topic_id','topic'),('subtopic_id','subtopic')]:
                value=path.get(key)
                if not value:
                    if key=='topic_id' and path.get('subtopic_id'):raise ValueError('Subtopic requires topic')
                    continue
                if value not in nodes or nodes[value]['parent_id']!=parent or nodes[value]['level']!=level or not nodes[value].get('active',True):raise ValueError('Invalid published related path')
                parent=value
            cleaned.append({**path,'source':'manual','review_status':'approved','taxonomy_version':nodes[path['subject_id']]['version'],'evidence':'Published review '+manifest['contribution_id']})
        q['relatedClassifications']=cleaned
    # Legacy extractors used -1 for an unanswered MCQ. Source restoration
    # must preserve its unsolved state instead of treating it as an answer.
    if q.get('answerIndex') == -1 and 'answerIndex' not in patch:
        q['answerIndex']=None
    opts=q.get('options') or [];ai=q.get('answerIndex')
    if ai is not None and (type(ai) is not int or not 0<=ai<len(opts) or opts[ai] is None):raise ValueError('Published answer cannot map to an option')
    if q.get('answerSource') in {'official','key'} and not any(e['kind']=='official-key' for e in p['evidence']):
        # Existing keyed content can receive an explanation/taxonomy-only edit.
        if set(patch)&{'answerIndex','answerSource','options'}:raise ValueError('Missing mapped key evidence')
    q['reviewPublicationId']=manifest['id']
    return out,q['id']

def apply_manifest(bank_path,root,manifest,expected_manifest_hash,dry_run=False,locked=False):
    bank_path=Path(bank_path).resolve();root=Path(root).resolve()
    if not dry_run:
        from bank_authority import require_writable
        require_writable(bank_path)
    if digest(manifest)!=expected_manifest_hash or manifest.get('schema')!=1:raise ValueError('Invalid manifest hash/version')
    if not manifest['id'].startswith('pub_') or not manifest['id'].removeprefix('pub_').isalnum():raise ValueError('Invalid publication ID')
    receipts=bank_path.parent/'review-receipts';receipts.mkdir(exist_ok=True)
    receipt_path=receipts/(manifest['id']+'.json')
    with (nullcontext() if locked else bank_lock(bank_path)):
        check_candidate(bank_path)
        if receipt_path.exists():
            prior=json.loads(receipt_path.read_text())
            if prior['manifest_hash']!=expected_manifest_hash:raise ValueError('Receipt/manifest mismatch')
            # A prepared receipt is durable BEFORE bank replacement. Replaying
            # either side of that boundary is safe and requires an exact hash.
            current=sha(bank_path)
            if current==prior['output_sha256']:
                finish_publication(bank_path)
                return prior
            if prior.get('batch_id'):raise ValueError('Prepared batch must be resumed with publish-owner-review-batch.py; never apply one member separately')
            if current!=prior['input_sha256']:raise ValueError('Bank changed after prepared publication; operator reconciliation required')
        before=sha(bank_path)
        if before!=manifest['bank_sha256']:raise ValueError('Bank snapshot changed since review export')
        for doc in manifest['documents']:
            path=(root/doc['source_file']).resolve()
            if not path.is_relative_to(root) or not path.is_file() or sha(path)!=doc['sha256']:
                raise ValueError('Registered evidence file is absent or its SHA256 changed')
        if manifest['payload']['patch'].get('figureImage'):
            image=(root/manifest['payload']['patch']['figureImage']).resolve()
            if not image.is_relative_to(root/'images') or not image.is_file():raise ValueError('Figure must be an existing registered bank asset')
        bank=json.loads(bank_path.read_text())
        out,qid=transform(bank,manifest)
        encoded=(json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode()
        receipt={'publication_id':manifest['id'],'manifest_hash':expected_manifest_hash,
            'input_sha256':before,'output_sha256':hashlib.sha256(encoded).hexdigest(),
            'before_fields':{key:(manifest['baseline'].get('record',{}).get(key,[] if key=='relatedClassifications' else None) if key in {'classification','relatedClassifications'} else next((q.get(key,manifest['baseline'].get('metadata',{}).get(key)) for q in bank['questions'] if q['id']==qid),None)) for key in manifest['payload']['patch']},
            'appearance_id':qid,'before':manifest.get('baseline',{}).get('record'),
            'after':record(next(q for q in out['questions'] if q['id']==qid)) if qid else None}
        if dry_run:return receipt
        backups=bank_path.parent/'review-backups';backups.mkdir(exist_ok=True)
        if shutil.disk_usage(bank_path.parent).free<10*1024**3:raise ValueError('Less than 10 GB free; pause publishing and archive backups')
        backup=backups/(before+'.json.gz')
        if not backup.exists():
            fd=os.open(backup,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            with os.fdopen(fd,'wb') as stream:
                with gzip.GzipFile(fileobj=stream,mode='wb',compresslevel=3) as zipped:zipped.write(bank_path.read_bytes())
                stream.flush();os.fsync(stream.fileno())
        atomic(receipt_path,receipt)
        # Protect against a legacy writer that has not yet adopted the lock.
        if sha(bank_path)!=before:raise ValueError('Concurrent bank writer detected')
        prepare_publication(bank_path,bank,out,[manifest])
        atomic(bank_path,out)
        if sha(bank_path)!=receipt['output_sha256']:raise ValueError('Publication output checksum mismatch')
        finish_publication(bank_path)
        return receipt
