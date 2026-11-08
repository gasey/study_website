import csv
import io
import json
import os
from pathlib import Path
import sqlite3

from .errors import SolverError
from .validate import SECRET


def write_export(path: Path, text: str):
    if SECRET.search(text):
        raise SolverError("invalid_response")
    # Never overwrite an existing file (including the source bank).
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as out:
        out.write(text)


def export_review(root: Path, out: Path):
    rows = []
    path = root / "jobs.sqlite"
    if path.exists():
        with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
            rows = [json.loads(r[0]) for r in db.execute("SELECT payload FROM drafts ORDER BY created_at,job_id")]
    columns = ["question_id", "question_version_hash", "selected_option_id", "explanation", "certainty",
               "review_required", "review_reasons", "official_key_agreement", "model_id", "reasoning",
               "prompt_version", "solver_run_id", "response_outcome", "human_approval"]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    for row in rows:
        values = {}
        for key in columns:
            value = row.get(key)
            text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value) if value is not None else ""
            # Prevent spreadsheet formula execution in user-controlled text.
            values[key] = "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) or text.startswith(("\t", "\r", "\n")) else text
        writer.writerow(values)
    write_export(out, buffer.getvalue())
    return {"exported": len(rows), "publication_enabled": False}
