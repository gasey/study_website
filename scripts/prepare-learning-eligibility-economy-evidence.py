#!/usr/bin/env python3
"""Fresh eligibility/learning compatibility proof; older receipts stay frozen."""
import importlib.util
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('learning_eligibility_proof',ROOT/'scripts/prepare-audience-background-economy-evidence.py')
background=importlib.util.module_from_spec(spec);spec.loader.exec_module(background)
proof=background.proof
proof.REPORT=ROOT/'reports/finna-learning-eligibility-20261120'
proof.PROOF_FILES=tuple(dict.fromkeys((*proof.PROOF_FILES,
    'api/tests/test_learning_eligibility.py','api/tests/test_learning_loop.py',
    'scripts/prepare-learning-eligibility-economy-evidence.py')))

if __name__=='__main__':
    assert sys.argv[1:] in ([],['--run-tests'])
    proof.REPORT.mkdir(exist_ok=True)
    assert not (proof.REPORT/'validation.json').exists(),'Frozen report; create a new target'
    if sys.argv[1:]:proof.run_fixtures()
    proof.main()
