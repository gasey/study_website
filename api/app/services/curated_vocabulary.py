"""Editor-authored word cards; publication uses the existing material review flow."""
import unicodedata
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,field_validator,model_serializer
from fastapi import HTTPException

def word_key(value):
    return ' '.join(unicodedata.normalize('NFKC',value).casefold().split())

class WordCard(BaseModel):
    model_config=ConfigDict(extra='forbid')
    language:Literal['english','mizo-english']='english'
    word:str=Field(default='',max_length=120)
    meaning:str=Field(default='',max_length=1200)
    usage:str=Field(default='',max_length=2000)
    mizo_gloss:str=Field(default='',max_length=600)
    recognition_options:list[str]=Field(default_factory=list,max_length=6)
    cloze_sentence:str=Field(default='',max_length=2000)
    cloze_options:list[str]=Field(default_factory=list,max_length=6)
    source_note:str=Field(default='',max_length=1200)
    mizo_options:list[str]=Field(default_factory=list,max_length=6)

    @model_serializer(mode='wrap')
    def legacy_shape(self,handler):
        value=handler(self)
        if not self.mizo_options:value.pop('mizo_options',None)
        return value

    @field_validator('recognition_options','cloze_options','mizo_options')
    @classmethod
    def options_bounded(cls,value):
        if any(any(ord(c)<32 and c not in '\n\t' for c in x) for x in value):raise ValueError('Unsupported control character')
        if any(len(x)>1200 for x in value):raise ValueError('Vocabulary choices allow at most1,200characters')
        return value

    @field_validator('word','meaning','usage','mizo_gloss','cloze_sentence','source_note')
    @classmethod
    def plain_text(cls,value):
        if any(ord(c)<32 and c not in '\n\t' for c in value):raise ValueError('Unsupported control character')
        return value


def publishable(card):
    if not all(word_key(x) for x in (card.word,card.meaning,card.usage,card.source_note)):
        raise HTTPException(422,'Finish the word, meaning, usage and source/editorial note on every vocabulary card')
    if card.language=='mizo-english' and not word_key(card.mizo_gloss):
        raise HTTPException(422,'Mizo–English cards need a Mizo gloss for review')
    for label,options,answer in [('recognition',card.recognition_options,card.meaning),('cloze',card.cloze_options,card.word)]:
        keys=[word_key(x) for x in options]
        if not 2<=len(keys)<=6 or any(not x for x in keys) or len(set(keys))!=len(keys) or keys.count(word_key(answer))!=1:
            raise HTTPException(422,'Give each '+label+' prompt2–6distinct choices including its correct meaning/word exactly once')
    if card.mizo_options:
        keys=[word_key(x) for x in card.mizo_options]
        if card.language!='mizo-english' or len(keys)<2 or any(not x for x in keys) or len(set(keys))!=len(keys) or keys.count(word_key(card.mizo_gloss))!=1:
            raise HTTPException(422,'Mizo choices need2–6distinct glosses including the correct gloss exactly once')
    if card.cloze_sentence.count('{{word}}')!=1 or not word_key(card.cloze_sentence.replace('{{word}}','')):
        raise HTTPException(422,'Write a usage-cloze sentence with exactly one {{word}} gap')


def validate_document(doc,publish):
    cards=[b.vocabulary for b in doc.blocks if b.type=='vocabulary']
    if any(b.vocabulary is not None and b.type!='vocabulary' for b in doc.blocks):
        raise HTTPException(422,'Vocabulary data belongs on a vocabulary card block')
    if not publish:return
    if cards and doc.kind!='vocabulary-deck':raise HTTPException(422,'Choose Vocabulary deck as the material type before submitting word cards')
    if doc.kind!='vocabulary-deck':return
    if not cards or any(c is None for c in cards):raise HTTPException(422,'Add at least one complete vocabulary card')
    if not doc.collection_id or not doc.subject_id:raise HTTPException(422,'Tag this vocabulary deck with its reviewed exam and subject applicability')
    for card in cards:publishable(card)
    keys=[(c.language,word_key(c.word)) for c in cards]
    if len(keys)!=len(set(keys)):raise HTTPException(422,'Use each word/language pair once in a deck')
