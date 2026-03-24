func = """

def _compute_scoring_status(session: dict, current_message: str) -> str:
    \"\"\"
    V4: Keyword-based qualification gate.
    All three signals must be present before Albert is allowed to push for booking.
    \"\"\"
    current_state = session.get('state', 'opening')

    if current_state == 'escalation':
        return 'escalate_to_human'

    all_text = ' '.join(
        [m['content'] for m in session.get('history', [])] + [current_message]
    ).lower()

    lead_gen_keywords = [
        'leads', 'enquiries', 'submissions', 'forms', 'ads', 'google', 'meta',
        'facebook', 'instagram', 'referrals', 'organic', 'inbound',
        'calls', 'per month', 'a month', 'a week'
    ]
    has_lead_gen = any(kw in all_text for kw in lead_gen_keywords)

    pain_keywords = [
        'slow', 'missing', 'losing', 'after hours', 'evenings', 'weekends', 'overnight',
        'manual', 'inconsistent', 'going cold', 'cold', 'no one', 'nobody',
        'not following up', 'struggling', 'problem', 'issue', 'gap',
        'nightmare', 'frustrating', 'bottleneck', 'missed', 'taking too long'
    ]
    has_pain = any(kw in all_text for kw in pain_keywords)

    engagement_keywords = [
        'how much', 'cost', 'price', 'how long', 'how does', 'how would', 'what would',
        'integration', 'crm', 'interested', 'looks good', 'sounds good',
        'makes sense', 'want to', 'book', 'call', 'yes', 'yeah', 'exactly'
    ]
    has_engagement = any(kw in all_text for kw in engagement_keywords)

    if has_lead_gen and has_pain and has_engagement:
        return 'push_for_booking'

    return 'continue_discovery'

"""

with open('app/llm.py', 'r', encoding='utf-8') as f:
    content = f.read()

marker = 'tracker = AlbertTracker()'
idx = content.find(marker)
if idx >= 0:
    insert_pos = idx + len(marker)
    new_content = content[:insert_pos] + func + content[insert_pos:]
    with open('app/llm.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('SUCCESS: _compute_scoring_status inserted')
else:
    print('ERROR: marker not found in file')
