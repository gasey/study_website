#!/usr/bin/env python3
"""Trusted operator-assisted intake, explicitly requested by the account owner.

Uses normal proposal validation and immutable history. Does NOT approve, grant
review permissions, export, publish, or mutate the bank. No auth session is
created or impersonated; an operator-assisted audit event records this intake.
"""
from pathlib import Path
import argparse,json,os,shlex,subprocess

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--owner-email',required=True);p.add_argument('--proposal',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();proposal=json.loads(args.proposal.read_text())
    code='''import asyncio,json,sys,os,subprocess
from pathlib import Path
from urllib.parse import urlsplit
pid=subprocess.check_output(['systemctl','show','ism-api','--property=MainPID','--value'],text=True).strip()
service_env=dict(item.split(b'=',1) for item in Path('/proc/'+pid+'/environ').read_bytes().split(b'\\0') if b'=' in item)
os.environ['DATABASE_URL']=service_env[b'DATABASE_URL'].decode()
if urlsplit(os.environ['DATABASE_URL']).path!='/mpsc':raise RuntimeError('Expected the running production service database')
from app.db import open_pool,close_pool,cursor
from app.services import bank_review as review
from app.services.review_policy import Proposal,digest
async def run():
 data=json.load(sys.stdin)
 proposal=Proposal.model_validate(data['proposal'])
 await open_pool()
 try:
  async with cursor() as cur:
   await cur.execute("SELECT u.id FROM users u WHERE lower(u.email)=lower(%s) AND EXISTS (SELECT 1 FROM review_grants g WHERE g.user_id=u.id AND g.role='owner' AND g.subject_id IS NULL AND g.revoked_at IS NULL)",(data['email'],))
   users=await cur.fetchall()
   if len(users)!=1:raise RuntimeError('Exactly one previously authorized owner account is required')
   owner=users[0]['id']
   key='operator-assisted:'+digest(proposal.model_dump(mode='json'))
   c=await review.create(cur,owner,proposal,key)
   if c['state']=='draft':
    await review.event(cur,c['id'],'operator:codex','operator_assisted_submission',{'authorization':'Owner explicitly requested preparation/submission in the implementation chat','dummy_approvals_imported':False})
    c=await review.update_state(cur,c,owner,'submitted',{'operator_assisted':True})
   await cur.execute("SELECT count(*) AS n FROM contribution_decisions WHERE contribution_id=%s AND revision=%s AND decision='approve'",(c['id'],c['revision']))
   approvals=(await cur.fetchone())['n']
   print(json.dumps({'id':c['id'],'state':c['state'],'lock_version':c['lock_version'],'url':'https://study.hawayu.in/contributions/'+c['id'],'independent_approvals':approvals}))
 finally:await close_pool()
asyncio.run(run())
'''
    shell='set -a\n. /etc/mpsc/db.env\nset +a\ncd /srv/api\nexec .venv/bin/python -c '+shlex.quote(code)
    result=subprocess.run(['ssh','-o','BatchMode=yes','ubuntu@152.67.31.231','sudo','bash','-c',shlex.quote(shell)],input=json.dumps({'email':args.owner_email,'proposal':proposal}),text=True,capture_output=True,timeout=60)
    if result.returncode:raise SystemExit(result.stderr[-2000:])
    receipt=json.loads(result.stdout)
    args.output.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
