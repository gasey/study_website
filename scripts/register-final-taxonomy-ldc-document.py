#!/usr/bin/env python3
"""Register one existing, cover-inspected PDF for this exact owner tagging scope.

Only source registry/workflow metadata is written. No bank question, key, paper
approval, account permission or content row is changed.
"""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path

SCOPE='2d9737104889f1f512412463ef403cb7abf0f130bc0ec507b438f855c40f5855'
PAPER='Old_Questions/Direct_NG_2024-2027/LDC under MPSC Paper-II 2025..pdf'
PDF_SHA='712c2c9334cdd9d779b40945a6019a22ddbc71af6cc229fe2edecc51c78a275a'
DOC='doc_712c2c9334cdd9d7'

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);a=p.parse_args()
    if os.geteuid()!=0:raise ValueError('Oracle operator required')
    root=Path('/srv/study/workshop/mpsc-question-bankv2');bank=root/'bank/mpsc_bank_v2.json'
    sys.path.insert(0,'/srv/study/workshop/india-study-map-app/scripts')
    from bank_authority import require_writable
    require_writable(bank)
    frozen=a.run/'frozen.json'
    with frozen.open('rb')as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
    if actual!=SCOPE or (a.run/'frozen.sha256').read_text().strip()!=SCOPE:raise ValueError('Wrong owner scope')
    scope=json.loads(frozen.read_text());items=[i for i in scope['items']if i['snapshot']['paper']['id']==PAPER]
    if len(items)!=100 or any(i.get('document',{}).get('id')!=DOC or i['document'].get('sha256')!=PDF_SHA for i in items):
        raise ValueError('Exact original 100-question PDF binding required')
    content=json.loads(bank.read_text());paper=next(p for p in content['papers']if p['id']==PAPER)
    if (paper.get('sourceFile')or'').removeprefix('pdfs/')!=PAPER:raise ValueError('Bank source path differs')
    path=(root/'pdfs'/PAPER).resolve()
    if not path.is_relative_to(root/'pdfs')or not path.is_file():raise ValueError('Existing PDF is missing')
    with path.open('rb')as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
    if actual!=PDF_SHA:raise ValueError('Original saved review PDF bytes differ')
    payload={'id':DOC,'paper_id':PAPER,'source_file':str(path.relative_to(root)),
             'sha256':PDF_SHA,'title':paper['examName'],'run_id':scope['run_id'],
             'owner_email':scope['owner_email'],'authorization':scope['authorization'],'scope_sha256':SCOPE,
             'inspection_scope':'Codex rendered and visually inspected physical page 1: MPSC Lower Division Clerk, February 2025, Paper-II. Identity only; no new review of the 100 questions or answers.'}
    code='''
import os,sys,json,asyncio
os.chdir('/tmp');os.environ['DATABASE_URL']='postgresql:///mpsc';sys.path.insert(0,'/srv/api')
import psycopg
from psycopg.rows import dict_row
from app.services.review_identity import require_role
from app.services.bank_review import event
data=json.load(sys.stdin)
async def main():
 async with await psycopg.AsyncConnection.connect('dbname=mpsc',row_factory=dict_row)as conn:
  async with conn.cursor()as cur:
   await cur.execute('SELECT id FROM users WHERE lower(email)=lower(%s)',(data['owner_email'],))
   users=await cur.fetchall()
   if len(users)!=1:raise ValueError('Exactly one existing owner required')
   await require_role(cur,users[0]['id'],roles=('owner',),lock=True)
   await cur.execute('SELECT id FROM papers WHERE id=%s FOR SHARE',(data['paper_id'],))
   if not await cur.fetchone():raise ValueError('Paper must already exist')
   await cur.execute("SELECT * FROM review_documents WHERE id=%s OR (paper_id=%s AND kind='paper')",(data['id'],data['paper_id']))
   previous=await cur.fetchall()
   if previous:
    if len(previous)!=1 or any(previous[0].get(k)!=data[k]for k in ('id','paper_id','source_file','sha256')) or previous[0]['kind']!='paper':
     raise ValueError('Existing document differs; do not overwrite history')
    created=False
   else:
    await cur.execute("INSERT INTO review_documents(id,paper_id,title,source_file,sha256,kind,registered_by) VALUES(%s,%s,%s,%s,%s,'paper','operator:owner-source-maintenance')",tuple(data[k]for k in ('id','paper_id','title','source_file','sha256')))
    await event(cur,None,'operator:owner-source-maintenance','owner_taxonomy_source_registered',
      {k:v for k,v in data.items()if k!='owner_email'}|{'owner_id':users[0]['id'],'independent_human_review':False,'new_question_review':False,'answer_verification':False})
    created=True
 print(json.dumps({'created':created,'document':{k:data[k]for k in ('id','paper_id','title','source_file','sha256')},'kind':'paper','questions_changed':0,'answers_verified':0}))
asyncio.run(main())
'''
    r=subprocess.run(['sudo','-u','postgres','/srv/api/.venv/bin/python','-c',code],input=json.dumps(payload),text=True,capture_output=True,check=True)
    result=json.loads(r.stdout);output=a.run/'document-registration.json'
    if not output.exists():output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
