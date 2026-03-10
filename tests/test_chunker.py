from app.chunker import chunk_message, calculate_typing_delay

def test_short_message():
    text = "Hello, how are you?"
    chunks = chunk_message(text)
    assert len(chunks) == 1
    assert chunks[0] == text

def test_chunk_marker():
    text = "First thought. ||| Second thought."
    chunks = chunk_message(text)
    assert len(chunks) == 2
    assert chunks[0] == "First thought."
    assert chunks[1] == "Second thought."

def test_sentence_splitting():
    text = "This is the first sentence. This is the second sentence. This is the third sentence."
    chunks = chunk_message(text)
    assert len(chunks) == 3
    assert chunks[0] == "This is the first sentence."

def test_typing_delay():
    delay = calculate_typing_delay("Small text")
    assert 1.0 <= delay <= 4.0
    
    delay_long = calculate_typing_delay("A very very long text that should take more time to type naturally on a mobile keyboard during a simulated conversation.")
    assert delay_long > delay

if __name__ == "__main__":
    test_short_message()
    test_chunk_marker()
    test_sentence_splitting()
    test_typing_delay()
    print("All tests passed!")
