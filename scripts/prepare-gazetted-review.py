#!/usr/bin/env python3
"""Prepare a source-bound Gazetted draft review proposal; never writes to a service.

Classification choices below were reviewed against the printed questions. Matching
booklets reuse classification only, after checking stem, options, passage and the
semantic direction. Printed wording, numbering and options remain booklet-specific.
"""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def normalized(text):
    return re.sub(r'\s+', ' ', text).strip().rstrip(':')


def signature(q):
    direction = re.sub(r'Question Nos?\.\s*[\d -]+', 'Question', q['direction'])
    return (normalized(q['question']), tuple(sorted(normalized(x) for x in q['options'])),
            normalized(q['passage']), normalized(direction), q['type'])


def english(q):
    if q['number'] in ('A1', 'A3'): return 'english/comprehension'
    if q['number'] == 'A2': return 'english'
    n = int(q['number'][1:])
    for end, path in [(10, 'grammar/parts-of-speech'), (14, 'vocabulary/antonyms'),
                      (18, 'vocabulary/synonyms'), (22, 'vocabulary'),
                      (26, 'vocabulary/idioms-and-phrases'), (36, 'grammar/subject-verb-agreement'),
                      (46, 'grammar/prepositions'), (52, 'grammar/tenses'), (66, 'grammar')]:
        if n <= end: return 'english/' + path
    raise ValueError(q['number'])


def gs1(q):
    n = int(q['number'])
    overrides = {57: 'mizoram', 65: 'indian-polity', 66: 'geography', 69: 'indian-polity',
                 76: 'indian-polity', 89: 'indian-economy', 90: 'indian-economy'}
    return 'general-studies/' + overrides.get(n, 'indian-history' if n <= 50 else 'current-affairs')


def gs2(q):
    n = int(q['number'])
    if n in (21, 25, 26, 29, 30): topic = 'indian-history'
    elif n <= 40 or n == 61: topic = 'indian-polity'
    elif n <= 80 or n in (88, 92): topic = 'indian-economy'
    else: topic = 'geography'
    return 'general-studies/' + topic


def gs3(q):
    n = int(q['number'])
    if n <= 40:
        overrides = {3: 'general-studies/indian-economy', 8: 'general-studies/indian-economy',
                     12: 'computer-science/networking', 16: 'general-studies/environment',
                     17: 'general-studies/indian-economy', 21: 'general-studies/geography',
                     22: 'computer-science/networking', 23: 'general-studies/indian-economy',
                     30: 'computer-science/computer-systems-and-architecture/computer-hardware',
                     31: 'science/biology', 39: 'general-studies/environment', 40: 'science/biology'}
        return overrides.get(n, 'general-knowledge/science-in-the-news')
    if n <= 80: return 'general-studies/mizoram'
    return {
        81: 'reasoning-and-aptitude/numerical-ability', 82: 'reasoning-and-aptitude',
        83: 'mathematics/arithmetic/averages', 84: 'english/sentence-correction',
        85: 'english/grammar', 86: 'reasoning-and-aptitude',
        87: 'reasoning-and-aptitude/verbal-reasoning', 88: 'english/comprehension',
        89: 'reasoning-and-aptitude/numerical-ability', 90: 'mathematics/arithmetic/profit-and-loss',
        91: 'mathematics/arithmetic/ratio-and-proportion', 92: 'reasoning-and-aptitude/series',
        93: 'reasoning-and-aptitude/verbal-reasoning', 94: 'english/vocabulary/one-word-substitution',
        95: 'reasoning-and-aptitude/verbal-reasoning', 96: 'reasoning-and-aptitude/verbal-reasoning',
        97: 'reasoning-and-aptitude/verbal-reasoning', 98: 'reasoning-and-aptitude/series',
        99: 'english/comprehension', 100: 'reasoning-and-aptitude',
    }[n]


