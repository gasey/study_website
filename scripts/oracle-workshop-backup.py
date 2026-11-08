#!/usr/bin/env python3
"""Root-only paired bank/workflow recovery snapshot. No pruning or cloud upload."""
import hashlib,json,os,subprocess,sys,tarfile,tempfile
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from review_bank_store import bank_lock,sha,atomic
from bank_authority import require_writable,CANONICAL
root=CANONICAL.parent.parent;dest=Path('/srv/study/backups/workshop');dest.mkdir(parents=True,exist_ok=True);dest.chmod(0o700)
require_writable(CANONICAL)
with bank_lock(CANONICAL):
 stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');folder=dest/stamp;folder.mkdir(mode=0o700)
 try:
  checksum=sha(CANONICAL)
  live=subprocess.check_output(['sudo','-u','postgres','psql','-d','mpsc','-Atc','SELECT bank_checksum FROM sync_log WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1'],text=True).strip()
  if checksum!=live:raise ValueError('Canonical bank is not fully synced; reconcile before backup')
  subprocess.run(['sudo','-u','postgres','pg_dump','-Fc','mpsc'],stdout=(folder/'workflow.dump').open('wb'),check=True)
  with tarfile.open(folder/'workshop.tar.gz','w:gz',compresslevel=3) as archive:
   for rel in ['bank/mpsc_bank_v2.json','bank/review-receipts','taxonomies','state/editorial-protection']:
    archive.add(root/rel,arcname='bank-workshop/'+rel)
   private=Path('/srv/study/private/paper-workbench')
   if private.exists():archive.add(private,arcname='paper-workbench',filter=lambda item:None if any(p.startswith('.') for p in Path(item.name).parts) else item)
   archive.add(Path(__file__).parent/'bank-authority-policy.json',arcname='bank-authority-policy.json')
  # Read through the archived bank, rather than merely checking tar headers.
  with tarfile.open(folder/'workshop.tar.gz') as archive:
   data=archive.extractfile('bank-workshop/bank/mpsc_bank_v2.json').read()
   if hashlib.sha256(data).hexdigest()!=checksum:raise ValueError('Bank recovery hash mismatch')
   bank=json.loads(data)
  subprocess.run(['pg_restore','--list',folder/'workflow.dump'],stdout=subprocess.DEVNULL,check=True)
  atomic(folder/'receipt.json',{'schema':1,'created_at':stamp,'bank_sha256':checksum,'questions':len(bank['questions']),'papers':len(bank['papers']),'archive_sha256':sha(folder/'workshop.tar.gz'),'database_sha256':sha(folder/'workflow.dump'),'original_sources':'Immutable PDFs and figures remain in the canonical workshop and pre-cutover local recovery copy. Copy sources separately for full disaster recovery.','offsite':'Not uploaded by this job'})
  print(str(folder))
 except Exception:
  # Keep partial evidence for operator investigation. Never claim a complete backup.
  (folder/'INCOMPLETE').touch();raise
