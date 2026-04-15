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

from apeirograph_brain.cli import build_default_system_prompt, main
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
    def test_main_answers_common_chord_note_queries_deterministically(self):
        cases = [
            ("Tell me the notes that makeup A minor chord", "A minor", ["A", "C", "E"]),
            ("Suppose we change C major to a sus2 chord -- what are the notes then?", "C sus2", ["C", "D", "G"]),
            ("Tell me which notes comprise A69", "A69", ["A", "C#", "E", "F#", "B"]),
            ("Tell me the notes in the chord Am6", "Am6", ["A", "C", "E", "F#"]),
            ("Tell me the notes in Eb7sus4", "Eb7sus4", ["Eb", "Ab", "Bb", "Db"]),
            ("Tell me the notes in Eb7(#9)", "Eb7(#9)", ["Eb", "G", "Bb", "Db", "F#"]),
            ("Tell me the notes in C#m7b5", "C#m7b5", ["C#", "E", "G", "B"]),
            ("Tell me the notes in C#dim", "C#dim", ["C#", "E", "G"]),
            ("Tell me the notes in C#dim7", "C#dim7", ["C#", "E", "G", "A#"]),
            ("Tell me the notes in G13", "G13", ["G", "B", "D", "F", "E"]),
        ]

        for prompt, chord_name, expected_notes in cases:
            with self.subTest(prompt=prompt):
                output = StringIO()
                with patch("apeirograph_brain.cli.OllamaClient.generate", side_effect=AssertionError("model should not be called")):
                    with redirect_stdout(output):
                        result = main(["--prompt", prompt])

                self.assertEqual(result, 0)
                rendered = output.getvalue().strip()
                self.assertIn(chord_name, rendered)
                for note in expected_notes:
                    self.assertIn(note, rendered)

    def test_default_system_prompt_includes_suspended_examples(self):
        system_prompt = build_default_system_prompt()
        self.assertIn("C sus2 chord = C-D-G.", system_prompt)
        self.assertIn("A sus2 chord = A-B-E.", system_prompt)

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
