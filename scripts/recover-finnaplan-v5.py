#!/usr/bin/env python3
"""Quarantine V.5 writes and restore paired prior static assets.

Retain the released API and additive schema: old API readers/validators cannot
protect moderated bios, purchased cosmetics or closed-account tombstones. This
is a compatibility recovery, not a downgrade to V.4. No SQL policy is rewritten.
Run the frozen copy in the private release backup, as root, with that directory.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import time

STATE = 'app/data/finnaplan-v5-writes.json'
ACTIVE = b'{"version":1,"writes_enabled":true}\n'
RECOVERY = b'{"version":1,"writes_enabled":false}\n'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def inventory(root):
    assert root.is_dir(), 'Missing artifact directory'
    assert not any(p.is_symlink() for p in root.rglob('*')), 'Symlink in static artifacts'
    return {p.relative_to(root).as_posix(): digest(p) for p in root.rglob('*') if p.is_file()}


def checked_names(manifest):
    for name, value in manifest.items():
        path = PurePosixPath(name)
        assert not path.is_absolute() and '..' not in path.parts and str(path) == name
        assert len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def validate_files(backup, api, public, scope):
    candidate = scope['candidate']
    for manifest in (candidate['api'], candidate['web'], scope['web_preimages']):
        checked_names(manifest)
    assert candidate['api'].get(STATE) == hashlib.sha256(ACTIVE).hexdigest()
    for name, expected in candidate['api'].items():
        allowed = {expected}
        if name == STATE:
            allowed.add(hashlib.sha256(RECOVERY).hexdigest())
        assert digest(api/name) in allowed, 'Newer or missing API artifact: '+name
    # An added static chunk is also a newer release, even if index.html matches.
    assert inventory(public) in (candidate['web'], scope['web_preimages']), 'Newer static release'
    assert inventory(backup/'public') == scope['web_preimages'], 'Changed static backup'


def recover_files(backup, api, public, scope):
    validate_files(backup, api, public, scope)
    state = api/STATE
    temporary = state.with_suffix('.recovery-tmp')
    temporary.write_bytes(RECOVERY)
    os.chmod(temporary, 0o644)
    os.replace(temporary, state)
    subprocess.run(['rsync', '-a', '--delete', str(backup/'public')+'/', str(public)+'/'], check=True)
    assert inventory(public) == scope['web_preimages']
    for name, expected in scope['candidate']['api'].items():
        assert digest(api/name) == (hashlib.sha256(RECOVERY).hexdigest() if name == STATE else expected)


def database_guards(conn):
    """Capture as postgres in a read-only transaction, also used by rehearsal."""
    functions = conn.execute("""SELECT p.proname,pg_get_functiondef(p.oid)
      FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
      WHERE n.nspname='public' AND p.proname IN
        ('account_has_pro','active_account_record','closed_identity_stays_anonymous')
      ORDER BY p.proname""").fetchall()
    triggers = conn.execute("""SELECT c.relname,t.tgname,pg_get_triggerdef(t.oid),t.tgenabled
      FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
      WHERE NOT t.tgisinternal AND t.tgname IN
        ('active_account_record','closed_identity_stays_anonymous') ORDER BY c.relname,t.tgname""").fetchall()
    constraint = conn.execute("""SELECT pg_get_constraintdef(oid) FROM pg_constraint
      WHERE conrelid='users'::regclass AND conname='closed_account_anonymous'""").fetchall()
    assert len(functions) == 3 and len(triggers) == 17 and len(constraint) == 1
    assert all(r[3] == 'O' for r in triggers), 'Account guard disabled'
    payload = {'functions': functions, 'triggers': triggers, 'constraint': constraint}
    return json.loads(json.dumps(payload))


def verify_database(expected):
    result = subprocess.run(['sudo', '-u', 'postgres', '/srv/api/.venv/bin/python', '-', '--guards'],
                            input=Path(__file__).read_bytes(), capture_output=True, check=True)
    assert json.loads(result.stdout) == expected, 'Changed account guards'


def main(backup):
    assert os.geteuid() == 0 and backup.parent == Path('/root') and backup.name.startswith('finna-v5-backup-')
    scope = json.loads((backup/'scope.json').read_text())
    api, public = Path('/srv/api'), Path('/srv/study/public')
    validate_files(backup, api, public, scope)
    verify_database(scope['v5_database_guards'])
    units = ('ism-oracle-bank-review.timer', 'ism-paper-publisher.service', 'ism-paper-documents.service')
    active = [u for u in units if subprocess.run(['systemctl', 'is-active', '--quiet', u]).returncode == 0]
    stopped = False
    try:
        for unit in active:
            subprocess.run(['systemctl', 'stop', unit], check=True)
        for _ in range(60):
            if subprocess.run(['systemctl', 'is-active', '--quiet', 'ism-oracle-bank-review.service']).returncode != 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError('Publisher did not drain; artifacts unchanged')
        subprocess.run(['systemctl', 'stop', 'ism-api'], check=True)
        stopped = True
        # Recheck after drain to reject a concurrent operator release.
        validate_files(backup, api, public, scope)
        verify_database(scope['v5_database_guards'])
        recover_files(backup, api, public, scope)
        subprocess.run(['chown', '-R', 'caddy:caddy', str(public)], check=True)
        subprocess.run(['systemctl', 'start', 'ism-api'], check=True)
        stopped = False
        from urllib.request import urlopen
        for url in ('https://study.hawayu.in/api/health', 'https://study.hawayu.in', 'https://family.hawayu.in'):
            with urlopen(url, timeout=30) as response:
                assert response.status == 200
        verify_database(scope['v5_database_guards'])
    finally:
        # After a partial copy failure keep the current API available with new
        # writes dark. The full private snapshot remains available for repair.
        if stopped:
            subprocess.run(['systemctl', 'start', 'ism-api'], check=True)
        for unit in reversed(active):
            subprocess.run(['systemctl', 'start', unit], check=True)
    print('Prior static restored; V.5 new writes paused. Current privacy readers, catalog, SQL guards and all history retained. Rehearse a bounded forward repair before resuming writes.')


if __name__ == '__main__':
    assert len(sys.argv) == 2
    if sys.argv[1] == '--guards':
        import psycopg
        with psycopg.connect('dbname=mpsc') as connection:
            connection.execute('SET TRANSACTION READ ONLY')
            print(json.dumps(database_guards(connection)))
    else:
        main(Path(sys.argv[1]).resolve())
