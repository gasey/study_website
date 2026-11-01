#!/usr/bin/env python3
"""Prepare exact-source shared passages, preserving examiner answers and source identity."""
import argparse,hashlib,json
from pathlib import Path
from review_bank_store import record,digest
ROOT=Path(__file__).resolve().parents[1]
BANK_ROOT=ROOT.parent/'mpsc-question-bankv2'
PACKET=ROOT/'docs/sources/mcs-reading-passage-repairs-20261101.json'

def prepare(packet,bank,bank_root):
    bank_root=Path(bank_root).resolve();by={q['id']:q for q in bank['questions']};items=[];seen=set()
    for item in packet['items']:
        aid=item['appearance_id'];q=by[aid];doc=item['source_document'];patch=item['patch'];expected=item['expected_source']
        if aid in seen:raise ValueError('One shared passage repair per target')
        seen.add(aid)
        path=(bank_root/doc['source_file']).resolve()
        if (doc['kind']!='paper' or doc['paper_id']!=q['paperId'] or q['paperId']!=item['paper_id']
                or not path.is_relative_to(bank_root/'pdfs') or not path.is_file()
                or hashlib.sha256(path.read_bytes()).hexdigest()!=doc['sha256']):raise ValueError('Exact inspected paper changed')
        blocks=[b for b in packet['blocks']if b['paper_id']==q['paperId']and b['kind']==item['passage_kind']]
        if (set(patch)!={'passage'} or len(blocks)!=1 or patch['passage']!=blocks[0]['text']
                or len(patch['passage'])<100 or expected.get('passage')is not None
                or blocks[0]['source_pages']!=item['source_pages']):raise ValueError('Require the complete exact inspected shared passage and all continuation pages')
        pages=item['source_pages'];question_page=item['physical_pdf_page']
        if (not pages or any(type(p)is not int or p<1 for p in [*pages,question_page])
                or pages!=list(range(min(pages),max(pages)+1))):raise ValueError('Inspected physical source pages must be explicit and consecutive')
        current=record(q)
        if current=={**expected,**patch}:continue
        if current!=expected or digest(q)!=item['baseline_sha256']:raise ValueError('Reviewed source/answer baseline changed')
        reason=item['source_review_note'];evidence=[dict(kind='paper',document_id=doc['id'],sha256=doc['sha256'],page=page,note=reason)for page in dict.fromkeys([*pages,question_page])]
        proposal=dict(kind='transcription',canonical_id=item['canonical_id'],appearance_id=aid,subject_id=current['classification']['subject_id'],title='Restore MCS shared passage for Q'+str(q['qnum']),patch=patch,rationale=reason,evidence=evidence)
        items.append(dict(proposal=proposal,expected_source=current,paper_id=q['paperId'],source_sha=doc['sha256'],reason=reason))
    return dict(operation='source-batch',owner_email='hruaitluangasailo20@gmail.com',authorization='Owner requested completion of MCS quality repairs. Restore only checked original shared passages through the audited source workflow, preserving examiner answers/provenance, positions, all holds, access and learner history.',items=items)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
    if not args.output.resolve().is_relative_to(ROOT/'reports'):parser.error('Write requests under reports/')
    request=prepare(json.loads(PACKET.read_text()),json.loads((BANK_ROOT/'bank/mpsc_bank_v2.json').read_text()),BANK_ROOT);args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(prepared=len(request['items']),publication=False)))
if __name__=='__main__':main()
