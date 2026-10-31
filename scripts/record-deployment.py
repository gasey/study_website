#!/usr/bin/env python3
"""Read-only SHA256 comparison of deployed API/static files; no secrets read."""
from pathlib import Path
import argparse,datetime,hashlib,json,shlex,subprocess
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    api={str(p.relative_to(ROOT/'api')):sha(p) for p in (ROOT/'api/app').rglob('*.py')};api['requirements.txt']=sha(ROOT/'api/requirements.txt')
    web={str(p.relative_to(ROOT/'web/dist')):sha(p) for p in (ROOT/'web/dist').rglob('*') if p.is_file()}
    code="from pathlib import Path;import hashlib,json;r=Path('/srv/api');w=Path('/srv/study/public');a={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*.py')};a['requirements.txt']=hashlib.sha256((r/'requirements.txt').read_bytes()).hexdigest();b={str(p.relative_to(w)):hashlib.sha256(p.read_bytes()).hexdigest() for p in w.rglob('*') if p.is_file()};print(json.dumps({'api':a,'web':b}))"
    result=subprocess.run(['ssh','ubuntu@152.67.31.231','sudo','python3','-c',shlex.quote(code)],text=True,capture_output=True,check=True,timeout=60)
    live=json.loads(result.stdout)
    if api!=live['api'] or web!=live['web']:raise SystemExit('Local/server artifact mismatch')
    manifest={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'git_base':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'checkout_dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),'server_artifacts_verified_equal':True,'api':api,'web':web,'migrations':{p.name:sha(p) for p in (ROOT/'api/migrations').glob('[0-9][0-9][0-9][0-9]_*.sql')}}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Verified {len(api)} API files and {len(web)} static artifacts match production.')
if __name__=='__main__':main()
