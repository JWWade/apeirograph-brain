import re
from typing import List, Optional, Tuple

SHARP_NOTE_NAMES = {
    0: "C",
    1: "C#",
    2: "D",
    3: "D#",
    4: "E",
    5: "F",
    6: "F#",
    7: "G",
    8: "G#",
    9: "A",
    10: "A#",
    11: "B",
}

FLAT_NOTE_NAMES = {
    0: "C",
    1: "Db",
    2: "D",
    3: "Eb",
    4: "E",
    5: "F",
    6: "Gb",
    7: "G",
    8: "Ab",
    9: "A",
    10: "Bb",
    11: "B",
}

ROOT_PITCH_CLASSES = {
    "C": 0,
    "B#": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "Fb": 4,
    "F": 5,
    "E#": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
    "Cb": 11,
}

CHORD_INTERVALS = {
    "major": [0, 4, 7],
    "minor": [0, 3, 7],
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
    "7sus4": [0, 5, 7, 10],
    "7#9": [0, 4, 7, 10, 15],
    "13": [0, 4, 7, 10, 21],
    "m7b5": [0, 3, 6, 10],
    "dim7": [0, 3, 6, 9],
    "diminished": [0, 3, 6],
    "augmented": [0, 4, 8],
    "major6": [0, 4, 7, 9],
    "minor6": [0, 3, 7, 9],
    "6": [0, 4, 7, 9],
    "m6": [0, 3, 7, 9],
    "major7": [0, 4, 7, 11],
    "minor7": [0, 3, 7, 10],
    "dominant7": [0, 4, 7, 10],
    "69": [0, 4, 7, 9, 14],
    "6/9": [0, 4, 7, 9, 14],
    "minor69": [0, 3, 7, 9, 14],
    "m69": [0, 3, 7, 9, 14],
}

QUALITY_PATTERN = r"7\(#9\)|7#9|7sus4|m7b5|dim7|major7|minor7|dominant7|major6|minor6|minor69|m69|m6|13|dim|aug|6/9|69|sus2|sus4|diminished|augmented|minor|major|6"
COMPACT_PATTERN = r"7\(#9\)|7#9|7sus4|m7b5|dim7|13|69|6/9|m69|minor69|maj7|m7|m6|sus2|sus4|dim|aug"

QUALITY_ALIASES = {
    "6/9": "69",
    "maj7": "major7",
    "m7": "minor7",
    "m6": "minor6",
    "7(#9)": "7#9",
    "dim": "diminished",
    "aug": "augmented",
}

COMPACT_RENDER_QUALITIES = {"69", "6/9", "m69", "m6", "6", "7sus4", "m7b5", "dim7", "13"}

THEORY_GROUNDING_LINES = [
    "You are a careful music-theory assistant for harmonic analysis.",
    "Use standard tonal terminology and exact pitch spelling.",
    "Never invent chord tones, scale degrees, or harmonic functions.",
    "When asked about a chord, name its exact notes first.",
    "For a major triad, the chord tones are root, major third, and perfect fifth.",
    "For a minor triad, the chord tones are root, minor third, and perfect fifth.",
    "For a sus2 chord, replace the third with the major second.",
    "For a sus4 chord, replace the third with the perfect fourth.",
    "C major triad = C-E-G.",
    "A minor triad = A-C-E.",
    "C sus2 chord = C-D-G.",
    "A sus2 chord = A-B-E.",
    "C sus4 chord = C-F-G.",
    "A69 chord = A-C#-E-F#-B.",
    "The fifth may be omitted in performance, but it still belongs to the full chord spelling.",
    "If the user asks for one short sentence, answer in one short sentence.",
    "If you are unsure, say you are unsure instead of guessing.",
]


def get_default_theory_prompt_lines() -> List[str]:
    return list(THEORY_GROUNDING_LINES)


