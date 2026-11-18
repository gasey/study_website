#!/usr/bin/env python3
"""Bounded V.6 release. Invoke through scripts/deploy.sh finnaplan-v6.

Only audited API files and locally built static artifacts ship. Additive schema
is retained in recovery; the exact prior V.5 API/static pair is restored. No bank,
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

REPORT='reports/finnaplan-v6-20261117'
MIGRATIONS=('0098_mobile_review_grants.sql',)


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


def remote(stage,check_only=False):
    assert os.geteuid()==0
    root,public=Path('/srv/api'),Path('/srv/study/public')
    frozen=json.loads((stage/'scope.json').read_text())
    manifest=json.loads((stage/'manifest.json').read_text())
    assert manifest==frozen['candidate'],'Candidate differs from reviewed release scope'
    assert set(manifest['migrations'])==set(MIGRATIONS)
    recovery_files={'__name__':'v5_deploy_recovery','__file__':str(stage/'recover.py')}
    exec(compile((stage/'recover.py').read_text(),'recover.py','exec'),recovery_files)
    for staged,name in (('deploy.py','scripts/deploy-finnaplan-v6.py'),
                        ('recover.py','scripts/recover-finnaplan-v5.py'),('rollback.py','scripts/rollback-finnaplan-v6.py'),('verify.py','scripts/verify-finnaplan-v6.py')):
        assert sha(stage/staged)==frozen['operator_files'][name],'Staged operator changed: '+name
    def preflight():
        allowed=set(frozen['unchanged_api'])|{n for n in manifest['api'] if n.endswith('.py')}
        assert {str(p.relative_to(root)) for p in (root/'app').rglob('*.py')}<=allowed,'Unexpected new API dependency'
        for name,before in frozen['api_preimages'].items():
            assert sha(root/name) in (before,manifest['api'][name]),'API changed: '+name
        for name,before in frozen['unchanged_api'].items():
            assert sha(root/name)==before,'Dependency changed: '+name
        for name,before in frozen['unchanged_migrations'].items():
            assert sha(root/name)==before,'Applied migration source changed: '+name
        # Compare every live static preimage, including unrelated screens.
        actual={str(p.relative_to(public)):sha(p) for p in public.rglob('*') if p.is_file()}
        assert actual in (frozen['web_preimages'],manifest['web']),'Static artifacts changed since audit'
    preflight()
    for name,expected in manifest['api'].items():
        assert sha(stage/'api'/name)==expected
        if name.endswith('.py'):compile((stage/'api'/name).read_bytes(),name,'exec')
    for name,expected in manifest['web'].items():assert sha(stage/'web'/name)==expected
    assert recovery_files['inventory'](stage/'web')==manifest['web']
    for name,expected in manifest['migrations'].items():
        assert sha(stage/'migrations'/name)==expected
        assert not sql("SELECT checksum FROM schema_migrations WHERE version='"+Path(name).stem+"'"),'Release already or partially applied; use saved recovery receipt for forward repair'
    assert shutil.disk_usage('/root').free>8*1024**3,'Insufficient paired-backup headroom'
    if check_only:
        print('V.6 bounded remote preflight passed; no services, SQL or live artifacts changed.')
        return
    backup=Path(tempfile.mkdtemp(prefix='finna-v6-backup-',dir='/root'))
    shutil.copy2(stage/'scope.json',backup/'scope.json')
    shutil.copy2(stage/'recover.py',backup/'guard-inspector.py')
    shutil.copy2(stage/'rollback.py',backup/'rollback.py')
    shutil.copy2(stage/'verify.py',backup/'verify.py')
    shutil.copytree(stage/'api',backup/'released-api')
    for name in manifest['api']:
        if (root/name).is_file():
            target=backup/'api'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/name,target)
    shutil.copytree(public,backup/'public')
    units=('ism-oracle-bank-review.timer','ism-paper-publisher.service','ism-paper-documents.service')
    active=[unit for unit in units if subprocess.run(['systemctl','is-active','--quiet',unit]).returncode==0]
    (backup/'workers.json').write_text(json.dumps(active))
    ledger_before=int(sql('SELECT count(*) FROM reward_ledger'))
    print('Private paired recovery snapshot: '+str(backup),flush=True)
    def install_api():
        for name in manifest['api']:
            target=root/name
            assert not target.is_symlink(),'Live API target is a symlink: '+name
            target.parent.mkdir(parents=True,exist_ok=True)
            temporary=target.with_suffix(target.suffix+'.v6-tmp')
            shutil.copy2(stage/'api'/name,temporary);temporary.chmod(0o644);os.replace(temporary,target)
    def restore():
        run(['systemctl','stop','ism-api'])
        for name in manifest['api']:
            old=backup/'api'/name;target=root/name
            if old.is_file():shutil.copy2(old,target)
            elif target.is_file():target.unlink()
        # Reject any unrelated concurrent static change before restoring a copy
        # that this installer may have only partially installed.
        actual=recovery_files['inventory'](public)
        for name,digest in actual.items():
            assert digest in {frozen['web_preimages'].get(name),manifest['web'].get(name)},'Unrelated static changed during recovery: '+name
        run(['rsync','-a','--delete',str(backup/'public')+'/',str(public)+'/'])
        run(['chown','-R','caddy:caddy',str(public)])
        run(['systemctl','restart','ism-api'])
        recovery_files['verify_database'](frozen['v5_database_guards'])
        for path in ('/api/health','/'):
            for _ in range(30):
                try:
                    if response(path)[0]==200:break
                except OSError:pass
                time.sleep(1)
            else:raise RuntimeError('Recovery health failed: '+path)
        with urlopen('https://family.hawayu.in',timeout=30) as family:assert family.status==200
    try:
        # Drain external publishers, then stop the API before behavioral DDL.
        # Restore exactly the previously active services even on an abort.
        for unit in active:run(['systemctl','stop',unit])
        for _ in range(60):
            if subprocess.run(['systemctl','is-active','--quiet','ism-oracle-bank-review.service']).returncode!=0:break
            time.sleep(1)
        else:raise RuntimeError('Existing correction publisher has not drained')
        preflight()
        run(['systemctl','stop','ism-api'])
        with (backup/'database.dump').open('wb') as dump:
            subprocess.run(['sudo','-u','postgres','pg_dump','-Fc','mpsc'],stdout=dump,check=True)
        (backup/'database.dump').chmod(0o600)
        for name in MIGRATIONS:
            version=Path(name).stem
            source=(stage/'migrations'/name).read_text().rstrip();assert source.endswith('COMMIT;')
            ledger="INSERT INTO schema_migrations(version,checksum) VALUES ('"+version+"','"+manifest['migrations'][name][:16]+"');\nCOMMIT;"
            sql("SET lock_timeout='5s'; SET statement_timeout='30s';\n"+source[:-len('COMMIT;')]+ledger)
            shutil.copy2(stage/'migrations'/name,root/'migrations'/name)
            print('Applied '+name,flush=True)
        recovery_files['verify_database'](frozen['v5_database_guards'])
        install_api()
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
        assert recovery_files['inventory'](public)==manifest['web']
        for name,expected in frozen['unchanged_api'].items():assert sha(root/name)==expected,'Dependency readback: '+name
        for name,expected in manifest['migrations'].items():assert sha(root/'migrations'/name)==expected,'Migration readback: '+name
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
          'read_only_flow':readback,'publishers_drained':True,'recovery_strategy':'Restore paired V.5 API/static; retain additive0098 grant and all V.5 SQL guards','recovery_executed':False,'learning_jobs_pending':pending,'worker_last_ok':True,'reward_rows_before':ledger_before,
          'reward_rows_after':ledger_after,'public_304':True,'credential_private':True,'study_healthy':True,'family_healthy':True}
        (backup/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print('RECEIPT '+json.dumps(receipt),flush=True)
    except BaseException:
        restore()
        print('Recovery completed using migration-aware compatibility floor; history and SQL protections retained.',flush=True)
        raise
    finally:
        for unit in reversed(active):run(['systemctl','start',unit])


def local(check_only=False):
    root=Path(__file__).resolve().parents[1]
    frozen=json.loads((root/REPORT/'release-scope.json').read_text())
    manifest=frozen['candidate']
    rehearsal=json.loads((root/REPORT/'migration-rehearsal.json').read_text())
    assert rehearsal['all_existing_columns_and_rows_preserved'] and rehearsal['clone_and_dump_removed']
    assert rehearsal['read_only_flow']['transactions_read_only']
    assert rehearsal['migration_sha256']==manifest['migrations'][MIGRATIONS[-1]]
    assert rehearsal['release_read_only_flow']['economy_reconciled']
    assert rehearsal['source_bound_economy_ready']
    assert '1085 passed' in (root/REPORT/'backend-tests.txt').read_text()
    assert 'built in' in (root/REPORT/'web-build.txt').read_text()
    for name,expected in frozen['operator_files'].items():assert sha(root/name)==expected,'Release helper changed: '+name
    for name,expected in frozen['proof_files'].items():assert sha(root/REPORT/name)==expected,'Release proof changed: '+name
    for name,expected in frozen['web_sources'].items():assert sha(root/name)==expected,'Web source changed: '+name
    for name,expected in rehearsal['candidate_sha256'].items():assert sha(root/'api'/name)==expected,'Rehearsed dependency changed: '+name
    host=os.environ.get('ISM_HOST','ubuntu@152.67.31.231')
    with tempfile.TemporaryDirectory(prefix='finna-v6-package-') as directory:
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
        assert {str(p.relative_to(package/'web')):sha(p) for p in (package/'web').rglob('*') if p.is_file()}==manifest['web']
        shutil.copy2(__file__,package/'deploy.py')
        shutil.copy2(root/'scripts/verify-finnaplan-v6.py',package/'verify.py')
        shutil.copy2(root/'scripts/recover-finnaplan-v5.py',package/'recover.py')
        shutil.copy2(root/'scripts/rollback-finnaplan-v6.py',package/'rollback.py')
        (package/'scope.json').write_text(json.dumps(frozen))
        (package/'manifest.json').write_text(json.dumps(manifest))
        stage=run(['ssh',host,'mktemp -d /tmp/finna-v6-stage.XXXXXX'],text=True).stdout.strip()
        assert stage.startswith('/tmp/finna-v6-stage.') and '\n' not in stage
        try:
            run(['rsync','-az','-e','ssh',str(package)+'/',host+':'+stage+'/'])
            mode='--remote-check' if check_only else '--remote'
            result=run(['ssh',host,'sudo python3 '+shlex.quote(stage+'/deploy.py')+' '+mode+' '+shlex.quote(stage)],text=True)
            (root/REPORT/('preflight.txt' if check_only else 'release.txt')).write_text(result.stdout)
            if check_only:
                print(result.stdout.strip());return
            receipt=next(line.removeprefix('RECEIPT ') for line in result.stdout.splitlines() if line.startswith('RECEIPT '))
            (root/REPORT/'release.json').write_text(json.dumps(json.loads(receipt),indent=2)+'\n')
            print('V.6 release verified; receipt: '+str(root/REPORT/'release.json'))
        finally:run(['ssh',host,'rm -rf -- '+shlex.quote(stage)])


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1] in ('--remote','--remote-check'):remote(Path(sys.argv[2]),sys.argv[1]=='--remote-check')
    else:
        assert sys.argv[1:] in ([],['--check'])
        local(sys.argv[1:]==['--check'])
