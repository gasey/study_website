import json, subprocess

script = """
import os, sys, json, asyncio
os.chdir('/tmp')
os.environ['DATABASE_URL'] = 'postgresql:///mpsc'
import psycopg
from psycopg.rows import dict_row

papers = [
    'Old_Questions/Direct_2014-2018/2.UDC (Contract) 2016-Cooperation Paper-II.pdf',
    'Old_Questions/Direct_2014-2018/2.UDC (contract) 2016 Art& Culture Paper-II.pdf',
    'Old_Questions/Direct_2014-2018/2.UDC Direct-2014 Health Deptt.& Co-operation Dept.Paper-II.pdf',
    'Old_Questions/Direct_2014-2018/2.UDC Excise Deptt. Paper-II.pdf',
    'Old_Questions/Direct_2014-2018/2.UDC Paper-II.pdf',
    'Old_Questions/Direct_2014-2018/2.UDC under Agriculture Deptt. Paper-II.pdf',
    'Old_Questions/Direct_2014-2018/2.UDC under EF&CC Deptt. Paper-II.pdf',
    'Old_Questions/Direct_2014-2018/2.UDC under SAD Paper-II.pdf',
    'Old_Questions/Direct_2019-2020/UDC ARC Paper-II.pdf',
    'Old_Questions/Direct_2020-2021/UDC Direct under Taxation Deptt - Paper-II.pdf',
    'Old_Questions/Direct_2021-2022/UDC Direct under Fisheries Deptt - Paper-II.pdf',
]

async def main():
    async with await psycopg.AsyncConnection.connect('dbname=mpsc', row_factory=dict_row) as conn:
        async with conn.cursor() as cur:
            for p in papers:
                await cur.execute('''
                    SELECT qnum, subject, topic, question
                    FROM appearances
                    WHERE paper_id = %s
                    ORDER BY qnum::int
                ''', (p,))
                rows = await cur.fetchall()
                print(f"=== {p} ({len(rows)} items) ===")
                # Print a few samples across range
                for idx in [0, len(rows)//4, len(rows)//2, 3*len(rows)//4, len(rows)-1]:
                    if idx < len(rows):
                        r = rows[idx]
                        print(f"  qnum={r['qnum']} | {r['question'][:70]}")

asyncio.run(main())
"""

proc = subprocess.run(
    ["ssh", "ubuntu@152.67.31.231", "sudo -u postgres /srv/api/.venv/bin/python -"],
    input=script, text=True, capture_output=True, timeout=60
)
if proc.returncode:
    print("Error:", proc.stderr)
else:
    print(proc.stdout)
