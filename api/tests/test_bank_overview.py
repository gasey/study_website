"""Overview counts canonical records once and never expands reviewer access."""
from uuid import uuid4
from test_admin_workbench import workbench

def test_overview_membership_dedup_and_permissions(client,actor,workbench,database):
    ids,paper,alternate=workbench
    conn=database[1];cid='overview-'+uuid4().hex
    other=conn.execute('SELECT paper_id FROM appearances WHERE id=%s',(alternate,)).fetchone()[0]
    conn.execute("INSERT INTO collections(id,title,kind,live_version) VALUES(%s,'Overview test','exam',2)",(cid,))
    for version,pid,browse in [(2,paper,True),(2,other,True),(1,'paper-test',True)]:
        conn.execute('INSERT INTO collection_papers(collection_id,version,paper_id,allow_browse) VALUES(%s,%s,%s,%s)',(cid,version,pid,browse))
    actor('owner')
    r=client.get('/api/admin/bank/summary');assert r.status_code==200,r.text
    data=r.json()['overview'];row=next(e for e in data['exams'] if e['id']==cid)
    assert row['questions']==8 # alternate appearance must not double count
    assert row['papers']==2 and row['mapped_papers']==0
    assert row['held']==1 and row['live']==7 and row['written']==1
    assert row['missing_subject']==0 and row['missing_topic']==8
    assert row['missing_answer']==1 and row['missing_explanation']==7
    assert row['source_issue']==1
    conn.execute('UPDATE collection_papers SET allow_browse=false WHERE collection_id=%s AND paper_id=%s AND version=2',(cid,paper))
    row=next(e for e in client.get('/api/admin/bank/summary').json()['overview']['exams'] if e['id']==cid)
    assert row['questions']==1 and row['papers']==1
    actor('reviewer1');assert client.get('/api/admin/bank/summary').json()['overview'] is None
    actor('outsider');assert client.get('/api/admin/bank/summary').status_code==403
