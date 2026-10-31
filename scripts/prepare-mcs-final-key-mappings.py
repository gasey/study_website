#!/usr/bin/env python3
"""Prepare source-checked MCS key cells. Does not submit decisions or edit bank."""
import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B = ROOT.parent / 'mpsc-question-bankv2'
SPEC = importlib.util.spec_from_file_location('mcs_extract', ROOT / 'scripts/restore-mcs-recent-papers.py')
EXTRACT = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(EXTRACT)


def transcription_gate(question, extracted):
    """A repaired source needs explicit remapping, never a stale OCR baseline."""
    text = '\n'.join([question['question'], *question['options']])
    if any(unicodedata.category(char) == 'Co' for char in text):
        return 'unresolved_font_glyphs'
    if any(question[field] != extracted[field] for field in ('question', 'options', 'page')):
        return 'changed_transcription_requires_manual_mapping'
    return None


def parse_text_key(text, compensated):
    matches = [(int(n), letter) for n, letter in re.findall(r'\b(\d{1,3})\s+\(([ABCD])\)', text)]
    cells = dict(matches)
    if len(matches) != len(cells):
        raise ValueError('Repeated question numbers in final-key table')
    if (set(cells) & set(compensated) or set(cells) | set(compensated) != set(range(1, 101))):
        raise ValueError('Every printed key cell must be a letter or an explicit compensation')
    return cells


def parse_image_key(page, compensated):
    if len(page['rows']) != 4 or any(len(row.split()) != 25 for row in page['rows']):
        raise ValueError('Require four complete 25-cell source columns')
    values = ' '.join(page['rows']).split()
    if set(values) - set('ABCDX'):
        raise ValueError('Unrecognized key cell; do not repair OCR by inference')
    if {n + 1 for n, letter in enumerate(values) if letter == 'X'} != set(compensated):
        raise ValueError('Compensation entries disagree with inspected source manifest')
    return {n + 1: letter for n, letter in enumerate(values) if letter != 'X'}


def prepare(output):
    output.mkdir(parents=True, exist_ok=True)
    raw = (B / 'bank/mpsc_bank_v2.json').read_bytes(); bank = json.loads(raw)
    compensations = json.loads((ROOT / 'docs/sources/mcs-recent-compensations.json').read_text())['papers']
    image_key = json.loads((ROOT / 'docs/sources/mcs-2025-final-key-cells.json').read_text())
    if {(p['paper'], p['series']) for p in image_key['pages']} != {(p, s) for p in ['I', 'II'] for s in 'ABCD'} or len(image_key['pages']) != 8:
        raise ValueError('Require exactly eight distinct booklet tables')
    keys = {}
    for p in compensations:
        source = B / 'pdfs' / p['final_key_file']
        if hashlib.sha256(source.read_bytes()).hexdigest() != p['key_sha256']:
            raise ValueError('Final key PDF changed')
        pid = p['paper_id']
        if '2023' in pid:
            text = subprocess.run(['pdftotext', '-layout', str(source), '-'], capture_output=True, text=True, check=True).stdout
            cells = parse_text_key(text, p['compensated_question_numbers'])
        else:
            if image_key['sourceSha256'] != p['key_sha256']:
                raise ValueError('Transcribed image key is for a different PDF')
            page = next(row for row in image_key['pages'] if row['page'] == p['key_page'])
            ident = re.search(r'Paper-(II|I) Series-([A-D])', pid)
            if not ident or ident.groups() != (page['paper'], page['series']):
                raise ValueError('Wrong paper or booklet page')
            cells = parse_image_key(page, p['compensated_question_numbers'])
        keys[pid] = {**p, 'answers': cells,
            'document_id': 'key_' + hashlib.sha256((pid + '|' + p['key_sha256']).encode()).hexdigest()[:24]}
    restoration = json.loads((ROOT / 'docs/sources/mcs-recent-restoration.json').read_text())
    targets = {(p['paper_id'], n) for p in restoration['papers'] for n in p['missing_question_numbers']}
    source_rows = {}
    for p in restoration['papers']:
        pdf = B / 'pdfs' / p['paper_id']
        if hashlib.sha256(pdf.read_bytes()).hexdigest() != p['sha256']:
            raise ValueError('Original question PDF changed')
        text = subprocess.run(['pdftotext', '-layout', str(pdf), '-'], capture_output=True, text=True, check=True).stdout
        for row in EXTRACT.extract(text):
            source_rows[p['paper_id'], row['qnum']] = row
    ready = []; pending = Counter(); source_review = []
    for q in bank['questions']:
        ident = (q['paperId'], q.get('qnum'))
        if ident not in targets:
            continue
        key = keys[q['paperId']]; row = source_rows[ident]
        if q['qnum'] not in key['answers']:
            pending['compensated'] += 1; continue
        if q.get('sourceDefect') or not row['valid_options']:
            pending['source_defect'] += 1; continue
        if not any(c.get('is_primary') and c.get('review_status') == 'approved' for c in q.get('classifications', [])):
            pending['classification'] += 1; continue
        # This prepares new mappings, not a retrospective source audit. A
        # repaired question already published through explicit key review must
        # not keep appearing as unfinished manual mapping on every later run.
        if q.get('answerIndex') is not None or q.get('answerSource') != 'none':
            pending['already_answered'] += 1; continue
        gate = transcription_gate(q, row)
        if gate:
            pending[gate] += 1
            source_review.append({'appearance_id': q['id'], 'paper_id': q['paperId'],
                                  'printed_question': q['qnum'], 'reason': gate})
            continue
        letter = key['answers'][q['qnum']]
        expected_source={k: q.get(k) for k in ('question', 'options', 'page', 'qnum', 'figureImage', 'direction', 'hasDiagram')}
        expected_source['qnum']=str(q['qnum'])
        ready.append({'appearance_id': q['id'], 'paper_id': q['paperId'], 'printed_question': q['qnum'],
            'page': q['page'], 'document_id': key['document_id'], 'key_page': key['key_page'],
            'key_sha256': key['key_sha256'], 'key_file': key['final_key_file'], 'key_letter': letter,
            'answer_index': 'ABCD'.index(letter), 'expected_source': expected_source})
    result = {'bank_sha256': hashlib.sha256(raw).hexdigest(), 'ready': ready, 'pending': dict(pending),
              'manual_source_review': source_review,
              'policy': 'Exact booklet key cells and original PDF positions. No answer letter copied between series. No worked explanation inferred.'}
    (output / 'mappings.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    (output / 'keys.json').write_text(json.dumps(keys, indent=2) + '\n')
    print(json.dumps({'ready': len(ready), 'pending': dict(pending), 'papers_with_keys': len(keys)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', type=Path, required=True)
    prepare(parser.parse_args().output)
