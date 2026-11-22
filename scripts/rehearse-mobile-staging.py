#!/usr/bin/env python3
"""Disposable loopback HTTPS + PostgreSQL rehearsal. Never accepts a remote DSN."""
from pathlib import Path
from uuid import uuid4
import hashlib
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'api/tests'), str(ROOT / 'api')]


def serve(config_path):
    config = json.loads(Path(config_path).read_text())
    name = config['database']
    assert name.startswith('ism_review_test_') and name.removeprefix('ism_review_test_').isalnum()
    from app import config as app_config
    app_config.settings = app_config.Settings(
        _env_file=None, database_url='postgresql:///' + name + '?options=-c%20role%3Dmpsc',
        public_origin=config['origin'], mobile_redirect_uris=['finna-staging://auth/callback'],
        account_mail_enabled=False, review_digest_enabled=False, referral_rewards_enabled=False,
        razorpay_checkout_enabled=False, smtp_host='', smtp_password='', google_client_id='',
        google_client_secret='', admin_token='', pool_min=1, pool_max=6,
        public_catalog_cache_seconds=0,
        registered_document_root=config['root'] + '/documents',
        canonical_workshop_root=config['root'] + '/bank',
        paper_workbench_root=config['root'] + '/workbench',
        paper_archive_root=config['root'] + '/papers',
    )
    # Defaults are explicit above; reject inherited service credentials as well.
    settings = app_config.settings
    assert not any((settings.smtp_username, settings.razorpay_key_id, settings.razorpay_key_secret,
                    settings.razorpay_webhook_secret, settings.mfa_encryption_key))
    from app.main import app
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
    web = ROOT / 'web/dist'
    app.mount('/assets', StaticFiles(directory=web / 'assets'), name='rehearsal-assets')

    @app.get('/{path:path}')
    async def web_fallback(path: str):
        from fastapi import HTTPException
        if path.startswith('api/'):
            raise HTTPException(404)
        return FileResponse(web / 'index.html')

    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=config['port'], ssl_certfile=config['cert'],
                ssl_keyfile=config['key'], access_log=False, log_level='warning')


