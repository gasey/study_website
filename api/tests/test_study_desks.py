"""Private planning isolation, membership lifecycle, disclosure and timer integrity."""

from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
import pytest
from psycopg.types.json import Jsonb


@pytest.fixture(autouse=True)
def desk_setup(database, client):
    from app.config import settings

    previous = settings.study_desks_private_enabled
    settings.study_desks_private_enabled = True
    _, conn = database
    original_plan = conn.execute(
        "SELECT plan_code,plan_status,trial_ends_at FROM users WHERE id='author'"
    ).fetchone()
    conn.execute(
        "UPDATE study_desks SET closed_at=now() WHERE owner_id='author' AND closed_at IS NULL"
    )
    conn.execute(
        "UPDATE study_desk_invites SET created_at=now()-interval '2 days' WHERE sender_id='author'"
    )
    conn.execute("DELETE FROM review_rate_buckets WHERE bucket LIKE 'cms:%'")
    conn.execute("DELETE FROM personal_desks")
    conn.execute("DELETE FROM study_focus_sessions")
    conn.execute(
        "UPDATE users SET plan_code='pro',plan_status='trial',trial_ends_at=now()+interval '7 days' WHERE id='author'"
    )
    yield
    settings.study_desks_private_enabled = previous
    conn.execute(
        "UPDATE users SET plan_code=%s,plan_status=%s,trial_ends_at=%s WHERE id='author'",
        original_plan,
    )


