#!/usr/bin/env python3
"""Fresh shared-subject visibility proof; preserve all prior frozen targets."""
import importlib.util
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('community_eligibility_proof',ROOT/'scripts/prepare-assessment-eligibility-economy-evidence.py')
assessment=importlib.util.module_from_spec(spec);spec.loader.exec_module(assessment)
proof=assessment.proof
proof.REPORT=ROOT/'reports/finna-community-eligibility-20261120'
proof.PROOF_FILES=tuple(dict.fromkeys((*proof.PROOF_FILES,
    'api/tests/test_community_eligibility.py','api/tests/test_creator_profiles.py',
    'api/tests/test_community_people.py','api/tests/test_discussions.py','api/tests/test_study_posts.py',
    'api/tests/test_material_shares.py','api/tests/test_content_studio.py','api/tests/test_inbox.py',
    'scripts/prepare-community-eligibility-economy-evidence.py')))

if __name__=='__main__':
    assert sys.argv[1:] in ([],['--run-tests'])
    proof.REPORT.mkdir(exist_ok=True)
    assert not (proof.REPORT/'validation.json').exists(),'Frozen report; use a new target'
    if sys.argv[1:]:proof.run_fixtures()
    proof.main()
