"""Anonymous HTTP caching must never reuse account or guest progress."""
import asyncio
import pytest

from app.services.public_browse_cache import PublicBrowseCache
from app.services.public_catalog_cache import catalog_cache


@pytest.mark.parametrize('path', [
    '/api/questions?limit=1', '/api/questions/taxonomy',
    '/api/questions/papers', '/api/questions/cq_test',
    '/api/collections', '/api/collections/udc/header',
    '/api/collections/udc', '/api/collections/udc/study-topics',
])
def test_anonymous_browse_has_validators_without_creating_identity(client, database, path):
    client.cookies.clear()
    users = database[1].execute('SELECT count(*) FROM users').fetchone()[0]
    first = client.get(path)
    assert first.status_code == 200, first.text
    assert first.headers['cache-control'] == 'public, max-age=0, must-revalidate'
    assert 'set-cookie' not in first.headers
    assert database[1].execute('SELECT count(*) FROM users').fetchone()[0] == users
    vary = {name.strip().lower() for name in first.headers['vary'].split(',')}
    assert {'cookie', 'authorization', 'x-device-id'} <= vary
    etag = first.headers['etag']
    for condition in (etag, 'W/' + etag, '"old", W/' + etag, '*'):
        cached = client.get(path, headers={'If-None-Match': condition})
        assert cached.status_code == 304 and cached.content == b''
        assert cached.headers['etag'] == etag
        assert 'content-length' not in cached.headers


@pytest.mark.parametrize('headers', [
    {'Cookie': 'ism_session=test-session-author'},
    {'Cookie': 'ism_guest=expired-guest'},
    {'Cookie': 'preference=theme'},
    {'Cookie': ''}, {'Authorization': 'Bearer unknown'},
    {'Authorization': ''}, {'X-Device-Id': 'untrusted-device'},
])
def test_any_cookie_or_token_bypasses_public_validation(client, headers):
    client.cookies.clear()
    public = client.get('/api/questions?limit=1')
    result = client.get('/api/questions?limit=1', headers={
        **headers, 'If-None-Match': public.headers['etag'],
    })
    assert result.status_code == 200, result.text
    assert result.headers['cache-control'] == 'private, no-store'
    assert 'etag' not in result.headers


def test_history_filter_keeps_guest_identity_and_scopes_never_share_etags(client):
    client.cookies.clear()
    scoped = client.get('/api/questions?limit=1')
    unscoped = client.get('/api/questions?limit=1&exam_scope=all', headers={
        'If-None-Match': scoped.headers['etag'],
    })
    assert unscoped.status_code == 200
    assert scoped.headers['etag'] != unscoped.headers['etag']
    personal = client.get('/api/questions?study_status=wrong')
    assert personal.status_code == 200
    assert personal.headers['cache-control'] == 'private, no-store'
    assert 'ism_guest=' in personal.headers['set-cookie']
    assert 'etag' not in personal.headers


def test_successful_admin_mutation_invalidates_anonymous_etag(client, actor):
    client.cookies.clear()
    first = client.get('/api/collections/udc/header')
    headers = actor('owner')
    # Owner-only read preview POST changes no bank content, but exercises the
    # actual successful admin/collection invalidation boundary.
    result = client.post('/api/admin/bank/retag/preview', headers=headers, json={
        'targets': [{'question_id': 'cq_test', 'appearance_id': 'appearance-test'}],
    })
    assert result.status_code == 200, result.text
    client.cookies.clear()
    fresh = client.get('/api/collections/udc/header', headers={'If-None-Match': first.headers['etag']})
    assert fresh.status_code == 200
    assert fresh.headers['etag'] != first.headers['etag']


def test_content_change_without_process_invalidation_changes_validator(client, database):
    client.cookies.clear()
    path = '/api/collections/udc/header'
    first = client.get(path)
    conn = database[1]
    title = conn.execute("SELECT title FROM collections WHERE id='udc'").fetchone()[0]
    try:
        conn.execute("UPDATE collections SET title=%s WHERE id='udc'", (title + ' changed',))
        fresh = client.get(path, headers={'If-None-Match': first.headers['etag']})
        assert fresh.status_code == 200
        assert fresh.headers['etag'] != first.headers['etag']
    finally:
        conn.execute("UPDATE collections SET title=%s WHERE id='udc'", (title,))


