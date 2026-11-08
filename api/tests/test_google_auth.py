from urllib.parse import urlparse,parse_qs
from uuid import uuid4
import pytest
from app.routers import google_auth as g
from app.config import settings

@pytest.fixture
def configured(monkeypatch):
 monkeypatch.setattr(settings,'google_client_id','test-client')
 monkeypatch.setattr(settings,'google_client_secret','test-secret')

def begin(client,monkeypatch,email,subject=None,action='login'):
 sub=subject or uuid4().hex
 monkeypatch.setattr(g,'exchange',lambda code,flow:dict(sub=sub,email=email,email_verified=True))
 r=client.post('/api/auth/google/start',json={'action':action},headers={'Origin':settings.public_origin,'X-Review-CSRF':client.get('/api/auth/session').json().get('csrf','')});assert r.status_code==200,r.text
 state=parse_qs(urlparse(r.json()['url']).query)['state'][0]
 return state,sub

def callback(client,state):
 r=client.get('/api/auth/google/callback',params={'state':state,'code':'synthetic'},follow_redirects=False);assert r.status_code==303,r.text

def finish(client,code=''):
 return client.post('/api/auth/google/finish',json={'code':code},headers={'Origin':settings.public_origin,'X-Review-CSRF':client.get('/api/auth/session').json().get('csrf','')})

def test_new_identity_and_single_use(client,configured,monkeypatch):
 client.cookies.clear();state,sub=begin(client,monkeypatch,uuid4().hex+'@example.test');callback(client,state)
 assert client.get('/api/auth/google/pending').json()['mfa_required'] is False
 r=finish(client);assert r.status_code==200,r.text
 assert client.get('/api/auth/session').json()['authenticated']
 assert finish(client).status_code==401
 assert client.get('/api/auth/google/callback',params={'state':state,'code':'again'}).status_code==400

def test_email_collision_never_replaces_account(client,actor,configured,monkeypatch,database):
 client.cookies.clear();state,_=begin(client,monkeypatch,'author@example.test');callback(client,state)
 r=finish(client);assert r.status_code==409,r.text
 assert database[1].execute("SELECT id FROM users WHERE email='author@example.test'").fetchone()[0]=='author'
 assert not client.get('/api/auth/session').json()['authenticated']

def test_link_requires_same_recent_session_and_preserves_user(client,actor,configured,monkeypatch,database):
 actor('author');state,sub=begin(client,monkeypatch,'different-google@example.test',action='link');callback(client,state)
 r=finish(client);assert r.status_code==200,r.text
 assert database[1].execute('SELECT user_id FROM google_identities WHERE subject=%s',(sub,)).fetchone()[0]=='author'
 assert client.get('/api/auth/session').json()['email']=='author@example.test'
 client.cookies.clear();state,_=begin(client,monkeypatch,'different-google@example.test',subject=sub);callback(client,state);assert finish(client).status_code==200
 assert client.get('/api/auth/session').json()['email']=='author@example.test'
 database[1].execute('DELETE FROM google_identities WHERE subject=%s',(sub,))

def test_invalid_origin_state_and_account_switch(client,actor,configured,monkeypatch):
 client.cookies.clear();assert client.post('/api/auth/google/start',json={}).status_code==403
 state,_=begin(client,monkeypatch,'none@example.test')
 assert client.get('/api/auth/google/callback',params={'state':'wrong','code':'x'}).status_code==400
 actor('author');state,_=begin(client,monkeypatch,'link@example.test',action='link')
 # Replace only the application session; retain OAuth binding cookie.
 client.cookies.set('ism_session','test-session-outsider')
 assert client.get('/api/auth/google/callback',params={'state':state,'code':'x'},follow_redirects=False).status_code==403

def test_mfa_not_bypassed(client,actor,configured,monkeypatch,database):
 sub=uuid4().hex;c=database[1]
 c.execute("INSERT INTO google_identities(subject,user_id) VALUES(%s,'outsider')",(sub,))
 c.execute("INSERT INTO account_mfa(user_id,secret_cipher,enabled_at) VALUES('outsider','synthetic',now()) ON CONFLICT(user_id) DO UPDATE SET enabled_at=now()")
 try:
  client.cookies.clear();state,_=begin(client,monkeypatch,'outsider@example.test',subject=sub);callback(client,state)
  assert client.get('/api/auth/google/pending').json()['mfa_required']
  assert finish(client).status_code==401
  async def consume(cur,user,code):return code=='valid-code'
  monkeypatch.setattr(g.mfa,'consume',consume)
  assert finish(client,'valid-code').status_code==200
  assert client.get('/api/auth/session').json()['mfa_verified']
 finally:
  c.execute("DELETE FROM account_mfa WHERE user_id='outsider'");c.execute('DELETE FROM google_identities WHERE subject=%s',(sub,))
