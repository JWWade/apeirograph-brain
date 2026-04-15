import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
EXAMPLE_FILE = ROOT / "data" / "examples" / "domain-schema-examples.json"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from apeirograph_brain.cli import main
from apeirograph_brain.schemas import SuggestionResponse
from apeirograph_brain.suggest import load_suggest_input, suggest_next_moves


class SuggestWorkflowTests(unittest.TestCase):
    def test_suggest_rejects_ungrounded_advisory_note(self):
        progression = load_suggest_input({
            "scale_context": {
                "root": "C",
                "mode": "ionian",
                "diatonic_pitch_classes": [0, 2, 4, 5, 7, 9, 11]
            },
            "chords": [
                {"root": "C", "quality": "major7", "pitch_classes": [0, 4, 7, 11], "label": "Cmaj7"},
                {"root": "A", "quality": "minor7", "pitch_classes": [9, 0, 4, 7], "label": "Am7"},
                {"root": "D", "quality": "minor7", "pitch_classes": [2, 5, 9, 0], "label": "Dm7"}
            ]
        })

        mock_client = Mock()
        mock_client.generate.return_value = "The next chord should be Cm7 for a balanced result."

        result = suggest_next_moves(progression, client=mock_client)

        self.assertNotIn("Cm7", result.advisory_note)
        self.assertIn("Cmaj7", result.advisory_note)

    def test_suggest_next_moves_returns_three_structured_candidates(self):
        with EXAMPLE_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        progression = load_suggest_input(data["progression_example"])

        mock_client = Mock()
        mock_client.generate.return_value = "Stay tonal and move toward gentle forward motion."

        result = suggest_next_moves(progression, client=mock_client)

        self.assertIsInstance(result, SuggestionResponse)
        self.assertEqual(len(result.suggestions), 3)
        self.assertTrue(all(item.rationale for item in result.suggestions))
        self.assertTrue(all(item.next_chord.root for item in result.suggestions))

    def test_cli_can_render_suggestion_output_from_json_file(self):
        payload = {
            "scale_context": {
                "root": "C",
                "mode": "ionian",
                "diatonic_pitch_classes": [0, 2, 4, 5, 7, 9, 11]
            },
            "chords": [
                {"root": "C", "quality": "major7", "pitch_classes": [0, 4, 7, 11], "label": "Cmaj7"},
                {"root": "A", "quality": "minor7", "pitch_classes": [9, 0, 4, 7], "label": "Am7"},
                {"root": "D", "quality": "minor7", "pitch_classes": [2, 5, 9, 0], "label": "Dm7"}
            ],
            "intent": "Suggest the next chord with a balanced tonal feel."
        }

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
            json.dump(payload, handle)
            path = handle.name

        output = StringIO()
        try:
            with redirect_stdout(output):
                result = main(["--suggest-file", path])
        finally:
            temp_path = Path(path)
            if temp_path.exists():
                temp_path.unlink()

        self.assertEqual(result, 0)
        rendered = json.loads(output.getvalue())
        self.assertIn("advisory_note", rendered)
        self.assertEqual(len(rendered["suggestions"]), 3)


if __name__ == "__main__":
    unittest.main()
