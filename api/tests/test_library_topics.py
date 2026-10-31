"""Isolated coverage for multi-path discovery and the real review/export contract."""

import csv, json, subprocess, sys
from pathlib import Path
from uuid import uuid4
import pytest
from psycopg.types.json import Jsonb
from review_bank_store import record, apply_manifest, digest, sha
from app.services.review_policy import Proposal

ROOT = Path(__file__).resolve().parents[2]


def nodes(conn):
    conn.execute(
        "INSERT INTO review_taxonomy(id,label,level,version,parent_id) VALUES ('general-studies','General Studies','subject','test',NULL),('general-studies/geography','Geography','topic','test','general-studies') ON CONFLICT(id) DO NOTHING"
    )


def question(conn, primary="english", related=True):
    nodes(conn)
    qid = "cq_lib_" + uuid4().hex[:10]
    aid = "a_" + qid
    opts = Jsonb(["A", "B", "C", "D"])
    conn.execute(
        "INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES (%s,'mcq','A synthetic library river question',%s,'B','derived')",
        (qid, opts),
    )
    conn.execute(
        "INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary,qnum,page) VALUES (%s,'paper-test','mcq','A synthetic library river question',%s,1,'derived',%s,true,'501',1)",
        (aid, opts, qid),
    )
    conn.execute(
        "INSERT INTO question_classifications(question_id,subject_id,subject_label,taxonomy_version,source,review_status,topic_id,topic_label) VALUES (%s,%s,%s,'test','manual','approved',%s,%s)",
        (
            qid,
            primary,
            "English" if primary == "english" else "General Studies",
            None if primary == "english" else "general-studies/geography",
            None if primary == "english" else "Geography",
        ),
    )
    if related:
        conn.execute(
            "INSERT INTO question_topic_links VALUES (%s,'general-studies/geography','general-studies','General Studies','general-studies/geography','Geography',NULL,NULL,'test','manual','approved','Synthetic reviewed link')",
            (qid,),
        )
    return qid, aid


def test_shelf_filters_secondary_paths_counts_and_origin(client, actor, database):
    conn = database[1]
    qid, aid = question(conn)
    actor("author")
    r = client.get(
        "/api/questions",
        params={"shelf_id": "geography", "pool": "all", "q": "synthetic library river"},
    )
    assert r.status_code == 200, r.text
    assert qid in [q["id"] for q in r.json()["items"]]
    item = next(q for q in r.json()["items"] if q["id"] == qid)
    assert len(item["taxonomy_paths"]) == 2 and "answer_text" not in item
    assert (
        client.get(
            "/api/questions", params={"subject_id": "general-studies", "pool": "all"}
        ).json()["total"]
        >= 1
    )
    assert qid in [
        q["id"]
        for q in client.get(
            "/api/questions", params={"topic_id": "general-studies/geography"}
        ).json()["items"]
    ]
    # Another valid path on the same subject must never duplicate the question.
    conn.execute(
        "INSERT INTO question_topic_links VALUES (%s,'general-studies','general-studies','General Studies',NULL,NULL,NULL,NULL,'test','manual','approved','Synthetic broad link')",
        (qid,),
    )
    found = client.get(
        "/api/questions",
        params={"shelf_id": "geography", "q": "synthetic library river"},
    ).json()
    assert sum(q["id"] == qid for q in found["items"]) == 1
    shelves = client.get("/api/library/shelves").json()
    assert next(s for s in shelves if s["id"] == "geography")["questions"] >= 1
    assert client.get("/api/library/shelves/geography").status_code == 200
    assert client.get("/api/library/shelves/not-real").status_code == 404
    facets = client.get("/api/questions/taxonomy").json()
    gs = next(f for f in facets if f["subject_id"] == "general-studies")
    assert gs["subject_questions"] >= 1
    assert (
        client.get(
            "/api/questions",
            params={
                "shelf_id": "geography",
                "origin": "community",
                "q": "synthetic library river",
            },
        ).json()["total"]
        == 0
    )
    # A pending related claim is stored but does not drive learner filters/search.
    conn.execute(
        "UPDATE question_topic_links SET review_status='pending' WHERE question_id=%s",
        (qid,),
    )
    assert qid not in [
        q["id"]
        for q in client.get(
            "/api/questions",
            params={"shelf_id": "geography", "q": "synthetic library river"},
        ).json()["items"]
    ]


