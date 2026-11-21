from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "run_runtime.py"


class RuntimeCliTaskTests(unittest.TestCase):
    def test_cli_runs_direct_and_composed_tasks(self):
        def evaluate(operation, operands):
            return {"contractVersion": "1.2.0", "operation": operation, "operands": operands, "domain": "real", "precision": {"mode": "exact", "decimalPlaces": 0}}

        task = {
            "contractVersion": "1.2.0",
            "objective": "Somar e depois multiplicar",
            "stages": [
                {"id": "sum", "tool": "calculation.evaluate", "input": evaluate("add", ["2", "3"])},
                {"id": "scale", "tool": "calculation.evaluate", "dependsOn": ["sum"], "input": evaluate("multiply", [{"$resultFrom": "sum", "field": "value"}, "4"])},
            ],
        }
        completed = subprocess.run(
            [sys.executable, str(CLI)], input=json.dumps({"task": task}), text=True, capture_output=True, cwd=ROOT, timeout=15, check=False
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["stages"][1]["result"]["value"], "20")


if __name__ == "__main__":
    unittest.main()
