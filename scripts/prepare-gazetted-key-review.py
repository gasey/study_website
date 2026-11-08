#!/usr/bin/env python3
"""Read-only exact-series provisional-key proposal and attributed AI review scope.

Run with the bundled PyMuPDF runtime. Source tables were visually inspected on all
eight PDF pages. Geometry ordering avoids the scanned PDF's scrambled OCR columns.
No service is contacted and no bank is written by this preparation helper.
"""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
import pymupdf as fitz

KEY_URL='https://mpsc.mizoram.gov.in/uploads/attachments/2026/09/8c4aca8d964afe5f70c36c25690e2692/provisional-answer-key-of-gr-b-gazetted-general-services-combined-sept-2026.pdf'
KEY_SHA='60797459386d2b11a825acce11fcf62f48c38faab54160d884fa7a97c813936e'
PAPERS=['general-english-series-a','general-english-series-b','gs-i-series-a','gs-i-series-b',
        'gs-ii-series-a','gs-ii-series-b','gs-iii-series-a','gs-iii-series-b']
FUTURE='https://learnenglish.britishcouncil.org/free-resources/grammar/b1-b2/future-continuous-future-perfect'
PAST='https://learnenglish.britishcouncil.org/free-resources/grammar/english-grammar-reference/past-perfect'


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def read_tables(pdf):
 result=[]
 for n,page in enumerate(pdf):
  entries=[]
  for word in page.get_text('words'):
   match=re.fullmatch(r'(?:\(|t)([ABCDabcd])\)',word[4])
   if match:entries.append({'x':(word[0]+word[2])/2,'y':(word[1]+word[3])/2,'answer':match.group(1).upper()})
  columns=[]
  for entry in sorted(entries,key=lambda w:w['x']):
   if not columns or entry['x']-columns[-1][-1]['x']>40:columns.append([])
   columns[-1].append(entry)
  rows=22 if n<2 else 25
  if len(columns)!=(3 if n<2 else 4)or any(len(col)!=rows for col in columns):raise ValueError('Ambiguous answer table; inspect source page '+str(n+1))
  result.append({'page':n+1,'paper':PAPERS[n],'answers':''.join(w['answer']for col in columns for w in sorted(col,key=lambda w:w['y']))})
 return result


