"""Overlapping modules reuse exact evidence, never permissions or source variants."""
from uuid import uuid4
import pytest
from psycopg.types.json import Jsonb
from test_editorial_assignments import source, active


def scope(client, module='udc'):
    r=client.get('/api/editorial/scope',params={'scope':'module:'+module});assert r.status_code==200,r.text
    return r.json()


def payload(client, qid, appearance, module='udc'):
    overview=scope(client,module)
    snap=client.get('/api/review/questions/'+qid,params={'appearance_id':appearance}).json()
    return {'scope':'module:'+module,'scope_revision':overview['scope']['revision'],'appearance_id':appearance,
            'source_version':snap['baseline_token'],'inspection_version':snap['inspection_version'],
            'attestation':'source-review-v1','outcome':'checked','request_key':uuid4().hex}


def test_owner_checks_without_assignment_and_reuses_in_compiled_module(client,actor,source,database):
    pid,qid,aid=source;c=database[1];h=actor('owner')
    version=c.execute("SELECT live_version FROM collections WHERE id='group-b-non-gazetted'").fetchone()[0]
    c.execute("INSERT INTO collection_papers(collection_id,version,paper_id,section_path) VALUES('group-b-non-gazetted',%s,%s,'papers')",(version,pid))
    b=payload(client,qid,aid);r=client.post('/api/editorial/checks',headers=h,json=b);assert r.status_code==200,r.text
    cid=r.json()['id'];assert c.execute('SELECT assignment_id,origin_scope FROM editorial_checks WHERE id=%s',(cid,)).fetchone()==(None,'module:udc')
    before=c.execute('SELECT count(*) FROM editorial_checks').fetchone()[0]
    replay=client.post('/api/editorial/checks',headers=h,json=b);assert replay.status_code==200 and replay.json()['replayed']
    other=scope(client,'group-b-non-gazetted');paper=next(p for p in other['items'] if p['id']==pid)
    assert paper['checked']==paper['reused']==1
    assert c.execute('SELECT count(*) FROM editorial_checks').fetchone()[0]==before
    h=actor('owner');assignment=active(client,actor);actor('outsider')
    p=client.get('/api/editorial/assignments/'+assignment['id']+'/papers').json()['items'];assert next(x for x in p if x['id']==pid)['checked']==1


def test_same_canonical_different_appearance_needs_own_check(client,actor,source,database):
    pid,qid,aid=source;c=database[1];h=actor('owner')
    c.execute("INSERT INTO appearances(id,paper_id,type,question,options,canonical_id,qnum,qnum_seq) VALUES(%s,%s,'mcq','Other printed version',%s,%s,'2',2)",(aid+'-other',pid,Jsonb(['B','A']),qid))
    r=client.post('/api/editorial/checks',headers=h,json=payload(client,qid,aid));assert r.status_code==200,r.text
    p=next(p for p in scope(client)['items'] if p['id']==pid)
    assert p['questions']==2 and p['checked']==1 and not p['complete']


def test_assignment_scope_is_not_expanded_by_parent_and_revocation(client,actor,source,database):
    pid,qid,aid=source;a=active(client,actor);actor('outsider');c=database[1]
    catalog=client.get('/api/editorial/scopes').json()['items'];assert any(x['id']=='assignment:'+a['id'] for x in catalog)
    r=client.get('/api/editorial/scope/questions',params={'scope':'module:udc','paper':'paper-test'})
    assert r.status_code==200 and r.json()['items']==[]
    c.execute("UPDATE editorial_assignments SET state='revoked',version=version+1 WHERE id=%s",(a['id'],))
    assert client.get('/api/editorial/scopes').status_code==403
    assert client.get('/api/editorial/scope',params={'scope':'assignment:'+a['id']}).status_code==404


def test_stale_membership_and_content_and_conflicting_request_rejected(client,actor,source,database):
    pid,qid,aid=source;c=database[1];h=actor('owner');b=payload(client,qid,aid)
    c.execute("UPDATE question_classifications SET topic_id='english-changed' WHERE question_id=%s",(qid,))
    r=client.post('/api/editorial/checks',headers=h,json=b);assert r.status_code==409
    b=payload(client,qid,aid);c.execute("UPDATE appearances SET question='Changed wording' WHERE id=%s",(aid,))
    assert client.post('/api/editorial/checks',headers=h,json=b).status_code==409
    b=payload(client,qid,aid);r=client.post('/api/editorial/checks',headers=h,json=b);assert r.status_code==200,r.text
    assert client.post('/api/editorial/checks',headers=h,json={**b,'note':'different'}).status_code==409


