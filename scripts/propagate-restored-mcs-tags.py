#!/usr/bin/env python3
"""Reuse approved tags for exact restored copies; never infer topics or answers.

This is the bank workshop's conservative exact-signature rule, bounded to the
explicit recent-restoration manifest. It does not create community approvals.
"""
import argparse
import copy
import fcntl
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from editorial_protection import write_guarded

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT.parent / 'mpsc-question-bankv2/bank/mpsc_bank_v2.json'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()


def signature(q):
    options = q.get('options') or []
    if (q.get('type') != 'mcq' or not isinstance(q.get('question'), str)
            or not q['question'].strip() or not 2 <= len(options) <= 8
            or any(not isinstance(v, str) or not v.strip() for v in options)):
        return None
    normalize = lambda text: re.sub(r'\s+', ' ', text).strip().lower()
    return normalize(q['question']), tuple(normalize(v) for v in options)


def candidates(bank, targets):
    sources = defaultdict(list)
    for q in bank['questions']:
        claims = [c for c in q.get('classifications', []) if c.get('is_primary')]
        sig = signature(q)
        if (q['id'] not in targets and sig and not q.get('sourceDefect')
                and len(claims) == 1 and claims[0].get('review_status') == 'approved'):
            sources[sig].append((q, claims[0]))
    result = []; skipped = Counter()
    for q in bank['questions']:
        if q['id'] not in targets:
            continue
        if q.get('classifications') or q.get('sourceDefect'):
            skipped['already_classified_or_source_issue'] += 1; continue
        matches = sources.get(signature(q), [])
        paths = {tuple(c.get(k) for k in ('subject_id', 'topic_id', 'subtopic_id')) for _, c in matches}
        if len(paths) != 1:
            skipped['conflicting_sources' if paths else 'no_exact_match'] += 1; continue
        if not next(iter(paths))[0]:
            skipped['invalid_source_path'] += 1; continue
        matches = sorted(matches, key=lambda pair: pair[0]['id'])
        source, claim = matches[0]
        classification = {k: claim.get(k) for k in ('subject_id', 'topic_id', 'subtopic_id', 'taxonomy_version')}
        classification.update(is_primary=True, review_status='approved', source='exact-signature-propagated',
            evidence='Reused existing approved path from exact normalized stem and full ordered options: ' +
                     ', '.join(q['id'] for q, _ in matches) + '. No answer transferred; not an independent content review.')
        result.append({'id': q['id'], 'baseline_sha256': digest(q), 'classification': classification,
                       'source_ids': [s['id'] for s, _ in matches],
                       'source_hashes': {s['id']: digest(s) for s, _ in matches}})
    return {'candidates': result, 'skipped': dict(skipped)}


def run(manifest_path, output, apply=False):
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(manifest_path.read_text())
    targets = {(p['paper_id'], n) for p in manifest['papers'] for n in p['missing_question_numbers']}
    if len(targets) != 480:
        raise ValueError('Use the exact 480-question restoration scope')
    for paper in manifest['papers']:
        pdf = BANK.parents[1] / 'pdfs' / paper['paper_id']
        if hashlib.sha256(pdf.read_bytes()).hexdigest() != paper['sha256']:
            raise ValueError('Source PDF changed')
    with open(str(BANK) + '.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        before = BANK.read_bytes(); bank = json.loads(before)
        qs = [q for q in bank['questions'] if (q['paperId'], q.get('qnum')) in targets]
        if len(qs) != 480 or any(q.get('origin', {}).get('kind') != 'restored-original-paper' for q in qs):
            raise ValueError('Target source records differ from the restoration')
        plan = candidates(bank, {q['id'] for q in qs})
        report = {'bank_sha256': hashlib.sha256(before).hexdigest(), 'applied': apply, **plan}
        if apply:
            if not plan['candidates']:
                raise ValueError('No new targets; do not replay publication')
            changes = {q['id']: q for q in plan['candidates']}
            (output / 'bank-before.json').write_bytes(before)
            for q in bank['questions']:
                if q['id'] in changes:
                    q['classifications'] = [changes[q['id']]['classification']]
            # A complete diff proves that all text, answers, metadata and all
            # unselected question records remain byte-value equivalent.
            previous = json.loads(before)
            for old, new in zip(previous['questions'], bank['questions']):
                expected = copy.deepcopy(old)
                if old['id'] in changes:
                    expected['classifications'] = [changes[old['id']]['classification']]
                if new != expected:
                    raise ValueError('Unexpected bank field changed')
            temp = BANK.with_suffix('.tags.tmp')
            with open(temp, 'w') as stream:
                json.dump(bank, stream, ensure_ascii=False, indent=2); stream.write('\n')
                stream.flush(); os.fsync(stream.fileno())
            write_guarded(BANK, bank, locked=True)
            temp.unlink(missing_ok=True)
            report['after_sha256'] = hashlib.sha256(BANK.read_bytes()).hexdigest()
        (output / ('receipt.json' if apply else 'preview.json')).write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'tagged': len(plan['candidates']), 'skipped': plan['skipped'], 'applied': apply}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(); run(args.manifest, args.output, args.apply)
