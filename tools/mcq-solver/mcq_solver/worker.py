import json
import random
import uuid

from .adapters.base import Question
from .errors import SolverError
from .prompts import request
from .validate import validate


def run(ledger, bank, inference, config, limit=5, stopping=lambda: False):
    if not 1 <= limit <= 5:
        raise SolverError("limit_exceeds_phase")
    if ledger.pause_reason():
        raise SolverError("queue_paused")
    summary = {"valid_drafts": 0, "flagged": 0, "failed": 0, "paused": 0, "stopped": False}
    run_id = str(uuid.uuid4())
    for _ in range(limit):
        if stopping():
            summary["stopped"] = True
            break
        job = ledger.claim(run_id, config.model, config.reasoning)
        if job is None:
            break
        try:
            question = Question.from_payload(json.loads(job["source"]))
            current = bank.current(job["question_id"])
            if current is None or current.fingerprint != job["question_version_hash"]:
                raise SolverError("stale_source")
            text = inference.respond(request(question, config.model, config.reasoning))
            draft = validate(text, question)
            current = bank.current(job["question_id"])
            if current is None or current.fingerprint != job["question_version_hash"]:
                raise SolverError("stale_source")
            ledger.save_draft(job, draft)
            summary["valid_drafts"] += 1
            summary["flagged"] += int(draft["review_required"])
        except SolverError as exc:
            if exc.code == "stale_source":
                latest = bank.current(job["question_id"])
                if latest:
                    ledger.enqueue(latest, config.model, config.reasoning)
            if exc.pauses:
                ledger.finish(job, "paused", code=exc.code)
                ledger.pause(exc.code)
                summary["paused"] += 1
                break
            delay = max(exc.retry_after, min(300, 2 ** job["attempt_count"] + random.uniform(0, 2)))
            state = "transient_failed" if exc.transient and job["attempt_count"] < 3 else "permanent_failed"
            ledger.finish(job, state, code=exc.code, delay=delay if exc.transient else 0)
            summary["failed"] += 1
            if exc.transient:
                break  # persist backoff; do not hammer a failing provider
        except (KeyboardInterrupt, SystemExit):
            ledger.finish(job, "transient_failed", code="stopped", delay=1)
            summary["stopped"] = True
            break
    return summary
