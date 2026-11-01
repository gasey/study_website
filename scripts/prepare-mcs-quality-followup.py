#!/usr/bin/env python3
"""Prepare reviewed MCS source/defect/answer requests; never write bank or server.

Each phase requires its predecessors to match the current canonical workshop.
Source publication and separate defect/answer adjudication use the existing
owner maintenance CLI, ordinary staff quotas and audited publisher workflow.
"""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from review_bank_store import record,digest
ROOT=Path(__file__).resolve().parents[1]
BANK_ROOT=ROOT.parent/'mpsc-question-bankv2'
BANK=BANK_ROOT/'bank/mpsc_bank_v2.json'
PACKET=ROOT/'docs/sources/mcs-quality-followup-20261101.json'


def validate_item(item,current):
    path=(BANK_ROOT/'pdfs'/item['paper_id']).resolve()
    if not path.is_relative_to(BANK_ROOT/'pdfs') or not path.is_file():
        raise ValueError('Reviewed PDF is unavailable: '+item['appearance_id'])
    if hashlib.sha256(path.read_bytes()).hexdigest()!=item['source_sha256']:
        raise ValueError('Reviewed PDF changed: '+item['appearance_id'])
    if current['paperId']!=item['paper_id'] or current['id']!=item['appearance_id']:
        raise ValueError('Source identity changed')
    if current.get('answerIndex')is not None:
        raise ValueError('An answer has already been assigned; inspect its current provenance before reusing this draft')
    image=current.get('figureImage')
    if current.get('hasDiagram') and (not image or not (BANK_ROOT/image).is_file()):
        raise ValueError('Required source image is unavailable')


