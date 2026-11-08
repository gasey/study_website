import json

p = json.load(open("reports/tagging-batch145-20261108/oracle-packet.json"))

print("=== ACTIVE TAXONOMY FOR MATH / REASONING / STATS ===")
for t in p["taxonomy"]:
    if t["active"] and any(s in t["id"] for s in ["mathematics", "reasoning", "statistics"]):
        print(f"id={t['id']} | parent={t['parent_id']} | level={t['level']}")
