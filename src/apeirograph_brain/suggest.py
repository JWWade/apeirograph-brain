import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from apeirograph_brain.ollama_client import OllamaClient, OllamaConnectionError
from apeirograph_brain.schemas import HarmonicTransform, ProgressionInput, SuggestionCandidate, SuggestionResponse

NOTE_NAMES = {
    0: "C",
    1: "C#",
    2: "D",
    3: "Eb",
    4: "E",
    5: "F",
    6: "F#",
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

DEFAULT_CHORDS = {
    "major7": [0, 4, 7, 11],
    "dominant7": [0, 4, 7, 10],
    "minor7": [0, 3, 7, 10],
    "major": [0, 4, 7],
    "minor": [0, 3, 7],
}


def load_suggest_input(payload: Any) -> ProgressionInput:
    if isinstance(payload, (str, Path)):
        path = Path(payload)
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

    if not isinstance(payload, dict):
        raise ValueError("Suggestion input must be a JSON object.")

    if "progression" in payload and isinstance(payload["progression"], dict):
        payload = payload["progression"]

    if "chords" not in payload:
        raise ValueError("Suggestion input must include at least one chord in 'chords'.")

    return ProgressionInput(**payload)


def build_suggestion_system_prompt() -> str:
    lines = [
        "You are a careful harmonic assistant.",
        "Use only the supplied progression and scale facts.",
        "Do not invent notes, functions, or modulations.",
        "Return one short advisory sentence about the next harmonic move.",
    ]
    return "\n".join(lines)


def build_suggestion_prompt(progression: ProgressionInput, candidates: List[SuggestionCandidate]) -> str:
    lines = [
        "Suggest the next move for this progression in one short advisory sentence.",
        "Intent: {0}".format(progression.intent or "Keep the motion musically coherent."),
        "Observed progression:",
    ]

    for chord in progression.chords:
        lines.append("- {0} {1} ({2})".format(chord.root, chord.quality, ", ".join(_note_names(chord.pitch_classes))))

    if progression.scale_context:
        lines.append(
            "Scale context: {0} {1}".format(
                progression.scale_context.root,
                progression.scale_context.mode,
            )
        )

    lines.append("Candidate moves:")
    for candidate in candidates:
        lines.append("- {0}: {1}".format(candidate.label, candidate.rationale))

    lines.append("Keep the note grounded and practical.")
    return "\n".join(lines)


def suggest_next_moves(progression: ProgressionInput, client: Optional[OllamaClient] = None) -> SuggestionResponse:
    suggestions = _build_candidate_suggestions(progression)
    advisory_note = _fallback_advisory_note(progression, suggestions)
    confidence = 0.84
    caveats: List[str] = []

    model_client = client or OllamaClient()
    try:
        note = model_client.generate(
            build_suggestion_prompt(progression, suggestions),
            system=build_suggestion_system_prompt(),
            options={"temperature": 0.1},
        )
        if note and _advisory_note_is_grounded(note, suggestions):
            advisory_note = note.strip().splitlines()[0]
            confidence = 0.88
        elif note:
            caveats.append("Used deterministic advisory note because the model wording was not grounded enough.")
    except OllamaConnectionError:
        caveats.append("Used deterministic suggestions because the local model was unavailable.")
    except Exception:
        caveats.append("Used deterministic suggestions because the model response was not reliable.")

    return SuggestionResponse(
        advisory_note=advisory_note,
        suggestions=suggestions,
        confidence=confidence,
        caveats=caveats,
    )


def suggest_file(file_path: str, client: Optional[OllamaClient] = None) -> SuggestionResponse:
    progression = load_suggest_input(file_path)
    return suggest_next_moves(progression, client=client)


def _build_candidate_suggestions(progression: ProgressionInput) -> List[SuggestionCandidate]:
    if progression.scale_context:
        return _build_scale_aware_candidates(progression)
    return _build_generic_candidates(progression)


def _build_scale_aware_candidates(progression: ProgressionInput) -> List[SuggestionCandidate]:
    scale = progression.scale_context
    assert scale is not None

    ordered = _ordered_scale_pitch_classes(scale.root, scale.diatonic_pitch_classes)
    last_root_pc = ROOT_PITCH_CLASSES.get(progression.chords[-1].root, ordered[0])
    current_index = ordered.index(last_root_pc) if last_root_pc in ordered else 0

    target_indices = [ordered.index(ROOT_PITCH_CLASSES.get(scale.root, ordered[0])), (current_index + 3) % len(ordered), (current_index + 2) % len(ordered)]
    labels = ["Return to the tonal center", "Continue the forward pull", "Add a gentle color shift"]
    stabilities = ["stable", "balanced", "adventurous"]
    rationales = [
        "This brings the line back toward the scale center for a more settled arrival.",
        "This continues the phrase with clear motion and a practical next step.",
        "This keeps the vocabulary diatonic while adding a fresh change of color.",
    ]
    transforms = [
        HarmonicTransform(operation="tonic-return", description="Recenter the phrase on the home collection."),
        HarmonicTransform(operation="forward-motion", description="Keep the progression moving with functional pull."),
        HarmonicTransform(operation="color-shift", description="Introduce a nearby diatonic contrast without leaving the mode."),
    ]

    suggestions: List[SuggestionCandidate] = []
    seen_roots: Set[str] = set()

    for idx, label, stability, rationale, transform in zip(target_indices, labels, stabilities, rationales, transforms):
        chord = _build_diatonic_seventh_chord(scale.root, ordered, idx)
        if chord.root in seen_roots:
            continue
        seen_roots.add(chord.root)
        suggestions.append(
            SuggestionCandidate(
                label="{0}: {1}".format(label, chord.label),
                rationale=rationale,
                stability=stability,
                next_chord=chord,
                transform_hint=transform,
            )
        )

    while len(suggestions) < 3:
        extra_idx = (current_index + len(suggestions) + 1) % len(ordered)
        chord = _build_diatonic_seventh_chord(scale.root, ordered, extra_idx)
        if chord.root in seen_roots:
            continue
        seen_roots.add(chord.root)
        suggestions.append(
            SuggestionCandidate(
                label="Alternative move: {0}".format(chord.label),
                rationale="This offers another in-key option with moderate contrast.",
                stability="balanced",
                next_chord=chord,
                transform_hint=HarmonicTransform(operation="alternate-motion", description="Keep the line flexible while staying inside the scale."),
            )
        )

    return suggestions[:3]


def _build_generic_candidates(progression: ProgressionInput) -> List[SuggestionCandidate]:
    last = progression.chords[-1]
    last_pc = ROOT_PITCH_CLASSES.get(last.root, 0)

    options = [
        ("Return to center", "stable", "A return to the current root family keeps the phrase settled.", last.root, "major" if "minor" not in last.quality.lower() else "minor"),
        ("Move by fourth", "balanced", "A fourth-based move usually adds clear directional pull.", NOTE_NAMES[(last_pc + 5) % 12], "dominant7"),
        ("Neighbor color", "adventurous", "A nearby root change can add contrast without breaking coherence.", NOTE_NAMES[(last_pc + 2) % 12], "minor7"),
    ]

    suggestions: List[SuggestionCandidate] = []
    for label, stability, rationale, root, quality in options:
        suggestions.append(
            SuggestionCandidate(
                label="{0}: {1}{2}".format(label, root, _quality_suffix(quality)),
                rationale=rationale,
                stability=stability,
                next_chord=_build_chord(root, quality),
                transform_hint=HarmonicTransform(operation="generic-motion", description="A simple next-step move without explicit scale context."),
            )
        )

    return suggestions


def _ordered_scale_pitch_classes(scale_root: str, diatonic_pitch_classes: List[int]) -> List[int]:
    root_pc = ROOT_PITCH_CLASSES.get(scale_root, diatonic_pitch_classes[0])
    normalized = sorted({int(value) % 12 for value in diatonic_pitch_classes})
    return sorted(normalized, key=lambda value: (value - root_pc) % 12)


def _build_diatonic_seventh_chord(scale_root: str, ordered_scale: List[int], degree_index: int):
    root_pc = ordered_scale[degree_index]
    chord_pcs = [ordered_scale[(degree_index + step) % len(ordered_scale)] for step in [0, 2, 4, 6]]
    quality = _infer_quality_from_pitch_classes(root_pc, chord_pcs)
    root_name = NOTE_NAMES[root_pc]
    label = "{0}{1}".format(root_name, _quality_suffix(quality))

    from apeirograph_brain.schemas import ChordObject

    return ChordObject(root=root_name, quality=quality, pitch_classes=chord_pcs, label=label)


def _infer_quality_from_pitch_classes(root_pc: int, chord_pcs: List[int]) -> str:
    intervals = sorted(((value - root_pc) % 12 for value in chord_pcs))
    if intervals == [0, 4, 7, 11]:
        return "major7"
    if intervals == [0, 4, 7, 10]:
        return "dominant7"
    if intervals == [0, 3, 7, 10]:
        return "minor7"
    if intervals[:3] == [0, 4, 7]:
        return "major"
    if intervals[:3] == [0, 3, 7]:
        return "minor"
    return "minor7"


def _build_chord(root: str, quality: str):
    root_pc = ROOT_PITCH_CLASSES[root]
    intervals = DEFAULT_CHORDS.get(quality, DEFAULT_CHORDS["major"])
    pitch_classes = [((root_pc + interval) % 12) for interval in intervals]

    from apeirograph_brain.schemas import ChordObject

    return ChordObject(root=root, quality=quality, pitch_classes=pitch_classes, label="{0}{1}".format(root, _quality_suffix(quality)))


def _quality_suffix(quality: str) -> str:
    mapping = {
        "major7": "maj7",
        "dominant7": "7",
        "minor7": "m7",
        "major": "",
        "minor": "m",
    }
    return mapping.get(quality, quality)


def _note_names(pitch_classes: List[int]) -> List[str]:
    unique = sorted({int(value) % 12 for value in pitch_classes})
    return [NOTE_NAMES[value] for value in unique]


def _fallback_advisory_note(progression: ProgressionInput, suggestions: List[SuggestionCandidate]) -> str:
    first_label = suggestions[0].next_chord.label or suggestions[0].next_chord.root
    intent = progression.intent or "Keep the motion clear and musical."
    return "{0} A strong first option is {1}.".format(intent.strip(), first_label)


def _advisory_note_is_grounded(note: str, suggestions: List[SuggestionCandidate]) -> bool:
    text = note.lower().strip()
    if not text:
        return False

    banned_terms = ["chromatic mediant", "polychord", "twelve-tone", "random"]
    if any(term in text for term in banned_terms):
        return False

    allowed_tokens = set()
    for candidate in suggestions:
        allowed_tokens.add(candidate.next_chord.root.lower())
        if candidate.next_chord.label:
            allowed_tokens.add(candidate.next_chord.label.lower())

    mentioned_chords = re.findall(r"\b[A-G](?:#|b)?(?:maj7|m7|7|m)?\b", note)
    if mentioned_chords and any(token.lower() not in allowed_tokens for token in mentioned_chords):
        return False

    return any(token in text for token in allowed_tokens) or "stable" in text or "motion" in text
