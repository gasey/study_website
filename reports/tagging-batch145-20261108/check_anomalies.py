import json

p = json.load(open("reports/tagging-batch145-20261108/oracle-packet.json"))

for item in p["items"]:
    snap = item["snapshot"]
    rec = snap["record"]
    c = rec.get("classification") or {}
    sid = c.get("subject_id")
    if sid not in ["mathematics", "reasoning-and-aptitude", "statistics"]:
        print(f"ANOMALY: {snap['paper']['id']} Q{item['appearance']['qnum']} | {c} | {rec['question'][:80]}")
