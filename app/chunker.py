import re

def chunk_message(text: str) -> list:
    """
    Cleans text (dashes, whitespace) and splits into max 3 chunks using |||.
    Enforces 'No Dashes' rule and 3-chunk maximum.
    """
    if not text:
        return []

    # 1. Enforce 'No Dashes' rule
    # Convert ranges like 2-3 to "2 to 3"
    text = re.sub(r'(\d+)\s*[-—]\s*(\d+)', r'\1 to \2', text)
    # Remove any remaining dashes/em-dashes, replace with commas for natural pause
    text = text.replace("—", ",").replace("--", ",").replace("- ", ", ").replace(" -", " ,")
    
    # 2. Split by |||
    if "|||" in text:
        chunks = [c.strip() for c in text.split("|||") if c.strip()]
    else:
        # Fallback: split by sentences if no ||| provided by LLM
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        chunks = [s.strip() for s in sentences if s.strip()]
    
    # 3. Enforce 3-chunk maximum
    if len(chunks) > 3:
        # Merge everything from index 2 onwards into the 3rd chunk
        merged_tail = " ".join(chunks[2:])
        chunks = chunks[:2] + [merged_tail]
        
    return chunks if chunks else [text.strip()]


def calculate_typing_delay(text: str) -> float:
    """
    Returns a realistic typing delay (in seconds) based on character count.
    Used for simulating a human typing on WhatsApp.
    """
    # Avg: 200 CPM (chars per minute) = ~3.3 chars per second
    # We use a slightly faster 8 chars/sec to keep UX snappy
    delay = len(text) / 8.0
    # Cap delay at 4 seconds per message
    return min(delay, 4.0)

def calculate_thinking_delay() -> float:
    """
    Returns a random thinking delay for the FIRST chunk.
    """
    import random
    return random.uniform(3.0, 5.0)
