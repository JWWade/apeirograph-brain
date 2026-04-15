import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
EXAMPLE_FILE = ROOT / "data" / "examples" / "domain-schema-examples.json"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from apeirograph_brain.schemas import (
    ChordObject,
    ExplanationResponse,
    ProgressionInput,
    ScaleContext,
    SuggestionResponse,
)


class DomainSchemaTests(unittest.TestCase):
    def test_chord_object_normalizes_pitch_classes(self):
        chord = ChordObject(root="C", quality="major7", pitch_classes=[7, 0, 4])
        self.assertEqual(chord.pitch_classes, [0, 4, 7])

    def test_progression_input_requires_at_least_one_chord(self):
        with self.assertRaises(ValueError):
            ProgressionInput(chords=[])

    def test_response_objects_accept_structured_fields(self):
        explanation = ExplanationResponse(
            summary="A stable tonic sonority with bright color.",
            salient_properties=["stable", "diatonic"],
            tension_level="low",
            symmetry_note="Contains balanced interval spacing.",
            motion_note="Minimal voice-leading pressure.",
            confidence=0.84,
        )
        self.assertEqual(explanation.tension_level, "low")

        suggestion = SuggestionResponse(
            advisory_note="Treat these as options, not instructions.",
            suggestions=[
                {
                    "label": "Move to G7",
                    "rationale": "Creates a strong dominant pull.",
                    "stability": "balanced",
                    "next_chord": {"root": "G", "quality": "dominant7", "pitch_classes": [7, 11, 2, 5]},
                }
            ],
            confidence=0.76,
        )
        self.assertEqual(len(suggestion.suggestions), 1)
        self.assertEqual(suggestion.suggestions[0].next_chord.root, "G")

    def test_sample_examples_load_and_validate(self):
        with EXAMPLE_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        chord = ChordObject(**data["chord_example"])
        scale = ScaleContext(**data["scale_context_example"])
        progression = ProgressionInput(**data["progression_example"])

        self.assertEqual(chord.root, "C")
        self.assertEqual(scale.mode, "ionian")
        self.assertEqual(len(progression.chords), 3)


if __name__ == "__main__":
    unittest.main()
