import json, subprocess
from pathlib import Path

out_dir = Path("/home/hruaia/workspace/projects/personal/india-study-map-app/reports/tagging-batch144-20261108")
out_dir.mkdir(parents=True, exist_ok=True)

paper_id = "Old_Questions/Direct_2014-2018/5.Jr. Administrative Grade and Sr. Grade of Mizoram Legal Service 2016 GK & Aptitute Test (Common).pdf"

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
                WHERE a.paper_id = '{paper_id}'
                  AND a.qnum::int >= 81
                ORDER BY a.qnum::int
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
    exit(1)

rows = json.loads(proc.stdout)
print(f"Total rows fetched: {len(rows)}")

with open(out_dir / "selection.json", "w") as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)

print(f"Wrote {len(rows)} items to {out_dir / 'selection.json'}")
for r in rows:
    print(f"  Q{r['qnum']}: {r['question'][:65]}")