def test_paper_directory_preserves_title_secondary_path_and_approval_rules(client, database):
    from uuid import uuid4
    from psycopg.types.json import Jsonb

    conn = database[1]
    tag = 'BrowseSentinel' + uuid4().hex[:8]
    paper_ids = []
    for kind in ('title', 'related', 'pending', 'outside'):
        pid = tag + '-' + kind
        paper_ids.append(pid)
        conn.execute('''INSERT INTO papers(id,exam_type,exam_name,source_file,year,exam_scope_id)
            VALUES(%s,'Direct',%s,%s,2026,%s)''',
            (pid, 'English' if kind == 'title' else 'Neutral subject', pid + '.pdf',
             'outside-mizoram' if kind == 'outside' else 'mizoram-recruitment'))
        conn.execute('''INSERT INTO canonical_questions(id,type,question,options,answer_source)
            VALUES(%s,'mcq','Synthetic source membership',%s,'none')''', (pid, Jsonb(['A', 'B'])))
        conn.execute('''INSERT INTO appearances(id,paper_id,canonical_id,type,question,options,is_primary)
            VALUES(%s,%s,%s,'mcq','Synthetic source membership',%s,true)''',
            (pid, pid, pid, Jsonb(['A', 'B'])))
        if kind != 'title':
            conn.execute('''INSERT INTO question_topic_links(question_id,path_id,subject_id,
                subject_label,taxonomy_version,source,review_status,evidence)
                VALUES(%s,'english','english','English','test','manual',%s,'Synthetic filter fixture')''',
                (pid, 'pending' if kind == 'pending' else 'approved'))

    def papers(**params):
        client.cookies.clear()
        result = client.get('/api/questions/papers', params={'q': tag, **params})
        assert result.status_code == 200, result.text
        assert all(item['questions'] == 1 and item['scorable'] == 0 for item in result.json()['items'])
        return result.json()

    assert {item['id'] for item in papers()['items']} == set(paper_ids[:2])
    assert {item['id'] for item in papers(subject_id='english')['items']} == {paper_ids[1]}
    assert {item['id'] for item in papers(exam_scope='all')['items']} == {paper_ids[0], paper_ids[1], paper_ids[3]}
    assert papers(limit=1)['total'] == papers(limit=1, offset=1)['total'] == 2
    assert papers(year_from=2027)['items'] == []


@pytest.mark.parametrize('path', [
    '/api/me/progress', '/api/questions/cq_test/answer-comparison',
    '/api/questions/cq_test/practice-state', '/api/admin/bank/questions',
    '/api/questions/not-found', '/api/collections/not-found',
])
def test_personal_admin_and_error_responses_never_get_public_validators(client, path):
    client.cookies.clear()
    response = client.get(path, headers={'If-None-Match': '*'})
    assert response.status_code != 304
    assert response.headers.get('cache-control') == 'private, no-store'
    assert 'etag' not in response.headers


def test_generation_change_during_response_and_cookie_response_fail_private():
    async def run(cookie=False):
        async def endpoint(scope, receive, send):
            headers = [(b'content-type', b'application/json')]
            if cookie:
                headers.append((b'set-cookie', b'identity=secret'))
            await send({'type': 'http.response.start', 'status': 200, 'headers': headers})
            catalog_cache.clear()
            await send({'type': 'http.response.body', 'body': b'{"items":[]}'})
        output = []
        async def send(message):
            output.append(message)
        await PublicBrowseCache(endpoint)({
            'type': 'http', 'method': 'GET', 'path': '/api/questions',
            'headers': [(b'if-none-match', b'*')], 'query_string': b'',
        }, None, send)
        headers = dict(output[0]['headers'])
        assert output[0]['status'] == 200
        assert headers[b'cache-control'] == b'private, no-store'
        assert b'etag' not in headers
        assert output[-1]['body'] == b'{"items":[]}'
    asyncio.run(run())
    asyncio.run(run(cookie=True))


@pytest.mark.parametrize('limit, expected', [(1024, 'public, max-age=0, must-revalidate'),
                                            (8, 'private, no-store')])
def test_chunked_responses_and_buffer_limit_preserve_body(monkeypatch, limit, expected):
    from app.services import public_browse_cache as cache
    monkeypatch.setattr(cache, '_MAX_BODY', limit)

    async def run():
        chunks = [b'{"items":', b'[1,2,3]', b'}']
        async def endpoint(scope, receive, send):
            await send({'type': 'http.response.start', 'status': 200,
                        'headers': [(b'content-type', b'application/json')]})
            for i, chunk in enumerate(chunks):
                await send({'type': 'http.response.body', 'body': chunk,
                            'more_body': i < len(chunks) - 1})
        output = []
        async def send(message):
            output.append(message)
        await PublicBrowseCache(endpoint)({
            'type': 'http', 'method': 'GET', 'path': '/api/questions',
            'headers': [], 'query_string': b'',
        }, None, send)
        assert dict(output[0]['headers'])[b'cache-control'].decode() == expected
        assert b''.join(message.get('body', b'') for message in output[1:]) == b''.join(chunks)
        assert not output[-1].get('more_body', False)
    asyncio.run(run())
