import asyncio
import os
import sys
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import httpx

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.stt import process_voice_note_from_media_id

class TestSTTPipeline(unittest.IsolatedAsyncioTestCase):

    @patch("app.stt.httpx.AsyncClient")
    async def test_stt_pipeline_success(self, mock_client_class):
        """Test full successful STT pipeline mock."""
        # 1. Mock Graph API response (media URL)
        mock_graph_resp = MagicMock()
        mock_graph_resp.status_code = 200
        mock_graph_resp.json.return_value = {"url": "https://cdn.whatsapp.net/media/123"}
        
        # 2. Mock Media Download response (audio bytes)
        mock_download_resp = MagicMock()
        mock_download_resp.status_code = 200
        mock_download_resp.content = b"fake-audio-bytes"
        
        # 3. Mock Whisper API response (transcription)
        mock_whisper_resp = MagicMock()
        mock_whisper_resp.status_code = 200
        mock_whisper_resp.json.return_value = {"text": "Hello, this is a test voice note."}
        
        # Setup the client
        mock_client = AsyncMock()
        mock_client.get.side_effect = [mock_graph_resp, mock_download_resp]
        mock_client.post.return_value = mock_whisper_resp
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        result = await process_voice_note_from_media_id("media_123")
        
        self.assertEqual(result, "Hello, this is a test voice note.")
        self.assertEqual(mock_client.get.call_count, 2)
        self.assertEqual(mock_client.post.call_count, 1)

    @patch("app.stt.httpx.AsyncClient")
    async def test_stt_pipeline_download_failure(self, mock_client_class):
        """Test STT pipeline failure on download."""
        mock_graph_resp = MagicMock()
        mock_graph_resp.status_code = 200
        mock_graph_resp.json.return_value = {"url": "https://cdn.whatsapp.net/media/123"}
        
        mock_download_resp = MagicMock()
        mock_download_resp.status_code = 404 # Not found
        
        mock_client = AsyncMock()
        mock_client.get.side_effect = [mock_graph_resp, mock_download_resp]
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        result = await process_voice_note_from_media_id("media_123")
        
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
