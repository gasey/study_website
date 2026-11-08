"""Automatic audit summaries describe changes; they never invent source inspection."""
from fastapi import HTTPException
from .review_identity import grants
from .review_policy import Proposal


async def is_owner(cur,user_id):
    return 'owner' in await grants(cur,user_id)


def answer_text(record,patch=None):
    r={**record,**(patch or {})};i=r.get('answerIndex');options=r.get('options') or []
    return options[i] if isinstance(i,int) and 0<=i<len(options) else None


def needs_answer_reason(record,kind,patch):
    return kind=='transcription' and 'options' in patch and answer_text(record)!=answer_text(record,patch)


def path_text(path):
    return ' / '.join(str(path.get(k)) for k in ('subject_id','topic_id','subtopic_id') if path.get(k)) or 'unclassified'


def change_summary(record,kind,patch):
    if kind=='taxonomy':
        pieces=[]
        if 'classification' in patch:pieces.append('primary path '+path_text(record.get('classification') or {})+' → '+path_text(patch['classification']))
        if 'relatedClassifications' in patch:pieces.append('related paths '+str(len(record.get('relatedClassifications') or []))+' → '+str(len(patch['relatedClassifications'])))
        detail='; '.join(pieces)
    elif kind=='source_reference':
        detail='; '.join(k+' '+str(record.get(k) or 'unset')+' → '+str(v) for k,v in patch.items())
    else:
        labels={'question':'question text','direction':'instructions','passage':'shared passage','options':'printed options',
          'answerIndex':'option-to-answer mapping','explanation':'explanation','questionMarkup':'text formatting','optionsMarkup':'option formatting'}
        detail=', '.join(labels.get(k,k) for k,v in patch.items() if record.get(k)!=v)
    return ('Automatic owner change summary: '+kind+'; '+detail+'.')[:2800]


def routine_proposal(snapshot,kind,patch,note='',evidence=None):
    record=snapshot['record'];note=note.strip()
    if needs_answer_reason(record,kind,patch) and len(note)<20:
        raise HTTPException(422,'Changing the correct answer needs a supporting note of at least 20 characters')
    summary=change_summary(record,kind,patch)
    reason=summary+('\nOwner note: '+note if note else '')
    return Proposal(kind=kind,canonical_id=snapshot['canonical_id'],appearance_id=record['id'],
      subject_id=(patch.get('classification') or record['classification'])['subject_id'],
      title='Owner correction: '+record['question'][:140],patch=patch,rationale=reason,
      evidence=evidence or [{'kind':'reasoning','note':reason[:4000]}])
