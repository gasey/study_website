#!/usr/bin/env python3
"""Root-only real paired-backup restore into disposable files and PostgreSQL.

No bank content, learner data, publisher, Caddy, provider or service is changed.
Only an actual completed rehearsal writes a verified operational receipt.
"""
import fcntl,hashlib,json,os,re,shutil,stat,subprocess,sys,tarfile,tempfile
from datetime import datetime,timezone
from pathlib import Path,PurePosixPath
from uuid import uuid4

API=Path('/srv/api')
BACKUPS=Path('/srv/study/backups/workshop')
REPORTS=Path('/srv/study/backups/restore-rehearsals')
SOURCE='paired-backup-restore-v1'


def now():return datetime.now(timezone.utc)
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as source:
        while block:=source.read(1024*1024):h.update(block)
    return h.hexdigest()


def run(args,**kwargs):
    p=subprocess.run(args,capture_output=True,timeout=900,**kwargs)
    if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace')[-4000:] if isinstance(p.stderr,bytes) else p.stderr[-4000:])
    return p.stdout


def api_sources():
    files=[p for part,pattern in [('app','*.py'),('migrations','*.sql')] for p in (API/part).rglob(pattern)]
    files.append(API/'app/data/learning-economy-v2.json')
    return {str(p.relative_to(API)):sha(p) for p in sorted(files)}


