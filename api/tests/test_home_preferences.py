"""Home layout preferences & first-time onboarding persistence."""
from app.services.mobile_identity import allowed


def test_home_preferences_defaults_save_and_normalize(client, actor, database):
    database[1].execute("DELETE FROM user_home_preferences WHERE user_id='author'")
    headers = actor("author")

    r = client.get("/api/me/home-preferences", headers=headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["exists"] is False
    assert data["preset"] == "balanced"
    assert data["onboarded"] is False
    assert "calendar" in data["hidden"]
    assert "explore" in data["hidden"]
    assert "discover" not in data["hidden"]

    save = client.put(
        "/api/me/home-preferences",
        headers=headers,
        json={
            "preset": "minimal",
            "hidden": ["calendar", "leaderboard", "unknown_widget", "calendar"],
            "onboarded": True,
        },
    )
    assert save.status_code == 200, save.text
    saved = save.json()
    assert saved["exists"] is True
    assert saved["preset"] == "minimal"
    assert saved["hidden"] == ["calendar", "leaderboard"]
    assert saved["onboarded"] is True
    assert saved["onboarded_at"] is not None

    r2 = client.get("/api/me/home-preferences", headers=headers)
    assert r2.status_code == 200
    loaded = r2.json()
    assert loaded["exists"] is True
    assert loaded["preset"] == "minimal"
    assert loaded["hidden"] == ["calendar", "leaderboard"]
    assert loaded["onboarded"] is True

    bad = client.put(
        "/api/me/home-preferences",
        headers=headers,
        json={"preset": "not-a-preset", "hidden": []},
    )
    assert bad.status_code == 422


def test_home_preferences_mobile_boundary():
    assert allowed("GET", "/api/me/home-preferences")
    assert allowed("PUT", "/api/me/home-preferences")
    assert not allowed("DELETE", "/api/me/home-preferences")
