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
                SELECT a.id, a.canonical_id, a.paper_id, a.qnum, a.subject, a.topic, a.question,
                       p.source_file, p.exam_name, p.paper_number, p.paper_subject
                FROM appearances a
                JOIN papers p ON p.id = a.paper_id
                ORDER BY a.paper_id, a.qnum
            ''')
            rows = await cur.fetchall()
            print(json.dumps(rows, default=str))

asyncio.run(main())
"""

proc = subprocess.run(
    ["ssh", "ubuntu@152.67.31.231", "sudo -u postgres /srv/api/.venv/bin/python -"],
    input=script, text=True, capture_output=True, timeout=120
)
if proc.returncode:
    print("Error:", proc.stderr)
    sys.exit(1)

all_appearances = json.loads(proc.stdout)
with open("/tmp/reviewed_aids.json") as f:
    reviewed = set(json.load(f))

print(f"Total appearances in DB: {len(all_appearances)}")
unreviewed = [a for a in all_appearances if a["id"] not in reviewed]
print(f"Total unreviewed appearances: {len(unreviewed)}")

# Search for any unreviewed questions that could possibly be English or Arithmetic
candidates_found = []
for a in unreviewed:
    pid = (a["paper_id"] or "").lower()
    sf = (a["source_file"] or "").lower()
    subj = (a["subject"] or "").lower()
    top = (a["topic"] or "").lower()
    psubj = (a["paper_subject"] or "").lower()
    qtext = (a["question"] or "").lower()
    name = (a["exam_name"] or "").lower()

    # Skip known secondary permutation series already documented
    if any(k in sf for k in ["series b", "series c", "series d", "series-b", "series-c", "series-d"]):
        continue
    # Skip known misnomer defect (Geology technical paper)
    if "geologist junior" in sf:
        continue

    # Is it English?
    is_eng = any(k in sf or k in subj or k in psubj or k in name for k in ["english", "enlish", "englsih"])
    # Is it Arithmetic / Math / Aptitude / Reasoning?
    is_arith = any(k in sf or k in subj or k in psubj or k in name for k in ["arithmetic", "mathematics", "aptitude", "aptitute", "reasoning", "quant"])

    if is_eng or is_arith:
        candidates_found.append(a)

print(f"\nUnreviewed potential candidates found (excluding Series B/C/D and Geology misnomer): {len(candidates_found)}")
papers_map = {}
for a in candidates_found:
    papers_map.setdefault(a["paper_id"], []).append(a)

for pid, items in sorted(papers_map.items()):
    sf = items[0]["source_file"]
    print(f"\n- Paper: {pid} ({len(items)} items)")
    for it in items[:5]:
        print(f"    Q{it['qnum']}: subj={it['subject']} | top={it['topic']} | {it['question'][:60]}")
