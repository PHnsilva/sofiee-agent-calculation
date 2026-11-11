"""Contract helpers for the versioned Communication API."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class ContractViolation(ValueError):
    pass


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "contracts" / "v1" / "contracts.json").read_text(encoding="utf-8"))
ERROR_SCHEMA = CONTRACT["errorSchema"]
TOOLS = {item["name"]: item for item in CONTRACT["tools"]}


def validate(schema: dict[str, Any], value: Any, path: str = "$") -> None:
    """Validate the JSON Schema keywords currently used by this versioned contract."""
    kind = schema.get("type")
    if kind == "object":
        if not isinstance(value, dict):
            raise ContractViolation(f"{path} must be an object")
        missing = set(schema.get("required", ())) - set(value)
        if missing:
            raise ContractViolation(f"{path} is missing required properties")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False and set(value) - set(properties):
            raise ContractViolation(f"{path} has unsupported properties")
        for key, child in value.items():
            if key in properties:
                validate(properties[key], child, f"{path}.{key}")
    elif kind == "array":
        if not isinstance(value, list):
            raise ContractViolation(f"{path} must be an array")
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", float("inf")):
            raise ContractViolation(f"{path} has an invalid number of items")
        if "items" in schema:
            for index, item in enumerate(value):
                validate(schema["items"], item, f"{path}[{index}]")
    elif kind == "string":
        if not isinstance(value, str):
            raise ContractViolation(f"{path} must be a string")
        if len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", float("inf")):
            raise ContractViolation(f"{path} has an invalid length")
        pattern = schema.get("pattern")
        if pattern is not None and re.fullmatch(pattern, value) is None:
            raise ContractViolation(f"{path} has an invalid format")
    elif kind == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ContractViolation(f"{path} must be an integer")
    elif kind == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ContractViolation(f"{path} must be numeric")
    elif kind == "boolean":
        if not isinstance(value, bool):
            raise ContractViolation(f"{path} must be a boolean")
    elif kind == "null":
        if value is not None:
            raise ContractViolation(f"{path} must be null")
    elif kind is not None:
        raise ContractViolation(f"Unsupported schema type: {kind}")

    if "const" in schema and value != schema["const"]:
        raise ContractViolation(f"{path} does not match the contract version")
    if "enum" in schema and value not in schema["enum"]:
        raise ContractViolation(f"{path} is not an allowed value")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value < schema.get("minimum", float("-inf")) or value > schema.get("maximum", float("inf")):
            raise ContractViolation(f"{path} is outside the allowed range")


def validate_input(tool_name: str, value: Any) -> None:
    tool = TOOLS.get(tool_name)
    if tool is None:
        raise ContractViolation("Unknown tool")
    validate(tool["inputSchema"], value)


def validate_result(tool_name: str, value: Any) -> None:
    tool = TOOLS.get(tool_name)
    if tool is None:
        raise ContractViolation("Unknown tool")
    validate(tool["resultSchema"], value)


def error_result(code: str, message: str, retryable: bool = False) -> dict[str, Any]:
    value = {
        "contractVersion": CONTRACT["contractVersion"],
        "code": code,
        "message": message[:500],
        "retryable": retryable,
    }
    validate(ERROR_SCHEMA, value)
    return value
