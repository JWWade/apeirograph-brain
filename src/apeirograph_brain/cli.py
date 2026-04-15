from typing import List

from apeirograph_brain.settings import get_project_paths


def build_startup_report() -> str:
    paths = get_project_paths()

    checks = [
        ("src", paths.src.exists()),
        ("data", paths.data.exists()),
        ("evals", paths.evals.exists()),
        ("tests", paths.tests.exists()),
    ]

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
            "Next recommended step:",
            "- wire in Ollama for the first local model connection",
            "- build explanation and suggestion workflows on top of the schemas",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    print(build_startup_report())
    return 0
