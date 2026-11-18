#!/usr/bin/env python3
"""Build per-question re-tag candidate batches from worker output (read-only; pending only).

Input : reports/retag-work-20261109/out/chunk_NNN.json  (worker decisions)
        reports/quarantine-templated-20261109/*/oracle-packet.json (fingerprints, taxonomy, snapshots)
Output: reports/tagging-retag-<batch>-20261109/{pending-candidates.json,oracle-packet.json,selection.json,summary.json,README.md}

Honesty rules enforced here:
* source_evidence.inspected is ALWAYS false: workers read the stored snapshot text only, never the PDF.
* Templated / boilerplate rationales are rejected.
* No answers, keys, content or live records are touched. review_status stays pending.
"""
import argparse, glob, hashlib, json, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'reports/retag-work-20261109'
QUAR = ROOT / 'reports/quarantine-templated-20261109'
BOILER = re.compile(r'(Question\s+(None|\d+)\s+assesses|Appropriately classified under|syllabus specifications|Verified against registered booklet)', re.I)
MODEL = 'Claude Sonnet 5.5'
TOOL = 'study-tagging-v1 (per-question retag, stored-snapshot review)'


def load_packets():
    items, tax, by_batch = {}, None, {}
    for d in sorted(QUAR.glob('tagging-batch*-20261108')):
        pk = json.loads((d / 'oracle-packet.json').read_text())
        tax = tax or pk['taxonomy']
        b = int(re.search(r'batch(\d+)-', d.name).group(1))
        for it in pk['items']:
            items[it['appearance_id']] = (b, it)
        by_batch[b] = pk
    return items, tax


def path_ok(p, nodes):
    if not isinstance(p, dict) or set(p) != {'subject_id', 'topic_id', 'subtopic_id'} or not p['subject_id']:
        return 'incomplete path object'
    if p['subtopic_id'] and not p['topic_id']:
        return 'subtopic without topic'
    parent = None
    for lvl in ('subject', 'topic', 'subtopic'):
        t = p[lvl + '_id']
        if t is None:
            continue
        n = nodes.get(t)
        if not n or n.get('active') is False or n['level'] != lvl or n.get('parent_id') != parent:
            return f'invalid active taxonomy path: {t}'
        parent = t
    return None


def build_record(w, b, it, nodes):
    rec = it['snapshot']['record']
    errs = []
    prim = {'subject_id': w.get('subject_id'), 'topic_id': w.get('topic_id'), 'subtopic_id': w.get('subtopic_id')}
    hold = bool(w.get('hold'))
    if not hold:
        e = path_ok(prim, nodes)
        if e:
            errs.append(e)
    why, skill = (w.get('why') or '').strip(), (w.get('skill') or '').strip()
    if len(why) < 30 or BOILER.search(why):
        errs.append('rationale missing/templated')
    if len(skill.split()) < 6 or BOILER.search(skill):
        errs.append('tested_skill missing/templated')
    related = w.get('related') or []
    for r in related:
        e = path_ok(r, nodes)
        if e:
            errs.append('related: ' + e)
    cur = rec['classification']
    cur_related = rec.get('relatedClassifications', [])
    if hold:
        action = 'hold'
        prim = None
        if not w.get('owner_question'):
            errs.append('hold needs owner_question')
    else:
        action = 'keep' if (prim == cur and related == cur_related) else 'retag'
    if errs:
        return None, errs
    page = rec.get('page')
    return {
        'policy_version': 'study-tagging-v1',
        'canonical_id': it['canonical_id'], 'appearance_id': it['appearance_id'],
        'source_fingerprint': it['source_fingerprint'], 'action': action, 'review_status': 'pending',
        'current_primary': cur, 'proposed_primary': prim, 'proposed_related': related,
        'tested_skill': skill, 'rationale': why,
        'source_evidence': {'document_id': None, 'sha256': None,
                            'physical_page': page if isinstance(page, int) and page >= 1 else None,
                            'printed_question': rec.get('qnum'), 'inspected': False,
                            'note': 'Decided from the stored question snapshot text (stem, options, direction); the original PDF was NOT inspected.'},
        'context_candidate': {'region': '', 'language': '', 'time_behavior': w.get('time') or 'unknown',
                              'reference_period': '', 'reference_basis': 'unknown'},
        'context_reason': 'Not evidenced from the stored snapshot; no reference period asserted.',
        'source_issues': w.get('issues') or [], 'taxonomy_gap': w.get('gap'), 'alternatives': [],
        'owner_question': w.get('owner_question') if hold else None,
        'reviewer_model': MODEL, 'reviewer_tool': TOOL,
    }, []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chunks', nargs='*', help='chunk numbers (default: all with output)')
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()
    items, tax = load_packets()
    nodes = {n['id']: n for n in tax}
    outs = sorted(glob.glob(str(WORK / 'out/chunk_*.json')))
    if a.chunks:
        outs = [o for o in outs if re.search(r'chunk_(\d+)', o).group(1).lstrip('0') in {c.lstrip('0') for c in a.chunks}]
    stats, rejects, built = Counter(), [], {}
    for o in outs:
        n = re.search(r'chunk_(\d+)', o).group(1)
        want = [x['aid'] for x in json.loads((WORK / f'chunks/chunk_{n}.json').read_text())]
        got = json.loads(Path(o).read_text())
        if [g['aid'] for g in got] != want:
            rejects.append((n, 'aid list/order mismatch')); continue
        for w in got:
            b, it = items[w['aid']]
            rec, errs = build_record(w, b, it, nodes)
            if errs:
                rejects.append((n, w['aid'], errs)); continue
            built.setdefault(b, []).append(rec); stats[rec['action']] += 1
    print(dict(stats), 'rejected', len(rejects))
    for r in rejects[:15]:
        print('  REJECT', r)
    if a.dry:
        return
    for b, recs in sorted(built.items()):
        d = ROOT / f'reports/tagging-retag-{b:04d}-20261109'
        d.mkdir(parents=True, exist_ok=True)
        (d / 'pending-candidates.json').write_text(json.dumps(recs, ensure_ascii=False, indent=2) + '\n')
        src = QUAR / f'tagging-batch{b}-20261108' / 'oracle-packet.json'
        pk = json.loads(src.read_text())
        ids = {r['appearance_id'] for r in recs}
        pk['items'] = [i for i in pk['items'] if i['appearance_id'] in ids]
        (d / 'oracle-packet.json').write_text(json.dumps(pk, ensure_ascii=False, indent=1) + '\n')
        (d / 'README.md').write_text(f'# Per-question re-tag of former batch {b}\n\nReplaces quarantined templated batch {b}. Pending candidates only; decided from stored snapshot text, PDFs NOT inspected (source_evidence.inspected=false). Reviewer: {MODEL}.\n\nCounts: {dict(Counter(r["action"] for r in recs))}\n')
    print('batches written', len(built))


if __name__ == '__main__':
    main()
