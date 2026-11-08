#!/usr/bin/env python3
"""Prepare source-bound Gazetted drafts. Reads PDFs only; never writes the bank.

This is segmentation, not source certification. Options that cannot be separated
unambiguously remain in the stem for a reviewer rather than receiving placeholders.
"""
import argparse
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

EXAM = "Combined Competitive Examination for Mizoram Group ‘B’ (Gazetted) General Services under Excise & Narcotics Department & Finance Department, Government of Mizoram"
COMMON = 'Old_Questions/Departmental_2015-2018/1.Departmental Exam for Sub Inspector and Inspector under Excise 2016 Paper I COMMON.pdf'
QUESTION = re.compile(r'^ {0,2}(\d{1,3})\.[ \t]+', re.M)
DIRECTION = re.compile(r'^\s*Direction \(Question Nos?\.\s*(\d+)\s*(?:-\s*(\d+))?\)\s*:', re.M)


def clean(text):
    lines = [line.rstrip() for line in text.splitlines()
             if not re.fullmatch(r'\s*(?:Series\s*-\s*[AB]\s*)?-\s*\d+\s*-\s*', line)
             and not re.fullmatch(r'\s*\*+\s*', line)]
    return '\n'.join(lines).strip()


def options_from(body):
    """Keep a/b and c/d two-column rows apart; refuse ambiguous continuations."""
    start = re.search(r'^[ \t]*\(a\)[ \t]+', body, re.M)
    if not start:
        return body, [], 'Inspect printed options: no option-a row found.'
    first = start.start()
    stem, option_text = body[:first].strip(), body[first:]
    matches = list(re.finditer(r'\(([a-d])\)[ \t]*', option_text))
    if [m[1] for m in matches] != list('abcd'):
        return body, [], 'Inspect printed options: labels are not one a/b/c/d set.'
    values = {letter: [] for letter in 'abcd'}
    current = None
    paired = False
    for line in option_text.splitlines():
        labels = list(re.finditer(r'\(([a-d])\)[ \t]*', line))
        if labels:
            paired = len(labels) > 1
            for i, label in enumerate(labels):
                end = labels[i + 1].start() if i + 1 < len(labels) else len(line)
                values[label[1]].append(line[label.end():end].strip())
            current = labels[-1][1]
        elif line.strip():
            if paired:
                return body, [], 'Inspect wrapped two-column options in the original PDF.'
            if current:
                values[current].append(line.strip())
    options = [' '.join(values[x]).strip() for x in 'abcd']
    if not all(options) or len(set(options)) != 4:
        return body, [], 'Inspect missing or identical extracted options in the original PDF.'
    return stem, options, None


