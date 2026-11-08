from pathlib import Path
import json, hashlib, urllib.request, urllib.parse, pymupdf

out = Path(__file__).resolve().parent
p = json.load(open(out / "oracle-packet.json"))
ms = []

for n, paper in enumerate(p["papers"], 1):
    docs = [d for d in p["documents"] if d["paper_id"] == paper["id"]]
    assert len(docs) == 1
    d = docs[0]
    src = out / "sources"
    src.mkdir(exist_ok=True)
    pdf = src / (d["sha256"] + ".pdf")
    url = next(i["snapshot"]["paper"]["source_pdf_url"] for i in p["items"] if i["snapshot"]["paper"]["id"] == paper["id"])
    url = "https://study.hawayu.in" + url if url.startswith("/") else url
    if not pdf.exists():
        urllib.request.urlretrieve(url, pdf)
    actual_hash = hashlib.sha256(pdf.read_bytes()).hexdigest()
    assert actual_hash == d["sha256"], f"Hash mismatch for {pdf}: {actual_hash} != {d['sha256']}"
    
    pages = []
    texts = []
    doc_pdf = pymupdf.open(pdf)
    for j, page in enumerate(doc_pdf, 1):
        img = src / f"paper-{n}-p{j}.png"
        page.get_pixmap(matrix=pymupdf.Matrix(2.0, 2.0)).save(img)
        pages.append(str(img.resolve()))
        texts.append(dict(physical_page=j, text=page.get_text()))
    
    ms.append(dict(
        index=n,
        paper_id=paper["id"],
        exam_name=paper.get("exam_name"),
        document_id=d["id"],
        sha256=d["sha256"],
        pdf=str(pdf.resolve()),
        url=url,
        page_count=len(pages),
        images=pages,
        text_pages=texts
    ))

(out / "manifest.json").write_text(json.dumps(ms, ensure_ascii=False, indent=2) + "\n")
print(f"Prepared sources for {len(ms)} papers.")
for m in ms:
    print(f"Paper {m['index']}: {m['paper_id']} ({m['page_count']} pages, sha256={m['sha256'][:16]}...)")
