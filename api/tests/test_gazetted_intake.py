"""Read-only preparation must not convert extraction guesses into answers."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('gazetted_intake', Path(__file__).resolve().parents[2] / 'scripts/prepare-gazetted-intake.py')
intake = importlib.util.module_from_spec(spec)
spec.loader.exec_module(intake)


def test_option_rows_preserve_columns_and_article_references():
    stem, options, issue = intake.options_from('Article 39(b) and (c): which?\n  (a) First    (b) Second\n  (c) Third    (d) Fourth')
    assert stem == 'Article 39(b) and (c): which?'
    assert options == ['First', 'Second', 'Third', 'Fourth'] and issue is None


def test_ambiguous_columns_keep_source_text_for_review():
    text = 'Which?\n  (a) First    (b) Second\n       ambiguous continuation\n  (c) Third    (d) Fourth'
    assert intake.options_from(text)[:2] == (text, [])
    assert intake.options_from('Which figure?')[1] == []


def test_single_column_wrapping_is_preserved():
    _, options, issue = intake.options_from('Which?\n  (a) A long\n      first option\n  (b) Two\n  (c) Three\n  (d) Four')
    assert options == ['A long first option', 'Two', 'Three', 'Four'] and issue is None


def test_page_labels_removed_without_removing_numbered_content():
    assert intake.clean('Series - A     - 12 -\n 95. Printed question\n*****') == '95. Printed question'


def test_repeated_or_missing_options_are_not_filled_in():
    for text in ['Which?\n(a) One\n(b) Two\n(d) Four', 'Which?\n(a) Same\n(b) Same\n(c) Three\n(d) Four']:
        assert intake.options_from(text)[1] == []
