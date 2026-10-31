#!/usr/bin/env python3
"""Append source-only recovered MCS records. Never infers keys or changes existing rows."""
import argparse,fcntl,hashlib,json,os
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('artifact',type=Path);p.add_argument('--bank',type=Path,default=Path(__file__).resolve().parents[2]/'mpsc-question-bankv2/bank/mpsc_bank_v2.json');p.add_argument('--receipt',type=Path,required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
 art=json.loads(a.artifact.read_text());assert len(art['papers'])==6 and len(art['questions'])==600
 pids={p['id']for p in art['papers']};assert len(pids)==6
 for pid in pids:
  qs=[q for q in art['questions']if q['paperId']==pid];assert len(qs)==100 and {q['qnum']for q in qs}==set(range(1,101))
 for q in art['questions']:
  assert q['answerIndex']is None and q['answerSource']=='none' and not q['classifications']
  assert len(q['options'])==4 and q['figureImage'] and q['page']>=1
  assert (a.bank.parents[1]/q['figureImage']).is_file()
 for paper in art['papers']:
  source=a.bank.parents[1]/'pdfs'/paper['sourceFile'];assert source.is_file()
  expected={q['origin']['source_sha256']for q in art['questions']if q['paperId']==paper['id']}
  assert expected=={hashlib.sha256(source.read_bytes()).hexdigest()},'Source PDF checksum mismatch'
 with open(str(a.bank)+'.lock','w')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);before=a.bank.read_bytes();bank=json.loads(before)
  assert not pids.intersection(x['id']for x in bank['papers']),'Already imported; do not duplicate'
  assert not {q['id']for q in art['questions']}.intersection(q['id']for q in bank['questions'])
  count=len(bank['questions']);bank['papers'].extend(art['papers']);bank['questions'].extend(art['questions']);bank.setdefault('sittings',{}).update(art['sittings'])
  receipt={'questions_before':count,'questions_after':len(bank['questions']),'new_papers':6,'new_questions':600,'existing_questions_changed':0,'official_answers_added':0,'before_sha256':hashlib.sha256(before).hexdigest(),'applied':a.apply}
  if a.apply:
   a.receipt.parent.mkdir(parents=True,exist_ok=True);(a.receipt.parent/'bank-before.json').write_bytes(before)
   temp=a.bank.with_suffix('.mcs-import.tmp');temp.write_text(json.dumps(bank,ensure_ascii=False,indent=2)+'\n');os.replace(temp,a.bank);receipt['after_sha256']=hashlib.sha256(a.bank.read_bytes()).hexdigest()
  a.receipt.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