def backup(root):
    folders=sorted((p for p in root.iterdir() if re.fullmatch(r'\d{8}T\d{6}Z',p.name)),reverse=True)
    if not folders:raise ValueError('No paired backup exists')
    folder=folders[0]
    if folder.is_symlink() or not folder.is_dir() or (folder/'INCOMPLETE').exists():raise ValueError('Newest backup incomplete')
    paths=(folder/'receipt.json',folder/'workflow.dump',folder/'workshop.tar.gz')
    for p in paths:
        if not stat.S_ISREG(p.lstat().st_mode):raise ValueError('Regular backup files required')
    signatures={p.name:[p.stat().st_dev,p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns,p.stat().st_ctime_ns] for p in paths}
    if (folder/'receipt.json').stat().st_size>16384:raise ValueError('Oversized backup receipt')
    data=json.loads((folder/'receipt.json').read_text())
    stamp=datetime.strptime(data['created_at'],'%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
    if data.get('schema')!=1 or folder.name!=data['created_at'] or stamp>now():raise ValueError('Invalid backup identity/time')
    for key in ('archive_sha256','database_sha256','bank_sha256'):
        if not re.fullmatch(r'[0-9a-f]{64}',data.get(key,'')):raise ValueError('Invalid backup digest')
    for name,key in [('workshop.tar.gz','archive_sha256'),('workflow.dump','database_sha256')]:
        if (folder/name).is_symlink() or not (folder/name).is_file() or sha(folder/name)!=data[key]:raise ValueError('Backup digest mismatch')
    if signatures!={p.name:[p.stat().st_dev,p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns,p.stat().st_ctime_ns] for p in paths}:raise ValueError('Backup changed during verification')
    return folder,data,stamp,signatures


def members(archive):
    rows=archive.getmembers();seen=set()
    for row in rows:
        p=PurePosixPath(row.name)
        if p.is_absolute() or '..' in p.parts or not p.parts or not (row.isdir() or row.isfile()):raise ValueError('Unsafe archive member')
        if row.name in seen:raise ValueError('Duplicate archive member')
        seen.add(row.name)
    return rows


def restore_files(source,destination):
    count=0
    with tarfile.open(source,'r:gz') as archive:
        rows=members(archive)
        if shutil.disk_usage(destination).free<sum(r.size for r in rows)+2*1024**3:raise ValueError('Insufficient archive-restore headroom')
        for row in rows:
            target=destination.joinpath(*PurePosixPath(row.name).parts)
            if row.isdir():target.mkdir(parents=True,exist_ok=True,mode=0o700);continue
            target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            digest=hashlib.sha256()
            with archive.extractfile(row) as stream,target.open('xb') as output:
                while block:=stream.read(1024*1024):output.write(block);digest.update(block)
            target.chmod(0o600)
            if sha(target)!=digest.hexdigest() or target.stat().st_size!=row.size:raise ValueError('Restored file readback mismatch')
            count+=1
    return count


def heartbeat(receipt):
    code="""import sys,json,psycopg
from psycopg.types.json import Jsonb
r=json.load(sys.stdin)
with psycopg.connect('dbname=mpsc') as c:
 c.execute('SET LOCAL ROLE mpsc')
 c.execute('''INSERT INTO worker_heartbeats(worker,last_beat,last_ok,note)
 VALUES('restore-rehearsal',clock_timestamp(),CASE WHEN %s THEN %s::timestamptz END,%s)
 ON CONFLICT(worker) DO UPDATE SET last_beat=clock_timestamp(),
 last_ok=CASE WHEN %s THEN EXCLUDED.last_ok ELSE worker_heartbeats.last_ok END,note=EXCLUDED.note''',
 (r['state']=='verified',r['completed_at'],json.dumps(r),r['state']=='verified'))
"""
    run(['sudo','-u','postgres',str(API/'.venv/bin/python'),'-c',code],input=json.dumps(receipt).encode())


def rehearsal():
    assert os.geteuid()==0,'Root is required for private backup reads'
    REPORTS.mkdir(mode=0o700,parents=True,exist_ok=True);REPORTS.chmod(0o700)
    lock=Path('/run/lock/finna-restore-rehearsal.lock').open('a');lock_path=Path(lock.name);lock_path.chmod(0o600)
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    sources=api_sources();index=sha(Path('/srv/study/public/index.html'))
    started=now();database='finna_restore_rehearsal_'+uuid4().hex[:12];created=False;temporary=None
    result={'schema':1,'source':SOURCE,'state':'failed','started_at':started.isoformat(),
            'operator_sha256':sha(Path(__file__)),
            'api_snapshot_sha256':hashlib.sha256(json.dumps(sources,sort_keys=True).encode()).hexdigest()}
    try:
        folder,receipt,backup_at,before=backup(BACKUPS)
        with tarfile.open(folder/'workshop.tar.gz','r:gz') as archive:archive_bytes=sum(r.size for r in members(archive))
        database_bytes=max(4*1024**3,(folder/'workflow.dump').stat().st_size*8)
        same_disk=REPORTS.stat().st_dev==Path('/var/lib/postgresql').stat().st_dev
        reserve=10*1024**3
        if shutil.disk_usage(REPORTS).free<archive_bytes+(database_bytes if same_disk else 0)+reserve:raise ValueError('Insufficient combined restore headroom')
        if not same_disk and shutil.disk_usage('/var/lib/postgresql').free<database_bytes+reserve:raise ValueError('Insufficient database-restore headroom')
        temporary=Path(tempfile.mkdtemp(prefix='finna-monthly-restore-',dir=REPORTS))
        restored_files=restore_files(folder/'workshop.tar.gz',temporary)
        bank=temporary/'bank-workshop/bank/mpsc_bank_v2.json'
        if sha(bank)!=receipt['bank_sha256']:raise ValueError('Restored bank digest mismatch')
        run(['sudo','-u','postgres','psql','-X','-q','-d','postgres','-c','CREATE DATABASE '+database]);created=True
        with (folder/'workflow.dump').open('rb') as dump:
            run(['sudo','-u','postgres','pg_restore','--exit-on-error','--no-owner','-d',database],stdin=dump)
        query="""BEGIN READ ONLY;SET LOCAL ROLE mpsc;
 SELECT json_build_object('database_role',current_user,'read_only',current_setting('transaction_read_only'),
 'bank_sha256',(SELECT bank_checksum FROM sync_log WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1),
 'tables',(SELECT count(*) FROM pg_tables WHERE schemaname='public'),
 'attempts',(SELECT count(*) FROM attempts),'ledger_rows',(SELECT count(*) FROM reward_ledger),
 'users',(SELECT count(*) FROM users),'registered_accounts',(SELECT count(*) FROM users WHERE email IS NOT NULL));ROLLBACK;"""
        checked=json.loads(run(['sudo','-u','postgres','psql','-X','-qAt','-d',database,'-c',query]))
        if checked['database_role']!='mpsc' or checked['read_only']!='on' or checked['bank_sha256']!=receipt['bank_sha256']:raise ValueError('Restored database/pair readback mismatch')
        after={p.name:[p.stat().st_dev,p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns,p.stat().st_ctime_ns] for p in (folder/'receipt.json',folder/'workflow.dump',folder/'workshop.tar.gz')}
        if before!=after or sources!=api_sources() or index!=sha(Path('/srv/study/public/index.html')):raise ValueError('Source changed during restore rehearsal')
        result.update(state='verified',backup_at=backup_at.isoformat(),archive_sha256=receipt['archive_sha256'],database_sha256=receipt['database_sha256'],bank_sha256=receipt['bank_sha256'],bank_pair_matches=True,database_restored=True,files_restored=True,read_only_role_checked=True,restored_tables=checked['tables'],restored_files=restored_files,database_counts=checked)
    except Exception as exc:
        result['diagnostic_kind']=type(exc).__name__;result['diagnostic']=str(exc)[-4000:]
    finally:
        try:
            if created:run(['sudo','-u','postgres','psql','-X','-q','-d','postgres','-c','DROP DATABASE '+database+' WITH (FORCE)'])
            result['clone_removed']=True
            if temporary:shutil.rmtree(temporary)
            result['temporary_files_removed']=True
        except Exception as exc:
            result.update(state='failed',cleanup_failure=type(exc).__name__)
    result['completed_at']=now().isoformat()
    report=REPORTS/(now().strftime('%Y%m%dT%H%M%SZ')+'-'+uuid4().hex[:6]+'.json')
    report.write_text(json.dumps(result,indent=2)+'\n');report.chmod(0o600)
    public={k:v for k,v in result.items() if k not in ('diagnostic','database_counts')};public['report_sha256']=sha(report)
    heartbeat(public)
    print(json.dumps({'state':result['state'],'report':str(report),'receipt':public}))
    if result['state']!='verified':raise SystemExit(1)


if __name__=='__main__':
    assert sys.argv[1:]==['--run'],'Use --run for an actual isolated paired restore'
    rehearsal()