def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--review-root',required=True,type=Path);args=parser.parse_args();root=args.review_root
 before=json.loads((root/'before.json').read_text());key=root/'provisional-key-20260929.pdf';assert hashlib.sha256(key.read_bytes()).hexdigest()==KEY_SHA
 pdf=fitz.open(key);assert len(pdf)==8;tables=read_tables(pdf);lookup={t['paper']:t for t in tables}
 crops=json.loads((root/'crop-receipt.json').read_text());jobs={d['id']:{j['question_id']:j for j in d['jobs']}for d in crops['drafts']}
 source_review=json.loads((root.parent/'draft-review/save-proposal.json').read_text());pairs=source_review['booklet_classification_matches']
 byname={Path(d['source_id']).stem:d for d in before['drafts']};matches=0
 for pair in pairs:
  if pair['a'].startswith('A'):continue
  a=byname[pair['paper']+'-series-a'];b=byname[pair['paper']+'-series-b'];qa=next(q for q in a['payload']['questions']if q['number']==pair['a']);qb=next(q for q in b['payload']['questions']if q['number']==pair['b'])
  ka=lookup[pair['paper']+'-series-a']['answers'][int(pair['a'].lstrip('B'))-1];kb=lookup[pair['paper']+'-series-b']['answers'][int(pair['b'].lstrip('B'))-1]
  assert qa['options'][ord(ka)-65]==qb['options'][ord(kb)-65],pair
  matches+=1
 assert matches==366
 authorization='Owner asked Codex to do the review and complete everything, then clarified: "i dont understand...i just want it to be solved". Complete these Gazetted papers and module with explicitly attributed AI-assisted review, not an independent human sign-off.'
 proposal={'authorization':authorization,'key_url':KEY_URL,'key_sha256':KEY_SHA,'key_path':'/tmp/gazetted-provisional-key-20260929.pdf','drafts':[]};conflicts=[];keyed=0
 for old in before['drafts']:
  p=copy.deepcopy(old['payload']);name=Path(old['source_id']).stem;table=lookup.get(name)
  p['key_status']='provisional'if table else None
  if table:
   assert p['key_sha256']is None
   p.update(key_sha256=KEY_SHA,key_title='MPSC provisional answer key · Group B (Gazetted) Combined exam · 29 September 2026 · Series A and B',key_series=p['booklet'])
   p['source_reference']+='\nOfficial provisional key (29 September 2026): '+KEY_URL
  for q,oq in zip(p['questions'],old['payload']['questions']):
   assert q['answer_index']is None and q['answer_source']=='none'and not q['explanation']
   if q['id']in jobs[old['id']]:
    assert not q['figure_job'];q['figure_job']=jobs[old['id']][q['id']]['job_id']
   if q['type']!='mcq':continue
   assert table and (not name.startswith('general-english')or q['number'].startswith('B'))
   n=int(q['number'].lstrip('B'));letter=table['answers'][n-1];index=ord(letter)-65
   if q['question'].startswith('They will have finished ploughing'):
    note="Source/key conflict: the printed sentence uses future perfect (will have + past participle), but no future perfect choice is printed. The Commission's provisional key marks (C), Future perfect continuous. The printed choices and official key document are preserved; no scoring answer is assigned. Grammar reference: "+FUTURE
   elif q['question'].startswith('Meena had all her classes'):
    note="Source/key conflict: 'had' is the main verb followed by the noun phrase 'all her classes', so the printed sentence is simple past (A). Past perfect requires had + a past participle. The Commission's provisional key marks (B), Past perfect. That official entry is retained in the attached key; scoring is withheld rather than silently replacing it. Grammar reference: "+PAST
   elif name.startswith('gs-iii')and q['question'].startswith('L, M, N, O, P, Q, R and S'):
    note="Source/key conflict: the circular-seating clues admit multiple arrangements. For example, clockwise L, N, R, O, S, M, P, Q satisfies every clue while both option (A) and option (D) are false. Exhaustive enumeration gives four arrangements after fixing L's position. The Commission's provisional key marks (A), but the printed task is underdetermined; scoring is withheld pending clarification."
   else:note=None
   if note:
    q['explanation']=note;conflicts.append({'draft_id':old['id'],'source_id':old['source_id'],'number':q['number'],'question_id':q['id'],'official_key_page':table['page'],'official_key_letter':letter,'official_key_option':q['options'][index],'note':note})
   else:q.update(answer_index=index,answer_source='key',key_page=table['page']);keyed+=1
   assert all(q[k]==oq[k]for k in q if k not in ('answer_index','answer_source','key_page','explanation','figure_job'))
  prefix=old['payload']['identity_note'].split('AI-assisted')[0].strip()
  p['identity_note']=prefix+' AI-assisted source/option/tag review and exact-key mapping completed 4 November 2026 under owner authorization. Review attribution is owner-authorized AI, not an independent human inspection. All original question IDs, printed text/options, instructions, passages and source figures are retained.'
  if table:
   p['identity_note']+=' Attached MPSC key is PROVISIONAL, dated 29 September 2026; physical key page '+str(table['page'])+' matches this paper and Series '+p['booklet']+'. Key mapping is not a claim that every provisional entry is factually final. Full teaching explanations are unavailable from the key.'
  else:p['identity_note']+=' Written-only source: no MCQ key or fabricated model answer was supplied. Printed marks, unit choices, instructions and word limits remain in each task.'
  flagged=[c for c in conflicts if c['draft_id']==old['id']]
  if flagged:p['identity_note']+=' Unscored source/key conflicts: '+', '.join(c['number']for c in flagged)+'. See the exact question notes and original key.'
  if p.get('target_paper_id'):p['identity_note']+=' Retain registered original '+p['target_paper_id']+'.'
  proposal['drafts'].append({'id':old['id'],'source_id':old['source_id'],'source_sha256':old['source_sha256'],'expected_version':old['version'],'expected_payload_hash':old['payload_hash'],'payload':p})
 assert keyed==726 and len(conflicts)==6
 evidence={'review_kind':'owner_ai','model':'Codex AI-assisted source and key review','authorization':authorization,'source_review_receipt_sha256':hashlib.sha256(Path('docs/sources/group-b-gazetted-draft-review-20261104.json').read_bytes()).hexdigest(),'source_pdf_pages_visually_checked':104,'key_pdf_pages_visually_checked':8,'key_url':KEY_URL,'key_sha256':KEY_SHA,'key_status':'provisional','official_key_rows_checked':732,'paired_mcq_mappings_checked':matches,'cross_booklet_key_conflicts':0,'keyed_answers':keyed,'withheld_conflicts':conflicts,'written_tasks':24,'tables':tables,'reasoning_checks':json.loads((root/'reasoning-checks.json').read_text()),'limitations':['Official key is provisional; no final key was listed on the inspected current Commission answer-key page.','This is source/key mapping and AI review, not an independent human or all-premises fact certification.','Written tasks preserve source context; no invented model answers. Ten valid subject-only paths remain where approved taxonomy has no suitable topic.'],'drafts':[{'id':d['id'],'source_sha256':d['source_sha256'],'payload_hash':digest(d['payload'])}for d in proposal['drafts']]}
 (root/'review-evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n');proposal['evidence_sha256']=hashlib.sha256((root/'review-evidence.json').read_bytes()).hexdigest()
 (root/'save-proposal.json').write_text(json.dumps(proposal,ensure_ascii=False,indent=2)+'\n')
 owners={d['author_id']for d in before['drafts']};assert len(owners)==1
 scope={'id':'gazetted-owner-ai-review-20261104','owner_id':owners.pop(),'authorization':authorization,'model':evidence['model'],'evidence_sha256':proposal['evidence_sha256'],'drafts':evidence['drafts']}
 Path('api/app/data/gazetted-owner-ai-review-20261104.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'drafts':len(proposal['drafts']),'keyed_answers':keyed,'unscored_conflicts':len(conflicts),'paired_mappings':matches,'scope_receipt':proposal['evidence_sha256']},indent=2))


if __name__=='__main__':main()
