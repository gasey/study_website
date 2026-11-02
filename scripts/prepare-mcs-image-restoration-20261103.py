#!/usr/bin/env python3
"""Prepare exact-source image/locator repairs and their separate explanations."""
import argparse,copy,hashlib,json
from pathlib import Path
from review_bank_store import record,digest
ROOT=Path(__file__).resolve().parents[1];BANK_ROOT=ROOT.parent/'mpsc-question-bankv2';PACKET=ROOT/'docs/sources/mcs-image-restoration-20261103.json'
def prepare(packet,bank,root,phase):
 if phase not in {'images','locators','explanations'}:raise ValueError('Unknown phase')
 root=Path(root).resolve();by={q['id']:q for q in bank['questions']};items=[]
 if len(packet['items'])!=9 or len({i['canonical_id']for i in packet['items']})!=9:raise ValueError('Require nine distinct inspected targets')
 for item in packet['items']:
  q=by[item['appearance_id']];original=item['original_raw_record'];doc=item['source_document'];pdf=(root/doc['source_file']).resolve();image=(root/item['figure_image']).resolve();page=item['physical_pdf_page']
  if(digest(original)!=item['baseline_sha256']or record(original)!=item['expected_source']or doc['paper_id']!=q['paperId']or not pdf.is_relative_to(root/'pdfs')or not pdf.is_file()or hashlib.sha256(pdf.read_bytes()).hexdigest()!=doc['sha256']or not image.is_relative_to(root/'images/page-renders')or not image.is_file()or hashlib.sha256(image.read_bytes()).hexdigest()!=item['figure_sha256']or image.stem!=item['figure_sha256']or type(page)is not int or page<1):raise ValueError('Inspected source or content-addressed asset changed')
  expected=copy.deepcopy(original)
  if phase!='images':expected.update(hasDiagram=True,figureImage=item['figure_image'])
  if phase=='explanations':expected['page']=page
  current=copy.deepcopy(q);current.pop('reviewPublicationId',None);expected.pop('reviewPublicationId',None)
  if current!=expected:raise ValueError('Exact source predecessor changed: '+q['id'])
  if phase=='locators'and original.get('page')==page:continue
  if phase=='images':kind='transcription';patch=dict(hasDiagram=True,figureImage=item['figure_image'])
  elif phase=='locators':kind='source_reference';patch=dict(page=page)
  else:
   opts=q.get('options')or[];ai=q.get('answerIndex')
   if((q.get('explanation')or'').strip()or q.get('type')!='mcq'or type(ai)is not int or not 0<=ai<len(opts)or len(opts)!=4 or any(not isinstance(o,str)or not o.strip()for o in opts)or len(set(opts))!=4 or q.get('answerSource')not in {'official','key','derived'}or len(item['explanation'].strip())<20):raise ValueError('Explanation requires empty text and a usable preserved answer')
   kind='explanation';patch=dict(explanation=item['explanation'])
  reason=item['source_review']+' Separate audited '+phase+' phase; retain all holds, source identities, ordered options, keys, account access and learner history. No human sign-off or independent peer certification is claimed.'
  proposal=dict(kind=kind,canonical_id=item['canonical_id'],appearance_id=q['id'],subject_id=record(q)['classification']['subject_id'],title='Restore MCS source Q'+str(q['qnum']),patch=patch,rationale=reason,evidence=[dict(kind='paper',document_id=doc['id'],sha256=doc['sha256'],page=page,note=reason)])
  items.append(dict(proposal=proposal,expected_source=record(q),paper_id=q['paperId'],source_sha=doc['sha256'],reason=reason))
 if len(items)!=(4 if phase=='locators'else 9):raise ValueError('Checked scope changed')
 return dict(operation='source-batch',owner_email='hruaitluangasailo20@gmail.com',authorization='Owner authorized continued exact-source MCS repairs and checked explanations through ordinary audited staff publication. Preserve editorial protection, source/key provenance, holds and learner history; no exemption or human review attribution.',items=items)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--phase',required=True,choices=['images','locators','explanations']);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if not a.output.resolve().is_relative_to(ROOT/'reports'):p.error('Write requests under reports/')
 req=prepare(json.loads(PACKET.read_text()),json.loads((BANK_ROOT/'bank/mpsc_bank_v2.json').read_text()),BANK_ROOT,a.phase);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(req,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(prepared=len(req['items']),publication=False)))
if __name__=='__main__':main()
