#!/usr/bin/env python3
"""Prepare exact-source graphical choices in separate audited publication phases."""
import argparse,hashlib,json
from pathlib import Path
from review_bank_store import record,digest
ROOT=Path(__file__).resolve().parents[1];BANK_ROOT=ROOT.parent/'mpsc-question-bankv2'
PACKET=ROOT/'docs/sources/mcs-figure-repairs-20261102.json'

def expected(item,phase):
    result=dict(item['expected_source'])
    if phase!='withdraw':result.update(answerIndex=None,answerSource='none',answerKeyRef=None,explanation=item['withdrawal_explanation'])
    if phase in {'defect','answers'}:result.update(options=item['options'],hasDiagram=True,figureImage=item['figure_image'])
    return result

def prepare(packet,bank,root,phase,index=None):
    if phase not in {'withdraw','transcription','defect','answers'}:raise ValueError('Unknown repair phase')
    if phase=='withdraw'and(type(index)is not int or not 0<=index<len(packet['items'])):raise ValueError('Choose one explicit withdrawal')
    root=Path(root).resolve();by={q['id']:q for q in bank['questions']};items=[];repairs=[]
    chosen=[packet['items'][index]]if phase=='withdraw'else packet['items']
    for item in chosen:
        q=by[item['appearance_id']];doc=item['source_document'];key=item['key'];image=(root/item['figure_image']).resolve()
        for d in [doc,key]:
            path=(root/d['source_file']).resolve()
            if not path.is_relative_to(root/'pdfs')or not path.is_file()or hashlib.sha256(path.read_bytes()).hexdigest()!=d['sha256']or d['paper_id']!=q['paperId']:raise ValueError('Exact registered source/key changed')
        if not image.is_relative_to(root/'images/page-renders')or not image.is_file()or hashlib.sha256(image.read_bytes()).hexdigest()!=item['figure_sha256']or image.stem!=item['figure_sha256']:raise ValueError('Exact inspected figure image changed')
        if (len(item['options'])!=4 or len(set(item['options']))!=4 or key['answer_index']!=1 or key['letter']!='B'
                or item['expected_source']!=record(item['original_raw_record'])or digest(item['original_raw_record'])!=item['baseline_sha256']):raise ValueError('Reviewed option mapping or immutable baseline changed')
        source=record(q)
        if source!=expected(item,phase):raise ValueError('Exact predecessor or reviewed source changed: '+q['id'])
        reason='Restore this exact2025MCS graph question from its original booklet and final key. Keep printed A–D order, source identity, all34holds and learner history. Each stage is independently audited; previous key/provenance retained in original snapshots.'
        if phase=='withdraw':
            repairs.append(dict(canonical_id=item['canonical_id'],appearance_id=q['id'],mode='unsolved',answer_index=None,explanation=item['withdrawal_explanation'],reason=reason+' Temporarily withdraw an unusable answer to blank choices; the question already has a blocking source defect. No replacement key is assigned.',expected_source=source))
        elif phase=='answers':
            if q.get('sourceDefect')is not None:raise ValueError('Separate source-defect clearance must be completed first')
            repairs.append(dict(canonical_id=item['canonical_id'],appearance_id=q['id'],mode='official',answer_index=1,document_id=key['id'],key_page=key['page'],explanation=item['explanation'],reason=reason+' Exact final-key cell B for printed Q'+str(q['qnum'])+' visually inspected, with mapped accessible option text and complete original diagram.',expected_source=source))
        else:
            patch={'options':item['options'],'answerIndex':None,'figureImage':item['figure_image'],'hasDiagram':True}if phase=='transcription'else{'sourceDefect':None,'disputeNote':'The original source diagram and four distinct accessible option descriptions have been restored and visually checked. Clear only the obsolete duplicate-options flag; answer remains null pending separate final-key mapping.'}
            items.append(dict(proposal=dict(kind=phase,canonical_id=item['canonical_id'],appearance_id=q['id'],subject_id=source['classification']['subject_id'],title='Restore MCS figure Q'+str(q['qnum'])if phase=='transcription'else'Clear restored MCS figure source flag',patch=patch,rationale=reason,evidence=[dict(kind='paper',document_id=doc['id'],sha256=doc['sha256'],page=item['physical_pdf_page'],note=reason)]),expected_source=source,paper_id=q['paperId'],source_sha=doc['sha256'],reason=reason))
    common=dict(owner_email='hruaitluangasailo20@gmail.com',authorization='Owner authorized continued MCS source/option repairs through ordinary staff quotas only. Preserve source identities, compensation/review holds, learner history and examiner attribution; restore only inspected exact-booklet diagrams/options and final-key cells.')
    if phase=='withdraw':return dict(**common,operation='answer',repair=repairs[0])
    if phase=='answers':return dict(**common,operation='answer-batch',repairs=repairs)
    return dict(**common,operation='source-batch',items=items)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--phase',required=True,choices=['withdraw','transcription','defect','answers']);p.add_argument('--index',type=int);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if not a.output.resolve().is_relative_to(ROOT/'reports'):p.error('Write requests under reports/')
    req=prepare(json.loads(PACKET.read_text()),json.loads((BANK_ROOT/'bank/mpsc_bank_v2.json').read_text()),BANK_ROOT,a.phase,a.index);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(req,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(phase=a.phase,publication=False)))
if __name__=='__main__':main()
