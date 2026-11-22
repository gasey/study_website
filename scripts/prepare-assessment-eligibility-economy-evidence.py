#!/usr/bin/env python3
"""Fresh assessment admission compatibility receipt; older targets stay frozen."""
import importlib.util
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('assessment_eligibility_proof',ROOT/'scripts/prepare-game-eligibility-economy-evidence.py')
games=importlib.util.module_from_spec(spec);spec.loader.exec_module(games)
proof=games.proof
proof.REPORT=ROOT/'reports/finna-reassessment-eligibility-20261120'
proof.PROOF_FILES=tuple(dict.fromkeys((*proof.PROOF_FILES,
    'api/tests/test_assessment_eligibility.py','api/tests/test_scoring_revisions.py',
    'api/tests/test_learning_workflows.py','scripts/prepare-assessment-eligibility-economy-evidence.py')))

if __name__=='__main__':
    assert sys.argv[1:] in ([],['--run-tests'])
    proof.REPORT.mkdir(exist_ok=True)
    assert not (proof.REPORT/'validation.json').exists(),'Frozen report; use a new target'
    if sys.argv[1:]:proof.run_fixtures()
    proof.main()
