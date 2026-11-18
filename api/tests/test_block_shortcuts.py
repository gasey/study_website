"""Existing account blocks back every new web shortcut; no report is required."""
import pytest
from test_discussions import database,client,approve,question,answer,create
from test_study_posts import ready,note,mixed,status
from test_study_replies import reply,listed
from test_material_shares import share
from test_content_studio import publish,document


@pytest.mark.parametrize('kind',['study','material-share'])
def test_block_private_post_author_hides_detail_and_feed_without_report_or_reward(client,actor,database,kind):
    _,conn=database
    mid=publish(client,actor,document(),user='author') if kind=='material-share' else None
    ready(conn);h=actor('author');pid=(share(client,h,mid) if mid else note(client,h)).json()['id'];approve(client,actor,pid)
    assert not conn.execute("SELECT public FROM creator_profiles WHERE user_id='author'").fetchone()
    h=actor('outsider');assert client.get(f'/api/community/study-posts/{pid}').json()['author_id']=='author';assert pid in mixed(client)
    before=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0];budget=status(client)
    for _ in range(2):assert client.post('/api/creators/author/block',headers=h,json={'enabled':True}).json()=={'blocked':True}
    assert client.get(f'/api/community/study-posts/{pid}').status_code==404;assert pid not in mixed(client)
    assert client.post(f'/api/community/study-posts/{pid}/helpful',headers=h,json={'enabled':True}).status_code==404
    assert client.get('/api/creators/settings').json()['blocked'][0]['id']=='author'
    assert not conn.execute('SELECT 1 FROM abuse_reports').fetchone()
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==before
    assert status(client)['posts_remaining']==budget['posts_remaining']
    assert client.post('/api/creators/author/block',headers=h,json={'enabled':False}).status_code==200
    assert client.get(f'/api/community/study-posts/{pid}').status_code==200


def test_block_reply_author_preserves_own_note_and_filters_before_pagination(client,actor,database):
    _,conn=database;ready(conn);h=actor('author');pid=note(client,h).json()['id'];approve(client,actor,pid)
    other=actor('outsider');rid=reply(client,other,pid).json()['id'];approve(client,actor,rid)
    h=actor('author');assert listed(client,pid)['items'][0]['author_id']=='outsider'
    assert client.post('/api/creators/outsider/block',headers=h,json={'enabled':True}).status_code==200
    assert client.get(f'/api/community/study-posts/{pid}').status_code==200
    assert listed(client,pid,limit=1)['items']==[] and not listed(client,pid,limit=1)['has_more']
    assert client.get(f'/api/community/study-posts/{rid}').status_code==404
    assert client.post('/api/creators/outsider/block',headers=h,json={'enabled':False}).status_code==200
    assert listed(client,pid)['items'][0]['id']==rid


def test_block_question_author_hides_root_and_own_accepted_reply(client,actor,question):
    qid,conn=question;h=answer(client,actor,qid,'author');pid=create(client,h,qid).json()['id'];approve(client,actor,pid)
    other=answer(client,actor,qid,'outsider');rid=create(client,other,qid,kind='reply',parent=pid).json()['id'];approve(client,actor,rid)
    h=actor('author');assert client.post(f'/api/community/posts/{rid}/accept',headers=h,json={'enabled':True}).status_code==200
    other=actor('outsider');assert client.post('/api/creators/author/block',headers=other,json={'enabled':True}).status_code==200
    assert client.get(f'/api/community/questions/{qid}/discussion').json()['items']==[]
    assert client.get(f'/api/community/posts/{pid}/replies').status_code==404
    assert client.get(f'/api/community/posts/{rid}/evidence').status_code==404
    assert pid not in mixed(client,'questions')
    assert not conn.execute('SELECT 1 FROM abuse_reports').fetchone()
