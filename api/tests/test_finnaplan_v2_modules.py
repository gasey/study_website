"""FINNAPLAN v2 P1/P4/D1 tests: data-driven module flags, single selector, facets, and D1 policy."""
import ast
from pathlib import Path
from uuid import uuid4
from psycopg.types.json import Jsonb
from app.services.browse_allowance import power_filter

APP_ROOT = Path(__file__).resolve().parents[1] / "app"
FORBIDDEN_EXAM_IDS = {"udc", "ldc", "assistant", "combined-prelims", "subject-wise-practice"}


def test_no_exam_id_literals_in_browse_conditionals():
    """FINNAPLAN v2 §3.4 guard: exam identity is data, never code branches."""
    targets = [
        APP_ROOT / "routers/questions.py",
        APP_ROOT / "routers/collections.py",
        APP_ROOT / "services/learning_taxonomy.py",
    ]
    violations = []
    for path in targets:
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value in FORBIDDEN_EXAM_IDS:
                    violations.append(f"{path.name}:{node.lineno}: {node.value!r}")
    assert not violations, "Hardcoded exam IDs found in browse path:\n" + "\n".join(violations)


def test_d1_module_filters_are_free_and_raw_bank_meters():
    """FINNAPLAN v2 D1: published module filters are free; raw /bank ad-hoc combos meter."""
    # Inside a published module, combining topic + year + answer pool is FREE
    assert power_filter({
        "collection_id": "udc",
        "topic_id": "english/vocabulary",
        "year_from": 2020,
        "pool": "practice",
    }) is False
    assert power_filter({
        "collection_id": "subject-english",
        "topic_id": "english/grammar",
        "year_to": 2024,
        "answer_status": "official",
    }) is False
    # Raw /bank (no collection_id) still meters 2+ categories
    assert power_filter({
        "topic_id": "english/vocabulary",
        "year_from": 2020,
    }) is True
    assert power_filter({
        "year_from": 2020,
        "source": ["official"],
    }) is True
    # Cross-exam `exam_scope=all` with subject still meters
    assert power_filter({
        "exam_scope": "all",
        "subject_id": "english",
    }) is True


def test_series_grouping_flag_controls_duplicate_collapse_from_data(client, database):
    """P1: collections.series_grouping=true collapses series printings; false does not."""
    conn = database[1]
    suffix = uuid4().hex[:8]
    cid = f"mod-series-{suffix}"
    sub_cid = f"subject-series-{suffix}"
    subj = f"subj-series-{suffix}"
    p_a = f"synth-{suffix}-2024-Series-A.pdf"
    p_b = f"synth-{suffix}-2024-Series-B.pdf"
    q_a = f"q-series-a-{suffix}"
    q_b = f"q-series-b-{suffix}"
    stem = f"Synthetic identical stem across series {suffix}"
    opts = Jsonb(["Alpha", "Beta", "Gamma", "Delta"])

    conn.execute(
        "INSERT INTO collections(id,title,kind,route,visibility,live_version,exam_scope_id,series_grouping) "
        "VALUES(%s,'Synthetic Series Module','exam',%s,'public',1,'mizoram-recruitment',false)",
        (cid, f"/exams/{cid}"),
    )
    conn.execute(
        "INSERT INTO collections(id,title,kind,route,visibility,live_version,exam_scope_id,series_grouping) "
        "VALUES(%s,'Synthetic Subject Series','practice',%s,'public',1,'mizoram-recruitment',true)",
        (sub_cid, f"/subjects/{sub_cid}"),
    )
    for pid in (p_a, p_b):
        conn.execute(
            "INSERT INTO papers(id,exam_type,exam_name,year,paper_number,exam_scope_id) "
            "VALUES(%s,'Direct','Synthetic Series Exam',2024,'Paper I','mizoram-recruitment')",
            (pid,),
        )
        conn.execute(
            "INSERT INTO collection_papers(collection_id,version,paper_id,section_path,as_mock,allow_browse) "
            "VALUES(%s,1,%s,'papers',false,true)",
            (cid, pid),
        )
    conn.execute(
        "INSERT INTO collection_sections(collection_id,version,path,title,position,formats,query,pins,excludes) "
        "VALUES(%s,1,'papers','Papers',0,'{}',%s,'{}','{}')",
        (cid, Jsonb({"paper_ids": [p_a, p_b]})),
    )
    conn.execute(
        "INSERT INTO collection_sections(collection_id,version,path,title,position,formats,query,pins,excludes) "
        "VALUES(%s,1,'all','All',0,'{}',%s,'{}','{}')",
        (sub_cid, Jsonb({"subject_id": subj})),
    )
    for qid, pid, series in [(q_a, p_a, "A"), (q_b, p_b, "B")]:
        conn.execute(
            "INSERT INTO canonical_questions(id,type,question,options,answer_source,first_year,last_year) "
            "VALUES(%s,'mcq',%s,%s,'none',2024,2024)",
            (qid, stem, opts),
        )
        conn.execute(
            "INSERT INTO appearances(id,paper_id,type,question,options,canonical_id,is_primary,qnum,page,series) "
            "VALUES(%s,%s,'mcq',%s,%s,%s,true,'1',1,%s)",
            (qid, pid, stem, opts, qid, series),
        )
        conn.execute(
            "INSERT INTO question_classifications(question_id,subject_id,subject_label,taxonomy_version,source,review_status) "
            "VALUES(%s,%s,'Synthetic Subject','test','manual','approved')",
            (qid, subj),
        )

    uncollapsed = client.get(f"/api/questions?collection_id={cid}&pool=all")
    assert uncollapsed.status_code == 200
    assert uncollapsed.json()["total"] == 2

    conn.execute("UPDATE collections SET series_grouping = true WHERE id = %s", (cid,))
    collapsed = client.get(f"/api/questions?collection_id={cid}&pool=all")
    assert collapsed.status_code == 200
    assert collapsed.json()["total"] == 1

    # Taxonomy-only subject module also collapses series printings across exams!
    sub_collapsed = client.get(f"/api/questions?collection_id={sub_cid}&pool=all")
    assert sub_collapsed.status_code == 200
    assert sub_collapsed.json()["total"] == 1


