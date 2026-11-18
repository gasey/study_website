"""Disposable clearly synthetic practice preview; never production content."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest,uvicorn
from test_content_studio import publish
from test_curated_vocabulary_authoring import deck,card
from test_curated_vocabulary import due_words
from test_learning_loop import questions,due
from app.routers.auth import _hash_password
from app.config import settings
prepared=conftest.fresh_database();database=next(prepared)
clients=conftest.client.__wrapped__(database);client=next(clients);conn=database[1]
try:
    actor=conftest.actor.__wrapped__(client)
    conn.execute("UPDATE users SET handle='synthetic_author',password_hash=%s WHERE id='author'",(_hash_password('SyntheticPassword123!'),))
    doc=deck();doc['title']='Synthetic word practice preview';doc['blocks']=[]
    for i in range(8):
        value=card();value.update(word='synthetic'+str(i),cloze_options=['synthetic'+str(i),'other'],cloze_sentence='Use {{word}} for this fixture.',mizo_options=['Mizo test gloss, not learning content','Other test gloss'])
        doc['blocks'].append({'id':'word'+str(i),'type':'vocabulary','vocabulary':value})
    mid=publish(client,actor,doc)
    ids=due_words(conn,'author',mid)
    conn.execute('DELETE FROM review_items WHERE user_id=%s AND vocab_card_id=ANY(%s)',('author',ids[4:]))
    _,bank=questions(database,4);due(conn,'author',bank)
    print('Synthetic practice: /vocabulary?curated_deck='+mid,flush=True)
    print('author@example.test / SyntheticPassword123!',flush=True)
finally:
    try:next(clients)
    except StopIteration:pass
settings.public_origin='http://127.0.0.1:5197'
from app.main import app
try:uvicorn.run(app,host='127.0.0.1',port=8027,log_level='warning')
finally:
    try:next(prepared)
    except StopIteration:pass
