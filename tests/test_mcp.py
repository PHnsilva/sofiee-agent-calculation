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
EXPECTED_NAMES = {
    'calculation.evaluate',
    'calculation.convertUnits',
    'calculation.symbolic',
    'calculation.statistics',
}
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
        statistics = await client.call_tool(
            'calculation.statistics',
            {
                'contractVersion': CONTRACT['contractVersion'],
                'operation': 'weighted_mean',
                'values': ['10', '20'],
                'weights': ['1', '3'],
                'unit': 'kg',
                'precision': {'mode': 'exact', 'decimalPlaces': 8},
            },
        )
        return names, tools, result, statistics


class McpTransportTests(unittest.TestCase):
    def test_real_client_discovers_contract_tools_and_calls_domain_operation(self):
        names, tools, result, statistics = asyncio.run(discover_and_call())
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
        self.assertFalse(statistics.is_error)
        self.assertEqual(statistics.structured_content.get("operation"), "weighted_mean")
        self.assertEqual(statistics.structured_content.get("value"), "35/2")


if __name__ == "__main__":
    unittest.main()
