"""Build candidates, findings, summary for Batch 144."""
import json
from pathlib import Path
from collections import Counter

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))

def make_primary(sid, tid=None, subid=None):
    return {
        "subject_id": sid,
        "topic_id": tid,
        "subtopic_id": subid
    }

pending_candidates = []
action_counts = Counter()
tax_counts = Counter()

for it in packet["items"]:
    snap = it["snapshot"]
    rec = snap["record"]
    aid = it["appearance_id"]
    cid = it["canonical_id"]
    cur_primary = rec["classification"]
    pid = it["appearance"]["paper_id"]
    pid_short = pid.split("/")[-1]
    qnum_str = str(it["appearance"]["qnum"])
    qtext = rec["question"]

    if qnum_str in ["81", "82", "85"]:
        prop = make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None)
        reason = f"Verbal reasoning and practical deduction (Q{qnum_str}) under reasoning-and-aptitude/verbal-reasoning."
    elif qnum_str == "83":
        prop = make_primary("english", "english/vocabulary", "english/vocabulary/one-word-substitution")
        reason = "Phobia terminology / one-word substitution (Agoraphobia) under english/vocabulary/one-word-substitution."
    elif qnum_str == "84":
        prop = make_primary("english", "english/vocabulary", "english/vocabulary/idioms-and-phrases")
        reason = "Meaning of proverb / idiom under english/vocabulary/idioms-and-phrases."
    elif qnum_str == "86":
        prop = make_primary("mathematics", "mathematics/arithmetic", None)
        reason = "Unitary arithmetic calculation (postcards purchased) under mathematics/arithmetic."
    elif qnum_str == "87":
        prop = make_primary("mathematics", "mathematics/arithmetic", "mathematics/arithmetic/ratio-and-proportion")
        reason = "Direct proportion / speed-distance-time rate calculation under mathematics/arithmetic/ratio-and-proportion."
    elif qnum_str == "88":
        prop = make_primary("mathematics", "mathematics/arithmetic", None)
        reason = "Inverse proportion / unitary time-and-work calculation under mathematics/arithmetic."
    elif qnum_str in ["89", "90", "91", "92", "93", "94"]:
        prop = make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None)
        reason = f"Analogical relationship and concept classification (Q{qnum_str}: '{qtext[:30]}...') under reasoning-and-aptitude/verbal-reasoning."
    elif qnum_str in ["95", "96", "97", "98", "99", "100"]:
        prop = make_primary("english", "english/vocabulary", "english/vocabulary/synonyms")
        reason = f"Vocabulary synonym identification (word '{qtext}') under english/vocabulary/synonyms."
    else:
        raise ValueError(f"Unexpected qnum: {qnum_str}")

    tax_counts[prop["subtopic_id"] or prop["topic_id"]] += 1

    is_same = (
        cur_primary.get("subject_id") == prop["subject_id"] and
        cur_primary.get("topic_id") == prop["topic_id"] and
        cur_primary.get("subtopic_id") == prop["subtopic_id"]
    )
    action = "keep" if is_same else "retag"
    action_counts[action] += 1

    candidate = {
        "candidate_id": f"tcand_b144_{aid[:16]}",
        "canonical_id": cid,
        "appearance_id": aid,
        "paper_id": pid,
        "source_fingerprint": it["source_fingerprint"],
        "action": action,
        "review_status": "pending",
        "current_primary": cur_primary,
        "proposed_primary": prop,
        "proposed_secondary": [],
        "reason": reason,
        "policy": "study-tagging-v1",
        "notes": f"Batch 144 source-reviewed: Mizoram Legal Service 2016 Aptitude & Vocabulary ({pid_short}) Q{qnum_str}."
    }
    pending_candidates.append(candidate)

(out / "pending-candidates.json").write_text(json.dumps(pending_candidates, ensure_ascii=False, indent=2) + "\n")

findings = [
    {
        "id": "finding_b144_mizoram_legal_service_aptitude_intake",
        "paper_id": "Old_Questions/Direct_2014-2018/5.Jr. Administrative Grade and Sr. Grade of Mizoram Legal Service 2016 GK & Aptitute Test (Common).pdf",
        "type": "composite_paper_partitioning",
        "severity": "info",
        "details": "Source-reviewed Questions 81-100 in the composite 2016 Mizoram Legal Service GK & Aptitude booklet: successfully partitioned 9 Verbal Reasoning concept questions, 3 Arithmetic/Unitary math problems, 6 Vocabulary synonyms, 1 One-Word Substitution (Agoraphobia), and 1 Proverb meaning into their respective taxonomy branches."
    },
    {
        "id": "finding_b144_series_permutations_deduplication_ledger",
        "paper_id": "multiple",
        "type": "series_deduplication",
        "severity": "info",
        "details": "Identified and catalogued secondary permutation series booklets that duplicate already-reviewed Series A papers: CAO March-2026 Series B (duplicates Series A from Batch 120), Jr. Accounts Officer Paper-I Series B (duplicates Series A from Batch 114), Jr. Accounts Officer Paper-II Series B (duplicates Series A from Batches 14 & 128), Direct NG General English Series B/C/D (duplicates Series A), and Uploaded Group B Gazetted Series B (duplicates Series A). Under single-booklet deduplication policy, secondary booklets are safely bypassed without double-counting appearances."
    },
    {
        "id": "finding_b144_geology_misnomer_defect_register",
        "paper_id": "Old_Questions/Direct_2019-2020/Geologist Junior General English Paper-III.pdf",
        "type": "ingestion_misnomer",
        "severity": "info",
        "details": "Formally registered defect for 'Geologist Junior General English Paper-III.pdf' (96 items) and 'Geologist Junior General Englsih Paper-III Nov.pdf' (99 items). Visual inspection of source PDFs confirms these are Mining & Geology Paper-III technical exams (structural geology, mineralogy, stratigraphy) erroneously titled 'General English' by source uploaders."
    }
]

(out / "findings.json").write_text(json.dumps(findings, ensure_ascii=False, indent=2) + "\n")

summary = {
    "batch": 144,
    "papers": [
        {
            "paper_id": p["id"],
            "paper_title": p.get("exam_name", p["id"].split("/")[-1]),
            "document_id": next(d["id"] for d in packet["documents"] if d["paper_id"] == p["id"]),
            "sha256": next(d["sha256"] for d in packet["documents"] if d["paper_id"] == p["id"]),
            "targets": sum(1 for it in packet["items"] if it["appearance"]["paper_id"] == p["id"])
        }
        for p in packet["papers"]
    ],
    "targets": 20,
    "completion": "100% section completion achieved for Mizoram Legal Service 2016 Aptitude & English Vocabulary section (20/20 questions reviewed: 9 Verbal Reasoning, 6 Vocabulary Synonyms, 3 Arithmetic & Ratio Problems, 1 One-Word Substitution, 1 Proverb/Idiom; 0 defect drops, single-booklet deduplication & geology misnomer register documented)",
    "actions": {
        "retag": action_counts["retag"],
        "keep": action_counts["keep"],
        "hold": 0
    },
    "breakdown": dict(sorted(tax_counts.items(), key=lambda x: -x[1])),
    "source_defects": [
        "Partitioned composite GK & Aptitude paper: Q81-100 tagged under verbal-reasoning, arithmetic, and english vocabulary.",
        "Documented series permutation deduplications (bypassing secondary Series B/C/D booklets without duplicate mutations).",
        "Registered formal defect for Geologist Junior Paper-III misnomer (geology technical exam titled as general english)."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 144 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
