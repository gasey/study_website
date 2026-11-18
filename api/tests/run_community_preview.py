"""Disposable V.10 UI preview. Synthetic content only; Ctrl-C drops its DB."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import conftest, uvicorn
from test_discussions import answer, create, approve
from app.routers.auth import _hash_password
from app.config import settings

prepared = conftest.fresh_database()
database = next(prepared)
clients = conftest.client.__wrapped__(database)
client = next(clients)
conn = database[1]
try:
    actor = conftest.actor.__wrapped__(client)
    h = answer(client, actor, 'cq_test', 'outsider')
    for body, kind in [
        ('Synthetic preview: why is option B correct in this practice question?', 'doubt'),
        ('Synthetic preview: compare the wording with the source before choosing an option.', 'explanation'),
    ]:
        result = create(client, h, 'cq_test', body=body, kind=kind)
        assert result.status_code == 201, result.text
        approve(client, actor, result.json()['id'])
        h = actor('outsider')
    conn.execute("INSERT INTO creator_profiles(user_id,public) VALUES('outsider',true)")
    h = answer(client, actor, 'cq_test', 'author')
    assert client.post('/api/creators/outsider/follow', headers=h, json={'enabled':True}).status_code == 200
    conn.execute("UPDATE users SET password_hash=%s WHERE id='author'", (_hash_password('SyntheticPassword123!'),))
finally:
    try:
        next(clients)
    except StopIteration:
        pass
settings.public_origin = 'http://127.0.0.1:5189'
print('Synthetic community preview: author@example.test / SyntheticPassword123!; question cq_test. No production activity.', flush=True)
from app.main import app
try:
    uvicorn.run(app, host='127.0.0.1', port=8019, log_level='warning')
finally:
    try:
        next(prepared)
    except StopIteration:
        pass
