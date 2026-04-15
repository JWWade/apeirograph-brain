import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from apeirograph_brain.ollama_client import OllamaClient, OllamaConnectionError
from apeirograph_brain.progressions import analyze_progression, detect_cadence
from apeirograph_brain.schemas import ChordObject, ExplanationResponse, ProgressionInput

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


def load_explain_input(payload: Any) -> ProgressionInput:
    if isinstance(payload, (str, Path)):
        path = Path(payload)
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

    if not isinstance(payload, dict):
        raise ValueError("Explanation input must be a JSON object.")

    if "progression" in payload and isinstance(payload["progression"], dict):
        payload = payload["progression"]

    if "chords" in payload:
        return ProgressionInput(**payload)

    chord = ChordObject(**payload)
    return ProgressionInput(chords=[chord], intent="Explain this harmonic object.")


def build_explanation_system_prompt() -> str:
    lines = [
        "You are a precise music-theory analyst.",
        "Use only the supplied facts.",
        "Do not invent notes, functions, or chord members.",
        "Return one concise explanation sentence.",
        "Prefer grounded tonal language such as stable, bright, tense, symmetric, or smooth motion.",
    ]
    return "\n".join(lines)


def build_explanation_prompt(progression: ProgressionInput) -> str:
    lines: List[str] = [
        "Explain this harmonic object using the provided structured facts.",
        "",
        "Intent: {0}".format(progression.intent or "Explain the harmony clearly."),
        "Chord count: {0}".format(len(progression.chords)),
    ]

    for index, chord in enumerate(progression.chords, start=1):
        label = chord.label or "{0} {1}".format(chord.root, chord.quality)
        note_names = ", ".join(_note_names(chord.pitch_classes))
        lines.append(
            "Chord {0}: {1} | root={2} | quality={3} | pitch_classes={4} | note_names={5}".format(
                index,
                label,
                chord.root,
                chord.quality,
                chord.pitch_classes,
                note_names,
            )
        )

    if progression.scale_context:
        lines.append(
            "Scale context: {0} {1} with pitch classes {2}".format(
                progression.scale_context.root,
                progression.scale_context.mode,
                progression.scale_context.diatonic_pitch_classes,
            )
        )

    if progression.transform:
        lines.append(
            "Transform: {0} | {1}".format(
                progression.transform.operation,
                progression.transform.description or "no extra description",
            )
        )

    lines.append("Keep the answer factual and concise.")
    return "\n".join(lines)


def explain_progression(progression: ProgressionInput, client: Optional[OllamaClient] = None) -> ExplanationResponse:
    salient_properties = _build_salient_properties(progression)
    tension_level = _infer_tension_level(progression)
    symmetry_note = _build_symmetry_note(progression)
    motion_note = _build_motion_note(progression)
    fallback_summary = _build_fallback_summary(progression, tension_level)

    summary = fallback_summary
    confidence = 0.84
    caveats: List[str] = []

    model_client = client or OllamaClient()
    try:
        model_summary = model_client.generate(
            build_explanation_prompt(progression),
            system=build_explanation_system_prompt(),
            options={"temperature": 0.1},
        )
        if model_summary and _model_summary_is_grounded(model_summary, progression):
            summary = model_summary.strip().splitlines()[0]
            confidence = 0.88
        elif model_summary:
            caveats.append("Used deterministic summary because the model wording was not grounded enough.")
    except OllamaConnectionError:
        caveats.append("Used fallback explanation because the local model was unavailable.")
    except Exception:
        caveats.append("Used fallback explanation because the model response was not reliable.")

    return ExplanationResponse(
        summary=summary,
        salient_properties=salient_properties,
        tension_level=tension_level,
        symmetry_note=symmetry_note,
        motion_note=motion_note,
        confidence=confidence,
        caveats=caveats,
    )


def explain_file(file_path: str, client: Optional[OllamaClient] = None) -> ExplanationResponse:
    progression = load_explain_input(file_path)
    return explain_progression(progression, client=client)


def _note_names(pitch_classes: List[int]) -> List[str]:
    return [NOTE_NAMES[int(value) % 12] for value in sorted({int(item) % 12 for item in pitch_classes})]


def _build_salient_properties(progression: ProgressionInput) -> List[str]:
    properties: List[str] = []
    chord_count = len(progression.chords)
    properties.append("{0} chord{1}".format(chord_count, "" if chord_count == 1 else "s"))

    first = progression.chords[0]
    properties.append("opens on {0} {1}".format(first.root, first.quality))
    properties.append("pitch content: {0}".format(", ".join(_note_names(first.pitch_classes))))

    if progression.scale_context:
        properties.append("scale context: {0} {1}".format(progression.scale_context.root, progression.scale_context.mode))
        if all(_is_diatonic(chord, progression) for chord in progression.chords):
            properties.append("all chords remain diatonic to the given scale")
        else:
            properties.append("includes non-diatonic color against the scale context")

        mode_name = _normalize_mode_for_analysis(progression.scale_context.mode)
        analysis = analyze_progression(
            progression.chords,
            progression.scale_context.root,
            mode_name,
        )
        for item in analysis:
            if item["roman"] not in properties:
                properties.append(item["roman"])
            properties.append("{0} = {1} ({2})".format(item["chord"], item["roman"], item["function"]))

        cadence = detect_cadence(progression.chords, progression.scale_context.root, mode_name)
        if cadence:
            properties.append("ends with an {0} cadence".format(cadence))

    if progression.transform:
        properties.append("transform: {0}".format(progression.transform.operation))

    return properties


