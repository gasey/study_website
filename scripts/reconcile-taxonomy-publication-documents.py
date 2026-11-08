#!/usr/bin/env python3
"""Recover malformed candidate evidence from exact hash-bound original packet metadata.

Creates a new, explicit supplemental scope; never edits the original frozen scope.
No source inspections, semantic decisions or bank changes are asserted here.
"""
import argparse,copy,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True)
    p.add_argument('--preflight',type=Path,required=True);p.add_argument('--documents',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--exclude-scope',type=Path,help='Already frozen supplement; never select its targets twice')
    a=p.parse_args()
    if a.output.exists():raise ValueError('Never overwrite a supplemental frozen scope')
    scope=json.loads((a.run/'frozen.json').read_text())
    assert sha(a.run/'frozen.json')==(a.run/'frozen.sha256').read_text().strip()
    pre=json.loads(a.preflight.read_text());docs=json.loads(a.documents.read_text())
    actual=json.loads((a.run/'source-hashes.json').read_text())
    targets={r['canonical_id']for r in pre['results']if r['status']=='blocked'and 'String should match pattern' in r['reason']}
    if a.exclude_scope:
        assert sha(a.exclude_scope)==a.exclude_scope.with_suffix('.sha256').read_text().strip()
        previous=json.loads(a.exclude_scope.read_text())
        assert previous['run_id']==scope['run_id']
        targets-={i['candidate']['canonical_id']for i in previous['items']}
    items=[];bindings=[];excluded=[]
    for original in scope['items']:
        if original['candidate']['canonical_id']not in targets:continue
        item=copy.deepcopy(original);paper=item['snapshot']['paper']['id'];candidate=item['candidate']
        # The existing rule routes a named tournament edition's winner to Current
        # Affairs, not static Sports. Preserve this known policy conflict for review.
        if ('LDC under MPSC Paper-I 2025' in paper and str(item['snapshot']['record']['qnum'])=='47'
                and item['primary'].get('topic_id')=='general-knowledge/sports'):
            excluded.append({'canonical_id':candidate['canonical_id'],'reason':'Known policy conflict: 2024 MotoGP winner is dated Current Affairs, not static Sports'});continue
        packet=ROOT/Path(item['candidate_file']).parent/'oracle-packet.json'
        expected=scope['file_hashes'].get(str(packet.relative_to(ROOT)))
        if not expected or sha(packet)!=expected:raise ValueError('Original source packet changed')
        saved=json.loads(packet.read_text())
        source=next(i for i in saved['items']if i['appearance_id']==candidate['appearance_id'])
        original_docs=[d for d in (saved.get('documents',[])+source.get('documents',[]))if d['paper_id']==paper and d['kind']=='paper']
        matches={f['id']:f for f in docs if f['paper_id']==paper and actual.get(f['id'])==f['sha256']
                 and any(d['sha256']==f['sha256'] for d in original_docs)}
        if len(matches)!=1:
            excluded.append({'canonical_id':candidate['canonical_id'],'reason':'No unique current registered document matches the exact original packet paper/hash and actual bytes'});continue
        doc=next(iter(matches.values()))
        binding={'appearance_id':candidate['appearance_id'],'basis':'Exact original frozen packet paper/document/hash, current registry and actual PDF bytes agree',
                 'original_evidence':candidate.get('source_evidence'),'packet_file':str(packet.relative_to(ROOT)),
                 'packet_sha256':expected,'original_packet_documents':original_docs,
                 'registered_document':doc,'new_source_inspection':False}
        item['document']=doc;item['document_binding']=binding
        items.append(item);bindings.append(binding)
    result={**scope,'items':items,'supplement_of_sha256':sha(a.run/'frozen.json'),
            'supplement_basis':'Metadata binding recovery only; original candidates and exact source fingerprints retained',
            'document_reconciliations':bindings,'excluded_policy_conflicts':excluded}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    a.output.with_suffix('.sha256').write_text(sha(a.output)+'\n')
    print(json.dumps({'reconciled':len(items),'left_blocked':len(excluded),'sha256':sha(a.output)}))

if __name__=='__main__':main()
