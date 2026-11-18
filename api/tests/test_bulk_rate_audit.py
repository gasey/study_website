"""Final read-only owner receipt endpoint, over actual synthetic claims."""
from test_bulk_rates import user,code,claim,BASE

def test_owner_claim_receipts_private_closed_history_and_cursor(client,actor,database):
    uid,_=user(database);row=code(client,actor('owner'));assert claim(client,actor,uid,row['code']).status_code==200
    path=BASE+'/admin/codes/'+row['code']+'/claims'
    assert client.get(path,headers=actor('reviewer1')).status_code==403
    r=client.get(path,headers=actor('owner'));assert r.status_code==200,r.text
    assert r.headers['cache-control']=='private, no-store' and r.json()['items'][0]['user_id']==uid
    assert not {'password_hash','token','scoring_snapshot'} & set(r.json()['items'][0])
    assert client.get(path,params={'after':uid}).json()['items']==[]
    conn=database[1]
    conn.execute("UPDATE users SET email=NULL,password_hash=NULL,name=NULL,avatar=NULL,email_verified_at=NULL,contribution_public=false,closed_at=now() WHERE id=%s",(uid,))
    r=client.get(path);assert r.json()['items'][0]['closed'] and r.json()['items'][0]['email'] is None
    assert client.get(BASE+'/admin/codes/'+'A'*24+'/claims').status_code==404
