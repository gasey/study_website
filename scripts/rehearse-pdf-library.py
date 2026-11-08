#!/usr/bin/env python3
"""Read-only source scan and query rehearsal against an explicitly disposable DB."""
import argparse
import asyncio
import importlib.util
import json
from pathlib import Path
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True)
    parser.add_argument('--staged-api', required=True)
    args = parser.parse_args()
    if not args.database.startswith('ism_pdf_cms_rehearsal_'):
        parser.error('Only an ism_pdf_cms_rehearsal_ database is allowed')
    sys.path.insert(0, '/srv/api')
    from app.config import settings
    settings.database_url = 'postgresql://mpsc@localhost:5432/' + args.database
    for module in ['pdf_library_scan', 'pdf_library']:
        spec = importlib.util.spec_from_file_location('app.services.' + module, Path(args.staged_api) / 'app/services' / (module + '.py'))
        loaded = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = loaded
        spec.loader.exec_module(loaded)
    from app.services.pdf_library_scan import scan
    from app.services.pdf_library import listing
    import psycopg
    from psycopg.rows import dict_row
    with psycopg.connect(settings.database_url, autocommit=True, row_factory=dict_row) as conn:
        conn.execute('SELECT pg_advisory_lock(77830114)')
        before = conn.execute('''SELECT (SELECT count(*) FROM papers) AS papers,
          (SELECT count(*) FROM canonical_questions) AS questions,(SELECT count(*) FROM attempts) AS attempts,
          (SELECT count(*) FROM editorial_assignment_papers) AS assigned_sources,
          (SELECT count(*) FROM review_grants WHERE revoked_at IS NULL) AS grants''').fetchone()
        conn.execute("INSERT INTO pdf_library_scans(state) VALUES('queued') ON CONFLICT DO NOTHING")
        sid = scan(conn)
        report = {'scan': conn.execute('SELECT * FROM pdf_library_scans WHERE id=%s', (sid,)).fetchone(), 'preservation_before': before}
        # A second scan should reuse every unchanged file hash.
        conn.execute("INSERT INTO pdf_library_scans(state) VALUES('queued')")
        report['repeat_scan'] = conn.execute('SELECT * FROM pdf_library_scans WHERE id=%s', (scan(conn),)).fetchone()
        report['preservation_after'] = conn.execute('''SELECT (SELECT count(*) FROM papers) AS papers,
          (SELECT count(*) FROM canonical_questions) AS questions,(SELECT count(*) FROM attempts) AS attempts,
          (SELECT count(*) FROM editorial_assignment_papers) AS assigned_sources,
          (SELECT count(*) FROM review_grants WHERE revoked_at IS NULL) AS grants''').fetchone()
        assert report['preservation_after'] == before
        assert report['repeat_scan']['files_hashed'] == 0

    async def queries():
        async with await psycopg.AsyncConnection.connect(settings.database_url, row_factory=dict_row, options='-c jit=off') as conn:
            async with conn.cursor() as cur:
                output = {}
                for name, kwargs in [('all', {}), ('empty', {'gap': 'empty'}), ('udc', {'module': 'udc'}), ('unlinked', {'gap': 'unlinked'}), ('registration', {'gap': 'registration'})]:
                    start = time.monotonic()
                    result = await listing(cur, sid, **kwargs)
                    output[name] = {'total': result['total'], 'summary': result['summary'], 'seconds': round(time.monotonic() - start, 3),
                                    'sample': [{key: row[key] for key in ['paper_id', 'title', 'asset_count', 'file_status', 'questions', 'missing_registration']} for row in result['items'][:2]]}
                return output
    report['queries'] = asyncio.run(queries())
    print(json.dumps(report, default=str, indent=2))


if __name__ == '__main__':
    main()
