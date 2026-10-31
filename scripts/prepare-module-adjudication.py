#!/usr/bin/env python3
"""Build source-bound, deduplicated review packets. Never modifies bank or DB."""
import argparse,hashlib,importlib.util,json,sys
from collections import Counter
from pathlib import Path
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'api'))
from app.services.review_policy import Proposal,digest,safe_url
spec=importlib.util.spec_from_file_location('audit_import',ROOT/'scripts/import-module-audits.py')
imp=importlib.util.module_from_spec(spec);spec.loader.exec_module(imp)

def prepare(bank_path,manifests,assessments):
 bank_sha=imp.file_sha(bank_path);bank=json.loads(bank_path.read_text());byid={q['id']:q for q in bank['questions']};papers={p['id']:p for p in bank['papers']};groups={}
 for path in manifests:
  m=json.loads(path.read_text());unsigned=json.loads(json.dumps(m));unsigned['run'].pop('manifest_sha256',None)
  if digest(unsigned)!=m['run']['manifest_sha256']:raise ValueError('Input manifest hash mismatch')
  if m['run']['bank_sha256']!=bank_sha:raise ValueError('Bank changed; regenerate module comparisons before adjudication')
  for item in m['items']:
   if item['comparison']!='conflict':continue
   exact=[c for c in item['candidates'] if c['imported'].get('identity_exact')]
   if item['match_status']!='exact_unique' or len(exact)!=1:raise ValueError('Conflict must have one current exact candidate')
   c=exact[0];q=byid[c['appearance_id']]
   if imp.identity(q)!=imp.identity(item['legacy']) or q.get('answerIndex')!=c['imported']['answer_index']:raise ValueError('Stale candidate identity or answer')
   groups.setdefault(q['id'],[]).append({'module_id':m['run']['module_id'],'item_id':item['id'],'manifest_sha256':m['run']['manifest_sha256'],'module_url':m['run']['module_url'],'legacy_id':item['legacy_id'],'module_answer_index':item['legacy']['answerIndex']})
 if len({a['appearanceId'] for a in assessments})!=len(assessments):raise ValueError('Duplicate research assessments')
 assessed={a['appearanceId']:a for a in assessments}
 if set(assessed)-set(groups):raise ValueError('Assessment is outside the input conflict cohort')
 claims=[];held=[];pdf_hashes={}
 for aid,refs in sorted(groups.items()):
  q=byid[aid];paper=papers[q['paperId']];a=assessed.get(aid);outcome=a['outcome'] if a else 'needs_source_review'
  if outcome not in {'propose_answer','retain_bank','source_defect','needs_source_review'}:raise ValueError('Unsupported outcome')
  if a and (a['expectedBankAnswerIndex']!=q.get('answerIndex') or a['expectedBankAnswerSource']!=q.get('answerSource')):raise ValueError('Assessment baseline changed')
  if a and a['expectedIdentitySha256']!=digest(imp.identity(q)):raise ValueError('Assessment identity changed')
  pdf=bank_path.parent.parent/paper['pdfPath']
  if pdf not in pdf_hashes:pdf_hashes[pdf]=imp.file_sha(pdf)
  record={'appearanceId':aid,'canonicalId':imp.cid(aid),'reviewStatus':'prepared_independent_review_required','outcome':outcome,'currentBankAnswerIndex':q.get('answerIndex'),'currentBankAnswerSource':q.get('answerSource'),'baselineSha256':digest(q),'optionsSha256':digest(q['options']),'question':q['question'],'options':q['options'],'bankPaperId':q['paperId'],'printedQuestion':q.get('qnum'),'pdfPage':q.get('page'),'sourcePdfSha256':pdf_hashes[pdf],'moduleReferences':refs,'sources':a.get('sources',[]) if a else [],'rationale':a['rationale'] if a else 'No independent source assessment completed in this batch. Keep both claims unresolved; inspect the printed source and historical context before proposing an answer.','proposals':[]}
  for s in record['sources']:safe_url(s['url'])
  if a:
   target=a.get('answerIndex',q.get('answerIndex'))
   if outcome in {'propose_answer','retain_bank'} and (type(target)is not int or not 0<=target<len(q['options'])):raise ValueError('Invalid assessed answer')
   if outcome=='propose_answer' and target==q.get('answerIndex'):raise ValueError('Answer proposal must change the current answer')
   if outcome=='retain_bank' and target!=q.get('answerIndex'):raise ValueError('Retain assessment must preserve answer')
   record['proposedAnswerIndex']=target if outcome=='propose_answer' else None
   record['supportedAnswerIndex']=target if outcome in {'propose_answer','retain_bank'} else None
   for source in record['sources']:
    if source.get('localKeyFile'):
     key=bank_path.parent.parent/source['localKeyFile'];record.setdefault('sourceKeyHashes',{})[source['localKeyFile']]=imp.file_sha(key)
   subject=next((c['subject_id'] for c in q.get('classifications',[]) if c.get('is_primary')),None)
   if not subject:raise ValueError('Target needs a primary subject')
   evidence=[{'kind':'reasoning','note':a['rationale']}]
   evidence += [{'kind':'reference','url':s['url'],'note':s['note']} for s in record['sources']]
   evidence += [{'kind':'reference','module_item_id':r['item_id'],'module_run_sha256':r['manifest_sha256'],'url':r['module_url'],'note':'Historical module claim retained for comparison; this reference is not official-key proof.'} for r in refs]
   changes=[]
   if outcome=='propose_answer':changes.append(('answer',{'answerIndex':target,'answerSource':'derived','answerKeyRef':None,'explanation':a['rationale']}))
   if a.get('contextPatch'):changes.append(('transcription',a['contextPatch']))
   if outcome=='source_defect':changes.append(('defect',{'sourceDefect':'unresolved-source','disputeNote':a['rationale']}))
   for kind,patch in changes:
    title=('Review answer: ' if kind=='answer' else 'Restore source context: ' if kind=='transcription' else 'Flag printed option defect: ')+q['question'][:140]
    p=Proposal(kind=kind,canonical_id=imp.cid(aid),appearance_id=aid,subject_id=subject,title=title,patch=patch,rationale=a['rationale'],evidence=evidence).model_dump(mode='json')
    record['proposals'].append({'id':'map_'+digest(p)[:32],'payload':p,'payloadSha256':digest(p),'status':'prepared_not_submitted'})
  (held if outcome in {'needs_source_review','source_defect'} else claims).append(record)
 packet={'schemaVersion':1,'created':'2026-10-23','policy':'Research and calculation recommendations only; not an independent approval, official key, publication or bank mutation. Unknown cases remain explicit. Drafts cite original immutable module runs.','bankSha256AtReview':bank_sha,'assessmentFileSha256':digest(assessments),'summary':{'moduleRows':sum(map(len,groups.values())),'uniqueAppearances':len(groups),'outcomes':dict(Counter(r['outcome'] for r in claims+held)),'preparedProposals':sum(len(r['proposals']) for r in claims+held)},'claims':claims,'held':held}
 packet['packetSha256']=digest(packet)
 return packet

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bank',type=Path,default=ROOT.parent/'mpsc-question-bankv2/bank/mpsc_bank_v2.json');p.add_argument('--manifest',type=Path,action='append',required=True);p.add_argument('--assessments',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 result=prepare(args.bank,args.manifest,json.loads(args.assessments.read_text()));args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result['summary']))
if __name__=='__main__':main()
