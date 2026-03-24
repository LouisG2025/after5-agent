auto_close_block = """
        # V4: 24h Session Auto-Close — prevents Albert responding to stale sessions
        last_updated_str = session.get("last_updated")
        if last_updated_str and session.get("state") not in [ConversationState.CONFIRMED, ConversationState.CLOSED]:
            try:
                from datetime import timezone as _tz
                lu_dt = datetime.fromisoformat(last_updated_str.replace("Z", "+00:00"))
                lu_aware = lu_dt if lu_dt.tzinfo else lu_dt.replace(tzinfo=_tz.utc)
                idle_seconds = (datetime.now(_tz.utc) - lu_aware).total_seconds()
                if idle_seconds > 86400:  # 24 hours
                    logger.info("[Conversation] 24h idle session auto-closing for %s", phone)
                    session["state"] = ConversationState.CLOSED
                    session["last_updated"] = datetime.now(_tz.utc).isoformat()
                    await redis_client.save_session(phone, session)
                    await redis_client.clear_generating(phone)
                    return
            except Exception as e:
                logger.warning("[Conversation] 24h auto-close check failed for %s: %s", phone, e)
"""

with open('app/conversation.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Insert after the session initialisation block
marker = '"low_content_count": 0\n            }\n        \n        lead_data'
if marker not in content:
    # Try without \r
    marker = '"low_content_count": 0\r\n            }\r\n        \r\n        lead_data'

idx = content.find('"low_content_count": 0')
if idx >= 0:
    # Find the end of the session block (after the closing brace)
    block_end = content.find('lead_data = session.get', idx)
    if block_end >= 0:
        new_content = content[:block_end] + auto_close_block + content[block_end:]
        with open('app/conversation.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print('SUCCESS: 24h auto-close inserted')
    else:
        print('ERROR: could not find lead_data insertion point')
else:
    print('ERROR: session init marker not found')
