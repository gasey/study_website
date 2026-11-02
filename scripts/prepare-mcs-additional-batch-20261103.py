#!/usr/bin/env python3
"""Prepare exact printed context, PDF locators, then 93 checked explanations."""
import argparse,copy,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PACKET=ROOT/'docs/sources/mcs-additional-checked-explanations-20261103.json'
s=importlib.util.spec_from_file_location('additional_explanations',ROOT/'scripts/prepare-mcs-completion-explanations.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def prepare(packet,bank,root,phase):
    if phase not in {'contexts','locators','explanations'} or len(packet['items'])!=93:
        raise ValueError('Require the bounded 93-item packet and checked phase')
    if phase=='explanations':return m.prepare(packet,bank,root)
    by={q['id']:q for q in bank['questions']};entries=[]
    for item in packet['items']:
        plan=item['required_source_patch'];context={k:v for k,v in plan.items()if k!='page'}
        if set(context)-{'direction','question'}:raise ValueError('Unreviewed source prerequisite field')
        patch=context if phase=='contexts'else({'page':plan['page']}if 'page'in plan else{})
        if not patch:continue
        original=item['reviewed_raw_record'];expected=copy.deepcopy(original)
        if phase=='locators':expected.update(context)
        current=copy.deepcopy(by[item['appearance_id']])
        # A previous source phase may only have added its audited receipt.
        current.pop('reviewPublicationId',None);expected.pop('reviewPublicationId',None)
        if current!=expected:raise ValueError('Exact source phase predecessor changed: '+item['appearance_id'])
        q=copy.deepcopy(by[item['appearance_id']]);q.update(plan)
        projected={**bank,'questions':[q]}
        subset=copy.deepcopy(packet);subset['items']=[item]
        checked,identical=m.prepare(subset,projected,root)
        if identical or len(checked['items'])!=1:raise ValueError('Source target already explained or changed')
        entry=checked['items'][0];proposal=entry['proposal'];page=item.get('source_context_physical_pdf_page')if phase=='contexts'else item['physical_pdf_page']
        if type(page)is not int or page<1:raise ValueError('Exact original context page required')
        reason='Coordinator visually inspected the hashed original booklet. Restore only the exact printed list/shared instruction.'if phase=='contexts'else'Coordinator visually inspected the hashed original booklet. Correct only the physical PDF page link, preserving printed numbering.'
        reason+=' Preserve ordered choices, examiner answers/key references, classification, holds, account access and learner history. Separate audited source phase; no explanation, peer certification or human sign-off is added.'
        proposal.update(kind='transcription'if phase=='contexts'else'source_reference',patch=patch,title='Restore MCS printed context'if phase=='contexts'else'Correct MCS physical PDF page link',rationale=reason)
        proposal['evidence']=[dict(kind='paper',document_id=item['source_document']['id'],sha256=item['source_document']['sha256'],page=page,note=reason)]
        entry.update(expected_source=m.record(by[item['appearance_id']]),reason=reason);entries.append(entry)
    if len(entries)!=(5 if phase=='contexts'else 13):raise ValueError('Exact checked source scope changed')
    return dict(operation='source-batch',owner_email='hruaitluangasailo20@gmail.com',authorization='Owner scheduled continued checked MCS work with ordinary staff quotas; publish only exact audited source prerequisites and checked explanations, preserving editorial protection, historical keys and learner history.',items=entries),[]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--phase',required=True,choices=['contexts','locators','explanations']);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if not a.output.resolve().is_relative_to(ROOT/'reports'):p.error('Write requests under reports/')
    req,identical=prepare(json.loads(PACKET.read_text()),json.loads((m.BANK_ROOT/'bank/mpsc_bank_v2.json').read_text()),m.BANK_ROOT,a.phase)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(req,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(items=len(req['items']),identical=len(identical),publication=False)))
if __name__=='__main__':main()
