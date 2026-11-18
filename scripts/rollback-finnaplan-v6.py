#!/usr/bin/env python3
"""Restore V.5 API/static after V.6, retaining its additive view grant without deleting learner history.

Run as root: python3 /root/finna-v6-backup-.../rollback.py BACKUP_DIRECTORY
Fails closed if newer API/static artifacts have replaced this release.
"""
import json,hashlib,os,shutil,subprocess,sys,time
from pathlib import Path


def restore_files(backup,root,public,manifest):
    for name in manifest['api']:
        target=root/name;old=backup/'api'/name
        if old.is_file():
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old,target)
        elif target.is_file():target.unlink()
    subprocess.run(['rsync','-a','--delete',str(backup/'public')+'/',str(public)+'/'],check=True)


def main(backup):
    assert os.geteuid()==0 and backup.parent==Path('/root') and backup.name.startswith('finna-v6-backup-')
    scope=json.loads((backup/'scope.json').read_text());manifest=scope['candidate']
    root,public=Path('/srv/api'),Path('/srv/study/public')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
    for name,digest in manifest['api'].items():
        assert sha(root/name) in (digest,scope['api_preimages'][name]),'Newer API change: '+name
        assert sha(backup/'api'/name)==scope['api_preimages'][name],'Changed API backup: '+name
    for name,digest in scope['unchanged_api'].items():
        assert sha(root/name)==digest,'Newer API dependency: '+name
    assert sha(backup/'guard-inspector.py')==scope['operator_files']['scripts/recover-finnaplan-v5.py'],'Changed guard inspector'
    assert {str(p.relative_to(backup/'public')):sha(p) for p in (backup/'public').rglob('*') if p.is_file()}==scope['web_preimages'],'Changed static backup'
    assert {str(p.relative_to(public)):sha(p) for p in public.rglob('*') if p.is_file()}==manifest['web'],'Newer static release'
    units=('ism-oracle-bank-review.timer','ism-paper-publisher.service','ism-paper-documents.service')
    active=[u for u in units if subprocess.run(['systemctl','is-active','--quiet',u]).returncode==0]
    stopped=False
    try:
        for unit in active:subprocess.run(['systemctl','stop',unit],check=True)
        for _ in range(60):
            if subprocess.run(['systemctl','is-active','--quiet','ism-oracle-bank-review.service']).returncode!=0:break
            time.sleep(1)
        else:raise RuntimeError('Correction publisher has not drained; no policy/files changed')
        subprocess.run(['systemctl','stop','ism-api'],check=True)
        stopped=True
        namespace={'__name__':'v6_guard_inspector','__file__':str(backup/'guard-inspector.py')}
        exec((backup/'guard-inspector.py').read_text(),namespace)
        namespace['verify_database'](scope['v5_database_guards'])
        restore_files(backup,root,public,manifest)
        for name,digest in scope['api_preimages'].items():assert sha(root/name)==digest,'API recovery readback: '+name
        assert {str(p.relative_to(public)):sha(p) for p in public.rglob('*') if p.is_file()}==scope['web_preimages'],'Static recovery readback'
        subprocess.run(['chown','-R','caddy:caddy',str(public)],check=True)
        subprocess.run(['systemctl','start','ism-api'],check=True)
        stopped=False
    finally:
        if stopped:subprocess.run(['systemctl','start','ism-api'],check=True)
        for unit in reversed(active):subprocess.run(['systemctl','start',unit],check=True)
    from urllib.request import urlopen
    for host in ('study.hawayu.in','family.hawayu.in'):
        with urlopen('https://'+host,timeout=30) as response:assert response.status==200
    print('V.5 API/static restored. V.6 capabilities removed; additive0098 grant, all V.5 SQL guards and learner history retained.')


if __name__=='__main__':
    assert len(sys.argv)==2
    main(Path(sys.argv[1]).resolve())
