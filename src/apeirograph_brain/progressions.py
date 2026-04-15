import re
from typing import Dict, List, Optional, Sequence, Union

from apeirograph_brain.keys import build_diatonic_triads
from apeirograph_brain.schemas import ChordObject

TONIC_ROMANS = {"I", "i", "iii", "III", "vi", "VI"}
PREDOMINANT_ROMANS = {"ii", "ii°", "IV", "iv"}
DOMINANT_ROMANS = {"V", "V7", "v", "v7", "vii°", "viiø7", "VII"}


def normalize_root_name(root: str) -> str:
    normalized = root.strip()
    if not normalized:
        raise ValueError("root must not be empty")
    return normalized[0].upper() + normalized[1:]


def normalize_quality_name(quality: str) -> str:
    normalized = quality.lower().replace(" ", "")
    if normalized in {"", "major", "maj"}:
        return "major"
    if normalized in {"minor", "min", "m"}:
        return "minor"
    if normalized in {"major7", "maj7"}:
        return "major7"
    if normalized in {"minor7", "m7"}:
        return "minor7"
    if normalized in {"dominant7", "7"}:
        return "dominant7"
    if normalized in {"m7b5", "halfdiminished7"}:
        return "m7b5"
    if normalized in {"dim", "diminished"}:
        return "diminished"
    if normalized in {"dim7"}:
        return "dim7"
    return normalized


def parse_chord_symbol(symbol: str) -> Dict[str, str]:
    text = symbol.strip()
    match = re.match(r"^(?P<root>[A-G](?:#|b)?)(?P<suffix>.*)$", text)
    if not match:
        raise ValueError("Unsupported chord symbol: {0}".format(symbol))

    root = normalize_root_name(match.group("root"))
    suffix = match.group("suffix").strip()

    if suffix in {"", "maj"}:
        quality = "major"
    elif suffix == "m":
        quality = "minor"
    elif suffix == "7":
        quality = "dominant7"
    elif suffix == "maj7":
        quality = "major7"
    elif suffix == "m7":
        quality = "minor7"
    elif suffix == "m7b5":
        quality = "m7b5"
    elif suffix == "dim":
        quality = "diminished"
    else:
        quality = normalize_quality_name(suffix)

    return {"root": root, "quality": quality}


def base_quality_family(quality: str) -> str:
    normalized = normalize_quality_name(quality)
    if normalized in {"minor", "minor7"}:
        return "minor"
    if normalized in {"diminished", "dim7", "m7b5"}:
        return "diminished"
    return "major"


def roman_suffix_for_quality(quality: str) -> str:
    normalized = normalize_quality_name(quality)
    if normalized == "major7":
        return "maj7"
    if normalized in {"minor7", "dominant7"}:
        return "7"
    if normalized == "m7b5":
        return "ø7"
    if normalized == "dim7":
        return "°7"
    return ""


def roman_numeral_for_chord(root: str, quality: str, key_root: str, mode: str) -> Optional[str]:
    normalized_root = normalize_root_name(root)
    triads = build_diatonic_triads(key_root, mode)
    base_family = base_quality_family(quality)
    suffix = roman_suffix_for_quality(quality)

    for roman, chord_name in triads.items():
        triad = parse_chord_symbol(chord_name)
        if triad["root"] != normalized_root:
            continue

        triad_family = base_quality_family(triad["quality"])
        if triad_family != base_family:
            return None

        if suffix == "ø7" and not roman.endswith("°"):
            return None
        if suffix == "°7" and not roman.endswith("°"):
            return None

        if suffix and roman.endswith("°") and suffix == "ø7":
            return roman[:-1] + suffix
        return roman + suffix

    return None


def harmonic_function_for_roman(roman: Optional[str]) -> str:
    if roman is None:
        return "chromatic"

    base = roman.replace("maj7", "").replace("7", "")
    if roman in DOMINANT_ROMANS or base in DOMINANT_ROMANS:
        return "dominant"
    if roman in PREDOMINANT_ROMANS or base in PREDOMINANT_ROMANS:
        return "predominant"
    if roman in TONIC_ROMANS or base in TONIC_ROMANS:
        return "tonic"
    return "color"


def analyze_progression(chords: Sequence[ChordObject], key_root: str, mode: str) -> List[Dict[str, str]]:
    analysis = []
    for chord in chords:
        roman = roman_numeral_for_chord(chord.root, chord.quality, key_root, mode)
        analysis.append(
            {
                "chord": chord.label or "{0}{1}".format(chord.root, chord.quality),
                "roman": roman or "?",
                "function": harmonic_function_for_roman(roman),
            }
        )
    return analysis


def detect_cadence(chords: Sequence[Union[str, ChordObject]], key_root: str, mode: str) -> Optional[str]:
    if len(chords) < 2:
        return None

    romans: List[Optional[str]] = []
    for chord in chords[-2:]:
        if isinstance(chord, ChordObject):
            roman = roman_numeral_for_chord(chord.root, chord.quality, key_root, mode)
        else:
            parsed = parse_chord_symbol(chord)
            roman = roman_numeral_for_chord(parsed["root"], parsed["quality"], key_root, mode)
        romans.append(roman)

    left, right = romans
    if left in {"V", "V7", "v", "v7"} and right in {"I", "Imaj7", "i", "i7", "imaj7"}:
        return "authentic"
    if left in {"IV", "iv"} and right in {"I", "i"}:
        return "plagal"
    if left in {"V", "V7", "v", "v7"} and right in {"vi", "VI"}:
        return "deceptive"
    if right in {"V", "V7", "v", "v7"}:
        return "half"
    return None
