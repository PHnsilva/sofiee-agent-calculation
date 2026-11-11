"""One-shot JSON CLI for the local calculation runtime."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_runtime import execute, execute_text_request
from agent_runtime.contracts import error_result


def main() -> int:
    raw = sys.stdin.buffer.read(80_001)
    if len(raw) > 80_000:
        print(json.dumps(error_result("limit_exceeded", "Request exceeds 80000 bytes.")))
        return 2
    try:
        request = json.loads(raw.decode("utf-8"))
        if not isinstance(request, dict):
            raise ValueError
        if set(request) == {"tool", "input"}:
            result = execute(request["tool"], request["input"])
        elif set(request) == {"text"}:
            result = execute_text_request(request["text"])
        else:
            raise ValueError
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError):
        print(json.dumps(error_result("invalid_request", "Expected JSON with either tool/input or text.")))
        return 2
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0 if "code" not in result else 2


if __name__ == "__main__":
    raise SystemExit(main())
