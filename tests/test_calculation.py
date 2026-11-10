from __future__ import annotations

import unittest

from agent_runtime.calculation import execute, execute_text_request, parse_text_request
from agent_runtime.local_model import LocalModel, ModelCallError
from agent_runtime.contracts import TOOLS


class FakeModel:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def generate_json(self, instruction, data, *, cancel_event=None):
        self.calls += 1
        return self.response


class CalculationTests(unittest.TestCase):
    def test_exact_arithmetic_uses_deterministic_tool(self):
        request = {
            "contractVersion": "1.0.0",
            "operation": "divide",
            "operands": ["1", "3"],
            "domain": "real",
            "precision": {"mode": "exact", "decimalPlaces": 8},
        }
        result = execute("calculation.evaluate", request)
        self.assertEqual(result["status"], "exact")
        self.assertEqual(result["value"], "1/3")

    def test_decimal_division_reports_approximation_and_error(self):
        request = {
            "contractVersion": "1.0.0",
            "operation": "divide",
            "operands": ["1", "3"],
            "domain": "real",
            "precision": {"mode": "decimal", "decimalPlaces": 8},
        }
        result = execute("calculation.evaluate", request)
        self.assertEqual(result["status"], "approximate")
        self.assertEqual(result["value"], "0.33333333")
        self.assertNotEqual(result["errorBound"], "0")

    def test_exact_root(self):
        request = {
            "contractVersion": "1.0.0",
            "operation": "root",
            "operands": ["27", "3"],
            "domain": "real",
            "precision": {"mode": "exact", "decimalPlaces": 0},
        }
        result = execute("calculation.evaluate", request)
        self.assertEqual(result["status"], "exact")
        self.assertEqual(result["value"], "3")

    def test_percentage_and_zero_division(self):
        percentage = {
            "contractVersion": "1.0.0",
            "operation": "percentage",
            "operands": ["15", "80"],
            "domain": "real",
            "precision": {"mode": "exact", "decimalPlaces": 0},
        }
        self.assertEqual(execute("calculation.evaluate", percentage)["value"], "12")
        divide = dict(percentage, operation="divide", operands=["1", "0"])
        self.assertEqual(execute("calculation.evaluate", divide)["status"], "ambiguous")

    def test_unit_conversion_is_dimension_checked(self):
        request = TOOLS["calculation.convertUnits"]["examples"]["validInput"]
        self.assertEqual(execute("calculation.convertUnits", request)["convertedAmount"], "1500")
        incompatible = dict(request, sourceUnit="kg", targetUnit="m")
        self.assertEqual(execute("calculation.convertUnits", incompatible)["status"], "unsupported")
        oversized = dict(request, amount="9" * 128, sourceUnit="mi", targetUnit="mm", decimalPlaces=0)
        limited = execute("calculation.convertUnits", oversized)
        self.assertEqual(limited["status"], "unsupported")
        self.assertEqual(limited["convertedAmount"], "")

    def test_symbolic_polynomial_derivative_and_integral(self):
        request = {
            "contractVersion": "1.0.0",
            "operation": "derivative",
            "expression": "x^2 + 3*x + 1",
            "variable": "x",
            "domain": "real",
            "substitutions": [],
            "precision": 0,
        }
        self.assertEqual(execute("calculation.symbolic", request)["value"], "2*x + 3")
        integral = dict(request, operation="integral")
        self.assertEqual(execute("calculation.symbolic", integral)["value"], "1/3*x^3 + 3/2*x^2 + x + C")

    def test_linear_solve_substitute_and_missing_limit_point(self):
        request = {
            "contractVersion": "1.0.0",
            "operation": "solve",
            "expression": "2*x - 4",
            "variable": "x",
            "domain": "real",
            "substitutions": [],
            "precision": 0,
        }
        self.assertEqual(execute("calculation.symbolic", request)["value"], "x = 2")
        substitute = dict(request, operation="substitute", substitutions=[{"name": "x", "value": "5"}])
        self.assertEqual(execute("calculation.symbolic", substitute)["value"], "6")
        limit = dict(request, operation="limit")
        self.assertEqual(execute("calculation.symbolic", limit)["status"], "insufficient_data")

    def test_unsafe_or_unsupported_symbolic_expression_fails_closed(self):
        request = {
            "contractVersion": "1.0.0",
            "operation": "simplify",
            "expression": "__import__('os').system('whoami')",
            "variable": "x",
            "domain": "real",
            "substitutions": [],
            "precision": 0,
        }
        self.assertEqual(execute("calculation.symbolic", request)["status"], "unsupported")

    def test_oversized_polynomial_coefficient_is_rejected(self):
        request = {
            "contractVersion": "1.0.0",
            "operation": "simplify",
            "expression": ("9" * 700) + "*x",
            "variable": "x",
            "domain": "real",
            "substitutions": [],
            "precision": 0,
        }
        result = execute("calculation.symbolic", request)
        self.assertEqual(result["status"], "unsupported")
        self.assertEqual(result["value"], "")

    def test_explicit_percentage_request_bypasses_model_and_uses_deterministic_math(self):
        fake = FakeModel({})
        result = execute_text_request("Qual é 15% de 80?", model=fake)
        self.assertEqual(fake.calls, 0)
        self.assertEqual(result["status"], "executed")
        self.assertEqual(result["result"]["value"], "12")

    def test_explicit_power_request_bypasses_model_and_uses_deterministic_math(self):
        fake = FakeModel({})
        result = execute_text_request("Calcule 2 elevado a 5.", model=fake)
        self.assertEqual(fake.calls, 0)
        self.assertEqual(result["status"], "executed")
        self.assertEqual(result["result"]["value"], "32")

    def test_less_explicit_natural_language_uses_local_model_for_parameters(self):
        fake = FakeModel(
            {
                "status": "ready",
                "tool": "calculation.evaluate",
                "input": {
                    "contractVersion": "1.0.0",
                    "operation": "power",
                    "operands": ["2", "5"],
                    "domain": "real",
                    "precision": {"mode": "exact", "decimalPlaces": 0},
                },
            }
        )
        result = execute_text_request("Calcule a quinta potência de dois.", model=fake)
        self.assertEqual(fake.calls, 1)
        self.assertEqual(result["status"], "executed")
        self.assertEqual(result["result"]["value"], "32")

    def test_invalid_model_proposal_is_rejected_before_execution(self):
        fake = FakeModel(
            {
                "status": "ready",
                "tool": "calculation.evaluate",
                "input": {
                    "contractVersion": "1.0.0",
                    "operation": "multiply",
                    "operands": ["2", "3"],
                    "domain": "math",
                    "precision": {"mode": "exact", "decimalPlaces": 0},
                },
            }
        )
        result = parse_text_request("Calcule dois vezes três.", model=fake)
        self.assertEqual(fake.calls, 1)
        self.assertEqual(result["code"], "unavailable")

    def test_missing_local_model_fails_closed(self):
        result = parse_text_request("Calcule uma expressão desconhecida.", model=LocalModel(model=None))
        self.assertEqual(result["code"], "unavailable")

    def test_inference_clarification_prevents_guessing(self):
        fake = FakeModel({"status": "needs_clarification", "questions": ["Qual unidade você quer converter?"]})
        result = execute_text_request("Converta 1.", model=fake)
        self.assertEqual(result["status"], "needs_clarification")


if __name__ == "__main__":
    unittest.main()