def test_taxonomy_subject_module_and_facets_endpoint(client, database):
    """P3/P4: taxonomy-only subject module resolves questions, study-topics, and /api/questions/facets."""
    conn = database[1]
    suffix = uuid4().hex[:8]
    cid = f"subject-synth-{suffix}"
    subj = f"synth-subj-{suffix}"
    topic = f"{subj}/topic-1"
    p1, p2 = f"p-fac-1-{suffix}", f"p-fac-2-{suffix}"
    q1, q2 = f"q-fac-1-{suffix}", f"q-fac-2-{suffix}"

    conn.execute(
        "INSERT INTO collections(id,title,kind,route,visibility,live_version,exam_scope_id,series_grouping) "
        "VALUES(%s,'Synthetic Subject','practice',%s,'public',1,'mizoram-recruitment',true)",
        (cid, f"/subjects/{cid}"),
    )
    conn.execute(
        "INSERT INTO collection_sections(collection_id,version,path,title,position,formats,query,pins,excludes) "
        "VALUES(%s,1,'all','All questions',0,'{}',%s,'{}','{}')",
        (cid, Jsonb({"subject_id": subj})),
    )
    for pid, yr in [(p1, 2022), (p2, 2024)]:
        conn.execute(
            "INSERT INTO papers(id,exam_type,exam_name,year,exam_scope_id) "
            "VALUES(%s,'Direct','Synthetic Exam',%s,'mizoram-recruitment')",
            (pid, yr),
        )
    for qid, pid, yr in [(q1, p1, 2022), (q2, p2, 2024)]:
        conn.execute(
            "INSERT INTO canonical_questions(id,type,question,options,answer_source,first_year,last_year) "
            "VALUES(%s,'mcq',%s,%s,'none',%s,%s)",
            (qid, f"Question {qid}", Jsonb(["A", "B", "C", "D"]), yr, yr),
        )
        conn.execute(
            "INSERT INTO appearances(id,paper_id,type,question,options,canonical_id,is_primary,qnum,page) "
            "VALUES(%s,%s,'mcq',%s,%s,%s,true,'1',1)",
            (qid, pid, f"Question {qid}", Jsonb(["A", "B", "C", "D"]), qid),
        )
        conn.execute(
            "INSERT INTO question_classifications(question_id,subject_id,subject_label,topic_id,topic_label,taxonomy_version,source,review_status) "
            "VALUES(%s,%s,'Synthetic Subject',%s,'Topic One','test','manual','approved')",
            (qid, subj, topic),
        )

    # Module browse total matches raw subject_id filter total
    mod_res = client.get(f"/api/questions?collection_id={cid}&pool=all")
    raw_res = client.get(f"/api/questions?subject_id={subj}&pool=all")
    assert mod_res.status_code == 200 and raw_res.status_code == 200
    assert mod_res.json()["total"] == 2
    assert mod_res.json()["total"] == raw_res.json()["total"]

    # Collection detail & study-topics work for taxonomy-only modules
    detail = client.get(f"/api/collections/{cid}")
    assert detail.status_code == 200 and detail.json()["questions"] == 2
    st = client.get(f"/api/collections/{cid}/study-topics")
    assert st.status_code == 200 and st.json()["questions"] == 2
    assert st.json()["subjects"][0]["id"] == subj
    assert st.json()["subjects"][0]["topics"][0]["id"] == topic

    # Unified /api/questions/facets returns subjects + year histogram in one call
    facets = client.get(f"/api/questions/facets?collection_id={cid}&pool=all")
    assert facets.status_code == 200
    body = facets.json()
    assert body["total"] == 2
    assert body["subjects"][0]["id"] == subj
    assert body["years"] == [{"year": 2024, "questions": 1}, {"year": 2022, "questions": 1}]
