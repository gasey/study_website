#!/usr/bin/env python3
"""Bind the successful isolated calibration/recovery to exact release sources."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'api'))
from app.services.reward_economy import RELEASE_FILES
report=ROOT/'reports/finnaplan-v4-20261117'
log=(report/'recovery-and-calibration-tests.txt').read_text()
assert '3 passed' in log
payload={'rule_version':'learning-v2','evidence':'reports/finnaplan-v4-20261117',
 'source_sha256':{n:hashlib.sha256((ROOT/'api'/n).read_bytes()).hexdigest() for n in RELEASE_FILES},
 'calibration':json.loads((report/'calibration.json').read_text()),'recovery':json.loads((report/'recovery.json').read_text()),
 'fixture_tests_sha256':hashlib.sha256((report/'recovery-and-calibration-tests.txt').read_bytes()).hexdigest()}
target=ROOT/'api/app/data/learning-economy-v2.json';target.write_text(json.dumps(payload,indent=2)+'\n')
from app.services.reward_economy import reconciled_release
assert reconciled_release()
print('Release-bound calibration evidence prepared:',target)
