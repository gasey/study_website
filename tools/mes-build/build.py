"""Build MES from pinned, source-checked inputs; no network or question-bank writes."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'web/src/data/exam-guides/mes.json'


def build():
    archive = json.loads((HERE / 'archive-source.json').read_text())
    syllabus = json.loads((HERE / 'syllabus-source.json').read_text())
    branch_names = [
        ('civil', 'Civil Engineering', 'Civil'),
        ('mechanical', 'Mechanical Engineering', 'Mechanical'),
        ('electrical', 'Electrical Engineering', 'Electrical'),
        ('electronics', 'Electronics & Communication Engineering', 'Electronics'),
        ('computer', 'Computer Science & Engineering', 'Computer Science'),
        ('architecture', 'Architecture', 'Architecture'),
        ('agricultural', 'Agricultural Engineering', 'Agricultural'),
    ]
    sources = [{
        'id': 'regulations-2013',
        'title': 'Mizoram Engineering Service (Competitive Examination) Regulations, 2013 · Gazette Ex-507/2013',
        'url': 'https://mpsc.mizoram.gov.in/uploads/attachments/2026/04/93a34ee88ddcf8904cdf0a2ed3d085a5/mizoram-engineering-service-competitive-examination-rregulations-2013.pdf',
        'checkedOn': '2026-11-12',
    }, {
        'id': 'syllabus-directory', 'title': 'MPSC official direct-recruitment syllabus directory',
        'url': 'https://mpsc.mizoram.gov.in/page/direct-syllabus', 'checkedOn': '2026-11-12',
    }] + archive['sources']
    for subject, filename in [('English I', 'eb7ba83501e9f64ae50ab94be040840e/aesdo-pe-2012-general-english-i.pdf'), ('English II', 'ae2f3b072523c6bea5e0117501b791b9/aesdo-pe-2012-general-english-ii.pdf'), ('Aptitude', 'cec3f9577ccc030ae718bf500fa14a1d/aesdo-pe-2012-general-aptitude-test.pdf')]:
        sources.append({'id': 'legacy-' + subject.lower().replace(' ', '-'), 'title': 'January 2012 P&E · ' + subject + ' · original paper cover', 'url': 'https://mpsc.mizoram.gov.in/uploads/attachments/' + filename, 'checkedOn': '2026-11-12'})
    common = [
        {'id': 'english-2013', 'schemeId': 'regulations-2013', 'branchId': None,
         'title': 'General English', 'marks': 100, 'durationMinutes': 180, 'format': 'Conventional written paper',
         'sourceId': 'regulations-2013', 'sourcePage': 5, 'units': [
             {'id': 'comprehension', 'title': 'Comprehension · 20 marks', 'description': 'Read a given passage and answer questions that test understanding of its meaning and argument.'},
             {'id': 'precis', 'title': 'Précis writing · 20 marks', 'description': 'Condense a passage while preserving its central argument, logical order and meaning.'},
             {'id': 'usage', 'title': 'Usage and vocabulary · 40 marks', 'description': 'Revise English usage and vocabulary. Practise identifying and correcting errors in context.'},
             {'id': 'essay', 'title': 'Short essay · 20 marks', 'description': 'Practise a concise essay with a clear introduction, developed argument and conclusion.'},
         ]},
        {'id': 'gs-2013', 'schemeId': 'regulations-2013', 'branchId': None,
         'title': 'General Studies', 'marks': 100, 'durationMinutes': 180, 'format': 'Objective paper',
         'sourceId': 'regulations-2013', 'sourcePage': 5, 'units': [
             {'id': 'general-awareness', 'title': 'General awareness and socio-economic issues', 'description': 'The regulations prescribe broad general awareness relevant to an engineering career, basic understanding of relevant issues, and analysis of conflicting socio-economic goals. They do not assign unit-wise marks to GS. Use the original papers to guide revision.'}
         ]},
    ]
    # The legacy scheme is an observed sitting, not an invented replacement syllabus.
    for title, marks, minutes, fmt, source in [
        ('General English I', 100, 180, 'Conventional written paper', 'legacy-english-i'),
        ('General English II', 100, 180, 'Conventional written paper', 'legacy-english-ii'),
        ('General Aptitude Test', 50, 60, '50 objective questions, 1 mark each', 'legacy-aptitude'),
    ]:
        common.append({'id': source, 'schemeId': 'legacy-2012', 'branchId': None, 'title': title, 'marks': marks, 'durationMinutes': minutes, 'format': fmt, 'sourceId': source, 'sourcePage': 1, 'units': []})
    module = {
        'schemaVersion': 1, 'id': 'mes', 'title': 'Mizoram Engineering Service',
        'eyebrow': 'MPSC · JUNIOR GRADE · AE / SDO', 'directorySourceId': 'syllabus-directory',
        'description': 'Your branch, your syllabus, your past papers. Prepare for Junior Grade MES (AE/SDO) with source-linked paper plans and a personal revision checklist.',
        'defaultSchemeId': 'regulations-2013', 'defaultBranchId': 'civil',
        'sources': sources,
        'schemes': [
            {'id': 'regulations-2013', 'title': '2013 regulations', 'status': 'verified',
             'description': 'The scheme linked in MPSC’s direct syllabus directory when checked on 12 November 2026. Five written papers: three technical papers of 200 marks, English 100, GS 100; interview 100. Each written paper lasts 3 hours. No replacement competitive-exam scheme was verified. Archive assignments to this scheme are inferred from year unless stated otherwise; check each original booklet and the notification for your recruitment.',
             'sourceIds': ['regulations-2013', 'syllabus-directory'], 'branchIds': [b[0] for b in branch_names], 'interviewMarks': 100},
            {'id': 'legacy-2012', 'title': 'Legacy · January 2012', 'status': 'archive',
             'description': 'The archived P&E sitting has two English papers, a separate aptitude test and three technical papers for each of Electrical, Electronics and Mechanical. English I and II: 100 marks and 3 hours each. Aptitude: 50 marks and 1 hour. These are observations from the original covers, not a verified full legacy syllabus. Use the booklets for technical format and instructions. The 2013 syllabus and progress are kept separate.',
             'sourceIds': ['legacy-english-i', 'legacy-english-ii', 'legacy-aptitude'], 'branchIds': ['mechanical', 'electrical', 'electronics'], 'interviewMarks': None},
        ],
        'branches': [{'id': b[0], 'title': b[1], 'short': b[2]} for b in branch_names],
        'syllabus': common + syllabus, 'archive': archive['papers'],
    }
    assert len(module['archive']) == 159, 'Archive count changed; inspect source additions/removals.'
    assert len(syllabus) == 21 and sum(len(p['units']) for p in syllabus) == 79
    return json.dumps(module, ensure_ascii=False, indent=2) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = build()
    if args.check:
        if not OUT.exists() or OUT.read_text() != data:
            raise SystemExit('MES output is stale. Run python3 tools/mes-build/build.py')
        print('MES catalog is reproducible: 159 papers, 7 branches, 2 scheme records.')
    else:
        OUT.write_text(data)
        print(OUT)
