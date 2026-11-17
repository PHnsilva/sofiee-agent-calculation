from __future__ import annotations

import unittest

from agent_runtime.calculation import execute, execute_text_request, parse_text_request
from agent_runtime.local_model import LocalModel, ModelCallError
from agent_runtime.contracts import ContractViolation, TOOLS, validate_input


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
            "contractVersion": "1.3.0",
            "operation": "divide",
            "operands": ["1", "3"],
            "domain": "real",
            "precision": {"mode": "exact", "decimalPlaces": 8},
        }
        result = execute("calculation.evaluate", request)
        self.assertEqual(result["status"], "exact")
        self.assertEqual(result["value"], "1/3")

    def test_fraction_addition_is_exact(self):
        request = {
            "contractVersion": "1.3.0",
            "operation": "add",
            "operands": ["1/3", "1/6"],
            "domain": "real",
            "precision": {"mode": "exact", "decimalPlaces": 8},
        }
        result = execute("calculation.evaluate", request)
        self.assertEqual(result["status"], "exact")
        self.assertEqual(result["value"], "1/2")

    def test_decimal_division_reports_approximation_and_error(self):
        request = {
            "contractVersion": "1.3.0",
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
            "contractVersion": "1.3.0",
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
            "contractVersion": "1.3.0",
            "operation": "percentage",
            "operands": ["15", "80"],
            "domain": "real",
            "precision": {"mode": "exact", "decimalPlaces": 0},
        }
        self.assertEqual(execute("calculation.evaluate", percentage)["value"], "12")
        divide = dict(percentage, operation="divide", operands=["1", "0"])
        self.assertEqual(execute("calculation.evaluate", divide)["status"], "ambiguous")

    def test_percentage_change_has_explicit_baseline_and_zero_rule(self):
        change = {
            "contractVersion": "1.3.0",
            "operation": "percentage_change",
            "operands": ["100", "120"],
            "domain": "real",
            "precision": {"mode": "exact", "decimalPlaces": 8},
        }
        self.assertEqual(execute("calculation.evaluate", change)["value"], "20")
        decrease = dict(change, operands=["120", "90"])
        self.assertEqual(execute("calculation.evaluate", decrease)["value"], "-25")
        zero_base = dict(change, operands=["0", "120"])
        result = execute("calculation.evaluate", zero_base)
        self.assertEqual(result["status"], "ambiguous")
        self.assertEqual(result["value"], "")
        self.assertIn("old value is zero", result["method"])

    def test_decimal_comma_is_explicit_and_mixed_separators_are_rejected(self):
        request = {
            "contractVersion": "1.3.0",
            "operation": "add",
            "operands": ["1,5", "2.25"],
            "domain": "real",
            "precision": {"mode": "exact", "decimalPlaces": 8},
        }
        result = execute("calculation.evaluate", request)
        self.assertEqual(result["status"], "exact")
        self.assertEqual(result["value"], "15/4")
        mixed = dict(request, operands=["1,234.5", "1"])
        self.assertEqual(execute("calculation.evaluate", mixed)["code"], "invalid_request")

    def test_decimal_rounding_is_reported_as_approximate_half_even(self):
        request = {
            "contractVersion": "1.3.0",
            "operation": "divide",
            "operands": ["5", "2"],
            "domain": "real",
            "precision": {"mode": "decimal", "decimalPlaces": 0},
        }
        result = execute("calculation.evaluate", request)
        self.assertEqual(result["status"], "approximate")
        self.assertEqual(result["value"], "2")
        self.assertIn("half-even", result["method"])
        self.assertNotEqual(result["errorBound"], "0")

    def _statistics_request(self, operation="mean", values=None, **extra):
        request = {
            "contractVersion": "1.3.0",
            "operation": operation,
            "values": ["1", "2", "3"] if values is None else values,
            "precision": {"mode": "exact", "decimalPlaces": 8},
        }
        request.update(extra)
        return request

    def test_descriptive_statistics_mean_weighted_mean_median_and_variance(self):
        self.assertEqual(execute("calculation.statistics", self._statistics_request())["value"], "2")
        weighted = self._statistics_request("weighted_mean", ["1", "3"], weights=["1", "3"])
        self.assertEqual(execute("calculation.statistics", weighted)["value"], "5/2")
        median = self._statistics_request("median", ["1", "2", "3", "4"])
        self.assertEqual(execute("calculation.statistics", median)["value"], "5/2")
        population = self._statistics_request("variance_population")
        sample = self._statistics_request("variance_sample")
        self.assertEqual(execute("calculation.statistics", population)["value"], "2/3")
        self.assertEqual(execute("calculation.statistics", sample)["value"], "1")

    def test_statistics_mode_returns_all_ties_and_all_distinct_values(self):
        tied = self._statistics_request("mode", ["2", "1", "2", "1", "3"])
        self.assertEqual(execute("calculation.statistics", tied)["modes"], ["1", "2"])
        distinct = self._statistics_request("mode", ["3", "1", "2"])
        result = execute("calculation.statistics", distinct)
        self.assertEqual(result["modes"], ["1", "2", "3"])
        self.assertIn("all are modes", result["assumptions"][0])

    def test_statistics_empty_invalid_weights_and_sample_limits_fail_explicitly(self):
        empty = self._statistics_request(values=[])
        self.assertEqual(execute("calculation.statistics", empty)["status"], "insufficient_data")
        empty_mode = self._statistics_request("mode", [])
        self.assertEqual(execute("calculation.statistics", empty_mode)["status"], "insufficient_data")
        empty_variance = self._statistics_request("variance_population", [], unit="kg")
        empty_result = execute("calculation.statistics", empty_variance)
        self.assertEqual(empty_result["status"], "insufficient_data")
        self.assertEqual(empty_result["unit"], "(kg)²")
        single_sample = self._statistics_request("variance_sample", ["7"])
        self.assertEqual(execute("calculation.statistics", single_sample)["status"], "insufficient_data")
        single_population = self._statistics_request("variance_population", ["7"])
        self.assertEqual(execute("calculation.statistics", single_population)["value"], "0")
        missing_weights = self._statistics_request("weighted_mean", ["1", "2"])
        self.assertEqual(execute("calculation.statistics", missing_weights)["status"], "insufficient_data")
        mismatched_weights = self._statistics_request("weighted_mean", ["1", "2"], weights=["1"])
        self.assertEqual(execute("calculation.statistics", mismatched_weights)["code"], "invalid_request")
        zero_weights = self._statistics_request("weighted_mean", ["1", "2"], weights=["0", "0"])
        self.assertEqual(execute("calculation.statistics", zero_weights)["code"], "invalid_request")
        negative_weight = self._statistics_request("weighted_mean", ["1", "2"], weights=["-1", "2"])
        self.assertEqual(execute("calculation.statistics", negative_weight)["code"], "invalid_request")
        invalid_value = self._statistics_request(values=["NaN"])
        self.assertEqual(execute("calculation.statistics", invalid_value)["code"], "invalid_request")
        oversized = self._statistics_request(values=["1"] * 1001)
        self.assertEqual(execute("calculation.statistics", oversized)["code"], "invalid_request")

    def test_statistics_preserve_units_and_report_decimal_error(self):
        mean = self._statistics_request(values=["1", "2"], unit="kg")
        approximate = dict(mean, precision={"mode": "decimal", "decimalPlaces": 0})
        result = execute("calculation.statistics", approximate)
        self.assertEqual(result["status"], "approximate")
        self.assertEqual(result["value"], "2")
        self.assertEqual(result["unit"], "kg")
        self.assertEqual(result["errorBound"], "≤0.5")
        variance = self._statistics_request("variance_population", ["1", "3"], unit="kg")
        result = execute("calculation.statistics", variance)
        self.assertEqual(result["unit"], "(kg)²")
        self.assertIn("divided by n.", result["method"])

    def test_combinatorics_obeys_order_repetition_and_multiset_counts(self):
        version = "1.3.0"
        permutation = execute(
            "calculation.combinatorics",
            {"contractVersion": version, "operation": "permutation", "itemCount": 5},
        )
        self.assertEqual(permutation["value"], "120")
        multiset = execute(
            "calculation.combinatorics",
            {"contractVersion": version, "operation": "permutation", "itemCount": 5, "multiplicities": [2, 2, 1]},
        )
        self.assertEqual(multiset["value"], "30")

        arrangement = {"contractVersion": version, "operation": "arrangement", "itemCount": 5, "selectionCount": 3}
        self.assertEqual(execute("calculation.combinatorics", dict(arrangement, allowRepetition=False))["value"], "60")
        self.assertEqual(execute("calculation.combinatorics", dict(arrangement, allowRepetition=True))["value"], "125")

        combination = {"contractVersion": version, "operation": "combination", "itemCount": 5, "selectionCount": 3}
        self.assertEqual(execute("calculation.combinatorics", dict(combination, allowRepetition=False))["value"], "10")
        self.assertEqual(execute("calculation.combinatorics", dict(combination, allowRepetition=True))["value"], "35")

    def test_combinatorics_handles_empty_impossible_and_bounded_results(self):
        version = "1.3.0"
        empty_permutation = execute(
            "calculation.combinatorics",
            {"contractVersion": version, "operation": "permutation", "itemCount": 0},
        )
        self.assertEqual(empty_permutation["value"], "1")
        impossible = execute(
            "calculation.combinatorics",
            {"contractVersion": version, "operation": "arrangement", "itemCount": 3, "selectionCount": 4, "allowRepetition": False},
        )
        self.assertEqual(impossible["value"], "0")
        empty_selection = execute(
            "calculation.combinatorics",
            {"contractVersion": version, "operation": "combination", "itemCount": 0, "selectionCount": 0, "allowRepetition": True},
        )
        self.assertEqual(empty_selection["value"], "1")
        oversized = execute(
            "calculation.combinatorics",
            {"contractVersion": version, "operation": "arrangement", "itemCount": 1000, "selectionCount": 1000, "allowRepetition": True},
        )
        self.assertEqual(oversized["status"], "unsupported")
        self.assertEqual(oversized["value"], "")

    def test_combinatorics_rejects_ambiguous_or_inconsistent_parameters(self):
        version = "1.3.0"
        missing_repetition = execute(
            "calculation.combinatorics",
            {"contractVersion": version, "operation": "combination", "itemCount": 5, "selectionCount": 2},
        )
        self.assertEqual(missing_repetition["code"], "invalid_request")
        bad_multiplicities = execute(
            "calculation.combinatorics",
            {"contractVersion": version, "operation": "permutation", "itemCount": 5, "multiplicities": [2, 2]},
        )
        self.assertEqual(bad_multiplicities["code"], "invalid_request")

    def test_contract_requires_operation_specific_inputs(self):
        with self.assertRaises(ContractViolation):
            validate_input(
                "calculation.combinatorics",
                {"contractVersion": "1.3.0", "operation": "arrangement", "itemCount": 5},
            )
        with self.assertRaises(ContractViolation):
            validate_input(
                "calculation.probability",
                {
                    "contractVersion": "1.3.0",
                    "operation": "conditional",
                    "eventCount": 3,
                    "sampleSpaceSize": 6,
                    "sampleSpaceModel": "equiprobable",
                },
            )

    def test_probability_requires_finite_sample_space_and_conditional_assumption(self):
        version = "1.3.0"
        simple = execute(
            "calculation.probability",
            {"contractVersion": version, "operation": "simple", "eventCount": 2, "sampleSpaceSize": 6, "sampleSpaceModel": "equiprobable"},
        )
        self.assertEqual(simple["value"], "1/3")
        self.assertIn("6 outcomes", simple["assumptions"][0])

        dependent = execute(
            "calculation.probability",
            {
                "contractVersion": version,
                "operation": "conditional",
                "eventCount": 4,
                "sampleSpaceSize": 10,
                "sampleSpaceModel": "equiprobable",
                "conditionEventCount": 5,
                "jointEventCount": 2,
                "dependencyAssumption": "dependent",
            },
        )
        self.assertEqual(dependent["value"], "2/5")

        independent = execute(
            "calculation.probability",
            {
                "contractVersion": version,
                "operation": "conditional",
                "eventCount": 3,
                "sampleSpaceSize": 6,
                "sampleSpaceModel": "equiprobable",
                "conditionEventCount": 2,
                "jointEventCount": 1,
                "dependencyAssumption": "independent",
            },
        )
        self.assertEqual(independent["value"], "1/2")

    def test_probability_rejects_missing_or_inconsistent_counts(self):
        version = "1.3.0"
        impossible_event = execute(
            "calculation.probability",
            {"contractVersion": version, "operation": "simple", "eventCount": 7, "sampleSpaceSize": 6, "sampleSpaceModel": "equiprobable"},
        )
        self.assertEqual(impossible_event["code"], "invalid_request")
        conditional = {
            "contractVersion": version,
            "operation": "conditional",
            "eventCount": 3,
            "sampleSpaceSize": 6,
            "sampleSpaceModel": "equiprobable",
            "conditionEventCount": 2,
            "jointEventCount": 1,
        }
        missing_assumption = execute("calculation.probability", conditional)
        self.assertEqual(missing_assumption["code"], "invalid_request")
        inconsistent_independence = execute(
            "calculation.probability", dict(conditional, dependencyAssumption="independent", jointEventCount=2)
        )
        self.assertEqual(inconsistent_independence["code"], "invalid_request")
        impossible_joint = execute(
            "calculation.probability", dict(conditional, dependencyAssumption="dependent", jointEventCount=4)
        )
        self.assertEqual(impossible_joint["code"], "invalid_request")
        impossible_lower_bound = execute(
            "calculation.probability",
            dict(
                conditional,
                eventCount=4,
                sampleSpaceSize=6,
                conditionEventCount=4,
                jointEventCount=1,
                dependencyAssumption="dependent",
            ),
        )
        self.assertEqual(impossible_lower_bound["code"], "invalid_request")
        empty_condition = execute(
            "calculation.probability",
            dict(conditional, conditionEventCount=0, jointEventCount=0, dependencyAssumption="dependent"),
        )
        self.assertEqual(empty_condition["status"], "ambiguous")
        self.assertEqual(empty_condition["value"], "")

    def test_unit_conversion_is_dimension_checked(self):
        request = TOOLS["calculation.convertUnits"]["examples"]["validInput"]
        self.assertEqual(execute("calculation.convertUnits", request)["convertedAmount"], "1500")
        decimal_comma = dict(request, amount="1,5")
        self.assertEqual(execute("calculation.convertUnits", decimal_comma)["convertedAmount"], "1500")
        incompatible = dict(request, sourceUnit="kg", targetUnit="m")
        self.assertEqual(execute("calculation.convertUnits", incompatible)["status"], "unsupported")
        oversized = dict(request, amount="9" * 128, sourceUnit="mi", targetUnit="mm", decimalPlaces=0)
        limited = execute("calculation.convertUnits", oversized)
        self.assertEqual(limited["status"], "unsupported")
        self.assertEqual(limited["convertedAmount"], "")

    def test_symbolic_polynomial_derivative_and_integral(self):
        request = {
            "contractVersion": "1.3.0",
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
            "contractVersion": "1.3.0",
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
            "contractVersion": "1.3.0",
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
            "contractVersion": "1.3.0",
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

    def test_explicit_percentage_change_in_both_locales_bypasses_model(self):
        fake = FakeModel({})
        for text in ("Variação percentual de 100 para 120", "Percentage change from 100 to 120"):
            with self.subTest(text=text):
                result = execute_text_request(text, model=fake)
                self.assertEqual(result["status"], "executed")
                self.assertEqual(result["input"]["operation"], "percentage_change")
                self.assertEqual(result["result"]["value"], "20")
        self.assertEqual(fake.calls, 0)

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
                    "contractVersion": "1.3.0",
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

    def test_local_parser_can_select_the_versioned_statistics_tool(self):
        fake = FakeModel(
            {
                "status": "ready",
                "tool": "calculation.statistics",
                "input": {
                    "contractVersion": "1.3.0",
                    "operation": "weighted_mean",
                    "values": ["10", "20"],
                    "weights": ["1", "3"],
                    "unit": "kg",
                    "precision": {"mode": "exact", "decimalPlaces": 8},
                },
            }
        )
        result = execute_text_request("Calcule a média ponderada de 10 kg e 20 kg.", model=fake)
        self.assertEqual(fake.calls, 1)
        self.assertEqual(result["status"], "executed")
        self.assertEqual(result["input"]["operation"], "weighted_mean")
        self.assertEqual(result["result"]["value"], "35/2")

    def test_invalid_model_proposal_is_rejected_before_execution(self):
        fake = FakeModel(
            {
                "status": "ready",
                "tool": "calculation.evaluate",
                "input": {
                    "contractVersion": "1.3.0",
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
