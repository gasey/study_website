import json

p = json.load(open("reports/tagging-batch142-20261108/oracle-packet.json"))

for t in p["taxonomy"]:
    if t["parent_id"] and t["parent_id"].startswith("english"):
        print(f"id={t['id']} | parent={t['parent_id']} | label={t['label']}")
