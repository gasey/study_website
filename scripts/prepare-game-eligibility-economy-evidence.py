#!/usr/bin/env python3
"""New game eligibility proof; never rerun older frozen report targets."""
import importlib.util
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('game_eligibility_proof',ROOT/'scripts/prepare-learning-eligibility-economy-evidence.py')
learning=importlib.util.module_from_spec(spec);spec.loader.exec_module(learning)
proof=learning.proof
proof.REPORT=ROOT/'reports/finna-game-eligibility-20261120'
proof.PROOF_FILES=tuple(dict.fromkeys((*proof.PROOF_FILES,
    'api/tests/test_game_eligibility.py','scripts/rehearse-game-eligibility-index.py',
    'scripts/prepare-game-eligibility-economy-evidence.py')))

if __name__=='__main__':
    assert sys.argv[1:] in ([],['--run-tests'])
    proof.REPORT.mkdir(exist_ok=True)
    assert not (proof.REPORT/'validation.json').exists(),'Frozen report; create a new target'
    if sys.argv[1:]:proof.run_fixtures()
    proof.main()
