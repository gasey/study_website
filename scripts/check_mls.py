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
                WHERE a.paper_id = 'Old_Questions/Direct_2014-2018/5.Jr. Administrative Grade and Sr. Grade of Mizoram Legal Service 2016 GK & Aptitute Test (Common).pdf'
                ORDER BY a.qnum::int
            ''')
            rows = await cur.fetchall()
            print(f"Total: {len(rows)}")
            for r in rows:
                print(f"#{r['qnum']}: {r['question'][:75]}")

asyncio.run(main())
"""

proc = subprocess.run(
    ["ssh", "ubuntu@152.67.31.231", "sudo -u postgres /srv/api/.venv/bin/python -"],
    input=script, text=True, capture_output=True, timeout=30
)
print(proc.stdout)
