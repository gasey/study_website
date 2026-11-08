import json, subprocess

script = """
import os, sys, json, asyncio
os.chdir('/tmp')
os.environ['DATABASE_URL'] = 'postgresql:///mpsc'
import psycopg
from psycopg.rows import dict_row

papers = [
    'Old_Questions/Direct_2014-2018/2.UDC Direct-2014 Health Deptt.& Co-operation Dept.Paper-II.pdf',
    'Old_Questions/Direct_2014-2018/2.UDC (contract) 2016 Art& Culture Paper-II.pdf',
    'Old_Questions/Direct_2014-2018/2.UDC Excise Deptt. Paper-II.pdf',
    'Old_Questions/Direct_2014-2018/2.UDC Paper-II.pdf',
    'Old_Questions/Direct_2014-2018/2.UDC under Agriculture Deptt. Paper-II.pdf',
    'Old_Questions/Direct_2014-2018/2.UDC under EF&CC Deptt. Paper-II.pdf',
    'Old_Questions/Direct_2014-2018/2.UDC under SAD Paper-II.pdf',
    'Old_Questions/Direct_2019-2020/UDC ARC Paper-II.pdf',
    'Old_Questions/Direct_2020-2021/UDC Direct under Taxation Deptt - Paper-II.pdf',
    'Old_Questions/Direct_2021-2022/UDC Direct under Fisheries Deptt - Paper-II.pdf',
    'Old_Questions/Direct_NG_2024-2027/Assistant UDC under MPSC paper-II..pdf',
]

async def main():
    async with await psycopg.AsyncConnection.connect('dbname=mpsc', row_factory=dict_row) as conn:
        async with conn.cursor() as cur:
            for p in papers:
                await cur.execute('''
                    SELECT a.id, a.canonical_id, a.paper_id, a.qnum, a.question, a.options
                    FROM appearances a
                    WHERE a.paper_id = %s
                      AND a.qnum::int >= 76
                    ORDER BY a.qnum::int
                ''', (p,))
                rows = await cur.fetchall()
                print(f"=== {p}: {len(rows)} items ===")
                for r in rows[:3]:
                    print(f"  Q{r['qnum']}: {r['question'][:65]}")

asyncio.run(main())
"""

proc = subprocess.run(
    ["ssh", "ubuntu@152.67.31.231", "sudo -u postgres /srv/api/.venv/bin/python -"],
    input=script, text=True, capture_output=True, timeout=60
)
print(proc.stdout)
