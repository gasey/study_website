#!/usr/bin/env python3
"""Local host evidence and real ExecStopPost outcomes. No application control."""
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

UNITS = {'ism-oracle-bank-review','ism-workshop-backup','ism-stats-refresh'}
KEYS = {'timer:'+x for x in UNITS} | {'probe:disk','probe:backup','timer:finna-ops-host'}
BACKUPS = Path('/srv/study/backups/workshop')
CACHE = Path('/run/finna-ops/backup-verified.json')
LOW_DISK = 10*1024**3


def now():
    return datetime.now(timezone.utc)


def record(key, state, note, ok_at=None, **detail):
    assert key in KEYS and state in {'healthy','attention','unknown'}
    return {'worker':key, 'ok_at':ok_at.isoformat() if ok_at else None,
            'note':{'schema':1,'state':state,'note':note,**detail}}


def timer_record(unit, result, at, exit_code=None, exit_status=None):
    if unit not in UNITS or result not in {
        'success','resources','timeout','exit-code','signal','core-dump','watchdog',
        'start-limit-hit','oom-kill','protocol','exec-condition','skip-condition'}:
        raise ValueError('A registered unit and actual SERVICE_RESULT are required')
    # systemd may call a service stopped by SIGTERM a success. A finished
    # oneshot must actually exit zero before we claim job completion.
    ok = result=='success' and exit_code=='exited' and exit_status=='0'
    return record('timer:'+unit,'healthy' if ok else 'attention',
                  'Actual job completed' if ok else 'Actual job failed; inspect unit journal',
                  at if ok else None,service_result=result,
                  exit_code=exit_code if exit_code in {'exited','killed','dumped'} else 'unavailable')


def disk_record(path, at):
    usage = os.statvfs(path)
    free, total = usage.f_bavail*usage.f_frsize, usage.f_blocks*usage.f_frsize
    return record('probe:disk','healthy' if free>=LOW_DISK else 'attention',
                  'Measured available host space' if free>=LOW_DISK else 'Available host space below 10 GiB',
                  at,free_bytes=free,total_bytes=total,warning_below_bytes=LOW_DISK)


def file_signature(path):
    s = path.lstat()
    if not stat.S_ISREG(s.st_mode):raise ValueError('Regular backup files required')
    return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        while chunk:=f.read(1024*1024):h.update(chunk)
    return h.hexdigest()


