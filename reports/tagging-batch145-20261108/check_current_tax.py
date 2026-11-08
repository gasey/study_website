import json
from collections import Counter

p = json.load(open("reports/tagging-batch145-20261108/oracle-packet.json"))

current_tax = Counter()
for item in p["items"]:
    snap = item["snapshot"]
    rec = snap["record"]
    c = rec.get("classification") or {}
    key = f"{c.get('subject_id')}/{c.get('topic_id')}/{c.get('subtopic_id')}"
    current_tax[key] += 1

print("Current classification breakdown:")
for k, cnt in current_tax.most_common():
    print(f"  {k}: {cnt}")
