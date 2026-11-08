import json

p = json.load(open("reports/tagging-batch144-20261108/oracle-packet.json"))

for t in p["taxonomy"]:
    tid = t["id"].lower()
    lbl = t["label"].lower()
    if any(k in tid or k in lbl for k in ["aptitude", "reason", "math", "arith", "mental"]):
        print(f"id={t['id']} | label={t['label']} | parent={t['parent_id']} | level={t['level']}")
