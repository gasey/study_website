"""Resumable discovery of PDF bytes. Never writes to a source or bank file."""
import hashlib
import os
from pathlib import Path

from ..config import settings


def roots():
    return {
        'canonical': Path(settings.pdf_library_archive_root) if getattr(settings, 'pdf_library_archive_root', '') else Path(settings.canonical_workshop_root) / 'pdfs',
        'served': Path(settings.paper_archive_root),
        'workbench': Path(settings.paper_workbench_root) / 'sources',
        'documents': Path(settings.registered_document_root),
    }


def safe_path(root, relative):
    base = roots().get(root)
    if base is None or not relative or '\\' in relative:
        raise ValueError('Unknown source location')
    parts = Path(relative).parts
    if Path(relative).is_absolute() or any(p in ('.', '..') for p in parts):
        raise ValueError('Invalid source location')
    path = base
    for part in parts:
        path = path / part
        if path.is_symlink():
            raise ValueError('Symbolic links are not source files')
    if not path.resolve().is_relative_to(base.resolve()):
        raise ValueError('Source is outside the archive')
    return path


def fingerprint(path):
    before = path.stat()
    sha = hashlib.sha256()
    with path.open('rb') as file:
        header = file.read(8)
        sha.update(header)
        for chunk in iter(lambda: file.read(1024 * 1024), b''):
            sha.update(chunk)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise ValueError('Source changed during scanning; refresh the inventory')
    return sha.hexdigest(), after, header.startswith(b'%PDF-') and after.st_size >= 16


def scan(conn):
    """Caller holds the session advisory lock. Per-file commits support recovery."""
    row = conn.execute("SELECT id FROM pdf_library_scans WHERE state IN ('running','queued') ORDER BY id LIMIT 1").fetchone()
    if not row:
        return None
    sid = row['id']
    conn.execute("UPDATE pdf_library_scans SET state='running',started_at=COALESCE(started_at,now()),heartbeat_at=now(),error=NULL WHERE id=%s", (sid,))
    seen = hashed = 0
    try:
        cache = {}
        for item in conn.execute('''SELECT DISTINCT ON(root,relative_path) f.* FROM pdf_library_files f
          JOIN pdf_library_scans s ON s.id=f.scan_id
          WHERE s.state='completed' OR s.id=%s ORDER BY root,relative_path,scan_id DESC''', (sid,)).fetchall():
            cache[(item['root'], item['relative_path'])] = item
        observed = set()
        for root, folder in roots().items():
            if not folder.is_dir():
                raise ValueError('Archive root unavailable: ' + root)
            def onerror(error):
                raise OSError('Cannot read archive directory in ' + root) from error
            for parent, dirs, names in os.walk(folder, followlinks=False, onerror=onerror):
                dirs[:] = sorted(d for d in dirs if not (Path(parent) / d).is_symlink())
                for name in sorted(names):
                    if not name.lower().endswith('.pdf'):
                        continue
                    path = Path(parent) / name
                    if path.is_symlink():
                        continue
                    relative = path.relative_to(folder).as_posix()
                    observed.add((root, relative))
                    stat = path.stat()
                    previous = cache.get((root, relative))
                    if previous and (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns) == (previous['bytes'], previous['mtime_ns'], previous['ctime_ns']):
                        sha, valid = previous['sha256'], previous['valid_pdf']
                    else:
                        sha, stat, valid = fingerprint(path)
                        hashed += 1
                    conn.execute('''INSERT INTO pdf_library_files(scan_id,root,relative_path,sha256,bytes,mtime_ns,ctime_ns,valid_pdf)
                      VALUES(%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(scan_id,root,relative_path) DO UPDATE
                      SET sha256=excluded.sha256,bytes=excluded.bytes,mtime_ns=excluded.mtime_ns,ctime_ns=excluded.ctime_ns,valid_pdf=excluded.valid_pdf''',
                      (sid, root, relative, sha, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, valid))
                    seen += 1
                    if seen % 25 == 0:
                        conn.execute('UPDATE pdf_library_scans SET files_seen=%s,files_hashed=%s,heartbeat_at=now() WHERE id=%s', (seen, hashed, sid))
        # A resumed scan may have rows for files removed while it was interrupted.
        for item in conn.execute('SELECT id,root,relative_path FROM pdf_library_files WHERE scan_id=%s', (sid,)).fetchall():
            if (item['root'], item['relative_path']) not in observed:
                conn.execute('DELETE FROM pdf_library_files WHERE id=%s', (item['id'],))
        conn.execute("UPDATE pdf_library_scans SET state='completed',finished_at=now(),heartbeat_at=now(),files_seen=%s,files_hashed=%s WHERE id=%s", (seen, hashed, sid))
    except Exception:
        # Filesystem errors can contain absolute private paths. Keep them in the
        # worker journal, never in a browser response.
        conn.execute("UPDATE pdf_library_scans SET state='failed',finished_at=now(),error='Archive scan failed. The last complete inventory is retained; check the worker journal.' WHERE id=%s", (sid,))
        raise
    return sid


def main():
    import argparse
    import psycopg
    from psycopg.rows import dict_row
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', action='store_true', help='Queue a scheduled inventory refresh')
    args = parser.parse_args()
    with psycopg.connect(settings.database_url, autocommit=True, row_factory=dict_row) as conn:
        if not conn.execute('SELECT pg_try_advisory_lock(77830114) AS locked').fetchone()['locked']:
            return
        if args.request:
            conn.execute("INSERT INTO pdf_library_scans(state) VALUES('queued') ON CONFLICT DO NOTHING")
        sid = scan(conn)
        if sid:
            print('PDF inventory scan completed:', sid)


if __name__ == '__main__':
    main()
