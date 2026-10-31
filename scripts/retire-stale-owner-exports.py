#!/usr/bin/env python3
"""Withdraw explicit unapplied owner exports after an unrelated bank advance.

Never alters an immutable manifest, canonical content, peer decision or receipt.
Fresh owner review must create fresh exports through the normal decision tool.
"""
import argparse
import importlib.util
import json
import subprocess
from pathlib import Path

SPEC=importlib.util.spec_from_file_location('owner_tool',Path(__file__).with_name('owner-bank-maintenance.py'))
OWNER=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(OWNER)
# Reuse only the established trusted SSH environment setup. No browser session
# or MFA identity is asserted by this operator command.
REMOTE=OWNER.REMOTE[:OWNER.REMOTE.index('async def adjudicate')]+'''
async def run():
 data=json.load(sys.stdin)
 ids=data['publication_ids']
 if not 1<=len(ids)<=100 or len(set(ids))!=len(ids):raise ValueError('Choose 1–100 explicit unapplied exports')
 if len(data['authorization'].strip())<20 or len(data['reason'].strip())<20:raise ValueError('Explicit owner delegation and withdrawal reason required')
 if not re.fullmatch(r'[0-9a-f]{64}',data['bank_sha256']):raise ValueError('Expected current bank checksum required')
 await open_pool()
 try:
  async with cursor()as cur:
   await cur.execute("SELECT u.id FROM users u WHERE lower(email)=lower(%s) AND EXISTS(SELECT 1 FROM review_grants g WHERE g.user_id=u.id AND role='owner'AND subject_id IS NULL AND revoked_at IS NULL)",(data['owner_email'],));owners=await cur.fetchall()
   if len(owners)!=1:raise ValueError('Exactly one current owner required')
   owner=owners[0]['id']
   await cur.execute('SELECT bank_checksum FROM sync_log WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1');current=(await cur.fetchone())['bank_checksum']
   if current!=data['bank_sha256']:raise ValueError('Bank changed again; re-inspect before withdrawing exports')
   await cur.execute("SELECT id FROM bank_publications WHERE state='exported'FOR UPDATE");waiting=await cur.fetchall()
   if {p['id']for p in waiting}!=set(ids):raise ValueError('Explicit list must match all outstanding exports')
   await cur.execute('SELECT * FROM bank_publications WHERE id=ANY(%s)',(ids,));pubs=await cur.fetchall();checked=[]
   for pub in pubs:
    m=pub['manifest']
    if digest(m)!=pub['manifest_hash']or m['author_id']!=owner or m['bank_sha256']==current or m.get('admin_decision',{}).get('actor_id')!=owner:raise ValueError('Only stale existing owner answer exports qualify')
    await cur.execute("SELECT 1 FROM contribution_events WHERE contribution_id=%s AND actor_id=%s AND action='operator_answer_completed'",(pub['contribution_id'],OPERATOR))
    if not await cur.fetchone():raise ValueError('Missing original owner delegation')
    c=await review.load(cur,pub['contribution_id'],owner,review=True)
    if c['state']!='publishing' or c['author_id']!=owner or c['kind']!='answer' or c['revision']!=pub['revision']:raise ValueError('Contribution changed before withdrawal')
    snap=await review.snapshot(cur,c['canonical_id'],c['appearance_id'])
    if digest(snap)!=m['baseline_hash']:raise ValueError('Target source changed; withdrawal needs separate inspection')
    checked.append((pub,c))
   for pub,c in checked:
    detail={'owner_id':owner,'authorization':data['authorization'],'reason':data['reason'],'publication_id':pub['id'],'stale_bank_sha256':pub['manifest']['bank_sha256'],'current_bank_sha256':current,'source_baseline_unchanged':True,'not_published':True}
    await cur.execute("UPDATE bank_publications SET state='failed',error=%s,finished_at=now() WHERE id=%s",('Unapplied stale export withdrawn for fresh owner review. '+data['reason'],pub['id']))
    c=await review.update_state(cur,c,OPERATOR,'publication_failed',detail)
    c=await review.update_state(cur,c,OPERATOR,'changes_requested',detail)
    await review.update_state(cur,c,OPERATOR,'withdrawn',detail)
    await review.event(cur,c['id'],OPERATOR,'operator_unapplied_export_withdrawn',detail)
    await cur.execute('UPDATE review_outbox SET finished_at=now(),last_error=%s WHERE event_key=%s',('Withdrawn before publication: '+data['reason'],pub['id']))
   print(json.dumps({'withdrawn_publication_ids':[p['id']for p,c in checked],'bank_sha256':current,'canonical_changes':0,'manifest_changes':0}))
 finally:await close_pool()
asyncio.run(run())
'''


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--request',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    # Reuse the existing host/DB environment and quoting contract verbatim.
    import shlex
    shell='set -a\n. /etc/mpsc/db.env\nset +a\ncd /srv/api\nexec .venv/bin/python -c '+shlex.quote(REMOTE)
    result=subprocess.run(['ssh','-o','BatchMode=yes','ubuntu@152.67.31.231','sudo','bash','-c',shlex.quote(shell)],input=args.request.read_text(),text=True,capture_output=True,timeout=60)
    if result.returncode:raise SystemExit(result.stderr[-2500:])
    receipt=json.loads(result.stdout);args.output.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'withdrawn':len(receipt['withdrawn_publication_ids']),'canonical_changes':0}))
