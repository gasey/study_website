#!/usr/bin/env python3
"""Fresh activity/adoption proof; never overwrite an earlier frozen report."""
import importlib.util
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('activity_audience_proof',ROOT/'scripts/prepare-community-eligibility-economy-evidence.py')
community=importlib.util.module_from_spec(spec);spec.loader.exec_module(community)
proof=community.proof
proof.REPORT=ROOT/'reports/finna-synchronous-activity-20261120'
proof.PROOF_FILES=tuple(dict.fromkeys((*proof.PROOF_FILES,
    'api/tests/test_synchronous_activity_audience.py','api/tests/test_account_hardening.py',
    'scripts/rehearse-synchronous-activity-audience.py',
    'scripts/prepare-synchronous-activity-economy-evidence.py')))

if __name__=='__main__':
    assert sys.argv[1:] in ([],['--run-tests'])
    proof.REPORT.mkdir(exist_ok=True)
    assert not (proof.REPORT/'validation.json').exists(),'Frozen report; use a new target'
    if sys.argv[1:]:proof.run_fixtures()
    proof.main()
