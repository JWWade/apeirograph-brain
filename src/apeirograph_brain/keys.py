from typing import List

from apeirograph_brain.chord_theory import NOTE_LETTERS, NATURAL_LETTER_PITCH_CLASSES, ROOT_PITCH_CLASSES
from apeirograph_brain.schemas import ScaleContext

MODE_ALIASES = {
    "major": "ionian",
    "ionian": "ionian",
    "minor": "aeolian",
    "naturalminor": "aeolian",
    "natural minor": "aeolian",
    "aeolian": "aeolian",
    "dorian": "dorian",
    "phrygian": "phrygian",
    "lydian": "lydian",
    "mixolydian": "mixolydian",
    "locrian": "locrian",
}

MODE_INTERVALS = {
    "ionian": [0, 2, 4, 5, 7, 9, 11],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "aeolian": [0, 2, 3, 5, 7, 8, 10],
    "locrian": [0, 1, 3, 5, 6, 8, 10],
}

ROMAN_NUMERALS = ["I", "II", "III", "IV", "V", "VI", "VII"]
TRIAD_SUFFIXES = {
    "major": "",
    "minor": "m",
    "diminished": "dim",
    "augmented": "aug",
}


def normalize_root_name(root: str) -> str:
    normalized = root.strip()
    if not normalized:
        raise ValueError("root must not be empty")
    return normalized[0].upper() + normalized[1:]


def normalize_mode_name(mode: str) -> str:
    normalized = mode.lower().strip()
    normalized = MODE_ALIASES.get(normalized, normalized)
    if normalized not in MODE_INTERVALS:
        raise ValueError("Unsupported mode: {0}".format(mode))
    return normalized


def spell_scale_degree(root: str, interval: int, degree_index: int) -> str:
    root_letter = root[0].upper()
    target_letter = NOTE_LETTERS[(NOTE_LETTERS.index(root_letter) + degree_index) % len(NOTE_LETTERS)]
    target_pc = (ROOT_PITCH_CLASSES[root] + interval) % 12
    natural_pc = NATURAL_LETTER_PITCH_CLASSES[target_letter]
    offset = (target_pc - natural_pc + 12) % 12

    if offset > 6:
        offset -= 12

    if offset == 2:
        return "{0}##".format(target_letter)
    if offset == 1:
        return "{0}#".format(target_letter)
    if offset == -1:
        return "{0}b".format(target_letter)
    if offset == -2:
        return "{0}bb".format(target_letter)
    return target_letter


def spell_key_notes(root: str, mode: str) -> List[str]:
    normalized_root = normalize_root_name(root)
    normalized_mode = normalize_mode_name(mode)

    if normalized_root not in ROOT_PITCH_CLASSES:
        raise ValueError("Unsupported root: {0}".format(root))

    return [
        spell_scale_degree(normalized_root, interval, degree_index)
        for degree_index, interval in enumerate(MODE_INTERVALS[normalized_mode])
    ]


def infer_triad_quality(scale_pitch_classes: List[int], degree_index: int) -> str:
    root_pc = scale_pitch_classes[degree_index]
    third_pc = scale_pitch_classes[(degree_index + 2) % len(scale_pitch_classes)]
    fifth_pc = scale_pitch_classes[(degree_index + 4) % len(scale_pitch_classes)]

    third_interval = (third_pc - root_pc) % 12
    fifth_interval = (fifth_pc - root_pc) % 12

    if third_interval == 4 and fifth_interval == 7:
        return "major"
    if third_interval == 3 and fifth_interval == 7:
        return "minor"
    if third_interval == 3 and fifth_interval == 6:
        return "diminished"
    if third_interval == 4 and fifth_interval == 8:
        return "augmented"
    raise ValueError("Unsupported diatonic triad quality for degree index {0}".format(degree_index))


def format_roman_numeral(degree_index: int, quality: str) -> str:
    base = ROMAN_NUMERALS[degree_index]
    if quality == "major":
        return base
    if quality == "minor":
        return base.lower()
    if quality == "diminished":
        return base.lower() + "°"
    if quality == "augmented":
        return base + "+"
    raise ValueError("Unsupported triad quality: {0}".format(quality))


def build_diatonic_triads(root: str, mode: str) -> dict:
    normalized_root = normalize_root_name(root)
    normalized_mode = normalize_mode_name(mode)
    scale_notes = spell_key_notes(normalized_root, normalized_mode)
    scale_pitch_classes = [
        (ROOT_PITCH_CLASSES[normalized_root] + interval) % 12
        for interval in MODE_INTERVALS[normalized_mode]
    ]

    triads = {}
    for degree_index, note_name in enumerate(scale_notes):
        quality = infer_triad_quality(scale_pitch_classes, degree_index)
        roman = format_roman_numeral(degree_index, quality)
        triads[roman] = "{0}{1}".format(note_name, TRIAD_SUFFIXES[quality])

    return triads


def get_diatonic_chord(root: str, mode: str, degree: str) -> str:
    normalized_degree = degree.strip()
    triads = build_diatonic_triads(root, mode)

    for roman, chord_name in triads.items():
        if roman.lower() == normalized_degree.lower():
            return chord_name

    raise ValueError("Unsupported degree: {0}".format(degree))


def build_scale_context(root: str, mode: str) -> ScaleContext:
    normalized_root = normalize_root_name(root)
    normalized_mode = normalize_mode_name(mode)
    diatonic_pitch_classes = [
        (ROOT_PITCH_CLASSES[normalized_root] + interval) % 12
        for interval in MODE_INTERVALS[normalized_mode]
    ]
    return ScaleContext(
        root=normalized_root,
        mode=normalized_mode,
        diatonic_pitch_classes=diatonic_pitch_classes,
    )
