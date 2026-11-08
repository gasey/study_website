"""Private PDF library: reconcile sources and continue established workflows."""
import hashlib
import os
import tempfile
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from psycopg.types.json import Jsonb
from starlette.concurrency import run_in_threadpool

from ..db import cursor
from ..services import pdf_library
from ..services.pdf_library_scan import safe_path
from ..services.review_identity import Actor, identity
from .current_affairs import no_assessment
from .materials import private
from .paper_workbench import global_access, storage, source_path, MAX_UPLOAD, Payload, Process, history, job
from ..services.paper_targets import registered_sources
from ..services import bank_review

router = APIRouter(prefix='/api/admin/bank/pdf-library', tags=['PDF library'], dependencies=[Depends(private)])
Account = Annotated[Actor, Depends(identity)]


async def access(cur, actor, write=False):
    await no_assessment(cur, actor.id)
    await global_access(cur, actor.id, write)


async def latest_scan(cur):
    await cur.execute("SELECT id,finished_at,files_seen,files_hashed FROM pdf_library_scans WHERE state='completed' ORDER BY id DESC LIMIT 1")
    return await cur.fetchone()


@router.get('/status')
async def status(actor: Account):
    async with cursor() as cur:
        await access(cur, actor)
        snapshot = await latest_scan(cur)
        await cur.execute('SELECT * FROM pdf_library_scans ORDER BY id DESC LIMIT 1')
        latest = await cur.fetchone()
        await cur.execute("SELECT id,title FROM collections WHERE visibility='public' AND live_version IS NOT NULL ORDER BY title")
        modules = await cur.fetchall()
        await cur.execute("SELECT worker_id,status,seen_at>now()-interval '2 minutes' AS available FROM review_worker_health WHERE worker_id IN ('oracle-paper-documents','oracle-paper-publisher')")
        workers = await cur.fetchall()
        await cur.execute("SELECT count(*)::int AS n FROM paper_workbench_jobs WHERE state IN ('queued','running')")
        return {'snapshot': snapshot, 'latest': latest, 'modules': modules, 'workers': workers, 'active_jobs': (await cur.fetchone())['n']}


@router.post('/scans', status_code=202)
async def request_scan(actor: Account):
    async with cursor() as cur:
        await access(cur, actor, True)
        await cur.execute("INSERT INTO pdf_library_scans(state,requested_by) VALUES('queued',%s) ON CONFLICT DO NOTHING RETURNING id", (actor.id,))
        result = await cur.fetchone()
        if result:
            await bank_review.event(cur, None, actor.id, 'pdf_library_scan_requested', result)
        else:
            await cur.execute("SELECT id FROM pdf_library_scans WHERE state IN ('queued','running')")
            result = await cur.fetchone()
        return result


@router.get('/items')
async def items(actor: Account, q: str = Query('', max_length=200),
                gap: Literal['', 'empty', 'unlinked', 'ambiguous', 'registration', 'missing-file', 'review', 'answers', 'attention'] = '',
                module: str = Query('', max_length=100), year: int | None = Query(None, ge=1900, le=2100),
                kind: str = Query('', max_length=80), key: str = Query('', max_length=700),
                offset: int = Query(0, ge=0, le=100000), limit: int = Query(20, ge=1, le=100)):
    async with cursor() as cur:
        await access(cur, actor)
        snapshot = await latest_scan(cur)
        result = await pdf_library.listing(cur, snapshot['id'] if snapshot else None, q=q, gap=gap,
                                           module=module, year=year, kind=kind, key=key, offset=offset, limit=limit)
        return {**result, 'snapshot': snapshot}


@router.get('/activity')
async def activity(actor: Account, before: int | None = Query(None, ge=1)):
    async with cursor() as cur:
        await access(cur, actor)
        await cur.execute('''SELECT j.id,j.draft_id,j.kind,j.state,j.attempts,j.error,j.result,j.created_at,j.finished_at,
          d.payload->>'title' AS title,d.state AS draft_state,d.published_paper_id
          FROM paper_workbench_jobs j JOIN paper_workbench_drafts d ON d.id=j.draft_id
          WHERE (%s::bigint IS NULL OR extract(epoch FROM j.created_at)*1000000<%s)
          ORDER BY j.created_at DESC,j.id LIMIT 50''', (before, before))
        rows = await cur.fetchall()
        await cur.execute('SELECT id,state,files_seen,files_hashed,error,created_at,finished_at FROM pdf_library_scans ORDER BY id DESC LIMIT 10')
        scans = await cur.fetchall()
        await cur.execute('SELECT bank_checksum,finished_at FROM sync_log WHERE finished_at IS NOT NULL ORDER BY finished_at DESC LIMIT 1')
        return {'jobs': rows, 'scans': scans, 'sync': await cur.fetchone()}


async def file_record(cur, fid):
    snapshot = await latest_scan(cur)
    # File links remain usable after a later scan only if they still describe
    # the same bytes; transfer revalidates the actual hash below.
    await cur.execute('''SELECT f.* FROM pdf_library_files f JOIN pdf_library_scans s ON s.id=f.scan_id
      WHERE f.id=%s AND s.state='completed' ''', (fid,))
    row = await cur.fetchone()
    if not row or not snapshot:
        raise HTTPException(404, 'Scanned PDF not found; refresh the library')
    try:
        path = safe_path(row['root'], row['relative_path'])
        st = path.stat()
    except (ValueError, OSError):
        raise HTTPException(409, 'The source file is unavailable; refresh the inventory')
    if (st.st_size, st.st_mtime_ns, st.st_ctime_ns) != (row['bytes'], row['mtime_ns'], row['ctime_ns']):
        raise HTTPException(409, 'The source changed; refresh the inventory before continuing')
    if not row['valid_pdf']:
        raise HTTPException(422, 'This file has no valid PDF header; inspect its archive entry')
    return row, path


