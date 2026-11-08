#!/usr/bin/env python3
"""SSH-only coordinator; run as postgres, separate from the web/API deployment."""
import asyncio
import json
import os
import sys
from pathlib import Path

from tagging_queue_store import Store, validate_candidates
import importlib.util

spec = importlib.util.spec_from_file_location('coverage', Path(__file__).with_name('audit-review-coverage.py'))
coverage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coverage)

STATE = Path('/var/lib/ism-tagging-coordination')


def read_bank(mode, rows=()):
    # Source bank and application database are always read-only in this tool.
    os.chdir('/tmp')
    os.environ['DATABASE_URL'] = 'postgresql:///mpsc'
    sys.path.insert(0, '/srv/api')
    import psycopg
    from psycopg.rows import dict_row
    from app.services.bank_review import snapshot
    from app.services.review_policy import digest
    from app.services.taxonomy_review_progress import progress, signature_sql

    async def read():
        async with await psycopg.AsyncConnection.connect('dbname=mpsc', row_factory=dict_row,
                                                       options='-c jit=off') as conn:
            async with conn.cursor() as cur:
                await cur.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                await cur.execute("SET LOCAL statement_timeout='90s'")
                if mode == 'progress':
                    return await progress(cur)
                await cur.execute('SELECT * FROM review_taxonomy WHERE active ORDER BY id')
                taxonomy = await cur.fetchall()
                await cur.execute("SELECT id,paper_id,source_file,sha256,kind FROM review_documents WHERE kind='paper' ORDER BY id")
                documents = await cur.fetchall()
                if mode == 'inventory':
                    await cur.execute('SELECT now() AS at')
                    at = str((await cur.fetchone())['at'])
                    await cur.execute('''SELECT id,canonical_id,paper_id,qnum,qnum_seq,page,
                      is_primary,type,has_diagram FROM appearances ORDER BY id''')
                    appearances = await cur.fetchall()
                    await cur.execute("""WITH latest AS (
                      SELECT DISTINCT ON(detail->>'canonical_id') detail FROM contribution_events
                      WHERE action='owner_ai_taxonomy_progress' ORDER BY detail->>'canonical_id',id DESC)
                      SELECT c.id FROM latest r JOIN appearances a ON a.id=r.detail->>'appearance_id'
                      JOIN canonical_questions c ON c.id=a.canonical_id
                      JOIN papers p ON p.id=a.paper_id LEFT JOIN question_classifications qc
                      ON qc.question_id=c.id AND qc.review_status='approved'
                      WHERE r.detail->>'status' IN ('published','confirmed')
                      AND r.detail->>'source_signature'=""" + signature_sql())
                    completed = [r['id'] for r in await cur.fetchall()]
                    await cur.execute("""WITH latest AS (
                      SELECT DISTINCT ON(detail->>'canonical_id') detail,created_at FROM contribution_events
                      WHERE action='owner_ai_taxonomy_progress' ORDER BY detail->>'canonical_id',id DESC)
                      SELECT detail,extract(epoch from created_at)AS blocked_at FROM latest WHERE detail->>'status'='blocked'""")
                    blocked={r['detail']['canonical_id']:{**r['detail'],'blocked_at':float(r['blocked_at'])}for r in await cur.fetchall()}
                    return {'exported_at': at, 'appearances': appearances,
                            'documents': documents, 'taxonomy': taxonomy, 'completed_ids': completed,
                            'blocked_outcomes':blocked}
                items = []
                for row in rows:
                    snap = await snapshot(cur, row['canonical_id'], row['appearance_id'])
                    items.append({'canonical_id': row['canonical_id'], 'appearance_id': row['appearance_id'],
                                  'snapshot': snap, 'source_fingerprint': digest(snap),
                                  'documents': [d for d in documents if d['paper_id'] == snap['paper']['id']],
                                  'previous_review': json.loads(row['legacy']) if row.get('legacy') else None})
                return {'items': items, 'taxonomy': taxonomy}
    return asyncio.run(read())


def main():
    os.umask(0o077)
    request = json.load(sys.stdin)
    store = Store(STATE / 'queue.sqlite')
    command = request['command']
    if command == 'sync':
        result = store.sync(read_bank('inventory'), request['exclusions'], request['followups'], coverage.family)
    elif command == 'claim':
        result = store.claim(request['worker'], request['model'], request['lane'], request['size'],
                             lambda rows: read_bank('packet', rows), request['packet_id'], request['token'])
    elif command == 'resume':
        result = store.resume(request['packet_id'], request['token'])
    elif command == 'save':
        result = store.save(request['packet_id'], request['token'], request['draft'])
    elif command == 'submit':
        def validate(packet, candidates):
            rows = [{'canonical_id': i['canonical_id'], 'appearance_id': i['appearance_id']}
                    for i in packet['items']]
            validate_candidates(packet, candidates, read_bank('packet', rows))
        result = store.submit(request['packet_id'], request['token'], request['candidates'], validate)
    elif command == 'release':
        result = store.release(request['packet_id'], request['token'], request['reason'], request['defer'])
    elif command == 'status':
        result = store.status()
        result['published_tagging_pass'] = read_bank('progress')
    else:
        raise ValueError('Unsupported command')
    print(json.dumps(result, ensure_ascii=False, default=str))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'error': str(exc)}))
        sys.exit(1)
