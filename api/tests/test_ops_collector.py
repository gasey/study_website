"""Real paired dump validation, cache invalidation and private durable receipts."""
import hashlib,importlib.util,json,shutil,subprocess,tarfile
from datetime import datetime,timedelta,timezone
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('ops_collector',ROOT/'scripts/ops-collector.py')
collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)


@pytest.fixture(scope='module')
def dump(database,tmp_path_factory):
    path=tmp_path_factory.mktemp('ops-paired-dump')/'workflow.dump'
    subprocess.run(['pg_dump','-Fc','--schema-only',database[0],'-f',str(path)],check=True)
    return path


def backup(tmp_path,dump,at):
    root=tmp_path/'backups';folder=root/(at-timedelta(hours=1)).strftime('%Y%m%dT%H%M%SZ');folder.mkdir(parents=True)
    shutil.copyfile(dump,folder/'workflow.dump')
    bank=tmp_path/'bank.json';bank.write_text('{"questions":[],"papers":[]}')
    with tarfile.open(folder/'workshop.tar.gz','w:gz') as archive:archive.add(bank,arcname='bank-workshop/bank/mpsc_bank_v2.json')
    (folder/'receipt.json').write_text(json.dumps({'schema':1,'created_at':folder.name,'archive_sha256':collector.sha(folder/'workshop.tar.gz'),'database_sha256':collector.sha(folder/'workflow.dump'),'bank_sha256':collector.sha(bank)}))
    return root,folder,tmp_path/'cache'/'verified.json'


def test_actual_dump_pair_verifies_and_metadata_cache_detects_corruption(tmp_path,dump,monkeypatch):
    at=datetime.now(timezone.utc);root,folder,cache=backup(tmp_path,dump,at)
    row=collector.backup_record(root,cache,at)
    assert row['note']['state']=='healthy' and row['ok_at']==row['note']['backup_at']
    assert row['ok_at']!=at.isoformat(),'Backup creation is not collector execution time'
    original=collector.sha
    calls=[]
    def track(path):calls.append(path.name);return original(path)
    monkeypatch.setattr(collector,'sha',track)
    collector.backup_record(root,cache,at)
    assert calls==['receipt.json'],'Unchanged verified pair must not be rehashed every five minutes'
    with (folder/'workflow.dump').open('ab') as f:f.write(b'corruption')
    with pytest.raises(ValueError,match='digest mismatch'):collector.backup_record(root,cache,at)


def test_newest_incomplete_backup_never_falls_back_and_other_probe_survives(tmp_path,dump):
    at=datetime.now(timezone.utc);root,folder,cache=backup(tmp_path,dump,at)
    newest=root/at.strftime('%Y%m%dT%H%M%SZ');newest.mkdir();(newest/'INCOMPLETE').touch()
    rows,failed=collector.host_records(at,root,cache,tmp_path)
    assert failed
    assert rows[0]['worker']=='probe:disk' and rows[0]['note']['state'] in ('healthy','attention')
    assert rows[1]['note']['state']=='attention' and rows[1]['ok_at'] is None
    assert rows[2]['note']['state']=='attention'


def test_synthetic_unit_outcome_failure_preserves_prior_success(database):
    conn=database[1];at=datetime.now(timezone.utc)
    with conn.transaction():
        conn.execute('SET LOCAL ROLE mpsc')
        good=collector.timer_record('ism-stats-refresh','success',at,'exited','0');collector.write_records(conn,[good])
        fail=collector.timer_record('ism-stats-refresh','timeout',at+timedelta(seconds=1));collector.write_records(conn,[fail])
        row=conn.execute("SELECT last_ok,note FROM worker_heartbeats WHERE worker='timer:ism-stats-refresh'").fetchone()
        assert row[0]==at and json.loads(row[1])['service_result']=='timeout'
    assert collector.timer_record('ism-stats-refresh','success',at,'killed','TERM')['note']['state']=='attention'
    assert collector.timer_record('ism-stats-refresh','success',at)['note']['state']=='attention'
    for unit,result in [('other','success'),('ism-stats-refresh','')]:
        with pytest.raises(ValueError):collector.timer_record(unit,result,at)
    with pytest.raises(ValueError):collector.write_records(conn,[{'worker':'other','ok_at':None,'note':{}}])


def test_snapshot_probes_reject_invalid_stale_or_future_evidence():
    from app.services.ops import collected,heartbeat
    at=datetime.now(timezone.utc)
    row={'last_beat':at,'last_ok':at,'note':json.dumps({'schema':1,'state':'healthy','note':'measured','free_bytes':11*1024**3,'total_bytes':20*1024**3})}
    assert collected(row,at,'disk')['state']=='healthy'
    row['last_beat']=at-timedelta(minutes=16);assert collected(row,at,'disk')['state']=='stale'
    row['last_beat']=at+timedelta(minutes=1);assert collected(row,at,'disk')['state']=='unknown'
    row['last_beat']=at;row['note']='not json';assert collected(row,at,'disk')['state']=='unknown'
    row['note']=json.dumps({'schema':1,'state':'healthy','note':'measured','free_bytes':-1,'total_bytes':20})
    assert collected(row,at,'disk')['state']=='unknown'
    row.update(last_beat=at,last_ok=at,note='failed: immediate failure after success')
    assert heartbeat('x','x',60,row,at)['state']=='attention'


def test_collector_success_allows_real_collection_and_peer_write_latency(client,actor,database):
    # Checksum work and runuser startup happen between event time and DB commit.
    # A fresh explicit successful outcome must not be judged by the in-process
    # beat timestamp tolerance. Failures still keep their prior success visible.
    conn=database[1];at=datetime.now(timezone.utc)
    for state in ('healthy','attention'):
        note=json.dumps({'schema':1,'state':state,'note':'Synthetic host collection outcome'})
        conn.execute("INSERT INTO worker_heartbeats(worker,last_beat,last_ok,note) VALUES('timer:finna-ops-host',now(),now()-interval '10 seconds',%s) ON CONFLICT(worker) DO UPDATE SET last_beat=EXCLUDED.last_beat,last_ok=EXCLUDED.last_ok,note=EXCLUDED.note",(note,))
        r=client.get('/api/admin/ops',headers=actor('owner'));assert r.status_code==200,r.text
        row=next(t for t in r.json()['timers'] if t['id']=='timer:finna-ops-host')
        assert row['state']==state
