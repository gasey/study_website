import json, subprocess
from pathlib import Path

out_dir = Path("/home/hruaia/workspace/projects/personal/india-study-map-app/reports/tagging-batch143-20261108")
out_dir.mkdir(parents=True, exist_ok=True)

script = """
import os, sys, json, asyncio
os.chdir('/tmp')
os.environ['DATABASE_URL'] = 'postgresql:///mpsc'
import psycopg
from psycopg.rows import dict_row

async def main():
    async with await psycopg.AsyncConnection.connect('dbname=mpsc', row_factory=dict_row) as conn:
        async with conn.cursor() as cur:
            # 1. Genral Enlish..pdf
            await cur.execute('''
                SELECT a.id as appearance_id, a.canonical_id, a.paper_id, a.qnum, a.question
                FROM appearances a
                WHERE a.paper_id = 'Old_Questions/Direct_2014-2018/Genral Enlish..pdf'
                ORDER BY a.qnum::int
            ''')
            r1 = await cur.fetchall()

            # 2. General Englsih Paper-I (EO).pdf
            await cur.execute('''
                SELECT a.id as appearance_id, a.canonical_id, a.paper_id, a.qnum, a.question
                FROM appearances a
                WHERE a.paper_id = 'Old_Questions/Direct_2019-2020/General Englsih Paper-I (EO).pdf'
                ORDER BY a.qnum::int
            ''')
            r2 = await cur.fetchall()

            # 3. 768a298... A1 & A2
            await cur.execute('''
                SELECT a.id as appearance_id, a.canonical_id, a.paper_id, a.qnum, a.question
                FROM appearances a
                WHERE a.paper_id = 'Old_Questions/Uploaded/768a298a6ef575d791958086c0626c7519bfecc094f850d63a05377746246336.pdf'
                  AND a.qnum IN ('A1', 'A2')
                ORDER BY a.qnum
            ''')
            r3 = await cur.fetchall()

            # 4. LDC under MPSC Paper-I 2025..pdf B1, B2, B3
            await cur.execute('''
                SELECT a.id as appearance_id, a.canonical_id, a.paper_id, a.qnum, a.question
                FROM appearances a
                WHERE a.paper_id = 'Old_Questions/Direct_NG_2024-2027/LDC under MPSC Paper-I 2025..pdf'
                  AND a.qnum IN ('B1', 'B2', 'B3')
                ORDER BY a.qnum
            ''')
            r4 = await cur.fetchall()

            all_rows = r1 + r2 + r3 + r4
            print(json.dumps(all_rows, default=str))

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
for r in unreviewed:
    print(f"  {r['paper_id']} Q{r['qnum']}: {r['question'][:50]}")
