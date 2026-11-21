from __future__ import annotations

import copy
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

from agent_runtime.calculation import execute
from agent_runtime.contracts import error_result
from agent_runtime.orchestration import run_task


VERSION = "1.2.0"


def _evaluate(operation: str, operands: list, domain: str = "real") -> dict:
    return {
        "contractVersion": VERSION,
        "operation": operation,
        "operands": operands,
        "domain": domain,
        "precision": {"mode": "exact", "decimalPlaces": 0},
    }


def _task(stages: list, **options) -> dict:
    return {"contractVersion": VERSION, "objective": "Executar cálculos locais compostos", "stages": stages, **options}


class CalculationOrchestrationTests(unittest.TestCase):
    def test_direct_task_executes_a_real_deterministic_capability(self):
        result = run_task(_task([{"id": "sum", "tool": "calculation.evaluate", "input": _evaluate("add", ["2", "3"])}]))
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["executed"])
        self.assertEqual(result["stages"][0]["mode"], "deterministic")
        self.assertEqual(result["stages"][0]["result"]["value"], "5")

    def test_composed_task_passes_only_a_declared_validated_numeric_value(self):
        task = _task(
            [
                {"id": "sum", "tool": "calculation.evaluate", "input": _evaluate("add", ["2", "3"])},
                {
                    "id": "scale",
                    "tool": "calculation.evaluate",
                    "dependsOn": ["sum"],
                    "input": _evaluate("multiply", [{"$resultFrom": "sum", "field": "value"}, "4"]),
                },
            ]
        )
        result = run_task(task)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["stages"][1]["result"]["value"], "20")
        self.assertEqual(result["checkpoint"]["completedStages"][1]["id"], "scale")

    def test_explicit_conversion_preserves_units_through_composition(self):
        result = run_task(
            _task(
                [
                    {
                        "id": "convert",
                        "tool": "calculation.convertUnits",
                        "input": {"contractVersion": VERSION, "amount": "1", "sourceUnit": "km", "targetUnit": "m", "decimalPlaces": 0},
                    },
                    {
                        "id": "sum",
                        "tool": "calculation.addQuantities",
                        "dependsOn": ["convert"],
                        "input": {
                            "contractVersion": VERSION,
                            "quantities": [
                                {"amount": {"$resultFrom": "convert", "field": "convertedAmount"}, "unit": "m"},
                                {"amount": "500", "unit": "m"},
                            ],
                        },
                    },
                ]
            )
        )
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["stages"][1]["result"]["sum"], "1500")
        self.assertEqual(result["stages"][1]["result"]["unit"], "m")

    def test_incompatible_units_block_before_consumer_tool_runs(self):
        calls = []

        def runner(tool, payload, _cancel):
            calls.append((tool, payload))
            return execute(tool, payload)

        task = _task(
            [
                {
                    "id": "convert",
                    "tool": "calculation.convertUnits",
                    "input": {"contractVersion": VERSION, "amount": "1", "sourceUnit": "km", "targetUnit": "m", "decimalPlaces": 0},
                },
                {
                    "id": "bad-sum",
                    "tool": "calculation.addQuantities",
                    "dependsOn": ["convert"],
                    "input": {
                        "contractVersion": VERSION,
                        "quantities": [
                            {"amount": {"$resultFrom": "convert", "field": "convertedAmount"}, "unit": "s"},
                            {"amount": "2", "unit": "s"},
                        ],
                    },
                },
            ]
        )
        result = run_task(task, execute_tool=runner)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["stages"][1]["status"], "blocked")
        self.assertEqual(result["stages"][1]["error"]["code"], "unit_mismatch")

    def test_domain_mismatch_blocks_without_coercion(self):
        def runner(tool, payload, _cancel):
            if payload.get("domain") == "complex":
                return {
                    "contractVersion": VERSION,
                    "status": "exact",
                    "operation": payload["operation"],
                    "value": "5",
                    "unit": "",
                    "method": "synthetic complex-domain source result",
                    "assumptions": [],
                    "errorBound": "0",
                }
            return execute(tool, payload)

        result = run_task(
            _task(
                [
                    {"id": "complex", "tool": "calculation.evaluate", "input": _evaluate("add", ["2", "3"], "complex")},
                    {
                        "id": "real",
                        "tool": "calculation.evaluate",
                        "dependsOn": ["complex"],
                        "input": _evaluate("multiply", [{"$resultFrom": "complex", "field": "value"}, "2"], "real"),
                    },
                ]
            ),
            execute_tool=runner,
        )
        self.assertEqual(result["stages"][0]["mode"], "simulated")
        self.assertEqual(result["stages"][1]["status"], "blocked")
        self.assertEqual(result["stages"][1]["error"]["code"], "domain_error")

    def test_symbolic_solution_cannot_be_reused_as_a_scalar(self):
        result = run_task(
            _task(
                [
                    {"id": "root", "tool": "calculation.solveEquation", "input": {"contractVersion": VERSION, "equation": "x = 2", "variable": "x", "domain": "real"}},
                    {
                        "id": "scale",
                        "tool": "calculation.evaluate",
                        "dependsOn": ["root"],
                        "input": _evaluate("multiply", [{"$resultFrom": "root", "field": "value"}, "4"]),
                    },
                ]
            )
        )
        self.assertEqual(result["stages"][1]["status"], "blocked")
        self.assertEqual(result["stages"][1]["error"]["code"], "invalid_request")

    def test_checkpoint_is_recomputed_and_tampering_is_rejected(self):
        task = _task([{"id": "sum", "tool": "calculation.evaluate", "input": _evaluate("add", ["2", "3"])}])
        first = run_task(task)
        resumed = run_task({**task, "resume": first["checkpoint"]})
        self.assertEqual(resumed["stages"][0]["mode"], "checkpoint_recomputed")
        self.assertTrue(resumed["executed"])
        self.assertEqual(resumed["stages"][0]["result"]["value"], "5")

        tampered = copy.deepcopy(first["checkpoint"])
        tampered["completedStages"][0]["resultDigest"] = "0" * 64
        rejected = run_task({**task, "resume": tampered})
        self.assertEqual(rejected["stages"][0]["status"], "failed")
        self.assertEqual(rejected["stages"][0]["error"]["code"], "invalid_request")

    def test_retry_only_occurs_for_explicit_retryable_error_and_clears_recovered_dependency(self):
        calls = 0

        def runner(tool, payload, _cancel):
            nonlocal calls
            calls += 1
            if calls == 1:
                return error_result("unavailable", "temporary", retryable=True)
            return execute(tool, payload)

        result = run_task(
            _task(
                [{"id": "sum", "tool": "calculation.evaluate", "input": _evaluate("add", ["2", "3"])}],
                limits={"maxAttempts": 2},
            ),
            execute_tool=runner,
        )
        self.assertEqual(calls, 2)
        self.assertEqual(result["stages"][0]["attempts"], 2)
        self.assertEqual(result["missingDependencies"], [])
        self.assertEqual(result["status"], "completed")

    def test_cancel_timeout_and_output_budget_are_observable(self):
        cancelled = threading.Event()
        cancelled.set()
        task = _task([{"id": "sum", "tool": "calculation.evaluate", "input": _evaluate("add", ["2", "3"])}])
        self.assertEqual(run_task(task, cancel_event=cancelled)["status"], "cancelled")

        ticks = iter([0.0, 0.0, 0.0, 2.0, 2.0])
        timed = run_task({**task, "limits": {"timeoutMs": 1_000}}, clock=lambda: next(ticks, 2.0))
        self.assertEqual(timed["status"], "timed_out")

        oversized = _task(
            [{"id": "solve", "tool": "calculation.solveSystem", "input": {"contractVersion": VERSION, "equations": ["x + 1 = 2"] * 10, "variables": ["x"], "domain": "real"}}],
            limits={"maxOutputBytes": 1024},
        )
        self.assertEqual(run_task(oversized)["code"], "limit_exceeded")

    def test_task_graph_rejects_forward_and_undeclared_references(self):
        consumer = {
            "id": "second",
            "tool": "calculation.evaluate",
            "input": _evaluate("add", [{"$resultFrom": "first", "field": "value"}, "1"]),
        }
        self.assertEqual(run_task(_task([consumer]))["code"], "invalid_request")
        producer = {"id": "first", "tool": "calculation.evaluate", "input": _evaluate("add", ["2", "3"])}
        self.assertEqual(run_task(_task([producer, consumer]))["code"], "invalid_request")

    def test_simultaneous_tasks_keep_results_and_ids_isolated(self):
        def calculate(pair):
            left, right = pair
            return run_task(_task([{"id": "sum", "tool": "calculation.evaluate", "input": _evaluate("add", [str(left), str(right)])}]))

        with ThreadPoolExecutor(max_workers=2) as pool:
            a, b = list(pool.map(calculate, [(2, 3), (10, 7)]))
        self.assertNotEqual(a["taskId"], b["taskId"])
        self.assertEqual(a["stages"][0]["result"]["value"], "5")
        self.assertEqual(b["stages"][0]["result"]["value"], "17")


if __name__ == "__main__":
    unittest.main()