def test_unresolved_inspection_needs_explicit_admin_resolution_and_keeps_history(client,actor,source,database):
    pid,qid,aid=source;c=database[1];h=actor('owner');b=payload(client,qid,aid)
    bad=client.post('/api/editorial/checks',headers=h,json={**b,'outcome':'cannot_verify','reason':'unclear_source'});assert bad.status_code==200,bad.text
    issue_id=bad.json()['id'];good=client.post('/api/editorial/checks',headers=h,json=payload(client,qid,aid));assert good.status_code==200,good.text
    p=next(p for p in scope(client)['items'] if p['id']==pid);assert p['checked']==0 and p['flagged']==1
    b=payload(client,qid,aid);resolved=client.post('/api/editorial/checks',headers=h,json={**b,'resolve_checks':[issue_id],'resolution_reason':'Compared the legible original source page and resolved this scan issue.'});assert resolved.status_code==200,resolved.text
    p=next(p for p in scope(client)['items'] if p['id']==pid);assert p['checked']==1
    assert c.execute('SELECT outcome FROM editorial_checks WHERE id=%s',(issue_id,)).fetchone()[0]=='cannot_verify'
    assert c.execute('SELECT count(*) FROM editorial_check_resolutions WHERE check_id=%s',(issue_id,)).fetchone()[0]==1


def test_reports_and_publication_failures_block_completion_not_source_reuse(client,actor,source,database):
    pid,qid,aid=source;c=database[1];h=actor('owner');r=client.post('/api/editorial/checks',headers=h,json=payload(client,qid,aid));assert r.status_code==200,r.text
    c.execute("INSERT INTO content_reports(canonical_id,kind,reporter_id,note) VALUES(%s,'subject','author','Synthetic wrong-tag report')",(qid,))
    p=next(p for p in scope(client)['items'] if p['id']==pid);assert p['checked']==1 and p['flagged']==1 and not p['complete']


def test_written_checks_have_not_applicable_mcq_flags(client,actor,source,database):
    pid,qid,aid=source;c=database[1];c.execute("UPDATE appearances SET type='descriptive',options='[]',answer_index=NULL WHERE id=%s",(aid,));c.execute("UPDATE canonical_questions SET type='descriptive',options='[]' WHERE id=%s",(qid,))
    h=actor('owner');r=client.post('/api/editorial/checks',headers=h,json=payload(client,qid,aid));assert r.status_code==200,r.text
    flags=c.execute('SELECT checklist FROM editorial_checks WHERE id=%s',(r.json()['id'],)).fetchone()[0]
    assert flags['answer_checked'] is None and flags['options_checked'] is None


def test_scoped_staff_cannot_inspect_without_publishing_or_assignment(client,actor,source):
    h=actor('reviewer1');r=client.post('/api/editorial/checks',headers=h,json=payload(client,source[1],source[2]));assert r.status_code==403,r.text


def test_context_exact_module_membership_no_private_proposals(client,actor,source):
    h=actor('owner');r=client.get('/api/editorial/scope/context',params={'scope':'module:udc','appearance':source[2]});assert r.status_code==200,r.text
    assert any(m['id']=='udc' for m in r.json()['modules'])
    assert 'answerIndex' not in r.text
    assert client.get('/api/editorial/scope/context',params={'scope':'module:udc','appearance':'appearance-test'}).status_code==404


def test_future_versioned_module_with_overlapping_sections_preserves_evidence(client,actor,source,database):
    pid,qid,aid=source;c=database[1];name='future-'+uuid4().hex
    c.execute("INSERT INTO collections(id,title,kind,live_version) VALUES(%s,'Synthetic future compiled exam','exam',1)",(name,))
    for path in ['first','overlap']:
        c.execute("INSERT INTO collection_sections(collection_id,version,path,title,position,query,pins,excludes) VALUES(%s,1,%s,'Synthetic section',0,%s,%s,%s)",(name,path,Jsonb({'paper_ids':[pid]}),[qid],[]))
    h=actor('owner');r=client.post('/api/editorial/checks',headers=h,json=payload(client,qid,aid));assert r.status_code==200,r.text
    view=scope(client,name);assert view['summary']['appearances']==1 and view['summary']['questions']==1 and view['summary']['reused']==1
    c.execute("INSERT INTO collection_sections(collection_id,version,path,title,position,query,pins,excludes) VALUES(%s,2,'new','Synthetic next version',0,%s,%s,%s)",(name,Jsonb({'paper_ids':[pid]}),[qid],[qid]))
    c.execute('UPDATE collections SET live_version=2 WHERE id=%s',(name,))
    assert scope(client,name)['summary']['appearances']==0
    assert next(p for p in scope(client)['items'] if p['id']==pid)['checked']==1


def test_group_b_area_membership_matches_actual_learner_selection(client,actor,database):
    from test_group_b_study import seed
    ids,_,_,_=seed(database[1]);actor('owner')
    for area in ['common','technical']:
        view=scope(client,'group-b-non-gazetted:'+area)
        got=set()
        for paper in view['items']:
            r=client.get('/api/editorial/scope/questions',params={'scope':'module:group-b-non-gazetted:'+area,'paper':paper['id']})
            assert r.status_code==200,r.text
            got.update(q['canonical_id'] for q in r.json()['items'])
        learner=client.get('/api/questions',params={'collection_id':'group-b-non-gazetted','study_area':area,'limit':100})
        assert learner.status_code==200,learner.text
        expected={q['id'] for q in learner.json()['items']}
        assert got & set(ids)==expected & set(ids)


