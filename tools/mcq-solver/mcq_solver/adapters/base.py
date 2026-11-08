from dataclasses import dataclass
from typing import Protocol

from ..storage import digest


@dataclass(frozen=True)
class Question:
    id: str
    record: dict
    paper: dict
    media: dict

    @property
    def fingerprint(self) -> str:
        # Include keys, explanations and all source metadata too: a human edit
        # anywhere in this record invalidates old proposals, without leaking it.
        return digest(self.payload())

    def payload(self):
        return {"record": self.record, "paper": self.paper, "media": self.media}

    @classmethod
    def from_payload(cls, value):
        return cls(value["record"]["id"], value["record"], value["paper"], value["media"])

    def blind_input(self):
        r = self.record
        return {"question_id": self.id, "question": r["question"],
                "options": [{"id": str(i), "text": text} for i, text in enumerate(r["options"])],
                "direction": r.get("direction"), "passage": r.get("passage"),
                "question_markup": r.get("questionMarkup"), "options_markup": r.get("optionsMarkup"),
                "subject": r.get("subject"), "topic": r.get("topic"),
                "exam_year": self.paper.get("year", self.paper.get("examYear")),
                "media_supplied": False,
                "media_required": bool(r.get("hasDiagram") or r.get("figureImage") or r.get("figureGroupId"))}


class BankReader(Protocol):
    def pending(self, limit: int) -> list[Question]: ...
    def current(self, question_id: str) -> Question | None: ...


class DraftWriter(Protocol):
    def save_draft(self, job: dict, draft: dict) -> None: ...
