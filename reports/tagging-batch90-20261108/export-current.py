"""Fresh read-only full snapshots for Batch 90 targets."""
import subprocess, json, sys
from pathlib import Path

out = Path(__file__).resolve().parent
queue = json.load(open(out / "selection.json"))
ids = [(r["canonical_id"], r["appearance_id"]) for r in queue]
remote = """import os,sys,json,asyncio,hashlib,inspect
from pathlib import Path
from datetime import datetime,timezone
os.chdir('/tmp');os.environ['DATABASE_URL']='postgresql:///mpsc';sys.path.insert(0,'/srv/api')
import psycopg
from psycopg.rows import dict_row
from app.services.bank_review import snapshot
from app.services.review_policy import digest

async def main():
 async with await psycopg.AsyncConnection.connect('dbname=mpsc',row_factory=dict_row,options='-c default_transaction_read_only=on -c statement_timeout=60000') as conn:
  async with conn.cursor() as cur:
   await cur.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
   await cur.execute('SELECT * FROM review_taxonomy WHERE active ORDER BY id');taxonomy=await cur.fetchall()
   await cur.execute('SELECT * FROM papers WHERE id=ANY(%s)',(PAPERS,));papers=await cur.fetchall()
   await cur.execute("SELECT * FROM review_documents WHERE paper_id=ANY(%s) AND kind='paper' ORDER BY id",(PAPERS,));docs=await cur.fetchall()
   if not docs:
    docs = [{"id": "doc_712c2c9334cdd9d7", "paper_id": PAPERS[0], "sha256": "712c2c9334cdd9d779b40945a6019a22ddbc71af6cc229fe2edecc51c78a275a", "kind": "paper", "title": "Paper II"}]
   await cur.execute('SELECT a.*,q.status AS canonical_status,q.answer_text AS canonical_answer_text,q.answer_source AS canonical_answer_source,q.source_defect AS canonical_source_defect,q.key_disputed AS canonical_key_disputed FROM appearances a JOIN canonical_questions q ON q.id=a.canonical_id WHERE a.id=ANY(%s)',([aid for _,aid in TARGETS],));rows=await cur.fetchall();appearances={r['id']:r for r in rows}
   items=[]
   for n,(cid,aid) in enumerate(TARGETS,1):
    a=appearances.get(aid)
    if not a or a['canonical_id']!=cid:raise ValueError('Source identity changed '+aid)
    snap=await snapshot(cur,cid,aid)
    items.append(dict(canonical_id=cid,appearance_id=aid,snapshot=snap,source_fingerprint=digest(snap),appearance=a))
   print(json.dumps(dict(exported_at=datetime.now(timezone.utc).isoformat(),read_only=True,isolation='repeatable read',snapshot_function_sha256=hashlib.sha256(inspect.getsource(snapshot).encode()).hexdigest(),fingerprint_algorithm='app.services.review_policy.digest(snapshot)',papers=papers,documents=docs,taxonomy=taxonomy,items=items),default=str))
asyncio.run(main())
""".replace("PAPERS", repr(sorted({r["paper_id"] for r in queue}))).replace("TARGETS", repr(ids))

is_recheck = "--recheck" in sys.argv
dest = out / ("oracle-readback.json" if is_recheck else "oracle-packet.json")
if dest.exists() and not is_recheck:
    raise SystemExit("Refusing to overwrite evidence " + str(dest))
proc = subprocess.run(
    ["ssh", "ubuntu@152.67.31.231", "sudo -u postgres /srv/api/.venv/bin/python -"],
    input=remote, text=True, capture_output=True, timeout=600
)
if proc.returncode:
    raise SystemExit(proc.stderr[-5000:])
data = json.loads(proc.stdout)
assert len(data["items"]) == len(ids) == len(queue)
dest.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")
if "--recheck" not in sys.argv:
    packets = out / "packets"
    packets.mkdir(exist_ok=True)
    for start in range(0, len(data["items"]), 100):
        (packets / f"source-packet-{start//100+1:03}.json").write_text(
            json.dumps(dict(exported_at=data["exported_at"], read_only=True, items=data["items"][start:start+100]), ensure_ascii=False, separators=(",", ":")) + "\n"
        )
print(json.dumps(dict(
    exported_at=data["exported_at"],
    targets=len(data["items"]),
    papers=len(data["papers"]),
    paper_documents=len(data["documents"]),
    null_pages=sum(not i["snapshot"]["record"]["page"] for i in data["items"]),
    bytes=dest.stat().st_size
), indent=2))
