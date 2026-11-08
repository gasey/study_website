import json, subprocess
from pathlib import Path

out_dir = Path("/home/hruaia/workspace/projects/personal/india-study-map-app/reports/tagging-batch142-20261108")
out_dir.mkdir(parents=True, exist_ok=True)

papers = [
    "Old_Questions/Direct_2023-2025/MCS Main 2023 English Paper-I..pdf",
    "Old_Questions/Direct_2023-2025/MCS Main 2023 English Paper-II..pdf",
    "Old_Questions/Direct_2022-2023/MCS Main 2022 English Paper-I..pdf",
    "Old_Questions/Direct_2022-2023/MCS Main 2022 English Paper-II..pdf",
    "Old_Questions/Direct_2014-2018/English-I.pdf",
    "Old_Questions/Direct_2014-2018/English-II.pdf",
    "Old_Questions/Direct_2014-2018/18. English Paper II.pdf"
]

script = f"""
import os, sys, json, asyncio
os.chdir('/tmp')
os.environ['DATABASE_URL'] = 'postgresql:///mpsc'
import psycopg
from psycopg.rows import dict_row

async def main():
    async with await psycopg.AsyncConnection.connect('dbname=mpsc', row_factory=dict_row) as conn:
        async with conn.cursor() as cur:
            await cur.execute('''
                SELECT a.id as appearance_id, a.canonical_id, a.paper_id, a.qnum, a.question
                FROM appearances a
                WHERE a.paper_id = ANY(%s)
                ORDER BY a.paper_id, a.qnum
            ''', ({papers},))
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
    exit(1)

rows = json.loads(proc.stdout)
with open("/tmp/reviewed_aids.json") as f:
    reviewed = set(json.load(f))

unreviewed = [r for r in rows if r["appearance_id"] not in reviewed]
print(f"Total rows fetched: {len(rows)}, unreviewed: {len(unreviewed)}")

with open(out_dir / "selection.json", "w") as f:
    json.dump(unreviewed, f, ensure_ascii=False, indent=2)

print(f"Wrote {len(unreviewed)} items to {out_dir / 'selection.json'}")
