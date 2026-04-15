import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from apeirograph_brain.keys import (
    build_diatonic_triads,
    build_scale_context,
    get_diatonic_chord,
    normalize_mode_name,
    spell_key_notes,
)


MAJOR_KEY_ROWS = [
    ("C", ["C", "D", "E", "F", "G", "A", "B"]),
    ("C#", ["C#", "D#", "E#", "F#", "G#", "A#", "B#"]),
    ("D", ["D", "E", "F#", "G", "A", "B", "C#"]),
    ("Eb", ["Eb", "F", "G", "Ab", "Bb", "C", "D"]),
    ("E", ["E", "F#", "G#", "A", "B", "C#", "D#"]),
    ("F", ["F", "G", "A", "Bb", "C", "D", "E"]),
    ("F#", ["F#", "G#", "A#", "B", "C#", "D#", "E#"]),
    ("G", ["G", "A", "B", "C", "D", "E", "F#"]),
    ("Ab", ["Ab", "Bb", "C", "Db", "Eb", "F", "G"]),
    ("A", ["A", "B", "C#", "D", "E", "F#", "G#"]),
    ("Bb", ["Bb", "C", "D", "Eb", "F", "G", "A"]),
    ("B", ["B", "C#", "D#", "E", "F#", "G#", "A#"]),
]

MINOR_KEY_ROWS = [
    ("C", ["C", "D", "Eb", "F", "G", "Ab", "Bb"]),
    ("C#", ["C#", "D#", "E", "F#", "G#", "A", "B"]),
    ("D", ["D", "E", "F", "G", "A", "Bb", "C"]),
    ("Eb", ["Eb", "F", "Gb", "Ab", "Bb", "Cb", "Db"]),
    ("E", ["E", "F#", "G", "A", "B", "C", "D"]),
    ("F", ["F", "G", "Ab", "Bb", "C", "Db", "Eb"]),
    ("F#", ["F#", "G#", "A", "B", "C#", "D", "E"]),
    ("G", ["G", "A", "Bb", "C", "D", "Eb", "F"]),
    ("G#", ["G#", "A#", "B", "C#", "D#", "E", "F#"]),
    ("A", ["A", "B", "C", "D", "E", "F", "G"]),
    ("Bb", ["Bb", "C", "Db", "Eb", "F", "Gb", "Ab"]),
    ("B", ["B", "C#", "D", "E", "F#", "G", "A"]),
]


class KeyFoundationTests(unittest.TestCase):
    def test_normalize_mode_aliases(self):
        self.assertEqual(normalize_mode_name("major"), "ionian")
        self.assertEqual(normalize_mode_name("minor"), "aeolian")
        self.assertEqual(normalize_mode_name("mixolydian"), "mixolydian")

    def test_build_scale_context_for_common_keys(self):
        c_major = build_scale_context("C", "major")
        self.assertEqual(c_major.root, "C")
        self.assertEqual(c_major.mode, "ionian")
        self.assertEqual(c_major.diatonic_pitch_classes, [0, 2, 4, 5, 7, 9, 11])

        a_minor = build_scale_context("A", "minor")
        self.assertEqual(a_minor.root, "A")
        self.assertEqual(a_minor.mode, "aeolian")
        self.assertEqual(a_minor.diatonic_pitch_classes, [0, 2, 4, 5, 7, 9, 11])

    def test_spell_key_notes_matches_reference_table_for_major_keys(self):
        for root, expected_notes in MAJOR_KEY_ROWS:
            with self.subTest(root=root):
                self.assertEqual(spell_key_notes(root, "major"), expected_notes)

    def test_spell_key_notes_matches_reference_table_for_minor_keys(self):
        for root, expected_notes in MINOR_KEY_ROWS:
            with self.subTest(root=root):
                self.assertEqual(spell_key_notes(root, "minor"), expected_notes)

    def test_diatonic_triads_follow_major_key_pattern(self):
        c_sharp_major = build_diatonic_triads("C#", "major")
        self.assertEqual(c_sharp_major["ii"], "D#m")
        self.assertEqual(c_sharp_major["iii"], "E#m")
        self.assertEqual(c_sharp_major["vii°"], "B#dim")

        b_flat_major = build_diatonic_triads("Bb", "major")
        self.assertEqual(b_flat_major, {
            "I": "Bb",
            "ii": "Cm",
            "iii": "Dm",
            "IV": "Eb",
            "V": "F",
            "vi": "Gm",
            "vii°": "Adim",
        })

        self.assertEqual(get_diatonic_chord("C#", "major", "ii"), "D#m")

    def test_diatonic_triads_follow_relative_minor_pattern(self):
        c_minor = build_diatonic_triads("C", "minor")
        self.assertEqual(c_minor, {
            "i": "Cm",
            "ii°": "Ddim",
            "III": "Eb",
            "iv": "Fm",
            "v": "Gm",
            "VI": "Ab",
            "VII": "Bb",
        })

        c_sharp_minor = build_diatonic_triads("C#", "minor")
        self.assertEqual(c_sharp_minor["i"], "C#m")
        self.assertEqual(c_sharp_minor["ii°"], "D#dim")
        self.assertEqual(c_sharp_minor["III"], "E")
        self.assertEqual(c_sharp_minor["iv"], "F#m")
        self.assertEqual(c_sharp_minor["v"], "G#m")
        self.assertEqual(c_sharp_minor["VI"], "A")
        self.assertEqual(c_sharp_minor["VII"], "B")

        self.assertEqual(get_diatonic_chord("C#", "minor", "III"), "E")

    def test_unsupported_modes_raise_clean_errors(self):
        with self.assertRaises(ValueError):
            build_scale_context("C", "lydian-dominant")


if __name__ == "__main__":
    unittest.main()
