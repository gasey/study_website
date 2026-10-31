import copy
import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('mcs_tags', Path(__file__).resolve().parents[2] / 'scripts/propagate-restored-mcs-tags.py')
TAGS = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(TAGS)


def question(qid, path=None):
    return {'id': qid, 'type': 'mcq', 'question': 'Which number?', 'options': ['One', 'Two', 'Three', 'Four'],
            'answerIndex': None, 'answerSource': 'none', 'classifications': [] if path is None else [
                {'subject_id': path, 'topic_id': None, 'subtopic_id': None, 'is_primary': True,
                 'review_status': 'approved', 'taxonomy_version': 'synthetic'}]}


def test_only_whitespace_case_normalize_and_no_answer_transfer():
    source = question('source', 'arithmetic'); source.update(answerIndex=2, answerSource='official')
    target = question('target'); target['question'] = ' Which\n NUMBER? '
    bank = {'questions': [source, target]}; before = copy.deepcopy(bank)
    plan = TAGS.candidates(bank, {'target'})
    assert len(plan['candidates']) == 1
    assert plan['candidates'][0]['classification']['subject_id'] == 'arithmetic'
    assert 'answerIndex' not in plan['candidates'][0] and bank == before
    target['options'].reverse()
    assert not TAGS.candidates(bank, {'target'})['candidates']


def test_conflicting_unapproved_defective_and_existing_tags_are_not_overwritten():
    a = question('a', 'arithmetic'); b = question('b', 'english'); target = question('target')
    assert TAGS.candidates({'questions': [a, b, target]}, {'target'})['skipped'] == {'conflicting_sources': 1}
    b['classifications'][0]['review_status'] = 'pending'; a['sourceDefect'] = 'unresolved-source'
    assert not TAGS.candidates({'questions': [a, b, target]}, {'target'})['candidates']
    target['classifications'] = copy.deepcopy(b['classifications'])
    assert TAGS.candidates({'questions': [a, target]}, {'target'})['skipped'] == {'already_classified_or_source_issue': 1}
