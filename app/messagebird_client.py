import logging
import asyncio
import httpx
from app.config import settings
from app.chunker import calculate_typing_delay

logger = logging.getLogger(__name__)

BASE_URL = "https://conversations.messagebird.com/v1"


def _get_headers() -> dict:
    """Return auth headers for MessageBird API."""
    return {
        "Authorization": f"AccessKey {settings.MESSAGEBIRD_API_KEY}",
        "Content-Type": "application/json",
    }


def _to_messagebird_phone(phone: str) -> str:
    """
    Convert our internal phone format to MessageBird format.
    Our system:  whatsapp:+447700900000
    MessageBird: +447700900000
    """
    return phone.replace("whatsapp:", "")


def _to_internal_phone(phone: str) -> str:
    """
    Convert MessageBird phone format to our internal format.
    MessageBird: +447700900000  (or integer 447700900000)
    Our system:  whatsapp:+447700900000
    """
    cleaned = str(phone).strip()
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned
    if not cleaned.startswith("whatsapp:"):
        cleaned = "whatsapp:" + cleaned
    return cleaned


async def send_message(to: str, body: str) -> dict | None:
    """
    Send a WhatsApp message via MessageBird Conversations API /v1/send.
    This automatically creates or resumes the appropriate conversation.

    Args:
        to:   Phone in our internal format (whatsapp:+XXXXXXXXXXX)
        body: Message text to send

    Returns:
        Parsed API response dict, or None on error.
    """
    mb_phone = _to_messagebird_phone(to)

    payload = {
        "to": mb_phone,
        "from": settings.MESSAGEBIRD_CHANNEL_ID,
        "type": "text",
        "content": {"text": body},
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{BASE_URL}/send",
                headers=_get_headers(),
                json=payload,
            )
            if response.status_code in (200, 201, 202):
                logger.info("Message sent to %s: %.50s…", mb_phone, body)
                return response.json()
            else:
                logger.error(
                    "MessageBird send failed: %s — %s",
                    response.status_code,
                    response.text,
                )
                return None
    except Exception as exc:
        logger.error("MessageBird send error: %s", exc)
        return None


async def reply_to_conversation(conversation_id: str, body: str) -> dict | None:
    """
    Reply within an existing MessageBird conversation.
    Prefer this over send_message() when you already have conversation_id
    (e.g. stored in Redis from the inbound webhook) because MessageBird
    doesn't need to look up the conversation.

    Args:
        conversation_id: MessageBird conversation ID
        body:            Message text to send

    Returns:
        Parsed API response dict, or None on error.
    """
    payload = {
        "type": "text",
        "content": {"text": body},
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{BASE_URL}/conversations/{conversation_id}/messages",
                headers=_get_headers(),
                json=payload,
            )
            if response.status_code in (200, 201, 202):
                logger.info(
                    "Reply sent to conversation %s: %.50s…", conversation_id, body
                )
                return response.json()
            else:
                logger.error(
                    "MessageBird reply failed: %s — %s",
                    response.status_code,
                    response.text,
                )
                return None
    except Exception as exc:
        logger.error("MessageBird reply error: %s", exc)
        return None


async def send_chunked_messages(to: str, chunks: list[str]) -> None:
    """
    Send multiple messages with realistic typing delays between them.

    Args:
        to:     Phone in our internal format (whatsapp:+XXXXXXXXXXX)
        chunks: Ordered list of message texts
    """
    for i, chunk in enumerate(chunks):
        if i > 0:
            delay = calculate_typing_delay(chunk)
            await asyncio.sleep(delay)
        await send_message(to, chunk)


async def reply_chunked_messages(conversation_id: str, chunks: list[str]) -> None:
    """
    Reply with multiple messages using a known conversation ID, with typing delays.

    Args:
        conversation_id: MessageBird conversation ID (from inbound webhook)
        chunks:          Ordered list of message texts
    """
    for i, chunk in enumerate(chunks):
        if i > 0:
            delay = calculate_typing_delay(chunk)
            await asyncio.sleep(delay)
        await reply_to_conversation(conversation_id, chunk)
