#!/usr/bin/env python3
"""Prepare the next checked MCS explanations after their exact source repairs."""
import argparse,copy,hashlib,json
from pathlib import Path
from review_bank_store import record,digest
ROOT=Path(__file__).resolve().parents[1]
BANK_ROOT=ROOT.parent/'mpsc-question-bankv2'
PACKET=ROOT/'docs/sources/mcs-completion-explanations-20261101.json'

def prepare(packet,bank,bank_root,offset=0,limit=100):
    if type(offset)is not int or offset<0 or type(limit)is not int or not 1<=limit<=100:raise ValueError('Choose a nonnegative offset and1–100items')
    all_items=packet['items']
    if not 1<=len(all_items)<=200 or len({i['appearance_id']for i in all_items})!=len(all_items)or len({i['canonical_id']for i in all_items})!=len(all_items):raise ValueError('Require at most200 distinct checked appearances and canonical targets')
    by={q['id']:q for q in bank['questions']};papers={p['id']:p for p in bank['papers']};root=Path(bank_root).resolve();items=[];identical=[]
    for item in all_items[offset:offset+limit]:
        q=by[item['appearance_id']];reviewed=item['reviewed_raw_record'];doc=item['source_document'];pid=q['paperId'];plan=item['required_source_patch']
        if (pid not in packet['scope']['paper_ids']or 'MCS Combined'not in pid or papers[pid].get('year')not in(2023,2025)
                or digest(reviewed)!=item['baseline_sha256']or record(reviewed)!=item['expected_source']
                or set(plan)-{'question','page','passage','direction'}):raise ValueError('Reviewed scope or immutable raw source baseline changed')
        expected=copy.deepcopy(reviewed);expected.update(plan)
        if record(expected)!=item['post_source_expected']:raise ValueError('The planned exact source predecessor changed')
        path=(root/doc['source_file']).resolve()
        if doc['kind']!='paper'or doc['paper_id']!=pid or not path.is_relative_to(root/'pdfs')or not path.is_file()or hashlib.sha256(path.read_bytes()).hexdigest()!=doc['sha256']:raise ValueError('Exact inspected source PDF changed')
        text=item['explanation'];page=item['physical_pdf_page'];opts=q.get('options')or[];ai=q.get('answerIndex')
        if (not isinstance(text,str)or len(text.strip())<20 or type(page)is not int or page<1
                or q.get('type')!='mcq'or type(ai)is not int or not 0<=ai<len(opts)or not 2<=len(opts)<=8
                or any(not isinstance(o,str)or not o.strip()for o in opts)or len({o.strip()for o in opts})!=len(opts)
                or q.get('answerSource')not in {'official','key','derived'}or q.get('sourceDefect')in{'duplicate-options','unresolved-source'}
                or q.get('hasDiagram')and(not q.get('figureImage')or not(root/q['figureImage']).is_file())):raise ValueError('A substantive explanation and usable preserved answer/source are required: '+q['id'])
        current=copy.deepcopy(q)
        if(current.get('explanation')or'').strip():
            if current['explanation']!=text:raise ValueError('Never overwrite a nonempty explanation')
            current['explanation']=expected.get('explanation');identical.append(q['id'])
        # Source publications add a durable receipt ID; no other raw fields may
        # drift. The record still has to match the exact planned predecessor.
        if 'reviewPublicationId'in current or 'reviewPublicationId'in expected:
            current['reviewPublicationId']=expected.get('reviewPublicationId')
            if 'reviewPublicationId'not in expected:current.pop('reviewPublicationId',None)
        if current!=expected or record(current)!=item['post_source_expected']:raise ValueError('Source repair not completed or reviewed answer/context changed: '+q['id'])
        if q['id']in identical:continue
        reason=item['source_review_note']+' Explanation-only maintenance. Preserve all examiner answers/key references, source positions/options, compensation/review holds and learner history; no independent peer certification.'
        evidence=[dict(kind='paper',document_id=doc['id'],sha256=doc['sha256'],page=page,note=reason)]
        for ref in item.get('supporting_references',[]):evidence.append(dict(kind='reference',url=ref['url'],note=ref.get('support','Primary reference checked for the historical explanation.')))
        proposal=dict(kind='explanation',canonical_id=item['canonical_id'],appearance_id=q['id'],subject_id=record(q)['classification']['subject_id'],title='Explain MCS printed Q'+str(q['qnum']),patch={'explanation':text},rationale=reason,evidence=evidence)
        items.append(dict(proposal=proposal,expected_source=record(q),paper_id=pid,source_sha=doc['sha256'],reason=reason))
    return dict(operation='source-batch',owner_email='hruaitluangasailo20@gmail.com',authorization='Owner requested completion of checked MCS explanations. Add only reviewed explanation text after exact source prerequisites through audited publication, preserving all answers/provenance, source mappings, holds, access and history.',items=items),identical

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--packet',type=Path,default=PACKET,help='Checked packet saved under docs/sources; all existing source/answer guards remain mandatory');p.add_argument('--offset',type=int,default=0);p.add_argument('--limit',type=int,default=100);p.add_argument('--preview',action='store_true');p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if not args.output.resolve().is_relative_to(ROOT/'reports'):p.error('Write reports under reports/')
    if not args.packet.resolve().is_relative_to(ROOT/'docs/sources'):p.error('Read checked packets under docs/sources/')
    packet=json.loads(args.packet.read_text());bank=json.loads((BANK_ROOT/'bank/mpsc_bank_v2.json').read_text())
    if args.preview:
        # In-memory validation only; this is not an executable publication
        # request and must not be passed to the owner-maintenance CLI.
        by={q['id']:q for q in bank['questions']}
        for item in packet['items']:by[item['appearance_id']].update(item['required_source_patch'])
    request,identical=prepare(packet,bank,BANK_ROOT,args.offset,args.limit)
    result=dict(preview=True,publication=False,prepared_after_exact_prerequisites=len(request['items']),already_identical=len(identical))if args.preview else request
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(preview=args.preview,prepared=len(request['items']),identical=len(identical),publication=False)))
if __name__=='__main__':main()
