import json, subprocess
from pathlib import Path

out = Path(__file__).resolve().parent
paper_id = "Old_Questions/Direct_NG_2024-2027/LDC under SW, WCD Paper - I..pdf"

script = f"""import json, asyncio, psycopg
from psycopg.rows import dict_row

async def main():
    async with await psycopg.AsyncConnection.connect('dbname=mpsc', row_factory=dict_row) as conn:
        async with conn.cursor() as cur:
            await cur.execute('''
                SELECT a.id as appearance_id, a.canonical_id, a.paper_id, a.qnum, a.subject, a.topic, a.question
                FROM appearances a
                WHERE a.paper_id = '{paper_id}' AND a.is_primary IS TRUE
                ORDER BY a.qnum_seq, a.id
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
print(f"Retrieved {len(rows)} appearances for {paper_id}")
assert len(rows) == 75, f"Expected 75 items, got {len(rows)}"

(out / "selection.json").write_text(json.dumps(rows, indent=2) + "\n")
print(f"Wrote selection.json with {len(rows)} items.")
