import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
_BOOTSTRAP_ENV_VAR = "APEIROGRAPH_BOOTSTRAPPED"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def resolve_preferred_python_executable(current_executable=None, root=None):
    base = Path(root) if root else ROOT
    current = Path(current_executable or sys.executable).resolve()
    candidates = [
        base / ".venv" / "Scripts" / "python.exe",
        base / ".venv" / "bin" / "python",
    ]

    for candidate in candidates:
        if candidate.exists():
            resolved_candidate = candidate.resolve()
            if resolved_candidate != current:
                return str(candidate)
            return str(resolved_candidate)

    return str(current)


def ensure_project_virtualenv() -> None:
    if os.environ.get(_BOOTSTRAP_ENV_VAR) == "1":
        return

    preferred = resolve_preferred_python_executable()
    current = str(Path(sys.executable).resolve())

    if preferred and str(Path(preferred).resolve()) != current:
        env = os.environ.copy()
        env[_BOOTSTRAP_ENV_VAR] = "1"
        completed = subprocess.run([preferred, __file__] + sys.argv[1:], env=env)
        raise SystemExit(completed.returncode)


ensure_project_virtualenv()

try:
    from apeirograph_brain.cli import main
except ModuleNotFoundError as exc:
    print(
        "Missing dependency: {0}. Activate the project virtual environment or install requirements with 'pip install -r requirements.txt'.".format(
            exc.name
        )
    )
    raise SystemExit(1)


if __name__ == "__main__":
    raise SystemExit(main())
