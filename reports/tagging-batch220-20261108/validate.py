import json, hashlib
from pathlib import Path

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))
candidates = json.load(open(out / "pending-candidates.json"))
nodes = {n["id"]: n for n in packet["taxonomy"]}

def digest(path):
    return hashlib.sha256(json.dumps(path, sort_keys=True).encode()).hexdigest()

def path_valid(path):
    if not isinstance(path, dict) or set(path) != {"subject_id", "topic_id", "subtopic_id"} or not path["subject_id"]:
        raise ValueError("Use complete subject/topic/subtopic objects")
    if path["subtopic_id"] and not path["topic_id"]:
        raise ValueError("Subtopic requires its parent topic")
    parent = None
    for level in ("subject", "topic", "subtopic"):
        tid = path[level + "_id"]
        if tid is None:
            continue
        n = nodes.get(tid)
        if not n or n.get("active") is False or n["level"] != level or n.get("parent_id") != parent:
            raise ValueError("Invalid active taxonomy path: " + str(tid))
        parent = tid

expected = {(i["canonical_id"], i["appearance_id"]): i for i in packet["items"]}
keys = [(c["canonical_id"], c["appearance_id"]) for c in candidates]
assert len(set(keys)) == len(keys) == len(expected) == 26, "Count mismatch"

for idx, c in enumerate(candidates):
    key = (c["canonical_id"], c["appearance_id"])
    item = expected[key]
    assert c.get("source_fingerprint") == item["source_fingerprint"], f"idx {idx} sf mismatch"
    assert c.get("current_primary") == item["snapshot"]["record"]["classification"], f"idx {idx} cp mismatch"
    assert c.get("policy_version") == "study-tagging-v1", f"idx {idx} pv mismatch"
    assert c.get("review_status") == "pending", f"idx {idx} rs mismatch"
    assert c.get("reviewer_model") and c.get("reviewer_tool"), f"idx {idx} rev mismatch"
    action = c.get("action")
    assert action in ("keep", "retag", "hold"), f"idx {idx} action invalid"
    assert len(c.get("rationale", "").strip()) >= 20, f"idx {idx} rationale short"
    assert c.get("tested_skill"), f"idx {idx} tested_skill missing"
    for f in ("source_issues", "alternatives"):
        assert isinstance(c.get(f), list), f"idx {idx} {f} not list"
    for f in ("taxonomy_gap", "owner_question", "context_reason"):
        assert f in c, f"idx {idx} {f} missing"
    path_valid(c.get("proposed_primary"))
    related = c.get("proposed_related")
    assert isinstance(related, list) and len(related) <= 12
    for p in related:
        path_valid(p)
    paths = [c["proposed_primary"], *related]
    assert len({digest(p) for p in paths}) == len(paths), f"idx {idx} duplicate paths"
    before = item["snapshot"]["record"]
    unchanged = (c["proposed_primary"] == before["classification"] and related == before.get("relatedClassifications", []))
    assert (action == "keep") == unchanged, f"Action keep mismatch for idx {idx} {c['canonical_id']}: {action} vs unchanged={unchanged}"
    ev = c.get("source_evidence") or {}
    assert ev.get("inspected") is True, f"idx {idx} ev inspected"
    assert type(ev.get("physical_page")) is int and ev["physical_page"] >= 1, f"idx {idx} ev page"
    assert len(ev.get("note", "").strip()) >= 20, f"idx {idx} ev note short"
    assert any(d["id"] == ev.get("document_id") and d["sha256"] == ev.get("sha256") for d in packet["documents"]), f"idx {idx} doc bind"
    context = c.get("context_candidate") or {}
    assert context.get("time_behavior") in ("static", "dated-event", "changes-over-time", "unknown"), f"idx {idx} context tb"
    assert context.get("reference_basis") in ("printed", "exam-date", "reviewed-source", "unknown"), f"idx {idx} context rb"
    if any(p["topic_id"] == "general-studies/current-affairs" for p in paths) or context["time_behavior"] in ("dated-event", "changes-over-time"):
        assert context.get("reference_period") and context["reference_basis"] != "unknown", f"idx {idx} context ca"

validation = {
    "batch": 220,
    "valid_count": 26,
    "failed_count": 0,
    "status": "PASS",
    "checks": [
        "100%_target_coverage",
        "exact_oracle_baselines",
        "exact_source_fingerprints",
        "100%_active_paths_and_parents",
        "document_binding_verified",
        "actions_consistent_with_proposals"
    ]
}
(out / "validation.json").write_text(json.dumps(validation, indent=2) + "\n")
print("Validation PASSED for Batch 220 (26/26 items).")
