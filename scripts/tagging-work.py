#!/usr/bin/env python3
"""Shared tagging coordination for Codex, Antigravity, OpenCode and manual workers.

All tools connect to the same Oracle queue. This never invokes a model or publisher.
"""
import argparse
import importlib.util
import json
import os
import re
import secrets
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOTE = 'sudo -u postgres /srv/api/.venv/bin/python /opt/ism-tagging-coordination/tagging_queue_server.py'


def write(path, data, exclusive=False):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if exclusive:
        with path.open('x') as f:
            os.chmod(path, 0o600)
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')
        return
    fd, tmp = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def remote(request):
    r = subprocess.run(['ssh', '-o', 'BatchMode=yes', 'ubuntu@152.67.31.231', REMOTE],
                       input=json.dumps(request), text=True, capture_output=True, timeout=240)
    if r.returncode:
        raise ValueError('Central queue request failed; do not create a local replacement queue. ' +
                         (r.stdout or r.stderr)[-1800:])
    result = json.loads(r.stdout)
    if 'error' in result:
        raise ValueError(result['error'])
    return result


def sync():
    spec = importlib.util.spec_from_file_location('coverage', ROOT / 'scripts/audit-review-coverage.py')
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    data = audit.audit(ROOT, ROOT / 'reports/booklet-card-cleanup-20261107/resolutions.json',
                       ROOT / 'reports/baseline-corrections-20261108/corrections.json')
    # Even invalid/conflicting historical rows are excluded from new work. Repair them explicitly.
    frozen_path = ROOT / 'reports/owner-taxonomy-publication-20261108/frozen.json'
    results_path = frozen_path.with_name('results.json')
    if not frozen_path.exists() or not results_path.exists():
        if not remote({'command': 'status'}).get('inventory'):
            raise ValueError('Initial setup requires existing publication ledger/reports; do not start over')
        frozen = []
        outcomes = {}
        reasons = {}
    else:
        frozen = json.loads(frozen_path.read_text())['items']
        outcomes = {r['detail']['appearance_id']: r['detail']['status']
                    for r in json.loads(results_path.read_text())}
        reasons = {r['detail']['appearance_id']: r['detail'].get('reason', '')
                   for r in json.loads(results_path.read_text())}
    frozen_ids = {i['candidate']['appearance_id'] for i in frozen}
    followups = []
    for i in frozen:
        c = i['candidate']
        if outcomes.get(c['appearance_id']) == 'blocked':
            followups.append({'canonical_id': c['canonical_id'], 'appearance_id': c['appearance_id'],
                              'kind': 'blocked', 'blocker_reason': reasons.get(c['appearance_id'], ''),
                              'candidate': c, 'candidate_file': i['candidate_file']})
    legacy_files = {}
    for f in data['files']:
        if not f['file'].startswith('reports/tagging-shared-'):
            for row in json.loads((ROOT / f['file']).read_text()):
                legacy_files.setdefault(row['appearance_id'], f['file'])
    for c in data['effective_candidates']:
        if c['appearance_id'] not in frozen_ids:
            # Shared submissions already live centrally; do not import them as another follow-up.
            found = legacy_files.get(c['appearance_id'])
            if found:
                followups.append({'canonical_id': c['canonical_id'], 'appearance_id': c['appearance_id'],
                                  'kind': 'saved_outside_frozen_run', 'candidate': c, 'candidate_file': found})
    return remote({'command': 'sync', 'exclusions': {
        'canonical': data['already_reviewed_canonical_ids'],
        'appearance': data['already_reviewed_appearance_ids']}, 'followups': followups})


def main():
    os.umask(0o077)
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('sync')
    sub.add_parser('status')
    claim = sub.add_parser('claim')
    claim.add_argument('--worker', required=True, help='Unique operator/session label, e.g. antigravity-01')
    claim.add_argument('--model', required=True, help='Actual model identity; do not guess')
    claim.add_argument('--lane', choices=['new', 'followup'], default='followup')
    claim.add_argument('--size', type=int, default=50)
    for name in ('resume', 'save', 'submit', 'release'):
        cmd = sub.add_parser(name)
        cmd.add_argument('--worker', required=True)
        if name in ('save', 'submit'):
            cmd.add_argument('--file', type=Path, required=True)
        if name == 'release':
            cmd.add_argument('--reason', required=True)
            cmd.add_argument('--defer', action='store_true', help='Keep inaccessible work out of normal claims')
    a = p.parse_args()
    if a.command == 'sync':
        result = sync()
    elif a.command == 'status':
        result = remote({'command': 'status'})
    else:
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', a.worker):
            p.error('Use a 1–64 character worker label with letters, digits, underscores or hyphens')
        session_file = ROOT / 'state/tagging-coordination' / (a.worker + '.json')
        if a.command == 'claim':
            if session_file.exists():
                raise ValueError('A local session exists. Resume it before claiming another packet.')
            sync()
            if not 1 <= a.size <= 100:
                p.error('Packet size must be 1–100')
            session = {'packet_id': 'tq_' + secrets.token_hex(12), 'token': secrets.token_urlsafe(32),
                       'claim': {'worker': a.worker, 'model': a.model, 'lane': a.lane, 'size': a.size}}
            write(session_file, session, exclusive=True)
            result = remote({'command': 'claim', **session['claim'],
                             'packet_id': session['packet_id'], 'token': session['token']})
            if result.get('empty'):
                session_file.unlink()
            if not result.get('empty'):
                packet = result['packet']
                result.pop('token')
                folder = ROOT / 'reports' / ('tagging-shared-' + packet['packet_id'])
                write(folder / 'oracle-packet.json', packet)
                result = {'packet_id': packet['packet_id'], 'targets': len(packet['items']),
                          'lane': a.lane, 'packet_file': str(folder / 'oracle-packet.json'),
                          'next': 'Inspect sources; save drafts centrally; submit pending candidates.'}
        else:
            session = json.loads(session_file.read_text())
            folder = ROOT / 'reports' / ('tagging-shared-' + session['packet_id'])
            if a.command == 'resume':
                # Reconcile a lost claim response without making a second reservation.
                recovered = remote({'command': 'claim', **session['claim'],
                                    'packet_id': session['packet_id'], 'token': session['token']})
                if recovered.get('empty'):
                    session_file.unlink()
                    print(json.dumps(recovered))
                    return
            request = {'command': a.command, 'packet_id': session['packet_id'], 'token': session['token']}
            if a.command in ('save', 'submit'):
                data = json.loads(a.file.read_text())
                request['draft' if a.command == 'save' else 'candidates'] = data
            if a.command == 'release':
                request.update(reason=a.reason, defer=a.defer)
            result = remote(request)
            if a.command == 'resume':
                write(folder / 'oracle-packet.json', result['packet'])
                if result.get('draft') is not None:
                    write(folder / 'resumed-draft.json', result['draft'])
                if result.get('result') is not None:
                    write(folder / 'pending-candidates.json', result['result'])
                result = {'packet_id': session['packet_id'], 'state': result['state'],
                          'packet_file': str(folder / 'oracle-packet.json'),
                          'draft_recovered': result.get('draft') is not None,
                          'result_recovered': result.get('result') is not None}
            if a.command == 'submit':
                write(folder / 'pending-candidates.json', data)
                write(folder / 'submission-receipt.json', result)
            if a.command in ('submit', 'release') or (a.command == 'resume' and result['state'] != 'claimed'):
                write(ROOT / 'state/tagging-coordination/archive' / (session['packet_id'] + '.json'), session)
                session_file.unlink()
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc))
