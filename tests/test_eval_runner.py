import json
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
EVAL_CASES = ROOT / "evals" / "cases"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from apeirograph_brain.cli import main
from apeirograph_brain.eval_runner import run_eval_pack


class EvalRunnerTests(unittest.TestCase):
    def test_run_eval_pack_produces_rubric_summary(self):
        report = run_eval_pack(EVAL_CASES)

        self.assertGreaterEqual(report["total_cases"], 5)
        self.assertIn("correctness", report["rubric_dimensions"])
        self.assertIn("usefulness", report["rubric_dimensions"])
        self.assertIn("clarity", report["rubric_dimensions"])
        self.assertEqual(len(report["cases"]), report["total_cases"])

    def test_cli_can_render_eval_summary(self):
        output = StringIO()

        with redirect_stdout(output):
            result = main(["--run-evals"])

        self.assertEqual(result, 0)
        rendered = json.loads(output.getvalue())
        self.assertIn("average_scores", rendered)
        self.assertIn("cases", rendered)


if __name__ == "__main__":
    unittest.main()
