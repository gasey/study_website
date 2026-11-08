import json

p = json.load(open("reports/tagging-batch143-20261108/oracle-packet.json"))

for item in p["items"]:
    snap = item["snapshot"]
    a = item["appearance"]
    rec = snap["record"]
    pid = snap["paper"]["id"]
    print(f"[{pid}] Q{a['qnum']} | cur={rec['classification']} | text={rec['question'][:70]} | options={rec.get('options')}")
