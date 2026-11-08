import json

p = json.load(open("reports/tagging-batch143-20261108/oracle-packet.json"))
print("Papers:", len(p["papers"]))
for paper in p["papers"]:
    docs = [d for d in p["documents"] if d["paper_id"] == paper["id"]]
    print(f"Paper: {paper['id']} -> docs: {len(docs)}")
    if not docs:
        print("  PDF path/url in paper record:", paper.get("pdf_path"), paper.get("pdf_url"), paper.get("source_file"))