def test_subject_progress_uses_whole_account_and_private_exam_filter(
    client, actor, database
):
    conn = database[1]
    qid, _ = question(conn)
    actor("author")
    cid = "lib_exam_" + uuid4().hex[:8]
    conn.execute(
        "INSERT INTO collections(id,title,kind,visibility,live_version) VALUES (%s,'Synthetic hidden exam','exam','hidden',1)",
        (cid,),
    )
    conn.execute(
        "INSERT INTO collection_papers(collection_id,version,paper_id) VALUES (%s,1,'paper-test')",
        (cid,),
    )
    conn.execute(
        "INSERT INTO attempts(user_id,canonical_id,chosen_text,correct,context,collection_id) VALUES ('author',%s,'A',false,'practice',%s)",
        (qid, cid),
    )
    params = {
        "shelf_id": "geography",
        "study_status": "wrong",
        "q": "synthetic library river",
    }
    assert qid in [
        q["id"] for q in client.get("/api/questions", params=params).json()["items"]
    ]
    assert qid not in [
        q["id"]
        for q in client.get(
            "/api/questions", params={**params, "study_status": "unseen"}
        ).json()["items"]
    ]
    assert (
        client.get("/api/questions", params={**params, "collection_id": cid}).json()[
            "total"
        ]
        == 0
    )
    assert cid not in [
        e["id"] for e in client.get("/api/library/shelves/geography").json()["exams"]
    ]
    actor("outsider")
    assert qid in [
        q["id"]
        for q in client.get(
            "/api/questions", params={**params, "study_status": "unseen"}
        ).json()["items"]
    ]


def test_multi_subject_review_scope_and_manifest(client, actor, database):
    conn = database[1]
    qid, aid = question(conn, related=False)
    body = {
        "kind": "taxonomy",
        "canonical_id": qid,
        "appearance_id": aid,
        "subject_id": "english",
        "title": "Add a related geography topic",
        "patch": {
            "classification": {
                "subject_id": "english",
                "topic_id": None,
                "subtopic_id": None,
            },
            "relatedClassifications": [
                {
                    "subject_id": "general-studies",
                    "topic_id": "general-studies/geography",
                    "subtopic_id": None,
                }
            ],
        },
        "rationale": "The question concerns rivers and should also be found in Geography.",
        "evidence": [
            {
                "kind": "reasoning",
                "note": "Synthetic river question used only for isolated review testing.",
            }
        ],
    }
    h = actor("author")
    h["Idempotency-Key"] = uuid4().hex
    r = client.post("/api/contributions", headers=h, json=body)
    assert r.status_code == 201, r.text
    c = r.json()
    cid = c["id"]
    r = client.post(
        "/api/contributions/" + cid + "/submit",
        headers=h,
        json={"expected_version": c["lock_version"]},
    )
    assert r.status_code == 200, r.text
    c = r.json()
    h = actor("reviewer1")
    r = client.post(
        "/api/review/" + cid + "/decisions",
        headers=h,
        json={
            "expected_version": c["lock_version"],
            "decision": "approve",
            "reason": "Reviewed the question and both requested subject paths.",
        },
    )
    assert r.status_code == 403, r.text
    h = actor("owner")
    r = client.post(
        "/api/review/" + cid + "/decisions",
        headers=h,
        json={
            "expected_version": c["lock_version"],
            "decision": "approve",
            "reason": "Independently checked the question and both paths.",
        },
    )
    assert r.status_code == 200, r.text
    c = r.json()
    assert c["state"] == "accepted"
    r = client.post(
        "/api/admin/bank/contributions/" + cid + "/publish",
        headers=h,
        json={"expected_version": c["lock_version"]},
    )
    assert r.status_code == 200, r.text
    manifest = conn.execute(
        "SELECT manifest FROM bank_publications WHERE id=%s", (r.json()["id"],)
    ).fetchone()[0]
    assert {"english", "general-studies", "general-studies/geography"} <= {
        n["id"] for n in manifest["taxonomy"]
    }
    # Published API work remains a proposal until the local bank worker applies it.
    assert (
        conn.execute(
            "SELECT count(*) FROM question_topic_links WHERE question_id=%s", (qid,)
        ).fetchone()[0]
        == 0
    )
    bad = {
        **body,
        "patch": {
            **body["patch"],
            "relatedClassifications": [
                {"subject_id": "english", "topic_id": "general-studies/geography"}
            ],
        },
    }
    h = actor("author")
    h["Idempotency-Key"] = uuid4().hex
    assert client.post("/api/contributions", headers=h, json=bad).status_code == 422


