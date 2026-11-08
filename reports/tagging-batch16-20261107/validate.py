"""Strict readback validation for Batch 16."""
import json, subprocess
from pathlib import Path
from datetime import datetime, timezone

out = Path(__file__).resolve().parent

# 1. Run recheck export
subprocess.run(["python3", str(out / "export-current.py"), "--recheck"], check=True)

# 2. Compare packet with readback
orig = json.load(open(out / "oracle-packet.json"))
readback = json.load(open(out / "oracle-readback.json"))

assert len(orig["items"]) == len(readback["items"]) == 50
for o, r in zip(orig["items"], readback["items"]):
    assert o["canonical_id"] == r["canonical_id"]
    assert o["appearance_id"] == r["appearance_id"]
    assert o["source_fingerprint"] == r["source_fingerprint"]
    assert o["appearance"] == r["appearance"]

# 3. Verify taxonomy paths
tax = {t["id"]: t for t in orig["taxonomy"] if t.get("active")}
candidates = json.load(open(out / "pending-candidates.json"))

for c in candidates:
    p = c["proposed_primary"]
    subj = p["subject_id"]
    top = p["topic_id"]
    subtop = p["subtopic_id"]

    assert subj in tax, f"Invalid subject {subj}"
    assert tax[subj]["level"] == "subject"

    if top:
        assert top in tax, f"Invalid topic {top}"
        assert tax[top]["level"] == "topic"
        assert tax[top]["parent_id"] == subj

    if subtop:
        assert subtop in tax, f"Invalid subtopic {subtop}"
        assert tax[subtop]["level"] == "subtopic"
        assert tax[subtop]["parent_id"] == top

val = {
    "validated_at": datetime.now(timezone.utc).isoformat(),
    "targets_validated": len(candidates),
    "zero_changes_confirmed": True,
    "fingerprints_match": True,
    "taxonomy_nodes_count": len(tax)
}
(out / "validation.json").write_text(json.dumps(val, indent=2) + "\n")
print(json.dumps(val, indent=2))
