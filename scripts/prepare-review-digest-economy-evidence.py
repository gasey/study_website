#!/usr/bin/env python3
"""Bind fresh community calibration and compatibility recovery to exact artifacts."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT/'reports/finna-review-digest-staged-20261119'
sys.path.insert(0, str(ROOT/'api'))
from app.services.reward_economy import RELEASE_FILES, reconciled_release
PROOF_FILES = ('api/tests/test_v5_recovery.py', 'api/tests/test_economy_recovery.py',
               'api/tests/test_reward_calibration.py', 'api/tests/test_economy_launch.py', 'api/tests/test_mobile_companion.py',
               'api/tests/test_curated_vocabulary.py','api/tests/test_account_mail_automation.py','api/tests/test_public_share.py','api/tests/test_onboarding.py','api/tests/test_onboarding_recovery.py','api/tests/test_bulk_rates.py','api/tests/test_bulk_rates_recovery.py','api/tests/test_bulk_rate_audit.py','api/tests/test_worker_health.py','api/tests/test_ops_collector.py','api/tests/test_ops.py','api/tests/test_account_retention.py','api/tests/test_site_notice.py','api/tests/test_account_viewer.py','api/tests/test_account_viewer_recovery.py','api/tests/test_question_detail_readiness.py','api/tests/test_desk_goals.py','api/tests/test_desk_review_circle.py','api/tests/test_desk_focus_board.py','api/tests/test_desk_practice.py','api/tests/test_games_search.py','api/tests/test_completion_awards.py','api/tests/test_desk_notes.py','api/tests/test_desk_calendar.py','api/tests/test_atlas_bindings.py','api/tests/test_atlas_studio.py','api/tests/test_review_digest.py','api/tests/test_atlas_context.py','api/tests/test_atlas_drills.py','api/tests/test_learning_habit.py','api/tests/test_browse_allowance.py','api/tests/test_public_browse_cache.py','api/tests/test_owned_calendar.py','api/tests/test_account_tools.py','api/tests/test_study_desks.py',
               'scripts/recover-finnaplan-v5.py', 'scripts/prepare-review-digest-economy-evidence.py')
OUTPUTS = ('calibration.json', 'economy-recovery.json', 'v5-recovery.json')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_fixtures():
    sources = {name: sha(ROOT/'api'/name) for name in RELEASE_FILES}
    proofs = {name: sha(ROOT/name) for name in PROOF_FILES}
    env = os.environ.copy()
    for key, name in zip(('FINNA_CALIBRATION_REPORT', 'FINNA_RECOVERY_REPORT', 'FINNA_V5_RECOVERY_REPORT'), OUTPUTS):
        env[key] = str(REPORT/name)
    with (REPORT/'recovery-and-calibration-tests.txt').open('w') as output:
        result = subprocess.run([sys.executable, '-m', 'pytest', *PROOF_FILES[:-2], '-q'], cwd=ROOT,
                                env=env, stdout=output, stderr=subprocess.STDOUT)
    assert sources == {name: sha(ROOT/'api'/name) for name in RELEASE_FILES}
    assert proofs == {name: sha(ROOT/name) for name in PROOF_FILES}
    run = {'exit_code': result.returncode, 'source_sha256': sources, 'proof_source_sha256': proofs,
           'log_sha256': sha(REPORT/'recovery-and-calibration-tests.txt')}
    if result.returncode == 0:
        run['output_sha256'] = {name: sha(REPORT/name) for name in OUTPUTS}
    (REPORT/'fixture-run.json').write_text(json.dumps(run, indent=2)+'\n')
    assert result.returncode == 0, 'Fixture failed; see the recorded test output'


def main():
    log = REPORT/'recovery-and-calibration-tests.txt'
    import re
    assert re.search(r'\b[1-9][0-9]* passed\b',log.read_text()) and 'failed' not in log.read_text()
    # Evidence preparation fails if a runtime input changed after the fixture run.
    run = json.loads((REPORT/'fixture-run.json').read_text())
    assert run['exit_code'] == 0
    assert run['log_sha256'] == sha(log)
    sources = {name: sha(ROOT/'api'/name) for name in RELEASE_FILES}
    assert sources == run['source_sha256'], 'Sources changed after fixture run'
    proof_sources = {name: sha(ROOT/name) for name in PROOF_FILES}
    assert proof_sources == run['proof_source_sha256'], 'Proof changed after fixture run'
    assert {name: sha(REPORT/name) for name in OUTPUTS} == run['output_sha256']
    payload = {'rule_version': 'learning-v2', 'evidence': str(REPORT.relative_to(ROOT)),
               'source_sha256': sources,
               'calibration': json.loads((REPORT/'calibration.json').read_text()),
               'recovery': json.loads((REPORT/'economy-recovery.json').read_text()),
               'v5_recovery': json.loads((REPORT/'v5-recovery.json').read_text()),
               'fixture_tests_sha256': sha(log), 'proof_source_sha256': proof_sources}
    target = ROOT/'api/app/data/learning-economy-v2.json'
    target.write_text(json.dumps(payload, indent=2)+'\n')
    assert reconciled_release()
    print('Atlas context compatibility evidence prepared:', len(sources), 'source bindings; 25 integrity checks; compatibility recovery passed')


if __name__ == '__main__':
    assert sys.argv[1:] in ([], ['--run-tests'])
    if sys.argv[1:]:
        run_fixtures()
    main()