def test_bank_publication_related_links_csv_and_reversal(tmp_path):
    q = {
        "id": "a_synthetic",
        "paperId": "p_synthetic",
        "type": "mcq",
        "question": "Which synthetic river is shown?",
        "options": ["A", "B"],
        "answerIndex": 1,
        "answerSource": "derived",
        "hasDiagram": False,
        "classifications": [
            {
                "subject_id": "english",
                "topic_id": None,
                "subtopic_id": None,
                "is_primary": True,
                "source": "manual",
                "review_status": "approved",
                "taxonomy_version": "test",
            }
        ],
    }
    bank = {"papers": [], "questions": [q]}
    path = tmp_path / "bank.json"
    path.write_text(json.dumps(bank))
    taxonomy = [
        {"id": "english", "parent_id": None, "level": "subject", "version": "test"},
        {
            "id": "general-studies",
            "parent_id": None,
            "level": "subject",
            "version": "test",
        },
        {
            "id": "general-studies/geography",
            "parent_id": "general-studies",
            "level": "topic",
            "version": "test",
        },
    ]
    manifest = {
        "schema": 1,
        "id": "pub_libtest",
        "contribution_id": "con_libtest",
        "author_id": "synthetic",
        "bank_sha256": sha(path),
        "documents": [],
        "taxonomy": taxonomy,
        "payload": {
            "kind": "taxonomy",
            "patch": {
                "relatedClassifications": [
                    {
                        "subject_id": "general-studies",
                        "topic_id": "general-studies/geography",
                        "subtopic_id": None,
                    }
                ]
            },
            "evidence": [],
        },
        "baseline": {"record": record(q)},
    }
    receipt = apply_manifest(path, tmp_path, manifest, digest(manifest))
    assert receipt["before_fields"]["relatedClassifications"] == []
    assert (
        receipt["after"]["relatedClassifications"][0]["topic_id"]
        == "general-studies/geography"
    )
    assert apply_manifest(path, tmp_path, manifest, digest(manifest)) == receipt
    csvdir = tmp_path / "csv"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/bank_to_csv.py"), str(path), str(csvdir)],
        check=True,
        capture_output=True,
    )
    rows = list(csv.DictReader((csvdir / "question_topic_links.csv").open()))
    assert (
        len(rows) == 1
        and rows[0]["review_status"] == "approved"
        and rows[0]["path_id"] == "general-studies/geography"
    )
    # No secondary claims leak into the single primary CSV.
    primary = list(csv.DictReader((csvdir / "question_classifications.csv").open()))
    assert len(primary) == 1 and primary[0]["subject_id"] == "english"
    manifest = {
        **manifest,
        "id": "pub_librevert",
        "bank_sha256": sha(path),
        "baseline": {"record": receipt["after"]},
        "payload": {
            "kind": "taxonomy",
            "patch": {"relatedClassifications": []},
            "evidence": [],
        },
    }
    reverted = apply_manifest(path, tmp_path, manifest, digest(manifest))
    assert "relatedClassifications" not in reverted["after"]


def test_database_map_owner_only_and_no_private_rows(client, actor):
    actor("author")
    assert client.get("/api/admin/bank/database-map").status_code == 403
    actor("owner")
    r = client.get("/api/admin/bank/database-map")
    assert r.status_code == 200, r.text
    d = r.json()
    assert any(t["id"] == "question_topic_links" for t in d["tables"])
    assert "author@example.test" not in r.text and "password" not in r.text


