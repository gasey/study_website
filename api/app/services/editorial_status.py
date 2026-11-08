"""Reuse attributed inspections of an exact appearance, without copying checks."""
from collections import defaultdict
from .editorial_access import source_versions, inspection_fingerprints, changed_aspects
from .review_policy import digest


def resolve(checks, token, fingerprints, resolutions=(), question_type='mcq'):
    fp = digest(fingerprints) if fingerprints else None
    dismissed = {r['check_id'] for r in resolutions if r['fingerprint'] == fp}
    unresolved = [c for c in checks if c['outcome'] != 'checked' and c['id'] not in dismissed]
    required = ['source_checked', 'explanation_checked'] + (['options_checked', 'answer_checked'] if question_type == 'mcq' else [])
    positives = [c for c in checks if c['outcome'] == 'checked' and all((c.get('checklist') or {}).get(k) is True for k in required)]
    current = next((c for c in positives if not changed_aspects(c, token, fingerprints)), None)
    previous = unresolved[0] if unresolved else current or (checks[0] if checks else None)
    if not previous:
        return {'checked': False, 'stale': False, 'previous_check': None, 'unresolved_checks': []}
    changed = changed_aspects(previous, token, fingerprints)
    summary = {k: previous.get(k) for k in ('id','outcome','created_at','reviewer_id','reviewer','assignment_id','origin_scope')}
    summary.update(stale=bool(changed), changed_aspects=changed)
    return {'checked': bool(current and not unresolved), 'stale': bool(not current and changed),
            'previous_check': summary, 'unresolved_checks': [{k:c.get(k) for k in ('id','outcome','reviewer','created_at','note')} for c in unresolved]}


async def statuses(cur, rows):
    """Rows contain exact id/canonical_id/paper_id/type; only permitted rows enter."""
    if not rows:
        return {}
    ids = [r['id'] for r in rows]
    papers = sorted({r['paper_id'] for r in rows})
    qids = sorted({r['canonical_id'] for r in rows})
    await cur.execute('''SELECT h.*,u.handle AS reviewer FROM editorial_checks h
      LEFT JOIN users u ON u.id=h.reviewer_id WHERE h.appearance_id=ANY(%s) ORDER BY h.id DESC''', (ids,))
    checks = defaultdict(list)
    for c in await cur.fetchall(): checks[c['appearance_id']].append(c)
    inspected = list(checks)
    versions = await source_versions(cur, papers) if inspected else {}
    fingerprints = await inspection_fingerprints(cur, papers, inspected) if inspected else {}
    await cur.execute('''SELECT r.*,h.appearance_id FROM editorial_check_resolutions r JOIN editorial_checks h ON h.id=r.check_id
      WHERE h.appearance_id=ANY(%s)''', (ids,))
    resolutions = defaultdict(list)
    for r in await cur.fetchall(): resolutions[r['appearance_id']].append(r)
    await cur.execute('''SELECT canonical_id,count(*)::int AS count FROM content_reports
      WHERE canonical_id=ANY(%s) AND status IN ('open','confirmed') GROUP BY canonical_id''', (qids,))
    reports = {r['canonical_id']:r['count'] for r in await cur.fetchall()}
    await cur.execute('''SELECT canonical_id,state,count(*)::int AS count FROM bank_contributions
      WHERE canonical_id=ANY(%s) AND state IN ('submitted','in_review','accepted','publishing','publication_failed','published')
      GROUP BY canonical_id,state''', (qids,))
    corrections = defaultdict(lambda: {'pending':0,'published':0,'failed':0})
    for c in await cur.fetchall():
        corrections[c['canonical_id']]['published' if c['state']=='published' else 'failed' if c['state']=='publication_failed' else 'pending'] += c['count']
    result = {}
    for row in rows:
        sid,qid = row['id'],row['canonical_id']
        s = resolve(checks[sid], versions.get(sid), fingerprints.get(sid), resolutions[sid], row['type'])
        s.update(reports=reports.get(qid,0), corrections=corrections[qid],
                 held=bool(row.get('canonical_status') not in (None,'live') or row.get('key_disputed') or row.get('source_defect') in ('duplicate-options','unresolved-source')))
        s['flagged'] = bool(s['unresolved_checks'] or s['reports'] or s['held'])
        s['complete'] = s['checked'] and not s['flagged'] and not s['corrections']['pending'] and not s['corrections']['failed']
        result[sid] = s
    return result


def paper_summaries(papers, rows, state, assignment=None, scope=None):
    from ..source_files import source_pdf_url
    by_paper = defaultdict(list)
    for row in rows: by_paper[row['paper_id']].append(row)
    result=[]
    for original in papers:
        p=dict(original); qs=by_paper[p['id']]
        ss=[state[q['id']] for q in qs]
        own=lambda s: bool(s['previous_check'] and (s['previous_check'].get('assignment_id')==assignment if assignment else s['previous_check'].get('origin_scope')==scope))
        corrections={k:0 for k in ('pending','published','failed')}
        for qid in {q['canonical_id'] for q in qs}:
            s=next(state[q['id']] for q in qs if q['canonical_id']==qid)
            for k in corrections:corrections[k]+=s['corrections'][k]
        p.update(questions=len(qs),recorded=sum(bool(s['previous_check']) for s in ss),checked=sum(s['checked'] for s in ss),
                 reused=sum(s['checked'] and not own(s) for s in ss),flagged=sum(s['flagged'] for s in ss),recheck=sum(s['stale'] for s in ss),
                 corrections=corrections,complete=bool(qs and all(s['complete'] for s in ss)),
                 last_activity=max((s['previous_check']['created_at'] for s in ss if s['previous_check']),default=None))
        def priority(pair):
            s=state[pair[1]['id']]
            if assignment:return (0 if s['stale'] else 1 if not s['previous_check'] else 2 if not s['checked'] else 3,pair[0])
            return (0 if s['flagged'] or s['corrections']['failed'] else 1 if s['stale'] else 2 if not s['checked'] else 3,pair[0])
        ordered=sorted(enumerate(qs),key=lambda pair:(state[pair[1]['id']]['complete'],*priority(pair)))
        p['resume']=None
        if ordered:
            position,q=ordered[0];s=state[q['id']]
            if scope and not s['complete']:
                remaining=[r for r in qs if not state[r['id']]['complete']]
                position=next(i for i,r in enumerate(remaining) if r['id']==q['id'])
            p['resume']={'appearance':q['id'],'question':q['canonical_id'],'qnum':q['qnum'],'offset':position//25*25,
                         'reason':'flagged' if s['flagged'] else 'recheck' if s['stale'] else 'recorded' if s['checked'] else 'unreviewed'}
        p['bank']='website' if p.pop('exam_type')=='Community' else 'mpsc'
        p['source_pdf_url']=source_pdf_url(p.pop('source_file'),p.pop('pdf_url'))
        result.append(p)
    return result
