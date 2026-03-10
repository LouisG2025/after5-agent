import re
import random
from app.config import settings


def chunk_message(text: str) -> list[str]:
    """
    Split an LLM response into multiple WhatsApp messages.
    
    Priority order:
    1. If text contains ||| separators (from LLM), split on those
    2. If text contains [CHUNK] markers (legacy), split on those
    3. If text is short enough (under 160 chars), return as single message
    4. If text is long but has no markers, split at natural sentence boundaries
    
    Rules:
    - Maximum 3 chunks per response
    - Strip empty chunks
    - Each chunk must be non-empty after stripping
    - Never split mid-sentence
    - FAIL-SAFE: Programmatically remove dashes/hyphens
    """
    
    # Fail-safe: Remove all dashes and hyphens (user-requested strict rule)
    # Replacing with a space or nothing depending on context isn't perfect, 
    # but the prompt handles the "to" conversion. This is to catch accidental ones.
    text = text.replace(" - ", ", ").replace("-", " ")
    
    # Step 1: Check for ||| separators (primary method — LLM outputs these)
    if "|||" in text:
        chunks = [chunk.strip() for chunk in text.split("|||") if chunk.strip()]
        # Enforce max 3 chunks
        if len(chunks) > 3:
            # Merge the extras into the last chunk
            chunks = chunks[:2] + [" ".join(chunks[2:])]
        return chunks if chunks else [text.strip()]
    
    # Step 2: Check for [CHUNK] markers (legacy/fallback)
    if "[CHUNK]" in text:
        chunks = [chunk.strip() for chunk in text.split("[CHUNK]") if chunk.strip()]
        if len(chunks) > 3:
            chunks = chunks[:2] + [" ".join(chunks[2:])]
        return chunks if chunks else [text.strip()]
    
    # Step 3: Split at natural sentence boundaries (. or ?)
    # This makes it feel more like a human typing multiple messages
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    
    # Filter out empty strings
    chunks = [s.strip() for s in sentences if s.strip()]
    
    # If no punctuation was found or it's just one chunk, return as is
    if len(chunks) <= 1:
        return [text.strip()]
        
    # Enforce max 3 chunks for flow safety
    if len(chunks) > 3:
        # Keep first two, merge the rest into the third
        chunks = [chunks[0], chunks[1], " ".join(chunks[2:])]
        
    return chunks


def _split_at_sentences(text: str) -> list[str]:
    """
    Split long text at sentence boundaries into 2-3 chunks.
    Each chunk should be 1-3 sentences.
    """
    # Split on sentence-ending punctuation followed by a space
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    
    if len(sentences) <= 2:
        return [text.strip()]
    
    # For 3-4 sentences, split into 2 chunks
    if len(sentences) <= 4:
        mid = len(sentences) // 2
        chunk1 = " ".join(sentences[:mid])
        chunk2 = " ".join(sentences[mid:])
        return [chunk1, chunk2]
    
    # For 5+ sentences, split into 3 chunks
    third = len(sentences) // 3
    chunk1 = " ".join(sentences[:third])
    chunk2 = " ".join(sentences[third:third*2])
    chunk3 = " ".join(sentences[third*2:])
    return [chunk1, chunk2, chunk3]


def calculate_typing_delay(text: str) -> float:
    """
    Calculate a realistic typing delay for a message.
    
    Based on message length with some randomness to feel natural.
    - ~0.03 seconds per character
    - Minimum 1.0 seconds
    - Maximum 3.5 seconds
    - Add small random jitter (±0.3s)
    """
    base_delay = len(text) * settings.TYPING_DELAY_PER_CHAR
    jitter = random.uniform(-0.3, 0.3)
    delay = base_delay + jitter
    return max(1.0, min(3.5, delay))
