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
        "Local harmonic intelligence lab scaffold is ready.",
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
            "- define the first harmonic domain schemas",
            "- wire in Ollama once the schema layer is stable",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    print(build_startup_report())
    return 0
