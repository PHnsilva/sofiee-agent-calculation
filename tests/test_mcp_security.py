"""Verify the real MCP server rejects authority-shaped untrusted input."""
from __future__ import annotations

import asyncio
import json
import unittest

from mcp import Client

from test_mcp import EXPECTED_NAMES, PAYLOAD, SERVER, TEST_TOOL


async def call_untrusted_inputs():
    async with Client(SERVER) as client:
        listing = await client.list_tools()
        names = {tool.name for tool in listing.tools}
        tool = next(item for item in listing.tools if item.name == TEST_TOOL)
        altered = dict(PAYLOAD)
        altered["permissions"] = {
            "admin": True,
            "note": "PRIVATE_DOCUMENT_SENTINEL",
        }
        authority_claim = await client.call_tool(TEST_TOOL, altered)
        oversized = await client.call_tool(TEST_TOOL, {"text": "x" * 81_000})
        unlisted = await client.call_tool(
            "admin.grantPermission", {"permissions": {"admin": True}}
        )
        return names, tool, authority_claim, oversized, unlisted


class McpSecurityIntegrationTests(unittest.TestCase):
    def test_hostile_data_does_not_add_permission_tools_or_bypass_contract(self):
        names, tool, authority_claim, oversized, unlisted = asyncio.run(
            call_untrusted_inputs()
        )

        self.assertSetEqual(names, EXPECTED_NAMES)
        self.assertNotIn("admin.grantPermission", names)
        self.assertNotIn("permissions", tool.input_schema["properties"])
        self.assertTrue(authority_claim.is_error)
        self.assertEqual(authority_claim.structured_content.get("code"), "invalid_request")
        self.assertNotIn(
            "PRIVATE_DOCUMENT_SENTINEL", json.dumps(authority_claim.structured_content)
        )
        self.assertTrue(oversized.is_error)
        self.assertEqual(oversized.structured_content.get("code"), "limit_exceeded")
        self.assertTrue(unlisted.is_error)
        self.assertEqual(unlisted.structured_content.get("code"), "invalid_request")


if __name__ == "__main__":
    unittest.main()
