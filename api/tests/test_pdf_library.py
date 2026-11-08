"""Archive reconciliation and private intake against disposable PostgreSQL."""
import hashlib
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg.rows import dict_row

from app.config import settings
from app.services.pdf_library_scan import scan, safe_path
from test_admin_workbench import workbench

BASE = '/api/admin/bank/pdf-library'


@pytest.fixture
def archive(database, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'canonical_workshop_root', str(tmp_path / 'bank'))
    monkeypatch.setattr(settings, 'paper_archive_root', str(tmp_path / 'served'))
    monkeypatch.setattr(settings, 'paper_workbench_root', str(tmp_path / 'workbench'))
    monkeypatch.setattr(settings, 'registered_document_root', str(tmp_path / 'documents'))
    for folder in ['bank/pdfs/Old_Questions', 'bank/pdfs/Answer_Keys', 'served/Old_Questions', 'workbench/sources', 'documents']:
        (tmp_path / folder).mkdir(parents=True)
    with psycopg.connect('dbname=' + database[0], autocommit=True, row_factory=dict_row) as conn:
        yield tmp_path, conn


def pdf(root, name, data=None):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    data = data or b'%PDF-1.4\nSynthetic source ' + uuid4().hex.encode()
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def run_scan(conn):
    conn.execute("INSERT INTO pdf_library_scans(state) VALUES('queued') ON CONFLICT DO NOTHING")
    return scan(conn)


def test_private_roles_scan_csrf_and_no_answer_leak(client, actor, archive):
    for user in ['outsider', 'reviewer1']:
        actor(user)
        assert client.get(BASE + '/status').status_code == 403
        assert client.get(BASE + '/items').status_code == 403
        assert client.get(BASE + '/activity').status_code == 403
    headers = actor('owner')
    assert client.post(BASE + '/scans', json={}).status_code == 403
    first = client.post(BASE + '/scans', json={}, headers=headers)
    assert first.status_code == 202, first.text
    assert client.post(BASE + '/scans', json={}, headers=headers).json() == first.json()
    assert client.get(BASE + '/items', params={'gap': 'invented'}).status_code == 422
    assert client.get(BASE + '/items', params={'limit': 101}).status_code == 422


def test_scan_hash_aliases_reuse_resume_and_failed_snapshot(client, actor, archive, monkeypatch):
    root, conn = archive
    sha = pdf(root, 'bank/pdfs/Old_Questions/alias.pdf')
    data = (root / 'bank/pdfs/Old_Questions/alias.pdf').read_bytes()
    pdf(root, 'served/Old_Questions/alias.pdf', data)
    (root / 'bank/pdfs/Old_Questions/escape.pdf').symlink_to('/etc/passwd')
    sid = run_scan(conn)
    row = conn.execute('SELECT * FROM pdf_library_scans WHERE id=%s', (sid,)).fetchone()
    assert row['files_seen'] == 2 and row['files_hashed'] == 2
    from app.services import pdf_library_scan
    real = pdf_library_scan.fingerprint
    monkeypatch.setattr(pdf_library_scan, 'fingerprint', lambda p: pytest.fail('Unchanged bytes should reuse their hashes'))
    second = run_scan(conn)
    assert conn.execute('SELECT files_hashed FROM pdf_library_scans WHERE id=%s', (second,)).fetchone()['files_hashed'] == 0
    monkeypatch.setattr(pdf_library_scan, 'fingerprint', real)
    # Simulate a stopped worker with a partially persisted running generation.
    next_id = conn.execute("INSERT INTO pdf_library_scans(state) VALUES('running') RETURNING id").fetchone()['id']
    conn.execute('''INSERT INTO pdf_library_files(scan_id,root,relative_path,sha256,bytes,mtime_ns,ctime_ns,valid_pdf)
      SELECT %s,root,relative_path,sha256,bytes,mtime_ns,ctime_ns,valid_pdf FROM pdf_library_files WHERE scan_id=%s''', (next_id, second))
    (root / 'served/Old_Questions/alias.pdf').unlink()
    assert scan(conn) == next_id
    assert conn.execute('SELECT count(*) AS n FROM pdf_library_files WHERE scan_id=%s', (next_id,)).fetchone()['n'] == 1
    actor('owner')
    page = client.get(BASE + '/items', params={'q': sha, 'gap': 'unlinked'}).json()
    assert page['total'] == 1 and page['items'][0]['copies'] == 1
    (root / 'documents').rmdir()
    with pytest.raises(ValueError):
        run_scan(conn)
    state = client.get(BASE + '/status').json()
    assert state['snapshot']['id'] == next_id and state['latest']['state'] == 'failed'
    assert str(root) not in state['latest']['error']
    with pytest.raises(ValueError):
        safe_path('served', '../outside.pdf')
    with pytest.raises(ValueError):
        safe_path('canonical', 'Old_Questions/escape.pdf')


