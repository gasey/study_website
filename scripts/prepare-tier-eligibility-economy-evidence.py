#!/usr/bin/env python3
"""New database community tier proof; preserve all frozen predecessor reports."""
import importlib.util
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('tier_eligibility_proof',ROOT/'scripts/prepare-contributor-visibility-economy-evidence.py')
contributor=importlib.util.module_from_spec(spec);spec.loader.exec_module(contributor)
proof=contributor.proof
proof.REPORT=ROOT/'reports/finna-tier-eligibility-20261120'
proof.PROOF_FILES=tuple(dict.fromkeys((*proof.PROOF_FILES,
    'api/tests/test_tier_eligibility.py','scripts/rehearse-tier-eligibility.py','scripts/rehearse-tier-lookup.py',
    'scripts/prepare-tier-eligibility-economy-evidence.py')))
if __name__=='__main__':
    assert sys.argv[1:] in ([],['--run-tests'])
    proof.REPORT.mkdir(exist_ok=True)
    assert not (proof.REPORT/'validation.json').exists(),'Frozen report; use a new target'
    if sys.argv[1:]:proof.run_fixtures()
    proof.main()
