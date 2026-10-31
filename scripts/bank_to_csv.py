#!/usr/bin/env python3
"""Emit CSVs from mpsc_bank_v2.json for psql \\copy. Stdlib only."""
import json, csv, sys, os

src, out = sys.argv[1], sys.argv[2]
taxonomy_path = sys.argv[3] if len(sys.argv) > 3 else None
os.makedirs(out, exist_ok=True)
d = json.load(open(src))

subjects, topics, subtopics = {}, {}, {}
if taxonomy_path and os.path.isfile(taxonomy_path):
    taxonomy = json.load(open(taxonomy_path))
    for subject in taxonomy.get("subjects", []):
        subjects[subject["id"]] = subject["label"]
        for topic in subject.get("topics", []):
            topics[topic["id"]] = topic["label"]
            for subtopic in topic.get("subtopics", []):
                subtopics[subtopic["id"]] = subtopic["label"]

def w(name, header, rows):
    p = os.path.join(out, name + ".csv")
    with open(p, "w", newline="") as f:
        c = csv.writer(f)
        c.writerow(header)
        n = 0
        for r in rows:
            c.writerow(r); n += 1
    print(f"{name}: {n}")

w("sittings", ["id","exam_name","exam_type","year","month"],
  ([s.get("id"), s.get("examName"), s.get("examType"), s.get("year"), s.get("month")]
   for s in d.get("sittings", {}).values()))

sit = set(d.get("sittings", {}).keys())
w("papers", ["id","exam_type","exam_name","post","paper_number","paper_subject",
             "year","month","kind","source_file","pdf_path","sitting_id","exam_scope_id"],
  ([p.get("id"), p.get("examType"), p.get("examName"), p.get("post"), p.get("paperNumber"),
    p.get("paperSubject"), p.get("year"), p.get("month"), p.get("kind"),
    p.get("sourceFile"), p.get("pdfPath"),
    p.get("sittingId") if p.get("sittingId") in sit else None,p.get("examScopeId")]
   for p in d.get("papers", [])))

papers = {p["id"] for p in d.get("papers", [])}
w("figure_groups", ["id","paper_id","page"],
  ([g.get("id") or k, g.get("paperId") if g.get("paperId") in papers else None, g.get("page")]
   for k, g in d.get("figureGroups", {}).items()))

w("passage_groups", ["id","passage"],
  ([g.get("id") or k, g.get("text")] for k, g in d.get("passageGroups", {}).items()))

fg = set(d.get("figureGroups", {}).keys())
pg = set(d.get("passageGroups", {}).keys())

def qrow(q):
    ai = q.get("answerIndex")
    if ai is not None and ai < 0:      # -1 is a JSON sentinel, not an answer
        ai = None
    opts = q.get("options") or []
    qn = q.get("qnum")
    try:
        seq = int(str(qn))
    except (TypeError, ValueError):
        seq = None
    return [
        q.get("id"), q.get("paperId") if q.get("paperId") in papers else None,
        q.get("type"), qn, seq, q.get("page"),
        q.get("question"), q.get("direction"), q.get("questionMarkup"),
        json.dumps(q["optionsMarkup"], ensure_ascii=False) if q.get("optionsMarkup") is not None else None,
        q.get("sourceContextRef"), json.dumps(opts, ensure_ascii=False),
        ai, q.get("answerSource"), q.get("answerKeyRef"),
        q.get("subject"), q.get("topic"), q.get("topicLabel"), q.get("difficulty"),
        q.get("explanation"), q.get("marks"),
        bool(q.get("hasDiagram")), bool(q.get("usedVision")),
        q.get("figureGroupId") if q.get("figureGroupId") in fg else None,
        q.get("figureImage"), q.get("passage"),
        q.get("passageId") if q.get("passageId") in pg else None,
        q.get("essayKind"),
        json.dumps({k:q[k] for k in ("sourceDefect","disputeNote","reviewPublicationId","origin") if k in q}, ensure_ascii=False),
    ]

w("questions", ["id","paper_id","type","qnum","qnum_seq","page","question","direction",
                "question_markup","options_markup","source_context_ref","options",
                "answer_index","answer_source","answer_key_ref","subject","topic",
                "topic_label","difficulty","explanation","marks","has_diagram",
                "used_vision","figure_group_id","figure_image","passage","passage_id",
                "essay_kind","review_metadata"],
  (qrow(q) for q in d.get("questions", [])))

def classification_rows():
    for q in d.get("questions", []):
        claims = q.get("classifications") or []
        # The merge contract keeps one selected primary path in the bank.
        # Ignore malformed/non-primary entries rather than guessing a winner.
        primary = [c for c in claims if c.get("is_primary") is True]
        if len(primary) != 1:
            continue
        c = primary[0]
        sid, tid, stid = c.get("subject_id"), c.get("topic_id"), c.get("subtopic_id")
        if not sid:
            continue
        yield [
            q.get("id"), sid, subjects.get(sid, sid.replace("-", " ").title()),
            tid, topics.get(tid, tid.rsplit("/", 1)[-1].replace("-", " ").title()) if tid else None,
            stid, subtopics.get(stid, stid.rsplit("/", 1)[-1].replace("-", " ").title()) if stid else None,
            c.get("taxonomy_version"), c.get("source"), c.get("review_status"),
            c.get("confidence"), c.get("evidence"), True,
        ]

w("question_classifications", ["question_id","subject_id","subject_label","topic_id",
                                 "topic_label","subtopic_id","subtopic_label",
                                 "taxonomy_version","source","review_status","confidence",
                                 "evidence","is_primary"], classification_rows())

# Secondary paths are explicit reviewed links, never parked alternative claims.
def related_rows():
    for q in d.get('questions', []):
        seen=set()
        for c in q.get('relatedClassifications') or []:
            sid,tid,stid=c.get('subject_id'),c.get('topic_id'),c.get('subtopic_id')
            path=stid or tid or sid
            if not sid or not path or path in seen:raise ValueError('Invalid/duplicate related taxonomy path for '+q['id'])
            seen.add(path)
            yield [q['id'],path,sid,subjects.get(sid,sid),tid,topics.get(tid,tid),stid,subtopics.get(stid,stid),c.get('taxonomy_version'),c.get('source'),c.get('review_status'),c.get('evidence') or '']
w('question_topic_links',['question_id','path_id','subject_id','subject_label','topic_id','topic_label','subtopic_id','subtopic_label','taxonomy_version','source','review_status','evidence'],related_rows())
