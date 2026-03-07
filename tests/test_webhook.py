"""
Tests for the MessageBird webhook endpoint.
"""
import json
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def _mb_payload(
    message_text="Hello!",
    direction="received",
    event_type="message.created",
    message_id="msg_abc123",
    conversation_id="conv_xyz789",
    contact_id="contact_111",
):
    """Helper to build a MessageBird webhook payload."""
    return {
        "type": event_type,
        "conversation": {
            "id": conversation_id,
            "contactId": contact_id,
        },
        "message": {
            "id": message_id,
            "conversationId": conversation_id,
            "direction": direction,
            "type": "text",
            "content": {"text": message_text},
        },
    }


@patch("app.webhook.redis_client")
@patch("app.webhook._get_sender_phone", new_callable=AsyncMock)
def test_webhook_valid(mock_get_phone, mock_redis):
    """Inbound message with direction=received should be accepted."""
    mock_get_phone.return_value = "whatsapp:+1234567890"
    mock_redis.check_dedup = AsyncMock(return_value=False)
    mock_redis.get_session = AsyncMock(return_value={})
    mock_redis.save_session = AsyncMock()
    mock_redis.buffer_message = AsyncMock()
    mock_redis.set_buffer_timer = AsyncMock()

    response = client.post(
        "/webhook",
        content=json.dumps(_mb_payload()),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@patch("app.webhook.redis_client")
@patch("app.webhook._get_sender_phone", new_callable=AsyncMock)
def test_webhook_ignores_outbound(mock_get_phone, mock_redis):
    """Outbound message echoes (direction=sent) must be silently ignored."""
    response = client.post(
        "/webhook",
        content=json.dumps(_mb_payload(direction="sent")),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert response.json()["reason"] == "outbound_echo"


def test_webhook_ignores_non_message_event():
    """Non-message.created events should be ignored."""
    response = client.post(
        "/webhook",
        content=json.dumps(_mb_payload(event_type="conversation.created")),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


@patch("app.webhook.redis_client")
@patch("app.webhook._get_sender_phone", new_callable=AsyncMock)
def test_webhook_dedup(mock_get_phone, mock_redis):
    """Duplicate message IDs should be silently dropped."""
    mock_get_phone.return_value = "whatsapp:+1234567890"
    mock_redis.check_dedup = AsyncMock(return_value=True)

    response = client.post(
        "/webhook",
        content=json.dumps(_mb_payload()),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert response.json()["reason"] == "duplicate"


def test_form_webhook():
    payload = {
        "name": "John Doe",
        "phone": "+1234567890",
        "company": "ACME Inc",
    }
    response = client.post("/form-webhook", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "outreach_scheduled"
