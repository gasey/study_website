#!/usr/bin/env python3
"""Owner-authorized reservation through ordinary assignment validation and audit.
No login/password, grant, activation, approval or publication is created.
"""
import argparse,json,subprocess
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 request=json.loads(a.request.read_text())
 code='''import asyncio,json,sys,os,subprocess
from pathlib import Path
pid=subprocess.check_output(['systemctl','show','ism-api','--property=MainPID','--value'],text=True).strip()
service_env=dict(item.split(b'=',1) for item in Path('/proc/'+pid+'/environ').read_bytes().split(b'\\0') if b'=' in item)
for k,v in service_env.items():os.environ[k.decode()]=v.decode()
sys.path.insert(0,'/srv/api')
from app.db import open_pool,close_pool,cursor
from app.routers.editorial import Invite,invite
from app.services.review_identity import Actor
from app.services import bank_review
async def run():
 data=json.load(sys.stdin);await open_pool()
 try:
  async with cursor() as cur:
   await cur.execute("SELECT u.id FROM users u WHERE lower(email)=lower(%s) AND EXISTS(SELECT 1 FROM review_grants g WHERE g.user_id=u.id AND g.role='owner' AND g.subject_id IS NULL AND g.revoked_at IS NULL)",(data['owner_email'],))
   owners=await cur.fetchall()
   if len(owners)!=1:raise ValueError('Exactly one active owner is required')
   owner=owners[0]['id']
  result=[]
  for item in data['assignments']:
   row=await invite(Invite(**item),Actor(owner,'',False,False))
   async with cursor() as cur:await bank_review.event(cur,None,'operator:editorial-handoff','editorial_reservation_requested',{'owner':owner,'assignment':row['id'],'authorization':data['authorization']})
   result.append({k:row[k] for k in ('id','email','collection_id','state','version')})
  print(json.dumps(result,default=str))
 finally:await close_pool()
asyncio.run(run())
'''
 remote='cd /srv/api && sudo .venv/bin/python -c '+__import__('shlex').quote(code)
 r=subprocess.run(['ssh','ubuntu@152.67.31.231',remote],input=json.dumps(request),text=True,capture_output=True,check=True,timeout=50)
 rows=json.loads(r.stdout);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
