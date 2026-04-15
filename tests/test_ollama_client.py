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
            ("Tell me the notes in Bb major chord", "Bb major", ["Bb", "D", "F"]),
            ("Tell me the notes in A dominant 7 chord", "A dominant 7", ["A", "C#", "E", "G"]),
            ("Tell me the notes in Abdim7", "Abdim7", ["Ab", "B", "D", "F"]),
            ("Tell me the notes in Absus4", "Ab sus4", ["Ab", "Db", "Eb"]),
            ("Tell me the notes in Bbmaj7", "Bbmaj7", ["Bb", "D", "F", "A"]),
            ("Tell me the notes in Badd9", "Badd9", ["B", "D#", "F#", "C#"]),
            ("Tell me the notes in C11", "C11", ["C", "E", "G", "Bb", "D", "F"]),
            ("Tell me the notes in C13", "C13", ["C", "E", "G", "Bb", "D", "F", "A"]),
            ("Tell me the notes in C13(#11)", "C13(#11)", ["C", "E", "G", "Bb", "D", "F#", "A"]),
            ("Tell me the notes in C13(b9)", "C13(b9)", ["C", "E", "G", "Bb", "Db", "A"]),
            ("Tell me the notes in C6/9", "C6/9", ["C", "E", "G", "A", "D"]),
            ("Tell me the notes in C7(#9)", "C7(#9)", ["C", "E", "G", "Bb", "D#"]),
            ("Tell me the notes in C7(#9, b13)", "C7(#9, b13)", ["C", "E", "G", "Bb", "D#", "Ab"]),
            ("Tell me the notes in C7(#11)", "C7(#11)", ["C", "E", "G", "Bb", "D", "F#"]),
            ("Tell me the notes in C7(b5)", "C7(b5)", ["C", "E", "Gb", "Bb"]),
            ("Tell me the notes in C7(b13)", "C7(b13)", ["C", "E", "G", "Bb", "Ab"]),
            ("Tell me the notes in C7(b9, b13)", "C7(b9, b13)", ["C", "E", "G", "Bb", "Db", "Ab"]),
            ("Tell me the notes in C9sus4", "C9sus4", ["C", "F", "G", "Bb", "D"]),
            ("Tell me the notes in C13sus4", "C13sus4", ["C", "F", "G", "Bb", "D", "A"]),
            ("Tell me the notes in Cdim7(maj7)", "Cdim7(maj7)", ["C", "Eb", "Gb", "A", "B"]),
            ("Tell me the notes in Cmaj13", "Cmaj13", ["C", "E", "G", "B", "D", "F", "A"]),
            ("Tell me the notes in Cmaj7(add13)", "Cmaj7(add13)", ["C", "E", "G", "B", "A"]),
            ("Tell me the notes in Cmaj7(#11)", "Cmaj7(#11)", ["C", "E", "G", "B", "D", "F#"]),
            ("Tell me the notes in Cmaj9", "Cmaj9", ["C", "E", "G", "B", "D"]),
            ("Tell me the notes in Cm(maj9)", "Cm(maj9)", ["C", "Eb", "G", "B", "D"]),
            ("Tell me the notes in Db9", "Db9", ["Db", "F", "Ab", "B", "Eb"]),
            ("Tell me the notes in D7", "D7", ["D", "F#", "A", "C"]),
            ("Tell me the notes in Edim", "Edim", ["E", "G", "A#"]),
            ("Tell me the notes in F#maj7", "F#maj7", ["F#", "A#", "E#"]),
            ("Tell me the notes in F#7", "F#7", ["F#", "A#", "E"]),
            ("Tell me the notes in F#m7", "F#m7", ["F#", "A", "E"]),
            ("Tell me the notes in F#maj9", "F#maj9", ["F#", "A#", "E#", "G#"]),
            ("Tell me the notes in F#9", "F#9", ["F#", "A#", "E", "G#"]),
            ("Tell me the notes in F#m9", "F#m9", ["F#", "A", "E", "G#"]),
            ("Tell me the notes in F#13", "F#13", ["F#", "A#", "E", "G#", "D#"]),
            ("Tell me the notes in F#maj13", "F#maj13", ["F#", "A#", "E#", "G#", "D#"]),
            ("Tell me the notes in F#7(b9)", "F#7(b9)", ["F#", "A#", "E", "G"]),
            ("Tell me the notes in F#7(#9)", "F#7(#9)", ["F#", "A#", "E", "A"]),
            ("Tell me the notes in F#7(#11)", "F#7(#11)", ["F#", "A#", "E", "B#"]),
            ("Tell me the notes in F#maj7(#11)", "F#maj7(#11)", ["F#", "A#", "E#", "B#"]),
            ("Tell me the notes in F#m11", "F#m11", ["F#", "A", "E", "B"]),
            ("Tell me the notes in F#13(b9)", "F#13(b9)", ["F#", "A#", "E", "G", "D#"]),
            ("Tell me the notes in F#7(b13)", "F#7(b13)", ["F#", "A#", "E", "D"]),
            ("Tell me the notes in F#m(maj7)", "F#m(maj7)", ["F#", "A", "E#"]),
            ("Tell me the notes in F#6/9", "F#6/9", ["F#", "A#", "D#", "G#"]),
            ("Tell me the notes in F#7(alt)", "F#7(alt)", ["F#", "A#", "E", "G", "A", "D"]),
            ("Tell me the notes in F#9sus4", "F#9sus4", ["F#", "B", "E", "G#"]),
            ("Tell me the notes in F#13sus4", "F#13sus4", ["F#", "B", "E", "G#", "D#"]),
            ("Tell me the notes in C#maj7", "C#maj7", ["C#", "E#", "B#"]),
            ("Tell me the notes in C#7", "C#7", ["C#", "E#", "B"]),
            ("Tell me the notes in C#m7", "C#m7", ["C#", "E", "B"]),
            ("Tell me the notes in C#maj9", "C#maj9", ["C#", "E#", "B#", "D#"]),
            ("Tell me the notes in C#9", "C#9", ["C#", "E#", "B", "D#"]),
            ("Tell me the notes in C#m9", "C#m9", ["C#", "E", "B", "D#"]),
            ("Tell me the notes in C#13", "C#13", ["C#", "E#", "B", "D#", "A#"]),
            ("Tell me the notes in C#maj13", "C#maj13", ["C#", "E#", "B#", "D#", "A#"]),
            ("Tell me the notes in C#7(b9)", "C#7(b9)", ["C#", "E#", "B", "D"]),
            ("Tell me the notes in C#7(#9)", "C#7(#9)", ["C#", "E#", "B", "E"]),
            ("Tell me the notes in C#7(#11)", "C#7(#11)", ["C#", "E#", "B", "F##"]),
            ("Tell me the notes in C#maj7(#11)", "C#maj7(#11)", ["C#", "E#", "B#", "F##"]),
            ("Tell me the notes in C#m11", "C#m11", ["C#", "E", "B", "F#"]),
            ("Tell me the notes in C#13(b9)", "C#13(b9)", ["C#", "E#", "B", "D", "A#"]),
            ("Tell me the notes in C#7(b13)", "C#7(b13)", ["C#", "E#", "B", "A"]),
            ("Tell me the notes in C#m(maj7)", "C#m(maj7)", ["C#", "E", "B#"]),
            ("Tell me the notes in C#6/9", "C#6/9", ["C#", "E#", "A#", "D#"]),
            ("Tell me the notes in C#7(alt)", "C#7(alt)", ["C#", "E#", "B", "D", "E", "G", "A"]),
            ("Tell me the notes in C#9sus4", "C#9sus4", ["C#", "F#", "B", "D#"]),
            ("Tell me the notes in C#13sus4", "C#13sus4", ["C#", "F#", "B", "D#", "A#"]),
            ("Tell me the notes in Abmaj9", "Abmaj9", ["Ab", "C", "G", "Bb"]),
            ("Tell me the notes in Am11", "Am11", ["A", "C", "G", "D"]),
            ("Tell me the notes in Bb7(alt)", "Bb7(alt)", ["Bb", "D", "Ab", "B", "Db", "E", "Gb"]),
            ("Tell me the notes in Bmaj7(#11)", "Bmaj7(#11)", ["B", "D#", "A#", "E#"]),
            ("Tell me the notes in D9", "D9", ["D", "F#", "C", "E"]),
            ("Tell me the notes in Eb7(b9)", "Eb7(b9)", ["Eb", "G", "Db", "Fb"]),
            ("Tell me the notes in Emaj13", "Emaj13", ["E", "G#", "D#", "F#", "C#"]),
            ("Tell me the notes in F7(#9)", "F7(#9)", ["F", "A", "Eb", "G#"]),
            ("Tell me the notes in G#m(maj7)", "G#m(maj7)", ["G#", "B", "G"]),
            ("Tell me the notes in D#m11", "D#m11", ["D#", "F#", "C#", "G#"]),
            ("Tell me the notes in Db6/9", "Db6/9", ["Db", "F", "Bb", "Eb"]),
            ("Tell me the notes in Gbadd9", "Gbadd9", ["Gb", "Bb", "Db", "Ab"]),
            ("Tell me the notes in Gbm6", "Gbm6", ["Gb", "A", "Db", "Eb"]),
            ("Tell me the notes in Gbsus2", "Gb sus2", ["Gb", "Ab", "Db"]),
            ("Tell me the notes in G6", "G6", ["G", "B", "D", "E"]),
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
