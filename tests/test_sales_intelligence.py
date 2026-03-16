import asyncio
import os
import sys
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.signals import detect_interest_level, detect_personality_type, get_approach_instructions
from app.conversation import build_enhanced_context
from app.models import ConversationState

class TestSalesIntelligence(unittest.IsolatedAsyncioTestCase):

    def test_interest_level_high(self):
        """Test high interest detection."""
        message = "This sounds exactly like what we need. How do we get started?"
        level = detect_interest_level(message)
        self.assertEqual(level, "high")

    def test_interest_level_low(self):
        """Test low interest detection."""
        message = "ok"
        level = detect_interest_level(message)
        self.assertEqual(level, "low")

    def test_personality_driver(self):
        """Test driver personality (short, direct)."""
        history = ["How much?", "Can it do CRM?", "Send link."]
        personality = detect_personality_type(history)
        self.assertEqual(personality, "driver")

    def test_personality_analytical(self):
        """Test analytical personality (long, detailed, questions)."""
        history = [
            "What is the average latency for the WhatsApp Cloud API integration in the Dubai region specifically?",
            "How do you handle data residency for GDPR compliance within the ApexAI group architecture?"
        ]
        personality = detect_personality_type(history)
        self.assertEqual(personality, "analytical")

    @patch("app.conversation.redis_client")
    @patch("app.conversation.llm_client")
    async def test_build_enhanced_context_rag_injection(self, mock_llm, mock_redis):
        """Verify that RAG context is correctly injected based on state."""
        mock_llm.build_context = AsyncMock(return_value=[{"role": "system", "content": "Base Prompt"}])
        mock_redis.get = AsyncMock(return_value="RAG Training Module Content")

        session = {
            "state": ConversationState.OPENING,
            "history": []
        }
        lead_data = {"name": "John"}
        message = "Hey"

        messages = await build_enhanced_context(session, lead_data, message)

        # check if rag content is in system message
        self.assertIn("RAG Training Module Content", messages[0]["content"])
        self.assertIn("--- SALES TRAINING MODULE ---", messages[0]["content"])
        self.assertIn("CURRENT BANT STATUS", messages[0]["content"]) # Included in instruction

    @patch("app.conversation.redis_client")
    @patch("app.conversation.llm_client")
    async def test_objection_rag_injection(self, mock_llm, mock_redis):
        """Verify that objection RAG is injected when budget mentioned."""
        mock_llm.build_context = AsyncMock(return_value=[{"role": "system", "content": "Base Prompt"}])
        mock_redis.get = AsyncMock(return_value="Objection Handling Training")

        session = {
            "state": ConversationState.DISCOVERY,
            "history": []
        }
        lead_data = {}
        message = "It sounds a bit expensive"

        await build_enhanced_context(session, lead_data, message)

        # Ensure redis.get was called with objection key
        mock_redis.get.assert_called_with("rag:sales:objections")

if __name__ == "__main__":
    unittest.main()
