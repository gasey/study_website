"""Protect handed-off source records against unreviewed parser/merge changes.

This is an integrity boundary for the supported publication/import/sync tools,
not a security boundary against an operator with filesystem/root access.
Publication authorization is called only after the existing manifest validator.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import fcntl
from contextlib import nullcontext, contextmanager

APP = Path(__file__).resolve().parents[1]
POLICY = APP / 'scripts/editorial-protection-policy.json'
CANONICAL = APP.parent / 'mpsc-question-bankv2/bank/mpsc_bank_v2.json'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()


def file_hash(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.protection-')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(value, f, indent=2, ensure_ascii=False)
            f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(name, path)
        fd = os.open(path.parent, os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)
    finally:
        if os.path.exists(name): os.unlink(name)


def configuration(bank_path, policy_path=None):
    # Synthetic fixture banks remain independent. Sync passes the policy
    # explicitly, so an alternate ISM_BANK cannot bypass production protection.
    if policy_path is None and Path(bank_path).resolve() != CANONICAL.resolve():
        return None
    policy_path = Path(policy_path or POLICY)
    if not policy_path.is_file():
        raise ValueError('Editorial protection policy is missing')
    policy = json.loads(policy_path.read_text())
    if policy.get('schema') != 1 or policy.get('required') is not True:
        raise ValueError('Invalid editorial protection policy')
    state = (policy_path.parent / policy['state']).resolve()
    return policy, state


def indexed(rows, name):
    result = {}
    for row in rows:
        key = row['id']
        if key in result:
            raise ValueError(f'Duplicate {name} ID: {key}')
        result[key] = row
    return result


def asset(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Protected asset escapes the bank workspace')
    return file_hash(path) if path.is_file() else None


def snapshot(bank, paper_ids, root):
    root = Path(root)
    papers = indexed(bank['papers'], 'paper')
    all_questions = indexed(bank['questions'], 'question')
    absent = set(paper_ids) - papers.keys()
    if absent:
        raise ValueError('Protected papers removed: ' + ', '.join(sorted(absent)[:3]))
    qs = {k: q for k, q in all_questions.items() if q['paperId'] in paper_ids}
    result = {'questions': {k: digest(v) for k, v in qs.items()},
              'papers': {k: digest(papers[k]) for k in paper_ids},
              'sittings': {}, 'figureGroups': {}, 'passageGroups': {}, 'assets': {}}
    for pid in paper_ids:
        p = papers[pid]
        sid = p.get('sittingId')
        if sid:
            result['sittings'][sid] = digest(bank.get('sittings', {}).get(sid))
        source = p.get('pdfPath') or ('pdfs/' + p['sourceFile'] if p.get('sourceFile') else None)
        if source:
            result['assets'][source] = asset(root, source)
    for q in qs.values():
        for field, group in [('figureGroupId', 'figureGroups'), ('passageId', 'passageGroups')]:
            key = q.get(field)
            if key:
                result[group][key] = digest(bank.get(group, {}).get(key))
        if q.get('figureImage'):
            result['assets'][q['figureImage']] = asset(root, q['figureImage'])
    return result


def differences(before, after):
    return {kind: sorted(k for k in set(before.get(kind, {})) | set(after.get(kind, {}))
                         if before.get(kind, {}).get(k, 'ABSENT') != after.get(kind, {}).get(k, 'ABSENT'))
            for kind in set(before) | set(after)
            if before.get(kind, {}) != after.get(kind, {})}


def load_state(state_path):
    if not state_path.is_file():
        raise ValueError('Required editorial protection baseline is missing; do not sync')
    state = json.loads(state_path.read_text())
    if state.get('schema') != 1 or not state.get('scopes') or not state.get('expected'):
        raise ValueError('Invalid editorial protection baseline')
    return state


def effective_state(state_path, bank, root):
    state = load_state(state_path)
    paper_ids = {p for scope in state['scopes'].values() for p in scope['paper_ids']}
    current = snapshot(bank, paper_ids, root)
    pending_path = state_path.with_suffix('.pending.json')
    if current == state['expected']:
        return state
    if pending_path.is_file():
        pending = json.loads(pending_path.read_text())
        if (pending.get('schema') == 1 and pending.get('before_state') == digest(state)
                and pending.get('next_state', {}).get('scopes') == state['scopes']
                and pending['next_state']['expected'] == current):
            return pending['next_state']
    diff = differences(state['expected'], current)
    counts = ', '.join(f'{kind}: {len(ids)}' for kind, ids in sorted(diff.items()))
    raise ValueError('Unreviewed changes to handed-off content (' + counts +
                     '). Keep AI output in staging and submit corrections through review.')


def check_candidate(bank_path, candidate=None, policy_path=None):
    config = configuration(bank_path, policy_path)
    if not config:
        return None
    _, state_path = config
    bank_path = Path(bank_path)
    bank = json.loads(bank_path.read_text())
    state = effective_state(state_path, bank, bank_path.parents[1])
    if candidate is not None:
        pids = {p for scope in state['scopes'].values() for p in scope['paper_ids']}
        changed = differences(state['expected'], snapshot(candidate, pids, bank_path.parents[1]))
        if changed:
            raise ValueError('AI/import would alter protected UDC/Prelims content; stage a proposal instead')
    return state


def guard_import(bank_path, candidate):
    """Legacy writer hook: reject changes and retain a draft for human comparison."""
    from bank_authority import require_writable
    require_writable(bank_path)
    try:
        return check_candidate(bank_path, candidate)
    except ValueError as exc:
        from datetime import datetime, timezone
        from uuid import uuid4
        bank_path = Path(bank_path)
        before = json.loads(bank_path.read_text())
        old, new = indexed(before['questions'], 'question'), indexed(candidate['questions'], 'question')
        changes = [{'appearance_id': key, 'before_sha256': digest(old[key]) if key in old else None,
                    'before': old.get(key), 'proposed': new.get(key)}
                   for key in sorted(set(old) | set(new)) if old.get(key) != new.get(key)]
        out = bank_path.parents[1] / 'state/parser-drafts' / (uuid4().hex + '.json')
        atomic(out, {'schema': 1, 'status': 'draft-only', 'created_at': datetime.now(timezone.utc).isoformat(),
                     'bank_sha256': file_hash(bank_path), 'reason': str(exc), 'changes': changes,
                     'proposed_papers': candidate.get('papers', []),
                     'note': 'Not published or verified. Recheck each source and current baseline.'})
        raise ValueError(f'{exc}. Draft saved to {out}') from exc


@contextmanager
def write_lock(path):
    with open(str(path) + '.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def write_guarded(bank_path, candidate, locked=False):
    """Validate and replace under the same lock as the publication worker."""
    with (nullcontext() if locked else write_lock(bank_path)):
        guard_import(bank_path, candidate)
        atomic(bank_path, candidate)


def prepare_publication(bank_path, before, after, manifests, policy_path=None):
    """Journal a bounded transition AFTER ordinary manifest/evidence validation.

    Called while the common bank lock is held, before replacing the bank.
    Existing prepared receipts remain the recovery authority for bank writes.
    """
    from bank_authority import require_writable
    require_writable(bank_path)
    config = configuration(bank_path, policy_path)
    if not config:
        return
    _, path = config
    root = Path(bank_path).parents[1]
    state = effective_state(path, before, root)
    pids = {p for scope in state['scopes'].values() for p in scope['paper_ids']}
    desired = snapshot(after, pids, root)
    diff = differences(state['expected'], desired)
    allowed = set()
    for m in manifests:
        if m['payload']['kind'] == 'new_question':
            allowed.add('community_' + m['contribution_id'].removeprefix('con_'))
        elif m['payload']['kind'] not in {'duplicate', 'source_request'}:
            allowed.add(m['baseline']['record']['id'])
    if any(kind not in {'questions', 'assets'} for kind in diff):
        raise ValueError('Publication cannot rewrite protected paper/group metadata')
    if set(diff.get('questions', [])) - allowed:
        raise ValueError('Publication changes an unreviewed protected target')
    # Existing assets are immutable. Source corrections use a new image path.
    for name in diff.get('assets', []):
        if name in state['expected']['assets'] and name in desired['assets']:
            raise ValueError('Existing protected assets cannot be replaced in place')
    if not diff:
        return
    next_state = copy.deepcopy(state)
    next_state['expected'] = desired
    next_state['last_publications'] = [{'id': m['id'], 'manifest_sha256': digest(m)} for m in manifests]
    pending = {'schema': 1, 'before_state': digest(state), 'next_state': next_state}
    # A prior completed transition may still be present after a crash. Persist
    # its exact state first; never adopt whatever the current bank happens to be.
    if digest(load_state(path)) != digest(state):
        atomic(path, state)
    atomic(path.with_suffix('.pending.json'), pending)


def finish_publication(bank_path, policy_path=None):
    config = configuration(bank_path, policy_path)
    if not config:
        return
    _, path = config
    bank = json.loads(Path(bank_path).read_text())
    state = effective_state(path, bank, Path(bank_path).parents[1])
    if digest(load_state(path)) != digest(state):
        atomic(path, state)
    pending = path.with_suffix('.pending.json')
    if pending.exists():
        pending.unlink()


def remote_scope(host, db, scopes):
    ids = ','.join("'" + s.replace("'", "''") + "'" for s in scopes)
    sql = """SELECT json_object_agg(id,item) FROM (SELECT c.id,
      json_build_object('version',c.live_version,'paper_ids',
        coalesce(json_agg(cp.paper_id ORDER BY cp.paper_id) FILTER(WHERE cp.paper_id IS NOT NULL),'[]')) AS item
      FROM collections c LEFT JOIN collection_papers cp ON cp.collection_id=c.id
        AND cp.version=c.live_version AND cp.allow_browse
      WHERE c.id IN (""" + ids + ') GROUP BY c.id,c.live_version) x;'
    command = 'sudo -u postgres psql -X -qAt -v ON_ERROR_STOP=1 -d ' + shlex.quote(db)
    transport=['sudo','-u','postgres','psql','-X','-qAt','-v','ON_ERROR_STOP=1','-d',db] if os.environ.get('ISM_DB_TRANSPORT')=='local' else ['ssh', '-o', 'ConnectTimeout=10', host, command]
    result = subprocess.run(transport,
                            input=sql, text=True, capture_output=True, check=True, timeout=40)
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['check', 'stage'])
    parser.add_argument('--bank', type=Path, required=True)
    parser.add_argument('--policy', type=Path, default=POLICY)
    parser.add_argument('--candidate', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--remote-scope', action='store_true')
    args = parser.parse_args()
    state = check_candidate(args.bank, policy_path=args.policy)
    if args.remote_scope and remote_scope(os.environ.get('ISM_HOST', 'ubuntu@152.67.31.231'),
                                         os.environ.get('ISM_DB', 'mpsc'), state['scopes']) != state['scopes']:
        raise ValueError('UDC/Prelims source membership changed; review and extend the protection scope explicitly')
    if args.mode == 'stage':
        if not args.candidate or not args.output:
            parser.error('stage requires --candidate and --output')
        if args.output.resolve() in {args.bank.resolve(), args.policy.resolve(), configuration(args.bank, args.policy)[1]}:
            raise ValueError('Draft output cannot replace bank or protection state')
        bank = json.loads(args.bank.read_text())
        candidate = json.loads(args.candidate.read_text())
        old, new = indexed(bank['questions'], 'question'), indexed(candidate['questions'], 'question')
        changes = [{'appearance_id': qid, 'before_sha256': digest(old[qid]) if qid in old else None,
                    'before': old.get(qid), 'proposed': new.get(qid)}
                   for qid in sorted(set(old) | set(new)) if old.get(qid) != new.get(qid)]
        atomic(args.output, {'schema': 1, 'status': 'draft-only', 'bank_sha256': file_hash(args.bank),
                             'candidate_sha256': file_hash(args.candidate), 'changes': changes,
                             'paper_changes': differences({'papers': {p['id']: digest(p) for p in bank['papers']}},
                                                          {'papers': {p['id']: digest(p) for p in candidate['papers']}})})
        print(f'Staged {len(changes)} question changes; no bank data or review status changed')
    else:
        print(f"Editorial protection OK: {len(state['expected']['papers'])} papers / "
              f"{len(state['expected']['questions'])} source questions")


if __name__ == '__main__':
    main()