def try_answer_basic_chord_note_prompt(prompt: str) -> Optional[str]:
    parsed = parse_chord_note_query(prompt)
    if not parsed:
        return None

    root, quality = parsed
    notes = spell_chord_notes(root, quality)
    if not notes:
        return None

    chord_name = render_chord_name(root, quality)
    article = "an" if chord_name[0].lower() in "aeiou" else "a"
    return "The notes of {0} {1} chord are {2}.".format(article, chord_name, natural_join(notes))


def parse_chord_note_query(prompt: str) -> Optional[Tuple[str, str]]:
    text = prompt.strip()
    lowered = text.lower()

    if "note" not in lowered and "notes" not in lowered:
        return None

    root = None
    quality = None

    target_match = re.search(r"to\s+(?:a\s+|an\s+)?(?P<quality>" + QUALITY_PATTERN + r")\s+chord", text, flags=re.IGNORECASE)
    root_match = re.search(r"(?P<root>[A-G](?:#|b)?)\s+(?P<quality>" + QUALITY_PATTERN + r")\b", text, flags=re.IGNORECASE)
    direct_match = re.search(r"(?P<root>[A-G](?:#|b)?)\s+(?P<quality>" + QUALITY_PATTERN + r")\s+chord", text, flags=re.IGNORECASE)
    compact_match = re.search(r"(?P<root>[A-G](?:#|b)?)(?P<quality>" + COMPACT_PATTERN + r")(?![A-Za-z0-9])", text, flags=re.IGNORECASE)

    if compact_match:
        root = compact_match.group("root")
        quality = compact_match.group("quality")
    elif root_match:
        root = root_match.group("root")

    if target_match:
        quality = target_match.group("quality")
    elif direct_match and quality is None:
        quality = direct_match.group("quality")
    elif root_match and quality is None:
        quality = root_match.group("quality")

    if not root or not quality:
        return None

    normalized_root = root[0].upper() + root[1:]
    normalized_quality = normalize_quality_name(quality)

    if normalized_root not in ROOT_PITCH_CLASSES or normalized_quality not in CHORD_INTERVALS:
        return None

    return normalized_root, normalized_quality


def normalize_quality_name(quality: str) -> str:
    normalized = quality.lower().replace(" ", "")
    return QUALITY_ALIASES.get(normalized, normalized)


def spell_chord_notes(root: str, quality: str) -> Optional[List[str]]:
    normalized_root = root[0].upper() + root[1:]
    normalized_quality = normalize_quality_name(quality)

    if normalized_root not in ROOT_PITCH_CLASSES or normalized_quality not in CHORD_INTERVALS:
        return None

    root_pc = ROOT_PITCH_CLASSES[normalized_root]
    note_names: List[str] = []

    for interval in CHORD_INTERVALS[normalized_quality]:
        note_pc = (root_pc + interval) % 12
        if normalized_quality == "7#9" and interval == 15:
            note_names.append(SHARP_NOTE_NAMES[note_pc])
        elif normalized_quality == "dim7" and "#" in normalized_root:
            note_names.append(SHARP_NOTE_NAMES[note_pc])
        else:
            note_map = FLAT_NOTE_NAMES if "b" in normalized_root else SHARP_NOTE_NAMES
            note_names.append(note_map[note_pc])

    return note_names


def render_chord_name(root: str, quality: str) -> str:
    normalized_quality = normalize_quality_name(quality)

    if normalized_quality in COMPACT_RENDER_QUALITIES:
        return "{0}{1}".format(root, normalized_quality)
    if normalized_quality == "7#9":
        return "{0}7(#9)".format(root)
    if normalized_quality == "diminished":
        return "{0}dim".format(root)
    if normalized_quality == "augmented":
        return "{0}aug".format(root)
    if normalized_quality == "major6":
        return "{0} major 6".format(root)
    if normalized_quality == "minor6":
        return "{0}m6".format(root)
    return "{0} {1}".format(root, normalized_quality)


def natural_join(parts: List[str]) -> str:
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return "{0} and {1}".format(parts[0], parts[1])
    return "{0}, and {1}".format(", ".join(parts[:-1]), parts[-1])
