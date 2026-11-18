#!/usr/bin/env python3
"""Frozen, bounded V.2 release. Invoke through scripts/deploy.sh finnaplan-v2.

Only audited API files and locally built static artifacts ship. Additive schema
is retained on rollback; API/static snapshots are restored together. No bank,
workshop, shared Caddy, dependencies or unit-file changes are performed.
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
from urllib.request import Request,urlopen

REPORT='reports/finnaplan-v2-today-20261117'
MIGRATIONS=('0083_daily_five.sql','0092_learning_loop.sql')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def run(args,**kwargs):
    try:return subprocess.run(args,check=True,capture_output=True,**kwargs)
    except subprocess.CalledProcessError as error:
        for output in (error.stdout,error.stderr):
            if output:print(output.decode(errors='replace') if isinstance(output,bytes) else output,file=sys.stderr)
        raise


def sql(query):
    return run(['sudo','-u','postgres','psql','-XqAt','-v','ON_ERROR_STOP=1','-d','mpsc'],input=query.encode()).stdout.decode().strip()


def response(path,headers=None):
    try:r=urlopen(Request('https://study.hawayu.in'+path,headers=headers or {}),timeout=30)
    except HTTPError as error:r=error
    with r:return r.code,r.headers,r.read()


def remote(stage):
    assert os.geteuid()==0
    root,public=Path('/srv/api'),Path('/srv/study/public')
    frozen=json.loads((stage/'scope.json').read_text())
    manifest=json.loads((stage/'manifest.json').read_text())
    assert manifest==frozen['candidate'],'Candidate differs from reviewed release scope'
    assert set(manifest['migrations'])==set(MIGRATIONS)
    def preflight():
        for name,before in frozen['api_preimages'].items():
            assert sha(root/name) in (before,manifest['api'][name]),'API changed: '+name
        for name,before in frozen['unchanged_api'].items():
            assert sha(root/name)==before,'Dependency changed: '+name
        # Compare every live static preimage, including unrelated screens.
        if sha(public/'index.html')!=manifest['web']['index.html']:
            for name,before in frozen['web_preimages'].items():
                assert sha(public/name)==before,'Static changed: '+name
    preflight()
    for name,expected in manifest['api'].items():
        assert sha(stage/'api'/name)==expected
        compile((stage/'api'/name).read_bytes(),name,'exec')
    for name,expected in manifest['web'].items():assert sha(stage/'web'/name)==expected
    for name,expected in manifest['migrations'].items():
        assert sha(stage/'migrations'/name)==expected
        prior=sql("SELECT checksum FROM schema_migrations WHERE version='"+Path(name).stem+"'")
        assert not prior or prior[:16]==expected[:16],'Applied migration drift: '+name
    assert shutil.disk_usage('/root').free>8*1024**3,'Insufficient paired-backup headroom'
    backup=Path(tempfile.mkdtemp(prefix='finna-v2-backup-',dir='/root'))
    shutil.copy2(stage/'scope.json',backup/'scope.json')
    for name in manifest['api']:
        if (root/name).is_file():
            target=backup/'api'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/name,target)
    shutil.copytree(public,backup/'public')
    with (backup/'database.dump').open('wb') as dump:
        subprocess.run(['sudo','-u','postgres','pg_dump','-Fc','mpsc'],stdout=dump,check=True)
    (backup/'database.dump').chmod(0o600)
    ledger_before=int(sql('SELECT count(*) FROM reward_ledger'))
    print('Paired rollback snapshot: '+str(backup),flush=True)
    preflight()
    for name in MIGRATIONS:
        version=Path(name).stem
        if not sql("SELECT version FROM schema_migrations WHERE version='"+version+"'"):
            source=(stage/'migrations'/name).read_text().rstrip();assert source.endswith('COMMIT;')
            ledger="INSERT INTO schema_migrations(version,checksum) VALUES ('"+version+"','"+manifest['migrations'][name][:16]+"');\nCOMMIT;"
            sql("SET lock_timeout='5s'; SET statement_timeout='30s';\n"+source[:-len('COMMIT;')]+ledger)
            print('Applied '+name,flush=True)
        shutil.copy2(stage/'migrations'/name,root/'migrations'/name)
    def restore():
        for name in manifest['api']:
            if (backup/'api'/name).is_file():shutil.copy2(backup/'api'/name,root/name)
            elif sha(root/name)==manifest['api'][name]:(root/name).unlink()
        run(['rsync','-a','--delete',str(backup/'public')+'/',str(public)+'/'])
        run(['chown','-R','caddy:caddy',str(public)])
        run(['systemctl','restart','ism-api'])
    try:
        run(['systemctl','stop','ism-api'])
        for name in manifest['api']:
            (root/name).parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(stage/'api'/name,root/name)
        run(['rsync','-a','--delete',str(stage/'web')+'/',str(public)+'/'])
        run(['chown','-R','caddy:caddy',str(public)])
        run(['systemctl','start','ism-api'])
        for _ in range(30):
            try:
                if response('/api/health')[0]==200:break
            except OSError:pass
            time.sleep(1)
        else:raise RuntimeError('API did not become healthy')
        for name,expected in manifest['api'].items():assert sha(root/name)==expected,'API readback: '+name
        for name,expected in manifest['web'].items():assert sha(public/name)==expected,'Static readback: '+name
        for _ in range(60):
            pending=int(sql('SELECT count(*) FROM learning_rollup_jobs WHERE processed_version<requested_version'))
            if not pending:break
            time.sleep(1)
        assert not pending,'Learning worker did not drain initial jobs'
        assert sql("SELECT last_ok IS NOT NULL FROM worker_heartbeats WHERE worker='mastery-reconciler'")=='t'
        check=run(['sudo','-u','postgres','/srv/api/.venv/bin/python','-'],input=(stage/'verify.py').read_bytes(),cwd=root)
        readback=json.loads(check.stdout)
        assert readback['account_users_checked']>0
        status,headers,_=response('/api/questions/taxonomy')
        assert status==200 and headers.get('Cache-Control')=='public, max-age=0, must-revalidate'
        assert response('/api/questions/taxonomy',{'If-None-Match':headers['ETag']})[0]==304
        status,headers,_=response('/api/questions/taxonomy',{'Cookie':'cache_probe=1'})
        assert status==200 and headers.get('Cache-Control')=='private, no-store' and not headers.get('ETag')
        assert response('/revise')[0]==200
        with urlopen('https://family.hawayu.in',timeout=30) as family:assert family.status==200
        ledger_after=int(sql('SELECT count(*) FROM reward_ledger'))
        receipt={**manifest,'backup':str(backup),'api_files':len(manifest['api']),'web_files':len(manifest['web']),
          'read_only_flow':readback,'learning_jobs_pending':pending,'worker_last_ok':True,'reward_rows_before':ledger_before,
          'reward_rows_after':ledger_after,'public_304':True,'credential_private':True,'study_healthy':True,'family_healthy':True}
        (backup/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print('RECEIPT '+json.dumps(receipt),flush=True)
    except BaseException:
        restore()
        print('Restored paired API/web snapshot; additive migrations and durable jobs retained.',flush=True)
        raise


def local():
    root=Path(__file__).resolve().parents[1]
    frozen=json.loads((root/REPORT/'release-scope.json').read_text())
    manifest=frozen['candidate']
    rehearsal=json.loads((root/REPORT/'migration-rehearsal.json').read_text())
    assert rehearsal['seed_preserves_all_existing_rows'] and rehearsal['cloned_acls_preserved']
    assert rehearsal['read_only_flow']['transactions_read_only']
    assert rehearsal['sha256']==manifest['migrations']['0092_learning_loop.sql']
    assert rehearsal['prerequisites'][0]['sha256']==manifest['migrations']['0083_daily_five.sql']
    assert '978 passed' in (root/REPORT/'backend-tests.txt').read_text()
    assert 'built in' in (root/REPORT/'web-build.txt').read_text()
    host=os.environ.get('ISM_HOST','ubuntu@152.67.31.231')
    with tempfile.TemporaryDirectory(prefix='finna-v2-package-') as directory:
        package=Path(directory)
        for name,expected in manifest['api'].items():
            assert sha(root/'api'/name)==expected,'Local candidate changed: '+name
            target=package/'api'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/'api'/name,target)
        (package/'migrations').mkdir()
        for name,expected in manifest['migrations'].items():
            assert sha(root/'api/migrations'/name)==expected
            shutil.copy2(root/'api/migrations'/name,package/'migrations'/name)
        shutil.copytree(root/'web/dist',package/'web')
        for name,expected in manifest['web'].items():assert sha(package/'web'/name)==expected
        shutil.copy2(__file__,package/'deploy.py')
        shutil.copy2(root/'scripts/verify-learning-loop.py',package/'verify.py')
        (package/'scope.json').write_text(json.dumps(frozen))
        (package/'manifest.json').write_text(json.dumps(manifest))
        stage=run(['ssh',host,'mktemp -d /tmp/finna-v2-stage.XXXXXX'],text=True).stdout.strip()
        assert stage.startswith('/tmp/finna-v2-stage.') and '\n' not in stage
        try:
            run(['rsync','-az','-e','ssh',str(package)+'/',host+':'+stage+'/'])
            result=run(['ssh',host,'sudo python3 '+shlex.quote(stage+'/deploy.py')+' --remote '+shlex.quote(stage)],text=True)
            (root/REPORT/'release.txt').write_text(result.stdout)
            receipt=next(line.removeprefix('RECEIPT ') for line in result.stdout.splitlines() if line.startswith('RECEIPT '))
            (root/REPORT/'release.json').write_text(json.dumps(json.loads(receipt),indent=2)+'\n')
            print('V.2 release verified; receipt: '+str(root/REPORT/'release.json'))
        finally:run(['ssh',host,'rm -rf -- '+shlex.quote(stage)])


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--remote':remote(Path(sys.argv[2]))
    else:
        assert len(sys.argv)==1
        local()
