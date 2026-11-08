#!/usr/bin/env python3
"""Oracle operator: read-only live completions and actual registered PDF hashes."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(mode=0o2770,parents=True,exist_ok=True)
    code='''
import os,sys,json,asyncio
os.chdir('/tmp');os.environ['DATABASE_URL']='postgresql:///mpsc';sys.path.insert(0,'/srv/api')
import psycopg
from psycopg.rows import dict_row
from app.services.taxonomy_review_progress import signature_sql
async def main():
 async with await psycopg.AsyncConnection.connect('dbname=mpsc',row_factory=dict_row,options='-c jit=off') as conn:
  async with conn.cursor() as cur:
   await cur.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
   await cur.execute("SELECT id,paper_id,source_file,sha256,kind FROM review_documents WHERE kind='paper' ORDER BY id")
   docs=await cur.fetchall()
   await cur.execute("""WITH latest AS (
    SELECT DISTINCT ON(detail->>'canonical_id') detail FROM contribution_events
    WHERE action='owner_ai_taxonomy_progress' ORDER BY detail->>'canonical_id',id DESC)
    SELECT c.id AS canonical_id,true AS source_bound,
      jsonb_build_object('subject_id',qc.subject_id,'topic_id',qc.topic_id,'subtopic_id',qc.subtopic_id) AS primary,
      COALESCE((SELECT jsonb_agg(jsonb_build_object('subject_id',l.subject_id,'topic_id',l.topic_id,'subtopic_id',l.subtopic_id)
       ORDER BY l.subject_id,l.topic_id NULLS FIRST,l.subtopic_id NULLS FIRST)
       FROM question_topic_links l WHERE l.question_id=c.id AND l.review_status='approved'),'[]'::jsonb) AS related
    FROM latest r JOIN appearances a ON a.id=r.detail->>'appearance_id'
    JOIN canonical_questions c ON c.id=a.canonical_id JOIN papers p ON p.id=a.paper_id
    LEFT JOIN question_classifications qc ON qc.question_id=c.id AND qc.review_status='approved'
    WHERE r.detail->>'status' IN ('published','confirmed')
    AND r.detail->>'source_signature'="""+signature_sql())
   print(json.dumps({'documents':docs,'completed':await cur.fetchall()},default=str))
asyncio.run(main())
'''
    r=subprocess.run(['sudo','-u','postgres','/srv/api/.venv/bin/python','-'],input=code,text=True,capture_output=True,check=True)
    data=json.loads(r.stdout);root=Path('/srv/study/workshop/mpsc-question-bankv2').resolve()
    hashes={};cache={};missing=[]
    for doc in data['documents']:
        path=(root/doc['source_file']).resolve()
        if not path.is_relative_to(root) or not path.is_file():missing.append(doc['id']);continue
        if path not in cache:cache[path]=sha(path)
        hashes[doc['id']]=cache[path]
    for name,value in [('source-hashes.json',hashes),('completed-live.json',data['completed']),('documents.json',data['documents'])]:
        target=a.output/name
        if target.exists():raise ValueError('Preserve existing source export; choose a new directory')
        target.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    bank=root/'bank/mpsc_bank_v2.json'
    summary={'documents':len(data['documents']),'actual_file_hashes':len(hashes),'missing_documents':missing,
             'completed_source_bound':len(data['completed']),'initial_bank_sha256':sha(bank)}
    (a.output/'source-check.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='missing_documents'}|{'missing_documents':len(missing)}))


if __name__=='__main__':main()
