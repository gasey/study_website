"""Append one source-bound approved paper; preserve all existing bank records."""
import copy,gzip,hashlib,json,os,shutil
from pathlib import Path
from bank_authority import require_writable
from editorial_protection import check_candidate,write_guarded
from review_bank_store import atomic,sha

PAPER_FIELDS={'id':'id','exam_type':'examType','exam_name':'examName','post':'post','paper_number':'paperNumber',
 'paper_subject':'paperSubject','year':'year','month':'month','kind':'kind','source_file':'sourceFile',
 'pdf_path':'pdfPath','sitting_id':'sittingId','exam_scope_id':'examScopeId'}

def existing_paper(bank,manifest):
 """Recheck JSON under the shared bank lock; never edit an existing paper row."""
 p=manifest['payload'];target=manifest.get('existing_source')
 if not target or target['paper_id']!=p.get('target_paper_id'):raise ValueError('Registered source binding is missing')
 snapshot=target['snapshot']
 version=hashlib.sha256(json.dumps(snapshot,sort_keys=True,ensure_ascii=False,separators=(',',':'),default=str).encode()).hexdigest()
 if version!=p.get('target_source_version'):raise ValueError('Registered source identity differs from the reviewed binding')
 docs=snapshot['documents'];pid=p['target_paper_id']
 if not docs or any(d['paper_id']!=pid or d['sha256']!=manifest['source_sha256'] for d in docs):raise ValueError('Original PDF does not uniquely match the registered paper')
 matches=[x for x in bank['papers'] if x['id']==pid]
 if len(matches)!=1:raise ValueError('Registered original paper is missing or ambiguous in the bank')
 original=matches[0]
 identity={column:original.get(key) for column,key in PAPER_FIELDS.items()}
 if identity['sitting_id'] not in bank.get('sittings',{}):identity['sitting_id']=None
 # Scope was backfilled in SQL by migration 0046. Normal sync deliberately
 # preserves that SQL-owned value when legacy JSON omits it (COALESCE).
 # The current SQL snapshot is separately bound and rechecked by the publisher.
 if identity['exam_scope_id'] is None:identity['exam_scope_id']=snapshot['paper']['exam_scope_id']
 if identity!=snapshot['paper']:raise ValueError('Registered paper metadata changed; obtain a fresh source-bound publication decision')
 if (p['exam_name'],p['year'],p['paper_subject'] or None)!=(identity['exam_name'],identity['year'],identity['paper_subject']):raise ValueError('Draft exam identity differs from the original paper')
 if any(q['paperId']==pid for q in bank['questions']):raise ValueError('Registered paper already has questions; cannot append or replace them')
 return pid

def build(bank,manifest):
 p=manifest['payload'];source=manifest['source_sha256']
 if len(source)!=64 or any(c not in '0123456789abcdef' for c in source):raise ValueError('Invalid source hash')
 paper_id=existing_paper(bank,manifest) if p.get('target_paper_id') else 'Old_Questions/Uploaded/'+source+'.pdf'
 if not p.get('target_paper_id') and any(x['id']==paper_id for x in bank['papers']):raise ValueError('This PDF already has a paper. Review existing questions instead of importing a duplicate.')
 out=copy.deepcopy(bank);nodes={n['id']:n for n in manifest['taxonomy']}
 if not p.get('target_paper_id'):
  out['papers'].append({'id':paper_id,'examType':'Direct','examName':p['exam_name'],'paperSubject':p['paper_subject'] or None,'year':p['year'],'series':p['booklet'] or None,'sourceFile':paper_id,'kind':'mcq' if any(q['type']=='mcq' for q in p['questions']) else 'descriptive','examScopeId':'mizoram-recruitment','origin':'reviewed-paper-workbench','paperWorkspace':manifest['draft_id']})
 existing={q['id'] for q in bank['questions']};ids=[]
 for i,q in enumerate(p['questions']):
  qid='paper_'+manifest['draft_id'].removeprefix('pwdraft_')+'_'+q['id']
  if qid in existing:raise ValueError('Imported source question ID already exists')
  ids.append(qid);c={}
  for key in ('subject_id','topic_id','subtopic_id'):
   if q.get(key):
    if q[key] not in nodes:raise ValueError('Classification registry changed')
    c[key]=q[key];c[key.replace('_id','_label')]=nodes[q[key]]['label']
  review_label='Owner paper decision ' if manifest.get('review_kind')=='owner' else 'Owner-authorized AI-assisted paper review ' if manifest.get('review_kind')=='owner_ai' else 'Independent paper review '
  c.update(is_primary=True,source='manual',review_status='approved',confidence=1,evidence=review_label+manifest['submission_id'],taxonomy_version=manifest['taxonomy_version'])
  image=manifest.get('figures',{}).get(q.get('figure_job'))
  out['questions'].append({'id':qid,'paperId':paper_id,'type':q['type'],'qnum':q['number'],'page':q['page'],'series':p['booklet'] or None,'question':q['question'],'options':q['options'],'direction':q['direction'] or None,'passage':q['passage'] or None,'explanation':q['explanation'] or None,'answerIndex':q['answer_index'],'answerSource':q['answer_source'],'answerKeyRef':('Uploaded key '+p['key_sha256']+' · '+p['key_title']+' · PDF page '+str(q['key_page'])+' · booklet '+p['key_series']) if q['answer_source']=='key' else None,'hasDiagram':bool(image),'figureImage':image,'usedVision':False,'classifications':[c],'origin':'reviewed-paper-workbench','paperWorkspace':manifest['draft_id']})
 return out,paper_id,ids

def apply(bank_path,root,manifest,receipt_path):
 bank_path=Path(bank_path);root=Path(root);receipt_path=Path(receipt_path)
 require_writable(bank_path);check_candidate(bank_path)
 h=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
 if receipt_path.exists():
  receipt=json.loads(receipt_path.read_text())
  if receipt['manifest_hash']!=h:raise ValueError('Paper receipt differs from the approved source')
  if sha(bank_path)==receipt['output_sha256']:return receipt
  if sha(bank_path)!=receipt['input_sha256']:raise ValueError('Bank advanced across an interrupted paper import; reconcile the prepared receipt')
 if shutil.disk_usage(root).free<10*1024**3:raise ValueError('Less than 10 GB free; pause publication and archive backups first')
 before=sha(bank_path);bank=json.loads(bank_path.read_text());out,paper_id,ids=build(bank,manifest)
 output=(json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode()
 receipt={'schema':1,'draft_id':manifest['draft_id'],'manifest_hash':h,'input_sha256':before,'output_sha256':hashlib.sha256(output).hexdigest(),'paper_id':paper_id,'appearance_ids':ids,'payload_hash':manifest['payload_hash'],'submission_id':manifest['submission_id']}
 backups=root/'bank/paper-backups';backups.mkdir(parents=True,exist_ok=True)
 backup=backups/(before+'.json.gz')
 if not backup.exists():
  tmp=backup.with_suffix('.tmp')
  with bank_path.open('rb') as src,gzip.open(tmp,'wb',compresslevel=3) as dst:shutil.copyfileobj(src,dst)
  os.replace(tmp,backup)
 receipt_path.parent.mkdir(parents=True,exist_ok=True)
 atomic(receipt_path,receipt)
 if sha(bank_path)!=before:raise ValueError('Concurrent bank writer detected')
 write_guarded(bank_path,out,locked=True)
 if sha(bank_path)!=receipt['output_sha256']:raise ValueError('Paper output hash differs')
 return receipt
