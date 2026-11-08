#!/usr/bin/env python3
"""One-time baseline of existing UDC/Prelims content; does not mark it verified."""
import json
import subprocess
import shlex
from datetime import datetime, timezone
from editorial_protection import CANONICAL, POLICY, atomic, configuration, file_hash, remote_scope, snapshot
from review_bank_store import bank_lock

def main():
    import os
    with bank_lock(CANONICAL):
        _, path = configuration(CANONICAL, POLICY)
        if path.exists() or path.with_suffix('.pending.json').exists():
            raise ValueError('Protection is already initialized; automatic rebaselining is forbidden')
        scopes = remote_scope(os.environ.get('ISM_HOST', 'ubuntu@152.67.31.231'),
                              os.environ.get('ISM_DB', 'mpsc'), ['udc', 'combined-prelims'])
        if set(scopes) != {'udc', 'combined-prelims'} or any(not s['paper_ids'] for s in scopes.values()):
            raise ValueError('Both live collections must have source papers')
        bank = json.loads(CANONICAL.read_text())
        cmd = 'sudo -u postgres psql -X -qAt -v ON_ERROR_STOP=1 -d ' + shlex.quote(os.environ.get('ISM_DB', 'mpsc'))
        result = subprocess.run(['ssh', '-o', 'ConnectTimeout=10', os.environ.get('ISM_HOST', 'ubuntu@152.67.31.231'), cmd],
                                input='SELECT bank_checksum FROM sync_log WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1;',
                                text=True, capture_output=True, check=True, timeout=40)
        if result.stdout.strip() != file_hash(CANONICAL):
            raise ValueError('Reconcile local/server bank before enabling protection')
        pids = {p for s in scopes.values() for p in s['paper_ids']}
        state = {'schema': 1, 'created_at': datetime.now(timezone.utc).isoformat(),
                 'baseline_bank_sha256': file_hash(CANONICAL), 'scopes': scopes,
                 'expected': snapshot(bank, pids, CANONICAL.parents[1]),
                 'last_publications': [],
                 'note': 'Integrity baseline only, not human factual sign-off.'}
        atomic(path, state)
        atomic(path.with_name('initial-baseline.json'), state)
        print(json.dumps({'papers': len(pids), 'questions': len(state['expected']['questions']),
                          'assets': len(state['expected']['assets']), 'scopes': {k: len(s['paper_ids']) for k,s in scopes.items()}}))

if __name__ == '__main__': main()
