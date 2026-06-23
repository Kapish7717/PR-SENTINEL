import hmac
import hashlib
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from webhook import app

# Override webhook secret after importing app to avoid .env file values overwriting it
os.environ["GITHUB_WEBHOOK_SECRET"] = "supersecret"

client = TestClient(app)

@patch("webhook.review_pr")
def test_webhook_ignored_events(mock_review):
    payload = b'{"zen": "Hello world", "action": "opened"}'
    signature = "sha256=" + hmac.new(b"supersecret", payload, hashlib.sha256).hexdigest()
    headers = {
        "X-GitHub-Event": "ping",
        "X-Hub-Signature-256": signature
    }
    
    response = client.post("/webhook", content=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert mock_review.call_count == 0

@patch("webhook.review_pr")
def test_webhook_invalid_signature(mock_review):
    headers = {
        "X-GitHub-Event": "pull_request",
        "X-Hub-Signature-256": "sha256=wrongsignature"
    }
    payload = b'{"action": "opened"}'
    response = client.post("/webhook", content=payload, headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid signature"

@patch("webhook.review_pr")
def test_webhook_valid_pr_event(mock_review):
    payload = (
        b'{"action": "opened", '
        b'"pull_request": {"number": 12, "head": {"sha": "abcdef12345"}}, '
        b'"repository": {"full_name": "owner/repo"}, '
        b'"installation": {"id": 999}}'
    )
    signature = "sha256=" + hmac.new(b"supersecret", payload, hashlib.sha256).hexdigest()
    headers = {
        "X-GitHub-Event": "pull_request",
        "X-Hub-Signature-256": signature
    }
    response = client.post("/webhook", content=payload, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"status": "review started"}
    
    mock_review.assert_called_once_with(
        pr_id=12,
        repo="owner/repo",
        commit_sha="abcdef12345",
        installation_id=999
    )
