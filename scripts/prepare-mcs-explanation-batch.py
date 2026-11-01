#!/usr/bin/env python3
"""Prepare bounded explanation-only requests from the checked MCS packet; no writes to bank/server."""
import argparse,hashlib,json
from pathlib import Path
from review_bank_store import record,digest
ROOT=Path(__file__).resolve().parents[1]
BANK_ROOT=ROOT.parent/'mpsc-question-bankv2'
PACKET=ROOT/'docs/sources/mcs-explanation-batch-20261101.json'


def prepare(packet,bank,bank_root,offset=0,limit=100):
    if type(offset)is not int or offset<0 or type(limit)is not int or not 1<=limit<=100:
        raise ValueError('Choose a nonnegative offset and 1–100 items')
    all_items=packet['items']
    if not 1<=len(all_items)<=200 or len({i['appearance_id']for i in all_items})!=len(all_items)or len({i['canonical_id']for i in all_items})!=len(all_items):
        raise ValueError('Packet must contain at most 200 distinct reviewed canonical appearances')
    by={q['id']:q for q in bank['questions']};papers={p['id']:p for p in bank['papers']};scope=set(packet['scope']['paper_ids']);items=[];identical=[]
    bank_root=Path(bank_root).resolve()
    for item in all_items[offset:offset+limit]:
        q=by[item['appearance_id']];expected=item['expected_source'];doc=item['source_document'];pid=q['paperId']
        if (pid not in scope or 'MCS Combined'not in pid or papers[pid].get('year')not in(2023,2025)
                or q.get('sourceDefect')in('duplicate-options','unresolved-source')
                or doc['kind']!='paper' or doc['paper_id']!=pid):
            raise ValueError('Reviewed source is outside the usable recent MCS scope')
        path=(bank_root/doc['source_file']).resolve()
        if not path.is_relative_to(bank_root/'pdfs')or not path.is_file()or hashlib.sha256(path.read_bytes()).hexdigest()!=doc['sha256']:
            raise ValueError('Exact reviewed PDF changed or is unavailable')
        current=record(q);opts=q.get('options')or[];ai=q.get('answerIndex')
        if (q.get('type')!='mcq' or type(ai)is not int or not 0<=ai<len(opts)or not 2<=len(opts)<=8
                or any(not isinstance(o,str)or not o.strip()for o in opts)or len({o.strip()for o in opts})!=len(opts)
                or q.get('answerSource')not in('official','key','derived')
                or q.get('hasDiagram')and(not q.get('figureImage')or not(bank_root/q['figureImage']).is_file())):
            raise ValueError('An existing usable answer and source are required')
        text=item['explanation']
        if not isinstance(text,str)or len(text.strip())<20 or not 1<=item['physical_pdf_page']<=10000:
            raise ValueError('A substantive explanation and inspected physical page are required')
        if(q.get('explanation')or'').strip():
            same_source={**current,'explanation':expected['explanation']}
            if q['explanation']==text and same_source==expected:
                identical.append(q['id']);continue
            raise ValueError('Never overwrite an existing explanation in this backfill')
        if digest(q)!=item['baseline_sha256']or current!=expected:
            raise ValueError('Reviewed question, answer, provenance or source baseline changed')
        reason=item['source_review_note']+' Explanation-only maintenance; preserve all answers, key references, source mappings, holds and learner history. Luna drafting checked by one operator; no independent peer approval asserted.'
        evidence=[dict(kind='paper',document_id=doc['id'],sha256=doc['sha256'],page=item['physical_pdf_page'],note=reason)]
        for ref in item.get('supporting_references',[]):
            evidence.append(dict(kind='reference',url=ref['url'],note='Checked primary reference for this explanation; original examiner key and scoring are unchanged.'))
        proposal=dict(kind='explanation',canonical_id=item['canonical_id'],appearance_id=q['id'],subject_id=current['classification']['subject_id'],
            title='Explain recent MCS printed Q'+str(q['qnum']),patch={'explanation':text},rationale=reason,evidence=evidence)
        items.append(dict(proposal=proposal,expected_source=current,paper_id=pid,source_sha=doc['sha256'],reason=reason))
    return dict(operation='source-batch',owner_email='hruaitluangasailo20@gmail.com',
        authorization='Owner requested recent MCS explanations using Luna drafts with coordinator source/reasoning checks. Publish only reviewed explanation text through the audited workflow; preserve all answers, provenance, source mapping, compensation holds and learner history.',items=items),identical


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--offset',type=int,default=0);p.add_argument('--limit',type=int,default=100);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if not args.output.resolve().is_relative_to(ROOT/'reports'):p.error('Write requests below reports/')
    request,identical=prepare(json.loads(PACKET.read_text()),json.loads((BANK_ROOT/'bank/mpsc_bank_v2.json').read_text()),BANK_ROOT,args.offset,args.limit)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'prepared':len(request['items']),'already_has_identical_text':len(identical),'publication':False,'output':str(args.output)}))

if __name__=='__main__':main()
