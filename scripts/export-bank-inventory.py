#!/usr/bin/env python3
"""Read-only export of server-owned operational inventory to a local snapshot.
Never imports server canonical questions over the authoritative local bank.
"""
import argparse,datetime,hashlib,json,os,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT.parent/'mpsc-question-bankv2/state/admin-inventory/latest.json');a=p.parse_args()
 tables=['bank_exam_catalog','bank_exam_papers','bank_paper_expectations','bank_inventory_events','bank_inventory_imports','bank_paper_intake']
 sql='SELECT json_build_object('+','.join("'"+t+"',(SELECT COALESCE(json_agg(x),'[]'::json) FROM (SELECT * FROM "+t+' ORDER BY '+('expectation_id'if t=='bank_paper_intake'else 'exam_id,paper_id'if t=='bank_exam_papers'else 'sha256'if t=='bank_inventory_imports'else 'id')+") x)"for t in tables)+');'
 r=subprocess.run(['ssh','ubuntu@152.67.31.231','sudo','-u','postgres','psql','-v','ON_ERROR_STOP=1','-qtA','-d','mpsc'],input=sql,text=True,capture_output=True,timeout=60)
 if r.returncode:raise RuntimeError(r.stderr[-1000:])
 data=json.loads(r.stdout);payload={'schema':1,'exported_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'authority':'server operational inventory; local question bank remains authoritative','sha256':hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest(),'data':data}
 a.output.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile('w',dir=a.output.parent,delete=False)as f:json.dump(payload,f,indent=2,ensure_ascii=False);f.write('\n');f.flush();os.fsync(f.fileno());temp=Path(f.name)
 os.replace(temp,a.output);print(json.dumps({'output':str(a.output),'sha256':payload['sha256'],'exams':len(data['bank_exam_catalog']),'expectations':len(data['bank_paper_expectations'])}))
if __name__=='__main__':main()
