import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from apeirograph_brain.progressions import analyze_progression, detect_cadence, roman_numeral_for_chord
from apeirograph_brain.schemas import ChordObject


class ProgressionAnalysisTests(unittest.TestCase):
    def test_labels_basic_major_progression(self):
        chords = [
            ChordObject(root="C", quality="major", pitch_classes=[0, 4, 7]),
            ChordObject(root="F", quality="major", pitch_classes=[5, 9, 0]),
            ChordObject(root="G", quality="major", pitch_classes=[7, 11, 2]),
            ChordObject(root="C", quality="major", pitch_classes=[0, 4, 7]),
        ]

        analysis = analyze_progression(chords, "C", "major")

        self.assertEqual([item["roman"] for item in analysis], ["I", "IV", "V", "I"])
        self.assertEqual([item["function"] for item in analysis], ["tonic", "predominant", "dominant", "tonic"])

    def test_labels_basic_minor_progression(self):
        chords = [
            ChordObject(root="A", quality="minor", pitch_classes=[9, 0, 4]),
            ChordObject(root="D", quality="minor", pitch_classes=[2, 5, 9]),
            ChordObject(root="E", quality="minor", pitch_classes=[4, 7, 11]),
            ChordObject(root="A", quality="minor", pitch_classes=[9, 0, 4]),
        ]

        analysis = analyze_progression(chords, "A", "minor")

        self.assertEqual([item["roman"] for item in analysis], ["i", "iv", "v", "i"])
        self.assertEqual([item["function"] for item in analysis], ["tonic", "predominant", "dominant", "tonic"])

    def test_labels_common_seventh_chords(self):
        self.assertEqual(roman_numeral_for_chord("D", "minor7", "C", "major"), "ii7")
        self.assertEqual(roman_numeral_for_chord("G", "dominant7", "C", "major"), "V7")
        self.assertEqual(roman_numeral_for_chord("C", "major7", "C", "major"), "Imaj7")
        self.assertEqual(roman_numeral_for_chord("B", "m7b5", "C", "major"), "viiø7")

    def test_detects_common_cadences(self):
        self.assertEqual(detect_cadence(["G", "C"], "C", "major"), "authentic")
        self.assertEqual(detect_cadence(["F", "C"], "C", "major"), "plagal")
        self.assertEqual(detect_cadence(["G", "Am"], "C", "major"), "deceptive")
        self.assertEqual(detect_cadence(["Dm", "G"], "C", "major"), "half")


if __name__ == "__main__":
    unittest.main()
