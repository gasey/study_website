"""Regression checks for invalid paths and accidental candidate approval."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("tag_policy", ROOT / "scripts/check-tagging-policy.py")
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class TaggingPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT / "docs/question-tagging-policy.json").read_text())
        self.registry = json.loads((ROOT / "reports/tagging-policy-20261107/live-audit.json").read_text())

    def test_current_examples_are_legal(self):
        self.assertEqual(CHECK.validate(self.policy, self.registry), [])

    def test_display_alias_is_rejected(self):
        self.policy["routes"][0]["path"]["subject_id"] = "gk-gs"
        self.assertTrue(any("display alias" in e for e in CHECK.validate(self.policy, self.registry)))

    def test_wrong_gk_parent_is_rejected(self):
        self.policy["routes"][0]["path"]["subject_id"] = "general-knowledge"
        self.assertTrue(any("invalid level/parent" in e for e in CHECK.validate(self.policy, self.registry)))

    def test_missing_and_inactive_topic_are_rejected(self):
        original = copy.deepcopy(self.policy)
        self.policy["routes"][0]["path"]["topic_id"] = "general-knowledge/current-affairs"
        self.assertTrue(any("missing/inactive" in e for e in CHECK.validate(self.policy, self.registry)))
        node = next(n for n in self.registry["taxonomy"] if n["id"] == "general-studies/current-affairs")
        node["active"] = False
        self.assertTrue(any("missing/inactive" in e for e in CHECK.validate(original, self.registry)))

    def test_model_candidates_cannot_self_approve(self):
        self.policy["candidate_review_status"] = "approved"
        self.assertIn("Model candidates must remain pending", CHECK.validate(self.policy, self.registry))


if __name__ == "__main__":
    unittest.main()