def room(client, actor):
    h = actor("author")
    r = client.post(
        "/api/desk/rooms",
        headers={**h, "idempotency-key": uuid4().hex},
        json={"name": "Synthetic private desk", "goal": "Revise a source together"},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def join(client, actor, did, target="outsider"):
    h = actor("author")
    r = client.post(
        "/api/desk/rooms/" + did + "/invite", headers=h, json={"handle": target}
    )
    assert r.status_code == 201, r.text
    iid = r.json()["id"]
    h = actor(target)
    r = client.post("/api/desk/invites/" + iid, headers=h, json={"decision": "accept"})
    assert r.status_code == 200, r.text
    return iid


def test_private_document_cas_account_binding_and_sources(client, actor, database):
    _, conn = database
    h = actor("author")
    r = client.get("/api/desk/personal")
    assert r.status_code == 200 and r.json()["registered"]
    assert r.headers["cache-control"] == "private, no-store"
    data = r.json()["data"]
    data.update(
        goal="Synthetic private goal",
        saved=["cq_test"],
        recent=["cq_test"],
        notes=[
            {
                "id": "n1",
                "title": "Private source note",
                "body": "This must never be visible to another account.",
                "subject": "English",
            }
        ],
    )
    body = {"user_id": "author", "expected_version": 0, "data": data}
    assert client.post("/api/desk/personal", json=body).status_code == 403
    r = client.post("/api/desk/personal", headers=h, json=body)
    assert r.status_code == 200 and r.json()["version"] == 1, r.text
    assert client.post("/api/desk/personal", headers=h, json=body).status_code == 409
    h = actor("outsider")
    assert client.get("/api/desk/personal").json()["data"]["goal"] == ""
    assert client.post("/api/desk/personal", headers=h, json=body).status_code == 409
    h = actor("author")
    body["expected_version"] = 1
    body["data"]["saved"] = ["not-a-question"]
    assert client.post("/api/desk/personal", headers=h, json=body).status_code == 422
    assert (
        conn.execute(
            "SELECT document->>'goal' FROM personal_desks WHERE user_id='author'"
        ).fetchone()[0]
        == "Synthetic private goal"
    )
    assert "answer_text" not in client.get("/api/desk/questions?ids=cq_test").text


def test_pro_creation_invites_acceptance_cooldown_expiry_and_block(
    client, actor, database
):
    import hashlib

    _, conn = database
    plain = "desk-free-" + uuid4().hex[:8]
    token = "session-" + plain
    conn.execute(
        "INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)",
        (plain, plain, plain + "@example.test"),
    )
    conn.execute(
        "INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES(%s,%s,now()+interval '1 day')",
        (hashlib.sha256(token.encode()).hexdigest(), plain),
    )
    h = {
        "Cookie": "ism_session=" + token,
        "Origin": "https://study.hawayu.in",
        "X-Review-CSRF": hashlib.sha256(("bank-review:" + token).encode()).hexdigest(),
    }
    key = uuid4().hex
    assert (
        client.post(
            "/api/desk/rooms",
            headers={**h, "idempotency-key": key},
            json={"name": "Not Pro"},
        ).status_code
        == 403
    )
    did = room(client, actor)
    h = actor("author")
    r = client.post(
        "/api/desk/rooms/" + did + "/invite", headers=h, json={"handle": "outsider"}
    )
    iid = r.json()["id"]
    assert (
        client.post(
            "/api/desk/rooms/" + did + "/invite", headers=h, json={"handle": "outsider"}
        ).json()["id"]
        == iid
    )
    assert (
        client.post(
            "/api/desk/invites/" + iid, headers=h, json={"decision": "accept"}
        ).status_code
        == 403
    )
    h = actor("outsider")
    assert client.get("/api/desk/rooms/" + did).status_code == 404
    assert len(client.get("/api/desk/rooms").json()["invitations"]) >= 1
    assert (
        client.post(
            "/api/desk/invites/" + iid, headers=h, json={"decision": "decline"}
        ).status_code
        == 200
    )
    h = actor("author")
    assert (
        client.post(
            "/api/desk/rooms/" + did + "/invite", headers=h, json={"handle": "outsider"}
        ).status_code
        == 409
    )
    did2 = room(client, actor)
    iid2 = client.post(
        "/api/desk/rooms/" + did2 + "/invite", headers=h, json={"handle": "outsider"}
    ).json()["id"]
    conn.execute(
        "UPDATE study_desk_invites SET expires_at=now()-interval '1 hour' WHERE id=%s",
        (iid2,),
    )
    h = actor("outsider")
    assert (
        client.post(
            "/api/desk/invites/" + iid2, headers=h, json={"decision": "accept"}
        ).status_code
        == 409
    )
    h = actor("author")
    r = client.post(
        "/api/desk/rooms/" + did2 + "/invite", headers=h, json={"handle": "outsider"}
    )
    assert r.status_code == 201, r.text
    assert (
        client.post(
            "/api/creators/outsider/block", headers=h, json={"enabled": True}
        ).status_code
        == 200
    )
    assert (
        conn.execute(
            "SELECT state FROM study_desk_invites WHERE id=%s", (r.json()["id"],)
        ).fetchone()[0]
        == "cancelled"
    )
    client.post("/api/creators/outsider/block", headers=h, json={"enabled": False})


def test_membership_chat_history_revocation_and_duplicate_saves(
    client, actor, database
):
    _, conn = database
    did = room(client, actor)
    h = actor("author")
    key = uuid4().hex
    r = client.post(
        "/api/desk/rooms/" + did + "/messages",
        headers={**h, "idempotency-key": key},
        json={"body": "Old chat before someone joined."},
    )
    assert r.status_code == 201, r.text
    join(client, actor, did)
    h = actor("outsider")
    assert not client.get("/api/desk/rooms/" + did + "/messages").json()["items"]
    body = {
        "kind": "question",
        "question_id": "cq_test",
        "body": "A synthetic shared question with context.",
    }
    key = uuid4().hex
    with ThreadPoolExecutor(max_workers=3) as pool:
        rs = list(
            pool.map(
                lambda _: client.post(
                    "/api/desk/rooms/" + did + "/items",
                    headers={**h, "idempotency-key": key},
                    json=body,
                ),
                range(3),
            )
        )
    assert all(r.status_code == 201 for r in rs), [r.text for r in rs]
    assert len({r.json()["id"] for r in rs}) == 1
    iid = rs[0].json()["id"]
    h = actor("author")
    assert (
        client.get("/api/desk/rooms/" + did + "/items").json()["items"][0]["id"] == iid
    )
    h = actor("outsider")
    assert (
        client.post("/api/desk/rooms/" + did + "/leave", headers=h, json={}).status_code
        == 200
    )
    for suffix in ["", "/items", "/messages"]:
        assert client.get("/api/desk/rooms/" + did + suffix).status_code == 404
    assert (
        client.post(
            "/api/desk/rooms/" + did + "/messages",
            headers={**h, "idempotency-key": uuid4().hex},
            json={"body": "Cannot post after leaving"},
        ).status_code
        == 404
    )
    h = actor("author")
    assert (
        client.post("/api/desk/rooms/" + did + "/leave", headers=h, json={}).status_code
        == 409
    )
    assert (
        client.post("/api/desk/rooms/" + did + "/close", headers=h, json={}).status_code
        == 200
    )
    assert client.get("/api/desk/rooms/" + did).status_code == 404


def test_explicit_progress_mistake_sharing_block_and_history(client, actor, database):
    _, conn = database
    did = room(client, actor)
    join(client, actor, did)
    h = actor("outsider")
    r = client.get("/api/desk/rooms/" + did)
    assert (
        next(m for m in r.json()["members"] if m["user_id"] == "author")["progress"]
        is None
    )
    data = {
        "kind": "mistake",
        "question_id": "cq_test",
        "body": "I choose to share this mistake.",
    }
    assert (
        client.post(
            "/api/desk/rooms/" + did + "/items",
            headers={**h, "idempotency-key": uuid4().hex},
            json=data,
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/desk/rooms/" + did + "/sharing",
            headers=h,
            json={"mistakes": True, "progress": True},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/desk/rooms/" + did + "/items",
            headers={**h, "idempotency-key": uuid4().hex},
            json=data,
        ).status_code
        == 201
    )
    h = actor("author")
    assert client.get("/api/desk/rooms/" + did + "/items?kind=mistake").json()["items"]
    h = actor("outsider")
    client.post(
        "/api/desk/rooms/" + did + "/sharing",
        headers=h,
        json={"mistakes": False, "progress": False},
    )
    h = actor("author")
    assert not client.get("/api/desk/rooms/" + did + "/items?kind=mistake").json()[
        "items"
    ]
    h = actor("outsider")
    key = uuid4().hex
    client.post(
        "/api/desk/rooms/" + did + "/messages",
        headers={**h, "idempotency-key": key},
        json={"body": "A visible message before a block."},
    )
    h = actor("author")
    assert client.get("/api/desk/rooms/" + did + "/messages").json()["items"]
    client.post("/api/creators/outsider/block", headers=h, json={"enabled": True})
    assert not client.get("/api/desk/rooms/" + did + "/messages").json()["items"]
    client.post("/api/creators/outsider/block", headers=h, json={"enabled": False})


def test_focus_cannot_fabricate_time_versions_or_rewards(client, actor, database):
    _, conn = database
    h = actor("author")
    before = conn.execute("SELECT count(*) FROM reward_ledger").fetchone()[0]
    key = uuid4().hex
    r = client.post(
        "/api/desk/focus", headers={**h, "idempotency-key": key}, json={"minutes": 5}
    )
    assert r.status_code == 201, r.text
    s = r.json()
    assert (
        client.post(
            "/api/desk/focus",
            headers={**h, "idempotency-key": key},
            json={"minutes": 5},
        ).json()["id"]
        == s["id"]
    )
    assert (
        client.post(
            "/api/desk/focus/" + s["id"],
            headers=h,
            json={"expected_version": 1, "action": "finish"},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/desk/focus/" + s["id"],
            headers=h,
            json={"expected_version": 1, "action": "pause"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/desk/focus/" + s["id"],
            headers=h,
            json={"expected_version": 1, "action": "resume"},
        ).status_code
        == 409
    )
    h2 = actor("outsider")
    assert (
        client.post(
            "/api/desk/focus/" + s["id"],
            headers=h2,
            json={"expected_version": 2, "action": "resume"},
        ).status_code
        == 404
    )
    h = actor("author")
    r = client.post(
        "/api/desk/focus/" + s["id"],
        headers=h,
        json={"expected_version": 2, "action": "cancel"},
    )
    assert r.status_code == 200 and r.json()["elapsed_seconds"] < 300
    assert conn.execute("SELECT count(*) FROM reward_ledger").fetchone()[0] == before
    r = client.post(
        "/api/desk/focus",
        headers={**h, "idempotency-key": uuid4().hex},
        json={"minutes": 5},
    )
    s = r.json()
    conn.execute(
        "UPDATE study_focus_sessions SET resumed_at=now()-interval '301 seconds' WHERE id=%s",
        (s["id"],),
    )
    assert (
        client.post(
            "/api/desk/focus/" + s["id"],
            headers=h,
            json={"expected_version": 1, "action": "finish"},
        ).status_code
        == 200
    )


def test_report_snapshot_scoped_admin_review_and_immutability(client, actor, database):
    _, conn = database
    did = room(client, actor)
    join(client, actor, did)
    h = actor("author")
    r = client.post(
        "/api/desk/rooms/" + did + "/messages",
        headers={**h, "idempotency-key": uuid4().hex},
        json={"body": "Synthetic message that will be reported."},
    )
    mid = r.json()["id"]
    h = actor("outsider")
    r = client.post(
        "/api/desk/rooms/" + did + "/report",
        headers=h,
        json={
            "target_kind": "message",
            "target_id": str(mid),
            "reason": "Synthetic conduct report with context.",
        },
    )
    assert r.status_code == 201, r.text
    assert client.get("/api/desk/admin/reports").status_code == 403
    h = actor("owner")
    r = client.get("/api/desk/admin/reports")
    assert r.status_code == 200
    rpt = next(r for r in r.json()["items"] if r["desk_id"] == did)
    assert rpt["snapshot"]["body"].startswith("Synthetic message")
    assert client.get("/api/desk/rooms/" + did + "/messages").status_code == 404
    assert (
        client.post(
            "/api/desk/admin/reports/" + str(rpt["id"]) + "/resolve",
            headers=h,
            json={"reason": "Synthetic report investigated.", "action": "remove"},
        ).status_code
        == 200
    )
    h = actor("author")
    assert not client.get("/api/desk/rooms/" + did + "/messages").json()["items"]
    assert (
        conn.execute(
            "SELECT snapshot->>'body' FROM study_desk_reports WHERE id=%s", (rpt["id"],)
        )
        .fetchone()[0]
        .startswith("Synthetic message")
    )
    with pytest.raises(Exception, match="append-only"):
        with conn.transaction():
            conn.execute(
                "UPDATE study_desk_events SET action='tampered' WHERE desk_id=%s",
                (did,),
            )


def test_last_seat_acceptance_is_atomic_and_rejoining_revokes_history(
    client, actor, database
):
    import hashlib

    _, conn = database
    did = room(client, actor)
    users = ["seat-" + uuid4().hex[:8] for _ in range(6)]
    invitations = {}
    headers = {}
    for user in users:
        conn.execute(
            "INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)",
            (user, user, user + "@example.test"),
        )
        token = "seat-session-" + user
        conn.execute(
            "INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES(%s,%s,now()+interval '1 day')",
            (hashlib.sha256(token.encode()).hexdigest(), user),
        )
        headers[user] = {
            "Cookie": "ism_session=" + token,
            "Origin": "https://study.hawayu.in",
            "X-Review-CSRF": hashlib.sha256(
                ("bank-review:" + token).encode()
            ).hexdigest(),
        }
        h = actor("author")
        r = client.post(
            "/api/desk/rooms/" + did + "/invite", headers=h, json={"handle": user}
        )
        assert r.status_code == 201, r.text
        invitations[user] = r.json()["id"]
    for user in users[:4]:
        assert (
            client.post(
                "/api/desk/invites/" + invitations[user],
                headers=headers[user],
                json={"decision": "accept"},
            ).status_code
            == 200
        )
    with ThreadPoolExecutor(max_workers=2) as pool:
        rs = list(
            pool.map(
                lambda user: client.post(
                    "/api/desk/invites/" + invitations[user],
                    headers=headers[user],
                    json={"decision": "accept"},
                ),
                users[4:],
            )
        )
    assert sorted(r.status_code for r in rs) == [200, 409], [r.text for r in rs]
    assert (
        conn.execute(
            "SELECT count(*) FROM study_desk_members WHERE desk_id=%s AND left_at IS NULL",
            (did,),
        ).fetchone()[0]
        == 6
    )
    user = users[0]
    assert (
        client.post(
            "/api/desk/rooms/" + did + "/leave", headers=headers[user], json={}
        ).status_code
        == 200
    )
    h = actor("author")
    r = client.post(
        "/api/desk/rooms/" + did + "/invite", headers=h, json={"handle": user}
    )
    assert r.status_code == 201, r.text
    assert (
        client.post(
            "/api/desk/invites/" + r.json()["id"],
            headers=headers[user],
            json={"decision": "accept"},
        ).status_code
        == 200
    )


def test_feature_switch_keeps_exit_safety_and_personal_work_available(
    client, actor, database
):
    from app.config import settings

    did = room(client, actor)
    join(client, actor, did)
    settings.study_desks_private_enabled = False
    h = actor("outsider")
    assert client.get("/api/desk/rooms/" + did).status_code == 200
    assert (
        client.post(
            "/api/desk/rooms/" + did + "/messages",
            headers={**h, "idempotency-key": uuid4().hex},
            json={"body": "Posting pauses when the flag is off."},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/desk/rooms/" + did + "/report",
            headers=h,
            json={
                "target_kind": "desk",
                "target_id": did,
                "reason": "Safety reports must keep working during a posting pause.",
            },
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/desk/rooms/" + did + "/sharing", headers=h, json={"progress": True}
        ).status_code
        == 409
    )
    assert (
        client.post("/api/desk/rooms/" + did + "/leave", headers=h, json={}).status_code
        == 200
    )
    assert client.get("/api/desk/personal").status_code == 200


def test_report_retention_preserves_open_cases_and_closed_content_is_purged(
    client, actor, database
):
    import asyncio
    from app.services.desk_retention import sweep
    from app.db import cursor

    _, conn = database
    did = room(client, actor)
    join(client, actor, did)
    h = actor("author")
    mid = client.post(
        "/api/desk/rooms/" + did + "/messages",
        headers={**h, "idempotency-key": uuid4().hex},
        json={"body": "Synthetic retained message for report."},
    ).json()["id"]
    h = actor("outsider")
    client.post(
        "/api/desk/rooms/" + did + "/report",
        headers=h,
        json={
            "target_kind": "message",
            "target_id": str(mid),
            "reason": "A synthetic reason for evidence retention.",
        },
    )
    rid = conn.execute(
        "SELECT id FROM study_desk_reports WHERE desk_id=%s", (did,)
    ).fetchone()[0]
    conn.execute(
        "UPDATE study_desk_reports SET retain_until=now()-interval '1 day' WHERE id=%s",
        (rid,),
    )

    actor("owner")
    assert any(
        r["id"] == rid for r in client.get("/api/desk/admin/reports").json()["items"]
    )

    # Use the fixture TestClient's running event loop, not a second psycopg pool.
    async def run():
        async with cursor() as cur:
            await sweep(cur)

    client.portal.call(run)
    assert conn.execute(
        "SELECT snapshot FROM study_desk_reports WHERE id=%s", (rid,)
    ).fetchone()[0]
    conn.execute("UPDATE study_desk_reports SET state='resolved' WHERE id=%s", (rid,))
    conn.execute(
        "UPDATE study_desks SET closed_at=now()-interval '31 days' WHERE id=%s", (did,)
    )
    client.portal.call(run)
    assert (
        conn.execute(
            "SELECT snapshot FROM study_desk_reports WHERE id=%s", (rid,)
        ).fetchone()[0]
        == {}
    )
    assert not conn.execute(
        "SELECT 1 FROM study_desk_messages WHERE desk_id=%s", (did,)
    ).fetchone()


def test_restricted_edits_cannot_bypass_posting_gate_but_withdrawal_works(
    client, actor, database
):
    _, conn = database
    did = room(client, actor)
    h = actor("author")
    mid = client.post(
        "/api/desk/rooms/" + did + "/messages",
        headers={**h, "idempotency-key": uuid4().hex},
        json={"body": "Synthetic message before restriction."},
    ).json()["id"]
    iid = client.post(
        "/api/desk/rooms/" + did + "/items",
        headers={**h, "idempotency-key": uuid4().hex},
        json={"kind": "note", "body": "Synthetic note before restriction."},
    ).json()["id"]
    action = conn.execute(
        "INSERT INTO mod_actions(actor_id,action,target_user,note) VALUES('owner','mute','author','Synthetic desk restriction') RETURNING id"
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO sanctions(user_id,kind,step,ends_at,action_id) VALUES('author','mute',1,now()+interval '1 hour',%s)",
        (action,),
    )
    try:
        for suffix in ["/messages/" + str(mid), "/items/" + iid]:
            assert (
                client.post(
                    "/api/desk/rooms/" + did + suffix,
                    headers=h,
                    json={
                        "expected_version": 1,
                        "body": "Restricted replacement text.",
                    },
                ).status_code
                == 403
            )
            assert (
                client.post(
                    "/api/desk/rooms/" + did + suffix,
                    headers=h,
                    json={"expected_version": 1, "body": "Withdrawn", "delete": True},
                ).status_code
                == 200
            )
        assert (
            client.post(
                "/api/desk/rooms/" + did + "/settings",
                headers=h,
                json={"expected_version": 1, "name": "Restricted replacement"},
            ).status_code
            == 403
        )
    finally:
        conn.execute("DELETE FROM sanctions WHERE action_id=%s", (action,))