def test_shelf_notes_and_discussions_keep_existing_audiences(client, actor, database):
    from test_content_studio import document, publish

    conn = database[1]
    qid, _ = question(conn)
    doc = document("paid-preview")
    doc["title"] = "Synthetic Geography tagged preview"
    doc["tags"] = ["Geography"]
    mid = publish(client, actor, doc)
    actor("outsider")
    r = client.get("/api/materials?shelf_id=geography")
    assert r.status_code == 200, r.text
    assert (
        mid in [m["id"] for m in r.json()["items"]]
        and "PRIVATE_BODY_MARKER" not in r.text
    )
    assert mid not in [
        m["id"] for m in client.get("/api/materials?shelf_id=history").json()["items"]
    ]
    pid = conn.execute(
        "INSERT INTO posts(canonical_id,author_id,kind,body) VALUES (%s,'author','doubt','Synthetic river question doubt needing a source explanation') RETURNING id",
        (qid,),
    ).fetchone()[0]
    # New filtering preserves the answer/disclosure gate.
    assert pid not in [
        p["id"]
        for p in client.get(
            "/api/community/feed?tab=questions&shelf_id=geography"
        ).json()["items"]
    ]
    conn.execute(
        "INSERT INTO attempts(user_id,canonical_id,chosen_text,correct,context) VALUES ('outsider',%s,'B',true,'practice')",
        (qid,),
    )
    r = client.get("/api/community/feed?tab=questions&shelf_id=geography")
    assert r.status_code == 200, r.text
    assert pid in [p["id"] for p in r.json()["items"]]
    assert pid not in [
        p["id"]
        for p in client.get(
            "/api/community/feed?tab=questions&shelf_id=history"
        ).json()["items"]
    ]
    conn.execute(
        "INSERT INTO creator_blocks(user_id,blocked_id) VALUES ('outsider','author')"
    )
    assert mid not in [
        m["id"] for m in client.get("/api/materials?shelf_id=geography").json()["items"]
    ]
    assert pid not in [
        p["id"]
        for p in client.get(
            "/api/community/feed?tab=questions&shelf_id=geography"
        ).json()["items"]
    ]
    conn.execute(
        "DELETE FROM creator_blocks WHERE user_id='outsider' AND blocked_id='author'"
    )


def test_actual_sync_sql_imports_and_removes_links_atomically(client,actor,database,tmp_path):
    conn=database[1];qid,aid=question(conn,related=False)
    bank={'papers':[],'questions':[{'id':aid,'paperId':'paper-test','type':'mcq','question':'Synthetic sync river question','options':['A','B'],'answerIndex':1,'classifications':[],'relatedClassifications':[{'subject_id':'general-studies','topic_id':'general-studies/geography','subtopic_id':None,'source':'manual','taxonomy_version':'test','review_status':'approved','evidence':'Reviewed synthetic link for actual SQL import.'}]}]}
    bankfile=tmp_path/'bank.json';bankfile.write_text(json.dumps(bank));csvdir=tmp_path/'csv'
    subprocess.run([sys.executable,str(ROOT/'scripts/bank_to_csv.py'),str(bankfile),str(csvdir)],check=True,capture_output=True)
    csvfile=csvdir/'question_topic_links.csv'
    script=(ROOT/'scripts/sync-bank.sh').read_text()
    start=script.index('CREATE TEMP TABLE s_links')
    end=script.index('SELECT review_status,COUNT',start)
    block=script[start:end]
    pre,rest=block.split('\\copy s_links',1)
    post=rest.split('\n',1)[1]
    before=conn.execute("SELECT count(*) FROM attempts").fetchone()[0]
    def sync(data):
        with conn.transaction():
            conn.execute(pre)
            with conn.cursor().copy('COPY s_links FROM STDIN WITH (FORMAT CSV,HEADER TRUE)') as cp:cp.write(data)
            conn.execute(post)
    sync(csvfile.read_text())
    assert conn.execute('SELECT path_id FROM question_topic_links WHERE question_id=%s',(qid,)).fetchone()[0]=='general-studies/geography'
    actor('author')
    assert qid in [q['id'] for q in client.get('/api/questions?shelf_id=geography').json()['items']]
    # Failure cannot partly remove approved links.
    invalid=csvfile.read_text().replace(aid,'appearance_missing')
    with pytest.raises(Exception,match='Related link target missing'):sync(invalid)
    assert conn.execute('SELECT count(*) FROM question_topic_links WHERE question_id=%s',(qid,)).fetchone()[0]==1
    sync(csvfile.read_text().splitlines()[0]+'\n')
    assert conn.execute('SELECT count(*) FROM question_topic_links').fetchone()[0]==0
    assert conn.execute('SELECT count(*) FROM attempts').fetchone()[0]==before


