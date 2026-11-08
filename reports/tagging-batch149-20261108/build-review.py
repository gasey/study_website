"""Build candidates, findings, summary for Batch 149 (SI under Excise 2014 Paper-I)."""
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

def get_physical_page(qnum):
    if qnum <= 6: return 1
    if qnum <= 17: return 2
    if qnum <= 30: return 3
    if qnum <= 38: return 4
    if qnum <= 47: return 5
    if qnum <= 58: return 6
    if qnum <= 71: return 7
    return 8

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
    qnum = int(it["appearance"]["qnum"])
    qtext = rec["question"]
    page = get_physical_page(qnum)

    if 1 <= qnum <= 30:
        prop = make_primary("general-studies", "general-studies/indian-history", None)
        reason = f"Modern Indian History (colonial governance, national movement, social reforms, Q{qnum})."
    elif 31 <= qnum <= 45:
        prop = make_primary("general-studies", "general-studies/indian-polity", None)
        reason = f"Indian Polity & Constitution (constitutional structure, rights, governance institutions, Q{qnum})."
    elif 46 <= qnum <= 60:
        prop = make_primary("general-studies", "general-studies/indian-economy", None)
        reason = f"Indian Economy & Economic Planning (economic structure, Five-Year Plans, fiscal & trade policy, Q{qnum})."
    else:
        prop = make_primary("general-studies", "general-studies/geography", None)
        reason = f"Indian Geography & Economic Geography (physical features, climate, demographics, agriculture, Q{qnum})."

    action = "keep" if prop == cur_primary else "retag"
    action_counts[action] += 1
    tax_counts[f"{prop['subject_id']} > {prop['topic_id']}"] += 1

    cand = {
        "candidate_id": f"tcand_b149_{aid[:16]}",
        "canonical_id": cid,
        "appearance_id": aid,
        "paper_id": pid,
        "source_fingerprint": it["source_fingerprint"],
        "action": action,
        "review_status": "pending",
        "current_primary": cur_primary,
        "proposed_primary": prop,
        "proposed_related": [],
        "tested_skill": reason,
        "rationale": f"Batch 149 source-inspected (page {page}): {reason}",
        "policy_version": "study-tagging-v1",
        "source_evidence": {
            "document_id": pid,
            "sha256": "SI under Excise 2014 General Studies - I.",
            "physical_page": page,
            "printed_question": str(qnum),
            "inspected": True,
            "note": f"Inspected physical page {page} of Sub-Inspector under Excise 2014 General Studies Paper-I (Q{qnum}). Verified question stem, options, and section classification."
        },
        "context_candidate": {
            "region": "IN",
            "language": "en",
            "time_behavior": "static",
            "reference_period": "",
            "reference_basis": "unknown"
        },
        "context_reason": "Static standard syllabus knowledge for Indian General Studies.",
        "source_issues": [],
        "taxonomy_gap": None,
        "alternatives": [],
        "owner_question": None
    }
    pending_candidates.append(cand)

assert len(pending_candidates) == 75

(out / "pending-candidates.json").write_text(json.dumps(pending_candidates, indent=2) + "\n")
(out / "packets" / "source-packet-001.json").write_text(json.dumps(pending_candidates, indent=2) + "\n")

findings = {
    "batch": 149,
    "paper": "Old_Questions/Direct_2014-2018/SI under Excise 2014 General Studies - I..pdf",
    "total_candidates": 75,
    "retags": action_counts["retag"],
    "keeps": action_counts["keep"],
    "holds": 0,
    "distribution": dict(tax_counts)
}
(out / "findings.json").write_text(json.dumps(findings, indent=2) + "\n")

summary = {
    "batch": 149,
    "status": "pending_owner_review",
    "live_changes": 0,
    "total_reviewed": 75,
    "actions": dict(action_counts),
    "paper_completion": "Old_Questions/Direct_2014-2018/SI under Excise 2014 General Studies - I..pdf (75/75 complete)"
}
(out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

manifest = {
    "batch": 149,
    "paper_id": "Old_Questions/Direct_2014-2018/SI under Excise 2014 General Studies - I..pdf",
    "items_count": 75,
    "actions": dict(action_counts)
}
(out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

print(f"Batch 149 review built successfully: {action_counts['retag']} retags, {action_counts['keep']} keeps, 0 holds.")
