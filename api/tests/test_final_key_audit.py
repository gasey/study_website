"""Synthetic read-only audit fixtures; no production bank or PDF dependency."""

import importlib.util
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "final_key_audit", ROOT / "scripts/audit-combined-2025-final-key.py"
)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


@pytest.fixture
def sources(tmp_path):
    bank_dir = tmp_path / "bank"
    bank_dir.mkdir()
    paper_dir = tmp_path / "pdfs"
    paper_dir.mkdir()
    pages = []
    for paper in ["I", "II"]:
        for series in "ABCD":
            cells = ["A"] * 100
            if (paper, series) == ("I", "A"):
                cells[0] = "C"
                cells[1] = "C"
                cells[36] = "X"
            if (paper, series) == ("II", "C"):
                cells[40] = "B"
            pages.append(
                {
                    "page": len(pages) + 1,
                    "paper": paper,
                    "series": series,
                    "rows": [" ".join(cells[i : i + 25]) for i in range(0, 100, 25)],
                }
            )
    key = tmp_path / "key.pdf"
    key.write_bytes(b"Synthetic inspected key bytes; not an actual exam document")
    transcription = tmp_path / "transcription.json"
    transcription.write_text(
        json.dumps(
            {
                "sourceSha256": AUDIT.sha(key),
                "sourceUrl": "https://example.test/synthetic-key.pdf",
                "pages": pages,
            }
        )
    )
    papers = []
    for paper, series in [("I", "A"), ("II", "C")]:
        pid = f"Old_Questions/Direct_2025-2027/MCS Combined 2025 Preliminary Exam Paper-{paper} Series-{series}..pdf"
        name = f"synthetic-{paper}-{series}.pdf"
        (paper_dir / name).write_bytes(b"Synthetic printed source")
        papers.append({"id": pid, "pdfPath": "pdfs/" + name})

    def question(qid, n, answer, paper=0):
        return {
            "id": qid,
            "paperId": papers[paper]["id"],
            "type": "mcq",
            "qnum": n,
            "page": 6,
            "question": "Synthetic source question " + qid,
            "options": ["6", "2", "10", "4"],
            "answerIndex": answer,
            "answerSource": "inferred",
            "classifications": [{"subject_id": "arithmetic", "is_primary": True}],
        }

    questions = [
        question("agreement", 1, 2),
        question("difference", 2, 0),
        question("compensated", 37, 2),
        question("f943e1fbab8eeb0ebff1", 41, 0, 1),
    ]
    questions.append({**question("missing", 1, -1), "paperId": "Other synthetic paper"})
    bank = bank_dir / "bank.json"
    bank.write_text(json.dumps({"papers": papers, "questions": questions}))
    return bank, key, transcription


def test_packet_is_read_only_and_payloads_are_bound(tmp_path, sources):
    bank, key, transcription = sources
    before = AUDIT.sha(bank)
    out = tmp_path / "output"
    summary = AUDIT.audit(bank, key, transcription, out)
    assert summary["missingMcqAnswerIndexes"] == 1
    assert summary["comparisons"] == {
        "agrees": 1,
        "compensated": 1,
        "answer_difference": 2,
    }
    assert summary["preparedProposals"] == 5
    packet = json.loads((out / "review-packet.json").read_text())
    for claim in packet["claims"]:
        if claim["comparison"] == "compensated":
            assert claim["proposedAnswerIndex"] is None
            assert (
                claim["proposals"][0]["payload"]["patch"]["sourceDefect"]
                == "unresolved-source"
            )
        for prepared in claim["proposals"]:
            assert prepared["status"] == "prepared_not_submitted"
            assert prepared["payloadSha256"] == AUDIT.digest(prepared["payload"])
    equation = next(
        c for c in packet["claims"] if c["appearanceId"] == "f943e1fbab8eeb0ebff1"
    )
    assert equation["pdfPage"] == 7 and equation["proposedAnswerIndex"] == 1
    assert "5^(2x + 1)" in next(
        p["payload"]["patch"]["question"]
        for p in equation["proposals"]
        if p["payload"]["kind"] == "transcription"
    )
    assert AUDIT.sha(bank) == before


def test_wrong_source_bytes_are_rejected(tmp_path, sources):
    bank, key, transcription = sources
    wrong = tmp_path / "wrong.pdf"
    wrong.write_bytes(b"Synthetic wrong source bytes")
    with pytest.raises(ValueError, match="differs"):
        AUDIT.audit(bank, wrong, transcription, tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_missing_cells_are_not_shifted_or_inferred(tmp_path, sources):
    bank, key, transcription = sources
    source = json.loads(transcription.read_text())
    source["pages"][0]["rows"][0] = "C C"
    path = tmp_path / "broken-transcription.json"
    path.write_text(json.dumps(source))
    with pytest.raises(ValueError, match="25 cells"):
        AUDIT.audit(bank, key, path, tmp_path / "output")
    assert not (tmp_path / "output").exists()
