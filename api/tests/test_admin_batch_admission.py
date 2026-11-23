"""Admission rules for the guarded batch publisher (`scripts/admin_tag_batch.py`).

Phase V.20 (§VIII.5.2 #4) widened the batch from taxonomy-only to taxonomy-or-explanation
so that a 20-item explanation batch stops costing 20 full `sync-bank.sh` runs. These tests
pin the gate that was widened, and the ones that must stay shut.

They are deliberately pure: every assertion here fires in the validation loop, which runs
before the bank lock, `check_candidate` and any file access, so no bank, no protection
baseline and no database are involved. The publication itself is NOT exercised — that needs
Oracle, and the DEVLOG records it as unverified.
"""
from __future__ import annotations

import pytest

from admin_tag_batch import BATCH_PATCH_KEYS, apply_admin_tag_batch
from review_bank_store import digest

ADMISSION = 'Only immutable final admin tag or explanation corrections qualify'
NO_BANK = '/nonexistent-bank-for-admission-tests/bank.json'


def _pub(pid, kind, patch, *, canonical=None, appearance=None, payload_kind=None):
    canonical = canonical or ('cq_' + pid)
    appearance = appearance or ('ap_' + pid)
    manifest = {
        'schema': 1,
        'admin_edit': {'id': 'adm_' + pid, 'actor_id': 'user_1', 'kind': kind},
        'payload': {
            'kind': payload_kind or kind,
            'canonical_id': canonical,
            'appearance_id': appearance,
            'patch': patch,
        },
        'baseline': {'record': {'id': appearance}},
        'documents': [],
        'bank_sha256': '0' * 64,
    }
    return {'id': pid, 'manifest': manifest, 'manifest_hash': digest(manifest)}


def _run(pubs):
    # locked=True skips bank_lock so a rejection surfaces as its own ValueError rather
    # than a lock error on a path that does not exist.
    return apply_admin_tag_batch(NO_BANK, '/nonexistent-bank-for-admission-tests', pubs,
                                 dry_run=True, locked=True)


def test_patch_key_map_is_the_whole_allowlist():
    assert BATCH_PATCH_KEYS == {
        'taxonomy': {'classification', 'relatedClassifications'},
        'explanation': {'explanation'},
    }


def test_explanation_batches_are_admitted():
    """The V.20 change. It must get PAST admission — it then fails on the missing bank,
    which is a different error and is all this test claims."""
    pubs = [_pub('p1', 'explanation', {'explanation': 'A worked explanation of the answer.'}),
            _pub('p2', 'explanation', {'explanation': 'Another worked explanation here.'})]
    with pytest.raises(Exception) as exc:
        _run(pubs)
    assert ADMISSION not in str(exc.value)
    assert 'exactly one correction kind' not in str(exc.value)


def test_taxonomy_batches_are_still_admitted():
    pubs = [_pub('p1', 'taxonomy', {'classification': {'subject_id': 'english'}})]
    with pytest.raises(Exception) as exc:
        _run(pubs)
    assert ADMISSION not in str(exc.value)


def test_transcription_is_refused_and_still_publishes_one_at_a_time():
    """A typo fix keeps its own receipt; it is not batchable."""
    with pytest.raises(ValueError, match=ADMISSION):
        _run([_pub('p1', 'transcription', {'question': 'Corrected question text'})])


def test_source_reference_is_refused():
    with pytest.raises(ValueError, match=ADMISSION):
        _run([_pub('p1', 'source_reference', {'page': 12})])


def test_an_explanation_patch_may_not_smuggle_another_field():
    with pytest.raises(ValueError, match=ADMISSION):
        _run([_pub('p1', 'explanation',
                   {'explanation': 'A worked explanation.', 'question': 'Rewritten stem'})])


def test_payload_kind_must_match_the_admin_edit_kind():
    with pytest.raises(ValueError, match=ADMISSION):
        _run([_pub('p1', 'explanation', {'explanation': 'A worked explanation.'},
                   payload_kind='taxonomy')])


def test_kinds_may_not_be_mixed_in_one_batch():
    pubs = [_pub('p1', 'explanation', {'explanation': 'A worked explanation here.'}),
            _pub('p2', 'taxonomy', {'classification': {'subject_id': 'english'}})]
    with pytest.raises(ValueError, match='exactly one correction kind'):
        _run(pubs)


def test_a_tampered_manifest_hash_is_refused():
    pub = _pub('p1', 'explanation', {'explanation': 'A worked explanation here.'})
    pub['manifest']['payload']['patch']['explanation'] = 'Swapped after hashing.'
    with pytest.raises(ValueError, match=ADMISSION):
        _run([pub])


def test_the_same_question_may_not_appear_twice():
    pubs = [_pub('p1', 'explanation', {'explanation': 'First worked explanation.'}, canonical='cq_same'),
            _pub('p2', 'explanation', {'explanation': 'Second worked explanation.'}, canonical='cq_same')]
    with pytest.raises(ValueError, match='Choose each shared question once'):
        _run(pubs)


@pytest.mark.parametrize('count', [0, 21])
def test_the_one_to_twenty_cap_is_unchanged(count):
    pubs = [_pub('p%d' % i, 'explanation', {'explanation': 'Worked explanation %d here.' % i})
            for i in range(count)]
    with pytest.raises(ValueError, match='1–20 exact decisions'):
        _run(pubs)
