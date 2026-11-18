#!/usr/bin/env python3
"""Bounded, preimage-checked Finnaplan V.1 API/schema/web release.

Use scripts/deploy.sh finnaplan-v1 after local build/tests and dump rehearsal.
Only the named API files and built web artifacts ship; workshop files stay put.
Rollback retains the additive schema and restores the paired API/web snapshot.
"""
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

PREIMAGES = {
    'app/main.py': '40623edf8683cd55618ee0781976c153a3548fa36f409fba43c011dfe0ab375f',
    'app/deps.py': '0c5afe51c391cd98c95447266be655b1d78e8e49cea6284098085db2e5ea31a8',
    'app/schemas.py': '17716f85c5d51e2d5be00acdcda7bba47cbd137c41f3bed8daa93cac671af092',
    'app/routers/questions.py': '71882c036acd25055815448420ea5e2222e1ff36cb224aae26f76385eb6b8ac3',
    'app/routers/me.py': '848664bf4002842a60e89e4fab05d774b624438a81cff7ef839d925341efcb62',
    'app/routers/rewards.py': '7def0519b433021e87b2fdce6113ba51a6e6f7aabf8007517f30ca2eacb4f920',
    'app/routers/mobile.py': '1c6ffc0d9baabe8956be4edff9e4a85f3c4ddf627699cc86e3dfd178b80a3c6a',
    'app/services/mobile_identity.py': '4e741445c91fcb6bedd53452f7507a4992890b5419fa053e6c1d88fde5f748eb',
    'app/services/public_browse_cache.py': None,
    'app/services/browse_allowance.py': None,
}
WEB_PREIMAGE = '98ec4265458fbe929a205a91762070ff23d7cfdaa45091142992cc7b8da609fa'
MIGRATIONS = ('0090_public_browse_indexes.sql', '0091_daily_feature_limits.sql')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def run(args, **kwargs):
    try:
        return subprocess.run(args, check=True, capture_output=True, **kwargs)
    except subprocess.CalledProcessError as error:
        for output in (error.stdout, error.stderr):
            if output:
                print(output.decode(errors='replace') if isinstance(output, bytes) else output, file=sys.stderr)
        raise


def sql(query):
    return run(['sudo', '-u', 'postgres', 'psql', '-XqAt', '-v', 'ON_ERROR_STOP=1',
                '-d', 'mpsc'], input=query.encode()).stdout.decode().strip()


def response(path, headers=None):
    try:
        result = urlopen(Request('https://study.hawayu.in' + path, headers=headers or {}), timeout=20)
    except HTTPError as error:
        result = error
    with result:
        return result.code, result.headers, result.read()


