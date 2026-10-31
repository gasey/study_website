#!/usr/bin/env python3
"""Mirror registered key/reference PDFs by their checked SHA256 to private storage."""
import hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1].parent/'mpsc-question-bankv2'
def main():
 r=subprocess.run(['ssh','ubuntu@152.67.31.231','sudo','-u','postgres','psql','-v','ON_ERROR_STOP=1','-qtA','-d','mpsc'],input="SELECT COALESCE(json_agg(d),'[]'::json) FROM(SELECT id,source_file,sha256 FROM review_documents WHERE kind IN('official-key','reference'))d;",text=True,capture_output=True,check=True,timeout=30)
 rows=json.loads(r.stdout);missing=[];count=0
 with tempfile.TemporaryDirectory(prefix='ism-key-docs-')as tmp:
  for d in rows:
   file=(ROOT/d['source_file']).resolve()
   if not file.is_relative_to(ROOT)or not file.is_file():missing.append(d['id']);continue
   if hashlib.sha256(file.read_bytes()).hexdigest()!=d['sha256']:raise ValueError('Registered document content changed: '+d['id'])
   shutil.copyfile(file,Path(tmp)/(d['sha256']+'.pdf'));count+=1
  subprocess.run(['ssh','ubuntu@152.67.31.231','umask 077; mkdir -p /tmp/ism-registered-documents-stage; chmod 700 /tmp/ism-registered-documents-stage'],check=True,timeout=30)
  subprocess.run(['rsync','-az',tmp+'/', 'ubuntu@152.67.31.231:/tmp/ism-registered-documents-stage/'],check=True,timeout=120)
  subprocess.run(['ssh','ubuntu@152.67.31.231',"sudo mkdir -p /srv/study/registered-documents && sudo rsync -a /tmp/ism-registered-documents-stage/ /srv/study/registered-documents/ && sudo chown -R root:www-data /srv/study/registered-documents && sudo chmod 750 /srv/study/registered-documents && sudo find /srv/study/registered-documents -type f -exec chmod 640 {} + && rm -rf /tmp/ism-registered-documents-stage"],check=True,timeout=60)
 print(json.dumps({'synced':count,'missing_local_registered_files':missing,'public_static_route':False}))
if __name__=='__main__':main()
