import json, subprocess

script = """
import os, sys, json, asyncio
os.chdir('/tmp')
os.environ['DATABASE_URL'] = 'postgresql:///mpsc'
import psycopg
from psycopg.rows import dict_row

papers = [
    'Old_Questions/Direct_2014-2018/Genral Enlish..pdf',
    'Old_Questions/Direct_2019-2020/General Englsih Paper-I (EO).pdf',
    'Old_Questions/Direct_NG_2024-2027/LDC under MPSC Paper-I 2025..pdf',
    'Old_Questions/Uploaded/768a298a6ef575d791958086c0626c7519bfecc094f850d63a05377746246336.pdf',
    'Old_Questions/Uploaded/a74537a49eb25ea285f9b1a65bd9e8e6856a504fce957f44e6eb91b214532615.pdf'
]

async def main():
    async with await psycopg.AsyncConnection.connect('dbname=mpsc', row_factory=dict_row) as conn:
        async with conn.cursor() as cur:
            for p in papers:
                await cur.execute('''
                    SELECT a.id, a.qnum, a.subject, a.topic, a.question, p.source_file, p.exam_name
                    FROM appearances a
                    JOIN papers p ON p.id = a.paper_id
                    WHERE a.paper_id = %s
                    ORDER BY a.qnum
                ''', (p,))
                rows = await cur.fetchall()
                print(f"=== {p} ({len(rows)} items, exam={rows[0]['exam_name'] if rows else 'N/A'}) ===")
                for r in rows[:10]:
                    print(f"  qnum={r['qnum']} | {r['question'][:75]}")

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
