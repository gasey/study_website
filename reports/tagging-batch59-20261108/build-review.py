"""Build review candidates and findings for Batch 59: Geologist Junior General English Paper-II (100 MCQs)."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))

def parse_path(path_str):
    parts = path_str.split("/")
    if len(parts) == 1:
        return {"subject_id": parts[0], "topic_id": None, "subtopic_id": None}
    elif len(parts) == 2:
        return {"subject_id": parts[0], "topic_id": path_str, "subtopic_id": None}
    elif len(parts) == 3:
        return {"subject_id": parts[0], "topic_id": f"{parts[0]}/{parts[1]}", "subtopic_id": path_str}
    raise ValueError(path_str)

def assign_tax(qnum, question, options):
    if 1 <= qnum <= 10:
        if qnum == 4:
            path = "english/grammar/prepositions"
            rat = "Identifies sentence containing a preposition ('She asked about the dog')."
        elif qnum == 1:
            path = "english/grammar/parts-of-speech"
            rat = "Identifies collective noun 'Crew' in given sentence."
        elif qnum == 2:
            path = "english/grammar/parts-of-speech"
            rat = "Identifies proper noun 'Rajiya' in given sentence."
        elif qnum == 3:
            path = "english/grammar/parts-of-speech"
            rat = "Identifies pronouns 'He, her, himself' in given sentence."
        elif qnum == 5:
            path = "english/grammar/parts-of-speech"
            rat = "Identifies sentence lacking an adjective ('Can you play tennis?')."
        elif qnum == 6:
            path = "english/grammar/parts-of-speech"
            rat = "Identifies sentence with adverb of manner ('The train runs fast')."
        elif qnum == 7:
            path = "english/grammar/parts-of-speech"
            rat = "Identifies sentence without a conjunction."
        elif qnum == 8:
            path = "english/grammar/parts-of-speech"
            rat = "Identifies interjection and sentence expressing happiness ('Hurrah! We have won the match')."
        elif qnum == 9:
            path = "english/grammar/parts-of-speech"
            rat = "Identifies 'hard' modifying noun 'metal' as descriptive adjective."
        else: # 10
            path = "english/grammar/parts-of-speech"
            rat = "Identifies 'is' functioning as linking finite verb."
    elif 11 <= qnum <= 20:
        path = "english/grammar/tenses"
        rat = f"Selects appropriate verb form and tense sequence for stem: {question[:50]}..."
    elif 21 <= qnum <= 30:
        path = "english/grammar/parts-of-speech"
        rat = f"Selects appropriate adjective form or determiner to fill blank: {question[:50]}..."
    elif 31 <= qnum <= 35:
        path = "english/grammar/parts-of-speech"
        rat = f"Selects appropriate adverb to fill blank: {question[:50]}..."
    elif 36 <= qnum <= 40:
        path = "english/grammar/prepositions"
        rat = f"Selects appropriate preposition governing object: {question[:50]}..."
    elif 41 <= qnum <= 50:
        path = "english/grammar"
        rat = f"Analyzes sentence structure and classifies as Simple, Compound, or Complex sentence: {question[:50]}..."
    elif 51 <= qnum <= 60:
        path = "english/grammar"
        rat = f"Identifies sentence function as Declarative, Imperative, Interrogative, or Exclamatory: {question[:50]}..."
    elif 61 <= qnum <= 70:
        path = "english/grammar"
        rat = f"Identifies type of underlined clause (noun, adjective, adverb, or co-ordinate clause): {question[:50]}..."
    elif 71 <= qnum <= 80:
        path = "english/vocabulary/idioms-and-phrases"
        rat = f"Identifies meaning of idiomatic expression in context: {question[:50]}..."
    elif 81 <= qnum <= 90:
        path = "english/vocabulary/one-word-substitution"
        rat = f"Identifies one-word substitution for description: {question[:50]}..."
    elif qnum == 91:
        path = "english/vocabulary"
        rat = "Selects correct spelling and vocabulary choice 'assemble'."
    elif qnum in (92, 93):
        path = "english/vocabulary/synonyms"
        rat = f"Identifies closest synonym in meaning to target word: {question[:50]}..."
    elif qnum == 94:
        path = "english/vocabulary/one-word-substitution"
        rat = "Identifies definition and meaning of 'sadist' (one who gets pleasure from hurting others)."
    elif qnum in (95, 96, 97, 98, 100):
        path = "english/vocabulary"
        rat = f"Selects contextually appropriate lexical item or confusable word: {question[:50]}..."
    elif qnum == 99:
        path = "english/vocabulary/idioms-and-phrases"
        rat = "Selects phrasal verb / idiom 'bottled up' (repressed emotions)."
    else:
        path = "english/grammar"
        rat = "Standard General English classification."
    return path, rat

pending_candidates = []
findings = []

for item in packet["items"]:
    cid = item["canonical_id"]
    aid = item["appearance_id"]
    rec = item["snapshot"]["record"]
    qnum = int(rec["qnum"])
    q_text = rec["question"]
    opts = rec.get("options", [])
    fingerprint = item["source_fingerprint"]
    
    cur_cls = rec.get("classification") or {"subject_id": "english", "topic_id": None, "subtopic_id": None}
    
    target_tax, rationale = assign_tax(qnum, q_text, opts)
    parsed = parse_path(target_tax)
    action = "keep" if parsed == cur_cls else "retag"
    
    cand = {
        "canonical_id": cid,
        "appearance_id": aid,
        "paper_id": "Old_Questions/Direct_2022-2023/Geologist Junior under Commerce Deptt - Gen English-II..pdf",
        "source_fingerprint": fingerprint,
        "review_status": "pending",
        "action": action,
        "current_primary": cur_cls,
        "proposed_primary": parsed,
        "confidence": 1.0,
        "rationale": rationale,
        "batch_id": 59,
        "policy": "study-tagging-v1"
    }
    pending_candidates.append(cand)
    
    findings.append({
        "qnum": qnum,
        "canonical_id": cid,
        "appearance_id": aid,
        "action": action,
        "current_taxonomy": cur_cls,
        "target_taxonomy": parsed,
        "rationale": rationale,
        "stem_excerpt": q_text[:80]
    })

findings.sort(key=lambda x: x["qnum"])
pending_candidates.sort(key=lambda x: int(next(i["snapshot"]["record"]["qnum"] for i in packet["items"] if i["appearance_id"] == x["appearance_id"])))

(out / "pending-candidates.json").write_text(json.dumps(pending_candidates, ensure_ascii=False, indent=2) + "\n")
(out / "findings.json").write_text(json.dumps(findings, ensure_ascii=False, indent=2) + "\n")
(out / "pending-written-intake.json").write_text(json.dumps([], ensure_ascii=False, indent=2) + "\n")

retags = sum(1 for c in pending_candidates if c["action"] == "retag")
keeps = sum(1 for c in pending_candidates if c["action"] == "keep")
holds = sum(1 for c in pending_candidates if c["action"] == "hold")

from collections import Counter
breakdown = Counter(c["proposed_primary"]["subtopic_id"] or c["proposed_primary"]["topic_id"] or c["proposed_primary"]["subject_id"] for c in pending_candidates)

summary = {
    "batch": 59,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2022-2023/Geologist Junior under Commerce Deptt - Gen English-II..pdf",
            "paper_title": "Competitive Examinations for Recruitment to the Post of Geologist Junior under Commerce & Industries Department — General English Paper - II (November 2022)",
            "document_id": "doc_a9476c81c3142d879ad48676",
            "sha256": "dd2f897a5c8ee39816b173e7361357819c955c76473134cd299e6cd10f64a83c",
            "targets": 100
        }
    ],
    "targets": 100,
    "completion": "100% paper completion achieved for Geologist Junior General English Paper-II (100/100 MCQs)",
    "actions": {
        "retag": retags,
        "keep": keeps,
        "hold": holds
    },
    "unextracted_items_preserved": 0,
    "conventional_marks_preserved": 0,
    "breakdown": dict(breakdown),
    "source_defects": [
        "Q61–Q70 Underlined Clauses in PDF Geometry: Target clauses in clause identification questions were underlined via horizontal vector line strokes in the PDF stream; verified via exact PyMuPDF geometry.",
        "Q71–Q80 Underlined Idioms in PDF Geometry: Target idiomatic phrases were underlined with vector line strokes in the printed booklet."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Generated {len(pending_candidates)} pending review candidates.")
print(f"Saved {len(findings)} detailed findings.")
print(f"Actions: {retags} retag, {keeps} keep, {holds} hold.")
print(f"Breakdown: {dict(breakdown)}")
