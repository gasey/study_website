"""Actual mpsc reads of public share metadata, never assessment/learner state."""
from html.parser import HTMLParser
from uuid import uuid4
import pytest
from app.config import settings
from test_shareable_tests import create, publish
from test_mobile_companion import connect

class Metadata(HTMLParser):
    def __init__(self, body):
        super().__init__(); self.meta={}; self.links={}; self.feed(body)
    def handle_starttag(self, tag, attrs):
        p=dict(attrs)
        if tag=='meta':self.meta[p.get('property',p.get('name',''))]=p.get('content')
        if tag=='link':self.links[p.get('rel')]=p.get('href')


def test_public_question_source_metadata_is_answer_free_and_identity_independent(client, actor, database):
    conn=database[1]
    conn.execute("UPDATE canonical_questions SET question=%s,explanation='PRIVATE SOLUTION SENTINEL' WHERE id='cq_test'",('Which <synthetic> choice & \"Mizo\" word?\nSecond line.',))
    url='/api/questions/cq_test/share?paper=paper-test'
    before=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    client.cookies.clear();r=client.get(url,headers={'Host':'evil.invalid'})
    assert r.status_code==200,r.text
    m=Metadata(r.text)
    assert m.meta['og:title']=='Which <synthetic> choice & "Mizo" word?\nSecond line.'
    assert 'Synthetic source paper · 2020 · Q1' in m.meta['og:description']
    assert m.meta['og:site_name']=='Finna' and m.meta['og:image']==settings.public_origin+'/og-finna.png'
    assert m.meta['og:image:width']=='1200' and m.meta['og:image:height']=='630'
    assert '/bank/cq_test?paper=paper-test&exam_scope=mizoram-recruitment' in m.links['canonical']
    assert 'evil.invalid' not in r.text and 'PRIVATE' not in r.text and '<synthetic>' not in r.text
    assert 'http-equiv' not in r.text and 'Set-Cookie' not in r.headers
    assert r.headers['cache-control']=='no-store' and 'etag' not in r.headers
    assert "default-src 'none'" in r.headers['content-security-policy']
    for user in ('author','outsider'):
        actor(user);assert client.get(url).text==r.text
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==before


@pytest.mark.parametrize('status',['held','withdrawn','merged'])
def test_unavailable_question_cannot_share(client,database,status):
    conn=database[1]
    if status=='merged':conn.execute("INSERT INTO canonical_questions(id,type,question) VALUES ('cq_merge_target','descriptive','Synthetic merge target') ON CONFLICT DO NOTHING")
    conn.execute("UPDATE canonical_questions SET status=%s,answer_text=CASE WHEN %s='withdrawn' THEN NULL ELSE 'B' END,merged_into=CASE WHEN %s='merged' THEN 'cq_merge_target' ELSE NULL END WHERE id='cq_test'",(status,status,status))
    try:assert client.get('/api/questions/cq_test/share').status_code==404
    finally:conn.execute("UPDATE canonical_questions SET status='live',answer_text='B',merged_into=NULL WHERE id='cq_test'")


def test_exact_appearance_and_scope_are_required(client,database):
    conn=database[1]
    assert client.get('/api/questions/missing/share').status_code==404
    assert client.get('/api/questions/cq_test/share?paper=not-the-source').status_code==404
    conn.execute("UPDATE papers SET exam_scope_id='outside-mizoram' WHERE id='paper-test'")
    try:
        assert client.get('/api/questions/cq_test/share').status_code==404
        r=client.get('/api/questions/cq_test/share?exam_scope=all');assert r.status_code==200
        assert 'exam_scope=all' in Metadata(r.text).links['canonical']
    finally:conn.execute("UPDATE papers SET exam_scope_id='mizoram-recruitment' WHERE id='paper-test'")
    assert client.get('/api/questions/cq_test/share?exam_scope=untrusted').status_code==422


def test_test_preview_uses_published_edition_only_and_escapes(client,actor,database):
    title='Synthetic <script>alert("x")</script> '+uuid4().hex[:6]
    user,p,row=create(client,actor,database,title=title,description='Synthetic <img src=x onerror=alert(1)> instructions.')
    url='/api/tests/'+row['id']+'/share'
    assert client.get(url).status_code==404
    pub=publish(client,actor,row,user)
    client.cookies.clear();r=client.get(url);assert r.status_code==200
    m=Metadata(r.text);assert m.meta['og:title']==title and m.meta['og:image'].endswith('/og-finna.png')
    assert '<script>' not in r.text and '<img src=x' not in r.text
    assert not any(k in r.text for k in ('answer_text','PRIVATE KEY','PRIVATE SOLUTION','published_by','question_ids'))
    assert '1 questions · 7 minutes' in m.meta['og:description']
    assert 'http-equiv' not in r.text and 'Set-Cookie' not in r.headers
    h=actor(user)
    edit=client.post('/api/learning-catalog',headers=h,json={'id':row['id'],'expected_version':pub['version'],'content':{**p,'title':'PRIVATE DRAFT TITLE'},'reason':'Synthetic unpublished edit.'})
    assert edit.status_code==200,edit.text
    assert 'PRIVATE DRAFT TITLE' not in client.get(url).text
    conn=database[1];conn.execute('UPDATE learning_catalog SET live_payload=NULL,live_test_version=NULL WHERE id=%s',(row['id'],))
    assert client.get(url).status_code==404


def test_question_share_remains_outside_native_capabilities(client,actor):
    headers,_=connect(client,actor)
    assert client.get('/api/questions/cq_test/share',headers=headers).status_code==403
