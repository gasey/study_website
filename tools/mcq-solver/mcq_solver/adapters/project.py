"""Actual mpsc_bank_v2.json format, read-only. No canonical ID inference."""
import json
from pathlib import Path

from .base import Question
from ..errors import SolverError


class RecoveryBank:
    def __init__(self, path: Path, held_ids=()):
        self.path = path.resolve(strict=True)
        self.held_ids = frozenset(held_ids)
        self._load()

    def _load(self):
        try:
            data = json.loads(self.path.read_text())
            self.papers = {p["id"]: p for p in data["papers"]}
            self.rows = {}
            for row in data["questions"]:
                if not isinstance(row.get("id"), str) or not row["id"]:
                    raise SolverError("invalid_question")
                if row["id"] in self.rows:
                    raise SolverError("duplicate_id")
                self.rows[row["id"]] = row
            self.figures = data.get("figureGroups", {})
            self.passages = data.get("passageGroups", {})
        except (ValueError, TypeError, KeyError):
            raise SolverError("invalid_question") from None

    def question(self, row):
        opts = row.get("options")
        if row.get("type") != "mcq" or not isinstance(row.get("question"), str) or not row["question"].strip():
            raise SolverError("invalid_question")
        if not isinstance(opts, list) or not 2 <= len(opts) <= 8 or any(not isinstance(o, str) or not o.strip() for o in opts):
            raise SolverError("invalid_question")
        paper = self.papers.get(row.get("paperId"), {})
        media = {"figure": self.figures.get(row.get("figureGroupId")),
                 "passage": self.passages.get(row.get("passageId"))}
        return Question(row["id"], row, paper, media)

    def pending(self, limit):
        found = []
        for row in self.rows.values():
            if row['id'] in self.held_ids:
                continue
            # AnswerIndex=-1 is the existing unknown sentinel. Zero is valid.
            unknown = row.get("answerIndex") is None or row.get("answerIndex") == -1
            flagged = bool(row.get("key_disputed") or row.get("sourceDefect"))
            if not (unknown or flagged) or row.get("compensated"):
                continue
            try:
                q = self.question(row)
            except SolverError:
                continue
            found.append(q)
            if len(found) == limit:
                break
        return found

    def current(self, question_id):
        if question_id in self.held_ids:
            return None
        self._load()  # re-read immediately before committing the local draft
        row = self.rows.get(question_id)
        if row is None:
            return None
        try:
            return self.question(row)
        except SolverError:
            return None
