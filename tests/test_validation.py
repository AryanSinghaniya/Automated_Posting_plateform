"""Validation tests for the /posting endpoint."""

from fastapi.testclient import TestClient
import pytest

from app.main import app

client = TestClient(app)


def test_valid_message():
    """Valid message with exactly one link must pass validation."""
    response = client.post(
        "/posting",
        json={"message": "Announcing our new feature! https://example.com/blog/feature"},
    )
    # The request passes schema validation and reaches the service (returning 200)
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "results" in data
    assert len(data["results"]) == 6


def test_empty_message():
    """Empty message or whitespace-only message must return 422."""
    response = client.post("/posting", json={"message": ""})
    assert response.status_code == 422
    assert "Message cannot be empty." in response.text

    response_ws = client.post("/posting", json={"message": "   "})
    assert response_ws.status_code == 422
    assert "Message cannot be empty." in response_ws.text


def test_over_200_characters():
    """Message over 200 characters must return 422."""
    long_text = "x" * 185 + " https://example.com"
    assert len(long_text) > 200
    response = client.post("/posting", json={"message": long_text})
    assert response.status_code == 422
    assert "Message exceeds maximum length of 200 characters" in response.text


def test_no_link():
    """Message without any link must return 422."""
    response = client.post(
        "/posting",
        json={"message": "Hello world without any link in the body"},
    )
    assert response.status_code == 422
    assert "Message must contain exactly one link (found 0)." in response.text


def test_two_links():
    """Message with more than one link must return 422."""
    response = client.post(
        "/posting",
        json={"message": "See https://first.com and also https://second.com"},
    )
    assert response.status_code == 422
    assert "Message must contain exactly one link (found 2)." in response.text


def test_malformed_url():
    """Message with an invalid/malformed URL must return 422."""
    response = client.post(
        "/posting",
        json={"message": "Here is an invalid url http://:80"},
    )
    assert response.status_code == 422
    assert "Invalid URL" in response.text
