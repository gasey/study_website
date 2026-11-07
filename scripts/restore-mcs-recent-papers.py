#!/usr/bin/env python3
"""Restore missing source appearances only; never copy keys or modify existing rows.

Preparation is provisional. Full PDF page images preserve tables, figures and
shared passages that a searchable text extraction cannot faithfully represent.
"""
import argparse
import fcntl
import hashlib
import io
import json
import os
import re
import subprocess
from pathlib import Path
from editorial_protection import write_guarded

ROOT = Path(__file__).resolve().parents[1]
BANK_ROOT = ROOT.parent / 'mpsc-question-bankv2'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def clean(text):
    return '\n'.join(line.rstrip() for line in text.splitlines()
                     if not re.search(r'Paper-\s*II?\s*\([A-D]\)|CSP\s*:', line)
                     and not re.fullmatch(r'\s*(?:[-* ]+|-\s*\d{1,3}\s*-)\s*', line)).strip()


def extract(text):
    # Preserve formfeeds for physical PDF page mapping. Do not parse the cover's
    # numbered instructions as printed questions.
    text = '\f\n'.join('' if 'QUESTION BOOKLET' in page and 'INSTRUCTIONS' in page
                     else clean(page) for page in text.split('\f'))
    starts = []
    for match in re.finditer(r'(?m)^[ \t]*(\d{1,3})\.[ \t]+', text):
        number = int(match[1])
        if number != len(starts) + 1:
            continue
        if starts:
            previous = text[starts[-1].end():match.start()]
            if (set(re.findall(r'\(([a-d])\)', previous)) != set('abcd')
                    and not re.search(r'\b(?:figures?|diagrams?)\b', previous, re.I)):
                continue
        starts.append(match)
    if len(starts) != 100:
        raise ValueError(f'Expected 100 sequential printed questions, found {len(starts)}')
    result = []
    for i, match in enumerate(starts):
        end = starts[i + 1].start() if i < 99 else len(text)
        body = text[match.end():end]
        labels = list(re.finditer(r'\(([a-d])\)\s*', body))
        first = {}
        for label in labels:
            first.setdefault(label[1], label)
        ordered = sorted(first.items(), key=lambda pair: pair[1].start())
        options = [''] * 4
        for j, (letter, label) in enumerate(ordered):
            value = body[label.end():ordered[j + 1][1].start() if j + 1 < len(ordered) else len(body)]
            value = re.split(r'(?im)^\s*(?:Directions?\b|Passage\s*[-–:]?\s*\d|Question Nos?\b)', value)[0]
            options[ord(letter) - 97] = clean(value)
        valid = len(ordered) == 4 and all(options) and len(set(options)) == 4
        result.append({'qnum': i + 1, 'page': text[:match.start()].count('\f') + 1,
                       'end_page': text[:max(match.start(), end - 1)].count('\f') + 1,
                       'question': clean(body[:ordered[0][1].start()] if ordered else body),
                       'options': [v or f'See printed option {chr(65+j)} in the source image'
                                   for j, v in enumerate(options)], 'valid_options': valid})
    return result


