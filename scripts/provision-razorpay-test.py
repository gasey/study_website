#!/usr/bin/env python3
"""Run once as root on Oracle; credentials arrive separately in a 0600 file.

Copies schema only, never live users or content. Production code/config are not
modified. A separate imported Caddy snippet exposes only the signed webhook.
"""
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time
from urllib.request import urlopen
from urllib.parse import urlparse

ROOT = Path('/srv/finna-razorpay-test')
ENV = Path('/etc/finna-razorpay-test.env')
SITE = Path('/etc/caddy/sites/finna-test.caddy')
UNIT = Path('/etc/systemd/system/finna-razorpay-test.service')


def run(args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, **kwargs)


def sql(database, statement):
    return run(['sudo', '-u', 'postgres', 'psql', '-X', '-v', 'ON_ERROR_STOP=1', '-d', database], input=statement.encode())


def main():
    if os.geteuid() != 0 or len(sys.argv) != 2:
        raise SystemExit('Run as root with the private credential JSON path')
    if any(p.exists() for p in (ROOT, ENV, SITE, UNIT)):
        raise SystemExit('Existing test service found; inspect it instead of overwriting')
    credentials = json.loads(Path(sys.argv[1]).read_text())
    if not credentials['key_id'].startswith('rzp_test_'):
        raise SystemExit('Only test keys are accepted')
    imports = Path('/etc/caddy/Caddyfile').read_text()
    if 'import /etc/caddy/sites/*.caddy' not in imports:
        raise SystemExit('Expected Caddy snippets import not found')
    pid = run(['systemctl', 'show', 'ism-api', '--property=MainPID', '--value']).stdout.decode().strip()
    live_env = dict(entry.split(b'=', 1) for entry in Path('/proc/' + pid + '/environ').read_bytes().split(b'\0') if b'=' in entry)
    live_db = urlparse(live_env[b'DATABASE_URL'].decode()).path.lstrip('/')
    if not live_db or live_db == 'finna_paytest':
        raise SystemExit('Could not identify the live schema source')
    schema = run(['sudo', '-u', 'postgres', 'pg_dump', '--schema-only', '--no-owner', '--no-privileges', '-d', live_db]).stdout
    if b'CREATE FOREIGN TABLE' in schema or b'CREATE SERVER' in schema:
        raise SystemExit('Foreign database objects require separate inspection')
    db_password, webhook_secret, session = (secrets.token_hex(32) for _ in range(3))
    sql('postgres', "CREATE ROLE finna_paytest LOGIN PASSWORD '" + db_password + "';\nCREATE DATABASE finna_paytest OWNER finna_paytest;\n")
    sql('finna_paytest', schema.decode())
    sql('finna_paytest', "GRANT USAGE ON SCHEMA public TO finna_paytest; GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO finna_paytest; GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO finna_paytest;")
    token_hash = hashlib.sha256(session.encode()).hexdigest()
    sql('finna_paytest', "INSERT INTO users(id,handle,email,role,plan_code,plan_status) VALUES('finna_razorpay_test','finna-test','finna-test@example.com','learner','free','free'); INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES('" + token_hash + "','finna_razorpay_test',now()+interval '7 days');")
    ROOT.mkdir(mode=0o755)
    shutil.copytree('/srv/api/app', ROOT / 'app', ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'data'))
    for name in ('razorpay-test-app.py', 'razorpay-test.html'):
        destination = ROOT / (name.replace('-', '_') if name.endswith('.py') else name)
        shutil.copyfile(Path(__file__).with_name(name), destination)
        destination.chmod(0o644)
    values = {
        'DATABASE_URL': 'postgresql://finna_paytest:' + db_password + '@127.0.0.1/finna_paytest',
        'PUBLIC_ORIGIN': 'http://127.0.0.1:8011',
        'POOL_MIN': '1', 'POOL_MAX': '3',
        'RAZORPAY_CHECKOUT_ENABLED': 'true',
        'RAZORPAY_KEY_ID': credentials['key_id'],
        'RAZORPAY_KEY_SECRET': credentials['key_secret'],
        'RAZORPAY_WEBHOOK_SECRET': webhook_secret,
        'FINNA_TEST_SESSION': session,
    }
    fd = os.open(ENV, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as f:
        f.write(''.join(k + '=' + v + '\n' for k, v in values.items()))
    # Dedicated nologin Unix account; no production environment files are loaded.
    run(['useradd', '--system', '--no-create-home', '--shell', '/usr/sbin/nologin', 'finna-paytest'])
    UNIT.write_text('''[Unit]
Description=Finna isolated Razorpay TEST billing only
After=network.target postgresql.service
[Service]
User=finna-paytest
Group=finna-paytest
WorkingDirectory=/srv/finna-razorpay-test
EnvironmentFile=/etc/finna-razorpay-test.env
ExecStart=/srv/api/.venv/bin/uvicorn razorpay_test_app:app --host 127.0.0.1 --port 8011 --no-access-log
Restart=on-failure
RestartSec=3
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadOnlyPaths=/srv/finna-razorpay-test
[Install]
WantedBy=multi-user.target
''')
    UNIT.chmod(0o644)
    run(['systemctl', 'daemon-reload'])
    run(['systemctl', 'start', 'finna-razorpay-test'])
    for attempt in range(10):
        try:
            with urlopen('http://127.0.0.1:8011/api/health', timeout=2) as response:
                health = json.load(response)
            if health.get('isolated_database') is True and health.get('test_mode') is True:
                break
        except Exception:
            if attempt == 9:
                raise RuntimeError('The isolated API did not become healthy') from None
            time.sleep(1)
    else:
        raise RuntimeError('The isolated API failed its isolation check')
    print('Isolated billing service installed on 127.0.0.1:8011; no production environment changed.')
    SITE.write_text('''finna-test.hawayu.in {
    handle /api/billing/webhook {
        reverse_proxy 127.0.0.1:8011
    }
    handle {
        respond "Private Finna payment test endpoint" 404
    }
}
''')
    SITE.chmod(0o644)
    try:
        run(['caddy', 'validate', '--config', '/etc/caddy/Caddyfile'])
        run(['systemctl', 'reload', 'caddy'])
    except Exception:
        SITE.unlink(missing_ok=True)
        raise
    print('Separate Caddy snippet installed; only the signed webhook is public.')


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as error:
        # Database/provider diagnostics may contain credentials: never echo them.
        print('Provisioning step failed, exit code ' + str(error.returncode), file=sys.stderr)
        raise SystemExit(1)
