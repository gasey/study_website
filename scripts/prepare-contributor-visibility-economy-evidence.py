#!/usr/bin/env python3
"""Fresh legacy contributor/voter read proof; preserve frozen predecessors."""
import importlib.util
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('contributor_visibility_proof',ROOT/'scripts/prepare-publication-eligibility-economy-evidence.py')
publication=importlib.util.module_from_spec(spec);spec.loader.exec_module(publication)
proof=publication.proof
proof.REPORT=ROOT/'reports/finna-contributor-visibility-20261120'
proof.PROOF_FILES=tuple(dict.fromkeys((*proof.PROOF_FILES,
    'api/tests/test_contributor_visibility.py',
    'scripts/prepare-contributor-visibility-economy-evidence.py')))

if __name__=='__main__':
    assert sys.argv[1:] in ([],['--run-tests'])
    proof.REPORT.mkdir(exist_ok=True)
    assert not (proof.REPORT/'validation.json').exists(),'Frozen report; use a new target'
    if sys.argv[1:]:proof.run_fixtures()
    proof.main()