def test_reconciliation_empty_paper_missing_registration_conflict_and_counts(client, actor, archive):
    root, conn = archive
    tag = uuid4().hex
    pid = 'pdf-test-' + tag
    relative = 'Old_Questions/' + tag + '.pdf'
    sha = pdf(root, 'bank/pdfs/' + relative)
    pdf(root, 'served/' + relative, (root / ('bank/pdfs/' + relative)).read_bytes())
    conn.execute("INSERT INTO papers(id,exam_name,exam_type,source_file,year) VALUES(%s,'Synthetic library original','Direct',%s,2024)", (pid, relative))
    run_scan(conn)
    actor('owner')
    response = client.get(BASE + '/items', params={'key': 'paper:' + pid})
    assert response.status_code == 200, response.text
    item = response.json()['items'][0]
    assert item['questions'] == 0 and item['empty_paper'] and item['missing_registration']
    assert item['asset_count'] == 1 and item['copies'] == 2 and not item['unlinked']
    assert client.get(BASE + '/items', params={'q': pid, 'gap': 'registration'}).json()['total'] == 1
    conn.execute("INSERT INTO review_documents(id,paper_id,title,source_file,sha256,kind,registered_by) VALUES(%s,%s,'Source','pdfs/'||%s,%s,'paper','test')", (tag, pid, relative, sha))
    assert client.get(BASE + '/items', params={'key': item['key']}).json()['items'][0]['missing_registration'] is False
    # Same path but different bytes is ambiguous, never an automatic source choice.
    pdf(root, 'served/' + relative)
    run_scan(conn)
    conflict = client.get(BASE + '/items', params={'key': item['key'], 'gap': 'ambiguous'}).json()
    assert conflict['total'] == 1 and conflict['items'][0]['asset_count'] == 2
    assert client.get(BASE + '/items', params={'q': pid, 'offset': 10000}).json()['total'] == 1
    assert client.get(BASE + '/items', params={'q': pid, 'offset': 10000}).json()['items'] == []


def test_intake_existing_empty_original_idempotency_stale_bytes_and_roles(client, actor, archive):
    root, conn = archive
    tag = uuid4().hex
    pid = 'pdf-intake-' + tag
    relative = 'Old_Questions/' + tag + '.pdf'
    sha = pdf(root, 'bank/pdfs/' + relative)
    conn.execute("INSERT INTO papers(id,exam_name,exam_type,source_file,year,paper_subject) VALUES(%s,'Synthetic registered exam','Direct',%s,2020,'English')", (pid, relative))
    conn.execute("INSERT INTO review_documents(id,paper_id,title,source_file,sha256,kind,registered_by) VALUES(%s,%s,'Source',%s,%s,'paper','test')", (tag, pid, relative, sha))
    run_scan(conn)
    headers = actor('owner')
    item = client.get(BASE + '/items', params={'key': 'paper:' + pid}).json()['items'][0]
    fid = item['file_id']
    assert client.get(BASE + '/files/' + str(fid)).content.startswith(b'%PDF-')
    response = client.post(BASE + '/files/' + str(fid) + '/intake', headers=headers, json={'sha256': sha, 'paper_id': pid})
    assert response.status_code == 200, response.text
    did = response.json()['id']
    assert client.post(BASE + '/files/' + str(fid) + '/intake', headers=headers, json={'sha256': sha, 'paper_id': pid}).json() == {'id': did, 'state': 'draft', 'published_paper_id': None, 'reused': True}
    draft = client.get('/api/paper-workbench/drafts/' + did).json()
    assert draft['payload']['target_paper_id'] == pid
    assert draft['payload']['exam_name'] == 'Synthetic registered exam' and draft['payload']['paper_subject'] == 'English'
    assert len(draft['jobs']) == 1 and draft['jobs'][0]['state'] == 'queued'
    duplicate = client.post('/api/paper-workbench/drafts', headers=headers, json={
        'source_sha256': sha, 'title': 'Same uploaded bytes', 'exam_name': 'Identity to confirm'})
    assert duplicate.status_code == 201 and duplicate.json()['id'] == did and duplicate.json()['reused']
    assert not conn.execute('SELECT 1 FROM appearances WHERE paper_id=%s', (pid,)).fetchone()
    assert client.get(BASE + '/activity').json()['jobs'][0]['draft_id'] == did
    pdf(root, 'bank/pdfs/' + relative)
    assert client.get(BASE + '/files/' + str(fid)).status_code == 409
    assert client.post(BASE + '/files/' + str(fid) + '/intake', headers=headers, json={'sha256': sha, 'paper_id': pid}).status_code == 409
    headers = actor('reviewer1')
    assert client.post(BASE + '/files/' + str(fid) + '/intake', headers=headers, json={'sha256': sha}).status_code == 403