def main(destination):
    import conftest
    import httpx
    from psycopg.types.json import Jsonb
    from test_study_sessions import seed
    from app.routers.auth import _hash_password
    from app.routers.mobile import challenge_for

    destination.mkdir(parents=True, exist_ok=True)
    prepared = conftest.fresh_database()
    database = next(prepared)
    name, conn = database
    checks = []
    process = None
    result = {'synthetic_only': True, 'production_access': False, 'phone_used': False,
              'native_system_browser_verified': False, 'checks': checks}

    def check(label, condition):
        assert condition, label
        checks.append(label)

    try:
        password = 'Synthetic-' + secrets.token_hex(16) + '1'
        for user in ('stage-a', 'stage-b'):
            conn.execute("INSERT INTO users(id,handle,email,password_hash,plan_code,plan_status,plan_ends_at) VALUES(%s,%s,%s,%s,'pro','active',now()+interval '1 day')",
                         (user, user, user + '@example.test', _hash_password(password)))
        paper, ids = seed(database, 4)
        collection = 'stage-' + uuid4().hex
        conn.execute("INSERT INTO collections(id,title,kind,visibility,live_version) VALUES(%s,'Synthetic staging exam','exam','public',1)", (collection,))
        conn.execute("INSERT INTO collection_papers(collection_id,version,paper_id,section_path,as_mock) VALUES(%s,1,%s,'papers',true)", (collection, paper))
        conn.execute("INSERT INTO collection_sections(collection_id,version,path,title,position,query) VALUES(%s,1,'papers','Papers',0,%s)", (collection, Jsonb({'paper_ids': [paper]})))
        with tempfile.TemporaryDirectory(prefix='finna-mobile-stage-') as temporary:
            private = Path(temporary)
            private.chmod(0o700)
            cert, key = private / 'cert.pem', private / 'key.pem'
            subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
                            '-keyout', str(key), '-out', str(cert), '-subj', '/CN=127.0.0.1',
                            '-addext', 'subjectAltName=IP:127.0.0.1'], check=True, capture_output=True)
            with socket.socket() as listener:
                listener.bind(('127.0.0.1', 0))
                port = listener.getsockname()[1]
            origin = f'https://127.0.0.1:{port}'
            config = dict(database=name, origin=origin, port=port, root=temporary, cert=str(cert), key=str(key))
            config_path = private / 'config.json'
            config_path.write_text(json.dumps(config))
            # No inherited application settings, service credentials or proxies.
            env = {k: v for k, v in os.environ.items() if k in ('PATH', 'HOME', 'USER', 'LANG', 'LD_LIBRARY_PATH')}
            with (destination / 'server.log').open('w') as server_log:
                process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--serve', str(config_path)],
                                           cwd=private, env=env, stdout=server_log, stderr=server_log)
                with httpx.Client(base_url=origin, verify=str(cert), trust_env=False, timeout=30) as api:
                    for _ in range(150):
                        if process.poll() is not None:
                            raise RuntimeError('Loopback server failed; inspect server.log')
                        try:
                            if api.get('/api/health').status_code == 200:
                                break
                        except httpx.TransportError:
                            pass
                        time.sleep(.1)
                    else:
                        raise RuntimeError('Loopback server readiness timed out')
                    check('HTTPS certificate verified; loopback API ready', True)
                    accounts = []
                    for user in ('stage-a', 'stage-b'):
                        verifier, state = secrets.token_urlsafe(48), secrets.token_hex(16)
                        start = api.post('/api/mobile-auth/start', json={'challenge': challenge_for(verifier), 'state': state, 'redirect_uri': 'finna-staging://auth/callback'})
                        assert start.status_code == 200, start.text
                        accounts.append(dict(**start.json(), verifier=verifier, state=state, email=user + '@example.test', user=user))
                    payload = dict(origin=origin, password=password, accounts=accounts, screenshot=str(destination / 'browser-confirmation.png'))
                    node = os.environ.get('FINNA_STAGE_NODE', '/home/hruaia/.nvm/versions/node/v22.23.4/bin/node')
                    browser = subprocess.run([node, str(ROOT / 'scripts/check-mobile-browser-auth.cjs')],
                                             input=json.dumps(payload), text=True, capture_output=True, timeout=90)
                    if browser.returncode:
                        raise RuntimeError(browser.stderr)
                    authorized = json.loads(browser.stdout)
                    result['desktop_browser'] = authorized['browser']
                    result['external_browser_requests_blocked'] = sum(a['external_requests_blocked'] for a in authorized['accounts'])
                    tokens = []
                    for account, callback in zip(accounts, authorized['accounts'], strict=True):
                        exchange = dict(flow=callback['flow'], code=callback['code'], verifier=account['verifier'], redirect_uri='finna-staging://auth/callback')
                        response = api.post('/api/mobile-auth/exchange', json=exchange)
                        assert response.status_code == 200, response.text
                        header = {'Authorization': 'Bearer ' + response.json()['access_token']}
                        tokens.append(header)
                        session = api.get('/api/mobile/session', headers=header)
                        check(account['user'] + ': real browser password login/confirmation and PKCE identity', session.json()['id'] == account['user'])
                        check(account['user'] + ': exchange replay refused', api.post('/api/mobile-auth/exchange', json=exchange).status_code == 400)
                    a, b = tokens
                    body = dict(collection_id=collection, filters={'paper_id': paper}, size=10, request_key=uuid4().hex)
                    started = api.post('/api/study-sessions', headers=a, json=body)
                    assert started.status_code == 200, started.text
                    session = started.json()
                    url = '/api/study-sessions/' + session['id']
                    check('Lost compose response retry returns same study set', api.post('/api/study-sessions', headers=a, json=body).json()['id'] == session['id'])
                    question = session['items'][0]
                    answer = dict(version=session['version'], question_id=question['id'], chosen_index=1, presentation_hash=question['presentation_hash'])
                    first = api.post(url + '/answer', headers=a, json=answer)
                    check('First practice answer accepted', first.status_code == 200)
                    replay = api.post(url + '/answer', headers=a, json=answer)
                    check('Discarded reply retry restores saved answer', replay.status_code == 200 and replay.json()['results'] == first.json()['results'])
                    check('Account switch cannot read earlier study set', api.get(url, headers=b).status_code == 404)
                    check('Account switch cannot answer earlier study set', api.post(url + '/answer', headers=b, json=answer).status_code == 404)
                    check('Replay created exactly one practice attempt', conn.execute('SELECT count(*) FROM attempts WHERE user_id=%s AND canonical_id=%s', ('stage-a', question['id'])).fetchone()[0] == 1)
                    stale = dict(chosen_index=1, request_key=str(uuid4()), expected_question='Stale offline presentation', expected_options=['A', 'B', 'C', 'D'])
                    check('Stale offline presentation refused', api.post('/api/mobile/questions/' + ids[1] + '/answer', headers=a, json=stale).status_code == 409)
                    mock = api.post('/api/mocks', headers=a, json=dict(collection_id=collection, count=2, duration_minutes=1, selection={'paper_id': paper}))
                    assert mock.status_code == 200, mock.text
                    mock = mock.json()
                    mock_url = '/api/mocks/' + mock['id']
                    qid = mock['questions'][0]['id']
                    saved = dict(question_id=qid, chosen_index=1, position=0, marked=False)
                    check('Timed mock saves answer', api.put(mock_url + '/answers', headers=a, json=saved).status_code == 200)
                    conn.execute("UPDATE mock_sessions SET started_at=now()-interval '65 seconds' WHERE id=%s", (mock['id'],))
                    check('Server refuses answer after deadline', api.put(mock_url + '/answers', headers=a, json={**saved, 'chosen_index': 0}).status_code == 409)
                    submit = api.post(mock_url + '/submit', headers=a, json={'answers': []})
                    check('Submission scores only saved choice', submit.status_code == 200 and submit.json()['n_correct'] == 1 and submit.json()['n_skipped'] == 1)
                    check('Lost submission reply retry conflicts safely', api.post(mock_url + '/submit', headers=a, json={'answers': []}).status_code == 409)
                    check('Authoritative result restores after lost reply', api.get(mock_url, headers=a).status_code == 200)
                    check('Native logout revokes current bearer', api.post('/api/mobile/logout', headers=a).status_code == 200 and api.get('/api/mobile/session', headers=a).status_code == 401)
                    check('Other account survives first logout', api.get('/api/mobile/session', headers=b).json()['id'] == 'stage-b')
                    cookie = authorized['accounts'][1]['parent_cookie']
                    parent_headers = {'Origin': origin, 'Cookie': 'ism_session=' + cookie}
                    check('Browser logout without CSRF is refused', api.post('/api/auth/logout', headers=parent_headers).status_code == 403)
                    parent = api.get('/api/auth/session', headers=parent_headers).json()
                    logged_out = api.post('/api/auth/logout', headers={**parent_headers, 'X-Review-CSRF': parent['csrf']})
                    check('Browser parent logout revokes linked bearer', logged_out.status_code == 200 and api.get('/api/mobile/session', headers=b).status_code == 401)
                    result['attempts'] = conn.execute('SELECT count(*) FROM attempts').fetchone()[0]
                    result['mail_rows'] = conn.execute('SELECT count(*) FROM account_mail_outbox').fetchone()[0]
                    check('No outgoing mail queued', result['mail_rows'] == 0)
                    result['passed'] = True
    finally:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        try:
            next(prepared)
        except StopIteration:
            pass
        result['disposable_database_removed'] = True
        result['loopback_service_stopped'] = process is None or process.poll() is not None
        result['source_sha256'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__).resolve(), ROOT / 'scripts/check-mobile-browser-auth.cjs')}
        (destination / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(f'{len(checks)} live HTTPS/browser checks pass; disposable database and server removed.')


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--serve':
        serve(sys.argv[2])
    else:
        assert len(sys.argv) == 2, 'Expected report directory'
        main(Path(sys.argv[1]).resolve())
