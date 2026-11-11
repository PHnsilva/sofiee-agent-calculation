"""Bound the MCP boundary without logging or echoing caller content."""
from __future__ import annotations

import asyncio
import json
import math
import os
import threading
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from agent_runtime.contracts import CONTRACT

Handler = Callable[[str, dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class McpLimits:
    max_input_bytes: int = 80_000
    max_output_bytes: int = 65_536
    timeout_seconds: float = 30.0
    max_concurrent_calls: int = 4

    @classmethod
    def from_environment(cls, environ: Mapping[str, str] | None = None) -> "McpLimits":
        source = os.environ if environ is None else environ
        return cls(
            max_input_bytes=_bounded_int(
                source, "SOFIEE_MCP_MAX_INPUT_BYTES", 80_000, 1_024, 1_000_000
            ),
            max_output_bytes=_bounded_int(
                source, "SOFIEE_MCP_MAX_OUTPUT_BYTES", 65_536, 1_024, 1_000_000
            ),
            timeout_seconds=_bounded_float(
                source, "SOFIEE_MCP_TIMEOUT_SECONDS", 30.0, 0.05, 120.0
            ),
            max_concurrent_calls=_bounded_int(
                source, "SOFIEE_MCP_MAX_CONCURRENCY", 4, 1, 16
            ),
        )


def _bounded_int(
    environ: Mapping[str, str], name: str, default: int, minimum: int, maximum: int
) -> int:
    raw = environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be an integer") from None
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} is outside the allowed range")
    return value


def _bounded_float(
    environ: Mapping[str, str], name: str, default: float, minimum: float, maximum: float
) -> float:
    raw = environ.get(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be numeric") from None
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f"{name} is outside the allowed range")
    return value


class BoundedToolExecutor:
    def __init__(self, handler: Handler, limits: McpLimits | None = None) -> None:
        self._handler = handler
        self.limits = limits or McpLimits.from_environment()
        self._slots = threading.BoundedSemaphore(self.limits.max_concurrent_calls)

    @staticmethod
    def _error(code: str, message: str, *, retryable: bool = False) -> dict[str, Any]:
        return {
            "contractVersion": CONTRACT["contractVersion"],
            "code": code,
            "message": message,
            "retryable": retryable,
        }

    async def call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            input_bytes = json.dumps(
                arguments, ensure_ascii=False, allow_nan=False, separators=(",", ":")
            ).encode("utf-8")
        except (TypeError, ValueError):
            return self._error("invalid_request", "Tool arguments must be JSON data.")

        if len(input_bytes) > self.limits.max_input_bytes:
            return self._error("limit_exceeded", "Tool input exceeds the configured limit.")
        if not self._slots.acquire(blocking=False):
            return self._error(
                "busy", "Tool concurrency limit reached.", retryable=True
            )

        def invoke() -> dict[str, Any]:
            try:
                result = self._handler(tool_name, arguments)
                if not isinstance(result, dict):
                    return self._error("internal_error", "Tool returned an invalid result.")
                return result
            except Exception:
                return self._error("internal_error", "Tool execution failed.")
            finally:
                self._slots.release()

        worker = asyncio.create_task(asyncio.to_thread(invoke))
        try:
            result = await asyncio.wait_for(
                asyncio.shield(worker), timeout=self.limits.timeout_seconds
            )
        except asyncio.TimeoutError:
            return self._error(
                "timeout", "Tool execution exceeded its time limit.", retryable=True
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            return self._error("internal_error", "Tool execution failed.")

        try:
            output_bytes = json.dumps(
                result, ensure_ascii=False, allow_nan=False, separators=(",", ":")
            ).encode("utf-8")
        except (TypeError, ValueError):
            return self._error("internal_error", "Tool result is not valid JSON data.")

        # Reserve room for the MCP envelope and short, non-sensitive text content.
        if len(output_bytes) + 512 > self.limits.max_output_bytes:
            return self._error("limit_exceeded", "Tool output exceeds the configured limit.")
        return result
