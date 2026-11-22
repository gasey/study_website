#!/usr/bin/env python3
"""New publication reward proof; preserve all frozen predecessor reports."""
import importlib.util
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('publication_audience_proof',ROOT/'scripts/prepare-synchronous-activity-economy-evidence.py')
activity=importlib.util.module_from_spec(spec);spec.loader.exec_module(activity)
proof=activity.proof
proof.REPORT=ROOT/'reports/finna-publication-eligibility-20261120'
proof.PROOF_FILES=tuple(dict.fromkeys((*proof.PROOF_FILES,
    'api/tests/test_publication_eligibility.py','api/tests/test_contribution_rewards_v2.py',
    'api/tests/test_bank_review.py','scripts/bank-review-worker.py',
    'scripts/rehearse-publication-eligibility.py',
    'scripts/prepare-publication-eligibility-economy-evidence.py')))

if __name__=='__main__':
    assert sys.argv[1:] in ([],['--run-tests'])
    proof.REPORT.mkdir(exist_ok=True)
    assert not (proof.REPORT/'validation.json').exists(),'Frozen report; use a new target'
    if sys.argv[1:]:proof.run_fixtures()
    proof.main()
