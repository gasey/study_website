"""Pure validation and publication policy; shared by API and isolated tests."""
import hashlib
import json
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator, model_serializer

KINDS = Literal['answer','transcription','explanation','taxonomy','source_reference','new_question','defect','duplicate','source_request']
HIGH_IMPACT = {'answer','transcription','new_question','defect','duplicate'}
PATCH_FIELDS = {'question','direction','questionMarkup','optionsMarkup','passage','options','answerIndex',
                'answerSource','answerKeyRef','explanation','difficulty','page','qnum','hasDiagram',
                'figureImage','sourceDefect','disputeNote','classification','relatedClassifications','duplicateId','sourceUrl','paperId'}
ALLOWED = {
 'answer': {'answerIndex','answerSource','answerKeyRef','explanation','disputeNote'},
 'explanation': {'explanation'},
 'transcription': {'question','direction','questionMarkup','optionsMarkup','passage','options','answerIndex','explanation','hasDiagram','figureImage'},
 'taxonomy': {'classification','relatedClassifications','difficulty'},
 'source_reference': {'page','qnum','sourceUrl'},
 'new_question': {'question','options','answerIndex','answerSource','explanation','classification','relatedClassifications','paperId','page','qnum'},
 'defect': {'sourceDefect','disputeNote'},
 'duplicate': {'duplicateId'}, 'source_request': {'sourceUrl','explanation','paperId'},
}

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',',':'), default=str).encode()).hexdigest()


def safe_url(value):
    url = urlsplit(value)
    if url.scheme != 'https' or not url.hostname or url.username or url.password:
        raise ValueError('Use an HTTPS source URL without embedded credentials')
    return value


class Evidence(BaseModel):
    module_item_id: str | None = Field(default=None,min_length=1,max_length=100)
    module_run_sha256: str | None = Field(default=None,pattern=r'^[0-9a-f]{64}$')
    model_config = ConfigDict(extra='forbid')
    kind: Literal['paper','official-key','reference','reasoning']
    document_id: str | None = Field(default=None,max_length=100)
    sha256: str | None = Field(default=None,pattern=r'^[0-9a-f]{64}$')
    page: int | None = Field(default=None,ge=1,le=10000)
    url: str | None = Field(default=None,max_length=2048)
    note: str = Field(min_length=5,max_length=4000)
    printed_question: str | None = Field(default=None,max_length=40)
    series: str | None = Field(default=None,max_length=20)
    answer_text: str | None = Field(default=None,max_length=4000)

    @model_serializer(mode='wrap')
    def serialize(self,handler):
        data=handler(self)
        if self.module_item_id is None:
            data.pop('module_item_id',None);data.pop('module_run_sha256',None)
        return data

    @model_validator(mode='after')
    def check(self):
        if bool(self.module_item_id)!=bool(self.module_run_sha256):raise ValueError('Module item and immutable run hash must be supplied together')
        if self.module_item_id and self.kind!='reference':raise ValueError('Module comparisons are reference evidence only')
        if self.url: safe_url(self.url)
        if self.kind in {'paper','official-key'} and not (self.document_id and self.sha256 and self.page):
            raise ValueError('Paper/key evidence needs a registered document, SHA256 and page')
        if self.kind == 'official-key' and not (self.printed_question and self.answer_text):
            raise ValueError('Key evidence needs the printed question and mapped answer text')
        return self


