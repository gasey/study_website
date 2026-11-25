"""Tests for the Daily & Weekly Leaderboard Question-Picker microservice."""

from __future__ import annotations

from uuid import uuid4
import pytest
from psycopg.types.json import Jsonb


@pytest.fixture(scope="module")
def picker_pool(database):
    _, conn = database
    tag = uuid4().hex[:8]

    def seed(subject_id: str, topic_id: str | None, label: str, count: int):
        ids = []
        for i in range(count):
            qid = f"cq_{tag}_{subject_id}_{i}"
            ids.append(qid)
            conn.execute(
                """INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source)
                   VALUES(%s,'mcq',%s,%s,'B','official')""",
                (qid, f"[{label}] Synthetic question {tag}-{i}", Jsonb(["A", "B", "C", "D"])),
            )
            conn.execute(
                """INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary)
                   VALUES(%s,'paper-test','mcq',%s,%s,1,'official',%s,true)""",
                (f"a_{qid}", f"[{label}] Synthetic question {tag}-{i}", Jsonb(["A", "B", "C", "D"]), qid),
            )
            conn.execute(
                """INSERT INTO question_classifications(question_id,subject_id,subject_label,topic_id,topic_label,taxonomy_version,source,review_status)
                   VALUES(%s,%s,%s,%s,%s,'test','manual','approved')""",
                (qid, subject_id, label, topic_id, topic_id),
            )
        return ids

    gk_ids = seed("general-studies", None, "General Studies", 30)
    eng_ids = seed("english", "english/grammar", "English", 18)
    math_ids = seed("mathematics", "mathematics/arithmetic", "Mathematics", 18)
    comp_ids = seed("computer-science", None, "Computer Science", 15)
    # Specialist technical/medical pool that MUST NEVER leak into leaderboard sets
    rad_ids = seed("radiology", None, "Radiology", 40)

    yield {
        "conn": conn,
        "gk": set(gk_ids),
        "english": set(eng_ids),
        "maths": set(math_ids),
        "computer": set(comp_ids),
        "radiology": set(rad_ids),
    }


def test_unauthenticated_and_non_owner_rejected(client, actor):
    client.cookies.clear()
    r = client.get("/api/admin/leaderboard-picker/upcoming")
    assert r.status_code == 401

    h = actor("outsider")
    r2 = client.get("/api/admin/leaderboard-picker/upcoming", headers=h)
    assert r2.status_code == 403


def test_ensure_picks_fair_non_technical_sets_and_never_leaks_radiology(client, actor, picker_pool):
    h = actor("owner")
    resp = client.post(
        "/api/admin/leaderboard-picker/ensure",
        headers=h,
        json={"days_ahead": 2, "daily_theme": "balanced", "cup_theme": "balanced"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    dailies = body["upcoming"]["dailies"]
    cups = body["upcoming"]["cups"]

    assert len(dailies) == 3  # today + 2 days ahead
    assert len(cups) >= 1

    all_daily_ids: list[str] = []
    for d in dailies:
        assert d["question_count"] == 5
        qids = [q["id"] for q in d["questions"]]
        assert not (set(qids) & picker_pool["radiology"]), "Radiology leaked into Daily Five!"
        all_daily_ids.extend(qids)

    # 30-day no-repeat window: 3 consecutive Daily Five sets (15 Qs) must all be distinct
    assert len(set(all_daily_ids)) == len(all_daily_ids)

    cup = cups[0]
    assert cup["question_count"] == 25
    cup_qids = [q["id"] for q in cup["questions"]]
    assert not (set(cup_qids) & picker_pool["radiology"]), "Radiology leaked into Weekly Cup!"
    # No overlap between pre-picked Daily Five sets and Weekly Cup
    assert not (set(cup_qids) & set(all_daily_ids))


def test_single_subject_themes_and_single_slot_swap(client, actor, picker_pool):
    h = actor("owner")
    ensured = client.post(
        "/api/admin/leaderboard-picker/ensure",
        headers=h,
        json={"days_ahead": 2, "daily_theme": "balanced"},
    )
    assert ensured.status_code == 200, ensured.text
    target_daily = ensured.json()["upcoming"]["dailies"][-1]
    set_id = target_daily["id"]

    # Re-roll with "Only GK"
    r_gk = client.post(
        "/api/admin/leaderboard-picker/regenerate",
        headers=h,
        json={"kind": "daily", "set_id": set_id, "theme": "gk"},
    )
    assert r_gk.status_code == 200, r_gk.text
    updated_gk = next(d for d in r_gk.json()["upcoming"]["dailies"] if d["id"] == set_id)
    assert all(q["id"] in picker_pool["gk"] for q in updated_gk["questions"])

    # Re-roll with "Only Computer"
    r_comp = client.post(
        "/api/admin/leaderboard-picker/regenerate",
        headers=h,
        json={"kind": "daily", "set_id": set_id, "theme": "computer"},
    )
    assert r_comp.status_code == 200, r_comp.text
    updated_comp = next(d for d in r_comp.json()["upcoming"]["dailies"] if d["id"] == set_id)
    assert all(q["id"] in picker_pool["computer"] for q in updated_comp["questions"])

    # Swap Q1 (index 0) with a fresh English question
    before_ids = [q["id"] for q in updated_comp["questions"]]
    r_swap = client.post(
        "/api/admin/leaderboard-picker/swap",
        headers=h,
        json={"kind": "daily", "set_id": set_id, "position": 0, "theme": "english"},
    )
    assert r_swap.status_code == 200, r_swap.text
    after_set = next(d for d in r_swap.json()["upcoming"]["dailies"] if d["id"] == set_id)
    after_ids = [q["id"] for q in after_set["questions"]]
    assert after_ids[0] in picker_pool["english"]
    assert after_ids[0] != before_ids[0]
    assert after_ids[1:] == before_ids[1:]


def test_locked_once_player_enters_daily_set(client, actor, picker_pool):
    h_owner = actor("owner")
    ensured = client.post(
        "/api/admin/leaderboard-picker/ensure",
        headers=h_owner,
        json={"days_ahead": 1, "daily_theme": "balanced"},
    )
    assert ensured.status_code == 200
    today_id = ensured.json()["upcoming"]["dailies"][0]["id"]

    # A player enters today's Daily Five
    h_player = actor("outsider")
    preview = client.post(
        "/api/games/preview",
        headers=h_player,
        json={"mode": "daily", "selection": {"kind": "mixed", "excluded_areas": []}},
    )
    assert preview.status_code == 200, preview.text
    started = client.post(
        "/api/games/rooms",
        headers=h_player,
        json={
            "mode": "daily",
            "selection": {"kind": "mixed", "excluded_areas": []},
            "preview_hash": preview.json()["context_hash"],
            "request_key": uuid4().hex,
        },
    )
    assert started.status_code == 200, started.text

    # Owner cannot regenerate or swap today's set now that a player has entered
    h_owner = actor("owner")
    r_regen = client.post(
        "/api/admin/leaderboard-picker/regenerate",
        headers=h_owner,
        json={"kind": "daily", "set_id": today_id, "theme": "gk"},
    )
    assert r_regen.status_code == 409

    r_swap = client.post(
        "/api/admin/leaderboard-picker/swap",
        headers=h_owner,
        json={"kind": "daily", "set_id": today_id, "position": 0, "theme": "gk"},
    )
    assert r_swap.status_code == 409
