from typing import Dict, List, Optional, Tuple

from .chord_theory import (
    CHORD_INTERVALS,
    COMPACT_CHORD_RE,
    COMPACT_RENDER_QUALITIES,
    DIMINISHED_FAMILY_QUALITIES,
    FLAT_NOTE_NAMES,
    FORCED_FLAT_INTERVALS,
    FORCED_SHARP_INTERVALS,
    INTERVAL_DEGREES,
    MINOR_FAMILY_QUALITIES,
    NATURAL_LETTER_PITCH_CLASSES,
    NOTE_LETTERS,
    QUALITY_ALIASES,
    QUALITY_DISPLAY_NAMES,
    ROOT_PITCH_CLASSES,
    ROOT_QUALITY_RE,
    SHARP_NOTE_NAMES,
    TARGET_CHORD_RE,
    THEORY_GROUNDING_LINES,
    DIRECT_CHORD_RE,
)


def get_default_theory_prompt_lines() -> List[str]:
    return list(THEORY_GROUNDING_LINES)


def is_note_query(text: str) -> bool:
    lowered = text.lower()
    return "note" in lowered or "notes" in lowered


def extract_chord_tokens(text: str) -> Tuple[Optional[str], Optional[str]]:
    root = None
    quality = None

    target_match = TARGET_CHORD_RE.search(text)
    root_match = ROOT_QUALITY_RE.search(text)
    direct_match = DIRECT_CHORD_RE.search(text)
    compact_match = COMPACT_CHORD_RE.search(text)

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

    return root, quality


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

    if not is_note_query(text):
        return None

    root, quality = extract_chord_tokens(text)

    if not root or not quality:
        return None

    normalized_root = normalize_root_name(root)
    normalized_quality = normalize_quality_name(quality)

    if normalized_root not in ROOT_PITCH_CLASSES or normalized_quality not in CHORD_INTERVALS:
        return None

    return normalized_root, normalized_quality


def normalize_quality_name(quality: str) -> str:
    normalized = quality.lower().replace(" ", "")
    return QUALITY_ALIASES.get(normalized, normalized)


def normalize_root_name(root: str) -> str:
    return root[0].upper() + root[1:]


def get_default_note_map(root: str) -> Dict[int, str]:
    return FLAT_NOTE_NAMES if "b" in root else SHARP_NOTE_NAMES


def _spell_note_by_degree(root: str, interval: int) -> Optional[str]:
    degree = INTERVAL_DEGREES.get(interval)
    if degree is None:
        return None

    root_letter = root[0].upper()
    target_letter = NOTE_LETTERS[(NOTE_LETTERS.index(root_letter) + (degree - 1)) % len(NOTE_LETTERS)]
    target_pc = (ROOT_PITCH_CLASSES[root] + interval) % 12
    natural_pc = NATURAL_LETTER_PITCH_CLASSES[target_letter]
    offset = (target_pc - natural_pc + 12) % 12
    if offset > 6:
        offset -= 12

    if offset < -2 or offset > 2:
        return None
    if offset == 2:
        if interval == 11:
            return None
        candidate = "{0}##".format(target_letter)
    elif offset == 1:
        candidate = "{0}#".format(target_letter)
    elif offset == -1:
        candidate = "{0}b".format(target_letter)
    elif offset == -2:
        candidate = "{0}bb".format(target_letter)
    else:
        candidate = target_letter

    if "b" in root and candidate in {"Cb", "Fb"} and degree == 7:
        return None
    return candidate


def spell_note_for_interval(root: str, quality: str, interval: int, root_pc: int) -> str:
    note_pc = (root_pc + interval) % 12
    default_note_map = get_default_note_map(root)

    if (quality, interval) in FORCED_SHARP_INTERVALS:
        return SHARP_NOTE_NAMES[note_pc]

    if quality == "7alt" and interval == 15:
        return default_note_map[note_pc]

    if quality == "dim7" and "#" in root:
        return SHARP_NOTE_NAMES[note_pc]

    if (quality, interval) in FORCED_FLAT_INTERVALS:
        return FLAT_NOTE_NAMES[note_pc]

    if interval == 3 and quality in MINOR_FAMILY_QUALITIES:
        spelled = _spell_note_by_degree(root, interval)
        if spelled is not None and "bb" not in spelled:
            return spelled
        return default_note_map[note_pc]

    if interval == 3 and quality in DIMINISHED_FAMILY_QUALITIES:
        note_map = SHARP_NOTE_NAMES if "#" in root else FLAT_NOTE_NAMES
        return note_map[note_pc]

    spelled = None
    if quality not in DIMINISHED_FAMILY_QUALITIES:
        spelled = _spell_note_by_degree(root, interval)
    if spelled is not None:
        return spelled

    return default_note_map[note_pc]


def spell_chord_notes(root: str, quality: str) -> Optional[List[str]]:
    normalized_root = normalize_root_name(root)
    normalized_quality = normalize_quality_name(quality)

    if normalized_root not in ROOT_PITCH_CLASSES or normalized_quality not in CHORD_INTERVALS:
        return None

    root_pc = ROOT_PITCH_CLASSES[normalized_root]
    return [
        spell_note_for_interval(normalized_root, normalized_quality, interval, root_pc)
        for interval in CHORD_INTERVALS[normalized_quality]
    ]


def render_chord_name(root: str, quality: str) -> str:
    normalized_quality = normalize_quality_name(quality)

    if normalized_quality in COMPACT_RENDER_QUALITIES:
        return "{0}{1}".format(root, normalized_quality)

    display_name = QUALITY_DISPLAY_NAMES.get(normalized_quality)
    if display_name is not None:
        return "{0}{1}".format(root, display_name)

    return "{0} {1}".format(root, normalized_quality)


def natural_join(parts: List[str]) -> str:
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return "{0} and {1}".format(parts[0], parts[1])
    return "{0}, and {1}".format(", ".join(parts[:-1]), parts[-1])
