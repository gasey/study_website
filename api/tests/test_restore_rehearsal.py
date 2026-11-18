from datetime import datetime,timedelta,timezone
import hashlib,importlib.util,io,json,tarfile
from pathlib import Path
import pytest
from app.services.restore_health import observation

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('monthly_restore',ROOT/'scripts/rehearse-monthly-restore.py')
restore=importlib.util.module_from_spec(spec);spec.loader.exec_module(restore)


def receipt(at,**changes):
    data={'schema':1,'source':'paired-backup-restore-v1','state':'verified','completed_at':at.isoformat(),
          'backup_at':(at-timedelta(hours=12)).isoformat(),'restored_files':3,'restored_tables':249,
          **{k:'a'*64 for k in ('archive_sha256','database_sha256','bank_sha256','report_sha256','operator_sha256','api_snapshot_sha256')},
          **{k:True for k in ('bank_pair_matches','database_restored','files_restored','read_only_role_checked','clone_removed','temporary_files_removed')},**changes}
    return {'last_ok':at,'last_beat':at+timedelta(seconds=2),'note':json.dumps(data)}


def test_only_actual_restore_evidence_counts_and_collection_latency_is_allowed():
    now=datetime.now(timezone.utc)
    assert observation(None,now)['days_since'] is None
    row=receipt(now-timedelta(seconds=20));r=observation(row,now)
    assert r['state']=='healthy' and r['days_since']==0
    for key in ('database_restored','files_restored','read_only_role_checked','clone_removed','temporary_files_removed'):
        assert observation(receipt(now,**{key:False}),now)['state']=='unknown'
    assert observation(receipt(now,source='sha256_pair_and_dump_index'),now)['state']=='unknown'
    assert observation(receipt(now,restored_tables=True),now)['state']=='unknown'
    assert observation(receipt(now,report_sha256='not-a-digest'),now)['state']=='unknown'


def test_age_40_future_receipts_and_failed_attempt_preserve_last_success():
    now=datetime.now(timezone.utc);old=now-timedelta(days=40)
    assert observation(receipt(now-timedelta(days=39)),now)['state']=='healthy'
    aged=observation(receipt(old),now);assert aged['state']=='attention' and aged['days_since']==40
    assert observation(receipt(now+timedelta(minutes=1)),now)['state']=='unknown'
    row=receipt(now,state='failed');row['last_ok']=old
    failed=observation(row,now);assert failed['state']=='attention' and failed['last_ok']==old and failed['days_since']==40
    row['last_ok']=None;assert observation(row,now)['days_since'] is None
    row['note']='malformed';assert observation(row,now)['state']=='unknown'


def archive(path,rows):
    with tarfile.open(path,'w:gz') as tar:
        for name,body,kind in rows:
            item=tarfile.TarInfo(name);item.type=kind
            if kind==tarfile.REGTYPE:item.size=len(body);tar.addfile(item,io.BytesIO(body))
            else:item.linkname='outside';tar.addfile(item)


def test_actual_archive_extract_and_readback_keep_private_permissions(tmp_path):
    source=tmp_path/'archive.tgz';target=tmp_path/'restored';target.mkdir()
    archive(source,[('bank-workshop/bank/mpsc_bank_v2.json',b'{"questions":[],"papers":[]}',tarfile.REGTYPE),('paper-workbench/example.txt',b'synthetic private recovery file',tarfile.REGTYPE)])
    assert restore.restore_files(source,target)==2
    assert (target/'paper-workbench/example.txt').read_bytes()==b'synthetic private recovery file'
    assert (target/'paper-workbench/example.txt').stat().st_mode&0o777==0o600


@pytest.mark.parametrize('name,kind',[('../escape',tarfile.REGTYPE),('/absolute',tarfile.REGTYPE),('link',tarfile.SYMTYPE),('hardlink',tarfile.LNKTYPE)])
def test_unsafe_archive_entries_never_escape_or_restore(tmp_path,name,kind):
    source=tmp_path/'archive.tgz';target=tmp_path/'restored';target.mkdir()
    archive(source,[(name,b'synthetic',kind)])
    with pytest.raises(ValueError,match='Unsafe archive'):restore.restore_files(source,target)
    assert not (tmp_path/'escape').exists()


def test_newest_incomplete_backup_never_falls_back(tmp_path):
    folder=tmp_path/'20260102T000000Z';folder.mkdir();(folder/'INCOMPLETE').touch()
    (tmp_path/'20260101T000000Z').mkdir()
    with pytest.raises(ValueError,match='Newest backup incomplete'):restore.backup(tmp_path)


def test_digest_validation_and_file_identity_changes_refuse_success(tmp_path,monkeypatch):
    folder=tmp_path/'20260101T000000Z';folder.mkdir();(folder/'workflow.dump').write_bytes(b'synthetic dump')
    archive(folder/'workshop.tar.gz',[('bank-workshop/bank/mpsc_bank_v2.json',b'{}',tarfile.REGTYPE)])
    data={'schema':1,'created_at':folder.name,'archive_sha256':restore.sha(folder/'workshop.tar.gz'),'database_sha256':restore.sha(folder/'workflow.dump'),'bank_sha256':'a'*64}
    (folder/'receipt.json').write_text(json.dumps(data));assert restore.backup(tmp_path)[0]==folder
    original=restore.sha
    def replaced(path):
        value=original(path)
        if path.name=='workflow.dump':
            p=folder/'workshop.tar.gz';p.write_bytes(p.read_bytes()+b'changed')
        return value
    monkeypatch.setattr(restore,'sha',replaced)
    with pytest.raises(ValueError,match='Backup changed during verification'):restore.backup(tmp_path)
