"""One leased document job at a time. No model calls or shell-supplied arguments."""
import asyncio,hashlib,json,logging,os,re,signal,struct,subprocess,tempfile
from pathlib import Path
from datetime import datetime,timezone
import psycopg
from psycopg.types.json import Jsonb
from ..config import settings
from ..db import cursor,open_pool,close_pool
from ..services.review_policy import digest

def command(args,work,timeout=90):
 """Bound CPU, address space, file size and execution time for untrusted PDFs."""
 error=work/'command-error.log'
 with error.open('wb') as f:
  result=subprocess.run(['prlimit','--as=805306368','--cpu=90','--fsize=33554432','--nofile=64','--',*map(str,args)],cwd=work,stdout=f,stderr=f,timeout=timeout)
 if result.returncode:raise ValueError('Document processing failed. Check encryption, damage or scan quality. '+error.read_bytes()[-500:].decode(errors='replace'))
 return error.read_text(errors='replace')

def pdf_pages(path):
 with tempfile.TemporaryDirectory() as tmp:
  info=command(['pdfinfo',path],Path(tmp))
  match=re.search(r'^Pages:\s+(\d+)',info,re.M)
  if not match or not 1<=int(match[1])<=300:raise ValueError('PDF must contain between 1 and 300 pages')
  return int(match[1])

def process_document(j,d):
 from ..routers.paper_workbench import source_path,storage
 src=source_path(d['source_sha256']);base=storage();out=base/'outputs';out.mkdir(parents=True,exist_ok=True)
 if src.exists() and os.geteuid()==0:os.chown(out,src.stat().st_uid,src.stat().st_gid);out.chmod(0o750)
 if not src.is_file() or hashlib.sha256(src.read_bytes()).hexdigest()!=d['source_sha256']:raise ValueError('Original source is missing or changed')
 args=j['args'];page=args.get('page',1)
 with tempfile.TemporaryDirectory(dir=out,prefix='.job-') as tmp:
  work=Path(tmp)
  info=command(['pdfinfo',src],work)
  match=re.search(r'^Pages:\s+(\d+)',info,re.M)
  if not match or not 1<=int(match[1])<=300:raise ValueError('PDF must contain between 1 and 300 pages')
  count=int(match[1])
  if j['kind']=='extract':
   dest=work/'text.txt';command(['pdftotext','-layout','-enc','UTF-8',src,dest],work)
   if dest.stat().st_size>4*1024*1024:raise ValueError('Extracted text exceeds the 4 MB limit; split the PDF')
   text=dest.read_text(errors='replace').split('\f')
   return {'pages':count,'characters':sum(len(x) for x in text),'tool':'pdftotext','needs_ocr':not any(x.strip() for x in text)},[(i+1,text[i] if i<len(text) else '') for i in range(count)]
  if page>count:raise ValueError('Page is outside the source PDF')
  selected=src;p=page
  if args.get('rotation'):
   one=work/'page.pdf';rotated=work/'rotated.pdf'
   command(['qpdf','--empty','--pages',src,str(page),'--',one],work)
   command(['qpdf',one,'--rotate=+'+str(args['rotation'])+':1','--',rotated],work)
   selected=rotated;p=1
  png=work/'page'
  command(['pdftoppm','-f',p,'-l',p,'-singlefile','-scale-to','1600','-png',selected,png],work)
  image=png.with_suffix('.png');header=image.read_bytes()[:24]
  if not header.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Page could not render')
  width,height=struct.unpack('>II',header[16:24])
  if j['kind']=='ocr':
   output=work/'ocr';command(['tesseract',image,output,'-l','eng','--psm',args.get('psm',3)],work)
   text=output.with_suffix('.txt').read_text(errors='replace')
   return {'page':page,'text':text[:200000],'rotation':args.get('rotation',0),'tool':'tesseract-eng','note':'OCR draft only; inspect the original before copying.'},[]
  if j['kind']=='crop':
   dest=work/'crop'
   command(['pdftoppm','-f',page,'-l',page,'-singlefile','-scale-to','1600','-x',int(args['x']*width),'-y',int(args['y']*height),'-W',max(1,int(args['width']*width)),'-H',max(1,int(args['height']*height)),'-png',src,dest],work)
   image=dest.with_suffix('.png')
  target=out/(j['id']+'.png');os.replace(image,target)
  if os.geteuid()==0:os.chown(target,src.stat().st_uid,src.stat().st_gid)
  target.chmod(0o640)
  return {'page':page,'width':width,'height':height,'rotation':args.get('rotation',0),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'image_url':'/api/paper-workbench/drafts/'+d['id']+'/images/'+j['id']},[]

