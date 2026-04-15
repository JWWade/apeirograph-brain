from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    src: Path
    data: Path
    evals: Path
    tests: Path


def get_project_paths(root: Optional[Path] = None) -> ProjectPaths:
    base = root or Path(__file__).resolve().parents[2]
    return ProjectPaths(
        root=base,
        src=base / "src",
        data=base / "data",
        evals=base / "evals",
        tests=base / "tests",
    )
