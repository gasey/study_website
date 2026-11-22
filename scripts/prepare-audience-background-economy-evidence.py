#!/usr/bin/env python3
"""New background-age compatibility receipt; refuses an already frozen target."""
import importlib.util
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('audience_background_proof',ROOT/'scripts/prepare-privacy-economy-evidence.py')
privacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(privacy)
proof=privacy.proof
proof.REPORT=ROOT/'reports/finna-audience-background-20261120'
proof.PROOF_FILES=tuple(dict.fromkeys((*proof.PROOF_FILES,
    'api/tests/test_audience_background.py','api/tests/test_calendar.py','api/tests/test_weekly_boards.py',
    'scripts/prepare-audience-background-economy-evidence.py')))

if __name__=='__main__':
    assert sys.argv[1:] in ([],['--run-tests'])
    proof.REPORT.mkdir(exist_ok=True)
    assert not (proof.REPORT/'validation.json').exists(),'Frozen report; create a new target'
    if sys.argv[1:]:proof.run_fixtures()
    proof.main()
