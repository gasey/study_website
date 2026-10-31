import importlib.util
from pathlib import Path
import pytest

SPEC = importlib.util.spec_from_file_location('mcs_numbering', Path(__file__).resolve().parents[2] / 'scripts/audit-mcs-historical-numbering.py')
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def test_cover_statements_figure_only_and_bare_number_keep_physical_pages():
    text = ('QUESTION BOOKLET INSTRUCTIONS\n1. Read carefully\n2. Use pen\f'
            '1. Consider these statements\n1. First premise\n2. Second premise\n'
            '(a) A (b) B (c) C (d) D\n2.\n(a) 1 (b) 2 (c) 3 (d) 4\f'
            '3 Weightlessness\n(a) A (b) B (c) C (d) D')
    rows = AUDIT.source_positions(text, 3)
    assert [(r['qnum'], r['page']) for r in rows] == [(1, 2), (2, 2), (3, 3)]


@pytest.mark.parametrize('text', [
    '1. Question\n(a) A (b) B (c) C (d) D\n3. Question\n(a) A (b) B (c) C (d) D',
    '1. Question\n(a) A (b) B (c) C (d) D\n2. Question\n(a) A (b) B (c) C',
])
def test_incomplete_source_never_becomes_a_complete_paper(text):
    with pytest.raises(ValueError):
        AUDIT.source_positions(text, 2)


def test_missing_duplicate_and_wrong_page_are_reported_without_mutation():
    records = [
        {'id': 'old', 'qnum': 1, 'page': 2, 'question': 'The question', 'options': ['A', 'B'], 'answerSource': 'inferred'},
        {'id': 'copy', 'qnum': 1, 'page': 2, 'question': 'The\n question', 'options': ['A', 'B'], 'answerSource': 'derived'},
        {'id': 'offset', 'qnum': 3, 'page': 2, 'question': 'Other', 'options': ['C', 'D']},
    ]
    before = AUDIT.digest(records)
    issues = AUDIT.compare_records(records, [{'qnum': n, 'page': 3} for n in range(1, 4)])
    assert AUDIT.digest(records) == before
    duplicate = next(i for i in issues if i['kind'] == 'duplicate-printed-position')
    assert duplicate['whitespace_normalized_text_and_ordered_options_agree']
    assert {r['answer_source'] for r in duplicate['records']} == {'inferred', 'derived'}
    assert [i['qnum'] for i in issues if i['kind'] == 'missing-source-appearance'] == [2]
    assert len([i for i in issues if i['kind'] == 'physical-page-mismatch']) == 3


def test_same_number_does_not_establish_equivalence_when_options_differ():
    records = [{'id': str(i), 'qnum': 1, 'page': 1, 'question': 'Same', 'options': options}
               for i, options in enumerate([['A', 'B'], ['B', 'A']])]
    issue = AUDIT.compare_records(records, [{'qnum': 1, 'page': 1}])[0]
    assert not issue['whitespace_normalized_text_and_ordered_options_agree']


def test_report_output_cannot_overwrite_the_canonical_bank():
    with pytest.raises(ValueError, match='reports directory'):
        AUDIT.audit(Path('not-read.json'), AUDIT.BANK_ROOT / 'bank/mpsc_bank_v2.json')
