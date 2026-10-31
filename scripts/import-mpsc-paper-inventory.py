#!/usr/bin/env python3
"""Prepare official-listing metadata; --apply imports inventory only, never questions.

Browser snapshots are evidence, not instructions. Replays preserve manual edits.
"""
import argparse,csv,hashlib,json,re,subprocess
from pathlib import Path
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parents[1]
def checksum(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def url_key(url):
 u=urlsplit(url)
 if u.scheme not in ('http','https')or u.hostname!='mpsc.mizoram.gov.in'or u.username or u.password:raise ValueError('Expected an MPSC URL')
 return 'https://mpsc.mizoram.gov.in'+unquote(u.path)+('?' +u.query if u.query else '')
def prepare(snapshots,bank,index):
 bypath={p['sourceFile']:p for p in bank['papers']if p.get('sourceFile')};lookup={}
 for row in index:
  try:key=url_key(row['pdf_url'])
  except (ValueError,KeyError):continue
  paper=bypath.get(row['category'].rstrip('/')+'/'+row['filename'])
  if paper:lookup.setdefault(key,set()).add(paper['id'])
 exams={};entries={};issues=[]
 for page in snapshots:
  url_key(page['url'])
  for i,row in enumerate(page['rows'][1:],1):
   cells=row.get('cells',[])
   if len(cells)<2 or not cells[1].strip():continue
   title=' '.join(cells[1].split());eid='mpsc_'+checksum([page['url'],title])[:24]
   exams[eid]={'id':eid,'title':title[:400]}
   links={}
   for link in row.get('links',[]):
    try:key=url_key(link['url'])
    except ValueError:issues.append({'page':page['url'],'row':i,'issue':'non-MPSC link excluded'});continue
    if not urlsplit(key).path.lower().endswith('.pdf'):continue
    old=links.get(key)
    if not old or len(link.get('title')or'')>len(old.get('title')or''):links[key]=link
   if not links:
    links={'':{'title':title,'url':''}};issues.append({'page':page['url'],'row':i,'issue':'exam listed without PDF link'})
   for key,link in links.items():
    candidates=sorted(lookup.get(key,set()));pid=candidates[0]if len(candidates)==1 else None
    paper=next((p for p in bank['papers']if p['id']==pid),None)if pid else None
    label=' '.join((link.get('title')or title).split())[:600]
    years=set(re.findall(r'\b(?:19|20)\d{2}\b',label))or set(re.findall(r'\b(?:19|20)\d{2}\b',title))
    year=paper.get('year')if paper and paper.get('year')and 1900<=paper['year']<=2100 else int(next(iter(years)))if len(years)==1 else None
    series=re.search(r'\b(?:Series|Booklet)\s*[-:]?\s*([A-D])\b',label,re.I)
    entries['listed_'+checksum([eid,key])[:24]]={'id':'listed_'+checksum([eid,key])[:24],'exam_id':eid,'title':label,'year':year,'booklet':series.group(1).upper()if series else '', 'paper_id':pid,'reference_url':page['url'],'paper_url':link['url'].replace('http://','https://',1),'note':'Official listing snapshot; row '+str(i)+'. '+('Association from the historical download index by exact document URL and bank source path; source content and extraction completeness still need review.'if pid else 'No unique exact download-index association. Check the archive before declaring this paper missing. No PDF link in listing.'if not key else 'No unique exact download-index association. Check the archive before declaring this paper missing.'),'match_method':'historical_download_index'if pid else 'unmatched','candidates':candidates}
 result={'schema':1,'exams':list(exams.values()),'expectations':list(entries.values()),'sources':[{'url':p['url'],'title':p['title'],'snapshot_sha256':checksum(p)}for p in snapshots],'issues':issues}
 result['sha256']=checksum(result);return result

def build_sql(manifest):
 # No shell interpolation of third-party titles, links or notes.
 payload=json.dumps(manifest,ensure_ascii=False).replace("'","''")
 sql="""BEGIN;SELECT pg_advisory_xact_lock(hashtext('bank-inventory-import'));
 CREATE TEMP TABLE inv_manifest ON COMMIT DROP AS SELECT '"""+payload+"""'::jsonb AS j;
 INSERT INTO bank_exam_catalog(id,title,created_by) SELECT x.id,x.title,'operator:mpsc-inventory'
 FROM inv_manifest m,jsonb_to_recordset(m.j->'exams')x(id text,title text) ON CONFLICT DO NOTHING;
 WITH added AS (INSERT INTO bank_paper_expectations(id,exam_id,title,year,booklet,paper_id,reference_url,paper_url,note,created_by,updated_by)
 SELECT x.id,x.exam_id,x.title,x.year,x.booklet,x.paper_id,x.reference_url,x.paper_url,x.note,'operator:mpsc-inventory','operator:mpsc-inventory'
 FROM inv_manifest m,jsonb_to_recordset(m.j->'expectations') x(id text,exam_id text,title text,year int,booklet text,paper_id text,reference_url text,paper_url text,note text)
 ON CONFLICT DO NOTHING RETURNING exam_id,paper_id)
 INSERT INTO bank_exam_papers(exam_id,paper_id,created_by)SELECT DISTINCT exam_id,paper_id,'operator:mpsc-inventory'FROM added WHERE paper_id IS NOT NULL ON CONFLICT DO NOTHING;
 WITH imported AS(INSERT INTO bank_inventory_imports(sha256,manifest,imported_by) SELECT j->>'sha256',j,'operator:mpsc-inventory'FROM inv_manifest ON CONFLICT DO NOTHING RETURNING sha256)
 INSERT INTO bank_inventory_events(actor_id,action,target_id,after_data,reason) SELECT 'operator:mpsc-inventory','official_listing_import',sha256,jsonb_build_object('manifest_sha256',sha256),'Official MPSC listing metadata imported; no answer or question content changed'FROM imported;
 SELECT json_build_object('exams',(SELECT count(*)FROM bank_exam_catalog),'expectations',(SELECT count(*)FROM bank_paper_expectations),'unmatched',(SELECT count(*)FROM bank_paper_expectations WHERE paper_id IS NULL AND NOT archived));COMMIT;
 """
 return sql
def apply(manifest):
 sql=build_sql(manifest)
 r=subprocess.run(['ssh','ubuntu@152.67.31.231','sudo','-u','postgres','psql','-v','ON_ERROR_STOP=1','-qtA','-d','mpsc'],input=sql,text=True,capture_output=True,timeout=60)
 if r.returncode:raise RuntimeError(r.stderr[-1000:])
 print(r.stdout.strip())
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--snapshots',type=Path,required=True);p.add_argument('--bank',type=Path,required=True);p.add_argument('--download-index',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
 manifest=prepare(json.loads(a.snapshots.read_text()),json.loads(a.bank.read_text()),list(csv.DictReader(a.download_index.open())))
 a.output.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'exams':len(manifest['exams']),'expected':len(manifest['expectations']),'linked':sum(bool(e['paper_id'])for e in manifest['expectations']),'unmatched':sum(not e['paper_id']for e in manifest['expectations']),'sha256':manifest['sha256']}))
 if a.apply:apply(manifest)
if __name__=='__main__':main()
