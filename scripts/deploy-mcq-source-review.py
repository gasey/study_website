#!/usr/bin/env python3
"""Deploy only the private pilot-review API, with backup and health rollback."""
from pathlib import Path
import subprocess
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
HOST = 'ubuntu@152.67.31.231'
FILES = ['app/routers/mcq_solver_reviews.py',
         'app/services/mcq_solver_drafts.py',
         'app/services/mcq_solver_source_reviews.py',
         'app/data/mcq-solver-source-review-20261106.json']
STAMP = str(time.time_ns())
STAGE = '/tmp/mcq-source-review-' + STAMP
BACKUP = '/srv/api/.release-backups/mcq-source-review-' + STAMP


def remote(code):
    subprocess.run(['ssh', HOST, 'sudo -n python3 -'], input=code, text=True, check=True)


subprocess.run(['ssh', HOST, 'mkdir', '-p', STAGE], check=True)
with tempfile.TemporaryDirectory() as temporary:
    stage = Path(temporary)
    for relative in FILES:
        target = stage / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / 'api' / relative).read_bytes())
    subprocess.run(['rsync', '-az', str(stage) + '/', HOST + ':' + STAGE + '/'], check=True)

remote(f'''
from pathlib import Path
import json, shutil, subprocess
root, stage, backup = Path('/srv/api'), Path({STAGE!r}), Path({BACKUP!r})
files = {FILES!r} + ['app/main.py']
backup.mkdir(parents=True, mode=0o700)
existing = []
for relative in files:
    src = root / relative
    if src.exists():
        dst = backup / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        existing.append(relative)
(backup / 'existing.json').write_text(json.dumps(existing))
for relative in {FILES!r}:
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(stage / relative, destination)
    destination.chmod(0o644)
main = root / 'app/main.py'
text = main.read_text()
if 'app.include_router(mcq_solver_reviews.router)' not in text:
    main.write_text(text + '\\nfrom .routers import mcq_solver_reviews\\napp.include_router(mcq_solver_reviews.router)\\n')
try:
    subprocess.run([str(root / '.venv/bin/python'), '-c', 'import app.main; assert any(r.path == "/api/admin/mcq-solver/review" for r in app.main.app.routes)'], cwd=root, check=True, stdout=subprocess.DEVNULL)
except Exception:
    for relative in files:
        target = root / relative
        if relative in existing:
            shutil.copy2(backup / relative, target)
        else:
            target.unlink(missing_ok=True)
    raise
subprocess.run(['systemctl', 'restart', 'ism-api'], check=True)
''')
try:
    for attempt in range(15):
        try:
            with urllib.request.urlopen('https://study.hawayu.in/api/health', timeout=5) as result:
                assert result.status == 200
            break
        except Exception:
            if attempt == 14:
                raise
            time.sleep(2)
    with urllib.request.urlopen('https://family.hawayu.in', timeout=15) as result:
        assert result.status == 200
except Exception:
    remote(f'''
from pathlib import Path
import json, shutil, subprocess
root, backup = Path('/srv/api'), Path({BACKUP!r})
existing = json.loads((backup / 'existing.json').read_text())
for relative in {FILES!r} + ['app/main.py']:
    target = root / relative
    if relative in existing:
        shutil.copy2(backup / relative, target)
    else:
        target.unlink(missing_ok=True)
subprocess.run(['systemctl', 'restart', 'ism-api'], check=True)
''')
    raise
print('Private review API healthy; rollback backup:', BACKUP)