def prepare(phase,packet,bank):
    by={q['id']:q for q in bank['questions']};items=[];repairs=[];blocked=[]
    if phase=='explanations':
        for item in packet.get('existing_explanation_drafts',[]):
            q=by[item['appearance_id']]
            if q.get('explanation')==item['explanation']:continue
            if digest(q)!=item['baseline_sha256'] or record(q)!=item['expected_source'] or q.get('sourceDefect'):
                raise ValueError('Existing explanation/source baseline changed: '+q['id'])
            key=item['key'];path=(BANK_ROOT/'pdfs'/key['file']).resolve()
            if not path.is_relative_to(BANK_ROOT/'pdfs')or hashlib.sha256(path.read_bytes()).hexdigest()!=key['sha256']:
                raise ValueError('Exact final-key source changed')
            if q['answerIndex']!=item['existing_answer_index']or q['answerSource']!='official'or q.get('answerKeyRef')!=key['document_id']:
                raise ValueError('Official-key provenance changed')
            repairs.append(dict(canonical_id=item['canonical_id'],appearance_id=q['id'],mode='official',answer_index=q['answerIndex'],document_id=key['document_id'],key_page=key['page'],explanation=item['explanation'],
                reason='Add checked reviewer-written working to this existing exact-booklet official answer. Original source question/choices and final-key cell inspected; no official worked explanation or independent peer approval asserted.',expected_source=record(q)))
        return {'operation':'answer-batch','repairs':repairs}
    for item in packet['items']:
        current=by.get(item['appearance_id'])
        if current is None:raise ValueError('Reviewed question is missing')
        validate_item(item,current)
        source=record(current)
        if phase=='transcription':
            # Do not submit unchanged nullable markup fields. In particular,
            # optionsMarkup=None is a source baseline, not a new options list.
            patch={key:value for key,value in item['transcription_patch'].items()
                   if source.get(key)!=value}
            if not patch:continue
            if source==item['post_transcription_source']:continue
            if source!=item['expected_source'] or digest(current)!=item['baseline_sha256']:
                raise ValueError('Reviewed transcription baseline changed: '+current['id'])
            reason=item['rationale']
            evidence=[dict(kind='paper',document_id=item['document_id'],sha256=item['source_sha256'],page=page,note=reason)
                      for page in dict.fromkeys([item['physical_pdf_page'],*item.get('additional_source_pages',[])])]
            items.append(dict(proposal=dict(kind='transcription',canonical_id=item['canonical_id'],appearance_id=current['id'],subject_id=item['subject_id'],
                title='Restore MCS printed Q'+str(item['printed_question'])+' source transcription',patch=patch,rationale=reason,evidence=evidence),
                paper_id=item['paper_id'],source_sha=item['source_sha256'],reason=reason,expected_source=source))
        else:
            if item['decision']=='retain-unresolved-source':continue
            # Compare all source fields while allowing the separately adjudicated
            # flag to be null in the answer phase. Never combine the phases.
            expected=dict(item['post_transcription_source'])
            if source!=expected or (phase=='answers' and current.get('sourceDefect') is not None):
                blocked.append({'appearance_id':current['id'],'reason':'Source transcription or separate defect adjudication has not been verified yet'})
                continue
            if phase=='defect':
                if current.get('sourceDefect') is None:continue
                if current['sourceDefect']!='unresolved-source':raise ValueError('The reviewed source defect changed')
                reason='Separate source-defect review: '+item['rationale']+' The checked source is now readable; retain null answers, source identity and provisional recovered-copy status.'
                items.append(dict(proposal=dict(kind='defect',canonical_id=item['canonical_id'],appearance_id=current['id'],subject_id=item['subject_id'],
                    title='Adjudicate MCS Q'+str(item['printed_question'])+' source readability',patch={'sourceDefect':None,'disputeNote':reason},rationale=reason,
                    evidence=[dict(kind='paper',document_id=item['document_id'],sha256=item['source_sha256'],page=item['physical_pdf_page'],note=reason)]),
                    paper_id=item['paper_id'],source_sha=item['source_sha256'],reason=reason,expected_source=source))
            elif item.get('answer_draft'):
                draft=item['answer_draft']
                if source['options'][draft['answer_index']]!=draft['answer_text']:
                    raise ValueError('Reviewed answer no longer matches the ordered source choices')
                repair=dict(canonical_id=item['canonical_id'],appearance_id=current['id'],mode=draft['mode'],answer_index=draft['answer_index'],
                    explanation=draft['explanation'],reason='Owner-authorized checked working for this exact source. Single operator review; no independent peer approval is asserted.',expected_source=source)
                if draft['mode']=='official':
                    key=draft['key'];path=(BANK_ROOT/'pdfs'/key['file']).resolve()
                    if not path.is_relative_to(BANK_ROOT/'pdfs')or hashlib.sha256(path.read_bytes()).hexdigest()!=key['sha256']:
                        raise ValueError('Exact final-key source changed')
                    repair.update(document_id=key['document_id'],key_page=key['page'])
                    repair['reason']='Exact-booklet final key, printed Q'+str(item['printed_question'])+', letter '+key['letter']+'. Source figures/ordered choices and checked mathematical working inspected; explanation is reviewer-written, not an official worked solution.'
                repairs.append(repair)
    if blocked:
        raise ValueError('Finish and verify predecessor publications first: '+json.dumps(blocked))
    return {'operation':'answer-batch','repairs':repairs}if phase=='answers'else{'operation':'source-batch','items':items}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=('transcription','defect','answers','explanations'),required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if not args.output.resolve().is_relative_to(ROOT/'reports'):
        parser.error('Write preparation reports beneath this app reports directory')
    packet=json.loads(PACKET.read_text());bank=json.loads(BANK.read_text())
    request=prepare(args.phase,packet,bank)
    request.update(owner_email='hruaitluangasailo20@gmail.com',authorization='Owner instructed Do all for the practice follow-up and MCS content-quality work. Publish only the checked source/defect/answer packet through the established audited workflow within ordinary staff allowance. Preserve source identity, compensation holds, provenance, account access and learner history.')
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'phase':args.phase,'prepared':len(request.get('repairs',request.get('items',[]))),'output':str(args.output),'publication':False}))

if __name__=='__main__':main()
