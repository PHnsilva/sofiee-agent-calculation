"""Verify MCP size, time, output, logging, and concurrency boundaries."""
from __future__ import annotations

import asyncio
import logging
import time
import unittest

from agent_runtime.mcp_limits import BoundedToolExecutor, McpLimits


class McpLimitTests(unittest.TestCase):
    def test_configuration_is_bounded_and_invalid_values_are_not_echoed(self):
        configured = McpLimits.from_environment(
            {
                "SOFIEE_MCP_MAX_INPUT_BYTES": "4096",
                "SOFIEE_MCP_MAX_OUTPUT_BYTES": "8192",
                "SOFIEE_MCP_TIMEOUT_SECONDS": "2.5",
                "SOFIEE_MCP_MAX_CONCURRENCY": "2",
            }
        )
        self.assertEqual(configured.max_input_bytes, 4096)
        self.assertEqual(configured.max_output_bytes, 8192)
        self.assertEqual(configured.timeout_seconds, 2.5)
        self.assertEqual(configured.max_concurrent_calls, 2)

        with self.assertRaises(ValueError) as failure:
            McpLimits.from_environment(
                {"SOFIEE_MCP_MAX_INPUT_BYTES": "PRIVATE_CONFIG_SENTINEL"}
            )
        self.assertIn("SOFIEE_MCP_MAX_INPUT_BYTES", str(failure.exception))
        self.assertNotIn("PRIVATE_CONFIG_SENTINEL", str(failure.exception))

    def test_oversized_input_is_rejected_before_dispatch(self):
        calls = []
        limits = McpLimits(
            max_input_bytes=128,
            max_output_bytes=2048,
            timeout_seconds=1,
            max_concurrent_calls=1,
        )
        executor = BoundedToolExecutor(
            lambda name, payload: calls.append((name, payload)) or {"ok": True}, limits
        )

        result = asyncio.run(executor.call("safe.tool", {"text": "x" * 256}))

        self.assertEqual(result["code"], "limit_exceeded")
        self.assertEqual(calls, [])

    def test_timeout_keeps_worker_slot_until_the_bounded_worker_finishes(self):
        calls = 0

        def slow_handler(_name, _payload):
            nonlocal calls
            calls += 1
            if calls == 1:
                time.sleep(0.08)
            return {"contractVersion": "1.0.0", "ok": True}

        limits = McpLimits(
            max_input_bytes=2048,
            max_output_bytes=2048,
            timeout_seconds=0.01,
            max_concurrent_calls=1,
        )
        executor = BoundedToolExecutor(slow_handler, limits)

        async def scenario():
            timed_out = await executor.call("slow.tool", {})
            saturated = await executor.call("slow.tool", {})
            await asyncio.sleep(0.12)
            recovered = await executor.call("slow.tool", {})
            return timed_out, saturated, recovered

        timed_out, saturated, recovered = asyncio.run(scenario())

        self.assertEqual(timed_out["code"], "timeout")
        self.assertEqual(saturated["code"], "busy")
        self.assertTrue(recovered["ok"])

    def test_oversized_output_is_replaced_without_echoing_private_data(self):
        secret = "PRIVATE_DOCUMENT_SENTINEL"
        limits = McpLimits(
            max_input_bytes=2048,
            max_output_bytes=512,
            timeout_seconds=1,
            max_concurrent_calls=1,
        )
        executor = BoundedToolExecutor(
            lambda _name, _payload: {"document": secret + ("x" * 1024)}, limits
        )

        result = asyncio.run(executor.call("safe.tool", {}))

        self.assertEqual(result["code"], "limit_exceeded")
        self.assertNotIn(secret, str(result))

    def test_unexpected_error_text_is_not_returned_or_logged(self):
        secret = "CREDENTIAL_SENTINEL"
        records = []

        class Capture(logging.Handler):
            def emit(self, record):
                records.append(record.getMessage())

        capture = Capture()
        logger = logging.getLogger()
        logger.addHandler(capture)
        try:
            limits = McpLimits(
                max_input_bytes=2048,
                max_output_bytes=2048,
                timeout_seconds=1,
                max_concurrent_calls=1,
            )
            executor = BoundedToolExecutor(
                lambda _name, _payload: (_ for _ in ()).throw(ValueError(secret)),
                limits,
            )
            result = asyncio.run(executor.call("safe.tool", {}))
        finally:
            logger.removeHandler(capture)

        self.assertEqual(result["code"], "internal_error")
        self.assertNotIn(secret, str(result))
        self.assertFalse(any(secret in message for message in records))


if __name__ == "__main__":
    unittest.main()
