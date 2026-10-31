#!/usr/bin/env python3
"""Read-only source-number/page audit; never merge, renumber or assign answers."""
import argparse
import hashlib
import json
import re
import subprocess
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK_ROOT = ROOT.parent / 'mpsc-question-bankv2'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()


def source_positions(text, expected=100):
    # Blanking a cover must retain the formfeed: pages are physical PDF pages.
    text = '\f\n'.join('' if 'QUESTION BOOKLET' in page and 'INSTRUCTIONS' in page
                       else page for page in text.split('\f'))
    starts = []
    # Some figure-only questions have just "39."; 2014 I prints bare "79 ".
    pattern = r'(?m)^[ \t]*(\d{1,3})(?:\.[ \t]*|[ \t]+(?=\S))'
    for match in re.finditer(pattern, text):
        number = int(match[1])
        if number != len(starts) + 1:
            continue
        # Numbered statements inside a stem cannot start the next question.
        if starts and set(re.findall(r'\(([a-d])\)',
                text[starts[-1].end():match.start()])) != set('abcd'):
            continue
        starts.append(match)
    if len(starts) != expected:
        raise ValueError(f'Expected {expected} sequential source positions; found {len(starts)}')
    result = []
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        body = text[match.end():end]
        if set(re.findall(r'\(([a-d])\)', body)) != set('abcd'):
            raise ValueError(f'Incomplete source choice labels at printed {match[1]}')
        result.append({'qnum': int(match[1]), 'page': text[:match.start()].count('\f') + 1,
                       'source_body_sha256': hashlib.sha256(body.encode()).hexdigest()})
    return result


def normalized_content(question):
    normalize = lambda value: re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', value)).strip()
    return normalize(question['question']), tuple(normalize(v) for v in question['options'])


def compare_records(records, positions):
    by_number = defaultdict(list)
    expected = {row['qnum']: row for row in positions}
    for question in records:
        by_number[question.get('qnum')].append(question)
    issues = []
    for number, source in expected.items():
        matches = by_number[number]
        if not matches:
            issues.append({'kind': 'missing-source-appearance', 'qnum': number,
                           'source': source, 'action': 'Prepare unanswered original-source restoration; do not infer a key.'})
        if len(matches) > 1:
            issues.append({'kind': 'duplicate-printed-position', 'qnum': number,
                'source': source,
                'whitespace_normalized_text_and_ordered_options_agree':
                    len({normalized_content(q) for q in matches}) == 1,
                'records': [{'id': q['id'], 'page': q.get('page'),
                             'answer_source': q.get('answerSource'), 'baseline_sha256': digest(q)} for q in matches],
                'action': 'Review canonical/appearance/history links before any retirement or merge; transfer no answer.'})
        for question in matches:
            if question.get('page') != source['page']:
                issues.append({'kind': 'physical-page-mismatch', 'qnum': number,
                    'appearance_id': question['id'], 'current_page': question.get('page'),
                    'expected_page': source['page'], 'baseline_sha256': digest(question),
                    'action': 'Audited source_reference correction; retain preceding shared passage context.'})
    for number, matches in by_number.items():
        if number not in expected:
            issues.append({'kind': 'unexpected-bank-position', 'qnum': number,
                           'appearance_ids': [q['id'] for q in matches]})
    return issues


def audit(manifest_path, output):
    # The only write is a report in the application workspace, never a source
    # PDF or canonical bank file (including through an output symlink).
    if not output.resolve().is_relative_to((ROOT / 'reports').resolve()) or output.suffix != '.json':
        raise ValueError('Write the audit JSON under the application reports directory')
    manifest = json.loads(manifest_path.read_text())
    raw = (BANK_ROOT / 'bank/mpsc_bank_v2.json').read_bytes()
    bank = json.loads(raw)
    papers = []
    seen = set()
    for paper in manifest['papers']:
        pid = paper['paper_id']
        if pid in seen:
            raise ValueError('Duplicate paper in audit scope')
        seen.add(pid)
        source = (BANK_ROOT / 'pdfs' / pid).resolve()
        if not source.is_relative_to((BANK_ROOT / 'pdfs').resolve()):
            raise ValueError('Source is outside the PDF archive')
        if hashlib.sha256(source.read_bytes()).hexdigest() != paper['sha256']:
            raise ValueError('Source PDF changed: ' + pid)
        text = subprocess.run(['pdftotext', '-layout', str(source), '-'],
                              capture_output=True, text=True, check=True).stdout
        positions = source_positions(text, paper['expected_printed_questions'])
        records = [q for q in bank['questions'] if q['paperId'] == pid]
        if not records:
            raise ValueError('Audit target has no bank records: ' + pid)
        papers.append({**paper, 'source_position_count': len(positions),
                       'bank_record_count': len(records), 'source_positions': positions,
                       'issues': compare_records(records, positions)})
    result = {'status': 'read-only audit; no corrections applied',
              'bank_sha256': hashlib.sha256(raw).hexdigest(), 'papers': papers,
              'limitations': 'Printed numbering/page inventory only. Not transcription, answer-key, exam-rule or simulation certification.'}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'papers': len(papers), 'source_positions': sum(p['source_position_count'] for p in papers),
                      'bank_records': sum(p['bank_record_count'] for p in papers),
                      'issues': sum(len(p['issues']) for p in papers), 'bank_changed': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    audit(args.manifest, args.output)
