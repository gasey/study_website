#!/usr/bin/env python3
"""Stage candidate reads under mpsc/read-only; no migration or live API changes."""
import hashlib,json,shlex,subprocess,tempfile
from pathlib import Path
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parents[1];REPORT=ROOT/'reports/finnaplan-v10-submissions-20261118';HOST='ubuntu@152.67.31.231'
def run(args,**kwargs):return subprocess.run(args,check=True,capture_output=True,text=True,**kwargs).stdout.strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
FILES=['app/services/submissions.py','app/routers/community.py']
def main():
    hashes={n:sha(ROOT/'api'/n) for n in FILES}
    stage=run(['ssh',HOST,'mktemp -d /tmp/finna-submissions-read.XXXXXX']);assert stage.startswith('/tmp/finna-submissions-read.') and '\n' not in stage
    try:
        run(['rsync','-az',str(ROOT/'api/app/services/submissions.py'),str(ROOT/'scripts/verify-finnaplan-v10-submissions.py'),HOST+':'+stage+'/'])
        run(['ssh',HOST,'chmod 755 '+shlex.quote(stage)])
        command='sudo -u postgres /srv/api/.venv/bin/python '+shlex.quote(stage+'/verify-finnaplan-v10-submissions.py')+' '+shlex.quote(stage+'/submissions.py')
        verification=json.loads(run(['ssh',HOST,command]))
        health={}
        for host in ('study.hawayu.in','family.hawayu.in'):
            with urlopen('https://'+host,timeout=30) as r:assert r.status==200;health[host]=r.status
        assert all(sha(ROOT/'api'/n)==v for n,v in hashes.items())
        output={'candidate_sha256':hashes,'verification':verification,'migration_changes':False,'live_api_or_service_changes':False,'database_writes':False,'both_site_health':health}
    finally:run(['ssh',HOST,'rm -rf -- '+shlex.quote(stage)])
    output['stage_removed']=True;(REPORT/'read-rehearsal.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))
if __name__=='__main__':main()