@router.get('/files/{fid}')
async def source(fid: int, actor: Account):
    async with cursor() as cur:
        await access(cur, actor)
        row, path = await file_record(cur, fid)
    return FileResponse(path, media_type='application/pdf', filename=Path(row['relative_path']).name,
                        content_disposition_type='inline', headers={'Cache-Control': 'private, no-store'})


class Intake(BaseModel):
    model_config = ConfigDict(extra='forbid')
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    paper_id: str | None = Field(default=None, max_length=600)


def stage_source(path, row):
    folder = storage() / 'sources'
    folder.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=folder, prefix='.library-')
    sha = hashlib.sha256()
    size = 0
    try:
        with os.fdopen(fd, 'wb') as target, path.open('rb') as source:
            for block in iter(lambda: source.read(1024 * 1024), b''):
                size += len(block)
                if size > MAX_UPLOAD:
                    raise HTTPException(413, 'The workbench accepts PDFs up to 20 MB')
                sha.update(block)
                target.write(block)
            target.flush()
            os.fsync(target.fileno())
        if sha.hexdigest() != row['sha256'] or size != row['bytes']:
            raise HTTPException(409, 'PDF bytes changed; refresh the inventory')
        # Atomic replacement also repairs a stale/corrupt content-addressed copy.
        os.replace(name, source_path(row['sha256']))
    finally:
        if os.path.exists(name):
            os.unlink(name)


@router.post('/files/{fid}/intake')
async def intake(fid: int, body: Intake, actor: Account):
    from uuid import uuid4
    async with cursor() as cur:
        await access(cur, actor, True)
        row, path = await file_record(cur, fid)
        if row['sha256'] != body.sha256:
            raise HTTPException(409, 'The selected PDF changed')
        # Serializes double-clicks and different aliases of the same PDF.
        await cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,771))', (row['sha256'],))
        await cur.execute('''SELECT id,state,published_paper_id,payload->>'target_paper_id' AS target_paper_id FROM paper_workbench_drafts
          WHERE source_sha256=%s ORDER BY updated_at DESC,id LIMIT 1''', (row['sha256'],))
        existing = await cur.fetchone()
        if existing:
            if body.paper_id and existing['target_paper_id'] not in (None,body.paper_id) and existing['published_paper_id'] != body.paper_id:
                raise HTTPException(409, 'This PDF already has a draft linked to a different registered source; inspect it first')
            return {key:value for key,value in {**existing, 'reused': True}.items() if key!='target_paper_id'}
        documents, candidates = await registered_sources(cur, row['sha256'])
        target = None
        if body.paper_id:
            target = next((c for c in candidates if c['paper_id'] == body.paper_id and c['unambiguous']), None)
            if not target:
                raise HTTPException(409, 'Register and reconcile this original PDF before importing its questions')
        elif documents:
            raise HTTPException(409, 'Choose the registered original paper before importing this PDF')
        if target and target['question_count']:
            raise HTTPException(409, 'This original already has questions; open its existing review workspace')
        # Reject a path-linked source with missing/conflicting registration rather
        # than creating an Uploaded alias of the original.
        if not target and row['root'] in ('canonical', 'served'):
            await cur.execute("SELECT 1 FROM papers WHERE regexp_replace(COALESCE(source_file,id),'^pdfs/','')=%s LIMIT 1", (row['relative_path'],))
            if await cur.fetchone():
                raise HTTPException(409, 'This path belongs to an existing paper; reconcile its document registration first')
        await cur.execute("SELECT 1 FROM review_documents WHERE sha256=%s AND kind<>'paper' LIMIT 1", (row['sha256'],))
        if await cur.fetchone() and not target:
            raise HTTPException(409, 'This is a registered reference/key document; attach it in the paper workbench')
        if row['bytes'] > MAX_UPLOAD:
            raise HTTPException(413, 'The workbench accepts PDFs up to 20 MB')
        try:
            await run_in_threadpool(stage_source, path, row)
        except OSError:
            raise HTTPException(409, 'Could not prepare this source; ask the operator to check archive permissions')
        title = Path(row['relative_path']).stem[:300]
        p = Payload(title=title if len(title) >= 3 else 'Source paper',
                    exam_name=(target['exam_name'] if target else None) or 'Exam identity to confirm',
                    year=target['year'] if target else None,
                    paper_subject=(target['paper_subject'] if target else '') or '',
                    target_paper_id=target['paper_id'] if target else None,
                    target_source_version=target['source_version'] if target else None)
        await cur.execute('''INSERT INTO paper_workbench_assets(sha256,bytes,filename,created_by)
          VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING''', (row['sha256'], row['bytes'], Path(row['relative_path']).name[:200], actor.id))
        did = 'pwdraft_' + uuid4().hex
        await cur.execute('''INSERT INTO paper_workbench_drafts(id,author_id,source_sha256,payload)
          VALUES(%s,%s,%s,%s) RETURNING *''', (did, actor.id, row['sha256'], Jsonb(p.model_dump())))
        draft = await cur.fetchone()
        await history(cur, draft, actor, 'created')
        jid = await job(cur, did, 'extract', Process(kind='extract').model_dump())
        await bank_review.event(cur, None, actor.id, 'pdf_library_intake', {'draft': did, 'file_id': fid, 'sha256': row['sha256'], 'paper_id': body.paper_id})
        return {'id': did, 'job_id': jid, 'reused': False}
