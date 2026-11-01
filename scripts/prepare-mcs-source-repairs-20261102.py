#!/usr/bin/env python3
"""Prepare only the ten inspected MCS notation/page repairs, without bank writes."""
import argparse,copy,hashlib,json
from pathlib import Path
from review_bank_store import record,digest
ROOT=Path(__file__).resolve().parents[1];BANK_ROOT=ROOT.parent/'mpsc-question-bankv2'
PACKET=ROOT/'docs/sources/mcs-notation-locators-20261102.json'
def prepare(packet,bank,root,phase):
    if phase not in {'transcription','locators'}:raise ValueError('Unknown phase')
    by={q['id']:q for q in bank['questions']};root=Path(root).resolve();items=[]
    for item in packet['items']:
        if item['phase']!=phase:continue
        q=by[item['appearance_id']];doc=item['source_document'];path=(root/doc['source_file']).resolve();patch=item['patch'];original=item['original_raw_record']
        if digest(original)!=item['baseline_sha256']or not path.is_relative_to(root/'pdfs')or hashlib.sha256(path.read_bytes()).hexdigest()!=doc['sha256']or doc['paper_id']!=q['paperId']:raise ValueError('Immutable source evidence changed')
        if set(patch)!=({'question'}if phase=='transcription'else{'page'}):raise ValueError('Only the inspected stem or locator may change')
        if phase=='transcription'and patch['question']not in {'If 5^(2x+1) ÷ 25 = 125, find the value of x.','Evaluate: √(∛(√4096)).'}:raise ValueError('Unreviewed notation')
        current=copy.deepcopy(q);current.pop('reviewPublicationId',None);original=copy.deepcopy(original);original.pop('reviewPublicationId',None)
        predecessor=copy.deepcopy(original)
        for prev in packet['items']:
            if prev is item:break
            if prev['appearance_id']==q['id']:predecessor.update(prev['patch'])
        if current!=predecessor or record(q)!=item['expected_source']:raise ValueError('Exact reviewed predecessor changed')
        reason='Coordinator visually checked the original physical PDF page and printed question. Restore only its exact mathematical notation or page locator; preserve every ordered option, examiner answer/key, source context, hold and learner attempt. No independent peer review is claimed.'
        p=dict(kind='transcription'if phase=='transcription'else'source_reference',canonical_id=item['canonical_id'],appearance_id=q['id'],subject_id=record(q)['classification']['subject_id'],title='Restore MCS source Q'+str(q['qnum']),patch=patch,rationale=reason,evidence=[dict(kind='paper',document_id=doc['id'],sha256=doc['sha256'],page=item['physical_pdf_page'],note=reason)])
        items.append(dict(proposal=p,expected_source=record(q),paper_id=q['paperId'],source_sha=doc['sha256'],reason=reason))
    if len(items)!=(7 if phase=='transcription'else 3):raise ValueError('Require the exact checked scope')
    return dict(operation='source-batch',owner_email='hruaitluangasailo20@gmail.com',authorization='Owner instructed continued MCS corrections using ordinary staff quota only, preserving examiner answers, original source identity, holds and learner history.',items=items)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--phase',choices=['transcription','locators'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if not a.output.resolve().is_relative_to(ROOT/'reports'):p.error('Write requests under reports/')
    request=prepare(json.loads(PACKET.read_text()),json.loads((BANK_ROOT/'bank/mpsc_bank_v2.json').read_text()),BANK_ROOT,a.phase);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'items':len(request['items']),'publication':False}))
if __name__=='__main__':main()
