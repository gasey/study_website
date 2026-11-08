#!/usr/bin/env python3
"""Inventory saved pending tagging work; never claims source or answer verification."""
import argparse,json,re,hashlib
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MARKER=re.compile(r"\b(?:series|booklet(?:\s+series)?|set)(?:\s+(?:no\.?|number|code))?[\s_:'\"()\-]*([A-D1-4])(?=$|[\s.\-_'\"()])",re.I)
def family(paper):
    path=Path(paper);match=MARKER.search(path.name)
    if not match:return None
    name=MARKER.sub('[booklet]',path.name)
    # Numbered source-archive prefixes are locators, not printed paper numbers.
    name=re.sub(r'^\d+[.]\s*','',name)
    name=re.sub(r'[.\s]+(?=\.pdf$)','',name,flags=re.I)
    return str(path.parent/name).lower(),match[1].upper()
def signature(row):
    keys=['source_fingerprint','current_primary','action','proposed_primary','proposed_related']
    return hashlib.sha256(json.dumps({k:row.get(k) for k in keys},sort_keys=True).encode()).hexdigest()

def audit(root=ROOT,resolution_file=None,corrections_file=None):
    candidates={};by_appearance=defaultdict(list);by_canonical=defaultdict(list);families=defaultdict(lambda:defaultdict(set));actions=Counter();files=[];problems=[];invalid=set();baseline_issues=[]
    corrections=json.loads(corrections_file.read_text()) if corrections_file and corrections_file.exists() else {}
    for file in sorted((root/'reports').glob('tagging-*/pending-candidates.json')):
        try:rows=json.loads(file.read_text())
        except (ValueError,OSError) as exc:problems.append({'file':str(file.relative_to(root)),'error':str(exc)});continue
        if not isinstance(rows,list):problems.append({'file':str(file.relative_to(root)),'error':'Expected candidate array'});continue
        fallback={'tagging-batch5-20261107':'source-recovery-review2-20261107','tagging-batch6-20261107':'source-recovery-review3-20261107','tagging-batch7-20261107':'source-recovery-review4-20261107'}
        packet=root/'reports'/fallback.get(file.parent.name,file.parent.name)/'oracle-packet.json'
        saved_packet=json.loads(packet.read_text()) if packet.exists() else {}
        source_by_id={i.get('appearance_id'):i for i in saved_packet.get('items',[])}
        name=str(file.relative_to(root));files.append({'file':name,'records':len(rows)})
        for row in rows:
            aid=row.get('appearance_id');cid=row.get('canonical_id')
            if not aid or not cid:problems.append({'file':name,'error':'Missing source/question identity'});continue
            corr=corrections.get(f'{name}::{aid}')
            if corr:
                row=dict(row)
                if 'corrected_primary' in corr:row['current_primary']=corr['corrected_primary']
                if 'corrected_fingerprint' in corr:row['source_fingerprint']=corr['corrected_fingerprint']
            item=source_by_id.get(aid)
            if item and (row.get('current_primary')!=(item.get('snapshot') or {}).get('record',{}).get('classification') or row.get('source_fingerprint')!=item.get('source_fingerprint')):
                invalid.add((name,aid));baseline_issues.append({'file':name,'appearance_id':aid,'issue':'Candidate baseline/fingerprint does not match its saved source snapshot'})
            if not item:
                invalid.add((name,aid));baseline_issues.append({'file':name,'appearance_id':aid,'issue':'Source snapshot unavailable to this audit'})
            candidates[(name,aid)]=row
            target={'proposal_signature':signature(row),'file':name,'appearance_id':aid,'canonical_id':cid,'review_status':row.get('review_status'),'action':row.get('action')}
            by_appearance[aid].append(target);by_canonical[cid].append(target);actions[row.get('action','unknown')]+=1
            evidence=row.get('source_evidence') or {};paper=evidence.get('paper_id') or row.get('paper_id')
            # Resolve paper identity only from the saved source snapshot when absent.
            if not paper:
                item=source_by_id.get(aid)
                if item:paper=(item.get('snapshot') or {}).get('paper',{}).get('id')
            group=family(paper) if paper else None
            if group:families[group[0]][group[1]].add(aid)
    resolutions=json.loads(resolution_file.read_text()) if resolution_file and resolution_file.exists() else {}
    effective=[];unresolved=[];resolved=[]
    for aid,targets in by_appearance.items():
        signatures={t['proposal_signature'] for t in targets}
        usable=[t for t in targets if (t['file'],aid) not in invalid]
        if not usable:continue
        selected=usable[0]
        if len({t['proposal_signature'] for t in usable})>1:
            resolution=resolutions.get(aid)
            if not resolution or set(resolution.get('proposal_signatures',[]))!=signatures:
                unresolved.append({'appearance_id':aid,'proposals':targets});continue
            selected=next((t for t in targets if t['file']==resolution['preferred_file']),None)
            if selected is None:unresolved.append({'appearance_id':aid,'proposals':targets});continue
            resolved.append(aid)
        effective.append(candidates[(selected['file'],aid)])
    return {'baseline_issues':baseline_issues,'effective_candidates':effective,'unresolved_conflicts':unresolved,'resolved_conflicts':resolved,
      'unique_actions':dict(Counter(r['action'] for r in effective)), 'observed_at':datetime.now(timezone.utc).isoformat(),'read_only':True,'files':files,
      'saved_candidate_records':sum(f['records'] for f in files),'unique_appearances':len(by_appearance),'unique_questions':len(by_canonical),'actions':dict(actions),
      'already_reviewed_appearance_ids':sorted(by_appearance),'already_reviewed_canonical_ids':sorted(by_canonical),
      'repeated_appearance_candidates':{k:v for k,v in by_appearance.items() if len(v)>1},
      'repeated_canonical_candidates':{k:v for k,v in by_canonical.items() if len(v)>1},
      'families_with_multiple_booklets_reviewed':{k:{s:len(ids) for s,ids in variants.items()} for k,variants in families.items() if len(variants)>1},
      'problems':problems,'meaning':'Saved tagging candidate coverage only. Pending proposals are not published tags, solved answers, or independent source verification. A booklet family is a routing aid, not proof of question equivalence.'}
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);parser.add_argument('--selection-output',type=Path);parser.add_argument('--resolutions',type=Path,default=ROOT/'reports/booklet-card-cleanup-20261107/resolutions.json');parser.add_argument('--corrections',type=Path,default=ROOT/'reports/baseline-corrections-20261108/corrections.json');args=parser.parse_args();data=audit(resolution_file=args.resolutions,corrections_file=args.corrections)
    selection=data.pop('effective_candidates')
    if args.selection_output:args.selection_output.parent.mkdir(parents=True,exist_ok=True);args.selection_output.write_text(json.dumps(selection,ensure_ascii=False,indent=2)+'\n')
    data['deduplicated_candidates']=len(selection)
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:data[k] for k in ['observed_at','saved_candidate_records','unique_appearances','unique_questions','actions','unique_actions','deduplicated_candidates','resolved_conflicts','problems']}|{'files':len(data['files']),'repeated_appearance_candidates':len(data['repeated_appearance_candidates']),'repeated_canonical_candidates':len(data['repeated_canonical_candidates']),'families_with_multiple_booklets_reviewed':len(data['families_with_multiple_booklets_reviewed'])},indent=2))