def tag_fields(path, taxonomy):
    fields = {'subject_id': '', 'topic_id': None, 'subtopic_id': None}
    while path:
        node = taxonomy[path]
        assert node['active'], path
        fields[node['level'] + '_id'] = path
        path = node['parent_id']
    assert fields['subject_id']
    return fields


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review-root', type=Path, required=True)
    args = parser.parse_args(); root = args.review_root
    before = json.loads((root/'before.json').read_text())
    geometry = json.loads((root/'pages/geometry-checks.json').read_text())
    taxonomy = {t['id']: t for t in before['taxonomy']}
    by_name = {Path(d['source_id']).name: d for d in before['drafts']}
    base_tags = {}; matches = []
    for stem, classify in [('general-english', english), ('gs-i', gs1), ('gs-ii', gs2), ('gs-iii', gs3)]:
        a = by_name[stem+'-series-a.pdf']; b = by_name[stem+'-series-b.pdf']
        index = {}
        for q in a['payload']['questions']:
            key = signature(q); assert key not in index
            index[key] = q; base_tags[q['id']] = classify(q)
        used = set()
        for q in b['payload']['questions']:
            source = index[signature(q)]; assert source['id'] not in used
            used.add(source['id']); base_tags[q['id']] = base_tags[source['id']]
            matches.append({'paper': stem, 'a': source['number'], 'b': q['number'],
                            'punctuation_variant': source['question'] != q['question']})
        assert len(used) == len(index)
    common = ['english/comprehension', 'english', 'english', 'english/comprehension',
              'english/sentence-correction', 'english/grammar/articles',
              'english/vocabulary/one-word-substitution', 'english/grammar',
              'english/grammar/prepositions', 'english/grammar']
    essay = ['computer-science/networking', 'general-studies/mizoram', 'general-studies/mizoram',
             'general-studies/indian-polity', 'general-studies/indian-economy',
             'general-studies/indian-polity', 'general-studies/mizoram', 'general-studies/mizoram']
    proposal = {'authorization': 'User Go: source fidelity, instructions and approved taxonomy review of the 756 Gazetted drafts; draft saves only.',
                'drafts': [], 'booklet_classification_matches': matches,
                'scope': 'AI-assisted source/transcription and primary learning classification review. All 104 source pages visually inspected. This is not independent human approval, answer solving, or verification of the truth of every printed premise.'}
    for old in before['drafts']:
        p = copy.deepcopy(old['payload']); name = Path(old['source_id']).name
        geo = next(d for d in geometry['drafts'] if d['id'] == old['id'])
        gqs = {q['id']: q for q in geo['questions']}
        cover = old['pages'][0]['text']
        if name.startswith('gs-'):
            context = 'Time Allowed : 2 hours. Maximum Marks : 200.\n'
            for num in (4, 8):
                part = re.search(r'(?ms)^\s*'+str(num)+r'\. (.*?)(?=^\s*\d\. |\Z)', cover).group(1)
                context += re.sub(r'\s+', ' ', part).strip().rstrip('*').strip()+'\n'
        elif name.startswith('general-english'):
            context = 'Time Allowed : 3 hours. Maximum Marks : 100.\n'
        elif name == 'general-essay.pdf': context = 'Time Allowed : 3 hours. FM : 100.\n'
        else: context = 'Time Allowed : 3 hours. FM : 100. PM : 40.\n'
        changes = []; crops = []
        for q, oq in zip(p['questions'], old['payload']['questions']):
            path = base_tags.get(q['id'])
            if path is None: path = (essay if name == 'general-essay.pdf' else common)[int(q['number'])-1]
            q.update(tag_fields(path, taxonomy)); q['direction'] = context + q['direction']
            if name.startswith('general-english') and q['type'] == 'mcq':
                q['direction'] = context + 'There will be penalty (negative marking). For each incorrect answer in the MCQ, one-third (l/3rd) of the marks assigned to that question will be deducted.\n' + oq['direction']
            q['direction'] = q['direction'].replace('(l/3rd)', '(1/3rd)').strip()
            if name.startswith('gs-ii-') and 'polymer banknote trial' in q['question']:
                assert q['options'][0] == 'The trial will cover 10 and 20 denominations, alongside existing paper notes.'
                assert q['options'][2] == 'The trial will initially focus on 500 and 2,000 denominations.'
                q['options'][0] = 'The trial will cover ₹ 10 and ₹ 20 denominations, alongside existing paper notes.'
                q['options'][2] = 'The trial will initially focus on ₹ 500 and ₹ 2,000 denominations.'
            if name.startswith('gs-ii-') and 'The Digital Rupee (e )' in q['question']:
                q['question'] = q['question'].replace('(e )', '(e₹)')
            if name.startswith('gs-iii-') and 'A television and a washing machine were sold for 12500' in q['question']:
                q['question'] = q['question'].replace('for 12500', 'for ₹ 12500')
            gq = gqs[q['id']]
            printed_defect = name.startswith('general-english') and q['question'].startswith('They will have finished ploughing')
            if (gq['graphics'] and not q['figure_job']) or printed_defect:
                rects = [x for x in gq['rectangles'] if x['bbox'][3]-x['bbox'][1] > 15]
                assert len(rects) == 1, (name, q['number'], rects)
                rect = rects[0]
                # Full width avoids clipping wide option layouts; the vertical
                # region contains this task and its complete diagram/options.
                crops.append({'number': q['number'], 'question_id': q['id'], 'page': rect['page'],
                              'bbox': rect['bbox'], 'reason': 'Printed option defect evidence' if printed_defect else 'Preserve source graphics/symbols/emphasis'})
            delta = {key: {'before': oq[key], 'after': q[key]} for key in q if q[key] != oq[key]}
            assert not any(key in delta for key in ('id','number','page','type','passage','answer_index','answer_source','key_page','explanation'))
            assert q['answer_index'] is None and q['answer_source'] == 'none' and q['key_page'] is None and not q['explanation']
            changes.append({'id':q['id'], 'number':q['number'], 'classification':path, 'changed_fields':list(delta),
                            'literal_source_repairs':{k:v for k,v in delta.items() if k in ('question','options')}})
        p['identity_note'] = old['payload']['identity_note'].split('AI-assisted text segmentation only;')[0].strip() + ' AI-assisted source and primary-tag review completed 2026-11-04: native PDF text/option-order checks and visual inspection of all source pages; cover context and source crops retained. Printed wording/options preserved except visually confirmed omitted ₹ glyphs. Printed premises and answers are not certified; no keys, solutions or human sign-offs supplied. Independent reviewer approval remains required before publication.'
        if name.startswith('general-english'):
            defect = 'B52' if p['booklet']=='A' else 'B16'
            p['identity_note'] += ' Part A1–A3 and Part B1–B66 remain separate (69 tasks, 100 marks). REVIEWER ATTENTION: '+defect+' (will have finished ploughing) prints no Future perfect option; original options retained and answer unset. A2 composition remains subject-only because no approved writing topic exists.'
        if name.startswith('gs-iii'):
            p['identity_note'] += ' Three visual/spatial tasks remain Reasoning subject-only because no approved visual reasoning topic exists.'
        if name == 'general-essay.pdf':
            p['identity_note'] += ' Essay learning tags follow each printed theme; unit choice, word limits and marks remain in directions.'
        if 'COMMON.pdf' in name:
            p['identity_note'] += ' Q2 memorandum and Q3 essay remain English subject-only because no approved writing topic exists. Linked to the registered empty original '+p['target_paper_id']+'; preserve this identity.'
        assert len(p['identity_note']) <= 3000
        proposal['drafts'].append({'id':old['id'], 'source_id':old['source_id'], 'source_sha256':old['source_sha256'],
                                   'expected_version':old['version'], 'expected_payload_hash':old['payload_hash'],
                                   'payload':p, 'changes':changes, 'crops':crops})
    (root/'proposal.json').write_text(json.dumps(proposal,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'drafts':len(proposal['drafts']), 'questions':sum(len(d['changes'])for d in proposal['drafts']),
                      'new_crops':sum(len(d['crops'])for d in proposal['drafts']),
                      'tag_changes':sum(any(k in q['changed_fields']for k in ('subject_id','topic_id','subtopic_id'))for d in proposal['drafts']for q in d['changes']),
                      'source_repairs':[{ 'source':Path(d['source_id']).name,'number':q['number'],'repairs':q['literal_source_repairs']}for d in proposal['drafts']for q in d['changes']if q['literal_source_repairs']],
                      'subject_only':[{'source':Path(d['source_id']).name,'number':q['number'],'subject':q['classification']}for d in proposal['drafts']for q in d['changes']if '/'not in q['classification']]},ensure_ascii=False,indent=2))


if __name__ == '__main__': main()
