#!/usr/bin/env python3
"""Disposable Android development fixture, reachable only over loopback/ADB.

The signed production-account beta must never point at this fixture. This runner
uses the existing development package with a dedicated Metro server. Stop by
creating the private stop file printed in the public control receipt; timeout
also removes the exact database, server and private credentials.
"""
from pathlib import Path
from uuid import uuid4
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


def serve(config):
    name = config['database']
    assert name.startswith('ism_review_test_') and name.removeprefix('ism_review_test_').isalnum()
    assert config['origin'] == f"http://127.0.0.1:{config['port']}"
    from app import config as app_config
    app_config.settings = app_config.Settings(
        _env_file=None, database_url='postgresql:///' + name + '?options=-c%20role%3Dmpsc',
        public_origin=config['origin'], mobile_redirect_uris=['finna-dev://auth/callback'],
        account_mail_enabled=False, review_digest_enabled=False, referral_rewards_enabled=False,
        razorpay_checkout_enabled=False, pool_min=1, pool_max=6, public_catalog_cache_seconds=0,
        registered_document_root=config['private'] + '/documents',
        canonical_workshop_root=config['private'] + '/bank',
        paper_workbench_root=config['private'] + '/workbench',
        paper_archive_root=config['private'] + '/papers',
    )
    settings = app_config.settings
    assert not any((settings.smtp_host, settings.smtp_username, settings.smtp_password,
                    settings.razorpay_key_id, settings.razorpay_key_secret,
                    settings.razorpay_webhook_secret, settings.google_client_id,
                    settings.google_client_secret, settings.admin_token, settings.mfa_encryption_key))
    from app.main import app
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
    web = ROOT / 'web/dist'
    app.mount('/assets', StaticFiles(directory=web / 'assets'), name='fixture-assets')

    @app.get('/{path:path}')
    async def web_fallback(path: str):
        from fastapi import HTTPException
        if path.startswith('api/'):
            raise HTTPException(404)
        return FileResponse(web / 'index.html')

    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=config['port'], access_log=False, log_level='warning')


def main(report):
    import conftest
    import httpx
    from app.routers.auth import _hash_password
    from test_study_sessions import seed
    report.mkdir(exist_ok=True, parents=True)
    prepared = conftest.fresh_database()
    database = next(prepared)
    name, conn = database
    process = None
    receipt = {'synthetic_only': True, 'production_access': False, 'questions': 1000,
               'release_https_acceptance': False, 'transport': 'ADB loopback HTTP development only'}
    try:
        with tempfile.TemporaryDirectory(prefix='finna-android-fixture-') as temporary:
            private = Path(temporary)
            password = 'Synthetic-' + secrets.token_hex(12) + '1'
            for user in ('android-stage-a', 'android-stage-b'):
                conn.execute("INSERT INTO users(id,handle,email,password_hash,email_verified_at,plan_code,plan_status,plan_ends_at) VALUES(%s,%s,%s,%s,now(),'pro','active',now()+interval '1 day')",
                             (user, user, user + '@example.test', _hash_password(password)))
            paper, ids = seed(database, 1000)
            conn.execute('ANALYZE canonical_questions')
            conn.execute('ANALYZE appearances')
            with socket.socket() as listener:
                listener.bind(('127.0.0.1', 0))
                port = listener.getsockname()[1]
            config = {'database': name, 'port': port, 'origin': f'http://127.0.0.1:{port}',
                      'private': temporary, 'paper': paper}
            config_path = private / 'config.json'
            config_path.write_text(json.dumps(config))
            credentials = private / 'accounts.json'
            credentials.write_text(json.dumps({'password': password, 'users': ['android-stage-a', 'android-stage-b']}))
            credentials.chmod(0o600)
            stop = private / 'stop'
            environment = {k: v for k, v in os.environ.items() if k in ('PATH', 'HOME', 'USER', 'LANG', 'LD_LIBRARY_PATH')}
            with (report / 'fixture-server.log').open('w') as log:
                process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--serve', str(config_path)],
                                           cwd=private, env=environment, stdout=log, stderr=log)
                with httpx.Client(base_url=config['origin'], trust_env=False, timeout=30) as api:
                    for _ in range(150):
                        if process.poll() is not None:
                            raise RuntimeError('Fixture server failed; inspect its local log')
                        try:
                            if api.get('/api/health').status_code == 200:
                                break
                        except httpx.TransportError:
                            pass
                        time.sleep(.1)
                    else:
                        raise RuntimeError('Fixture server readiness timed out')
                    found = []
                    for offset in range(0, 1000, 100):
                        page = api.get('/api/questions', params={'paper_id': paper, 'limit': 100, 'offset': offset, 'order': 'paper', 'origin': 'paper', 'pool': 'all'})
                        assert page.status_code == 200, page.text
                        body = page.json()
                        assert body['total'] == 1000
                        found.extend(item['id'] for item in body['items'])
                    assert len(found) == len(set(found)) == 1000 and set(found) == set(ids)
                    receipt['pagination_1000_unique_verified'] = True
                control = {**config, 'credentials_file': str(credentials), 'stop_file': str(stop),
                           'development_package': 'in.hawayu.finna.dev', 'expires_after_minutes': 25}
                (report / 'fixture-control.json').write_text(json.dumps(control, indent=2) + '\n')
                print(json.dumps({'ready': True, 'origin': config['origin'], 'questions': 1000,
                                  'control_receipt': str(report / 'fixture-control.json')}), flush=True)
                deadline = time.monotonic() + 25 * 60
                while not stop.exists() and time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError('Fixture server stopped unexpectedly')
                    time.sleep(.25)
                receipt['attempts'] = conn.execute('SELECT count(*) FROM attempts').fetchone()[0]
                receipt['mail_rows'] = conn.execute('SELECT count(*) FROM account_mail_outbox').fetchone()[0]
                assert receipt['mail_rows'] == 0
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
        receipt['database_removed'] = True
        receipt['server_stopped'] = process is None or process.poll() is not None
        receipt['private_credentials_removed'] = True
        (report / 'fixture-validation.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('Exact Android fixture database/server/private credentials removed.', flush=True)


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--serve':
        serve(json.loads(Path(sys.argv[2]).read_text()))
    else:
        assert len(sys.argv) == 2, 'Expected report directory'
        main(Path(sys.argv[1]).resolve())
