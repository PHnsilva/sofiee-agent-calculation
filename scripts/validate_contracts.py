"""Check public contract fixtures against the JSON Schema subset used here.

This is a zero-dependency fixture checker, not a production JSON Schema engine.
The runtime must validate the same schemas with its selected official SDK.
"""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "v1" / "contracts.json"


def matches(value, schema):
    kind = schema.get("type")
    if kind == "object":
        if not isinstance(value, dict):
            return False
        if any(key not in value for key in schema.get("required", [])):
            return False
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False and set(value) - set(properties):
            return False
        return all(matches(child, properties[key]) for key, child in value.items() if key in properties)
    if kind == "array":
        if not isinstance(value, list):
            return False
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", float("inf")):
            return False
        return all(matches(item, schema["items"]) for item in value)
    if kind == "string":
        if not isinstance(value, str):
            return False
        if len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", float("inf")):
            return False
        if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
            return False
    elif kind == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            return False
    elif kind == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
    elif kind == "boolean":
        if not isinstance(value, bool):
            return False
    elif kind == "null":
        if value is not None:
            return False
    elif kind is not None:
        raise ValueError(f"Unsupported schema type: {kind}")
    if "const" in schema and value != schema["const"]:
        return False
    if "enum" in schema and value not in schema["enum"]:
        return False
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value < schema.get("minimum", float("-inf")) or value > schema.get("maximum", float("inf")):
            return False
    return True


def main():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["contractVersion"] == "1.0.0"
    assert contract["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    error_schema = contract["errorSchema"]
    assert error_schema["$schema"] == contract["$schema"]
    assert error_schema["additionalProperties"] is False
    assert "contractVersion" in error_schema["required"]
    assert error_schema["properties"]["contractVersion"]["const"] == contract["contractVersion"]
    tools = contract["tools"]
    assert tools and len({tool["name"] for tool in tools}) == len(tools)
    checked = 0
    for tool in tools:
        assert tool["sideEffects"] is False, tool["name"]
        for schema_name in ("inputSchema", "resultSchema"):
            schema = tool[schema_name]
            assert schema["$schema"] == contract["$schema"]
            assert schema["additionalProperties"] is False
            assert "contractVersion" in schema["required"]
            assert schema["properties"]["contractVersion"]["const"] == contract["contractVersion"]
        assert tool["errorCodes"]
        assert set(tool["examples"]) == {"validInput", "invalidInput", "validResult", "error"}
        assert tool["examples"]["error"]["code"] in tool["errorCodes"]
        for key, schema in (
            ("validInput", tool["inputSchema"]),
            ("invalidInput", tool["inputSchema"]),
            ("validResult", tool["resultSchema"]),
            ("error", contract["errorSchema"]),
        ):
            result = matches(tool["examples"][key], schema)
            assert result == (key != "invalidInput"), f"{tool['name']}:{key} fixture mismatch"
            checked += 1
    print(f"contract-fixtures: {checked} checked; tools: {len(tools)}; version: {contract['contractVersion']}")


if __name__ == "__main__":
    main()
