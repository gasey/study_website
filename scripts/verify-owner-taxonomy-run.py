#!/usr/bin/env python3
"""Read-only end-to-end proof of a frozen owner taxonomy publication run."""
import argparse,gzip,hashlib,importlib.util,json,os,sys
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

os.environ['ISM_DB_TRANSPORT']='local'
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,'/srv/api')
spec=importlib.util.spec_from_file_location('worker',ROOT/'scripts/bank-review-worker.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);a=p.parse_args();run=a.run
    frozen=json.loads((run/'frozen.json').read_text());pre=json.loads((run/'preflight.json').read_text())
    rows=w.remote("SELECT p.id,p.state,p.manifest,p.manifest_hash,p.receipt,p.contribution_id FROM bank_publications p WHERE EXISTS(SELECT 1 FROM contribution_events e WHERE e.contribution_id=p.contribution_id AND e.action='operator_taxonomy_authorization' AND e.detail->>'run_id'="+w.literal(frozen['run_id'])+")",True)
    late_blocked=set();targets=set();phases={}
    for plan in run.rglob('preflight.json'):
        phase=json.loads(plan.read_text());blocked=set()
        for file in (plan.parent/'chunks').glob('*.queued.json'):
            blocked.update(json.loads(file.read_text()).get('blocked',[]))
        late_blocked.update(blocked)
        targets.update({r['canonical_id']for r in phase['results']if r['status']=='ready'}-blocked)
        phases[str(plan.parent.relative_to(run))]=phase['counts']
    assert len(rows)==len(targets) and all(r['state']=='applied'for r in rows),'Publications remain unapplied'
    assert {r['manifest']['payload']['canonical_id']for r in rows}==targets
    first_pub=json.loads((run/'chunks/0001.queued.json').read_text())['publications'][0]
    initial=next(r for r in rows if r['id']==first_pub)['manifest']['bank_sha256']
    backup=w.BANK.parent/'review-backups'/(initial+'.json.gz')
    if backup.exists():raw=gzip.decompress(backup.read_bytes())
    else:raw=(w.BANK.parent/'review-backups'/(initial+'.json')).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==initial
    before=json.loads(raw);after=json.loads(w.BANK.read_text())
    b={q['id']:q for q in before['questions']};c={q['id']:q for q in after['questions']}
    assert b.keys()==c.keys(),'Question identities changed'
    assert {k:v for k,v in before.items()if k!='questions'}=={k:v for k,v in after.items()if k!='questions'},'Paper identity/metadata changed'
    allowed={'classifications','relatedClassifications','reviewPublicationId'}
    changed=[]
    for qid in b:
        if b[qid]==c[qid]:continue
        assert {k:v for k,v in b[qid].items()if k not in allowed}=={k:v for k,v in c[qid].items()if k not in allowed},'Non-taxonomy content changed: '+qid
        changed.append(qid)
    assert set(changed)=={r['manifest']['baseline']['record']['id']for r in rows},'Unexpected changed source set'
    # Verify every independent receipt in bounded read-only queries again.
    for start in range(0,len(rows),100):
        group=rows[start:start+100]
        w.verify_live_batch([r['receipt']for r in group],{r['id']:r['manifest']for r in group})
    unrelated=w.remote("SELECT count(*)::int AS n FROM bank_publications WHERE state='exported'",True)[0]['n']
    assert unrelated==0,'Outstanding publication exports'
    decisions=w.remote("SELECT count(*)::int AS peer_votes FROM contribution_decisions WHERE contribution_id IN("+','.join(w.literal(r['contribution_id'])for r in rows)+')',True)[0]['peer_votes']
    answers=w.remote("SELECT count(*)::int AS answer_decisions FROM admin_answer_decisions WHERE contribution_id IN("+','.join(w.literal(r['contribution_id'])for r in rows)+')',True)[0]['answer_decisions']
    assert decisions==answers==0,'Tagging run must not create answer/peer inspections'
    current=w.sha(w.BANK);sync=w.remote('SELECT bank_checksum FROM sync_log WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1',True)[0]['bank_checksum']
    assert current==sync,'Canonical/live checksums differ'
    result={'at':datetime.now(timezone.utc).isoformat(),'run_id':frozen['run_id'],'frozen_sha256':hashlib.sha256((run/'frozen.json').read_bytes()).hexdigest(),
            'published':len(rows),'phase_counts':phases,'late_context_blocks':len(late_blocked),'source_questions':len(b),'changed_sources':len(changed),
            'all_answers_options_text_provenance_preserved':True,'paper_identity_preserved':True,'peer_votes_created':decisions,
            'answer_decisions_created':answers,'initial_bank_sha256':initial,'final_bank_sha256':current,
            'unapplied_exports':unrelated,'publication_ids':[r['id']for r in rows],
            'blocker_reasons':dict(Counter(r['reason']for r in pre['results']if r['status']=='blocked'))}
    results=w.remote("SELECT DISTINCT ON(e.detail->>'canonical_id') e.detail,e.contribution_id,p.id AS publication_id,p.state AS publication_state FROM contribution_events e LEFT JOIN bank_publications p ON p.contribution_id=e.contribution_id WHERE e.action='owner_ai_taxonomy_progress' AND e.detail->>'run_id'="+w.literal(frozen['run_id'])+" ORDER BY e.detail->>'canonical_id',e.id DESC",True)
    assert len(results)==len(frozen['items']),'A frozen target has no recorded outcome'
    result['recorded_outcomes']=dict(Counter(r['detail']['status']for r in results))
    assert result['recorded_outcomes'].get('published',0)==len(rows)
    result['remaining_in_entire_bank_tagging_pass']=len(b)-len(rows)-result['recorded_outcomes'].get('confirmed',0)
    (run/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    (run/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k not in ('publication_ids','blocker_reasons')}))
if __name__=='__main__':main()
