#!/usr/bin/env python3
"""Prepare checked MCS locator/radical repairs, never mutate the bank or server."""
import argparse,hashlib,json
from pathlib import Path
from review_bank_store import record,digest
ROOT=Path(__file__).resolve().parents[1]
BANK_ROOT=ROOT.parent/'mpsc-question-bankv2'
PACKET=ROOT/'docs/sources/mcs-source-navigation-repairs-20261101.json'

def prepare(packet,bank,bank_root,phase):
    if phase not in {'transcription','source_reference'}:raise ValueError('Choose a supported separate source phase')
    by={q['id']:q for q in bank['questions']};items=[];seen=set()
    bank_root=Path(bank_root).resolve()
    for item in packet['items']:
        if item['kind']!=phase:continue
        aid=item['appearance_id'];q=by[aid];doc=item['source_document'];expected=dict(item['expected_source'])
        if aid in seen:raise ValueError('One repair per target per phase')
        seen.add(aid)
        source=(bank_root/doc['source_file']).resolve()
        if (doc['kind']!='paper' or doc['paper_id']!=q['paperId'] or q['paperId']!=item['paper_id']
                or not source.is_relative_to(bank_root/'pdfs') or not source.is_file()
                or hashlib.sha256(source.read_bytes()).hexdigest()!=doc['sha256']):raise ValueError('Exact reviewed PDF/source identity changed')
        patch=item['patch'];allowed={'page'}if phase=='source_reference'else{'question'}
        if set(patch)!=allowed:raise ValueError('Only the reviewed page or stem field can change')
        if type(item['physical_pdf_page'])is not int or item['physical_pdf_page']<1:raise ValueError('An inspected physical page is required')
        if phase=='source_reference' and patch['page']!=item['physical_pdf_page']:raise ValueError('Locator must name the inspected page')
        if phase=='transcription':
            if '( 3  1.73)'not in expected['question'] or patch['question']!=expected['question'].replace('( 3  1.73)','(√3 = 1.73)'):
                raise ValueError('Only the visually checked radical/equality restoration qualifies')
        # Q89 receives its transcription first. Require that exact predecessor
        # rather than rebasing over arbitrary newly edited text.
        if phase=='source_reference':
            predecessors=[i for i in packet['items']if i['appearance_id']==aid and i['kind']=='transcription']
            for predecessor in predecessors:
                expected.update(predecessor['patch'])
        current=record(q)
        already={**expected,**patch}
        if current==already:continue
        if current!=expected:raise ValueError('Reviewed baseline or predecessor changed: '+aid)
        if phase=='transcription'and digest(q)!=item['baseline_sha256']:raise ValueError('Full raw baseline changed')
        reason=item['reason'];proposal=dict(kind=phase,canonical_id=item['canonical_id'],appearance_id=aid,subject_id=current['classification']['subject_id'],title='Repair MCS source navigation/text Q'+str(q['qnum']),patch=patch,rationale=reason,evidence=[dict(kind='paper',document_id=doc['id'],sha256=doc['sha256'],page=item['physical_pdf_page'],note=reason)])
        items.append(dict(proposal=proposal,expected_source=current,paper_id=q['paperId'],source_sha=doc['sha256'],reason=reason))
    return dict(operation='source-batch',owner_email='hruaitluangasailo20@gmail.com',authorization='Owner requested completion of remaining checked MCS source repairs. Publish only inspected source text or locators through the audited workflow, preserving answers/provenance, all compensation holds, source identity and learner history.',items=items)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--phase',required=True,choices=['transcription','source_reference']);parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
    if not args.output.resolve().is_relative_to(ROOT/'reports'):parser.error('Write requests under reports/')
    request=prepare(json.loads(PACKET.read_text()),json.loads((BANK_ROOT/'bank/mpsc_bank_v2.json').read_text()),BANK_ROOT,args.phase)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(phase=args.phase,prepared=len(request['items']),publication=False)))
if __name__=='__main__':main()
