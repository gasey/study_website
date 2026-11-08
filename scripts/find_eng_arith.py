import subprocess, json

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
                SELECT p.id, p.exam_name, p.post, p.paper_number, p.paper_subject, p.year, p.source_file,
                       count(a.id) as total_q,
                       array_agg(a.id) as aid_list
                FROM papers p
                JOIN appearances a ON a.paper_id = p.id
                GROUP BY p.id, p.exam_name, p.post, p.paper_number, p.paper_subject, p.year, p.source_file
                ORDER BY p.source_file
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
    sys.exit(1)

papers = json.loads(proc.stdout)
with open("/tmp/reviewed_aids.json") as f:
    reviewed = set(json.load(f))

keywords = [
    "english", "arithmetic", "math", "aptitude", "reasoning", "quant",
    "general english", "paper-i", "paper-ii", "paper i", "paper ii"
]

print("=== PAPERS WITH UNREVIEWED QUESTIONS MATCHING ENGLISH / ARITHMETIC / APTITUDE ===")
target_papers = []
for p in papers:
    aids = set(p["aid_list"])
    unreviewed = aids - reviewed
    if not unreviewed:
        continue
    sf = (p.get("source_file") or "").lower()
    subj = (p.get("paper_subject") or "").lower()
    name = (p.get("exam_name") or "").lower()
    post = (p.get("post") or "").lower()
    
    # check if strictly english / arithmetic / math / aptitude
    is_eng_arith = any(k in sf or k in subj or k in name for k in [
        "english", "arithmetic", "math", "aptitude", "reasoning", "quant"
    ])
    
    if is_eng_arith:
        target_papers.append((p, len(unreviewed), len(aids)))

print(f"Total matching papers: {len(target_papers)}")
for p, unrev, tot in target_papers:
    sf = p.get("source_file") or p.get("exam_name") or p["id"]
    subj = p.get("paper_subject") or ""
    pnum = p.get("paper_number") or ""
    pid = p["id"]
    print(f"- [{unrev}/{tot} unrev] id={pid} | subj={subj} | num={pnum} | {sf}")
