import logging
import asyncio
import httpx
from fastapi import APIRouter, Request, BackgroundTasks
from app.config import settings
from app.redis_client import redis_client
from app.conversation import process_conversation
from app.messagebird_client import (
    _get_headers,
    _to_internal_phone,
    BASE_URL,
)

logger = logging.getLogger(__name__)
router = APIRouter()


async def _get_sender_phone(contact_id: str) -> str | None:
    """
    Fetch the sender's phone number from the MessageBird Contacts API.
    Returns the phone in our internal format: whatsapp:+XXXXXXXXXXX

    MessageBird does not include the sender phone directly in the webhook
    payload, so we look it up via the contactId.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{BASE_URL}/contacts/{contact_id}",
                headers=_get_headers(),
            )
            if response.status_code == 200:
                data = response.json()

                # msisdn is returned as an integer, e.g. 447700900000
                msisdn = data.get("msisdn")
                if msisdn:
                    return _to_internal_phone(msisdn)

                # Some contacts expose customPlatformId as fallback
                custom = data.get("customPlatformId", "")
                if custom:
                    return _to_internal_phone(custom)

            logger.warning("Could not get phone for contact %s", contact_id)
            return None
    except Exception as exc:
        logger.error("Error fetching contact %s: %s", contact_id, exc)
        return None


async def _buffer_timeout_handler(phone: str):
    """Waits for buffer timer to expire, then processes combined messages."""
    await asyncio.sleep(settings.INPUT_BUFFER_SECONDS)

    # Wait until the timer key actually expires
    while await redis_client.is_timer_active(phone):
        await asyncio.sleep(0.5)

    messages = await redis_client.get_and_clear_buffer(phone)
    if messages:
        combined_message = " ".join(messages)
        # Retrieve conversation_id stored during inbound webhook handling
        session = await redis_client.get_session(phone) or {}
        conversation_id = session.get("messagebird_conversation_id", "")
        await process_conversation(phone, combined_message, conversation_id=conversation_id)


@router.post("/webhook")
async def messagebird_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives MessageBird Conversations webhooks (JSON, not form-encoded).

    Only processes message.created events with direction=received.
    Returns 200 immediately; heavy processing runs in the background.

    IMPORTANT: MessageBird fires webhooks for *outbound* messages too.
    The direction == "received" guard prevents Albert from replying to
    his own messages and causing an infinite loop.
    """
    try:
        payload = await request.json()
    except Exception:
        logger.warning("Webhook received non-JSON body")
        return {"status": "error", "reason": "invalid_json"}

    event_type = payload.get("type", "")

    # Only handle inbound messages
    if event_type != "message.created":
        return {"status": "ignored", "reason": f"event_type:{event_type}"}

    message = payload.get("message", {})
    conversation = payload.get("conversation", {})

    # Filter out our own outbound messages (critical — prevents infinite loop)
    direction = message.get("direction", "")
    if direction != "received":
        return {"status": "ignored", "reason": "outbound_echo"}

    message_id = message.get("id", "")
    conversation_id = conversation.get("id", "")
    contact_id = conversation.get("contactId", "")
    message_text = message.get("content", {}).get("text", "")

    if not message_text:
        return {"status": "ignored", "reason": "empty_body"}

    # Dedup on message ID
    if message_id and await redis_client.check_dedup(message_id):
        logger.info("Duplicate message %s, ignoring", message_id)
        return {"status": "ignored", "reason": "duplicate"}

    # Resolve sender phone via Contacts API
    sender_phone = await _get_sender_phone(contact_id)
    if not sender_phone:
        logger.error("Could not resolve phone for contact %s", contact_id)
        return {"status": "error", "reason": "phone_resolution_failed"}

    logger.info("Message from %s: %.60s…", sender_phone, message_text)

    # Store conversation_id in Redis so process_conversation can reply faster
    session = await redis_client.get_session(sender_phone) or {}
    session["messagebird_conversation_id"] = conversation_id
    await redis_client.save_session(sender_phone, session)

    # Buffer message and set/reset expiry timer
    await redis_client.buffer_message(sender_phone, message_text)
    await redis_client.set_buffer_timer(sender_phone)

    # Schedule processing (returns 200 immediately)
    background_tasks.add_task(_buffer_timeout_handler, sender_phone)

    return {"status": "ok"}