def backup_record(root, cache, at):
    # Never fall back silently when the newest snapshot is incomplete/corrupt.
    folders = sorted((p for p in root.iterdir() if re.fullmatch(r'\d{8}T\d{6}Z',p.name)),reverse=True)
    if not folders:return record('probe:backup','unknown','No paired backup receipt found')
    folder=folders[0]
    if folder.is_symlink() or not folder.is_dir() or (folder/'INCOMPLETE').exists():
        raise ValueError('Newest backup incomplete')
    receipt=folder/'receipt.json'
    if receipt.stat().st_size>16384:raise ValueError('Oversized backup receipt')
    signatures={name:file_signature(folder/name) for name in ('receipt.json','workflow.dump','workshop.tar.gz')}
    data=json.loads(receipt.read_text())
    stamp=datetime.strptime(data['created_at'],'%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
    if data.get('schema')!=1 or folder.name!=data['created_at'] or (stamp-at).total_seconds()>30:
        raise ValueError('Invalid backup receipt identity/time')
    for key in ('archive_sha256','database_sha256','bank_sha256'):
        if not re.fullmatch(r'[0-9a-f]{64}',data[key]):raise ValueError('Invalid backup digest')
    identity={'folder':folder.name,'signatures':signatures,'receipt_sha256':sha(receipt)}
    cached=False
    try:
        s=cache.lstat()
        if stat.S_ISREG(s.st_mode) and s.st_uid==os.geteuid() and s.st_mode&0o077==0:
            cached=json.loads(cache.read_text())==identity
    except (OSError,ValueError):pass
    if not cached:
        if sha(folder/'workflow.dump')!=data['database_sha256'] or sha(folder/'workshop.tar.gz')!=data['archive_sha256']:
            raise ValueError('Paired backup digest mismatch')
        subprocess.run(['pg_restore','--list',str(folder/'workflow.dump')],check=True,
                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=60)
        # Refuse a backup changed during verification, even if a file was replaced.
        if signatures!={name:file_signature(folder/name) for name in signatures}:
            raise ValueError('Backup changed during verification')
        cache.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        fd,name=tempfile.mkstemp(prefix='.verified-',dir=cache.parent)
        try:
            with os.fdopen(fd,'w') as f:json.dump(identity,f)
            os.replace(name,cache)
        finally:
            if os.path.exists(name):os.unlink(name)
    return record('probe:backup','healthy','Paired archive/dump digests verified; dump index readable',
                  stamp,backup_at=stamp.isoformat(),verification='sha256_pair_and_dump_index')


def host_records(at, root=BACKUPS, cache=CACHE, disk=Path('/srv/study')):
    records=[];failed=False
    for key,collect in [('probe:disk',lambda:disk_record(disk,at)),
                        ('probe:backup',lambda:backup_record(root,cache,at))]:
        try:records.append(collect())
        except Exception:
            failed=True
            records.append(record(key,'attention','Collection failed; inspect host collector journal'))
    records.append(record('timer:finna-ops-host','attention' if failed else 'healthy',
                          'Host collection failed' if failed else 'Host collection cycle complete',None if failed else at))
    return records,failed


def write_records(conn, records):
    if not 1<=len(records)<=3:raise ValueError('Bounded records required')
    for row in records:
        if set(row)!={'worker','ok_at','note'} or row['worker'] not in KEYS:
            raise ValueError('Unregistered evidence')
        note=row['note']
        if note.get('schema')!=1 or note.get('state') not in {'healthy','attention','unknown'}:
            raise ValueError('Invalid evidence')
        payload=json.dumps(note,separators=(',',':'))
        if len(payload)>2000:raise ValueError('Oversized evidence')
        stamp=datetime.fromisoformat(row['ok_at']) if row['ok_at'] else None
        if stamp and (stamp.tzinfo is None or (stamp-now()).total_seconds()>30):
            raise ValueError('Invalid success timestamp')
        conn.execute('''INSERT INTO worker_heartbeats(worker,last_beat,last_ok,note)
          VALUES(%s,clock_timestamp(),%s,%s) ON CONFLICT(worker) DO UPDATE
          SET last_beat=clock_timestamp(),last_ok=COALESCE(EXCLUDED.last_ok,worker_heartbeats.last_ok),note=EXCLUDED.note''',
          (row['worker'],stamp,payload))


def persist(records):
    # Peer authentication; neither DB URLs nor service credentials are consumed.
    subprocess.run(['/usr/sbin/runuser','-u','postgres','--','/srv/api/.venv/bin/python',
                    str(Path(__file__).resolve()),'--record'],input=json.dumps(records).encode(),
                   check=True,timeout=15,env={'PATH':'/usr/sbin:/usr/bin:/bin','LANG':'C.UTF-8'})


def main():
    if sys.argv[1:]==['--record']:
        if os.geteuid()!=pwd.getpwnam('postgres').pw_uid:raise PermissionError('Peer writer required')
        raw=sys.stdin.buffer.read(10001)
        if len(raw)>10000:raise ValueError('Oversized evidence')
        import psycopg
        with psycopg.connect('dbname=mpsc connect_timeout=5 options=-cstatement_timeout=5000') as conn:
            write_records(conn,json.loads(raw))
        return
    if os.geteuid()!=0:raise PermissionError('Host collector requires root')
    if sys.argv[1:]==['host']:
        rows,failed=host_records(now());persist(rows)
        print(json.dumps({'collected':[r['worker'] for r in rows],'failed':failed}))
        if failed:raise SystemExit(1)
    elif len(sys.argv)==3 and sys.argv[1]=='unit':
        persist([timer_record(sys.argv[2],os.environ.get('SERVICE_RESULT',''),now(),
                              os.environ.get('EXIT_CODE'),os.environ.get('EXIT_STATUS'))])
    else:raise ValueError('Use host or unit <registered unit>')


if __name__=='__main__':main()
