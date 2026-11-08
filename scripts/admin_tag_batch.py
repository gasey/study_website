"""Bounded atomic publication of explicit admin tag decisions from one snapshot."""
import gzip
import hashlib
import json
import os
import shutil
from pathlib import Path
from contextlib import nullcontext
from review_bank_store import atomic,bank_lock,digest,sha,record,transform
from editorial_protection import check_candidate,prepare_publication,finish_publication


def apply_admin_tag_batch(bank_path,root,publications,dry_run=False,locked=False):
    bank_path=Path(bank_path).resolve();root=Path(root).resolve()
    if not dry_run:
        from bank_authority import require_writable
        require_writable(bank_path)
    if not 1<=len(publications)<=20:raise ValueError('Admin tag batches contain 1–20 exact decisions')
    publications=sorted(publications,key=lambda p:p['id'])
    manifests=[p['manifest'] for p in publications]
    canonical=[]
    for pub in publications:
        m=pub['manifest'];p=m['payload']
        if (digest(m)!=pub['manifest_hash'] or m.get('schema')!=1 or not m.get('admin_edit')
            or m['admin_edit'].get('kind')!='taxonomy' or p.get('kind')!='taxonomy'
            or not p.get('canonical_id') or not p.get('patch') or set(p['patch'])-{'classification','relatedClassifications'}):
            raise ValueError('Only immutable final admin tag corrections qualify for this batch')
        canonical.append(p['canonical_id'])
    if len(set(canonical))!=len(canonical):raise ValueError('Choose each shared question once')
    bid='admin_tags_'+digest([p['id'] for p in publications])[:32]
    directory=bank_path.parent/'review-batches';journal_path=directory/(bid+'.json')
    with (nullcontext() if locked else bank_lock(bank_path)):
        check_candidate(bank_path)
        current=sha(bank_path)
        journal=json.loads(journal_path.read_text()) if journal_path.exists() else None
        if journal:
            if ({r['publication_id']:r['manifest_hash'] for r in journal['receipts']}!={p['id']:p['manifest_hash'] for p in publications}
                or current not in (journal['input_sha256'],journal['output_sha256'])):
                raise ValueError('Prepared admin tag batch changed; explicit reconciliation is required')
            if current==journal['output_sha256']:
                if not dry_run:finish_publication(bank_path)
                return journal
        if any(m['bank_sha256']!=current for m in manifests):
            raise ValueError('Bank snapshot changed since the tag preview; reopen the corrections')
        raw=bank_path.read_bytes();bank=json.loads(raw);by_id={q['id']:q for q in bank['questions']}
        changes={};receipts=[]
        for pub in publications:
            m=pub['manifest'];target=m['baseline']['record']['id']
            if target in changes or target not in by_id:raise ValueError('Tag targets must be distinct existing sources')
            for doc in m['documents']:
                path=(root/doc['source_file']).resolve()
                if not path.is_relative_to(root) or not path.is_file() or sha(path)!=doc['sha256']:
                    raise ValueError('Registered tag evidence changed')
            # Transform only this source; avoid copying the complete bank for each question.
            changed,_=transform({'questions':[by_id[target]],'papers':[]},m)
            changes[target]=changed['questions'][0]
            receipts.append({'publication_id':pub['id'],'manifest_hash':pub['manifest_hash'],'batch_id':bid,
              'input_sha256':current,'appearance_id':target,'before':m['baseline']['record'],
              'before_fields':{k:m['baseline']['record'].get(k,[] if k=='relatedClassifications' else None) for k in m['payload']['patch']},
              'after':record(changes[target])})
        output={**bank,'questions':[changes.get(q['id'],q) for q in bank['questions']]}
        output_sha=hashlib.sha256((json.dumps(output,ensure_ascii=False,indent=2)+'\n').encode()).hexdigest()
        for receipt in receipts:receipt['output_sha256']=output_sha
        prepared={'schema':1,'batch_id':bid,'input_sha256':current,'output_sha256':output_sha,'receipts':receipts}
        if journal and prepared!=journal:raise ValueError('Prepared tag output changed')
        if dry_run:return prepared
        if shutil.disk_usage(bank_path.parent).free<10*1024**3:raise ValueError('Less than 10 GB free; pause publishing')
        backups=bank_path.parent/'review-backups';backups.mkdir(exist_ok=True)
        backup=backups/(current+'.json.gz')
        if not backup.exists():
            fd=os.open(backup,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            with os.fdopen(fd,'wb') as stream:
                with gzip.GzipFile(fileobj=stream,mode='wb',compresslevel=3) as zipped:zipped.write(raw)
                stream.flush();os.fsync(stream.fileno())
        directory.mkdir(exist_ok=True);atomic(journal_path,prepared)
        receipt_dir=bank_path.parent/'review-receipts';receipt_dir.mkdir(exist_ok=True)
        for receipt in receipts:atomic(receipt_dir/(receipt['publication_id']+'.json'),receipt)
        if sha(bank_path)!=current:raise ValueError('Concurrent bank writer detected')
        prepare_publication(bank_path,bank,output,manifests)
        atomic(bank_path,output)
        if sha(bank_path)!=output_sha:raise ValueError('Admin tag output checksum mismatch')
        finish_publication(bank_path)
        return prepared
