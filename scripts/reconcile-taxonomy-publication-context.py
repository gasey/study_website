#!/usr/bin/env python3
"""Bind explicit saved question periods to tagging evidence; never infer today's facts.

Restricted to the current frozen run's context blockers. Ambiguous/static cases
stay blocked. No answers or canonical organization-context records are changed.
"""
import argparse,copy,hashlib,importlib.util,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REVIEWED_SCOPE='2d9737104889f1f512412463ef403cb7abf0f130bc0ec507b438f855c40f5855'
spec=importlib.util.spec_from_file_location('coverage',ROOT/'scripts/audit-review-coverage.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

# Individually inspected source stems: these years do not establish that the
# question tests changing facts. Do not turn a year into an automatic CA decision.
POLICY_HOLDS={
 'cq_31188681ea22f433':'1960 treaty usage rights are established treaty knowledge, not a news fact merely because a year appears.',
 'cq_8f87e5461ce1cb40':'NEP architect attribution needs a stable-policy versus news routing decision.',
 'cq_fd3d81a90e6b4143':'A birth-name question framed by a recent death remains a biography-versus-news routing issue.',
 'cq_07652514e8a5ccd1':'A 1968 Nobel identity in a 2014 paper needs science/history versus historical-news routing review.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Never overwrite a frozen supplement')
    scope=json.loads((a.run/'frozen.json').read_text())
    assert sha(a.run/'frozen.json')==(a.run/'frozen.sha256').read_text().strip()
    if sha(a.run/'frozen.json')!=REVIEWED_SCOPE:
        raise ValueError('Printed-period/policy decisions were inspected only for this exact frozen scope; review a new scope separately')
    blocked={r['canonical_id']for r in json.loads((a.run/'preflight.json').read_text())['results']
             if r.get('reason','').startswith('Current Affairs review lacks')}
    docs=json.loads((a.run/'documents.json').read_text());actual=json.loads((a.run/'source-hashes.json').read_text())
    items=[];reconciled=[];left=[]
    for original in scope['items']:
        row=original['candidate'];qid=row['canonical_id'];snap=original['snapshot'];stem=snap['record']['question']
        moto=('LDC under MPSC Paper-I 2025' in snap['paper']['id'] and str(snap['record']['qnum'])=='47'
              and original['primary'].get('topic_id')=='general-knowledge/sports')
        if qid not in blocked and not moto:continue
        if qid in POLICY_HOLDS:left.append({'canonical_id':qid,'reason':POLICY_HOLDS[qid]});continue
        years=sorted(set(re.findall(r'\b(?:19|20)\d{2}\b',stem)))
        if qid=='cq_f7dfbf1a338a5276':period='FY 2024; April 2025'
        elif len(years)==1:period=years[0]
        else:left.append({'canonical_id':qid,'reason':'No unique explicit printed reference period; exam year is not guessed'});continue
        folder=Path(original['candidate_file']).parent
        fallback={'tagging-batch5-20261107':'source-recovery-review2-20261107','tagging-batch6-20261107':'source-recovery-review3-20261107','tagging-batch7-20261107':'source-recovery-review4-20261107'}
        packet=ROOT/'reports'/fallback.get(folder.name,folder.name)/'oracle-packet.json'
        expected=scope['file_hashes'].get(str(packet.relative_to(ROOT)))
        if not expected or sha(packet)!=expected:raise ValueError('Original packet changed')
        saved=json.loads(packet.read_text());source=next(i for i in saved['items']if i['appearance_id']==row['appearance_id'])
        originals=saved.get('documents',[])+source.get('documents',[])
        if original.get('document'):originals.append(original['document'])
        evidence=row.get('source_evidence')or row.get('evidence')or{}
        if evidence.get('document_id') and evidence.get('sha256'):
            originals.append({'id':evidence['document_id'],'paper_id':snap['paper']['id'],'sha256':evidence['sha256'],'kind':'paper'})
        matches={d['id']:d for d in docs if d['paper_id']==snap['paper']['id'] and actual.get(d['id'])==d['sha256']
                 and any(o.get('paper_id')==d['paper_id']and o.get('sha256')==d['sha256'] for o in originals)}
        if len(matches)!=1 or type(original['physical_page'])is not int or original['physical_page']<1:
            left.append({'canonical_id':qid,'reason':'No exact original/current document/hash/page binding'});continue
        item=copy.deepcopy(original);candidate=item['candidate'];old_context=candidate.get('context_candidate')
        candidate['context_candidate']={'region':'','language':'en',**(old_context or {}),'time_behavior':'dated-event',
                                         'reference_period':period,'reference_basis':'printed'}
        candidate['context_reason']='Exact reference period is printed in the frozen source stem: '+stem
        if moto:
            candidate.update(action='keep',proposed_primary=snap['record']['classification'],
                             proposed_related=snap['record'].get('relatedClassifications',[]),
                             rationale='study-tagging-v1 explicitly routes named tournament edition winners to Current Affairs. Reject the static-Sports retag; retain the existing Current Affairs path and printed 2024 period. Saved source review is reused; no new independent inspection or answer verification.')
            item['primary']=candidate['proposed_primary'];item['related']=candidate['proposed_related'];item['reason']=candidate['rationale']
        candidate['reviewer_tool']='Codex policy/context reconciliation'
        candidate['reviewer_model']='Exact session model identity not exposed; no separate model or human inspection asserted'
        item['candidate_signature']=audit.signature(candidate);item['document']=next(iter(matches.values()))
        proof={'canonical_id':qid,'appearance_id':candidate['appearance_id'],'source_stem':stem,
               'original_context':old_context,'reference_period':period,'reference_basis':'printed',
               'packet_file':str(packet.relative_to(ROOT)),'packet_sha256':expected,
               'registered_document':item['document'],'new_source_inspection':False,
               'basis':'Explicit printed event/report period in the exact saved model-reviewed source; original packet, registered PDF and actual byte hashes agree',
               'policy_correction':bool(moto),'canonical_context_published':False}
        item['context_reconciliation']=proof;item['document_binding']=proof
        items.append(item);reconciled.append(proof)
    result={**scope,'items':items,'supplement_of_sha256':sha(a.run/'frozen.json'),
            'context_reconciliations':reconciled,'context_left_blocked':left,
            'supplement_basis':'Printed-period metadata normalization; one explicit policy correction retains the already correct live CA path. No answers or canonical context records changed.'}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    a.output.with_suffix('.sha256').write_text(sha(a.output)+'\n')
    print(json.dumps({'targets':len(items),'left_blocked':len(left),'sha256':sha(a.output)}))

if __name__=='__main__':main()
