import os
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from apeirograph_brain.cli import main
from apeirograph_brain.ollama_client import OllamaClient, OllamaConnectionError
from apeirograph_brain.settings import get_ollama_settings


class OllamaSettingsTests(unittest.TestCase):
    def test_default_settings_are_stable_for_mvp(self):
        settings = get_ollama_settings({})
        self.assertEqual(settings.base_url, "http://localhost:11434")
        self.assertEqual(settings.model, "llama3.2:1b")
        self.assertEqual(settings.timeout_seconds, 30)


class OllamaClientTests(unittest.TestCase):
    def test_generate_returns_text_from_ollama_json(self):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": "Stable tonic gravity."}

        mock_session = Mock()
        mock_session.post.return_value = mock_response

        client = OllamaClient(session=mock_session)
        result = client.generate("Explain this chord.")

        self.assertEqual(result, "Stable tonic gravity.")
        mock_session.post.assert_called_once()

    def test_generate_wraps_transport_failures(self):
        mock_session = Mock()
        mock_session.post.side_effect = RuntimeError("boom")

        client = OllamaClient(session=mock_session)

        with self.assertRaises(OllamaConnectionError):
            client.generate("test")


class OllamaCliTests(unittest.TestCase):
    def test_main_uses_grounded_default_system_prompt(self):
        output = StringIO()

        with patch("apeirograph_brain.cli.OllamaClient.generate", return_value="C-E-G") as mock_generate:
            with redirect_stdout(output):
                result = main(["--prompt", "Explain a C major triad in one short sentence."])

        self.assertEqual(result, 0)
        self.assertIn("C major triad = C-E-G", mock_generate.call_args[1]["system"])

    def test_main_handles_keyboard_interrupt_cleanly(self):
        output = StringIO()

        with patch("apeirograph_brain.cli.OllamaClient.generate", side_effect=KeyboardInterrupt):
            with redirect_stdout(output):
                result = main(["--prompt", "test"])

        self.assertEqual(result, 130)
        self.assertIn("Request cancelled.", output.getvalue())


if __name__ == "__main__":
    unittest.main()