def test_shelf_year_matches_a_real_printing_not_first_last_interval(client,actor,database):
    conn=database[1];qid,_=question(conn)
    conn.execute('UPDATE canonical_questions SET first_year=2000,last_year=2020 WHERE id=%s',(qid,))
    actor('author')
    a=client.get('/api/questions',params={'shelf_id':'geography','year_from':2010,'year_to':2010}).json()
    assert qid not in [q['id'] for q in a['items']]
    b=client.get('/api/questions',params={'shelf_id':'geography','year_from':2020,'year_to':2020}).json()
    found=next(q for q in b['items'] if q['id']==qid)
    assert found['source_appearance']['year']==2020


def test_exam_stats_count_related_paths_once_and_respect_exclusions(client,actor,database):
    conn=database[1];qid,_=question(conn,related=False)
    conn.execute("UPDATE canonical_questions SET answer_source='official' WHERE id=%s",(qid,))
    cid='lib_stats_'+uuid4().hex[:8]
    conn.execute("INSERT INTO collections(id,title,kind,visibility,live_version) VALUES (%s,'Synthetic topic stats','practice','public',1)",(cid,))
    for position,path in enumerate(['topic','paper']):
        query={'subject_id':'general-studies'}
        if path=='paper':query['paper_ids']=['paper-test']
        conn.execute("INSERT INTO collection_sections(collection_id,version,path,title,position,query) VALUES (%s,1,%s,%s,%s,%s)",(cid,path,path,position,Jsonb(query)))
    actor('author')
    before={s['path']:s for s in client.get('/api/collections/'+cid).json()['section_list']}
    for path,topic in [('general-studies',None),('general-studies/geography','general-studies/geography')]:
        conn.execute("INSERT INTO question_topic_links VALUES (%s,%s,'general-studies','General Studies',%s,%s,NULL,NULL,'test','manual','approved','Synthetic overlap for collection stats')",(qid,path,topic,'Geography' if topic else None))
    r=client.get('/api/collections/'+cid);assert r.status_code==200,r.text
    after={s['path']:s for s in r.json()['section_list']}
    for path in before:
        assert after[path]['questions']==before[path]['questions']+1
        assert after[path]['scorable']==before[path]['scorable']+1
    conn.execute('UPDATE collection_sections SET excludes=%s WHERE collection_id=%s',([qid],cid))
    after=client.get('/api/collections/'+cid).json()['section_list']
    assert all(s['questions']==before[s['path']]['questions'] for s in after)


def test_existing_related_paths_do_not_expand_answer_reviewer_scope(client,actor,database):
    from test_bank_review import proposal
    qid,aid=question(database[1])
    body=proposal();body['canonical_id']=qid;body['appearance_id']=aid
    h=actor('author');h['Idempotency-Key']=uuid4().hex
    r=client.post('/api/contributions',headers=h,json=body);assert r.status_code==201,r.text;c=r.json();cid=c['id']
    r=client.post('/api/contributions/'+cid+'/submit',headers=h,json={'expected_version':c['lock_version']});assert r.status_code==200,r.text;c=r.json()
    for reviewer in ['reviewer1','reviewer2']:
        h=actor(reviewer)
        r=client.post('/api/review/'+cid+'/decisions',headers=h,json={'expected_version':c['lock_version'],'decision':'approve','reason':'Independently reviewed the English answer; related tags are unchanged.'})
        assert r.status_code==200,r.text;c=r.json()
    assert c['state']=='accepted'


def test_empty_or_reordered_related_paths_are_not_rewardable_changes():
    from app.services.review_policy import validate_target
    body={'kind':'taxonomy','canonical_id':'cq_synthetic','subject_id':'english','title':'Synthetic related topic edit','patch':{'relatedClassifications':[]},'rationale':'A synthetic test of meaningful contribution validation.','evidence':[{'kind':'reasoning','note':'Synthetic topic identity evidence only.'}]}
    with pytest.raises(ValueError,match='no change'):validate_target(Proposal.model_validate(body),{'classification':{'subject_id':'english'}})
    paths=[{'subject_id':'mizo','topic_id':None,'subtopic_id':None},{'subject_id':'general-studies','topic_id':None,'subtopic_id':None}]
    body['patch']['relatedClassifications']=paths
    with pytest.raises(ValueError,match='no change'):validate_target(Proposal.model_validate(body),{'relatedClassifications':list(reversed(paths))})

    body['patch']={'classification':{'subject_id':'english'}}
    with pytest.raises(ValueError,match='no change'):validate_target(Proposal.model_validate(body),{'classification':{'subject_id':'english','topic_id':None,'subtopic_id':None}})
