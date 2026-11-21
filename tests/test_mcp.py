"""Exercise discovery and a real MCP call against the local stdio process."""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path

from mcp import Client
from mcp.client.stdio import StdioServerParameters
from agent_runtime.contracts import CONTRACT

ROOT = Path(__file__).resolve().parents[1]
SERVER = StdioServerParameters(
    command=sys.executable,
    args=["-m", "agent_runtime.mcp_server"],
    cwd=ROOT,
)
EXPECTED_NAMES = {'calculation.evaluate', 'calculation.convertUnits', 'calculation.addQuantities', 'calculation.symbolic', 'calculation.solveEquation', 'calculation.solveSystem'}
TEST_TOOL = "calculation.evaluate"
PAYLOAD = {'contractVersion': CONTRACT['contractVersion'],
 'operation': 'percentage_change',
 'operands': ['100', '120'],
 'domain': 'real',
 'precision': {'mode': 'decimal', 'decimalPlaces': 8}}


async def discover_and_call():
    async with Client(SERVER) as client:
        listing = await client.list_tools()
        names = {item.name for item in listing.tools}
        tools = {item.name: item for item in listing.tools}
        result = await client.call_tool(TEST_TOOL, PAYLOAD)
        quantity_result = await client.call_tool(
            "calculation.addQuantities",
            {
                "contractVersion": CONTRACT["contractVersion"],
                "quantities": [
                    {"amount": "1", "unit": "km"},
                    {"amount": "500", "unit": "m"},
                ],
            },
        )
        symbolic_result = await client.call_tool(
            "calculation.symbolic",
            {
                "contractVersion": CONTRACT["contractVersion"],
                "operation": "substitute",
                "expression": "x*y + 2*x",
                "variable": "x",
                "domain": "real",
                "substitutions": [{"name": "x", "value": "3"}, {"name": "y", "value": "4"}],
                "precision": 0,
            },
        )
        system_result = await client.call_tool(
            "calculation.solveSystem",
            {
                "contractVersion": CONTRACT["contractVersion"],
                "equations": ["x + y = 5", "x - y = 1"],
                "variables": ["x", "y"],
                "domain": "real",
            },
        )
        equation_result = await client.call_tool(
            "calculation.solveEquation",
            {
                "contractVersion": CONTRACT["contractVersion"],
                "equation": "x^2 = 4",
                "variable": "x",
                "domain": "real",
            },
        )
        return names, tools, result, quantity_result, symbolic_result, equation_result, system_result


class McpTransportTests(unittest.TestCase):
    def test_real_client_discovers_contract_tools_and_calls_domain_operation(self):
        names, tools, result, quantity_result, symbolic_result, equation_result, system_result = asyncio.run(discover_and_call())
        self.assertSetEqual(names, EXPECTED_NAMES)
        self.assertEqual(
            tools[TEST_TOOL].input_schema["$id"],
            'https://sofiee-agent-calculation.local/contracts/v1/evaluate.input.schema.json',
        )
        self.assertIsInstance(result.structured_content, dict)
        self.assertEqual(result.structured_content.get("contractVersion"), CONTRACT['contractVersion'])
        self.assertFalse(result.is_error)
        self.assertEqual(result.structured_content.get("operation"), "percentage_change")
        self.assertEqual(result.structured_content.get("value"), "20")
        self.assertFalse(quantity_result.is_error)
        self.assertEqual(quantity_result.structured_content.get("sum"), "3/2")
        self.assertEqual(quantity_result.structured_content.get("unit"), "km")
        self.assertFalse(symbolic_result.is_error)
        self.assertEqual(symbolic_result.structured_content.get("status"), "exact")
        self.assertEqual(symbolic_result.structured_content.get("value"), "18")
        self.assertFalse(equation_result.is_error)
        self.assertEqual(equation_result.structured_content.get("status"), "exact")
        self.assertEqual(equation_result.structured_content.get("value"), "x = -2; x = 2")
        self.assertEqual(equation_result.structured_content.get("solutionVerification"), "verified")
        self.assertFalse(system_result.is_error)
        self.assertEqual(system_result.structured_content.get("status"), "exact")
        self.assertEqual(system_result.structured_content.get("value"), "x = 3; y = 2")
        self.assertEqual(system_result.structured_content.get("solutionVerification"), "verified")


if __name__ == "__main__":
    unittest.main()
