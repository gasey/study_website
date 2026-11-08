import importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('coverage',Path(__file__).with_name('audit-review-coverage.py'))
coverage=importlib.util.module_from_spec(spec);spec.loader.exec_module(coverage)
class CoverageTests(unittest.TestCase):
 def write(self,root,name,rows):
  folder=root/'reports'/name;folder.mkdir(parents=True)
  (folder/'pending-candidates.json').write_text(json.dumps(rows))
  items=[{'appearance_id':r['appearance_id'],'source_fingerprint':'fresh','snapshot':{'record':{'classification':{'subject_id':'english'}},'paper':{'id':'Archive/Paper-I Booklet A.pdf'}}} for r in rows]
  (folder/'oracle-packet.json').write_text(json.dumps({'items':items}))
 def row(self,**extra):return {'appearance_id':'a1','canonical_id':'q1','source_fingerprint':'fresh','current_primary':{'subject_id':'english'},'action':'retag','proposed_primary':{'subject_id':'english','topic_id':'english/vocabulary'},'proposed_related':[],**extra}
 def test_coalesces_equal_targets_and_excludes_bad_baselines(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);self.write(root,'tagging-one',[self.row()]);self.write(root,'tagging-two',[self.row(),self.row(appearance_id='a2',canonical_id='q2',current_primary={'subject_id':'gk'})])
   data=coverage.audit(root)
   self.assertEqual(data['unique_questions'],2);self.assertEqual(len(data['effective_candidates']),1);self.assertEqual(len(data['baseline_issues']),1)
   self.assertEqual(len(data['repeated_appearance_candidates']),1)
 def test_differing_proposals_require_bound_resolution(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);a=self.row();b=self.row(proposed_primary={'subject_id':'english','topic_id':'english/comprehension'})
   self.write(root,'tagging-one',[a]);self.write(root,'tagging-two',[b]);data=coverage.audit(root)
   self.assertEqual(len(data['unresolved_conflicts']),1);self.assertEqual(data['effective_candidates'],[])
   resolution=root/'resolved.json';resolution.write_text(json.dumps({'a1':{'proposal_signatures':[coverage.signature(a),coverage.signature(b)],'preferred_file':'reports/tagging-one/pending-candidates.json'}}))
   self.assertEqual(len(coverage.audit(root,resolution)['effective_candidates']),1)
   b['proposed_primary']={'subject_id':'english'};(root/'reports/tagging-two/pending-candidates.json').write_text(json.dumps([b]))
   self.assertEqual(coverage.audit(root,resolution)['effective_candidates'],[])
if __name__=='__main__':unittest.main()
