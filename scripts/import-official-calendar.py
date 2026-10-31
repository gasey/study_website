#!/usr/bin/env python3
"""Import a reviewed public-source packet without impersonating an account.

Dry-run by default. Never updates an existing event; staff revisions win.
The public evidence SHA and import receipt identify the technical intake.
"""

import argparse, hashlib, json, sys
from pathlib import Path
import psycopg
from psycopg.types.json import Jsonb

p = argparse.ArgumentParser()
p.add_argument("--manifest", type=Path, required=True)
p.add_argument("--evidence", type=Path, required=True)
p.add_argument("--database", required=True)
p.add_argument(
    "--api-root", type=Path, default=Path(__file__).resolve().parents[1] / "api"
)
p.add_argument("--apply", action="store_true")
a = p.parse_args()
sys.path.insert(0, str(a.api_root))
from app.routers.calendar import Event

packet = json.loads(a.manifest.read_text())
digest = hashlib.sha256(a.evidence.read_bytes()).hexdigest()
if digest != packet["evidence_sha256"]:
    raise SystemExit("Evidence SHA mismatch")
rows = []
seen = set()
for row in packet["events"]:
    if row["id"] in seen or not row["id"].startswith("cal_portal_"):
        raise SystemExit("Invalid/duplicate intake ID")
    seen.add(row["id"])
    data = Event.model_validate(row["event"]).model_dump(mode="json")
    rows.append((row["id"], data))
counts = {
    "prepared": len(rows),
    "inserted": 0,
    "existing": 0,
    "evidence_sha256": digest,
    "apply": a.apply,
}
with psycopg.connect("dbname=" + a.database) as conn:
    for eid, data in rows:
        conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", ("calendar:" + eid,))
        old = conn.execute(
            "SELECT id FROM exam_calendar_events WHERE id=%s", (eid,)
        ).fetchone()
        if old:
            counts["existing"] += 1
            continue
        if (
            data["collection_id"]
            and not conn.execute(
                "SELECT 1 FROM collections WHERE id=%s AND visibility='public'",
                (data["collection_id"],),
            ).fetchone()
        ):
            raise SystemExit("Public exam collection not found")
        if a.apply:
            columns = list(data)
            conn.execute(
                "INSERT INTO exam_calendar_events(id,"
                + ",".join(columns)
                + ",published_at) VALUES("
                + ",".join(["%s"] * (len(columns) + 1))
                + ",now())",
                (eid, *data.values()),
            )
            conn.execute(
                "INSERT INTO calendar_history(event_id,version,reason,snapshot) VALUES(%s,1,%s,%s)",
                (
                    eid,
                    "Technical official-source intake; evidence SHA256 " + digest,
                    Jsonb(data),
                ),
            )
            counts["inserted"] += 1
print(json.dumps(counts, indent=2))
