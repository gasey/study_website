from uuid import uuid4
from psycopg.types.json import Jsonb
import pytest

@pytest.fixture
def history(database,client):
    conn=database[1];batch=uuid4().hex;ids=[]
    for i,(subject,author,publisher,state) in enumerate([
        ('english','owner','owner','applied'),('english','author','reviewer1','failed'),
        ('mizo','owner','owner','applied'),('english','author','owner','exported')]):
        cid='history-con-'+batch+str(i);pid='history-pub-'+batch+str(i)
        conn.execute('''INSERT INTO bank_contributions(id,author_id,canonical_id,kind,subject_id,title,state,idempotency_key,request_hash)
          VALUES(%s,%s,'cq_test','explanation',%s,%s,'published',%s,'test')''',(cid,author,subject,'History '+batch+str(i),cid))
        manifest={'baseline':{'record':{'explanation':'Old reasoning','qnum':'7'},'paper':{'title':'History paper'}},
          'payload':{'rationale':'Correct the historical explanation.','patch':{'explanation':'Requested reasoning'}}}
        receipt={'before':{'explanation':'Old reasoning'},'after':{'explanation':'Recorded reasoning'}} if state=='applied' else None
        conn.execute('''INSERT INTO bank_publications(id,contribution_id,revision,manifest,manifest_hash,exported_by,state,receipt,finished_at)
          VALUES(%s,%s,1,%s,'test',%s,%s,%s,CASE WHEN %s='applied' THEN now() ELSE NULL END)''',
          (pid,cid,Jsonb(manifest),publisher,state,Jsonb(receipt),state));ids.append(pid)
    return batch,ids

def test_history_scope_filters_and_pagination(client,actor,history):
    batch,ids=history;actor('owner')
    url='/api/admin/bank/publication-history'
    page=client.get(url,params={'q':batch,'limit':1}).json()
    assert len(page['items'])==1 and page['next_offset']==1
    second=client.get(url,params={'q':batch,'limit':1,'offset':1}).json()
    assert page['items'][0]['id']!=second['items'][0]['id']
    all_mine=client.get(url,params={'q':batch}).json()['items']
    assert {r['id'] for r in all_mine}=={ids[0],ids[2],ids[3]}
    assert all('manifest' not in r and 'receipt' not in r for r in all_mine)
    all_rows=client.get(url,params={'q':batch,'mine':False}).json()['items']
    assert len(all_rows)==4
    assert [r['id'] for r in client.get(url,params={'q':batch,'mine':False,'state':'failed'}).json()['items']]==[ids[1]]
    actor('reviewer1')
    visible=client.get(url,params={'q':batch,'mine':False}).json()['items']
    assert {r['id'] for r in visible}=={ids[0],ids[1],ids[3]}
    assert client.get(url,params={'q':'x'*201}).status_code==422
    assert client.get(url,params={'state':'published'}).status_code==422
    actor('outsider');assert client.get(url).status_code==403

def test_history_details_use_receipt_and_preserve_gates(client,actor,history,database):
    _,ids=history;actor('owner')
    url='/api/admin/bank/publication-history/'
    response=client.get(url+ids[0]);assert response.status_code==200,response.text
    assert response.headers['cache-control']=='private, no-store'
    change=response.json()['changes'][0]
    assert change['before']=='Old reasoning' and change['after']=='Recorded reasoning'
    assert change['recorded_after'] is True
    pending=client.get(url+ids[3]).json()['changes'][0]
    assert pending['after']=='Requested reasoning' and pending['recorded_after'] is False
    actor('reviewer1');assert client.get(url+ids[2]).status_code==403
    database[1].execute("INSERT INTO collections(id,title,kind) VALUES ('history-mock','History mock','exam') ON CONFLICT DO NOTHING")
    mid='history-mock-'+uuid4().hex
    database[1].execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES (%s,'owner','history-mock',ARRAY['cq_test'],60)",(mid,))
    actor('owner');assert client.get(url+ids[0]).status_code==409
    database[1].execute('DELETE FROM mock_sessions WHERE id=%s',(mid,))
    actor('outsider');assert client.get(url+ids[0]).status_code==403
