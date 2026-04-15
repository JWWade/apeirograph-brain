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
from apeirograph_brain.explain import explain_progression, load_explain_input
from apeirograph_brain.schemas import ExplanationResponse


class ExplainWorkflowTests(unittest.TestCase):
    def test_explain_progression_rejects_ungrounded_model_wording(self):
        progression = load_explain_input({
            "root": "C",
            "quality": "major",
            "pitch_classes": [0, 4, 7],
            "label": "C"
        })

        mock_client = Mock()
        mock_client.generate.return_value = "C major is the tonic, dominant, and subdominant all at once."

        result = explain_progression(progression, client=mock_client)

        self.assertIn("C, E, and G", result.summary)
        self.assertNotIn("subdominant", result.summary.lower())

    def test_explain_progression_uses_full_progression_facts(self):
        progression = load_explain_input({
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
        mock_client.generate.return_value = "This moves from C to Am with a gentle change in color."

        result = explain_progression(progression, client=mock_client)

        self.assertIn("C ionian", result.summary)
        self.assertIn("Dm7", result.summary)

    def test_explain_progression_returns_structured_response(self):
        with EXAMPLE_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        progression = load_explain_input(data["progression_example"])

        mock_client = Mock()
        mock_client.generate.return_value = "The progression begins with tonic stability and moves gently toward more motion."

        result = explain_progression(progression, client=mock_client)

        self.assertIsInstance(result, ExplanationResponse)
        self.assertTrue(result.summary)
        self.assertIn(result.tension_level, {"low", "medium", "high"})
        self.assertTrue(result.symmetry_note)
        self.assertTrue(result.motion_note)

    def test_cli_can_explain_a_single_chord_file(self):
        payload = {
            "root": "C",
            "quality": "major",
            "pitch_classes": [0, 4, 7],
            "label": "C"
        }

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
            json.dump(payload, handle)
            path = handle.name

        output = StringIO()
        try:
            with redirect_stdout(output):
                result = main(["--explain-file", path])
        finally:
            temp_path = Path(path)
            if temp_path.exists():
                temp_path.unlink()

        self.assertEqual(result, 0)
        rendered = json.loads(output.getvalue())
        self.assertIn("summary", rendered)
        self.assertIn("salient_properties", rendered)
        self.assertEqual(rendered["tension_level"], "low")


if __name__ == "__main__":
    unittest.main()