async def once(kinds=None):
 kinds=kinds or ['extract','render','ocr','crop','publish']
 worker_id='oracle-paper-publisher' if kinds==['publish'] else 'oracle-paper-documents'
 # Session-level lock on a dedicated connection survives short transactions.
 # Two accidentally started services cannot compete for OCR CPU or bank writes.
 async with await psycopg.AsyncConnection.connect(settings.database_url,autocommit=True) as lease:
  lock=await lease.execute("SELECT pg_try_advisory_lock(hashtext('ism-paper-worker-v1'))")
  if not (await lock.fetchone())[0]:return False
  try:
   async with cursor() as cur:
    await cur.execute("UPDATE paper_workbench_jobs SET state='failed',error='Worker interrupted three times; inspect and retry.',finished_at=now(),lease_until=NULL WHERE state='running' AND lease_until<now() AND attempts>=3 RETURNING draft_id,kind")
    for abandoned in await cur.fetchall():
     if abandoned['kind']=='publish':await cur.execute("UPDATE paper_workbench_drafts SET state='failed',last_error='Publisher interrupted; inspect and retry the durable receipt.' WHERE id=%s",(abandoned['draft_id'],))
    await cur.execute('''SELECT * FROM paper_workbench_jobs WHERE (state='queued' OR state='running' AND lease_until<now()) AND attempts<3 AND kind=ANY(%s) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1''',(kinds,));j=await cur.fetchone()
    if not j:return False
    await cur.execute("UPDATE paper_workbench_jobs SET state='running',attempts=attempts+1,lease_until=now()+interval '10 minutes',error=NULL WHERE id=%s",(j['id'],))
    await cur.execute('SELECT * FROM paper_workbench_drafts WHERE id=%s',(j['draft_id'],));d=await cur.fetchone()
    await cur.execute("INSERT INTO review_worker_health(worker_id,status) VALUES(%s,'processing') ON CONFLICT(worker_id) DO UPDATE SET seen_at=now(),status='processing'",(worker_id,))
   try:
    if j['kind']=='publish':
     from .paper_publish import publish_job
     result=await publish_job(j,d);pages=[]
    else:result,pages=await asyncio.to_thread(process_document,j,d)
    async with cursor() as cur:
     if pages:
      # Extraction creates a fresh revision; it never overwrites manual questions.
      await cur.executemany('INSERT INTO paper_workbench_pages(extraction_id,page,text) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING',[(j['id'],page,text) for page,text in pages])
      await cur.execute('UPDATE paper_workbench_drafts SET extraction_id=%s WHERE id=%s',(j['id'],d['id']))
     await cur.execute("UPDATE paper_workbench_jobs SET state='done',result=%s,error=NULL,finished_at=now(),lease_until=NULL WHERE id=%s",(Jsonb(result),j['id']))
   except Exception as e:
    logging.getLogger(__name__).exception('Paper job failed: %s',j['id'])
    message=str(e)[:1500]
    async with cursor() as cur:
     await cur.execute("UPDATE paper_workbench_jobs SET state='failed',error=%s,finished_at=now(),lease_until=NULL WHERE id=%s",(message,j['id']))
     if j['kind']=='publish':await cur.execute("UPDATE paper_workbench_drafts SET state='failed',last_error=%s WHERE id=%s",(message,d['id']))
   async with cursor() as cur:await cur.execute("UPDATE review_worker_health SET seen_at=now(),status='online' WHERE worker_id=%s",(worker_id,))
   return True
  finally:await lease.execute("SELECT pg_advisory_unlock(hashtext('ism-paper-worker-v1'))")

async def run(single=False,kinds=None):
 worker_id='oracle-paper-publisher' if kinds==['publish'] else 'oracle-paper-documents'
 stop=asyncio.Event()
 loop=asyncio.get_running_loop()
 for sig in (signal.SIGTERM,signal.SIGINT):loop.add_signal_handler(sig,stop.set)
 await open_pool()
 try:
  while not stop.is_set():
   worked=await once(kinds)
   if single:break
   if not worked:
    async with cursor() as cur:await cur.execute("INSERT INTO review_worker_health(worker_id,status) VALUES(%s,'online') ON CONFLICT(worker_id) DO UPDATE SET seen_at=now(),status='online'",(worker_id,))
    try:await asyncio.wait_for(stop.wait(),timeout=3)
    except asyncio.TimeoutError:pass
 finally:await close_pool()
if __name__=='__main__':
 import sys
 asyncio.run(run('--once' in sys.argv,['publish'] if '--publish' in sys.argv else ['extract','render','ocr','crop'] if '--documents' in sys.argv else None))
