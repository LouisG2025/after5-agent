import sys
import os
sys.path.append(os.getcwd())
from app.chunker import chunk_message, calculate_typing_delay

test_cases = [
    "Hey Sarah, hope you're having a good one. Was this regarding Pulse Media?",
    "Nice one. Here is the link: https://calendly.com/after5/free-discovery-call. Let me know if that works.",
    "Yeah that's exactly what we build. Ps Louis handles all the strategy calls.",
    "Haha nice.",
    "This is a very long message that shouldn't be split because it's just one idea but it has some punctuation like a dot here. And another one here. But overall it's just one thought about AI.",
]

for i, test in enumerate(test_cases):
    print(f"\n--- Test Case {i+1} ---")
    print(f"Input: {test}")
    chunks = chunk_message(test)
    for j, chunk in enumerate(chunks):
        delay = calculate_typing_delay(chunk)
        print(f"  Chunk {j+1} [{delay:.2f}s]: {chunk}")
