import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    src: Path
    data: Path
    evals: Path
    tests: Path


@dataclass(frozen=True)
class OllamaSettings:
    base_url: str
    model: str
    timeout_seconds: int


def get_project_paths(root: Optional[Path] = None) -> ProjectPaths:
    base = root or Path(__file__).resolve().parents[2]
    return ProjectPaths(
        root=base,
        src=base / "src",
        data=base / "data",
        evals=base / "evals",
        tests=base / "tests",
    )


def get_ollama_settings(env: Optional[Mapping[str, str]] = None) -> OllamaSettings:
    source = os.environ if env is None else env

    base_url = str(source.get("APEIROGRAPH_OLLAMA_BASE_URL", "http://localhost:11434")).strip()
    model = str(source.get("APEIROGRAPH_OLLAMA_MODEL", "llama3.2:1b")).strip()
    timeout_raw = str(source.get("APEIROGRAPH_OLLAMA_TIMEOUT_SECONDS", "30")).strip()

    try:
        timeout_seconds = max(1, int(timeout_raw))
    except ValueError:
        timeout_seconds = 30

    return OllamaSettings(
        base_url=base_url.rstrip("/"),
        model=model,
        timeout_seconds=timeout_seconds,
    )
