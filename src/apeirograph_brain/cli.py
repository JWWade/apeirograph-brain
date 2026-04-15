import argparse
from typing import List, Optional

from apeirograph_brain.ollama_client import OllamaClient, OllamaConnectionError
from apeirograph_brain.settings import get_ollama_settings, get_project_paths


def build_default_system_prompt() -> str:
    lines = [
        "You are a careful music-theory assistant for harmonic analysis.",
        "Use standard tonal terminology and exact pitch spelling.",
        "Never invent chord tones, scale degrees, or harmonic functions.",
        "When asked about a chord, name its exact notes first.",
        "For a major triad, the chord tones are root, major third, and perfect fifth.",
        "C major triad = C-E-G.",
        "A minor triad = A-C-E.",
        "If the user asks for one short sentence, answer in one short sentence.",
        "If you are unsure, say you are unsure instead of guessing.",
    ]
    return "\n".join(lines)


def build_startup_report() -> str:
    paths = get_project_paths()
    settings = get_ollama_settings()
    client = OllamaClient(settings=settings)

    checks = [
        ("src", paths.src.exists()),
        ("data", paths.data.exists()),
        ("evals", paths.evals.exists()),
        ("tests", paths.tests.exists()),
    ]

    try:
        available_models = client.list_models()
        ollama_status = "OK"
        model_status = "READY" if settings.model in available_models else "NOT PULLED"
    except OllamaConnectionError:
        available_models = []
        ollama_status = "UNREACHABLE"
        model_status = "UNKNOWN"

    lines: List[str] = [
        "Apeirograph Brain",
        "=================",
        "Local harmonic intelligence lab scaffold and schema layer are ready.",
        "",
        "Scaffold checks:",
    ]

    for name, exists in checks:
        status = "OK" if exists else "MISSING"
        lines.append("- {0}: {1}".format(name, status))

    lines.extend(
        [
            "",
            "Ollama runtime:",
            "- base URL: {0}".format(settings.base_url),
            "- default model: {0}".format(settings.model),
            "- runtime status: {0}".format(ollama_status),
            "- model status: {0}".format(model_status),
        ]
    )

    if available_models:
        lines.append("- installed models: {0}".format(", ".join(available_models)))

    lines.extend(
        [
            "",
            "Next recommended step:",
            "- run with --prompt to test a local model response",
            "- build explanation and suggestion workflows on top of the schemas",
        ]
    )

    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Apeirograph Brain local runtime")
    parser.add_argument("--prompt", help="Send a one-off prompt to the configured Ollama model")
    parser.add_argument("--system", help="Optional system message for the prompt")
    args = parser.parse_args(argv)

    if args.prompt:
        client = OllamaClient()
        system_prompt = args.system or build_default_system_prompt()
        try:
            print(client.generate(args.prompt, system=system_prompt, options={"temperature": 0.1}))
            return 0
        except KeyboardInterrupt:
            print("Request cancelled.")
            return 130
        except OllamaConnectionError as exc:
            print(str(exc))
            return 1

    print(build_startup_report())
    return 0
