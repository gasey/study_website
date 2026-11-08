#!/usr/bin/env python3
"""Freeze existing AI tag proposals and source snapshots for owner acceptance."""
import argparse,hashlib,importlib.util,json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('coverage_audit',ROOT/'scripts/audit-review-coverage.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def norm(path):
    if not isinstance(path,dict):return None
    return {k:path.get(k,path.get(k.removesuffix('_id'))) for k in ('subject_id','topic_id','subtopic_id')}

def completed_matches(existing,primary,related,snapshot):
    intended=(snapshot['record'].get('relatedClassifications',[]) if related is None else [norm(x)for x in related])
    return bool(existing and existing.get('source_bound') is True
                and primary==existing['primary'] and intended==existing['related'])

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--authorization',required=True)
    p.add_argument('--run-id',default='owner-taxonomy-20261108')
    p.add_argument('--completed',type=Path,help='Fresh source-bound completion export from Oracle; skip only matching intended paths')
    a=p.parse_args()
    if a.output.exists():raise SystemExit('Never overwrite a frozen run')
    corrections_file=ROOT/'reports/baseline-corrections-20261108/corrections.json'
    corrections=json.loads(corrections_file.read_text()) if corrections_file.exists() else {}
    resolutions_file=ROOT/'reports/booklet-card-cleanup-20261107/resolutions.json'
    data=audit.audit(resolution_file=resolutions_file,corrections_file=corrections_file)
    if data['problems'] or data['baseline_issues'] or data['unresolved_conflicts']:
        raise ValueError('Resolve audit/schema/baseline/conflict issues before freezing publication')
    completed={x['canonical_id']:x for x in json.loads(a.completed.read_text())} if a.completed else {}
    index={};packets={};hashes={}
    for entry in data['files']:
        file=ROOT/entry['file'];hashes[entry['file']]=sha(file)
        for row in json.loads(file.read_text()):
            row=dict(row);aid=row.get('appearance_id');corr=corrections.get(entry['file']+'::'+str(aid),{})
            if 'corrected_primary' in corr:row['current_primary']=corr['corrected_primary']
            if 'corrected_fingerprint' in corr:row['source_fingerprint']=corr['corrected_fingerprint']
            index[(aid,audit.signature(row))]=entry['file']
    items=[];skipped=[]
    for row in data.pop('effective_candidates'):
        existing=completed.get(row['canonical_id'])
        primary=norm(row.get('proposed_primary') or row.get('proposed_classification'))
        related=row.get('proposed_related',row.get('proposed_secondary'))
        file=index[(row['appearance_id'],audit.signature(row))]
        folder=Path(file).parent
        fallback={'tagging-batch5-20261107':'source-recovery-review2-20261107','tagging-batch6-20261107':'source-recovery-review3-20261107','tagging-batch7-20261107':'source-recovery-review4-20261107'}
        packet_path=ROOT/'reports'/fallback.get(folder.name,folder.name)/'oracle-packet.json'
        if str(packet_path) not in packets:
            packet=json.loads(packet_path.read_text());packets[str(packet_path)]=(packet,{x['appearance_id']:x for x in packet['items']})
            hashes[str(packet_path.relative_to(ROOT))]=sha(packet_path)
        packet,by_id=packets[str(packet_path)];source=by_id[row['appearance_id']]
        snap=source['snapshot'];paper=snap['paper']['id']
        if completed_matches(existing,primary,related,snap):
            skipped.append(row['canonical_id']);continue
        evidence=row.get('source_evidence') or row.get('evidence') or {}
        docid=evidence.get('document_id') or evidence.get('source_document_id')
        docs=[d for d in (packet.get('documents',[]) + source.get('documents',[])) if d.get('paper_id')==paper and d.get('kind')=='paper']
        docs=list({d['id']:d for d in docs}.values())
        doc=next((d for d in docs if d['id']==docid),None) if docid else docs[0] if len(docs)==1 else None
        related=row.get('proposed_related',row.get('proposed_secondary'))
        items.append({'candidate':row,'candidate_file':file,'candidate_signature':audit.signature(row),
                      'snapshot':snap,'source_fingerprint':source['source_fingerprint'],
                      'primary':norm(row.get('proposed_primary') or row.get('proposed_classification')),
                      'related':None if related is None else [norm(x) for x in related],
                      'reason':row.get('rationale') or row.get('reason') or row.get('review_reason') or row.get('review_summary') or '',
                      'document':doc,'physical_page':evidence.get('physical_page') or evidence.get('page') or snap['record'].get('page')})
    for f in (corrections_file,resolutions_file,ROOT/'scripts/audit-review-coverage.py'):
        if f.exists():hashes[str(f.relative_to(ROOT))]=sha(f)
    if a.completed:hashes[str(a.completed)]=sha(a.completed)
    result={'run_id':a.run_id,'at':datetime.now(timezone.utc).isoformat(),
            'authorization':a.authorization,'review_kind':'owner-delegated-ai-taxonomy',
            'independent_human_review':False,'owner_email':'hruaitluangasailo20@gmail.com',
            'file_hashes':hashes,'coverage_audit':data,'already_completed_matching_live_paths':skipped,'items':items}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    print(json.dumps({'targets':len(items),'already_completed':len(skipped),'actions':dict(Counter(i['candidate']['action'] for i in items)), 'sha256':sha(a.output)}))
if __name__=='__main__':main()
