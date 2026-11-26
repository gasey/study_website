"""Finna Blocks backend tests: run lifecycle, score bounds, XP award, leaderboard & mobile boundary."""
from app.services.mobile_identity import allowed


def test_block_run_lifecycle_score_bound_and_leaderboard(client, actor, database):
    conn = database[1]
    conn.execute("DELETE FROM block_puzzle_runs WHERE user_id='author'")
    conn.execute(
        "INSERT INTO reward_profiles(user_id, board_public) VALUES('author', true) "
        "ON CONFLICT (user_id) DO UPDATE SET board_public=true"
    )
    headers = actor("author")

    start = client.post(
        "/api/blocks/runs",
        headers=headers,
        json={"mode": "endless", "subject_scope": "gk-gs"},
    )
    assert start.status_code == 200, start.text
    run_id = start.json()["run_id"]
    assert run_id.startswith("blk_")

    # Checkpoint with plausible progress
    cp = client.post(
        f"/api/blocks/runs/{run_id}/checkpoint",
        headers=headers,
        json={
            "score": 1450,
            "lines_cleared": 4,
            "pieces_placed": 12,
            "questions_answered": 3,
            "questions_correct": 2,
            "best_streak": 2,
            "max_combo": 2,
            "clutch_saves_used": 0,
        },
    )
    assert cp.status_code == 200, cp.text
    assert cp.json()["score"] == 1450
    assert cp.json()["status"] == "active"

    # Attempt absurd spoofed score -> clamped to server plausibility bound
    fin = client.post(
        f"/api/blocks/runs/{run_id}/finish",
        headers=headers,
        json={
            "score": 9_999_999,
            "lines_cleared": 6,
            "pieces_placed": 18,
            "questions_answered": 5,
            "questions_correct": 4,
            "best_streak": 3,
            "max_combo": 3,
            "clutch_saves_used": 1,
        },
    )
    assert fin.status_code == 200, fin.text
    done = fin.json()
    assert done["status"] == "finished"
    assert done["score"] < 20_000
    assert done["is_new_best"] is True
    assert done["xp_awarded"] > 0

    me = client.get("/api/blocks/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["best_endless"] == done["score"]
    assert me.json()["total_questions_correct"] >= 4

    board = client.get("/api/blocks/leaderboard?period=week", headers=headers)
    assert board.status_code == 200, board.text
    b = board.json()
    assert b["total"] >= 1
    assert any(row["score"] == done["score"] for row in b["items"])
    assert b["placement"]["score"] == done["score"]


def test_blocks_mobile_boundary():
    assert allowed("GET", "/api/blocks/leaderboard")
    assert allowed("GET", "/api/blocks/me")
    assert allowed("POST", "/api/blocks/runs")
    assert allowed("POST", "/api/blocks/runs/blk_abc123/checkpoint")
    assert allowed("POST", "/api/blocks/runs/blk_abc123/finish")
    assert not allowed("DELETE", "/api/blocks/runs/blk_abc123")
