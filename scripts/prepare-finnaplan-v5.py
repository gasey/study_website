#!/usr/bin/env python3
"""Freeze only reviewed V.5 artifacts against a fresh read-only live audit."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT/'reports/finnaplan-v5-recovery-20261117'
sys.path.insert(0, str(ROOT/'api'))
from app.services.reward_economy import RELEASE_FILES, reconciled_release


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert reconciled_release()
    assert '1081 passed' in (REPORT/'backend-tests.txt').read_text()
    assert 'built in' in (REPORT/'web-build.txt').read_text()
    rehearsal = json.loads((REPORT/'migration-rehearsal.json').read_text())
    assert rehearsal['all_existing_columns_and_rows_preserved'] and rehearsal['clone_and_dump_removed']
    assert rehearsal['source_bound_economy_ready']
    assert rehearsal['release_read_only_flow']['transactions_read_only']
    assert rehearsal['release_read_only_flow']['account_users_checked'] > 0
    assert rehearsal['verifier_sha256'] == sha(ROOT/'scripts/verify-finnaplan-v5.py')
    assert rehearsal['recovery_helper_sha256'] == sha(ROOT/'scripts/recover-finnaplan-v5.py')
    assert all(value == 0 for value in rehearsal['reward_integrity'].values())
    for name, digest in rehearsal['candidate_sha256'].items():
        assert sha(ROOT/'api'/name) == digest, 'Source changed after rehearsal: '+name
    audit = json.loads((REPORT/'live-audit.json').read_text())
    names = [name for name in RELEASE_FILES if name.startswith('app/')]+['app/data/learning-economy-v2.json']
    api = {name: sha(ROOT/'api'/name) for name in names if audit['api'].get(name) != sha(ROOT/'api'/name)}
    # Every changed live Python module must belong to this explicit V.5 scope.
    unchanged = {name: digest for name, digest in audit['api'].items() if name not in api}
    for name, digest in unchanged.items():
        assert sha(ROOT/'api'/name) == digest, 'Unrelated local dependency differs: '+name
    migrations = {'0097_owned_calendar.sql': sha(ROOT/'api/migrations/0097_owned_calendar.sql')}
    assert migrations['0097_owned_calendar.sql'] == rehearsal['migration_sha256']
    manifest = {'api': api, 'migrations': migrations,
                'web': {str(p.relative_to(ROOT/'web/dist')): sha(p) for p in (ROOT/'web/dist').rglob('*') if p.is_file()}}
    helpers = ('scripts/deploy-finnaplan-v5.py', 'scripts/recover-finnaplan-v5.py',
               'scripts/verify-finnaplan-v5.py', 'scripts/rehearse-v5-recovery.py',
               'scripts/prepare-v5-economy-evidence.py', 'scripts/prepare-finnaplan-v5.py')
    inputs = ('backend-tests.txt', 'web-build.txt', 'migration-rehearsal.json', 'fixture-run.json',
              'recovery-and-calibration-tests.txt', 'calibration.json', 'economy-recovery.json', 'v5-recovery.json',
              'web-source-hashes.json')
    web_sources = json.loads((REPORT/'web-source-hashes.json').read_text())
    for name, digest in web_sources.items():
        assert sha(ROOT/name) == digest, 'Web source changed after build: '+name
    scope = {'candidate': manifest, 'api_preimages': {name: audit['api'].get(name) for name in api},
             'unchanged_api': unchanged, 'web_preimages': audit['web'],
             'unchanged_migrations': {name: sha(ROOT/'api'/name) for name in RELEASE_FILES
                                      if name.startswith('migrations/') and Path(name).name not in migrations},
             'web_sources': web_sources,
             'operator_files': {name: sha(ROOT/name) for name in helpers},
             'proof_files': {name: sha(REPORT/name) for name in inputs},
             'v5_database_guards': rehearsal['v5_database_guards'],
             'scope': 'V.5 boards/recap/calendar/profile/shop/account tools; explicit API overlay, 0097 and built web',
             'recovery': 'Prior static plus quarantined current V.5 API; keep catalog, moderation readers, tombstones and SQL guards',
             'excluded': 'canonical bank/workshop, provider calls/configuration, paid-plan writes, dependencies, units and shared Caddy'}
    (REPORT/'release-scope.json').write_text(json.dumps(scope, indent=2)+'\n')
    print('Frozen V.5:', len(api), 'API artifacts;', len(manifest['web']), 'static artifacts; migration0097')


if __name__ == '__main__':
    main()
