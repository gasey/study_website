#!/usr/bin/env python3
"""Emit CSVs from mpsc_bank_v2.json for psql \\copy. Stdlib only."""
import json, csv, sys, os

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
d = json.load(open(src))

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
             "year","month","kind","source_file","pdf_path","sitting_id"],
  ([p.get("id"), p.get("examType"), p.get("examName"), p.get("post"), p.get("paperNumber"),
    p.get("paperSubject"), p.get("year"), p.get("month"), p.get("kind"),
    p.get("sourceFile"), p.get("pdfPath"),
    p.get("sittingId") if p.get("sittingId") in sit else None]
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
        q.get("question"), json.dumps(opts, ensure_ascii=False),
        ai, q.get("answerSource"), q.get("answerKeyRef"),
        q.get("subject"), q.get("topic"), q.get("topicLabel"), q.get("difficulty"),
        q.get("explanation"), q.get("marks"),
        bool(q.get("hasDiagram")), bool(q.get("usedVision")),
        q.get("figureGroupId") if q.get("figureGroupId") in fg else None,
        q.get("figureImage"), q.get("passage"),
        q.get("passageId") if q.get("passageId") in pg else None,
        q.get("essayKind"),
    ]

w("questions", ["id","paper_id","type","qnum","qnum_seq","page","question","options",
                "answer_index","answer_source","answer_key_ref","subject","topic",
                "topic_label","difficulty","explanation","marks","has_diagram",
                "used_vision","figure_group_id","figure_image","passage","passage_id",
                "essay_kind"],
  (qrow(q) for q in d.get("questions", [])))