def prepare(manifest, output):
    import pymupdf
    from PIL import Image
    bank_path = BANK_ROOT / 'bank/mpsc_bank_v2.json'
    before = bank_path.read_bytes()
    bank = json.loads(before)
    questions = []
    assets = {}
    for item in manifest['papers']:
        pid = item['paper_id']
        source = BANK_ROOT / 'pdfs' / pid
        assert digest(source.read_bytes()) == item['sha256'], 'Source PDF changed'
        existing = [q for q in bank['questions'] if q['paperId'] == pid]
        present = {int(q['qnum']) for q in existing}
        missing = set(item['missing_question_numbers'])
        assert present.isdisjoint(missing) and present | missing == set(range(1, 101))
        assert len(present) == len(existing), 'Duplicate printed numbers require separate review'
        text = subprocess.run(['pdftotext', '-layout', str(source), '-'],
                              capture_output=True, text=True, check=True).stdout
        (output / (source.name + '.txt')).write_text(text)
        doc = pymupdf.open(source)
        for row in extract(text):
            if row['qnum'] not in missing:
                continue
            # Include preceding passage pages for aptitude questions. These are
            # source context, never purported question bounding-box highlights.
            first_page = max(1, row['page'] - 2) if 'Paper-II ' in pid else row['page']
            pages = tuple(range(first_page, min(len(doc), row['end_page']) + 1))
            key = (pid, pages)
            if key not in assets:
                ims = [Image.open(io.BytesIO(doc[p-1].get_pixmap(matrix=pymupdf.Matrix(1.4, 1.4)).tobytes('png'))).convert('L') for p in pages]
                im = Image.new('L', (max(x.width for x in ims), sum(x.height for x in ims)), 255)
                y = 0
                for img in ims:
                    im.paste(img, (0, y)); y += img.height
                buf = io.BytesIO(); im.save(buf, format='PNG', optimize=True)
                data = buf.getvalue(); rel = 'images/page-renders/' + digest(data) + '.png'
                path = BANK_ROOT / rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
                assets[key] = rel
            q = {'id': digest((pid + '|mcq|' + str(row['qnum'])).encode())[:20],
                 'paperId': pid, 'type': 'mcq', 'qnum': row['qnum'], 'page': row['page'],
                 'question': row['question'], 'options': row['options'], 'answerIndex': None,
                 'answerSource': 'none', 'explanation': None, 'marks': None, 'classifications': [],
                 'hasDiagram': True, 'figureImage': assets[key],
                 'direction': 'Read the original printed question and any shared passages, tables and figures in the source image. Searchable transcription is provisional; answer-key matching is pending.',
                 'origin': {'kind': 'restored-original-paper', 'source_sha256': item['sha256'],
                            'review_date': '2026-10-31', 'text_status': 'provisional; original PDF pages retained'}}
            if not row['valid_options']:
                q.update(sourceDefect='unresolved-source', disputeNote='Option extraction requires visual review against the original PDF.')
            questions.append(q)
    artifact = {'bank_sha256': digest(before), 'manifest': manifest, 'questions': questions}
    (output / 'restoration.json').write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'new_questions': len(questions), 'images': len(assets),
                      'option_issues': sum('sourceDefect' in q for q in questions)}))


def apply(artifact_path, receipt_path):
    artifact = json.loads(artifact_path.read_text())
    bank_path = BANK_ROOT / 'bank/mpsc_bank_v2.json'
    with open(str(bank_path) + '.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        before = bank_path.read_bytes()
        assert digest(before) == artifact['bank_sha256'], 'Bank changed: prepare again'
        bank = json.loads(before); known = {q['id'] for q in bank['questions']}
        targets = {(p['paper_id'], n) for p in artifact['manifest']['papers'] for n in p['missing_question_numbers']}
        added = artifact['questions']
        assert len(added) == len(targets) == 480
        assert {(q['paperId'], q['qnum']) for q in added} == targets
        assert len({q['id'] for q in added}) == len(added) and not known.intersection(q['id'] for q in added)
        for item in artifact['manifest']['papers']:
            assert digest((BANK_ROOT / 'pdfs' / item['paper_id']).read_bytes()) == item['sha256']
        for q in added:
            assert q['answerIndex'] is None and q['answerSource'] == 'none' and q['classifications'] == []
            assert q['page'] >= 1 and len(q['options']) == 4 and all(q['options'])
            assert (BANK_ROOT / q['figureImage']).is_file()
        # Keep a byte-identical backup and preserve every existing record object.
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        (receipt_path.parent / 'bank-before.json').write_bytes(before)
        bank['questions'].extend(added)
        tmp = bank_path.with_suffix('.restoration.tmp')
        tmp.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + '\n')
        write_guarded(bank_path, bank, locked=True)
        tmp.unlink(missing_ok=True)
        receipt_path.write_text(json.dumps({'before_sha256': digest(before),
            'after_sha256': digest(bank_path.read_bytes()), 'added': len(added),
            'existing_records_changed': 0, 'answers_added': 0}, indent=2) + '\n')
        print(receipt_path.read_text())


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='mode', required=True)
    prep = sub.add_parser('prepare'); prep.add_argument('--manifest', type=Path, required=True); prep.add_argument('--output', type=Path, required=True)
    imp = sub.add_parser('apply'); imp.add_argument('artifact', type=Path); imp.add_argument('--receipt', type=Path, required=True)
    args = p.parse_args()
    if args.mode == 'prepare':
        args.output.mkdir(parents=True, exist_ok=True)
        prepare(json.loads(args.manifest.read_text()), args.output)
    else:
        apply(args.artifact, args.receipt)