def remote(stage):
    assert os.geteuid() == 0
    root, public = Path('/srv/api'), Path('/srv/study/public')
    manifest = json.loads((stage/'manifest.json').read_text())
    assert set(manifest['api']) == set(PREIMAGES)
    assert set(manifest['migrations']) == set(MIGRATIONS)

    def preflight():
        for name, before in PREIMAGES.items():
            assert sha(root/name) in (before, manifest['api'][name]), 'API changed: ' + name
        assert sha(public/'index.html') in (WEB_PREIMAGE, manifest['web']['index.html']), 'Web changed'
    preflight()
    for name, expected in manifest['api'].items():
        assert sha(stage/'api'/name) == expected
        compile((stage/'api'/name).read_bytes(), name, 'exec')
    for name, expected in manifest['web'].items():
        assert sha(stage/'web'/name) == expected
    for name, expected in manifest['migrations'].items():
        assert sha(stage/'migrations'/name) == expected
        version = Path(name).stem
        prior = sql("SELECT checksum FROM schema_migrations WHERE version='" + version + "'")
        assert not prior or prior[:16] == expected[:16], 'Applied migration drift: ' + name

    backup = Path(tempfile.mkdtemp(prefix='finna-v1-backup-', dir='/root'))
    for name in PREIMAGES:
        if (root/name).is_file():
            target = backup/'api'/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root/name, target)
    shutil.copytree(public, backup/'public')
    with (backup/'database.dump').open('wb') as dump:
        subprocess.run(['sudo', '-u', 'postgres', 'pg_dump', '-Fc', 'mpsc'], stdout=dump, check=True)
    (backup/'database.dump').chmod(0o600)
    print('Paired rollback snapshot: ' + str(backup), flush=True)
    preflight()  # Backup time must not hide a concurrent release.

    for name in MIGRATIONS:
        version = Path(name).stem
        if sql("SELECT version FROM schema_migrations WHERE version='" + version + "'"):
            continue
        source = (stage/'migrations'/name).read_text().rstrip()
        assert source.endswith('COMMIT;')
        ledger = "INSERT INTO schema_migrations(version,checksum) VALUES ('" + version + "','" + manifest['migrations'][name][:16] + "');\nCOMMIT;"
        sql("SET lock_timeout='5s'; SET statement_timeout='30s';\n" + source[:-len('COMMIT;')] + ledger)
        shutil.copy2(stage/'migrations'/name, root/'migrations'/name)
        print('Applied ' + name, flush=True)

    def restore():
        for name in PREIMAGES:
            if (backup/'api'/name).is_file():
                shutil.copy2(backup/'api'/name, root/name)
            elif sha(root/name) == manifest['api'][name]:
                (root/name).unlink()
        run(['rsync', '-a', '--delete', str(backup/'public')+'/', str(public)+'/'])
        run(['chown', '-R', 'caddy:caddy', str(public)])
        run(['systemctl', 'restart', 'ism-api'])

    try:
        for name in PREIMAGES:
            shutil.copy2(stage/'api'/name, root/name)
        run(['rsync', '-a', '--delete', str(stage/'web')+'/', str(public)+'/'])
        run(['chown', '-R', 'caddy:caddy', str(public)])
        run(['systemctl', 'restart', 'ism-api'])
        for _ in range(15):
            try:
                if response('/api/health')[0] == 200:
                    break
            except OSError:
                pass
            time.sleep(1)
        else:
            raise RuntimeError('API did not become healthy')
        for name, expected in manifest['api'].items():
            assert sha(root/name) == expected, 'API readback mismatch: ' + name
        for name, expected in manifest['web'].items():
            assert sha(public/name) == expected, 'Web readback mismatch: ' + name
        status, headers, _ = response('/api/questions/taxonomy')
        assert status == 200 and headers.get('Cache-Control') == 'public, max-age=0, must-revalidate'
        assert response('/api/questions/taxonomy', {'If-None-Match': headers['ETag']})[0] == 304
        private = response('/api/questions/taxonomy', {'Cookie': 'cache_probe=1'})
        assert private[0] == 200 and private[1].get('Cache-Control') == 'private, no-store' and not private[1].get('ETag')
        with urlopen('https://family.hawayu.in', timeout=20) as family:
            assert family.status == 200
        receipt = {**manifest, 'backup': str(backup), 'api_files': len(manifest['api']),
                   'web_files': len(manifest['web']), 'public_304': True, 'credential_private': True,
                   'study_healthy': True, 'family_healthy': True}
        (backup/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
        print('RECEIPT ' + json.dumps(receipt), flush=True)
    except BaseException:
        restore()
        print('Restored paired API/web snapshot; additive migrations retained.', flush=True)
        raise


def local():
    root = Path(__file__).resolve().parents[1]
    assert (root/'web/dist/index.html').is_file(), 'Build web locally before release'
    host = os.environ.get('ISM_HOST', 'ubuntu@152.67.31.231')
    with tempfile.TemporaryDirectory(prefix='finna-v1-package-') as scratch:
        package = Path(scratch)
        for name in PREIMAGES:
            target = package/'api'/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root/'api'/name, target)
        (package/'migrations').mkdir()
        for name in MIGRATIONS:
            shutil.copy2(root/'api/migrations'/name, package/'migrations'/name)
        shutil.copytree(root/'web/dist', package/'web')
        manifest = {'api': {name: sha(package/'api'/name) for name in PREIMAGES},
                    'migrations': {name: sha(package/'migrations'/name) for name in MIGRATIONS},
                    'web': {str(p.relative_to(package/'web')): sha(p) for p in (package/'web').rglob('*') if p.is_file()}}
        (package/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
        shutil.copy2(__file__, package/'deploy.py')
        stage = run(['ssh', host, 'mktemp -d /tmp/finna-v1-stage.XXXXXX'], text=True).stdout.strip()
        assert stage.startswith('/tmp/finna-v1-stage.') and '\n' not in stage
        run(['rsync', '-az', '-e', 'ssh', str(package)+'/', host+':'+stage+'/'])
        result = run(['ssh', host, 'sudo python3 ' + shlex.quote(stage+'/deploy.py') + ' --remote ' + shlex.quote(stage)], text=True)
        print(result.stdout)
        report = root/'reports/finnaplan-v1-20261117'
        report.mkdir(parents=True, exist_ok=True)
        (report/'release.txt').write_text(result.stdout)
        receipt = next(line.removeprefix('RECEIPT ') for line in result.stdout.splitlines() if line.startswith('RECEIPT '))
        (report/'release.json').write_text(json.dumps(json.loads(receipt), indent=2)+'\n')


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--remote':
        remote(Path(sys.argv[2]))
    else:
        assert len(sys.argv) == 1
        local()
