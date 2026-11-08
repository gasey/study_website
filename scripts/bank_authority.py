"""One physical writable canonical bank; local copies become read-only snapshots."""
import hashlib,json
from pathlib import Path
APP=Path(__file__).resolve().parents[1]
CANONICAL=APP.parent/'mpsc-question-bankv2/bank/mpsc_bank_v2.json'
POLICY=APP/'scripts/bank-authority-policy.json'
def machine_fingerprint():return hashlib.sha256(Path('/etc/machine-id').read_bytes().strip()).hexdigest()
def require_writable(bank_path,force=False,policy_path=None):
 bank=Path(bank_path).resolve()
 if not force and bank!=CANONICAL.resolve():return
 policy=Path(policy_path or POLICY)
 if not policy.is_file():raise ValueError('Canonical authority policy is missing; do not publish from this checkout')
 p=json.loads(policy.read_text())
 if p.get('schema')!=1 or bank!=(Path(p['writable_root'])/'bank/mpsc_bank_v2.json').resolve() or machine_fingerprint()!=p.get('machine_sha256'):
  raise ValueError('This is a read-only bank snapshot. Publish through the authoritative Oracle workspace; do not force a local sync.')
if __name__=='__main__':
 import sys
 require_writable(sys.argv[1],force=True)
 print('Canonical write authority verified')