def prepare(path, source_id, sha):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != sha:
        raise ValueError(f'Source hash changed: {source_id}')
    text = subprocess.run(['pdftotext', '-layout', '-enc', 'UTF-8', str(path), '-'],
                          capture_output=True, check=True, timeout=120).stdout.decode('utf-8')
    pages = text.split('\f')
    if not pages[-1].strip():
        pages.pop()
    english = path.name.startswith('general-english-')
    common = path.name == 'common-2016-paper-i.pdf'
    essay = path.name == 'general-essay.pdf'
    # Cover instructions also use numbered paragraphs; they are not questions.
    body = '\f\n'.join(clean(page) if i or common or essay else '' for i, page in enumerate(pages))
    starts = list(QUESTION.finditer(body))
    expected = list(range(1, 11)) if common else list(range(1, 9)) if essay else list(range(1, 4)) + list(range(1, 67)) if english else list(range(1, 101))
    if [int(m[1]) for m in starts] != expected:
        raise ValueError(f'Printed number sequence differs from inspected source: {source_id}')
    directions = []
    for m in DIRECTION.finditer(body):
        following = next(s for s in starts if s.start() > m.end())
        directions.append((m.start(), int(m[1]), int(m[2] or m[1]), clean(body[m.start():following.start()])))
    questions, checks = [], []
    for i, m in enumerate(starts):
        number = int(m[1]); end = starts[i + 1].start() if i + 1 < len(starts) else len(body)
        # A new instruction belongs to the next question, never option d above it.
        cuts = [d[0] for d in directions if m.end() < d[0] < end]
        part_b = re.search(r'^\s*PART-?\s*B\b', body[m.end():end], re.M)
        if part_b:
            cuts.append(m.end() + part_b.start())
        unit = re.search(r'^\s*UNIT\s*-\s*II\b', body[m.end():end], re.M)
        if unit:
            cuts.append(m.end() + unit.start())
        if cuts:
            end = min(cuts)
        value = clean(body[m.end():end])
        written = common or essay or english and i < 3
        printed = ('A' if i < 3 else 'B') + str(number) if english else str(number)
        direction = next((d[3] for d in reversed(directions) if d[0] < m.start() and d[1] <= number <= d[2]), '') if not written else ''
        if english:
            direction = ('PART - A (Conventional Type) (34 Marks). This Section should be answered only on the Answer Sheet provided. Marks for each question is indicated against it.' if written else 'PART - B (Multiple Choice Questions) (66 Marks). All questions carry equal mark of 1. Attempt all questions. The questions in this Section should be answered only on the OMR Response Sheet provided.\n' + direction)
        elif common:
            direction = 'Marks for each question is indicated against it. Attempt all questions.'
        elif essay:
            direction = ('Write an essay on any 2 (two) of the following topics taking 1 (one) topic from each unit. Each topic carries equal marks of 50. Each essay shall be written in 1000 - 1200 words.\nUNIT - ' + ('I' if number <= 4 else 'II'))
        stem, options, issue = (value, [], None) if written else options_from(value)
        if issue:
            checks.append({'number': printed, 'issue': issue})
        page = body[:m.start()].count('\f') + 1
        formatting = bool(re.search(r'underlined|italici[sz]ed|marked in Italics|\bfigures?\b|\bdiagrams?\b', direction + ' ' + stem, re.I))
        if formatting:
            checks.append({'number': printed, 'issue': 'Source image required for printed emphasis/diagram.', 'page': page})
        questions.append({'id': 'draft_' + hashlib.sha256((sha + ':' + printed).encode()).hexdigest()[:24],
                          'number': printed, 'page': page, 'type': 'descriptive' if written else 'mcq',
                          'question': stem, 'options': options, 'direction': direction, 'passage': '',
                          'explanation': '', 'answer_index': None, 'answer_source': 'none', 'key_page': None,
                          'subject_id': 'english' if common or english else 'general-studies',
                          'topic_id': None, 'subtopic_id': None, 'figure_job': None})
    subject = 'Paper I — General English (Common)' if common else 'General English' if english else 'General Essay' if essay else 'General Studies-' + path.stem.split('-')[1].upper()
    booklet = path.stem[-1].upper() if 'series-' in path.stem else ''
    year = 2016 if common else 2026
    exam = 'Departmental Examinations for Sub-Inspector and Inspector (Common) under Excise & Narcotics Department' if common else EXAM
    notes = ('PDF page 1 identifies the examination and September ' + str(year) + ' sitting. AI-assisted text segmentation only; independent source inspection, exact learning tags and option/formatting review remain. No answers or human sign-offs supplied. ')
    if english:
        notes += 'Printed numbering restarts in Part B: A1–A3 and B1–B66 preserve the section identity (69 top-level questions, 100 marks). '
    if common:
        notes += 'Already registered as ' + COMMON + '. Link this draft to that existing empty original in the workbench before independent review; preserve its registered exam identity instead of creating an Uploaded duplicate. '
    if checks:
        notes += 'Inspect extraction/formatting: ' + ', '.join(sorted({c['number'] for c in checks})) + '.'
    payload = {'title': subject + (' · Series ' + booklet if booklet else '') + ' · ' + str(year),
               'exam_name': exam, 'year': year, 'paper_subject': subject, 'booklet': booklet,
               'source_reference': source_id, 'identity_page': 1, 'identity_note': notes,
               'expected_questions': len(questions), 'key_sha256': None, 'key_title': '', 'key_series': '', 'questions': questions}
    crops = []
    if any('page' in check for check in checks):
        ns = {'x': 'http://www.w3.org/1999/xhtml'}
        tree = ET.fromstring(subprocess.run(['pdftotext', '-bbox-layout', str(path), '-'],
                                          capture_output=True, check=True, timeout=120).stdout)
        boxes = tree.findall('.//x:page', ns)
        for check in checks:
            if 'page' not in check:
                continue
            box = boxes[check['page'] - 1]
            starts_on_page = []
            for line in box.findall('.//x:line', ns):
                words = line.findall('x:word', ns)
                if words and re.fullmatch(r'\d+\.', words[0].text or '') and float(words[0].get('xMin')) < 80:
                    starts_on_page.append((words[0].text[:-1], float(line.get('yMin'))))
            target = check['number'].removeprefix('B')
            hits = [y for n, y in starts_on_page if n == target]
            if len(hits) != 1:
                raise ValueError(f'Cannot locate source crop: {source_id} {target}')
            height = float(box.get('height')); top = max(0, hits[0] - 4)
            bottom = min([y - 4 for n, y in starts_on_page if y > hits[0]] + [height - 30])
            crops.append({'number': check['number'], 'kind': 'crop', 'page': check['page'],
                          'x': 0.035, 'width': 0.93, 'y': top / height, 'height': (bottom - top) / height})
    return {'source_id': source_id, 'source_sha256': sha, 'filename': path.name, 'pages': len(pages),
            'text_sha256': hashlib.sha256(text.encode()).hexdigest(), 'payload': payload, 'review_checks': checks, 'crops': crops}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sources', type=Path, required=True)
    p.add_argument('--audit', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    audit = json.loads(args.audit.read_text())
    papers = []
    for row in audit['missing_2026_sources']:
        papers.append(prepare(args.sources / Path(row['id']).name, row['id'], row['sha256']))
    document = next(d for d in audit['documents'] if d['paper_id'] == COMMON and d['kind'] == 'paper')
    papers.append(prepare(args.sources / 'common-2016-paper-i.pdf', COMMON, document['sha256']))
    artifact = {'schema': 1, 'status': 'draft-only; no source certification, answer inference or independent approval', 'papers': papers}
    args.output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps([{'source': x['filename'], 'questions': len(x['payload']['questions']), 'checks': len(x['review_checks'])} for x in papers], indent=2))


if __name__ == '__main__':
    main()
