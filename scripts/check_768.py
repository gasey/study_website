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
                SELECT a.id, a.canonical_id, a.qnum, a.subject, a.topic, a.question
                FROM appearances a
                WHERE a.paper_id = 'Old_Questions/Uploaded/768a298a6ef575d791958086c0626c7519bfecc094f850d63a05377746246336.pdf'
                ORDER BY a.qnum
            ''')
            print(json.dumps(await cur.fetchall(), default=str))

asyncio.run(main())
"""

proc = subprocess.run(
    ["ssh", "ubuntu@152.67.31.231", "sudo -u postgres /srv/api/.venv/bin/python -"],
    input=script, text=True, capture_output=True, timeout=30
)
rows = json.loads(proc.stdout)
with open("/tmp/reviewed_aids.json") as f:
    reviewed = set(json.load(f))
for r in rows:
    if r["id"] not in reviewed:
        print(f"Unreviewed in 768a298: aid={r['id']} cid={r['canonical_id']} qnum={r['qnum']} subj={r['subject']} topic={r['topic']} text={r['question'][:70]}")