class Proposal(BaseModel):
    model_config = ConfigDict(extra='forbid')
    kind: KINDS
    reverts_publication: str | None = Field(default=None,max_length=100)
    canonical_id: str | None = Field(default=None,max_length=100)
    appearance_id: str | None = Field(default=None,max_length=200)
    subject_id: str = Field(min_length=2,max_length=100)
    title: str = Field(min_length=5,max_length=200)
    patch: dict = Field(min_length=1,max_length=20)
    rationale: str = Field(min_length=20,max_length=8000)
    evidence: list[Evidence] = Field(min_length=1,max_length=10)

    @model_validator(mode='after')
    def check(self):
        if set(self.patch) - ALLOWED[self.kind]:
            raise ValueError('Fields do not belong to this contribution kind')
        for key,value in self.patch.items():
            if key in {'options','optionsMarkup'}:
                if not isinstance(value,list) or not 2<=len(value)<=8 or any(v is not None and (not isinstance(v,str) or len(v)>4000) for v in value):
                    raise ValueError('Options need 2–8 text entries')
            elif key=='answerIndex':
                if value is not None and (type(value) is not int or not 0<=value<=7): raise ValueError('Invalid answer index')
            elif key=='hasDiagram':
                if type(value) is not bool: raise ValueError('hasDiagram must be boolean')
            elif key=='page':
                if type(value) is not int or not 1<=value<=10000: raise ValueError('Invalid page')
            elif key=='relatedClassifications':
                if not isinstance(value,list) or len(value)>12: raise ValueError('Choose at most twelve related topic paths')
                seen=set()
                for path in value:
                    if not isinstance(path,dict) or set(path)-{'subject_id','topic_id','subtopic_id'} or not path.get('subject_id'): raise ValueError('Choose valid related taxonomy paths')
                    if any(v is not None and (not isinstance(v,str) or not v or len(v)>160) for v in path.values()): raise ValueError('Invalid related path')
                    marker=(path.get('subject_id'),path.get('topic_id'),path.get('subtopic_id'))
                    if marker in seen: raise ValueError('Remove duplicate related paths')
                    seen.add(marker)
                self.patch[key]=sorted([{k:p.get(k) for k in ('subject_id','topic_id','subtopic_id')} for p in value],key=lambda p:(p['subject_id'],p['topic_id'] or '',p['subtopic_id'] or ''))
            elif key=='classification':
                if not isinstance(value,dict) or set(value)-{'subject_id','topic_id','subtopic_id'} or not value.get('subject_id'):
                    raise ValueError('Choose a valid taxonomy path')
                if any(v is not None and (not isinstance(v,str) or len(v)>160) for v in value.values()): raise ValueError('Invalid classification')
            elif value is not None and (not isinstance(value,str) or len(value)>12000):
                raise ValueError(f'Invalid text value for {key}')
        if self.patch.get('answerSource') not in {None,'derived','official','key','none'}: raise ValueError('Unsupported answer provenance')
        if self.patch.get('difficulty') not in {None,'easy','medium','hard'}: raise ValueError('Invalid difficulty')
        if self.patch.get('sourceDefect') not in {None,'duplicate-options','hand-transcribed-matching-table','correct-option-added','diagram-not-embedded','unresolved-source'}:
            raise ValueError('Unsupported source defect')
        if self.patch.get('sourceUrl'): safe_url(self.patch['sourceUrl'])
        if self.patch.get('figureImage') and (self.patch['figureImage'].startswith('/') or '..' in self.patch['figureImage'].split('/') or ':' in self.patch['figureImage']):
            raise ValueError('Figure must reference a registered relative asset path')
        if self.kind not in {'new_question','source_request'} and not self.canonical_id: raise ValueError('Choose a target question')
        if 'question' in self.patch and (not isinstance(self.patch['question'],str) or len(self.patch['question'].strip())<5): raise ValueError('Question text is required')
        if self.kind in {'new_question','answer','explanation'} and len(str(self.patch.get('explanation') or '').strip())<20: raise ValueError('Provide a useful explanation of at least 20 characters')
        if self.kind=='new_question':
            for key in ('question','options','answerIndex','explanation','classification'):
                if key not in self.patch: raise ValueError(f'New MCQ requires {key}')
            opts=self.patch['options']; ai=self.patch['answerIndex']
            if any(not o or not o.strip() for o in opts) or len(set(opts))!=len(opts): raise ValueError('New MCQ options must be complete and distinct')
            if ai is None or ai>=len(opts): raise ValueError('Choose the correct option')
            if self.patch.get('answerSource','derived')!='derived': raise ValueError('Community MCQs use reviewed derived provenance')
        if self.patch.get('answerSource') in {'official','key'} and not any(e.kind=='official-key' for e in self.evidence):
            raise ValueError('Official provenance requires a registered mapped key')
        if self.kind=='answer' and not {'answerIndex','answerSource','explanation'} <= set(self.patch):
            raise ValueError('Answer proposals need index, provenance and explanation')
        return self


def validate_target(proposal, baseline, allow_noop=False):
    def unchanged(key,value):
        if key=='classification' and baseline.get(key):return tuple(value.get(k) for k in ('subject_id','topic_id','subtopic_id'))==tuple(baseline[key].get(k) for k in ('subject_id','topic_id','subtopic_id'))
        return (key in baseline or key=='relatedClassifications') and value==baseline.get(key,[] if key=='relatedClassifications' else None)
    if baseline and not allow_noop and all(unchanged(key,value) for key,value in proposal.patch.items()):
        raise ValueError('This proposal makes no change to the current question')
    merged={**baseline,**proposal.patch}
    opts=merged.get('options') or []
    ai=merged.get('answerIndex')
    if ai is not None and (ai>=len(opts) or opts[ai] is None): raise ValueError('Answer points outside available options')
    if 'options' in proposal.patch and 'answerIndex' not in proposal.patch and baseline.get('answerIndex') is not None:
        raise ValueError('Option changes must explicitly re-map the answer index')
    if merged.get('answerSource') in {'official','key'} and 'options' in proposal.patch and not any(e.kind=='official-key' for e in proposal.evidence):
        raise ValueError('Changing officially keyed options requires renewed key mapping')
    for e in proposal.evidence:
        if e.kind=='official-key':
            if ai is None or e.answer_text!=opts[ai]: raise ValueError('Key evidence does not match the proposed answer text')
            if baseline.get('qnum') and e.printed_question!=str(baseline['qnum']): raise ValueError('Key question number does not match')


def quorum(kind, baseline, patch):
    changing_official = baseline.get('answerSource') in {'official','key'} and bool(set(patch)&{'answerIndex','options','question','answerSource'})
    return (2 if kind in HIGH_IMPACT else 1), changing_official
