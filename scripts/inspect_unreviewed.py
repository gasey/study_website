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
else:
    papers = json.loads(proc.stdout)
    with open("/tmp/reviewed_aids.json") as f:
        reviewed = set(json.load(f))
    
    print(f"Total papers in DB: {len(papers)}")
    unreviewed_papers = []
    for p in papers:
        aids = set(p["aid_list"])
        unreviewed_aids = aids - reviewed
        if unreviewed_aids:
            unreviewed_papers.append((p, len(unreviewed_aids), len(aids)))
            
    print(f"Papers with unreviewed questions: {len(unreviewed_papers)}")
    print("\nListing all papers with unreviewed questions:")
    for p, unreviewed_count, total in unreviewed_papers:
        sf = p.get("source_file") or p.get("exam_name") or p["id"]
        subj = p.get("paper_subject") or ""
        pnum = p.get("paper_number") or ""
        pid = p["id"]
        print(f"- [{unreviewed_count}/{total} unreviewed] id={pid} | subj={subj} | num={pnum} | {sf}")
