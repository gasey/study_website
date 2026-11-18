"""Curated cards remain editorial revisions with existing publication/privacy gates."""
import copy
from uuid import uuid4
import pytest
from pydantic import ValidationError
from app.services.content_studio import Document
from app.services.curated_vocabulary import WordCard,word_key
from test_content_studio import document,create,publish


def card():
    return {'language':'mizo-english','word':'synthetic','meaning':'Created only for a test','usage':'This is a synthetic fixture.','mizo_gloss':'Mizo test gloss, not learning content','source_note':'Disposable test fixture; not a real language claim.','recognition_options':['Created only for a test','A different synthetic meaning'],'cloze_sentence':'This is a {{word}} fixture.','cloze_options':['synthetic','different']}


def deck(access='free'):
    doc=document(access);doc.update(kind='vocabulary-deck',collection_id='udc',subject_id='english',blocks=[{'id':'word-one','type':'vocabulary','vocabulary':card()}]);return doc


def test_curated_cards_need_valid_prompts_and_explicit_exam_subject_before_submission(client,actor,database):
    draft=deck();draft['blocks'][0]['vocabulary']['meaning']=''
    mid,h,_=create(client,actor,draft)
    assert client.post('/api/studio/materials/'+mid+'/submit',headers=h,json={'expected_version':1}).status_code==422
    for change in [{'recognition_options':['same','SAME']},{'cloze_options':['other','wrong']},{'cloze_sentence':'No gap here'},{'cloze_sentence':'{{word}} {{word}}'},{'mizo_gloss':''}]:
        invalid=deck();invalid['blocks'][0]['vocabulary'].update(change);mid,h,_=create(client,actor,invalid)
        assert client.post('/api/studio/materials/'+mid+'/submit',headers=h,json={'expected_version':1}).status_code==422
    for field in ('collection_id','subject_id'):
        invalid=deck();invalid[field]=None;mid,h,_=create(client,actor,invalid)
        assert client.post('/api/studio/materials/'+mid+'/submit',headers=h,json={'expected_version':1}).status_code==422
    database[1].execute("INSERT INTO collections(id,title,kind,visibility) VALUES('word-card-nonexam','Synthetic non-exam','guide','public')")
    invalid=deck();invalid['collection_id']='word-card-nonexam';h=actor('author')
    assert client.post('/api/studio/materials',headers={**h,'Idempotency-Key':uuid4().hex},json=invalid).status_code==422
    invalid=deck();other=copy.deepcopy(invalid['blocks'][0]);other['id']='other';other['vocabulary']['word']='ＳＹＮＴＨＥＴＩＣ';invalid['blocks'].append(other)
    mid,h,_=create(client,actor,invalid)
    assert client.post('/api/studio/materials/'+mid+'/submit',headers=h,json={'expected_version':1}).status_code==422


def test_word_cards_use_exact_cms_revision_review_and_private_draft_workflow(client,actor,database):
    doc=deck();mid,h,key=create(client,actor,doc)
    before=database[1].execute('SELECT count(*) FROM canonical_questions').fetchone()[0]
    assert client.post('/api/studio/materials',headers={**h,'Idempotency-Key':key},json=doc).json()['id']==mid
    actor('outsider');assert client.get('/api/materials/'+mid).status_code==404
    h=actor('author');assert client.post('/api/studio/materials/'+mid+'/submit',headers=h,json={'expected_version':1}).status_code==200
    assert client.post('/api/admin/bank/content/'+mid+'/review',headers=h,json={'expected_version':2,'decision':'publish'}).status_code==403
    h=actor('owner');assert client.post('/api/admin/bank/content/'+mid+'/review',headers=h,json={'expected_version':2,'decision':'publish'}).status_code==200
    actor('outsider');published=client.get('/api/materials/'+mid);assert published.status_code==200
    assert published.json()['document']['blocks'][0]['vocabulary']['word']=='synthetic'
    changed=copy.deepcopy(doc);changed['blocks'][0]['vocabulary']['meaning']='UNAPPROVED_CARD_MEANING'
    h=actor('author');assert client.post('/api/studio/materials/'+mid+'/save',headers=h,json={'expected_version':3,'document':changed}).status_code==200
    actor('outsider');assert 'UNAPPROVED_CARD_MEANING' not in client.get('/api/materials/'+mid).text
    h=actor('owner');assert client.post('/api/admin/bank/content/'+mid+'/review',headers=h,json={'expected_version':4,'decision':'publish'}).status_code==409
    assert database[1].execute('SELECT count(*) FROM canonical_questions').fetchone()[0]==before
    assert database[1].execute('SELECT count(*) FROM vocabulary_state').fetchone()[0]==0


def test_pro_word_cards_keep_existing_body_redaction_and_block_filters(client,actor,database):
    mid=publish(client,actor,deck('pro'));actor('outsider');r=client.get('/api/materials/'+mid);assert r.status_code==200
    assert r.json()['document']['blocks']==[] and 'Mizo test gloss' not in r.text
    database[1].execute("UPDATE users SET plan_code='pro',plan_status='trial',trial_ends_at=now()+interval '1 day' WHERE id='outsider'")
    assert client.get('/api/materials/'+mid).json()['document']['blocks'][0]['type']=='vocabulary'
    h=actor('outsider');assert client.post('/api/creators/author/block',headers=h,json={'enabled':True}).status_code==200
    assert client.get('/api/materials/'+mid).status_code==404


def test_new_card_contract_preserves_legacy_material_retry_shape_and_rejects_extra_answer_authority():
    old=Document.model_validate(document()).model_dump()
    assert all('vocabulary' not in b for b in old['blocks'])
    assert word_key(' ＳＹＮＴＨＥＴＩＣ ')==word_key('synthetic')
    with pytest.raises(ValidationError):WordCard.model_validate({**card(),'official_key':True})
    with pytest.raises(ValidationError):WordCard.model_validate({**card(),'recognition_options':['bad\x00choice','other']})
