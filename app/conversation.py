import asyncio
from app.config import settings
from app.llm import llm_client
from app.redis_client import redis_client
from app.supabase_client import supabase_client
from app.messagebird_client import send_message, send_chunked_messages, reply_to_conversation, reply_chunked_messages, send_typing_indicator
from app.chunker import chunk_message, calculate_typing_delay
from app.state_machine import check_transition
from app.bant import extract_bant
from app.models import ConversationState
from typing import Dict, Any

from app.tracker import AlbertTracker

tracker = AlbertTracker()

async def process_conversation(phone: str, message: str, conversation_id: str = "", source: str = "text"):
    """Main conversation engine logic."""
    print(f"\n[Conversation] Starting processing for {phone} (via {source}): '{message[:100]}...'", flush=True)

    # 2. Get session and lead data
    session = await redis_client.get_session(phone)
    if not session:
        # Try to find lead in Supabase via Tracker
        lead = tracker.get_lead_by_phone(phone)
        if not lead:
            lead = tracker.create_lead(phone=phone)
            
        session = {
            "state": ConversationState.OPENING,
            "history": [],
            "turn_count": 0,
            "lead_data": lead or {"phone": phone}
        }
    
    lead_data = session.get("lead_data", {})
    lead_id = lead_data.get("id")

    # 3. Log inbound message (already done in webhook.py for raw messages, 
    # but process_conversation might be called for combined messages)
    # The requirement says "log every time a lead sends Albert a WhatsApp message"
    # and "Call every time Albert sends a WhatsApp reply".
    # Since webhook.py logs the raw inbound, and process_conversation handles the AI response,
    # we should log the AI response here.

    # 3.1 Show typing and thinking delay
    print(f"[Conversation] Simulation: Human delay + Typing indicator for {phone}", flush=True)
    await send_typing_indicator(phone)
    # Simulate thinking time (1.5s to 3s)
    await asyncio.sleep(2.0)

    # 4. Build context and call LLM
    print(f"[Conversation] Calling LLM for {phone} using model: {settings.OPENROUTER_PRIMARY_MODEL}", flush=True)
    messages = await llm_client.build_context(session, lead_data, message)
    response_text = await llm_client.call_llm(
        messages,
        model=settings.OPENROUTER_PRIMARY_MODEL,
        lead_id=lead_id,
        conversation_state=session["state"],
        phone=phone,
        company=lead_data.get("company", "")
    )
    print(f"[Conversation] AI Response received for {phone}: '{response_text[:100]}...'", flush=True)

    # 5. Chunk and send response
    chunks = chunk_message(response_text)

    # Add initial typing delay for the first message to feel human
    if chunks:
        initial_delay = calculate_typing_delay(chunks[0][:100])
        await asyncio.sleep(initial_delay)

    if len(chunks) == 1:
        # Single message
        if conversation_id:
            await reply_to_conversation(conversation_id, chunks[0])
        else:
            await send_message(phone, chunks[0])
    else:
        # Multiple chunks
        if conversation_id:
            await reply_chunked_messages(conversation_id, chunks)
        else:
            await send_chunked_messages(phone, chunks)

    # 6. Update session history
    session["history"].append({"role": "user", "content": message})
    session["history"].append({"role": "assistant", "content": response_text})
    session["history"] = session["history"][-10:]
    session["turn_count"] += 1

    # 7. Log outbound messages to Tracker
    for chunk in chunks:
        tracker.log_outbound(lead_id, chunk)

    # 8. Check for state transition
    new_state = check_transition(session["state"], session)
    if new_state and new_state != session["state"]:
        session["state"] = new_state
        
        # Mapping to Dashboard states
        state_map = {
            ConversationState.OPENING: "Opening",
            ConversationState.DISCOVERY: "Discovery",
            ConversationState.QUALIFICATION: "Qualification",
            ConversationState.BOOKING: "Booking Push",
            ConversationState.ESCALATION: "Escalation",
            ConversationState.CONFIRMED: "Confirmed",
            ConversationState.CLOSED: "In Progress"
        }
        dashboard_state = state_map.get(new_state, "Opening")
        
        # Update dashboard state
        tracker.update_state(lead_id, dashboard_state)

    # 9. Save session
    await redis_client.save_session(phone, session)

    # 10. Background BANT extraction
    asyncio.create_task(extract_bant(phone, session["history"]))
