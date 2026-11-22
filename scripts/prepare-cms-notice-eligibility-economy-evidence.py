#!/usr/bin/env python3
"""Fresh CMS and workflow notice proof; preserve frozen predecessor reports."""
import importlib.util
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('cms_notice_proof',ROOT/'scripts/prepare-tier-eligibility-economy-evidence.py')
tier=importlib.util.module_from_spec(spec);spec.loader.exec_module(tier)
proof=tier.proof
proof.REPORT=ROOT/'reports/finna-cms-notice-eligibility-20261120'
proof.PROOF_FILES=tuple(dict.fromkeys((*proof.PROOF_FILES,
    'api/tests/test_cms_notice_eligibility.py','api/tests/test_content_studio.py',
    'api/tests/test_publication_eligibility.py','api/tests/test_bank_review.py','api/tests/test_inbox.py',
    'scripts/bank-review-worker.py','scripts/rehearse-cms-notice-eligibility.py',
    'scripts/prepare-cms-notice-eligibility-economy-evidence.py')))
if __name__=='__main__':
    assert sys.argv[1:] in ([],['--run-tests'])
    proof.REPORT.mkdir(exist_ok=True)
    assert not (proof.REPORT/'validation.json').exists(),'Frozen report; use a new target'
    if sys.argv[1:]:proof.run_fixtures()
    proof.main()
