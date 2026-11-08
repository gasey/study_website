#!/usr/bin/env python3
"""Trusted Oracle read adapter. JSON stdin; never exposes service credentials."""
import asyncio,json,os,sys,subprocess
from pathlib import Path
from urllib.parse import urlsplit
sys.path.insert(0,'/srv/api')
from app.services.review_policy import digest

async def run(data):
    from app.db import open_pool,close_pool,cursor
    from app.services import bank_review as review
    from app.services.operator_maintenance import _validate_explanation_target
    from app.services.discovery import ranking,hot_picks
    await open_pool()
    try:
        async with cursor() as cur:
            if data['operation']=='audit':
                import hashlib
                bank=Path('/srv/study/workshop/mpsc-question-bankv2/bank/mpsc_bank_v2.json')
                baseline_sha=data.get('baseline_bank_sha256')
                if baseline_sha:
                    import re,gzip
                    if not re.fullmatch('[0-9a-f]{64}',baseline_sha):raise ValueError('Invalid historical bank hash')
                    content=gzip.decompress((bank.parent/'review-backups'/(baseline_sha+'.json.gz')).read_bytes())
                    if hashlib.sha256(content).hexdigest()!=baseline_sha:raise ValueError('Historical backup hash mismatch')
                else:content=bank.read_bytes()
                payload=json.loads(content);targets=set(data.get('appearance_ids',[]))
                explanations={q['id']:q.get('explanation') for q in payload['questions'] if q['id'] in targets}
                publications={q['id']:q.get('reviewPublicationId') for q in payload['questions'] if q['id'] in targets}
                for q in payload['questions']:
                    if q['id'] in targets:q.pop('explanation',None);q.pop('reviewPublicationId',None)
                result={'bank_sha256':hashlib.sha256(content).hexdigest(),'unaffected_content_sha256':digest(payload),'target_explanations':explanations,'target_publications':publications}
                for table in ('attempts','editorial_assignments','editorial_assignment_papers','editorial_checks','review_grants'):
                    await cur.execute('SELECT to_jsonb(t) AS row FROM '+table+' t ORDER BY to_jsonb(t)::text')
                    rows=await cur.fetchall();result[table]={'count':len(rows),'sha256':digest(rows)}
                # Match bank_review.create's ordinary budget: a fully attributed,
                # scoped operator taxonomy run has a separate recorded allowance.
                await cur.execute("""SELECT count(*)::int AS total,
                  count(*) FILTER (WHERE NOT (c.kind='taxonomy' AND EXISTS(
                    SELECT 1 FROM contribution_events x JOIN contribution_events a
                      ON a.contribution_id=x.contribution_id
                    WHERE x.contribution_id=c.id AND x.actor_id='operator:owner-source-maintenance'
                      AND x.action='owner_maintenance_quota_exemption'
                      AND x.detail->>'owner_id'=c.author_id
                      AND a.actor_id='operator:owner-source-maintenance'
                      AND a.action='operator_taxonomy_authorization'
                      AND a.detail->>'owner_id'=c.author_id
                      AND a.detail->>'run_id'=x.detail->>'run_id')))::int AS ordinary
                  FROM bank_contributions c WHERE c.created_at>now()-interval '1 day'
                  AND c.author_id=(SELECT id FROM users WHERE lower(email)='hruaitluangasailo20@gmail.com')""")
                usage=await cur.fetchone()
                result['total_contributions_last24h']=usage['total']
                result['ordinary_used']=usage['ordinary']
                result['ordinary_staff_limit']=500
                result['ordinary_staff_remaining']=max(0,500-usage['ordinary'])
                await cur.execute("SELECT count(*) AS n FROM bank_publications WHERE state='exported'")
                result['pending_exports']=(await cur.fetchone())['n']
                return result
            if data['operation']=='reconcile':
                from app.services.review_policy import Proposal
                proposal=Proposal.model_validate(data['proposal']);key='operator-source:'+digest(proposal.model_dump(mode='json'))
                await cur.execute("""SELECT p.id,p.state,p.contribution_id FROM bank_contributions c
                  JOIN users u ON u.id=c.author_id JOIN bank_publications p ON p.contribution_id=c.id AND p.revision=c.revision
                  WHERE lower(u.email)=lower(%s) AND c.idempotency_key=%s""",('hruaitluangasailo20@gmail.com',key))
                return {'publications':await cur.fetchall()}
            if data['operation']=='status':
                await cur.execute('SELECT id,state,error FROM bank_publications WHERE id=%s',(data['publication_id'],));pub=await cur.fetchone()
                snap=await review.snapshot(cur,data['canonical_id'],data['appearance_id'])
                return {'publication':pub,'snapshot':snap}
            if data['operation']=='source':
                snap=await review.snapshot(cur,data['canonical_id'],data['appearance_id'])
                eligible=True
                try:await _validate_explanation_target(cur,snap)
                except Exception:eligible=False
                await cur.execute("SELECT explanation,(answer_source IN ('official','key') OR EXISTS(SELECT 1 FROM v_reviewed_answer_publications rp WHERE rp.canonical_id=q.id)) AS supported FROM canonical_questions q WHERE id=%s",(data['canonical_id'],));canonical=await cur.fetchone()
                eligible=eligible and canonical['supported'] and not (snap['record'].get('explanation')or'').strip() and not (canonical['explanation']or'').strip()
                return {'snapshot':snap,'fingerprint':digest(snap),'eligible':bool(eligible)}
            if data['operation']!='export':raise ValueError('Unknown read operation')
            collection=data.get('collection_id','combined-prelims')
            if collection not in ('udc','combined-prelims'):raise ValueError('Unsupported collection')
            limit=data.get('limit',5000)
            if type(limit)is not int or not 1<=limit<=5000:raise ValueError('Limit must be 1–5000')
            await cur.execute("""SELECT q.id,a.id AS appearance_id,p.year FROM canonical_questions q
              JOIN LATERAL (SELECT a.* FROM appearances a
                JOIN collection_papers cp ON cp.paper_id=a.paper_id
                JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version
                WHERE a.canonical_id=q.id AND cp.collection_id=%s AND c.visibility='public'
                ORDER BY a.is_primary DESC,a.id LIMIT 1) a ON true
              JOIN papers p ON p.id=a.paper_id
              WHERE q.status='live' AND NOT q.key_disputed
                AND COALESCE(q.source_defect,'') NOT IN ('duplicate-options','unresolved-source')
                AND (q.answer_source IN ('official','key') OR q.answer_source='derived' AND EXISTS(SELECT 1 FROM v_reviewed_answer_publications rp WHERE rp.canonical_id=q.id)) AND q.answer_text IS NOT NULL
                AND btrim(COALESCE(q.explanation,''))='' AND btrim(COALESCE(a.explanation,''))=''
                AND a.page IS NOT NULL
              ORDER BY p.year NULLS FIRST,q.id LIMIT %s""",(collection,limit))
            candidates=await cur.fetchall();items=[]
            rank=await ranking(cur,collection)
            hot=await hot_picks(cur,collection)
            hot_ids=[p['taxonomy_id'] for p in hot]
            for row in candidates:
                snap=await review.snapshot(cur,row['id'],row['appearance_id'])
                try:await _validate_explanation_target(cur,snap)
                except Exception:continue
                if not snap['record']['classification']['subject_id']:continue
                await cur.execute("SELECT * FROM review_documents WHERE paper_id=%s AND kind='paper' ORDER BY id LIMIT 1",(snap['paper']['id'],));doc=await cur.fetchone()
                if not doc:continue
                g=rank['groups'].get(row['id']);score=rank['scores'].get(g,{});path=snap['record']['classification']
                items.append({'canonical_id':row['id'],'appearance_id':row['appearance_id'],'snapshot':snap,
                  'fingerprint':digest(snap),'document':doc,'popular_score':score.get('score',0) if score.get('participants',0)>=5 else 0,
                  'hot':bool(set(v for v in path.values() if v)&set(hot_ids)),'year':row['year']})
            return {'collection_id':collection,'items':items,'exported_candidates':len(candidates),'eligible':len(items)}
    finally:await close_pool()

if __name__=='__main__':
    pid=subprocess.check_output(['systemctl','show','ism-api','--property=MainPID','--value'],text=True).strip()
    env=dict(x.split(b'=',1) for x in Path('/proc/'+pid+'/environ').read_bytes().split(b'\0') if b'=' in x)
    os.environ['DATABASE_URL']=env[b'DATABASE_URL'].decode()
    for k in (b'PGPASSWORD',b'PGSSLMODE',b'PGPASSFILE'):
        if k in env:os.environ[k.decode()]=env[k].decode()
    if urlsplit(os.environ.get('DATABASE_URL','')).path!='/mpsc':raise SystemExit('Expected Oracle production read connection')
    print(json.dumps(asyncio.run(run(json.load(sys.stdin))),default=str))
