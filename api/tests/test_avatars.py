from test_account_hardening import headers as account_headers
"""Account isolation, curated cosmetics, durable level unlocks and public projections."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
from uuid import uuid4
import pytest
from app.services.avatars import DEFAULT


@pytest.fixture
def avatar_user(client, database):
    user = "avatar-" + uuid4().hex[:12]
    token = "session-" + user
    conn = database[1]
    conn.execute(
        "INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)",
        (user, user, user + "@example.test"),
    )
    conn.execute(
        "INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES(%s,%s,now()+interval '1 day')",
        (hashlib.sha256(token.encode()).hexdigest(), user),
    )
    client.cookies.clear()
    client.cookies.set("ism_session", token)
    return user, {
        "Origin": "https://study.hawayu.in",
        "X-Review-CSRF": hashlib.sha256(("bank-review:" + token).encode()).hexdigest(),
    }


def body(user, look=None, version=0):
    return {
        "user_id": user,
        "expected_version": version,
        "look": dict(DEFAULT) if look is None else look,
    }


def test_account_save_reload_profile_session_and_no_reward_mutation(
    client, avatar_user, database
):
    user, h = avatar_user
    conn = database[1]
    r = client.get("/api/me/avatar")
    assert r.status_code == 200 and r.headers["cache-control"] == "private, no-store"
    assert (
        r.json()["avatar"] is None
        and sum(i["available"] for i in r.json()["catalog"]) == 19
    )
    before = conn.execute("SELECT count(*) FROM reward_ledger").fetchone()[0]
    look = {**DEFAULT, "hair": "Long", "top": "Teal"}
    r = client.post("/api/me/avatar", headers=h, json=body(user, look))
    assert r.status_code == 200, r.text
    assert client.get("/api/me/avatar").json()["avatar"] == look
    assert client.get("/api/me/profile").json()["avatar"] == look
    assert client.get("/api/auth/session").json()["avatar"] == look
    assert (
        client.patch("/api/me/profile", headers=account_headers(client), json={"name": "Synthetic display name"}).json()[
            "avatar"
        ]
        == look
    )
    assert conn.execute("SELECT count(*) FROM reward_ledger").fetchone()[0] == before
    assert (
        conn.execute(
            "SELECT count(*) FROM avatar_events WHERE user_id=%s", (user,)
        ).fetchone()[0]
        == 1
    )
    r = client.post("/api/me/avatar", headers=h, json=body(user, look))
    assert r.status_code == 200 and r.json()["replayed"]
    assert (
        conn.execute(
            "SELECT count(*) FROM avatar_events WHERE user_id=%s", (user,)
        ).fetchone()[0]
        == 1
    )


def test_csrf_account_binding_curated_values_and_level_guards(
    client, avatar_user, database
):
    user, h = avatar_user
    assert client.post("/api/me/avatar", json=body(user)).status_code == 403
    assert (
        client.post("/api/me/avatar", headers=h, json=body("owner")).status_code == 409
    )
    for change in [
        {"bg": "url(https://example.test/image.svg)"},
        {"hair": "<script>"},
        {"photo": "https://example.test/a.png"},
    ]:
        assert (
            client.post(
                "/api/me/avatar", headers=h, json=body(user, {**DEFAULT, **change})
            ).status_code
            == 422
        )
    assert (
        client.post(
            "/api/me/avatar", headers=h, json={**body(user), "xp": 99999}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/me/avatar", headers=h, json=body(user, {**DEFAULT, "acc": "Glasses"})
        ).status_code
        == 403
    )
    client.cookies.clear()
    guest = {"X-Device-Id": str(uuid4())}
    assert (
        client.post(
            "/api/me/avatar", headers={**h, **guest}, json=body(user)
        ).status_code
        == 401
    )
    assert client.get("/api/me/avatar", headers=guest).json()["avatar"] is None


def test_concurrent_different_looks_conflict_and_reset_keeps_history(
    client, avatar_user, database
):
    user, h = avatar_user
    conn = database[1]
    looks = [{**DEFAULT, "hair": "Short"}, {**DEFAULT, "hair": "Long"}]
    with ThreadPoolExecutor(max_workers=2) as pool:
        rs = list(
            pool.map(
                lambda look: client.post(
                    "/api/me/avatar", headers=h, json=body(user, look)
                ),
                looks,
            )
        )
    assert sorted(r.status_code for r in rs) == [200, 409]
    assert client.get("/api/me/avatar").json()["avatar_version"] == 1
    r = client.post(
        "/api/me/avatar",
        headers=h,
        json={"user_id": user, "expected_version": 1, "look": None},
    )
    assert r.status_code == 200
    assert client.get("/api/me/avatar").json()["avatar"] is None
    assert (
        conn.execute(
            "SELECT count(*) FROM avatar_events WHERE user_id=%s", (user,)
        ).fetchone()[0]
        == 2
    )
    with pytest.raises(Exception, match="append-only"):
        with conn.transaction():
            conn.execute(
                "UPDATE avatar_events SET action='saved' WHERE user_id=%s", (user,)
            )


def test_earned_unlocks_persist_after_xp_reversal_and_cannot_be_client_granted(
    client, avatar_user, database
):
    user, h = avatar_user
    conn = database[1]
    conn.execute(
        "INSERT INTO reward_ledger(user_id,event_key,kind,xp,note) VALUES(%s,%s,'adjustment',4000,'Synthetic XP only')",
        (user, uuid4().hex),
    )
    assert client.get("/api/me/avatar").json()["level"] == 10
    look = {**DEFAULT, "top": "Saffron", "acc": "Headphones", "bg": "#D3EAEA"}
    assert (
        client.post("/api/me/avatar", headers=h, json=body(user, look)).status_code
        == 200
    )
    assert (
        conn.execute(
            "SELECT count(*) FROM user_avatar_items WHERE user_id=%s", (user,)
        ).fetchone()[0]
        == 5
    )
    conn.execute(
        "INSERT INTO reward_ledger(user_id,event_key,kind,xp,note) VALUES(%s,%s,'adjustment',-4000,'Synthetic XP reversal')",
        (user, uuid4().hex),
    )
    r = client.get("/api/me/avatar").json()
    assert r["level"] == 1
    assert all(
        i["available"] and i["claimed"]
        for i in r["catalog"]
        if i["id"] == "acc-headphones"
    )
    assert (
        client.post(
            "/api/me/avatar", headers=h, json=body(user, {**look, "hair": "Buzz"}, 1)
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/me/avatar", headers=h, json=body(user, {**look, "frame": "Gold"}, 2)
        ).status_code
        == 403
    )


def test_existing_public_visibility_and_desk_block_boundaries(
    client, avatar_user, database, actor
):
    user, h = avatar_user
    conn = database[1]
    look = dict(DEFAULT)
    assert (
        client.post("/api/me/avatar", headers=h, json=body(user, look)).status_code
        == 200
    )
    assert (
        client.post(
            "/api/creators/settings",
            headers=h,
            json={"public": True, "bio": "Synthetic avatar test creator."},
        ).status_code
        == 200
    )
    assert client.get("/api/creators/" + user).json()["avatar"] == look
    conn.execute(
        "INSERT INTO reward_ledger(user_id,event_key,kind,xp,note) VALUES(%s,%s,'adjustment',10,'Synthetic public board XP')",
        (user, uuid4().hex),
    )
    assert not any(
        r["handle"] == user
        for r in client.get("/api/rewards/leaderboard").json()["items"]
    )
    assert (
        client.post(
            "/api/rewards/visibility", headers=h, json={"public": True}
        ).status_code
        == 200
    )
    assert (
        next(
            r
            for r in client.get("/api/rewards/leaderboard").json()["items"]
            if r["handle"] == user
        )["avatar"]
        == look
    )
    did = "desk_" + uuid4().hex
    conn.execute(
        "INSERT INTO study_desks(id,owner_id,name) VALUES(%s,%s,'Synthetic avatar desk')",
        (did, user),
    )
    conn.execute(
        "INSERT INTO study_desk_members(desk_id,user_id) VALUES(%s,%s),(%s,%s)",
        (did, user, did, "outsider"),
    )
    h = actor("outsider")
    assert (
        next(
            m
            for m in client.get("/api/desk/rooms/" + did).json()["members"]
            if m["user_id"] == user
        )["avatar"]
        == look
    )
    assert (
        client.post(
            "/api/creators/" + user + "/block", headers=h, json={"enabled": True}
        ).status_code
        == 200
    )
    assert client.get("/api/creators/" + user).status_code == 404
    assert (
        next(
            m
            for m in client.get("/api/desk/rooms/" + did).json()["members"]
            if m["user_id"] == user
        )["avatar"]
        is None
    )
    assert not any(r["id"] == user for r in client.get("/api/creators").json()["items"])