def test_unlinked_intake_no_duplicate_original_or_key_and_assessment_guard(client, actor, archive):
    root, conn = archive
    tag = uuid4().hex
    sha = pdf(root, 'bank/pdfs/Old_Questions/new-' + tag + '.pdf')
    run_scan(conn)
    headers = actor('owner')
    item = client.get(BASE + '/items', params={'key': 'file:' + sha}).json()['items'][0]
    assert item['unlinked'] and item['kind'] == 'paper'
    result = client.post(BASE + '/files/' + str(item['file_id']) + '/intake', headers=headers, json={'sha256': sha})
    assert result.status_code == 200, result.text
    assert result.json()['reused'] is False
    assert not client.get('/api/paper-workbench/drafts/' + result.json()['id']).json()['payload']['target_paper_id']
    # A registered path without its document record must never become Uploaded/.
    relative = 'Old_Questions/missing-' + tag + '.pdf'
    other = pdf(root, 'bank/pdfs/' + relative)
    conn.execute("INSERT INTO papers(id,exam_name,exam_type,source_file) VALUES(%s,'Registration missing','Direct',%s)", (tag, relative))
    run_scan(conn)
    record = client.get(BASE + '/items', params={'key': 'paper:' + tag}).json()['items'][0]
    assert client.post(BASE + '/files/' + str(record['file_id']) + '/intake', headers=headers, json={'sha256': other}).status_code == 409
    key_sha = pdf(root, 'bank/pdfs/Answer_Keys/' + tag + '.pdf')
    conn.execute("INSERT INTO review_documents(id,title,source_file,sha256,kind,key_status,registered_by) VALUES(%s,'Official synthetic key','keys/synthetic.pdf',%s,'official-key','provisional','test')", ('key-' + tag, key_sha))
    run_scan(conn)
    key = client.get(BASE + '/items', params={'key': 'file:' + key_sha}).json()['items'][0]
    assert key['kind'] == 'official-key'
    assert client.post(BASE + '/files/' + str(key['file_id']) + '/intake', headers=headers, json={'sha256': key_sha}).status_code == 409
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,'owner','ldc',ARRAY['cq_test'],60)", (tag,))
    try:
        assert client.get(BASE + '/files/' + str(item['file_id'])).status_code == 409
        assert client.get(BASE + '/activity').status_code == 409
    finally:
        conn.execute('DELETE FROM mock_sessions WHERE id=%s', (tag,))


def test_detail_uses_existing_answer_status_rules(client, actor, archive, workbench):
    _, paper, _ = workbench
    actor('owner')
    response = client.get(BASE + '/items', params={'key': 'paper:' + paper})
    assert response.status_code == 200, response.text
    item = response.json()['items'][0]
    original = client.get('/api/admin/bank/inventory/paper', params={'paper_id': paper}).json()
    for field in ['questions', 'official', 'verified', 'needs_review', 'unsolved', 'written']:
        assert item[field] == original[field], (field, item[field], original[field])
