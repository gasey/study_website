import copy
import importlib.util
import json
import tempfile
import threading
import unittest
from pathlib import Path

from tagging_queue_store import Store, digest, validate_candidates

spec = importlib.util.spec_from_file_location('audit', Path(__file__).with_name('audit-review-coverage.py'))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def inventory(count=4):
    return {'exported_at': 'today', 'documents': [{'id': 'doc', 'paper_id': 'paper', 'sha256': 'hash'}],
            'appearances': [{'id': 'a' + str(i), 'canonical_id': 'q' + str(i), 'paper_id': 'paper',
                             'page': 1, 'is_primary': True} for i in range(count)]}


def packet(rows):
    return {'taxonomy': [{'id': 'english', 'parent_id': None, 'level': 'subject', 'active': True},
                         {'id': 'english/grammar', 'parent_id': 'english', 'level': 'topic', 'active': True}],
            'items': [{'canonical_id': r['canonical_id'], 'appearance_id': r['appearance_id'],
                       'snapshot': {'record': {'classification': {'subject_id': 'english', 'topic_id': None, 'subtopic_id': None}}},
                       'source_fingerprint': 'fresh',
                       'documents': [{'id': 'doc', 'sha256': 'hash'}]} for r in rows]}


def candidate(item):
    return {'canonical_id': item['canonical_id'], 'appearance_id': item['appearance_id'],
            'reviewer_model': 'test-fixture', 'reviewer_tool': 'unittest',
            'source_fingerprint': 'fresh', 'policy_version': 'study-tagging-v1', 'review_status': 'pending',
            'action': 'keep', 'current_primary': item['snapshot']['record']['classification'],
            'proposed_primary': item['snapshot']['record']['classification'], 'proposed_related': [],
            'rationale': 'The inspected source tests a broad English skill.', 'tested_skill': 'English usage',
            'source_evidence': {'document_id': 'doc', 'sha256': 'hash', 'physical_page': 1,
                                'inspected': True, 'note': 'Fixture evidence only, not a real inspection.'},
            'context_candidate': {'time_behavior': 'static', 'reference_basis': 'unknown'},
            'context_reason': 'Static language task', 'source_issues': [], 'alternatives': [],
            'taxonomy_gap': None, 'owner_question': None}


class CoordinationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'queue.sqlite'
        self.store = Store(self.path)
        self.store.sync(inventory(), {'canonical': [], 'appearance': []}, [], audit.family)

    def tearDown(self):
        self.store.db.close()
        self.tmp.cleanup()

    def claim(self, **kw):
        return self.store.claim(kw.get('worker', 'worker'), 'test-model', 'new', kw.get('size', 2), packet,
                                kw.get('pid'), kw.get('token'))

    def test_simultaneous_workers_get_disjoint_targets(self):
        barrier = threading.Barrier(2)
        results, errors = [], []
        def work(name):
            s = Store(self.path)
            try:
                barrier.wait(timeout=10)
                results.append(s.claim(name, 'test', 'new', 2, packet))
            except Exception as e:
                errors.append(e)
            finally:
                s.db.close()
        threads = [threading.Thread(target=work, args=(str(i),)) for i in range(2)]
        for t in threads: t.start()
        for t in threads: t.join(timeout=20)
        self.assertEqual(errors, [])
        self.assertEqual(len(results), 2)
        ids = [{i['canonical_id'] for i in r['packet']['items']} for r in results]
        self.assertFalse(ids[0] & ids[1])
        self.assertEqual(len(ids[0] | ids[1]), 4)

    def test_lost_claim_response_retry_is_idempotent(self):
        first = self.claim(pid='known', token='secret')
        second = self.claim(pid='known', token='secret')
        self.assertEqual(first['packet'], second['packet'])
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM reservations').fetchone()[0], 2)
        with self.assertRaises(ValueError): self.claim(pid='known', token='wrong')

    def test_failed_source_fetch_rolls_back_claim(self):
        def fail(rows): raise ValueError('database unavailable')
        with self.assertRaises(ValueError): self.store.claim('worker', 'model', 'new', 2, fail)
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM packets').fetchone()[0], 0)
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM targets WHERE state='ready'").fetchone()[0], 4)

    def test_resume_preserves_draft_and_does_not_expire(self):
        r = self.claim()
        pid = r['packet']['packet_id']
        self.store.save(pid, r['token'], [{'partial': True}])
        self.store.db.execute('UPDATE packets SET touched=0')
        with self.assertRaises(ValueError): self.claim()
        self.assertEqual(self.store.resume(pid, r['token'])['draft'], [{'partial': True}])
        with self.assertRaises(ValueError): self.store.save(pid, 'wrong', [])

    def test_submission_retry_and_failed_validation_preserve_reservations(self):
        r = self.claim()
        pid, token, p = r['packet']['packet_id'], r['token'], r['packet']
        candidates = [candidate(i) for i in p['items']]
        bad = copy.deepcopy(candidates); bad[0]['source_fingerprint'] = 'old'
        validate = lambda p, c: validate_candidates(p, c, p)
        with self.assertRaises(ValueError): self.store.submit(pid, token, bad, validate)
        self.assertEqual(self.store.resume(pid, token)['state'], 'claimed')
        self.store.submit(pid, token, candidates, validate)
        self.assertTrue(self.store.submit(pid, token, candidates, validate)['idempotent'])
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM reservations').fetchone()[0], 2)
        self.store.sync(inventory(), {'canonical': [], 'appearance': []}, [], audit.family)
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM targets WHERE state='submitted'").fetchone()[0], 2)

    def test_exclusions_and_followups_survive_other_checkouts(self):
        f = {'canonical_id': 'q0', 'appearance_id': 'a0', 'kind': 'blocked'}
        self.store.sync(inventory(), {'canonical': ['q0', 'q1'], 'appearance': []}, [f], audit.family)
        self.store.sync(inventory(), {'canonical': [], 'appearance': []}, [], audit.family)
        self.assertEqual(self.store.db.execute("SELECT lane,state FROM targets WHERE canonical_id='q0'").fetchone()[:], ('followup', 'ready'))
        self.assertEqual(self.store.db.execute("SELECT state FROM targets WHERE canonical_id='q1'").fetchone()[0], 'excluded')

    def test_canonical_and_booklet_duplicates_are_scheduled_once(self):
        inv = inventory(1)
        inv['appearances'][0]['paper_id'] = 'Exam Booklet A.pdf'
        inv['appearances'] += [{'id': 'a-alt', 'canonical_id': 'q-alt', 'paper_id': 'Exam Booklet B.pdf', 'page': 1},
                               {'id': 'a-repeat', 'canonical_id': 'q0', 'paper_id': 'other.pdf', 'page': 1}]
        self.store.sync(inv, {'canonical': [], 'appearance': []}, [], audit.family)
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM targets WHERE present=1').fetchone()[0], 2)
        self.assertEqual(self.store.db.execute("SELECT state FROM targets WHERE canonical_id='q-alt'").fetchone()[0], 'alternate')

    def test_live_completion_supersedes_old_followup_report(self):
        inv = inventory(); inv['completed_ids'] = ['q0']
        f = {'canonical_id': 'q0', 'appearance_id': 'a0', 'kind': 'blocked'}
        self.store.sync(inv, {'canonical': [], 'appearance': []}, [f], audit.family)
        self.assertEqual(self.store.db.execute("SELECT lane,state FROM targets WHERE canonical_id='q0'").fetchone()[:], ('new', 'excluded'))

    def test_release_keeps_drafts_and_defer_is_not_reclaimed(self):
        r = self.claim(); pid = r['packet']['packet_id']
        self.store.save(pid, r['token'], {'partial': 'work'})
        self.store.release(pid, r['token'], 'Missing registered PDF evidence', defer=True)
        self.assertEqual(self.store.resume(pid, r['token'])['draft'], {'partial': 'work'})
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM reservations').fetchone()[0], 0)
        self.store.sync(inventory(), {'canonical': [], 'appearance': []}, [], audit.family)
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM targets WHERE state='deferred'").fetchone()[0], 2)


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.packet = packet([{'canonical_id': 'q', 'appearance_id': 'a'}])
        self.c = candidate(self.packet['items'][0])

    def validate(self, c=None, fresh=None):
        validate_candidates(self.packet, [c or self.c], fresh or self.packet)

    def test_valid_keep_and_hold(self):
        self.validate()
        c = copy.deepcopy(self.c)
        c.update(action='hold', proposed_primary=None, source_evidence={'inspected': False},
                 source_issues=['Missing exact original page'])
        self.validate(c)

    def test_changed_source_document_and_mismatched_ids_rejected(self):
        for field in ('source_fingerprint', 'documents'):
            fresh = copy.deepcopy(self.packet)
            fresh['items'][0][field] = 'changed'
            with self.assertRaises(ValueError): self.validate(fresh=fresh)
        c = copy.deepcopy(self.c); c['appearance_id'] = 'other'
        with self.assertRaises(ValueError): self.validate(c)

    def test_invalid_path_false_keep_uninspected_and_missing_context_rejected(self):
        changes = [dict(proposed_primary={'subject_id': 'gk-gs', 'topic_id': None, 'subtopic_id': None}),
                   dict(action='retag'), dict(source_evidence={'inspected': False}),
                   dict(context_candidate={'time_behavior': 'dated-event', 'reference_basis': 'unknown'})]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                c = copy.deepcopy(self.c); c.update(change); self.validate(c)


if __name__ == '__main__':
    unittest.main()
