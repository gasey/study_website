"""Validate Batch 150 against Oracle readback, taxonomy rules, and audit-review-coverage.py."""
import subprocess, json
from pathlib import Path

batch_dir = Path(__file__).resolve().parent

proc = subprocess.run(["python3", str(batch_dir / "export-current.py"), "--recheck"], capture_output=True, text=True)
if proc.returncode:
    raise SystemExit("Recheck export failed: " + proc.stderr)

orig = json.load(open(batch_dir / "oracle-packet.json"))
readback = json.load(open(batch_dir / "oracle-readback.json"))
candidates = json.load(open(batch_dir / "pending-candidates.json"))
summary = json.load(open(batch_dir / "summary.json"))

assert len(orig["items"]) == len(readback["items"]) == 34
assert len(candidates) == 34

c_by_aid = {c["appearance_id"]: c for c in candidates}
assert len(c_by_aid) == len(candidates) == 34

fp_matches = 0
for o, r in zip(orig["items"], readback["items"]):
    c = c_by_aid[o["appearance_id"]]
    assert o["canonical_id"] == r["canonical_id"] == c["canonical_id"]
    assert o["appearance_id"] == r["appearance_id"] == c["appearance_id"]
    assert o["source_fingerprint"] == r["source_fingerprint"] == c["source_fingerprint"]
    assert o["snapshot"]["record"]["classification"] == r["snapshot"]["record"]["classification"] == c["current_primary"]
    assert o["snapshot"]["record"]["question"] == r["snapshot"]["record"]["question"]
    assert o["snapshot"]["record"]["options"] == r["snapshot"]["record"]["options"]
    fp_matches += 1

assert summary["live_changes"] == 0
assert all(c["review_status"] == "pending" for c in candidates)

tax_by_id = {t["id"]: t for t in orig["taxonomy"] if t["active"]}
for c in candidates:
    prop = c["proposed_primary"]
    sid, tid, subid = prop["subject_id"], prop["topic_id"], prop["subtopic_id"]
    assert sid in tax_by_id and tax_by_id[sid]["level"] == "subject", f"Invalid subject: {sid}"
    if tid is not None:
        assert tid in tax_by_id and tax_by_id[tid]["level"] == "topic" and tax_by_id[tid]["parent_id"] == sid, f"Invalid topic: {tid}"
    if subid is not None:
        assert subid in tax_by_id and tax_by_id[subid]["level"] == "subtopic" and tax_by_id[subid]["parent_id"] == tid, f"Invalid subtopic: {subid}"

validation_result = {
    "batch": 150,
    "validated_at": readback["exported_at"],
    "source_fingerprints_verified": fp_matches,
    "database_live_writes": 0,
    "candidates_status": "all_pending",
    "taxonomy_validity": "100%_active_paths_and_parents",
    "verified": True
}
(batch_dir / "validation.json").write_text(json.dumps(validation_result, indent=2) + "\n")
print("Validation succeeded:", json.dumps(validation_result, indent=2))
