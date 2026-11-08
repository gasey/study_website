#!/usr/bin/env python3
"""Read-only, checksum-verified recovery copy to the operator's private storage."""
import fcntl,json,os,re,shutil,subprocess
from pathlib import Path
from review_bank_store import sha
root=Path.home()/'.local/share/ism-oracle-recovery';root.mkdir(parents=True,exist_ok=True);root.chmod(0o700)
with (root/'.pull.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 host=os.environ.get('ISM_HOST','ubuntu@152.67.31.231')
 command="sudo python3 -c 'from pathlib import Path; p=Path(\"/srv/study/backups/workshop\"); rows=sorted(x.name for x in p.iterdir() if (x/\"receipt.json\").is_file() and not (x/\"INCOMPLETE\").exists()); print(rows[-1] if rows else \"\")'"
 stamp=subprocess.check_output(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15',host,command],text=True).strip()
 if not re.fullmatch(r'[0-9]{8}T[0-9]{6}Z',stamp):raise ValueError('No complete Oracle recovery snapshot is available')
 folder=root/stamp
 if not folder.exists():
  if shutil.disk_usage(root).free<2*1024**3:raise ValueError('Less than 2 GB free; recovery copy paused')
  stage=root/('.incoming-'+stamp);stage.mkdir(mode=0o700,exist_ok=True)
  subprocess.run(['rsync','-az','--rsync-path=sudo rsync','--chmod=D700,F600',host+':/srv/study/backups/workshop/'+stamp+'/',str(stage)+'/'],check=True)
  receipt=json.loads((stage/'receipt.json').read_text())
  if sha(stage/'workshop.tar.gz')!=receipt['archive_sha256'] or sha(stage/'workflow.dump')!=receipt['database_sha256']:raise ValueError('Downloaded recovery checksum differs; partial copy retained for inspection')
  os.replace(stage,folder)
 receipt=json.loads((folder/'receipt.json').read_text())
 if sha(folder/'workshop.tar.gz')!=receipt['archive_sha256'] or sha(folder/'workflow.dump')!=receipt['database_sha256']:raise ValueError('Existing recovery copy failed verification')
 print(str(folder))
