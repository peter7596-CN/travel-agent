from app.concur_client import ConcurClient, ConcurConfig


def test_mock_mode_without_credentials():
    client = ConcurClient(ConcurConfig())

    profile = client.get_traveler_profile("ceo@example.com")

    assert profile["email"] == "ceo@example.com"
    assert profile["seat_preference"] == "Aisle"


def test_refresh_token_flow_is_used_for_api_calls(monkeypatch):
    cfg = ConcurConfig(
        base_url="https://www.concursolutions.com",
        client_id="cid",
        client_secret="csecret",
        refresh_token="rtok",
        token_url="https://us2.api.concursolutions.com/oauth2/v0/token",
    )
    client = ConcurClient(cfg)

    calls: list[tuple[str, str, dict | None]] = []

    def fake_request_json(method: str, url: str, payload=None):
        calls.append((method, url, payload))
        if "travelprofile" in url:
            return {"email": "ceo@example.com", "seat_preference": "Window"}
        return {"ok": True}

    monkeypatch.setattr(client, "_request_json", fake_request_json)

    result = client.get_traveler_profile("ceo@example.com")

    assert result["seat_preference"] == "Window"
    assert calls and calls[0][0] == "GET"
    assert "travelprofile" in calls[0][1]
