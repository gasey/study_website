#!/usr/bin/env python3
"""Fresh privacy/audience compatibility proof. Never reruns frozen output targets."""
import importlib.util
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('privacy_compatibility',ROOT/'scripts/prepare-empty-pins-economy-evidence.py')
proof=importlib.util.module_from_spec(spec);spec.loader.exec_module(proof)
proof.REPORT=ROOT/'reports/finna-privacy-implementation-20261120'
proof.PROOF_FILES=tuple(dict.fromkeys((*proof.PROOF_FILES,'api/tests/test_account_privacy.py','web/scripts/check-privacy.cjs','scripts/prepare-privacy-economy-evidence.py')))

if __name__=='__main__':
    assert sys.argv[1:] in ([],['--run-tests'])
    proof.REPORT.mkdir(exist_ok=True)
    if sys.argv[1:]:
        assert not (proof.REPORT/'validation.json').exists(),'Frozen report; create a new target'
        proof.run_fixtures()
    proof.main()
