"""Local draft ledger. Contains no publication path or production DB credential."""
import json
from pathlib import Path
import secrets
import sqlite3
import time

from .adapters.base import Question
from .errors import SolverError
from .prompts import VERSION
from .storage import digest, private_dir


class Ledger:
    def __init__(self, root: Path):
        private_dir(root)
        self.path = root / "jobs.sqlite"
        if self.path.is_symlink():
            raise SolverError("unsafe_path")
        self.db = sqlite3.connect(self.path, timeout=10)
        self.path.chmod(0o600)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY, question_id TEXT NOT NULL, question_version_hash TEXT NOT NULL,
            source TEXT NOT NULL, model_id TEXT NOT NULL, reasoning TEXT NOT NULL,
            prompt_version TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
            attempt_count INTEGER NOT NULL DEFAULT 0, started_at REAL, completed_at REAL,
            last_error_code TEXT, lease_token TEXT, lease_deadline REAL,
            next_eligible_at REAL NOT NULL DEFAULT 0, solver_run_id TEXT,
            created_at REAL NOT NULL, updated_at REAL NOT NULL);
          CREATE TABLE IF NOT EXISTS drafts (
            job_id TEXT PRIMARY KEY REFERENCES jobs(id), payload TEXT NOT NULL,
            created_at REAL NOT NULL, human_approval TEXT);
          CREATE TABLE IF NOT EXISTS control (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)

    def close(self):
        self.db.close()

    def enqueue(self, question: Question, model: str, reasoning: str):
        # Reasoning is included to retain audit history if configuration changes.
        key = digest([question.id, question.fingerprint, VERSION, model, reasoning])
        now = time.time()
        with self.db:
            self.db.execute("""INSERT OR IGNORE INTO jobs
                (id,question_id,question_version_hash,source,model_id,reasoning,prompt_version,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?)""", (key, question.id, question.fingerprint, json.dumps(question.payload()), model, reasoning, VERSION, now, now))
        return key

    def pause_reason(self):
        row = self.db.execute("SELECT value FROM control WHERE key='pause'").fetchone()
        return row[0] if row else None

    def pause(self, code):
        code = SolverError(code).code
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO control VALUES('pause',?)", (code,))

    def resume(self):
        # An explicit operator command, not a timer or account switch.
        with self.db:
            self.db.execute("DELETE FROM control WHERE key='pause'")
            self.db.execute("UPDATE jobs SET status='pending',updated_at=? WHERE status='paused' AND attempt_count<3", (time.time(),))

    def claim(self, run_id, model, reasoning, *, lease_seconds=600, now=None, job_id=None):
        now = time.time() if now is None else now
        self.db.execute("BEGIN IMMEDIATE")
        try:
            if self.pause_reason():
                self.db.rollback()
                raise SolverError("queue_paused")
            self.db.execute("""UPDATE jobs SET status=CASE WHEN attempt_count>=3 THEN 'permanent_failed' ELSE 'pending' END,
                lease_token=NULL,lease_deadline=NULL,last_error_code='stream_truncated',updated_at=?
                WHERE status='leased' AND lease_deadline<=?""", (now, now))
            row = self.db.execute("""SELECT * FROM jobs WHERE status IN ('pending','transient_failed')
                AND attempt_count<3 AND next_eligible_at<=? AND model_id=? AND reasoning=? AND prompt_version=?
                AND (? IS NULL OR id=?)
                ORDER BY created_at,id LIMIT 1""", (now, model, reasoning, VERSION, job_id, job_id)).fetchone()
            if row is None:
                self.db.commit()
                return None
            token = secrets.token_hex(24)
            self.db.execute("""UPDATE jobs SET status='leased',attempt_count=attempt_count+1,
                lease_token=?,lease_deadline=?,started_at=?,updated_at=?,solver_run_id=? WHERE id=?""",
                (token, now + lease_seconds, now, now, run_id, row["id"]))
            self.db.commit()
            return dict(self.db.execute("SELECT * FROM jobs WHERE id=?", (row["id"],)).fetchone())
        except BaseException:
            self.db.rollback()
            raise

    def finish(self, job, status, *, code=None, delay=0, draft=None):
        now = time.time()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            active = self.db.execute("SELECT * FROM jobs WHERE id=? AND status='leased' AND lease_token=? AND lease_deadline>?",
                                     (job["id"], job["lease_token"], now)).fetchone()
            if not active:
                raise SolverError("lost_lease")
            if draft is not None:
                self.db.execute("INSERT INTO drafts(job_id,payload,created_at) VALUES(?,?,?)", (job["id"], json.dumps(draft), now))
            self.db.execute("""UPDATE jobs SET status=?,last_error_code=?,next_eligible_at=?,
                completed_at=?,updated_at=?,lease_token=NULL,lease_deadline=NULL WHERE id=?""",
                (status, SolverError(code).code if code else None, now + delay,
                 now if status in {"solved_draft", "review_required", "permanent_failed"} else None, now, job["id"]))
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise

    def save_draft(self, job, draft):
        payload = {**draft, "question_id": job["question_id"],
                   "question_version_hash": job["question_version_hash"], "model_id": job["model_id"],
                   "reasoning": job["reasoning"], "prompt_version": job["prompt_version"],
                   "solver_run_id": job["solver_run_id"], "completed_at": time.time(),
                   "response_outcome": "validated_draft", "human_approval": None}
        self.finish(job, "review_required" if draft["review_required"] else "solved_draft", draft=payload)

    def pending_count(self, model, reasoning):
        return self.db.execute("SELECT count(*) FROM jobs WHERE status IN ('pending','transient_failed','leased') AND model_id=? AND reasoning=?",
                               (model, reasoning)).fetchone()[0]


def status(root: Path):
    path = root / "jobs.sqlite"
    if not path.exists():
        return {"counts": {}, "drafts": 0, "pause_reason": None}
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
        counts = dict(db.execute("SELECT status,count(*) FROM jobs GROUP BY status"))
        pause = db.execute("SELECT value FROM control WHERE key='pause'").fetchone()
        errors = dict(db.execute("SELECT last_error_code,count(*) FROM jobs WHERE last_error_code IS NOT NULL GROUP BY last_error_code"))
        return {"counts": counts, "drafts": db.execute("SELECT count(*) FROM drafts").fetchone()[0],
                "pause_reason": pause[0] if pause else None, "errors": errors}