def test_issue_notes_not_leaked_from_paged_lists_and_held_sources_not_complete(client,actor,source,database):
    pid,qid,aid=source;c=database[1];h=actor('owner');body=payload(client,qid,aid)
    r=client.post('/api/editorial/checks',headers=h,json={**body,'outcome':'cannot_verify','reason':'unclear_source','note':'Synthetic private answer-bearing evidence note'});assert r.status_code==200,r.text
    page=client.get('/api/editorial/scope/questions',params={'scope':'module:udc','paper':pid})
    assert 'Synthetic private answer-bearing evidence note' not in page.text
    ctx=client.get('/api/editorial/scope/context',params={'scope':'module:udc','appearance':aid})
    assert 'Synthetic private answer-bearing evidence note' in ctx.text
    c.execute("UPDATE canonical_questions SET status='held' WHERE id=%s",(qid,))
    assert next(p for p in scope(client)['items'] if p['id']==pid)['complete'] is False


def test_continuation_seeks_after_saved_source_across_shrinking_pages(client,actor,source,database):
    pid,qid,aid=source;c=database[1];actor('owner')
    c.execute('UPDATE appearances SET qnum_seq=1 WHERE id=%s',(aid,))
    for n in range(2,28):
        c.execute("INSERT INTO appearances(id,paper_id,type,question,options,canonical_id,qnum,qnum_seq) VALUES(%s,%s,'mcq','Synthetic continuation',%s,%s,%s,%s)",
                  (aid+str(n),pid,Jsonb(['A','B']),qid,str(n),n))
    args={'scope':'module:udc','paper':pid,'queue':'remaining','offset':25,'after':aid+'25'}
    result=client.get('/api/editorial/scope/questions',params=args).json()
    assert result['next']['appearance']==aid+'26' and result['offset']==25
    # Remove saved source from remaining; the next source moves to page one.
    h=actor('owner');body=payload(client,qid,aid+'25')
    assert client.post('/api/editorial/checks',headers=h,json=body).status_code==200
    result=client.get('/api/editorial/scope/questions',params=args).json()
    assert result['next']['appearance']==aid+'26' and result['offset']==0
    assert result['next']['appearance'] in {r['id'] for r in result['items']}
    args['after']=aid+'27'
    result=client.get('/api/editorial/scope/questions',params=args).json()
    assert result['next']['appearance']==aid


def test_continuation_excludes_only_saved_unresolved_source(client,actor,source):
    actor('owner')
    result=client.get('/api/editorial/scope/questions',params={'scope':'module:udc','paper':source[0],'queue':'remaining','after':source[2]}).json()
    assert result['total']==1 and result['next'] is None


def test_module_work_corrections_deduplicate_shared_canonical(client,actor,source,database):
    pid,qid,aid=source;c=database[1];actor('owner')
    c.execute("INSERT INTO appearances(id,paper_id,type,question,options,canonical_id,qnum,qnum_seq) VALUES(%s,%s,'mcq','Shared question',%s,%s,'2',2)",(aid+'copy',pid,Jsonb(['A','B']),qid))
    c.execute("INSERT INTO content_reports(canonical_id,kind,reporter_id,note) VALUES(%s,'subject','author','Synthetic tag report')",(qid,))
    before=scope(client)['work']
    for state in ('submitted','publication_failed'):
        token=uuid4().hex
        c.execute('''INSERT INTO bank_contributions(id,author_id,canonical_id,appearance_id,kind,subject_id,title,state,idempotency_key,request_hash)
          VALUES(%s,'author',%s,%s,'taxonomy','english','Synthetic correction',%s,%s,%s)''',(token,qid,aid,state,token,'a'*64))
    result=scope(client)
    assert result['work']['pending']==before['pending']+1
    assert result['work']['failed']==before['failed']+1
    assert result['work']['reports']>=1
    paper=next(p for p in result['items'] if p['id']==pid)
    assert paper['flagged']==2
    assert result['work']['inspections']==result['summary']['appearances']-result['summary']['checked']


def test_review_page_size_and_continuation(client,actor,source,database):
    pid,qid,aid=source;c=database[1];actor('owner')
    c.execute('UPDATE appearances SET qnum_seq=1 WHERE id=%s',(aid,))
    for n in range(2,103):
        c.execute("INSERT INTO appearances(id,paper_id,type,question,options,canonical_id,qnum,qnum_seq) VALUES(%s,%s,'mcq','Synthetic page size',%s,%s,%s,%s)",(aid+str(n),pid,Jsonb(['A','B']),qid,str(n),n))
    args={'scope':'module:udc','paper':pid,'limit':100}
    first=client.get('/api/editorial/scope/questions',params=args).json()
    assert len(first['items'])==100 and first['total']==102
    last=client.get('/api/editorial/scope/questions',params={**args,'offset':100}).json()
    assert len(last['items'])==2 and last['offset']==100
    seek=client.get('/api/editorial/scope/questions',params={**args,'after':aid+'100'}).json()
    assert seek['offset']==100 and seek['next']['appearance']==aid+'101'
    assert client.get('/api/editorial/scope/questions',params={**args,'limit':101}).status_code==422
