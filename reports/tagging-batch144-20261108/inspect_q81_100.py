import json

p = json.load(open("reports/tagging-batch144-20261108/oracle-packet.json"))

for item in p["items"]:
    snap = item["snapshot"]
    a = item["appearance"]
    rec = snap["record"]
    qnum = a["qnum"]
    print(f"Q{qnum}: {rec['question'][:60]} | opts={rec.get('options')}")
