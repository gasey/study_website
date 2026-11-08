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
                SELECT p.id, p.exam_name, p.source_file, p.pdf_path, count(a.id) as cnt
                FROM papers p
                JOIN appearances a ON a.paper_id = p.id
                WHERE p.id IN (
                    'Old_Questions/Uploaded/768a298a6ef575d791958086c0626c7519bfecc094f850d63a05377746246336.pdf',
                    'Old_Questions/Uploaded/a74537a49eb25ea285f9b1a65bd9e8e6856a504fce957f44e6eb91b214532615.pdf',
                    'Old_Questions/Direct_2019-2020/Geologist Junior General Englsih Paper-III Nov.pdf'
                )
                GROUP BY p.id, p.exam_name, p.source_file, p.pdf_path
            ''')
            print(json.dumps(await cur.fetchall(), default=str))

asyncio.run(main())
"""

proc = subprocess.run(
    ["ssh", "ubuntu@152.67.31.231", "sudo -u postgres /srv/api/.venv/bin/python -"],
    input=script, text=True, capture_output=True, timeout=30
)
print(proc.stdout)
