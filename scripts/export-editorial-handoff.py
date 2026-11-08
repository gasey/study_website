#!/usr/bin/env python3
"""Export assigned source worklists and friend-facing instructions, read-only."""
import argparse,json,subprocess,zipfile,shlex
from pathlib import Path
from urllib.parse import urlencode
from datetime import datetime,timezone

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 sql="""BEGIN READ ONLY; SET LOCAL statement_timeout='60s';
 WITH source_rows AS (
 SELECT cp.collection_id,a.id AS appearance_id,a.canonical_id,a.paper_id,a.qnum,a.page,a.qnum_seq,
 q.type,a.question,s.answer_status,q.status,q.source_defect,q.key_disputed,
 nullif(btrim(q.explanation),'') IS NULL AS missing_explanation,
 p.exam_name,p.year,p.source_file,p.pdf_url
 FROM collection_papers cp JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version
 JOIN appearances a ON a.paper_id=cp.paper_id JOIN canonical_questions q ON q.id=a.canonical_id
 JOIN v_bank_answer_status s ON s.id=q.id JOIN papers p ON p.id=a.paper_id
 WHERE c.id IN ('udc','combined-prelims') AND cp.allow_browse AND q.status IN ('live','held')
 ) SELECT json_agg(source_rows ORDER BY collection_id,year DESC NULLS LAST,paper_id,qnum_seq,appearance_id) FROM source_rows;
 COMMIT;"""
 result=subprocess.run(['ssh','ubuntu@152.67.31.231','sudo -u postgres psql -X -qAt -v ON_ERROR_STOP=1 -d mpsc'],input=sql,text=True,capture_output=True,check=True,timeout=70)
 rows=json.loads(result.stdout)
 assignments=json.loads((a.output/'assignments.json').read_text())
 for collection,name in [('udc','Sangzel'),('combined-prelims','Solomon')]:
  assignment=next(x for x in assignments if x['collection_id']==collection)
  selected=[r for r in rows if r['collection_id']==collection];papers={}
  for r in selected:
   r['review_url']='https://study.hawayu.in/editorial?'+urlencode({'assignment':assignment['id'],'paper':r['paper_id'],'question':r['canonical_id'],'appearance':r['appearance_id']})
   r['correction_url']='https://study.hawayu.in/contribute/new?'+urlencode({'question':r['canonical_id'],'appearance':r['appearance_id'],'kind':'answer' if r['type']=='mcq' else 'transcription'})
   r['source_pdf_url']=('https://study.hawayu.in/papers/source/'+__import__('urllib.parse',fromlist=['quote']).quote(r['source_file'],safe='/')) if r['source_file'] else r['pdf_url']
   papers.setdefault(r['paper_id'],{'paper_id':r['paper_id'],'exam':r['exam_name'],'year':r['year'],'pdf':r['source_pdf_url'],'source_questions':0})['source_questions']+=1
  title='UDC' if collection=='udc' else 'MCS Prelims'
  onboarding=(f"1. Your account **{assignment['email']}** and this assignment are active. Get your individual starting password privately from the owner. Log in at https://study.hawayu.in/login?next=%2Feditorial; do not create another account.\n2. Change your starting password in Account security (https://study.hawayu.in/account/security), then return to Assigned paper review. Keep your password private."
    if assignment['state']=='active' else f"1. Create your own account at https://study.hawayu.in/join using **{assignment['email']}**. Choose your own password; do not share it.\n2. Tell the owner your account is ready. The owner confirms it and activates this assignment. The reservation does not grant access before activation.")
  guide=f'''# {name} — {title} paper review

Open [Assigned paper review](https://study.hawayu.in/editorial).

{onboarding}
3. Sign in, open Assigned paper review, choose {title}, then a paper and question. Keep the original PDF beside it; physical PDF page and printed question number can differ.
4. Compare the complete question, shared instructions, underlines, options, diagrams, answer and explanation. For written questions, inspect every passage/subquestion and the marking guidance. Original exam-date facts remain tied to the sitting.
5. If correct, tick the four inspection boxes, add a specific source/evidence note and save Checked. If evidence is missing or the source is defective, use Cannot verify or Needs correction. Do not guess.
6. To fix content, choose Propose a correction, select the appropriate correction kind, give evidence and a useful explanation, then save and submit the proposal. [Your proposals](https://study.hawayu.in/contribute) retain the diff, review decisions and publication history. You do not publish your own change or turn an AI suggestion into an official key.
7. A changed source rejects an old form. Copy your note somewhere safe, reopen the current question and compare again. Never repeatedly force-save an old draft. After any published correction, repeat the source check; an earlier check is historical.

Assignment covers **{len(papers)} source papers / {len(selected):,} source appearances** in this snapshot. Similar booklet copies and shared questions keep their exact identities; a canonical correction can affect more than one exam. Work on one paper at a time and tell the owner when the paper is finished or blocked.

An editorial check records your inspection. It does not automatically change answer provenance, remove a scoring hold or certify the whole paper. “Verified solution · unofficial” and official-key labels are different; verify the actual evidence. Official answer keys do not verify an explanation. High-impact contribution changes still need the existing independent review and owner publication process.

The attached question index contains no answers. It gives the exact review/source/correction links and current backlog flags. Use the live page before acting; this snapshot becomes stale as corrections land. Contribution rate limits still apply. If a paper batch exceeds the current limit, tell the owner rather than reusing another account.

No email invitation was sent automatically. No admin or publishing role is granted by this assignment.
'''
  (a.output/(collection+'-START-HERE.md')).write_text(guide)
  (a.output/(collection+'-source-index.json')).write_text(json.dumps({'captured_at':datetime.now(timezone.utc).isoformat(),'assignment_id':assignment['id'],'papers':list(papers.values()),'questions':selected},indent=2,ensure_ascii=False)+'\n')
  with zipfile.ZipFile(a.output/(collection+'-review-pack.zip'),'w',zipfile.ZIP_DEFLATED) as z:
   for filename in [collection+'-START-HERE.md',collection+'-source-index.json']:z.write(a.output/filename,filename)
  print(title,len(papers),'papers,',len(selected),'source appearances')
if __name__=='__main__':main()
