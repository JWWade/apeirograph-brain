import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from apeirograph_brain.chord_spelling import (
    natural_join,
    parse_chord_note_query,
    render_chord_name,
    spell_chord_notes,
    try_answer_basic_chord_note_prompt,
)


class ChordSpellingTests(unittest.TestCase):
    def test_parse_chord_note_queries_for_supported_shapes(self):
        cases = [
            ("Tell me the notes that makeup A minor chord", ("A", "minor")),
            ("Tell me the notes in Bb major chord", ("Bb", "major")),
            ("Tell me the notes in A dominant 7 chord", ("A", "dominant7")),
            ("Tell me the notes in Abdim7", ("Ab", "dim7")),
            ("Tell me the notes in Absus4", ("Ab", "sus4")),
            ("Tell me the notes in Bbmaj7", ("Bb", "major7")),
            ("Tell me the notes in Badd9", ("B", "add9")),
            ("Tell me the notes in C11", ("C", "11")),
            ("Tell me the notes in C13", ("C", "13")),
            ("Tell me the notes in C13(#11)", ("C", "13#11")),
            ("Tell me the notes in C13(b9)", ("C", "13b9")),
            ("Tell me the notes in C6/9", ("C", "6/9")),
            ("Tell me the notes in C7(#9)", ("C", "7#9")),
            ("Tell me the notes in C7(#9, b13)", ("C", "7#9b13")),
            ("Tell me the notes in C7(#11)", ("C", "7#11")),
            ("Tell me the notes in C7(b5)", ("C", "7b5")),
            ("Tell me the notes in C7(b13)", ("C", "7b13")),
            ("Tell me the notes in C7(b9, b13)", ("C", "7b9b13")),
            ("Tell me the notes in C9sus4", ("C", "9sus4")),
            ("Tell me the notes in C13sus4", ("C", "13sus4")),
            ("Tell me the notes in Cdim7(maj7)", ("C", "dim7maj7")),
            ("Tell me the notes in Cmaj13", ("C", "major13")),
            ("Tell me the notes in Cmaj7(add13)", ("C", "major7add13")),
            ("Tell me the notes in Cmaj7(#11)", ("C", "major7#11")),
            ("Tell me the notes in Cmaj9", ("C", "major9")),
            ("Tell me the notes in Cm(maj9)", ("C", "minormajor9")),
            ("Tell me the notes in Db9", ("Db", "9")),
            ("Tell me the notes in D7", ("D", "7")),
            ("Tell me the notes in Edim", ("E", "diminished")),
            ("Tell me the notes in F#maj7", ("F#", "major7")),
            ("Tell me the notes in F#m9", ("F#", "minor9")),
            ("Tell me the notes in F#7(b9)", ("F#", "7b9")),
            ("Tell me the notes in F#7(#11)", ("F#", "7#11")),
            ("Tell me the notes in F#m(maj7)", ("F#", "minormajor7")),
            ("Tell me the notes in F#7(alt)", ("F#", "7alt")),
            ("Tell me the notes in F#9sus4", ("F#", "9sus4")),
            ("Tell me the notes in F#13sus4", ("F#", "13sus4")),
            ("Tell me the notes in C#maj7", ("C#", "major7")),
            ("Tell me the notes in C#7(b9)", ("C#", "7b9")),
            ("Tell me the notes in C#7(#11)", ("C#", "7#11")),
            ("Tell me the notes in C#maj7(#11)", ("C#", "major7#11")),
            ("Tell me the notes in C#m11", ("C#", "minor11")),
            ("Tell me the notes in C#m(maj7)", ("C#", "minormajor7")),
            ("Tell me the notes in C#7(alt)", ("C#", "7alt")),
            ("Tell me the notes in C#9sus4", ("C#", "9sus4")),
            ("Tell me the notes in C#13sus4", ("C#", "13sus4")),
            ("Tell me the notes in Abmaj9", ("Ab", "major9")),
            ("Tell me the notes in Am11", ("A", "minor11")),
            ("Tell me the notes in Bb7(alt)", ("Bb", "7alt")),
            ("Tell me the notes in Bmaj7(#11)", ("B", "major7#11")),
            ("Tell me the notes in D9", ("D", "9")),
            ("Tell me the notes in Eb7(b9)", ("Eb", "7b9")),
            ("Tell me the notes in Emaj13", ("E", "major13")),
            ("Tell me the notes in F7(#9)", ("F", "7#9")),
            ("Tell me the notes in G#m(maj7)", ("G#", "minormajor7")),
            ("Tell me the notes in D#m11", ("D#", "minor11")),
            ("Tell me the notes in Db6/9", ("Db", "6/9")),
            ("Tell me the notes in Gbadd9", ("Gb", "add9")),
            ("Tell me the notes in Gbm6", ("Gb", "minor6")),
            ("Tell me the notes in Gbsus2", ("Gb", "sus2")),
            ("Tell me the notes in G6", ("G", "6")),
            ("Suppose we change C major to a sus2 chord -- what are the notes then?", ("C", "sus2")),
            ("Tell me the notes in Eb7(#9)", ("Eb", "7#9")),
            ("Tell me the notes in C#m7b5", ("C#", "m7b5")),
        ]

        for prompt, expected in cases:
            with self.subTest(prompt=prompt):
                self.assertEqual(parse_chord_note_query(prompt), expected)

    def test_spell_chord_notes_uses_expected_accidentals(self):
        cases = [
            (("Eb", "7sus4"), ["Eb", "Ab", "Bb", "Db"]),
            (("C#", "dim7"), ["C#", "E", "G", "A#"]),
            (("Ab", "dim7"), ["Ab", "B", "D", "F"]),
            (("Ab", "sus4"), ["Ab", "Db", "Eb"]),
            (("A", "69"), ["A", "C#", "E", "F#", "B"]),
            (("Bb", "major7"), ["Bb", "D", "F", "A"]),
            (("B", "add9"), ["B", "D#", "F#", "C#"]),
            (("C", "11"), ["C", "E", "G", "Bb", "D", "F"]),
            (("C", "13"), ["C", "E", "G", "Bb", "D", "F", "A"]),
            (("C", "13#11"), ["C", "E", "G", "Bb", "D", "F#", "A"]),
            (("C", "13b9"), ["C", "E", "G", "Bb", "Db", "A"]),
            (("C", "6/9"), ["C", "E", "G", "A", "D"]),
            (("C", "7#11"), ["C", "E", "G", "Bb", "D", "F#"]),
            (("C", "7#9b13"), ["C", "E", "G", "Bb", "D#", "Ab"]),
            (("C", "7b5"), ["C", "E", "Gb", "Bb"]),
            (("C", "7b13"), ["C", "E", "G", "Bb", "Ab"]),
            (("C", "7b9b13"), ["C", "E", "G", "Bb", "Db", "Ab"]),
            (("C", "9sus4"), ["C", "F", "G", "Bb", "D"]),
            (("C", "13sus4"), ["C", "F", "G", "Bb", "D", "A"]),
            (("C", "dim7maj7"), ["C", "Eb", "Gb", "A", "B"]),
            (("C", "major13"), ["C", "E", "G", "B", "D", "F", "A"]),
            (("C", "major7add13"), ["C", "E", "G", "B", "A"]),
            (("C", "major7#11"), ["C", "E", "G", "B", "D", "F#"]),
            (("C", "major9"), ["C", "E", "G", "B", "D"]),
            (("C", "minormajor9"), ["C", "Eb", "G", "B", "D"]),
            (("Db", "9"), ["Db", "F", "Ab", "B", "Eb"]),
            (("F#", "major7"), ["F#", "A#", "E#"]),
            (("F#", "minor9"), ["F#", "A", "E", "G#"]),
            (("F#", "7b9"), ["F#", "A#", "E", "G"]),
            (("F#", "7#11"), ["F#", "A#", "E", "B#"]),
            (("F#", "minormajor7"), ["F#", "A", "E#"]),
            (("F#", "7alt"), ["F#", "A#", "E", "G", "A", "D"]),
            (("F#", "9sus4"), ["F#", "B", "E", "G#"]),
            (("F#", "13sus4"), ["F#", "B", "E", "G#", "D#"]),
            (("C#", "major7"), ["C#", "E#", "B#"]),
            (("C#", "7b9"), ["C#", "E#", "B", "D"]),
            (("C#", "7#11"), ["C#", "E#", "B", "F##"]),
            (("C#", "major7#11"), ["C#", "E#", "B#", "F##"]),
            (("C#", "minor11"), ["C#", "E", "B", "F#"]),
            (("C#", "minormajor7"), ["C#", "E", "B#"]),
            (("C#", "7alt"), ["C#", "E#", "B", "D", "E", "G", "A"]),
            (("C#", "9sus4"), ["C#", "F#", "B", "D#"]),
            (("C#", "13sus4"), ["C#", "F#", "B", "D#", "A#"]),
            (("Ab", "major9"), ["Ab", "C", "G", "Bb"]),
            (("A", "minor11"), ["A", "C", "G", "D"]),
            (("Bb", "7alt"), ["Bb", "D", "Ab", "B", "Db", "E", "Gb"]),
            (("B", "major7#11"), ["B", "D#", "A#", "E#"]),
            (("D", "9"), ["D", "F#", "C", "E"]),
            (("Eb", "7b9"), ["Eb", "G", "Db", "Fb"]),
            (("E", "major13"), ["E", "G#", "D#", "F#", "C#"]),
            (("F", "7#9"), ["F", "A", "Eb", "G#"]),
            (("G#", "minormajor7"), ["G#", "B", "G"]),
            (("D#", "minor11"), ["D#", "F#", "C#", "G#"]),
            (("Db", "6/9"), ["Db", "F", "Bb", "Eb"]),
            (("D", "7"), ["D", "F#", "A", "C"]),
            (("E", "diminished"), ["E", "G", "A#"]),
            (("Gb", "add9"), ["Gb", "Bb", "Db", "Ab"]),
            (("Gb", "minor6"), ["Gb", "A", "Db", "Eb"]),
            (("Gb", "sus2"), ["Gb", "Ab", "Db"]),
            (("G", "6"), ["G", "B", "D", "E"]),
        ]

        for (root, quality), expected in cases:
            with self.subTest(root=root, quality=quality):
                rendered = spell_chord_notes(root, quality)
                self.assertIsNotNone(rendered)
                for note in expected:
                    self.assertIn(note, rendered)

    def test_render_and_prompt_answer_are_user_facing(self):
        self.assertEqual(render_chord_name("C#", "diminished"), "C#dim")
        self.assertEqual(render_chord_name("Eb", "7#9"), "Eb7(#9)")

        answer = try_answer_basic_chord_note_prompt("Tell me the notes in the chord Am6")
        self.assertEqual(answer, "The notes of an Am6 chord are A, C, E, and F#.")

    def test_non_note_prompts_fall_through(self):
        self.assertIsNone(parse_chord_note_query("Explain why this cadence works"))
        self.assertIsNone(try_answer_basic_chord_note_prompt("Suggest a smoother reharmonization"))
        self.assertEqual(natural_join(["C", "E"]), "C and E")


if __name__ == "__main__":
    unittest.main()
