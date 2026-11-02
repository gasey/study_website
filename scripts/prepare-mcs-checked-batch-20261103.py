#!/usr/bin/env python3
"""Prepare the checked 80 explanations after their one exact source prerequisite."""
import argparse,copy,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];PACKET=ROOT/'docs/sources/mcs-checked-explanations-20261103.json'
s=importlib.util.spec_from_file_location('mcs_checked',ROOT/'scripts/prepare-mcs-completion-explanations.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def prepare(packet,bank,root,phase):
 if phase not in {'tree','explanations'}or len(packet['items'])!=80:raise ValueError('Require the exact checked phase and eighty-item scope')
 if phase=='explanations':
  request,identical=m.prepare(packet,bank,root)
  return request,identical
 trees=[i for i in packet['items']if i['required_source_patch']]
 if len(trees)!=1 or trees[0]['appearance_id']!='0eed0b2ebf96f8e03af7':raise ValueError('Only the inspected tree annotation is a source prerequisite')
 item=trees[0];original=item['reviewed_raw_record'];patch=item['required_source_patch'];old='( 3  1.73)'
 if not original['question'].endswith(old)or patch!={'question':original['question'][:-len(old)]+'(√3 = 1.73)'}:raise ValueError('Unreviewed source change')
 projected=copy.deepcopy(bank)
 q=next(q for q in projected['questions']if q['id']==item['appearance_id']);q.update(patch)
 # The existing shared verifier checks exact full source/predecessor, PDF hash,
 # preserved answer/provenance/context, empty explanation and source eligibility.
 subset=copy.deepcopy(packet);subset['items']=[item];checked,_=m.prepare(subset,projected,root)
 if len(checked['items'])!=1:raise ValueError('Exact source prerequisite already completed or changed')
 reason='Coordinator visually checked the exact original PDF page: restore only the printed square-root/equality annotation, √3 = 1.73. Preserve all question context, ordered choices, answer/key provenance, holds and learner history. No explanation or human certification is added in this source phase.'
 proposal=checked['items'][0]['proposal'];proposal.update(kind='transcription',patch=patch,title='Restore printed square-root approximation in MCS tree question',rationale=reason)
 for evidence in proposal['evidence']:evidence['note']=reason
 entry=checked['items'][0];entry['expected_source']=item['expected_source'];entry['reason']=reason
 return dict(operation='source-batch',owner_email=checked['owner_email'],authorization=checked['authorization'],items=[entry]),[]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--phase',required=True,choices=['tree','explanations']);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if not a.output.resolve().is_relative_to(ROOT/'reports'):p.error('Write reports under reports/')
 req,identical=prepare(json.loads(PACKET.read_text()),json.loads((m.BANK_ROOT/'bank/mpsc_bank_v2.json').read_text()),m.BANK_ROOT,a.phase);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(req,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(items=len(req['items']),identical=len(identical),publication=False)))
if __name__=='__main__':main()
