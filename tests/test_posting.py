"""Integration tests with mocked HTTP responses using respx."""

from fastapi.testclient import TestClient
import pytest
import respx
import httpx

from app.config import settings
from app.main import app

client = TestClient(app)

SAMPLE_MESSAGE = "Check out our new update https://example.com/releases/v1"


@pytest.fixture(autouse=True)
def configure_credentials(monkeypatch):
    """Ensure all credentials have test values by default."""
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "mock_telegram_token")
    monkeypatch.setattr(settings, "TELEGRAM_CHANNEL", "@mockchannel")
    monkeypatch.setattr(settings, "MASTODON_BASE_URL", "https://mastodon.social")
    monkeypatch.setattr(settings, "MASTODON_TOKEN", "mock_mastodon_token")
    monkeypatch.setattr(settings, "BLUESKY_HANDLE", "test.bsky.social")
    monkeypatch.setattr(settings, "BLUESKY_APP_PASSWORD", "mock-app-password")
    monkeypatch.setattr(settings, "GITHUB_TOKEN", "mock_github_token")
    monkeypatch.setattr(settings, "PASTEEE_API_KEY", "mock_pasteee_key")
    monkeypatch.setattr(settings, "NTFY_TOPIC", "mock_topic")


def mock_all_platforms_success(respx_mock):
    """Register successful mock responses for all 6 platforms."""
    # 1. Telegram
    respx_mock.post(
        f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    ).respond(
        status_code=200,
        json={"ok": True, "result": {"message_id": 1001}},
    )
    # 2. Mastodon
    respx_mock.post("https://mastodon.social/api/v1/statuses").respond(
        status_code=200,
        json={"url": "https://mastodon.social/@user/1234567890"},
    )
    # 3. Bluesky
    respx_mock.post("https://bsky.social/xrpc/com.atproto.server.createSession").respond(
        status_code=200,
        json={
            "accessJwt": "mock_jwt_token_header_payload_sig",
            "did": "did:plc:mockdid12345",
            "handle": "test.bsky.social",
        },
    )
    respx_mock.post("https://bsky.social/xrpc/com.atproto.repo.createRecord").respond(
        status_code=200,
        json={"uri": "at://did:plc:mockdid12345/app.bsky.feed.post/3abcxyz123"},
    )
    # 4. GitHub Gist
    respx_mock.post("https://api.github.com/gists").respond(
        status_code=201,
        json={"html_url": "https://gist.github.com/testuser/mockgistid123"},
    )
    # 5. Paste.ee
    respx_mock.post("https://api.paste.ee/v1/pastes").respond(
        status_code=200,
        json={
            "id": "mockpaste123",
            "link": "https://paste.ee/p/mockpaste123",
            "success": True,
        },
    )
    # 6. ntfy.sh
    respx_mock.post("https://ntfy.sh").respond(
        status_code=200,
        json={
            "id": "mockntfy123",
            "topic": "mock_topic",
            "message": SAMPLE_MESSAGE,
        },
    )


@respx.mock
def test_all_platforms_succeed(respx_mock):
    """Test scenario (a): all 6 platforms post successfully."""
    mock_all_platforms_success(respx_mock)

    response = client.post("/posting", json={"message": SAMPLE_MESSAGE})
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert len(data["results"]) == 6

    expected_urls = {
        "telegram": "https://t.me/mockchannel/1001",
        "mastodon": "https://mastodon.social/@user/1234567890",
        "bluesky": "https://bsky.app/profile/test.bsky.social/post/3abcxyz123",
        "gist": "https://gist.github.com/testuser/mockgistid123",
        "pasteee": "https://paste.ee/p/mockpaste123",
        "ntfy": "https://ntfy.sh/mock_topic",
    }

    for item in data["results"]:
        pname = item["platform"]
        assert pname in expected_urls
        assert item["status"] == "success"
        assert item["posted_url"] == expected_urls[pname]
        assert item["public_access"] is True
        assert item["date"] is not None
        assert item["time"] is not None
        assert item["error"] is None


@respx.mock
def test_one_platform_fails_with_401_others_succeed(respx_mock):
    """Test scenario (b): one platform returns 401, others succeed; overall success is True."""
    mock_all_platforms_success(respx_mock)

    # Override Paste.ee with a 401 Unauthorized
    respx_mock.post("https://api.paste.ee/v1/pastes").respond(
        status_code=401,
        text='{"errors":[{"message":"Invalid application key.","code":1}],"success":false}',
    )

    response = client.post("/posting", json={"message": SAMPLE_MESSAGE})
    assert response.status_code == 200
    data = response.json()

    # Still overall success because 5 platforms succeeded
    assert data["success"] is True
    assert len(data["results"]) == 6

    results_by_platform = {r["platform"]: r for r in data["results"]}

    # Paste.ee should have failed
    pasteee_res = results_by_platform["pasteee"]
    assert pasteee_res["status"] == "failed"
    assert pasteee_res["posted_url"] is None
    assert pasteee_res["public_access"] is False
    assert pasteee_res["date"] is None
    assert pasteee_res["time"] is None
    assert "401" in pasteee_res["error"]

    # Other 5 platforms must have succeeded
    for pname in ["telegram", "mastodon", "bluesky", "gist", "ntfy"]:
        assert results_by_platform[pname]["status"] == "success"
        assert results_by_platform[pname]["posted_url"] is not None


@respx.mock
def test_missing_credential_produces_failed_result_with_clear_error(monkeypatch, respx_mock):
    """Test scenario (c): missing credential fails gracefully without crashing."""
    mock_all_platforms_success(respx_mock)

    # Empty Paste.ee credential
    monkeypatch.setattr(settings, "PASTEEE_API_KEY", "")

    response = client.post("/posting", json={"message": SAMPLE_MESSAGE})
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    results_by_platform = {r["platform"]: r for r in data["results"]}

    pasteee_res = results_by_platform["pasteee"]
    assert pasteee_res["status"] == "failed"
    assert "PASTEEE_API_KEY not configured" in pasteee_res["error"]
    assert pasteee_res["public_access"] is False

    # Other platforms still succeeded
    assert results_by_platform["telegram"]["status"] == "success"
    assert results_by_platform["gist"]["status"] == "success"
    assert results_by_platform["ntfy"]["status"] == "success"


@respx.mock
def test_all_platforms_fail_returns_success_false(respx_mock):
    """Test scenario (d): all platforms fail, response has success=False."""
    respx_mock.post(f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage").respond(
        status_code=500, text="Internal Server Error"
    )
    respx_mock.post("https://mastodon.social/api/v1/statuses").respond(
        status_code=500, text="Internal Server Error"
    )
    respx_mock.post("https://bsky.social/xrpc/com.atproto.server.createSession").respond(
        status_code=500, text="Internal Server Error"
    )
    respx_mock.post("https://api.github.com/gists").respond(
        status_code=500, text="Internal Server Error"
    )
    respx_mock.post("https://api.paste.ee/v1/pastes").respond(
        status_code=500, text="Internal Server Error"
    )
    respx_mock.post("https://ntfy.sh").respond(
        status_code=500, text="Internal Server Error"
    )

    response = client.post("/posting", json={"message": SAMPLE_MESSAGE})
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is False
    assert len(data["results"]) == 6
    for item in data["results"]:
        assert item["status"] == "failed"
        assert item["posted_url"] is None
        assert item["public_access"] is False
        assert item["error"] is not None
