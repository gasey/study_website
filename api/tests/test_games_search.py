"""Real server game timing, multiplayer races, safe rewards and search audiences."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import hashlib, json, subprocess, sys
from uuid import uuid4
from pathlib import Path
import pytest
from psycopg.types.json import Jsonb


@pytest.fixture
def game_case(client, database):
    _, conn = database
    tag = uuid4().hex[:10]
    subject = "game_" + tag
    conn.execute("INSERT INTO review_taxonomy(id,label,level,version) VALUES(%s,%s,'subject','test')",(subject,subject))
    users = []
    headers = []
    for n in range(6):
        user = "player_" + tag + "_" + str(n)
        token = "session-" + user
        users.append(user)
        conn.execute(
            "INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)",
            (user, user, user + "@example.test"),
        )
        conn.execute(
            "INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES(%s,%s,now()+interval '1 day')",
            (hashlib.sha256(token.encode()).hexdigest(), user),
        )
        headers.append(
            {
                "Cookie": "ism_session=" + token,
                "Origin": "https://study.hawayu.in",
                "X-Review-CSRF": hashlib.sha256(
                    ("bank-review:" + token).encode()
                ).hexdigest(),
            }
        )
    ids = []
    for n in range(40):
        qid = "cq_" + tag + "_" + str(n)
        ids.append(qid)
        conn.execute(
            "INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES(%s,'mcq',%s,%s,'B','official')",
            (
                qid,
                "Synthetic game " + tag + " question " + str(n),
                Jsonb(["A", "B", "C", "D"]),
            ),
        )
        conn.execute(
            "INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary) VALUES(%s,'paper-test','mcq',%s,%s,1,'official',%s,true)",
            (
                "a_" + qid,
                "Synthetic game " + tag + " question " + str(n),
                Jsonb(["A", "B", "C", "D"]),
                qid,
            ),
        )
        conn.execute(
            "INSERT INTO question_classifications(question_id,subject_id,subject_label,taxonomy_version,source,review_status) VALUES(%s,%s,'Synthetic Game Topic','test','manual','approved')",
            (qid, subject),
        )
    client.cookies.clear()
    yield conn, subject, users, headers, ids
    # Close only this fixture's reservations. Production controller remains untouched.
    conn.execute(
        "UPDATE game_rooms SET state='cancelled',finished_at=now() WHERE owner_id=ANY(%s) AND state IN ('waiting','running')",
        (users,),
    )
    conn.execute(
        "UPDATE game_members SET released_at=COALESCE(released_at,now()) WHERE user_id=ANY(%s)",
        (users,),
    )


def create(client, h, subject, mode="speed", key=None, **kw):
    selection={'kind':'mixed','excluded_areas':[]} if mode=='cup' else {'kind':'area','area_id':'subject:'+subject,'excluded_areas':[]}
    preview=client.post('/api/games/preview',headers=h,json={'mode':mode,'selection':selection})
    if preview.status_code!=200:return preview
    return client.post(
        "/api/games/rooms",
        headers=h,
        json={
            "mode": mode,
            "selection": selection,
            "preview_hash": preview.json()["context_hash"],
            "request_key": key or uuid4().hex,
            **kw,
        },
    )


def play(client, h, room, choice=1):
    return client.post(
        "/api/games/rooms/" + room["id"] + "/answer",
        headers=h,
        json={"position": room["position"], "chosen_index": choice},
    )


def finish(client, h, r, conn=None):
    while r["state"] == "running":
        if conn:
            q = conn.execute(
                "SELECT questions FROM game_rooms WHERE id=%s", (r["id"],)
            ).fetchone()[0][r["position"]]
            choice = q["options"].index(q["answer_text"])
        else:
            choice = 1
        response = play(client, h, r, choice)
        assert response.status_code == 200, response.text
        r = response.json()
    return r


def test_solo_authority_replay_rewards_and_guards(client, game_case):
    conn, subject, users, h, ids = game_case
    key = uuid4().hex
    assert create(client, {}, subject).status_code == 401
    no_csrf = {k: v for k, v in h[0].items() if k != "X-Review-CSRF"}
    assert create(client, no_csrf, subject).status_code == 403
    r = create(client, h[0], subject, key=key)
    assert r.status_code == 200, r.text
    r = r.json()
    assert r["state"] == "running" and r["position"] == 0
    assert (
        "answer_text" not in json.dumps(r)
        and "answer_index" not in json.dumps(r)
        and "explanation" not in json.dumps(r)
    )
    assert create(client, h[0], subject, key=key).json()["id"] == r["id"]
    assert client.get("/api/games/rooms/" + r["id"], headers=h[1]).status_code == 404
    assert (
        client.post(
            "/api/questions/" + r["question"]["id"] + "/answer",
            headers=h[0],
            json={"chosen_index": 1},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/mocks", headers=h[0], json={"collection_id": "iti-instructor-2026"}
        ).status_code
        == 409
    )
    bad = client.post(
        "/api/games/rooms/" + r["id"] + "/answer",
        headers=h[0],
        json={"position": 0, "chosen_index": 1, "score": 1000},
    )
    assert bad.status_code == 422
    done = finish(client, h[0], r)
    assert done["state"] == "finished"
    me = done["players"][0]
    assert me["correct"] == 10 and me["wrong"] == 0 and len(done["review"]) == 10
    assert conn.execute(
        "SELECT sum(xp),sum(points) FROM reward_ledger WHERE user_id=%s", (users[0],)
    ).fetchone() == (100, 10)
    assert (
        conn.execute(
            "SELECT count(*) FROM attempts WHERE user_id=%s AND context='game'",
            (users[0],),
        ).fetchone()[0]
        == 10
    )
    replay = play(client, h[0], {**r, "position": 0})
    assert replay.status_code == 200
    assert (
        conn.execute(
            "SELECT count(*) FROM reward_question_claims WHERE user_id=%s", (users[0],)
        ).fetchone()[0]
        == 10
    )
    assert create(client, h[0], subject, key=key).json()["state"] == "finished"
    with pytest.raises(Exception):
        conn.execute("UPDATE game_rooms SET questions='[]' WHERE id=%s", (r["id"],))


def test_duel_matching_answer_races_and_blocking(client, game_case):
    conn, subject, users, h, _ = game_case
    r = create(client, h[0], subject, mode="duel", matchmaking=True)
    assert r.status_code == 200, r.text
    a = r.json()
    assert a["state"] == "waiting" and a["question"] is None
    key = uuid4().hex
    r = create(client, h[1], subject, mode="duel", matchmaking=True, key=key)
    assert r.status_code == 200, r.text
    b = r.json()
    assert a["id"] == b["id"] and b["state"] == "waiting"
    assert client.post('/api/games/rooms/'+a['id']+'/ready',headers=h[0],json={'ready':True}).status_code==200
    b=client.post('/api/games/rooms/'+a['id']+'/ready',headers=h[1],json={'ready':True}).json()
    assert b['state']=='running'
    assert (
        create(client, h[1], subject, mode="duel", matchmaking=True, key=key).json()[
            "id"
        ]
        == a["id"]
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        rs = list(pool.map(lambda c: play(client, h[0], b, c), [1, 0]))
    assert sorted(x.status_code for x in rs) == [200, 409]
    current = client.get("/api/games/rooms/" + a["id"], headers=h[1]).json()
    assert current["position"] == 0 and not current["answered"]
    r = play(client, h[1], current)
    assert r.status_code == 200
    r = r.json()
    assert r["position"] == 1
    assert "answer_index" not in json.dumps(r)
    for _ in range(9):
        r = play(client, h[0], r).json()
        r = play(client, h[1], r).json()
    assert r["state"] == "finished" and len(r["players"]) == 2
    fresh = create(client, h[0], subject, mode="party").json()
    conn.execute(
        "INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)",
        (users[0], users[1]),
    )
    assert (
        client.post(
            "/api/games/join", headers=h[1], json={"code": fresh["join_code"],"context_hash":fresh["context_hash"]}
        ).status_code
        == 403
    )


def test_multiplayer_capacity_forfeit_and_clock(client, game_case):
    conn, subject, users, h, _ = game_case
    r = create(client, h[0], subject, mode="party").json()
    code = r["join_code"]
    with ThreadPoolExecutor(max_workers=5) as pool:
        rs = list(
            pool.map(
                lambda headers: client.post(
                    "/api/games/join", headers=headers, json={"code": code,"context_hash":r["context_hash"]}
                ),
                h[1:],
            )
        )
    assert [x.status_code for x in rs].count(200) == 3 and [
        x.status_code for x in rs
    ].count(409) == 2, [x.text for x in rs]
    roster = client.get("/api/games/rooms/" + r["id"], headers=h[0]).json()
    assert len(roster["players"]) == 4
    assert client.post(
        "/api/games/rooms/" + r["id"] + "/start", headers=h[1], json={}
    ).status_code in (403, 404)
    members=conn.execute('SELECT user_id FROM game_members WHERE room_id=%s',(r['id'],)).fetchall()
    for (member,) in members:
        index=users.index(member)
        assert client.post('/api/games/rooms/'+r['id']+'/ready',headers=h[index],json={'ready':True}).status_code==200
    start = client.post("/api/games/rooms/" + r["id"] + "/start", headers=h[0], json={})
    assert start.status_code == 200, start.text
    conn.execute(
        "UPDATE game_rooms SET round_ends_at=now()-interval '1 second',round_started_at=now()-interval '26 seconds' WHERE id=%s",
        (r["id"],),
    )
    read = client.get("/api/games/rooms/" + r["id"], headers=h[0])
    assert read.json()["position"] == 1
    assert (
        client.post(
            "/api/games/rooms/" + r["id"] + "/leave", headers=h[0], json={}
        ).status_code
        == 200
    )
    conn.execute(
        "UPDATE game_rooms SET deadline=now()-interval '1 second' WHERE id=%s",
        (r["id"],),
    )
    from app.services import games as g

    async def end():
        from app.db import cursor

        async with cursor() as cur:
            await g.advance(cur, await g.room(cur, r["id"]), await g.clock(cur))

    client.portal.call(end)
    assert not conn.execute(
        "SELECT 1 FROM game_members WHERE room_id=%s AND released_at IS NULL",
        (r["id"],),
    ).fetchone()
    assert not conn.execute(
        "SELECT 1 FROM reward_ledger WHERE user_id=%s", (users[0],)
    ).fetchone()


def test_gauntlet_lives_source_changes_and_shared_cap(client, game_case):
    conn, subject, users, h, _ = game_case
    r = create(client, h[0], subject, mode="gauntlet").json()
    for _ in range(3):
        r = play(client, h[0], r, 0).json()
    assert (
        r["state"] == "finished"
        and r["players"][0]["lives"] == 0
        and r["players"][0]["wrong"] == 3
    )
    conn.execute(
        "INSERT INTO reward_ledger(user_id,event_key,kind,xp,note) VALUES(%s,%s,'study',290,'Synthetic cap setup')",
        (users[1], uuid4().hex),
    )
    r = create(client, h[1], subject).json()
    first = r["question"]["id"]
    r = play(client, h[1], r).json()
    conn.execute("UPDATE canonical_questions SET answer_text='C' WHERE id=%s", (first,))
    r = finish(client, h[1], r)
    assert r["players"][0]["excluded"] == 1
    assert (
        conn.execute(
            "SELECT sum(xp) FROM reward_ledger WHERE user_id=%s", (users[1],)
        ).fetchone()[0]
        == 300
    )
    assert not conn.execute(
        "SELECT 1 FROM reward_question_claims WHERE user_id=%s AND canonical_id=%s",
        (users[1], first),
    ).fetchone()


def test_weekly_cup_window_one_entry_and_delayed_review(client, game_case, monkeypatch):
    from app.services import games as g

    conn, subject, users, h, _ = game_case
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    cid, opens, closes = g.cup_window(now)

    async def before(cur):
        return opens - timedelta(seconds=1)

    monkeypatch.setattr(g, "clock", before)
    assert create(client, h[0], None, mode="cup").status_code == 409

    async def opened(cur):
        return opens + timedelta(seconds=1)

    monkeypatch.setattr(g, "clock", opened)
    response = create(client, h[0], None, mode="cup", public_result=True)
    assert response.status_code == 200, response.text
    r = finish(client, h[0], response.json(), conn)
    assert r["state"] == "finished" and r["review"] == [] and r["review_available_at"]
    assert create(client, h[0], None, mode="cup").status_code == 409
    board = client.get("/api/games/cup/board", headers=h[1], params={"cup_id": cid})
    assert any(x["handle"] == users[0] for x in board.json()["items"])

    hidden = client.post(
        "/api/games/cup/visibility",
        headers=h[0],
        json={"cup_id": cid, "enabled": False},
    )
    assert hidden.status_code == 200, hidden.text
    assert not any(
        x["handle"] == users[0]
        for x in client.get(
            "/api/games/cup/board", headers=h[1], params={"cup_id": cid}
        ).json()["items"]
    )
    own = client.get(
        "/api/games/cup/board", headers=h[0], params={"cup_id": cid}
    ).json()["items"]
    assert any(x["is_you"] and not x["public_result"] for x in own)

    async def closed(cur):
        return closes + timedelta(seconds=1)

    monkeypatch.setattr(g, "clock", closed)
    assert (
        len(client.get("/api/games/rooms/" + r["id"], headers=h[0]).json()["review"])
        == 25
    )


def test_global_search_audiences_and_previews(client, game_case):
    conn, subject, users, h, ids = game_case
    term = "searchtoken" + uuid4().hex[:8]
    conn.execute(
        "INSERT INTO creator_profiles(user_id,public,bio) VALUES(%s,true,%s),(%s,false,%s)",
        (users[1], term + " public biography", users[2], term + " PRIVATE BIO"),
    )
    desk = "desk_" + term
    conn.execute(
        "INSERT INTO study_desks(id,owner_id,name,goal) VALUES(%s,%s,%s,%s)",
        (desk, users[1], term + " desk", "Private group goal"),
    )
    conn.execute(
        "INSERT INTO study_desk_members(desk_id,user_id) VALUES(%s,%s)",
        (desk, users[1]),
    )
    conn.execute(
        "INSERT INTO personal_desks(user_id,document) VALUES(%s,%s)",
        (
            users[0],
            Jsonb(
                {
                    "notes": [
                        {
                            "id": "private-note",
                            "title": term + " own note",
                            "body": "PRIVATE NOTE BODY",
                        }
                    ]
                }
            ),
        ),
    )
    conn.execute(
        "INSERT INTO personal_desks(user_id,document) VALUES(%s,%s)",
        (
            users[2],
            Jsonb(
                {
                    "notes": [
                        {
                            "id": "other-note",
                            "title": term + " other note",
                            "body": "OTHER PRIVATE SECRET",
                        }
                    ]
                }
            ),
        ),
    )
    mid = "m_" + term
    draft = "draft_" + term
    payload = {
        "title": term + " paid guide",
        "summary": "Public preview summary",
        "access": "paid-preview",
        "tags": [],
        "blocks": [{"type": "paragraph", "text": "PAID BLOCK SECRET"}],
    }
    for key, status in [(mid, "published"), (draft, "draft")]:
        conn.execute(
            "INSERT INTO materials(id,author_id,title,blocks,status,published_revision) VALUES(%s,%s,%s,%s,%s,1)",
            (key, users[1], term + " material", Jsonb([]), status),
        )
        conn.execute(
            "INSERT INTO material_revisions(material_id,revision,payload,created_by) VALUES(%s,1,%s,%s)",
            (key, Jsonb(payload), users[1]),
        )
    r = client.get("/api/search", headers=h[0], params={"q": term})
    assert r.status_code == 200, r.text
    data = r.json()
    assert r.headers["cache-control"] == "private, no-store"
    groups = {g["category"]: g for g in data["groups"]}
    assert groups["people"]["total"] == 1 and groups["desks"]["total"] == 0
    assert groups["notes"]["total"] == 2 and groups["listings"]["total"] == 1
    text = json.dumps(data)
    assert (
        "PRIVATE BIO" not in text
        and "PAID BLOCK SECRET" not in text
        and "OTHER PRIVATE SECRET" not in text
        and draft not in text
    )
    assert "PRIVATE NOTE BODY" in text
    conn.execute(
        "INSERT INTO study_desk_members(desk_id,user_id) VALUES(%s,%s)",
        (desk, users[0]),
    )
    assert (
        client.get(
            "/api/search", headers=h[0], params={"q": term, "category": "desks"}
        ).json()["groups"][0]["total"]
        == 1
    )
    conn.execute(
        "INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)",
        (users[0], users[1]),
    )
    result = client.get("/api/search", headers=h[0], params={"q": term}).json()
    groups = {g["category"]: g for g in result["groups"]}
    assert (
        groups["people"]["total"] == 0
        and groups["listings"]["total"] == 0
        and groups["notes"]["total"] == 1
    )
    q = client.get(
        "/api/search",
        headers=h[0],
        params={"q": "Synthetic game", "category": "questions"},
    )
    assert q.status_code == 200, q.text
    assert q.json()["groups"][0]["total"] >= 40
    assert "answer_text" not in q.text and "answer_index" not in q.text
    assert (
        client.get("/api/search", headers=h[0], params={"q": "  "}).status_code == 422
    )
    assert (
        client.get(
            "/api/search",
            headers=h[0],
            params={"q": term, "category": "notes", "offset": 10001},
        ).status_code
        == 422
    )


def test_game_lobby_expiry_and_derived_exclusion(client, game_case):
    conn, subject, users, h, ids = game_case
    conn.execute(
        "UPDATE canonical_questions SET answer_source='derived' WHERE id=%s", (ids[0],)
    )
    r = create(client, h[0], subject, mode="duel").json()
    assert ids[0] not in [
        q["id"]
        for q in conn.execute(
            "SELECT questions FROM game_rooms WHERE id=%s", (r["id"],)
        ).fetchone()[0]
    ]
    conn.execute(
        "UPDATE game_rooms SET created_at=now()-interval '11 minutes' WHERE id=%s",
        (r["id"],),
    )
    closed = client.get("/api/games/rooms/" + r["id"], headers=h[0])
    assert closed.status_code == 200
    assert closed.json()["state"] == "cancelled"
    assert create(client, h[0], subject, mode="speed").status_code == 200


def test_search_question_subject_and_pagination(client, game_case):
    _, subject, _, h, _ = game_case
    first = client.get(
        "/api/search", headers=h[0], params={"q": subject, "category": "questions"}
    )
    assert first.status_code == 200, first.text
    page = first.json()["groups"][0]
    assert page["total"] == 40 and len(page["items"]) == 20
    second = client.get(
        "/api/search",
        headers=h[0],
        params={"q": subject, "category": "questions", "offset": 20},
    ).json()["groups"][0]
    assert len(second["items"]) == 20 and not set(x["id"] for x in page["items"]) & set(
        x["id"] for x in second["items"]
    )


def test_active_mock_resume_metadata_is_private_and_preserves_mode(client,game_case):
    from urllib.parse import urlparse,parse_qs
    conn,subject,users,h,ids=game_case
    cid='resume_'+uuid4().hex[:8]
    conn.execute("INSERT INTO collections(id,title,kind,visibility,live_version) VALUES (%s,'Synthetic unfinished mock','exam','public',1)",(cid,))
    conn.execute("INSERT INTO collection_sections(collection_id,version,path,title,position,query) VALUES (%s,1,'general/english','English',0,%s)",(cid,Jsonb({'subject_id':subject})))
    r=client.post('/api/mocks',headers=h[0],json={'collection_id':cid,'section_path':'general/english','answer_mode':'derived-practice','count':1,'duration_minutes':1})
    assert r.status_code==200,r.text
    mock=r.json()
    r=client.get('/api/games',headers=h[0]);assert r.status_code==200,r.text
    active=r.json()['active_mock']
    assert active['id']==mock['id'] and active['collection_title']=='Synthetic unfinished mock'
    parsed=urlparse(active['resume_url'])
    assert parsed.path=='/exams/'+cid+'/mock' and parse_qs(parsed.query)=={'section':['general/english'],'mode':['derived']}
    assert not {'questions','question_ids','saved_answers','answer_text','answer_index'}&set(active)
    assert client.get('/api/games',headers=h[1]).json()['active_mock'] is None
    assert create(client,h[0],subject).status_code==409
    conn.execute("UPDATE mock_sessions SET started_at=now()-interval '2 minutes' WHERE id=%s",(mock['id'],))
    assert client.get('/api/games',headers=h[0]).json()['active_mock']['seconds_remaining']==0
    r=client.post('/api/mocks/'+mock['id']+'/submit',headers=h[0],json={'answers':[]});assert r.status_code==200,r.text
    assert client.get('/api/games',headers=h[0]).json()['active_mock'] is None
