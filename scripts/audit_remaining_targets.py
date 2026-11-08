import json, subprocess, sys

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
                SELECT a.id, a.canonical_id, a.paper_id, a.qnum, a.subject, a.topic, a.question, a.series,
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

# Categorize unreviewed appearances
eng_candidates = []
arith_candidates = []
udc_paper2_arith = []
other_unreviewed = []

for a in unreviewed:
    pid = a["paper_id"]
    sf = (a["source_file"] or "").lower()
    subj = (a["subject"] or "").lower()
    top = (a["topic"] or "").lower()
    psubj = (a["paper_subject"] or "").lower()
    qtext = (a["question"] or "").lower()
    
    # Is it UDC Paper-II?
    if "udc" in sf and "paper-ii" in sf:
        try:
            qnum_val = int(a["qnum"])
            # In UDC Paper-II, 76-100 (or 51-75 if 75 items) is Arithmetic
            if qnum_val >= 76:
                udc_paper2_arith.append(a)
                continue
        except (ValueError, TypeError):
            pass

    # English checks
    if subj in ["english", "general english", "general-english"] or \
       "english" in sf or "english" in psubj or "enlish" in sf or "englsih" in sf:
        eng_candidates.append(a)
    elif subj in ["arithmetic", "mathematics", "math", "aptitude", "reasoning", "quant"] or \
         "arithmetic" in sf or "arithmetic" in psubj or "aptitude" in sf or "aptitute" in sf:
        arith_candidates.append(a)
    else:
        other_unreviewed.append(a)

print(f"\nUnreviewed English items: {len(eng_candidates)}")
# Group English items by paper
papers_eng = {}
for a in eng_candidates:
    papers_eng.setdefault(a["paper_id"], []).append(a)
for pid, items in sorted(papers_eng.items()):
    sf = items[0]["source_file"]
    print(f"  - {pid} ({len(items)} items): {sf}")

print(f"\nUnreviewed Arithmetic / Aptitude items: {len(arith_candidates)}")
papers_arith = {}
for a in arith_candidates:
    papers_arith.setdefault(a["paper_id"], []).append(a)
for pid, items in sorted(papers_arith.items()):
    sf = items[0]["source_file"]
    print(f"  - {pid} ({len(items)} items): {sf}")

print(f"\nUnreviewed UDC Paper-II Arithmetic items (qnum >= 76): {len(udc_paper2_arith)}")
papers_udc2 = {}
for a in udc_paper2_arith:
    papers_udc2.setdefault(a["paper_id"], []).append(a)
for pid, items in sorted(papers_udc2.items()):
    sf = items[0]["source_file"]
    print(f"  - {pid} ({len(items)} items): {sf}")
