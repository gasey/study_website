import json, subprocess

script = """
import os, sys, json, asyncio
os.chdir('/tmp')
os.environ['DATABASE_URL'] = 'postgresql:///mpsc'
import psycopg
from psycopg.rows import dict_row

async def main():
    async with await psycopg.AsyncConnection.connect('dbname=mpsc', row_factory=dict_row) as conn:
        async with conn.cursor() as cur:
            await cur.execute('''
                SELECT a.id, a.qnum, a.subject, a.topic, a.question
                FROM appearances a
                WHERE a.paper_id = 'Old_Questions/Direct_NG_2024-2027/Assistant, UDC Paper-II Series A..pdf'
                ORDER BY a.qnum
            ''')
            rows = await cur.fetchall()
            print(json.dumps(rows, default=str))

asyncio.run(main())
"""

proc = subprocess.run(
    ["ssh", "ubuntu@152.67.31.231", "sudo -u postgres /srv/api/.venv/bin/python -"],
    input=script, text=True, capture_output=True, timeout=60
)
if proc.returncode:
    print("Error:", proc.stderr)
else:
    rows = json.loads(proc.stdout)
    with open("/tmp/reviewed_aids.json") as f:
        reviewed = set(json.load(f))
    rev_items = [r for r in rows if r["id"] in reviewed]
    unrev_items = [r for r in rows if r["id"] not in reviewed]
    print(f"Total: {len(rows)}, Reviewed: {len(rev_items)}, Unreviewed: {len(unrev_items)}")
    print("Sample reviewed items:")
    for r in rev_items[:5]:
        print(f"  #{r['qnum']}: subj={r['subject']} | topic={r['topic']} | text={r['question'][:50]}")
    print("Sample unreviewed items:")
    for r in unrev_items[:5]:
        print(f"  #{r['qnum']}: subj={r['subject']} | topic={r['topic']} | text={r['question'][:50]}")
