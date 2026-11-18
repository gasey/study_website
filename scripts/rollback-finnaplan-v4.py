#!/usr/bin/env python3
"""Restore the exact paired V.4 snapshot without deleting learner history.

Run as root: python3 /root/finna-v4-backup-.../rollback.py BACKUP_DIRECTORY
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
    assert os.geteuid()==0 and backup.parent==Path('/root') and backup.name.startswith('finna-v4-backup-')
    scope=json.loads((backup/'scope.json').read_text());manifest=scope['candidate']
    root,public=Path('/srv/api'),Path('/srv/study/public')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
    for name,digest in manifest['api'].items():
        assert sha(root/name) in (digest,scope['api_preimages'][name]),'Newer API change: '+name
    for name,digest in manifest['web'].items():
        assert sha(public/name)==digest,'Newer web change; prepare a new bounded recovery: '+name
    units=('ism-oracle-bank-review.timer','ism-paper-publisher.service','ism-paper-documents.service')
    active=[u for u in units if subprocess.run(['systemctl','is-active','--quiet',u]).returncode==0]
    try:
        for unit in active:subprocess.run(['systemctl','stop',unit],check=True)
        for _ in range(60):
            if subprocess.run(['systemctl','is-active','--quiet','ism-oracle-bank-review.service']).returncode!=0:break
            time.sleep(1)
        else:raise RuntimeError('Correction publisher has not drained; no policy/files changed')
        subprocess.run(['systemctl','stop','ism-api'],check=True)
        code=(backup/'recovery.py').read_text().split("if __name__=='__main__':",1)[0]
        code+="\nimport psycopg\nwith psycopg.connect('dbname=mpsc') as c: suspend(c,"+repr(json.loads((backup/'policy.json').read_text()))+")\n"
        subprocess.run(['sudo','-u','postgres','/srv/api/.venv/bin/python','-'],input=code.encode(),check=True)
        restore_files(backup,root,public,manifest)
        subprocess.run(['chown','-R','caddy:caddy',str(public)],check=True)
        subprocess.run(['systemctl','start','ism-api'],check=True)
    finally:
        for unit in reversed(active):subprocess.run(['systemctl','start',unit],check=True)
    print('Prior API/static/policy restored. Additive schema, receipts and entitlements retained. Rehearse a forward repair before reenabling v2.')


if __name__=='__main__':
    assert len(sys.argv)==2
    main(Path(sys.argv[1]).resolve())
