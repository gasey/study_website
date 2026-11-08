"""Bind an independently reviewed draft to one registered, empty source paper."""
from fastapi import HTTPException
from .review_policy import digest

IDENTITY_COLUMNS = 'id,exam_type,exam_name,post,paper_number,paper_subject,year,month,kind,source_file,pdf_path,sitting_id,exam_scope_id'


async def registered_sources(cur, sha):
    await cur.execute("SELECT id,paper_id,title,source_file,sha256 FROM review_documents WHERE sha256=%s AND kind='paper' ORDER BY id", (sha,))
    documents = await cur.fetchall()
    candidates = []
    for pid in sorted({d['paper_id'] for d in documents if d['paper_id']}):
        await cur.execute('SELECT '+IDENTITY_COLUMNS+' FROM papers WHERE id=%s', (pid,))
        paper = await cur.fetchone()
        if not paper:
            continue
        snapshot = {'paper': paper, 'documents': documents}
        await cur.execute('SELECT count(*) AS n FROM appearances WHERE paper_id=%s', (pid,))
        count = (await cur.fetchone())['n']
        candidates.append({'paper_id': pid, 'exam_name': paper['exam_name'], 'year': paper['year'],
                           'paper_subject': paper['paper_subject'], 'source_version': digest(snapshot),
                           'question_count': count, 'unambiguous': {d['paper_id'] for d in documents} == {pid},
                           'snapshot': snapshot})
    return documents, candidates


async def validate_target(cur, payload, sha, *, require_empty=True, publication=False):
    documents, candidates = await registered_sources(cur, sha)
    if not payload.target_paper_id:
        # An interrupted publication of a new uploaded paper may already have
        # registered its own source. Its immutable bank receipt still gates retry.
        uploaded = 'Old_Questions/Uploaded/'+sha+'.pdf'
        if documents and not (publication and {d['paper_id'] for d in documents} == {uploaded}):
            raise HTTPException(409, 'This PDF is registered. Select its empty original paper, or review its existing questions.')
        return None
    target = next((c for c in candidates if c['paper_id'] == payload.target_paper_id), None)
    if not target or not target['unambiguous']:
        raise HTTPException(409, 'The PDF must match exactly one registered original paper.')
    if target['source_version'] != payload.target_source_version:
        raise HTTPException(409, 'The registered source changed. Refresh its link and obtain a new independent review.')
    if require_empty and target['question_count']:
        raise HTTPException(409, 'This paper already has questions. Use its existing review workflow.')
    if (payload.exam_name, payload.year, payload.paper_subject or None) != (target['exam_name'], target['year'], target['paper_subject']):
        raise HTTPException(422, 'Keep the registered exam name, year and paper subject when filling its empty source.')
    return target
