"""Printed numbering and numeric options must survive source-only restoration."""
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    'mcs_restore', Path(__file__).resolve().parents[2] / 'scripts/restore-mcs-recent-papers.py')
RESTORE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RESTORE)


def booklet():
    return [f'{n}. Synthetic question {n}?\n (a) 22     (b) 33\n (c) 44     (d) 12\n'
            for n in range(1, 101)]


def test_cover_page_break_and_numeric_answers():
    questions = booklet()
    text = ('QUESTION BOOKLET\nINSTRUCTIONS\n1. Read carefully.\n2. All items required.\f'
            + ''.join(questions[:11]) + '\fPaper-I (C) -2- CSP : 23\n'
            + ''.join(questions[11:]))
    rows = RESTORE.extract(text)
    assert len(rows) == 100
    assert rows[0]['qnum'] == 1 and rows[0]['page'] == 2
    assert rows[11]['qnum'] == 12 and rows[11]['page'] == 3
    assert rows[11]['options'] == ['22', '33', '44', '12']
    assert all(q['valid_options'] for q in rows)


def test_numbered_statements_are_not_new_questions():
    questions = booklet()
    questions[0] = '1. Consider these statements:\n 1. First statement.\n 2. Second statement.\n (a) One (b) Two (c) Both (d) Neither\n'
    rows = RESTORE.extract(''.join(questions))
    assert '2. Second statement.' in rows[0]['question']
    assert rows[1]['question'] == 'Synthetic question 2?'


def test_figure_only_choices_stay_unresolved_without_losing_next_question():
    questions = booklet()
    questions[57] = '58. Consider the following figures and choose the next diagram:\n\n'
    rows = RESTORE.extract(''.join(questions))
    assert not rows[57]['valid_options']
    assert rows[57]['options'][0] == 'See printed option A in the source image'
    assert rows[58]['qnum'] == 59


def test_incomplete_source_is_rejected_instead_of_padding():
    with pytest.raises(ValueError, match='found 99'):
        RESTORE.extract(''.join(booklet()[:-1]))
