#!/usr/bin/env python3
"""One-time bounded live credential/router install; leaves checkout disabled.

Run as root on Oracle with a private staging directory argument containing
razorpay-live.json, razorpay-live-webhook.json, and billing.py. Never prints keys.
The fixed preimage prevents replay over a later router deployment.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen, Request
from urllib.error import HTTPError


def main():
    assert os.geteuid() == 0, 'Root is required'
    stage = Path(sys.argv[1])
    router = Path('/srv/api/app/routers/billing.py')
    env = Path('/etc/mpsc/db.env')
    assert hashlib.sha256(router.read_bytes()).hexdigest() == '9b1bafef4846e241ed61dfc1a8b710295f7ad6d78b39f804191fcadac2bdd1a2', 'Router preimage changed'
    keys = json.loads((stage/'razorpay-live.json').read_text())
    webhook = json.loads((stage/'razorpay-live-webhook.json').read_text())
    assert keys['mode'] == webhook['mode'] == 'live'
    assert keys['key_id'].startswith('rzp_live_')
    assert webhook['url'] == 'https://study.hawayu.in/api/billing/webhook'
    source = (stage/'billing.py').read_bytes()
    compile(source, str(router), 'exec')
    values = {'RAZORPAY_CHECKOUT_ENABLED': 'false',
              'RAZORPAY_KEY_ID': keys['key_id'],
              'RAZORPAY_KEY_SECRET': keys['key_secret'],
              'RAZORPAY_WEBHOOK_SECRET': webhook['webhook_secret'],
              'PUBLIC_ORIGIN': 'https://study.hawayu.in'}
    assert all('\n' not in v and '\r' not in v for v in values.values())
    lines = [line for line in env.read_text().splitlines()
             if line.split('=', 1)[0].strip() not in values]
    backup = Path(tempfile.mkdtemp(prefix='finna-billing-backup-', dir='/root'))
    shutil.copy2(env, backup/'db.env')
    shutil.copy2(router, backup/'billing.py')
    try:
        env.write_text('\n'.join(lines + [k+'='+v for k,v in values.items()])+'\n')
        env.chmod(0o600)
        router.write_bytes(source)
        subprocess.run(['systemctl','restart','ism-api'], check=True, capture_output=True)
        healthy = False
        for _ in range(20):
            try:
                with urlopen('https://study.hawayu.in/api/health', timeout=5) as r:
                    healthy = json.load(r).get('status') == 'ok'
                if healthy: break
            except Exception:
                pass
            time.sleep(1)
        assert healthy, 'API health did not recover'
        with urlopen('https://study.hawayu.in/api/billing/config', timeout=10) as r:
            assert json.load(r)['enabled'] is False
        try:
            urlopen(Request('https://study.hawayu.in/api/billing/webhook', data=b'{}',
                            headers={'Content-Type':'application/json'}), timeout=10)
            raise AssertionError('Unsigned webhook accepted')
        except HTTPError as exc:
            assert exc.code == 400, 'Webhook secret not active'
        with urlopen('https://family.hawayu.in', timeout=15) as r:
            assert r.status == 200
        print('Live credentials and tested router installed. Checkout remains disabled.')
        print('Root-only rollback directory:', backup)
    except Exception:
        shutil.copy2(backup/'db.env', env)
        shutil.copy2(backup/'billing.py', router)
        subprocess.run(['systemctl','restart','ism-api'], capture_output=True)
        raise RuntimeError('Live install failed; previous environment/router restored') from None
    finally:
        for name in ['razorpay-live.json','razorpay-live-webhook.json']:
            (stage/name).unlink(missing_ok=True)


if __name__ == '__main__':
    main()
