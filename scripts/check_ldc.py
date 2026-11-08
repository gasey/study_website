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
                WHERE a.paper_id = 'Old_Questions/Direct_NG_2024-2027/LDC under MPSC Paper-I 2025..pdf'
                ORDER BY a.qnum
            ''')
            rows = await cur.fetchall()
            print(json.dumps(rows, default=str))

asyncio.run(main())
"""
proc = subprocess.run(["ssh", "ubuntu@152.67.31.231", "sudo -u postgres /srv/api/.venv/bin/python -"], input=script, text=True, capture_output=True)
rows = json.loads(proc.stdout)
with open("/tmp/reviewed_aids.json") as f:
    reviewed = set(json.load(f))
for r in rows:
    status = "REVIEWED" if r["id"] in reviewed else "UNREVIEWED"
    print(f"qnum={r['qnum']} [{status}] subj={r['subject']} | {r['question'][:60]}")
