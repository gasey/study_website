import json

p = json.load(open("reports/tagging-batch142-20261108/oracle-packet.json"))

print("=== TAXONOMY UNDER ENGLISH ===")
for t in p["taxonomy"]:
    if t["parent_id"] == "english" or t["id"] == "english":
        print(f"id={t['id']} | label={t['label']} | parent={t['parent_id']}")

print("\n=== ITEMS IN BATCH 142 ===")
for item in p["items"]:
    snap = item["snapshot"]
    q = snap.get("canonical_question") or {}
    a = item["appearance"]
    pid = snap["paper"]["id"]
    print(f"[{pid}] qnum={a['qnum']} | subj={a['subject']} | top={a['topic']} | text={a['question'][:60]}")
