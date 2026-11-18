#!/usr/bin/env python3
"""Run the source-bound isolated rehearsal once; no live API/static deployment."""
import hashlib,json,shlex,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/finnaplan-v12-maintenance-20261118'
HOST='ubuntu@152.67.31.231'

def run(args):
 p=subprocess.run(args,text=True,capture_output=True)
 if p.returncode:raise RuntimeError(p.stderr[-4000:])
 return p.stdout

if __name__=='__main__':
 source=ROOT/'scripts/rehearse-monthly-restore.py';digest=hashlib.sha256(source.read_bytes()).hexdigest()
 stage=run(['ssh',HOST,'mktemp -d /tmp/finna-monthly-restore-stage.XXXXXX']).strip()
 assert stage.startswith('/tmp/finna-monthly-restore-stage.') and '\n' not in stage
 try:
  run(['rsync','-az',str(source),HOST+':'+stage+'/restore.py'])
  remote_hash=run(['ssh',HOST,'sha256sum '+shlex.quote(stage+'/restore.py')]).split()[0];assert remote_hash==digest
  result=run(['ssh',HOST,'sudo /srv/api/.venv/bin/python '+shlex.quote(stage+'/restore.py')+' --run'])
  receipt=json.loads(result.strip().splitlines()[-1]);assert receipt['receipt']['operator_sha256']==digest
  (REPORT/'actual-restore.json').write_text(json.dumps(receipt,indent=2)+'\n')
  assert receipt['state']=='verified',receipt['state']
  print('Actual paired restore completed and cleaned; receipt saved to '+str(REPORT/'actual-restore.json'))
 finally:run(['ssh',HOST,'sudo rm -rf -- '+shlex.quote(stage)])
