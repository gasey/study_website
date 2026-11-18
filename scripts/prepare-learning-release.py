#!/usr/bin/env python3
"""Freeze the reviewed V.4 candidate against the fresh read-only live audit."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/finnaplan-v4-20261117'
sys.path.insert(0,str(ROOT/'api'))
from app.services.reward_economy import RELEASE_FILES,reconciled_release
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert '1035 passed' in (REPORT/'backend-tests.txt').read_text()
assert 'built in' in (REPORT/'web-build.txt').read_text()
assert reconciled_release()
audit=json.loads((REPORT/'live-audit.json').read_text());audit.pop('directory')
audit['api_preimages']['app/data/learning-economy-v2.json']=None
files=[n for n in RELEASE_FILES if n.startswith('app/')]+['app/data/learning-economy-v2.json']
manifest={'api':{n:sha(ROOT/'api'/n) for n in files},
 'migrations':{Path(n).name:sha(ROOT/'api'/n) for n in RELEASE_FILES if n.startswith('migrations/')},
 'web':{str(p.relative_to(ROOT/'web/dist')):sha(p) for p in (ROOT/'web/dist').rglob('*') if p.is_file()}}
helpers=['scripts/deploy-finnaplan-v4.py','scripts/rollback-finnaplan-v4.py','scripts/learning-economy-recovery.py',
 'scripts/verify-learning-release.py','scripts/rehearse-learning-release.py','scripts/prepare-learning-economy-evidence.py','scripts/prepare-learning-release.py']
scope=audit|{'candidate':manifest,'operator_files':{n:sha(ROOT/n) for n in helpers},
 'scope':'V.4 economy; exactly 11 API Python sources + release-bound calibration JSON, 0094–0096 and reviewed local web build',
 'excluded':'canonical bank, workshop, provider/configuration, dependency installs, unit files and shared Caddy'}
(REPORT/'release-scope.json').write_text(json.dumps(scope,indent=2)+'\n')
print('Frozen:',len(manifest['api']),'API artifacts,',len(manifest['migrations']),'migrations,',len(manifest['web']),'static artifacts')
