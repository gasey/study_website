"""Commit-only wakeups and scoped lightweight progress; disposable PostgreSQL."""
import importlib.util
from pathlib import Path
from uuid import uuid4
import psycopg
from test_admin_answers import setup

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('publication_wakeup_test',ROOT/'scripts/publication-wakeup.py')
wakeup=importlib.util.module_from_spec(spec);spec.loader.exec_module(wakeup)


def test_save_notifies_only_after_commit_and_never_on_rollback(client,actor,database):
    q,a,p,h,base,payload=setup(client,actor,database)
    with psycopg.connect(dbname=database[0],autocommit=True,options='-c default_transaction_read_only=on')as listener:
        stream=wakeup.events(listener,timeout=1)
        assert next(stream)=='ready'
        try:
            with database[1].transaction():
                database[1].execute("SELECT pg_notify('ism_bank_publication','')")
                raise ValueError('Rollback a failed save')
        except ValueError:pass
        assert list(listener.notifies(timeout=.05,stop_after=1))==[]
        result=client.post(base,headers=h,json=payload);assert result.status_code==200,result.text
        assert next(stream)=='wake'
        stream.close()


def test_listener_recovers_queued_work_without_a_notification(client,actor,database):
    q,a,p,h,base,payload=setup(client,actor,database)
    result=client.post(base,headers=h,json=payload);assert result.status_code==200,result.text
    with psycopg.connect(dbname=database[0],autocommit=True,options='-c default_transaction_read_only=on')as listener:
        stream=wakeup.events(listener,timeout=.01)
        assert next(stream)=='ready'
        assert next(stream)=='wake' # pending-read fallback after a missed startup event
        stream.close()


def test_pulse_is_permission_scoped_and_changes_after_workflow_update(client,actor,database):
    conn=database[1];actor('owner')
    path='/api/admin/bank/publication-pulse'
    original=client.get(path);assert original.status_code==200,original.text
    actor('reviewer1');english_before=client.get(path).json()
    cid='pulse-'+uuid4().hex
    conn.execute("""INSERT INTO bank_contributions(id,author_id,kind,subject_id,title,state,idempotency_key,request_hash)
       VALUES(%s,'owner','taxonomy','mizo','Synthetic scoped pulse','accepted',%s,'test')""",(cid,cid))
    assert client.get(path).json()==english_before
    actor('owner');changed=client.get(path).json()
    assert changed['revision']!=original.json()['revision'] and changed['pending']==original.json()['pending']+1
    conn.execute("UPDATE bank_contributions SET state='published',lock_version=lock_version+1 WHERE id=%s",(cid,))
    done=client.get(path).json();assert done['revision']!=changed['revision'] and done['pending']==changed['pending']-1
    assert set(done)=={'revision','pending'}
    assert original.headers['cache-control']=='private, no-store'
    actor('outsider');assert client.get(path).status_code==403


def test_wakeup_only_starts_fixed_unit_and_uses_readonly_database(monkeypatch):
    from contextlib import nullcontext
    calls=[];connection=object()
    def connect(database,**kwargs):
        assert database=='postgresql://limited@localhost/test'
        assert kwargs['autocommit'] is True and 'default_transaction_read_only=on' in kwargs['options']
        return nullcontext(connection)
    monkeypatch.setenv('DATABASE_URL','postgresql://limited@localhost/test')
    monkeypatch.setattr(wakeup.psycopg,'connect',connect)
    monkeypatch.setattr(wakeup,'events',lambda c:iter(['ready','malicious unit or payload','wake']))
    monkeypatch.setattr(wakeup.subprocess,'run',lambda command,**kwargs:calls.append(command))
    wakeup.serve()
    assert calls==[['systemctl','start','--no-block','ism-oracle-bank-review.service']]*2
