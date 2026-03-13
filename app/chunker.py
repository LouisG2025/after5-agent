import re
import random

def chunk_message(text: str) -> list:
    """
    Cleans text (dashes, whitespace) and returns a single coherent bubble.
    Enforces 'No Dashes' rule.
    """
    if not text:
        return []

    # 1. Enforce 'No Dashes' rule
    # Convert ranges like 2-3 to "2 to 3"
    text = re.sub(r'(\d+)\s*[-—]\s*(\d+)', r'\1 to \2', text)
    # Remove any remaining dashes/em-dashes, replace with commas for natural pause
    text = text.replace("—", ",").replace("--", ",").replace("- ", ", ").replace(" -", " ,")
    
    # 2. Cleanup separators if LLM used them
    text = text.replace("|||", " ")
    
    return [text.strip()]


def calculate_typing_delay(text: str) -> float:
    """
    Returns a realistic typing delay (in seconds) based on character count.
    Used for simulating a human typing on WhatsApp.
    """
    # 15 chars per second (quite fast but human)
    delay = len(text) / 15.0
    # Cap delay at 15 seconds total for the single coherent response
    return min(max(2.0, delay), 15.0)

def calculate_reading_delay(text: str) -> float:
    """
    Returns a realistic reading delay based on incoming message length.
    Avg human reads ~25 chars per second.
    """
    if not text:
        return 1.0
    delay = len(text) / 25.0
    return max(1.0, delay)

def calculate_thinking_delay() -> float:
    """
    Returns a random thinking delay for legacy support, 
    but we now prefer reading_delay + typing_delay.
    """
    return random.uniform(2.0, 4.0)