def _infer_tension_level(progression: ProgressionInput) -> str:
    score = 0

    for chord in progression.chords:
        quality = chord.quality.lower()
        if "dim" in quality or "alt" in quality or "aug" in quality:
            score += 2
        elif "7" in quality and "maj7" not in quality:
            score += 1
        elif "sus" in quality:
            score += 1

        if progression.scale_context and not _is_diatonic(chord, progression):
            score += 1

    if score <= 1:
        return "low"
    if score <= 3:
        return "medium"
    return "high"


def _build_symmetry_note(progression: ProgressionInput) -> str:
    first = progression.chords[0]
    chord_size = len(first.pitch_classes)

    if chord_size == 3:
        return "The chord uses balanced triadic spacing, which supports a clear tonal center without strong symmetry effects."
    if chord_size == 4:
        return "The sonority is evenly distributed enough to feel coherent, though it still preserves tonal direction more than strict symmetry."
    return "The pitch collection feels organized and readable rather than fully symmetrical."


def _build_motion_note(progression: ProgressionInput) -> str:
    if len(progression.chords) == 1:
        return "With only one chord present, the motion is static and centered on its local color."

    root_steps: List[int] = []
    for left, right in zip(progression.chords, progression.chords[1:]):
        left_pc = ROOT_PITCH_CLASSES.get(left.root, 0)
        right_pc = ROOT_PITCH_CLASSES.get(right.root, 0)
        step = (right_pc - left_pc) % 12
        root_steps.append(min(step, 12 - step))

    average_step = sum(root_steps) / float(len(root_steps))
    if average_step <= 2.5:
        return "The roots move by relatively small intervals, suggesting smooth, connected harmonic motion."
    if average_step <= 4.5:
        return "The roots shift with moderate contrast, giving the phrase some forward pull without sounding abrupt."
    return "The roots move with wider jumps, creating a more dramatic sense of directional change."


def _build_fallback_summary(progression: ProgressionInput, tension_level: str) -> str:
    first = progression.chords[0]
    note_names = _natural_join(_note_names(first.pitch_classes))

    if len(progression.chords) == 1:
        return "This {0} {1} chord uses the notes {2} and gives a {3}-tension, stable harmonic color.".format(
            first.root,
            first.quality,
            note_names,
            tension_level,
        )

    labels = [chord.label or "{0}{1}".format(chord.root, chord.quality) for chord in progression.chords]
    path = " to ".join(labels)
    if progression.scale_context:
        mode_name = _normalize_mode_for_analysis(progression.scale_context.mode)
        analysis = analyze_progression(progression.chords, progression.scale_context.root, mode_name)
        roman_path = "-".join(item["roman"] for item in analysis)
        cadence = detect_cadence(progression.chords, progression.scale_context.root, mode_name)
        cadence_text = " It closes with an {0} cadence.".format(cadence) if cadence else ""
        return "This phrase stays within {0} {1} and moves from {2} as {3}, creating {4} tension with readable forward motion.{5}".format(
            progression.scale_context.root,
            progression.scale_context.mode,
            path,
            roman_path,
            tension_level,
            cadence_text,
        )

    return "This phrase moves from {0} and creates a {1} level of tension across the progression.".format(
        path,
        tension_level,
    )


def _model_summary_is_grounded(summary: str, progression: ProgressionInput) -> bool:
    text = summary.lower().strip()
    if not text:
        return False

    banned_terms = [
        "subdominant",
        "secondary dominant",
        "tritone substitution",
        "deceptive cadence",
    ]
    if any(term in text for term in banned_terms):
        return False

    root_mentions = sum(1 for chord in progression.chords if chord.root.lower() in text)
    if len(progression.chords) == 1:
        note_names = [name.lower() for name in _note_names(progression.chords[0].pitch_classes)]
        return root_mentions >= 1 and all(name in text for name in note_names)

    if root_mentions < len(progression.chords):
        return False

    if progression.scale_context:
        if progression.scale_context.root.lower() not in text:
            return False
        if progression.scale_context.mode.lower() not in text:
            return False

    return True


def _normalize_mode_for_analysis(mode: str) -> str:
    if mode.lower().strip() == "ionian":
        return "major"
    if mode.lower().strip() == "aeolian":
        return "minor"
    return mode


def _natural_join(parts: List[str]) -> str:
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return "{0} and {1}".format(parts[0], parts[1])
    return "{0}, and {1}".format(", ".join(parts[:-1]), parts[-1])


def _is_diatonic(chord: ChordObject, progression: ProgressionInput) -> bool:
    if not progression.scale_context:
        return True
    diatonic = set(progression.scale_context.diatonic_pitch_classes)
    return set(chord.pitch_classes).issubset(diatonic)
