#!/usr/bin/env python3
"""Candidate modules under mpsc/read-only; no live API, DB or service writes."""
import hashlib,json,shlex,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];REPORT=ROOT/'reports/finnaplan-v10-vocabulary-proof-20261118';HOST='ubuntu@152.67.31.231'
def run(args):return subprocess.run(args,check=True,capture_output=True,text=True).stdout.strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    files={'vocabulary_decks.py':ROOT/'api/app/services/vocabulary_decks.py','vocabulary.py':ROOT/'api/app/routers/vocabulary.py','verify.py':ROOT/'scripts/verify-finnaplan-v10-vocabulary.py'}
    hashes={k:sha(v) for k,v in files.items()}
    stage=run(['ssh',HOST,'mktemp -d /tmp/finna-vocabulary-read.XXXXXX']);assert stage.startswith('/tmp/finna-vocabulary-read.') and '\n' not in stage
    try:
        for n,p in files.items():run(['rsync','-az',str(p),HOST+':'+stage+'/'+n])
        run(['ssh',HOST,'chmod 755 '+shlex.quote(stage)])
        command='sudo -u postgres /srv/api/.venv/bin/python '+shlex.quote(stage+'/verify.py')+' '+shlex.quote(stage+'/vocabulary_decks.py')+' '+shlex.quote(stage+'/vocabulary.py')
        result=json.loads(run(['ssh',HOST,command]));assert all(sha(p)==hashes[n] for n,p in files.items())
    finally:run(['ssh',HOST,'rm -rf -- '+shlex.quote(stage)])
    output={'candidate_sha256':hashes,'verification':result,'migration_changes':False,'live_api_or_service_changes':False,'database_writes':False,'stage_removed':True}
    (REPORT/'read-rehearsal.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))
if __name__=='__main__':main()
