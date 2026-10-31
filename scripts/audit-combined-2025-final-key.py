#!/usr/bin/env python3
"""Read-only bank/key comparison. Prepared payloads never submit, approve or publish."""

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
from app.services.review_policy import Proposal, digest, validate_target


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def audit(bank_path, key_path, transcription, out):
    bank = json.loads(bank_path.read_text())
    source = json.loads(transcription.read_text())
    if sha(key_path) != source["sourceSha256"]:
        raise ValueError("Key PDF differs from the inspected transcription")
    key = {}
    for page in source["pages"]:
        ident = (page["paper"], page["series"])
        if ident in key or len(page["rows"]) != 4:
            raise ValueError("Duplicate or incomplete key page")
        if any(len(row.split()) != 25 for row in page["rows"]):
            raise ValueError("Each source column must have exactly 25 cells")
        cells = " ".join(page["rows"]).split()
        if set(cells) - set("ABCDX"):
            raise ValueError("Unsupported key cell; never infer an OCR replacement")
        key[ident] = (page["page"], cells)
    if set(key) != {(p, s) for p in ["I", "II"] for s in "ABCD"}:
        raise ValueError("All eight paper/series tables are required")
    out.mkdir(parents=True, exist_ok=True)
    missing = [
        q
        for q in bank["questions"]
        if q["type"] == "mcq"
        and not (
            type(q.get("answerIndex")) is int
            and 0 <= q["answerIndex"] < len(q.get("options") or [])
        )
    ]
    papers = {p["id"]: p for p in bank["papers"]}
    comparisons, flagged = [], []
    pattern = r"MCS Combined 2025 Preliminary Exam Paper-(II|I) Series-([A-D])\.\.pdf$"
    for q in bank["questions"]:
        match = re.search(pattern, q["paperId"])
        if not match:
            continue
        page, cells = key[match.groups()]
        n = q.get("qnum")
        if type(n) is not int or not 1 <= n <= 100:
            raise ValueError("Unverified question numbering: " + q["id"])
        cell = cells[n - 1]
        target = None if cell == "X" else "ABCD".index(cell)
        state = (
            "compensated"
            if target is None
            else "agrees" if target == q.get("answerIndex") else "answer_difference"
        )
        row = {
            "appearanceId": q["id"],
            "paperId": q["paperId"],
            "printedQuestion": n,
            "series": match[2],
            "keyPage": page,
            "keyCell": cell,
            "bankAnswerIndex": q.get("answerIndex"),
            "bankAnswerSource": q.get("answerSource"),
            "comparison": state,
        }
        comparisons.append(row)
        if state != "agrees":
            flagged.append((q, row))
    # These source-page corrections and the equation were verified on page renders,
    # separately from the mechanical number/cell comparison.
    page_fixes = {"63980b4a9756b90957ef": 15, "f943e1fbab8eeb0ebff1": 7}
    equation_id = "f943e1fbab8eeb0ebff1"
    claims = []
    source_root = bank_path.parent.parent
    for q, row in flagged:
        paper = papers[q["paperId"]]
        printed_page = page_fixes.get(q["id"], q["page"])
        target = None if row["keyCell"] == "X" else "ABCD".index(row["keyCell"])
        key_id = (
            "key_"
            + hashlib.sha256(
                (q["paperId"] + "|" + source["sourceSha256"]).encode()
            ).hexdigest()[:24]
        )
        paper_id = "doc_" + hashlib.sha256(q["paperId"].encode()).hexdigest()[:24]
        paper_sha = sha(source_root / paper["pdfPath"])
        locator = f"Paper {row['paperId'].split('Paper-')[1].split(' Series')[0]}, booklet {row['series']}, Q{q['qnum']}; final key page {row['keyPage']} dated 20 August 2025."
        rationale = (
            locator
            + " The cell says Compensated, not an answer letter. The provisional option must not be treated as the final correct option. Preserve the printed question in paper view and exclude it from ordinary option-based scoring pending reviewed publication."
            if target is None
            else locator
            + f" The final cell is {row['keyCell']}, corresponding to {q['options'][target]!r}, not the current bank choice. Stem, printed number and ordered choices were checked against the source page."
        )
        if q["id"] == equation_id:
            rationale += " The source expression is 5^(2x + 1) ÷ 25 = 125, so 2x + 1 - 2 = 3 and x = 2. The bank expression is corrupted and the PDF locator is one page early; companion transcription/locator proposals must be rebased after any answer publication."
        evidence = [
            {
                "kind": "paper",
                "document_id": paper_id,
                "sha256": paper_sha,
                "page": printed_page,
                "note": "Printed stem, question number and ordered options inspected; PDF page, not printed footer page.",
            },
            {
                "kind": "reference" if target is None else "official-key",
                "document_id": key_id,
                "sha256": source["sourceSha256"],
                "page": row["keyPage"],
                "url": source["sourceUrl"],
                "printed_question": str(q["qnum"]),
                "series": q.get("series"),
                "answer_text": (
                    "Compensated" if target is None else q["options"][target]
                ),
                "note": locator
                + " Booklet is explicitly verified from the paper/key headings; legacy appearance.series is null, retained in the payload to match the existing review contract.",
            },
            {"kind": "reasoning", "note": rationale},
        ]
        cid = "cq_" + hashlib.md5(q["id"].encode()).hexdigest()[:16]
        claim = {
            **row,
            "canonicalId": cid,
            "question": q["question"],
            "options": q["options"],
            "bankPaperId": q["paperId"],
            "pdfPage": printed_page,
            "baselineSha256": digest(q),
            "optionsSha256": digest(q["options"]),
            "sourcePdfSha256": paper_sha,
            "currentBankAnswerIndex": q.get("answerIndex"),
            "currentBankAnswerSource": q.get("answerSource"),
            "outcome": "source_defect" if target is None else "propose_answer",
            "reviewStatus": "prepared_independent_review_required",
            "rationale": rationale,
            "proposedAnswerIndex": target,
            "supportedAnswerIndex": target,
            "sources": [{"url": source["sourceUrl"], "note": locator}],
            "proposals": [],
        }
        subject = next(
            c["subject_id"] for c in q["classifications"] if c.get("is_primary")
        )
        changes = (
            [
                (
                    "defect",
                    {"sourceDefect": "unresolved-source", "disputeNote": rationale},
                )
            ]
            if target is None
            else [
                (
                    "answer",
                    {
                        "answerIndex": target,
                        "answerSource": "official",
                        "answerKeyRef": key_path.name,
                        "explanation": rationale,
                    },
                )
            ]
        )
        if q["id"] in page_fixes:
            changes.append(("source_reference", {"page": printed_page}))
        if q["id"] == equation_id:
            changes.append(
                (
                    "transcription",
                    {
                        "question": "If 5^(2x + 1) ÷ 25 = 125, find the value of x:",
                        "answerIndex": target,
                        "explanation": rationale,
                    },
                )
            )
        for kind, patch in changes:
            proposal = Proposal(
                kind=kind,
                canonical_id=cid,
                appearance_id=q["id"],
                subject_id=subject,
                title=("Final-key review: " + q["question"])[:200],
                patch=patch,
                rationale=rationale,
                evidence=[
                    (
                        {**e, "kind": "reference"}
                        if kind == "source_reference" and e["kind"] == "official-key"
                        else e
                    )
                    for e in evidence
                ],
            )
            validate_target(proposal, q)
            payload = proposal.model_dump(mode="json")
            prepared = {
                "id": "map_" + digest(payload)[:32],
                "payload": payload,
                "payloadSha256": digest(payload),
                "status": "prepared_not_submitted",
            }
            claim["proposals"].append(prepared)
            (out / "proposals").mkdir(exist_ok=True)
            write_json(out / "proposals" / (prepared["id"] + ".json"), payload)
        claims.append(claim)
    summary = {
        "totalQuestions": len(bank["questions"]),
        "mcqs": sum(q["type"] == "mcq" for q in bank["questions"]),
        "missingMcqAnswerIndexes": len(missing),
        "missingIndexValues": dict(Counter(str(q.get("answerIndex")) for q in missing)),
        "missingOptionsCounts": dict(
            Counter(len(q.get("options") or []) for q in missing)
        ),
        "descriptiveQuestions": sum(
            q["type"] == "descriptive" for q in bank["questions"]
        ),
        "keyCellsTranscribed": 800,
        "compensatedKeyCells": sum(cells.count("X") for _, cells in key.values()),
        "existingAppearancesCompared": len(comparisons),
        "comparisons": dict(Counter(r["comparison"] for r in comparisons)),
        "preparedProposals": sum(len(r["proposals"]) for r in claims),
        "visuallyVerifiedFlaggedAppearances": len(claims),
    }
    packet = {
        "schemaVersion": 1,
        "created": "2026-10-23",
        "bankSha256AtReview": sha(bank_path),
        "sourceKeySha256": sha(key_path),
        "transcriptionSha256": sha(transcription),
        "policy": "Number/cell comparisons are not blanket answer verification. Only flagged printed appearances were visually mapped. Prepared payloads require registered evidence, live baseline recheck and independent review. No bank or account mutation. Multiple proposals for one target must be rebased after each publication.",
        "summary": summary,
        "claims": claims,
        "held": [],
    }
    packet["packetSha256"] = digest(packet)
    write_json(out / "review-packet.json", packet)
    write_json(out / "summary.json", summary)
    for filename, rows in [
        ("comparison.csv", comparisons),
        (
            "missing-mcq-queue.csv",
            [
                {
                    "appearanceId": q["id"],
                    "paperId": q["paperId"],
                    "qnum": q.get("qnum"),
                    "page": q.get("page"),
                    "optionsCount": len(q.get("options") or []),
                    "answerIndex": q.get("answerIndex"),
                    "question": q["question"],
                }
                for q in missing
            ],
        ),
    ]:
        with (out / filename).open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else [])
            writer.writeheader()
            writer.writerows(rows)
    return summary


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--bank",
        type=Path,
        default=ROOT.parent / "mpsc-question-bankv2/bank/mpsc_bank_v2.json",
    )
    p.add_argument(
        "--key",
        type=Path,
        default=ROOT.parent
        / "mpsc-question-bankv2/pdfs/Answer_Keys/MCS Combined Prelim 2025 Final Answer Key 20 August 2025.pdf",
    )
    p.add_argument(
        "--transcription",
        type=Path,
        default=ROOT / "reports/bank-final-key-20261023/key-transcription.json",
    )
    p.add_argument(
        "--output", type=Path, default=ROOT / "reports/bank-final-key-20261023"
    )
    args = p.parse_args()
    print(
        json.dumps(
            audit(args.bank, args.key, args.transcription, args.output), indent=2
        )
    )
