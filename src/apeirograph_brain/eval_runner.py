from pathlib import Path
from typing import Dict, List

from apeirograph_brain.explain import explain_file
from apeirograph_brain.ollama_client import OllamaConnectionError
from apeirograph_brain.suggest import suggest_file

RUBRIC_DIMENSIONS = ["correctness", "usefulness", "clarity"]


class _DisabledModelClient:
    def generate(self, prompt, system=None, options=None):
        raise OllamaConnectionError("Eval runner is using the fast deterministic path.")


def run_eval_pack(eval_cases_path, use_model=False) -> Dict[str, object]:
    base = Path(eval_cases_path)
    case_paths = sorted(path for path in base.glob("*.json") if path.is_file())

    cases: List[Dict[str, object]] = []
    total_scores = {name: 0.0 for name in RUBRIC_DIMENSIONS}
    client = None if use_model else _DisabledModelClient()

    for case_path in case_paths:
        case_report = _run_single_case(case_path, client=client)
        cases.append(case_report)
        for name in RUBRIC_DIMENSIONS:
            total_scores[name] += case_report["scores"][name]

    total_cases = len(cases)
    average_scores = {}
    if total_cases:
        for name in RUBRIC_DIMENSIONS:
            average_scores[name] = round(total_scores[name] / float(total_cases), 2)
    else:
        for name in RUBRIC_DIMENSIONS:
            average_scores[name] = 0.0

    return {
        "prompt_profile": "local-mvp-live" if use_model else "local-mvp-fast",
        "rubric_dimensions": RUBRIC_DIMENSIONS,
        "total_cases": total_cases,
        "average_scores": average_scores,
        "cases": cases,
    }


def _run_single_case(case_path: Path, client=None) -> Dict[str, object]:
    workflow = _infer_workflow(case_path)

    if workflow == "explain":
        response = explain_file(str(case_path), client=client)
        scores = _score_explanation(response)
        preview = response.summary
        expected_qualities = [
            "musically correct note content",
            "clear plain-language explanation",
            "structured tension, symmetry, and motion fields",
        ]
    else:
        response = suggest_file(str(case_path), client=client)
        scores = _score_suggestion(response)
        preview = response.advisory_note
        expected_qualities = [
            "three plausible next moves",
            "short rationale for each candidate",
            "grounded harmonic vocabulary",
        ]

    overall = round(sum(scores.values()) / float(len(scores)), 2)

    return {
        "name": case_path.stem,
        "workflow": workflow,
        "scores": scores,
        "overall": overall,
        "expected_qualities": expected_qualities,
        "preview": preview,
    }


def _infer_workflow(case_path: Path) -> str:
    name = case_path.stem.lower()
    if name.startswith("suggest-"):
        return "suggest"
    return "explain"


def _score_explanation(response) -> Dict[str, float]:
    correctness = 5.0 if response.summary and response.tension_level in {"low", "medium", "high"} else 2.0
    usefulness = 5.0 if len(response.salient_properties) >= 2 and bool(response.motion_note) else 3.0
    clarity = 5.0 if len(response.summary.split()) <= 30 else 4.0
    return {
        "correctness": correctness,
        "usefulness": usefulness,
        "clarity": clarity,
    }


def _score_suggestion(response) -> Dict[str, float]:
    has_three = len(response.suggestions) == 3
    distinct_roots = len({item.next_chord.root for item in response.suggestions}) == len(response.suggestions)
    correctness = 5.0 if has_three and distinct_roots else 3.0
    usefulness = 5.0 if all(item.rationale for item in response.suggestions) else 3.0
    clarity = 5.0 if response.advisory_note and len(response.advisory_note.split()) <= 24 else 4.0
    return {
        "correctness": correctness,
        "usefulness": usefulness,
        "clarity": clarity,
    }
