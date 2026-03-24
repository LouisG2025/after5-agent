with open('app/conversation.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The bug: line 62 has 'lead_data' without proper indentation
bad = 'logger.warning("[Conversation] 24h auto-close check failed for %s: %s", phone, e)\nlead_data = session.get("lead_data", {})'
good = 'logger.warning("[Conversation] 24h auto-close check failed for %s: %s", phone, e)\n\n        lead_data = session.get("lead_data", {})'

if bad in content:
    content = content.replace(bad, good)
    with open('app/conversation.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: fixed indentation')
else:
    # Try with CRLF
    bad2 = bad.replace('\n', '\r\n')
    good2 = good.replace('\n', '\r\n')
    if bad2 in content:
        content = content.replace(bad2, good2)
        with open('app/conversation.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print('SUCCESS (CRLF): fixed indentation')
    else:
        # Show context around line 62
        lines = content.split('\n')
        for i, line in enumerate(lines[58:68], start=59):
            print(f'{i}: {repr(line)}')
        print('ERROR: pattern not found')
