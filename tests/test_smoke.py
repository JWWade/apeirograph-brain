import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from apeirograph_brain.cli import build_startup_report
from apeirograph_brain.settings import get_project_paths

import app


class ScaffoldSmokeTests(unittest.TestCase):
    def test_entrypoint_prefers_project_virtualenv_python(self):
        preferred = app.resolve_preferred_python_executable(
            current_executable=str(ROOT / "fake-python.exe"),
            root=ROOT,
        )
        self.assertEqual(preferred, str(ROOT / ".venv" / "Scripts" / "python.exe"))

    def test_startup_report_mentions_lab(self):
        report = build_startup_report()
        self.assertIn("Local harmonic intelligence lab scaffold and schema layer are ready.", report)

    def test_expected_directories_exist(self):
        paths = get_project_paths(ROOT)
        self.assertTrue(paths.src.exists())
        self.assertTrue(paths.data.exists())
        self.assertTrue(paths.evals.exists())
        self.assertTrue(paths.tests.exists())


if __name__ == "__main__":
    unittest.main()
