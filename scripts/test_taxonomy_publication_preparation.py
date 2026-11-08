import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('prepare',Path(__file__).with_name('prepare-owner-taxonomy-run.py'))
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.primary={'subject_id':'english','topic_id':'english/grammar','subtopic_id':None}
        self.existing={'source_bound':True,'primary':self.primary,'related':[]}
        self.snapshot={'record':{}}

    def test_missing_related_means_preserve_snapshot_links(self):
        self.assertTrue(p.completed_matches(self.existing,self.primary,None,self.snapshot))
        self.snapshot['record']['relatedClassifications']=[{'subject_id':'science','topic_id':None,'subtopic_id':None}]
        self.assertFalse(p.completed_matches(self.existing,self.primary,None,self.snapshot))

    def test_different_proposal_or_unbound_completion_is_not_skipped(self):
        other={**self.primary,'topic_id':None}
        self.assertFalse(p.completed_matches(self.existing,other,[],self.snapshot))
        self.assertFalse(p.completed_matches({**self.existing,'source_bound':False},self.primary,[],self.snapshot))
        self.assertFalse(p.completed_matches(None,self.primary,[],self.snapshot))

if __name__=='__main__':unittest.main()
