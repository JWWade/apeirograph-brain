import argparse
from typing import List, Optional

from apeirograph_brain.chord_spelling import get_default_theory_prompt_lines, try_answer_basic_chord_note_prompt
from apeirograph_brain.eval_runner import run_eval_pack
from apeirograph_brain.explain import explain_file
from apeirograph_brain.ollama_client import OllamaClient, OllamaConnectionError
from apeirograph_brain.settings import get_ollama_settings, get_project_paths
from apeirograph_brain.suggest import suggest_file


def build_default_system_prompt() -> str:
    return "\n".join(get_default_theory_prompt_lines())


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
    parser.add_argument("--explain-file", help="Explain a JSON chord or progression file and return structured analysis")
    parser.add_argument("--suggest-file", help="Suggest three next-move options from a JSON progression file")
    parser.add_argument("--run-evals", action="store_true", help="Run the starter eval pack and print a summary report")
    parser.add_argument("--eval-live-model", action="store_true", help="Use live model calls during eval runs instead of the fast deterministic path")
    args = parser.parse_args(argv)

    if args.run_evals:
        try:
            eval_report = run_eval_pack(get_project_paths().evals / "cases", use_model=args.eval_live_model)
            import json
            print(json.dumps(eval_report, indent=2))
            return 0
        except KeyboardInterrupt:
            print("Request cancelled.")
            return 130
        except (OllamaConnectionError, ValueError, OSError) as exc:
            print(str(exc))
            return 1

    if args.explain_file:
        try:
            response = explain_file(args.explain_file)
            print(response.json(indent=2))
            return 0
        except KeyboardInterrupt:
            print("Request cancelled.")
            return 130
        except (OllamaConnectionError, ValueError, OSError) as exc:
            print(str(exc))
            return 1

    if args.suggest_file:
        try:
            response = suggest_file(args.suggest_file)
            print(response.json(indent=2))
            return 0
        except KeyboardInterrupt:
            print("Request cancelled.")
            return 130
        except (OllamaConnectionError, ValueError, OSError) as exc:
            print(str(exc))
            return 1

    if args.prompt:
        deterministic_answer = try_answer_basic_chord_note_prompt(args.prompt)
        if deterministic_answer:
            print(deterministic_answer)
            return 0

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
