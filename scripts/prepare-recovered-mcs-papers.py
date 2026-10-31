#!/usr/bin/env python3
"""Prepare source-only MCS reproductions; extraction is provisional and keys stay absent."""
from pathlib import Path
import re,json,hashlib,collections,pymupdf,io,subprocess
from PIL import Image
import argparse
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--manifest',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1];R=args.output.resolve();R.mkdir(parents=True,exist_ok=True);B=ROOT.parent/'mpsc-question-bankv2';art={'papers':[],'questions':[],'sittings':{}};assets={};issues=[]
sha=lambda s:hashlib.sha256(s).hexdigest()
manifest=json.loads(args.manifest.read_text())
def clean(s):
 lines=s.splitlines();lines=[l for l in lines if not re.fullmatch(r'\s*(?:\d{1,3}|\*+|[- ]+)\s*',l) and not re.search(r'MCS\s*Preliminary|Preliminary\s*Exam\s*Paper|QUESTION BOOKLET|Chase Academy|chaseacademy',l,re.I)]
 return '\n'.join(l.rstrip() for l in lines).strip()
def source_image(doc,pages):
 key=(doc.name,tuple(pages))
 if key not in assets:
  ims=[Image.open(io.BytesIO(doc[i-1].get_pixmap(matrix=pymupdf.Matrix(1.35,1.35)).tobytes('png'))).convert('RGB') for i in pages]
  im=Image.new('RGB',(max(x.width for x in ims),sum(x.height for x in ims)),'white');y=0
  for x in ims:im.paste(x,(0,y));y+=x.height
  bio=io.BytesIO();im.save(bio,format='PNG');data=bio.getvalue();rel='images/page-renders/'+sha(data)+'.png';(B/rel).write_bytes(data);assets[key]=rel
 return assets[key]
for item in manifest:
 year,roman=item['year'],item['paper'];src=ROOT/item['local_file'];assert sha(src.read_bytes())==item['sha256'],'Source PDF checksum changed';doc=pymupdf.open(src)
 pid=f'Old_Questions/Recovered_MCS/MCS Combined {year} Preliminary Exam Paper-{roman} Series-A Chase copy.pdf'
 sid=sha(f'MCS Combined {year}'.encode())[:16];art['sittings'][sid]={'id':sid,'examName':f'Mizoram Civil Services Combined Preliminary Examination {year}','examType':'Direct','year':year}
 art['papers'].append({'id':pid,'examType':'Direct','examName':f'Mizoram Civil Services Combined Preliminary Examination {year}','paperNumber':roman,'paperSubject':'General Studies'if roman=='I'else'Aptitude Tests','year':year,'sourceFile':pid,'pdfPath':'pdfs/'+pid,'kind':'mcq','sittingId':sid,'examScopeId':'mizoram-recruitment'})
 # Layout extraction retains option rows; positions track original PDF page mapping.
 textfile=src.with_suffix('.txt');text=textfile.read_text() if textfile.is_file() else subprocess.run(['pdftotext','-layout',str(src),'-'],capture_output=True,text=True,check=True).stdout;pages=text.split('\f');text='\f\n'.join('' if 'QUESTION BOOKLET' in p and 'INSTRUCTIONS' in p else clean(p) for p in pages)
 starts=[]
 for match in re.finditer(r'(?m)^[ \t]*(\d{1,3})(?:\.[ \t]*|[ \t]+(?=\S))',text):
  n=int(match[1]);
  if 1<=n<=100:
   if n==len(starts)+1:starts.append((n,match))
 assert len(starts)==100,(year,roman,len(starts),[n for n,m in starts])
 for i,(n,m) in enumerate(starts):
  end=starts[i+1][1].start()if i<99 else len(text);body=text[m.end():end]
  opts=list(re.finditer(r'\(([a-d])\)\s*',body))
  first={}
  for o in opts:
   if o[1]not in first:first[o[1]]=o
  valid=set(first)==set('abcd');stem=body[:min((o.start()for o in first.values()),default=len(body))].strip()
  choices=['See printed option '+l.upper()+' in the source image'for l in 'abcd']
  # Keep each printed row; option text after a shared direction belongs to the next question.
  if valid:
   ordered=sorted(first.items(),key=lambda x:x[1].start())
   for j,(label,o)in enumerate(ordered):
    val=body[o.end():ordered[j+1][1].start()if j+1<len(ordered)else len(body)]
    val=re.split(r'(?im)^\s*(?:Directions?\b|Passage\s*[-–:]?\s*\d|Question Nos?\b)',val)[0]
    choices[ord(label)-97]=clean(val).strip()
   valid=all(choices)
  choices=[o or 'See printed option '+chr(65+j)+' in the source image'for j,o in enumerate(choices)]
  p0=text[:m.start()].count('\f')+1;p1=text[:end].count('\f')+1;p1=min(p1,len(doc))
  # Always retain source context, including immediately preceding shared passage pages.
  imagepages=list(range(max(1,p0-2)if roman=='II'else p0,p1+1))
  q={'id':sha((pid+'|mcq|'+str(n)).encode())[:20],'paperId':pid,'type':'mcq','qnum':n,'page':p0,'question':clean(stem)or f'Printed question {n}. Read the source image.','options':choices,'answerIndex':None,'answerSource':'none','marks':None,'hasDiagram':True,'figureImage':source_image(doc,imagepages),'direction':'Read the printed question and all shared passages, tables and figures in the source image. This recovered reproduction has not been checked against a matching final answer key.','explanation':None,'classifications':[],'origin':{'kind':'recovered-third-party-paper','source_url':item['url'],'source_sha256':item['sha256'],'review_date':'2026-10-31','host':'Chase Academy','series_status':'host-labelled A; final-key matching pending','text_status':'searchable extraction; source image is authoritative'}}
  if not valid:q['sourceDefect']='unresolved-source';q['disputeNote']='Searchable options could not be reliably segmented. Read the source image; answer verification is pending.';issues.append({'year':year,'paper':roman,'qnum':n})
  art['questions'].append(q)
 (B/'pdfs'/pid).parent.mkdir(parents=True,exist_ok=True);(B/'pdfs'/pid).write_bytes(src.read_bytes())
(R/'import-artifact.json').write_text(json.dumps(art,ensure_ascii=False,indent=2)+'\n');(R/'extraction-issues.json').write_text(json.dumps(issues,indent=2));print('papers',len(art['papers']),'questions',len(art['questions']),'unresolved options',len(issues),'source images',len(assets))
