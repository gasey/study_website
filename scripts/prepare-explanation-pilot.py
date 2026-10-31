#!/usr/bin/env python3
"""Adjudicate model-drafted English explanations into human-review packets.

This tool never writes bank data, grants approval, publishes, or mints credit.
"""
import argparse,hashlib,json,re
from pathlib import Path
from urllib.parse import urlsplit,quote
IDENTITY_FIELDS=['id','paperId','type','question','options','direction','questionMarkup','optionsMarkup','passage','answerIndex','answerSource']
def identity(q):return hashlib.sha256(json.dumps({k:q.get(k)for k in IDENTITY_FIELDS},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def rows_by_id(rows,name):
    if not isinstance(rows,list):raise ValueError(name+' must be a list')
    out={}
    for r in rows:
        if not isinstance(r,dict)or not isinstance(r.get('id'),str)or r['id']in out:raise ValueError(name+' has missing/duplicate IDs')
        out[r['id']]=r
    return out
def plausible_reference(c):
    if not isinstance(c,dict):return False
    if any(not isinstance(c.get(field),str)for field in ('url','title','supports')):return False
    try:u=urlsplit(c['url'])
    except ValueError:return False
    return u.scheme=='https' and bool(u.hostname)and not(u.username or u.password)and len(c.get('supports','').strip())>=10 and len(c.get('title','').strip())>=3
GENERIC=re.compile(r'conflicts with the passage meaning or the required word|matches the passage deduction or grammatical|this option is (?:wrong|incorrect) because it is not correct',re.I)
def adjudicate(items,drafts,blind,critiques,keys,current,check_files=True):
    inputs=rows_by_id(items,'input');d=rows_by_id(drafts,'draft');b=rows_by_id(blind,'blind');c=rows_by_id(critiques,'critique');k=rows_by_id(keys,'keys');bank=rows_by_id(current,'bank')
    for name,records in [('draft',d),('blind',b),('critique',c),('keys',k)]:
        if set(records)!=set(inputs):raise ValueError(name+' ID set differs from pilot')
    result=[]
    for qid,item in inputs.items():
        draft=d[qid];review=b[qid];critique=c[qid];key=k[qid];now=bank.get(qid);issues=[];n=len(item['options'])
        for name,obj,valid in [('draft',draft,'proposed'),('blind',review,'supported'),('critique',critique,'approve_draft')]:
            if obj.get('status')!=valid:issues.append(name+': '+str(obj.get('status','missing status')))
        for name,obj in [('draft',draft),('blind',review)]:
            ai=obj.get('answer_index')
            if type(ai)is not int or not 0<=ai<n:issues.append(name+': invalid/unresolved choice')
        if draft.get('answer_index')!=review.get('answer_index'):issues.append('models disagree')
        if draft.get('answer_index')!=key['answer_index'] or review.get('answer_index')!=key['answer_index']:issues.append('stored key disagreement: source/key adjudication required')
        explanation=draft.get('explanation','')
        if not isinstance(explanation,str)or len(explanation.split())<24:issues.append('explanation too short for this pilot')
        analysis=draft.get('option_analysis')or[]
        if not isinstance(analysis,list):analysis=[]
        if len(analysis)!=n or any(not isinstance(r,dict)or type(r.get('index'))is not int for r in analysis)or {r.get('index')for r in analysis if isinstance(r,dict)}!=set(range(n)):issues.append('option analysis incomplete/duplicated')
        if any(not isinstance(r,dict)or not isinstance(r.get('reason'),str)or len(r['reason'].strip())<12 or GENERIC.search(r['reason'])for r in analysis):issues.append('option analysis is generic or insufficient')
        citations=draft.get('citations')or[]
        if not isinstance(citations,list):citations=[];issues.append('invalid citation list')
        if any(not plausible_reference(x)for x in citations):issues.append('invalid citation metadata')
        if item['topic']!='english/comprehension' and not citations:issues.append('no checked grammar/dictionary reference')
        if not draft.get('source_checks')or not review.get('source_checks'):issues.append('source check missing')
        if not now or identity(now)!=item['identity_sha256']:issues.append('bank baseline changed')
        if critique.get('presentation_fixes'):issues.append('source presentation correction required')
        if check_files:
            p=Path(item['source']['path'])
            if not p.is_file()or hashlib.sha256(p.read_bytes()).hexdigest()!=item['source']['sha256']:issues.append('source PDF changed/missing')
        status='hold' if issues else 'ready_for_human_review'
        row={'revision_author':draft.get('revision_author'),'revision_note':draft.get('revision_note'),'id':qid,'canonical_id':item['canonical_id'],'status':status,'issues':issues,'model_notes':{'draft':draft.get('issues',[]),'blind':review.get('issues',[]),'critique':critique.get('issues',[])},'presentation_fixes':critique.get('presentation_fixes',[]),'draft_answer_index':draft.get('answer_index'),'blind_answer_index':review.get('answer_index'),'stored_answer_index':key['answer_index'],'baseline_sha256':item['identity_sha256'],'source':item['source'],'proposal':None}
        if status=='ready_for_human_review':
            # Include specific distractor reasoning in the published explanation text.
            final=explanation.strip()+'\n\nOptions:\n'+'\n'.join(chr(65+r['index'])+'. '+r['reason'].strip()for r in sorted(analysis,key=lambda r:r['index']))
            evidence=[{'kind':'reasoning','note':('AI-assisted pilot draft by GPT-6 Luna; '+('corrected explanation by '+draft['revision_author']+'. ' if draft.get('revision_author') else '')+'Blind answer check and explanation critique by GPT-6.1 Sol. These are model checks, not human approvals. '+review.get('reason',''))[:3900]}, {'kind':'reference','url':'https://study.hawayu.in/papers/source/'+quote(item['source']['paper_id'],safe='/')+('#page='+str(item['source']['page'])if item['source'].get('page')else ''),'note':'Printed question '+str(item['source'].get('printed_question'))+'; source PDF SHA256 '+item['source']['sha256']+'. Source identity is retained; this reference does not independently prove an answer key.'}]
            evidence.extend({'kind':'reference','url':x['url'],'note':(x['title']+': '+x['supports'])[:3900]}for x in citations[:6])
            row['proposal']={'kind':'explanation','canonical_id':item['canonical_id'],'appearance_id':qid,'subject_id':'english','title':'Explain: '+item['question'][:90],'patch':{'explanation':final},'rationale':'English explanation pilot: add a source-supported teaching explanation without changing the stored answer, options, classification or provenance. Model agreement is not an independent human approval. Reviewer must confirm source context and citations.','evidence':evidence}
        result.append(row)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,required=True);p.add_argument('--bank',type=Path,required=True);p.add_argument('--revisions',type=Path);p.add_argument('--revision-reviews',type=Path);a=p.parse_args();d=a.directory
    if bool(a.revisions)!=bool(a.revision_reviews):p.error('Both revisions and revision reviews are required together')
    read=lambda name:json.loads((d/name).read_text())
    drafts=rows_by_id(read('draft-a-output.json')+read('draft-b-output.json'),'drafts');critiques=rows_by_id(read('sol-explanation-critique.json'),'critiques')
    if a.revisions:
        revisions=rows_by_id(json.loads(a.revisions.read_text()),'revisions');reviews=rows_by_id(json.loads(a.revision_reviews.read_text()),'revision reviews')
        if set(revisions)!=set(reviews)or not set(revisions)<=set(drafts):raise ValueError('Revision/review ID sets must agree and belong to the pilot')
        for qid,draft in revisions.items():
            if not draft.get('revision_author')or not draft.get('revision_note'):raise ValueError('Revision provenance required')
            # Source-context repairs are a separate proposal, never cleared by an explanation rewrite.
            if critiques[qid].get('presentation_fixes'):raise ValueError('Cannot replace source-context hold with explanation revision')
            drafts[qid]=draft;critiques[qid]=reviews[qid]
    supplemental=d/'supplemental-review-holds.json'
    if supplemental.is_file():
        for qid,hold in rows_by_id(json.loads(supplemental.read_text()),'supplemental holds').items():
            if qid not in critiques or hold.get('status')!='hold':raise ValueError('Invalid supplemental hold')
            prior=critiques[qid];critiques[qid]={**prior,'status':'hold','issues':prior.get('issues',[])+hold.get('issues',[]),'presentation_fixes':prior.get('presentation_fixes',[])+hold.get('presentation_fixes',[])}
    rows=adjudicate(read('pilot-questions.json'),list(drafts.values()),read('sol-blind-review.json'),list(critiques.values()),read('comparison-keys.json'),json.loads(a.bank.read_text())['questions'])
    (d/'adjudicated.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n')
    proposals=d/'proposals';proposals.mkdir(exist_ok=True)
    expected=set()
    for row in rows:
        if row['proposal']:
            target=proposals/(row['id']+'.json');expected.add(target.name);target.write_text(json.dumps(row['proposal'],indent=2,ensure_ascii=False)+'\n')
    # Stale review packets must not survive a later failed eligibility check.
    for target in proposals.glob('*.json'):
        if target.name not in expected:target.unlink()
    summary={'total':len(rows),'ready_for_human_review':sum(r['status']=='ready_for_human_review'for r in rows),'held':sum(r['status']=='hold'for r in rows),'bank_modified':False,'published':False,'human_approvals':0}
    (d/'adjudication-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
if __name__=='__main__':main()
