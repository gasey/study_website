"""Unknown operator modes must fail before locking or any network/database action."""
import os
from pathlib import Path
import subprocess

def test_unknown_sync_flag_never_falls_through_to_writing(tmp_path):
    root=Path(__file__).resolve().parents[2]
    for args in [['--status'],['--check','extra']]:
        result=subprocess.run(['bash',str(root/'scripts/sync-bank.sh'),*args],env={**os.environ,'ISM_BANK':str(tmp_path/'absent.json')},capture_output=True,text=True)
        assert result.returncode==2
        assert not (tmp_path/'absent.json.lock').exists()


def test_primary_sync_preserves_retired_difficulty(client,database):
    from uuid import uuid4
    from psycopg.types.json import Jsonb
    conn=database[1];qid='cq_retired_'+uuid4().hex
    conn.execute("INSERT INTO canonical_questions(id,type,question,options,difficulty) VALUES (%s,'mcq','Synthetic retired difficulty',%s,'hard')",(qid,Jsonb(['A','B'])))
    conn.execute("INSERT INTO appearances(id,paper_id,canonical_id,is_primary,type,question,options,difficulty) VALUES (%s,'paper-test',%s,true,'mcq','Synthetic retired difficulty',%s,'medium')",('a_'+qid,qid,Jsonb(['A','B'])))
    script=(Path(__file__).resolve().parents[2]/'scripts/sync-bank.sh').read_text()
    block='UPDATE canonical_questions c SET\n    question'+script.split('UPDATE canonical_questions c SET\n    question',1)[1].split(';',1)[0]
    conn.execute(block+' AND c.id=%s',(qid,))
    assert conn.execute('SELECT difficulty FROM canonical_questions WHERE id=%s',(qid,)).fetchone()[0] is None
    assert conn.execute('SELECT difficulty FROM appearances WHERE canonical_id=%s',(qid,)).fetchone()[0]=='medium'
