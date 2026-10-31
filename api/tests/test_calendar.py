"""Calendar publication, privacy, concurrent revisions and inbox delivery."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from psycopg.types.json import Jsonb
import pytest

TODAY = datetime.now(ZoneInfo("Asia/Kolkata")).date()


def doc(cid=None, **kw):
    d = dict(
        title="Synthetic examination notice",
        collection_id=cid,
        kind="exam",
        starts_on=str(TODAY + timedelta(days=1)),
        ends_on=None,
        summary="Synthetic official-source UI fixture only.",
        source_url="https://mpsc.mizoram.gov.in/test-calendar",
        source_reference="Synthetic reference 42",
        verification_note="Checked synthetic source dates for this isolated test.",
        verified_on=str(TODAY),
        state="draft",
    )
    return {**d, **kw}


def save(client, h, eid, d, v=0):
    return client.post(
        "/api/admin/calendar/" + eid,
        headers=h,
        json={
            "expected_version": v,
            "reason": "Synthetic staff source verification.",
            "event": d,
        },
    )


@pytest.fixture
def calendar_case(database, client):
    _, conn = database
    cid = "calendar_" + uuid4().hex[:10]
    eid = "event_" + uuid4().hex[:10]
    conn.execute(
        "INSERT INTO collections(id,title,kind,visibility) VALUES(%s,'Synthetic calendar exam','exam','public')",
        (cid,),
    )
    pref = conn.execute(
        "SELECT reminders FROM user_calendar_preferences WHERE user_id='author'"
    ).fetchone()
    yield conn, cid, eid
    conn.execute("DELETE FROM user_calendar_saved WHERE event_id=%s", (eid,))
    conn.execute("DELETE FROM user_exam_bookmarks WHERE collection_id=%s", (cid,))
    if pref:
        conn.execute(
            "UPDATE user_calendar_preferences SET reminders=%s WHERE user_id='author'",
            (pref[0],),
        )
    else:
        conn.execute("DELETE FROM user_calendar_preferences WHERE user_id='author'")


def test_calendar_publication_validation_and_cas(client, actor, calendar_case):
    conn, cid, eid = calendar_case
    h = actor("author")
    assert save(client, h, eid, doc(cid)).status_code == 403
    h = actor("owner")
    assert save(client, {}, eid, doc(cid)).status_code == 403
    for patch in [
        dict(source_url="https://mpsc.mizoram.gov.in.evil.test/x"),
        dict(source_url="http://mpsc.mizoram.gov.in/x"),
        dict(source_url="https://u:p@mpsc.mizoram.gov.in/x"),
        dict(verified_on=str(TODAY + timedelta(days=1))),
        dict(ends_on=str(TODAY)),
        dict(starts_on=None),
        dict(points=500),
    ]:
        assert save(client, h, eid, doc(cid, **patch)).status_code == 422
    r = save(client, h, eid, doc(cid))
    assert r.status_code == 200, r.text
    assert client.get("/api/calendar/events/" + eid).status_code == 404
    assert save(client, h, eid, doc(cid, state="published"), 1).status_code == 200
    r = client.get("/api/calendar/events/" + eid)
    assert r.json()["state"] == "published"
    assert "created_by" not in r.json()
    params = {
        "start": str(TODAY),
        "end": str(TODAY + timedelta(days=7)),
        "collection_id": cid,
    }
    r = client.get("/api/calendar/events", params=params)
    assert r.json()["total"] == 1
    assert r.headers["cache-control"].startswith("public")
    with ThreadPoolExecutor(max_workers=2) as pool:
        rs = list(
            pool.map(
                lambda n: save(
                    client,
                    h,
                    eid,
                    doc(
                        cid,
                        state="published",
                        title="Synthetic concurrent notice " + str(n),
                    ),
                    2,
                ),
                [1, 2],
            )
        )
    assert sorted(r.status_code for r in rs) == [200, 409]
    assert (
        len(client.get("/api/admin/calendar/" + eid + "/history").json()["items"]) == 3
    )
    with pytest.raises(Exception):
        conn.execute("DELETE FROM calendar_history WHERE event_id=%s", (eid,))
    assert save(client, h, eid, doc(cid, state="draft"), 3).status_code == 422
    assert save(client, h, eid, doc(cid, state="archived"), 3).status_code == 200
    assert client.get("/api/calendar/events", params=params).json()["total"] == 0
    assert client.get("/api/calendar/events/" + eid).json()["state"] == "archived"
    assert (
        client.get(
            "/api/calendar/events",
            params={"start": str(TODAY), "end": str(TODAY + timedelta(days=367))},
        ).status_code
        == 422
    )


def test_calendar_account_follows_saves_and_private_collection(
    client, actor, calendar_case
):
    conn, cid, eid = calendar_case
    h = actor("owner")
    assert save(client, h, eid, doc(cid, state="published")).status_code == 200
    h = actor("author")
    assert (
        client.post(
            "/api/me/calendar/save", json={"event_id": eid, "enabled": True}
        ).status_code
        == 403
    )
    for _ in range(2):
        assert (
            client.post(
                "/api/me/calendar/save",
                headers=h,
                json={"event_id": eid, "enabled": True},
            ).status_code
            == 200
        )
    assert (
        client.post(
            "/api/me/calendar/follow",
            headers=h,
            json={"collection_id": cid, "enabled": True},
        ).status_code
        == 200
    )
    r = client.get("/api/me/calendar")
    assert r.headers["cache-control"] == "private, no-store"
    p = r.json()
    assert (
        eid in p["saved"]
        and cid in p["following"]
        and p["upcoming"]["id"] == eid
        and not p["reminders"]
    )
    assert cid in client.get("/api/me/exam-bookmarks").json()["collection_ids"]
    actor("outsider")
    assert eid not in client.get("/api/me/calendar").json()["saved"]
    assert client.get("/api/admin/calendar").status_code == 403
    conn.execute("UPDATE collections SET visibility='hidden' WHERE id=%s", (cid,))
    assert client.get("/api/calendar/events/" + eid).status_code == 404
    assert not client.get(
        "/api/calendar/events",
        params={
            "start": str(TODAY),
            "end": str(TODAY + timedelta(days=2)),
            "collection_id": cid,
        },
    ).json()["items"]
    client.cookies.clear()
    assert (
        client.post(
            "/api/me/calendar/reminders",
            headers={"X-Device-Id": str(uuid4())},
            json={"enabled": True},
        ).status_code
        == 401
    )


def test_calendar_reminders_replay_preferences_and_withdrawal(
    client, actor, calendar_case
):
    import asyncio
    from app.services.calendar_reminders import sweep
    from app.db import cursor

    conn, cid, eid = calendar_case
    h = actor("owner")
    assert save(client, h, eid, doc(cid, state="published")).status_code == 200
    h = actor("author")
    client.post(
        "/api/me/calendar/follow",
        headers=h,
        json={"collection_id": cid, "enabled": True},
    )
    client.post(
        "/api/me/calendar/save", headers=h, json={"event_id": eid, "enabled": True}
    )

    async def run():
        async with cursor() as cur:
            await sweep(cur)

    client.portal.call(run)
    assert not conn.execute(
        "SELECT 1 FROM review_notifications WHERE calendar_event_id=%s", (eid,)
    ).fetchone()
    assert (
        client.post(
            "/api/me/calendar/reminders", headers=h, json={"enabled": True}
        ).status_code
        == 200
    )
    for _ in range(2):
        client.portal.call(run)
    rows = conn.execute(
        "SELECT event_key FROM review_notifications WHERE calendar_event_id=%s", (eid,)
    ).fetchall()
    assert (
        len(rows) == 2
    )  # one update plus one tomorrow reminder; audience deduplicated
    h = actor("owner")
    assert save(client, h, eid, doc(cid, state="archived"), 1).status_code == 200
    client.portal.call(run)
    client.portal.call(run)
    assert (
        conn.execute(
            "SELECT count(*) FROM review_notifications WHERE calendar_event_id=%s AND message LIKE 'Official calendar entry withdrawn:%%'",
            (eid,),
        ).fetchone()[0]
        == 1
    )
    assert not client.get("/api/me/calendar").json()["upcoming"]


def test_dateless_notice_and_pagination(client, actor, calendar_case):
    _, cid, eid = calendar_case
    h = actor("owner")
    assert (
        save(
            client,
            h,
            eid,
            doc(cid, kind="notification", starts_on=None, state="published"),
        ).status_code
        == 200
    )
    assert client.get("/api/calendar/events/" + eid).json()["starts_on"] is None
    r = client.get("/api/calendar/notices?limit=1")
    assert r.status_code == 200
    assert len(r.json()["items"]) == 1


def test_official_intake_receipt_and_replay(client, actor, database, tmp_path):
    import hashlib, json, subprocess, sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    evidence = tmp_path / "source.txt"
    evidence.write_text("Synthetic official-source evidence only.")
    eid = "cal_portal_" + uuid4().hex[:20]
    manifest = tmp_path / "intake.json"
    packet = {
        "evidence_sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
        "events": [{"id": eid, "event": doc(state="published")}],
    }
    manifest.write_text(json.dumps(packet))
    cmd = [
        sys.executable,
        str(root / "scripts/import-official-calendar.py"),
        "--manifest",
        str(manifest),
        "--evidence",
        str(evidence),
        "--database",
        database[0],
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["inserted"] == 0
    r = subprocess.run(cmd + ["--apply"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["inserted"] == 1
    h = actor("owner")
    changed = doc(state="published", title="Staff revised synthetic calendar notice")
    assert save(client, h, eid, changed, 1).status_code == 200
    r = subprocess.run(cmd + ["--apply"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["existing"] == 1
    assert client.get("/api/calendar/events/" + eid).json()["title"] == changed["title"]
    evidence.write_text("Changed synthetic evidence")
    assert (
        subprocess.run(cmd + ["--apply"], capture_output=True, text=True).returncode
        != 0
    )
