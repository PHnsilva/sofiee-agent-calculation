"""Request-scoped task coordination for deterministic calculation tools."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable

from .calculation import execute
from .contracts import (
    CONTRACT,
    ERROR_SCHEMA,
    ContractViolation,
    error_result,
    validate,
    validate_input,
    validate_result,
)


ROOT = Path(__file__).resolve().parents[1]
TASK_SCHEMA = json.loads((ROOT / "contracts" / "v1" / "task.schema.json").read_text(encoding="utf-8"))
TASK_RESULT_SCHEMA = json.loads(
    (ROOT / "contracts" / "v1" / "task-result.schema.json").read_text(encoding="utf-8")
)
TASK_TOOLS = {
    "calculation.evaluate",
    "calculation.symbolic",
    "calculation.solveEquation",
    "calculation.solveSystem",
    "calculation.convertUnits",
    "calculation.addQuantities",
}
_DEFAULT_LIMITS = {
    "maxSteps": 8,
    "timeoutMs": 60_000,
    "maxAttempts": 1,
    "maxConcurrency": 1,
    "maxDelegationDepth": 0,
    "maxOutputBytes": 256_000,
}
_NUMERIC = re.compile(r"^-?(?:[0-9]+(?:[.,][0-9]+)?|[0-9]+/[1-9][0-9]*)$")
_Runner = Callable[[str, dict[str, Any], threading.Event | None], dict[str, Any]]


class _DependencyBlocked(ValueError):
    def __init__(self, source_id: str, code: str, message: str):
        super().__init__(message)
        self.source_id = source_id
        self.code = code


def _digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _stage_digest(stage: dict[str, Any]) -> str:
    return _digest(
        {
            "id": stage["id"],
            "tool": stage["tool"],
            "input": stage["input"],
            "dependsOn": stage.get("dependsOn", []),
        }
    )


def _definition(task: dict[str, Any], limits: dict[str, int]) -> dict[str, Any]:
    return {
        "contractVersion": task["contractVersion"],
        "objective": task["objective"],
        "stages": [
            {"id": stage["id"], "tool": stage["tool"], "input": stage["input"], "dependsOn": stage.get("dependsOn", [])}
            for stage in task["stages"]
        ],
        "limits": limits,
    }


def _references(value: Any, path: tuple[str | int, ...] = ()) -> list[tuple[str, str, tuple[str | int, ...]]]:
    if isinstance(value, list):
        return [reference for index, item in enumerate(value) for reference in _references(item, path + (index,))]
    if isinstance(value, dict):
        if "$resultFrom" in value:
            if set(value) != {"$resultFrom", "field"} or not all(isinstance(value[key], str) for key in value):
                raise ContractViolation("A result reference must contain only a stage ID and field name")
            return [(value["$resultFrom"], value["field"], path)]
        return [reference for key, item in value.items() for reference in _references(item, path + (key,))]
    return []


def _resolve(value: Any, results: dict[str, dict[str, Any]]) -> Any:
    if isinstance(value, list):
        return [_resolve(item, results) for item in value]
    if isinstance(value, dict):
        if "$resultFrom" in value:
            source_id, field, _ = _references(value)[0]
            result = results.get(source_id)
            if result is None or field not in result:
                raise _DependencyBlocked(source_id, "invalid_request", "Referenced calculation output is unavailable")
            return copy.deepcopy(result[field])
        return {key: _resolve(item, results) for key, item in value.items()}
    return value


def _graph(stages: list[dict[str, Any]], limits: dict[str, int]) -> None:
    if len(stages) > limits["maxSteps"]:
        raise ContractViolation("Task exceeds maxSteps")
    prior: set[str] = set()
    for stage in stages:
        if stage["id"] in prior:
            raise ContractViolation("Stage IDs must be unique")
        if stage["tool"] not in TASK_TOOLS:
            raise ContractViolation("Task tool is not available")
        dependencies = stage.get("dependsOn", [])
        if len(dependencies) != len(set(dependencies)):
            raise ContractViolation("Stage dependencies must be unique")
        if any(dependency not in prior for dependency in dependencies):
            raise ContractViolation("Dependencies must point to earlier stages")
        referenced = {source for source, _, _ in _references(stage["input"])}
        if not referenced.issubset(set(dependencies)):
            raise ContractViolation("Every referenced result must be a declared dependency")
        prior.add(stage["id"])


def _numeric_source(
    source_id: str,
    field: str,
    definitions: dict[str, dict[str, Any]],
    results: dict[str, dict[str, Any]],
) -> tuple[str, str, str]:
    definition = definitions.get(source_id)
    result = results.get(source_id)
    if definition is None or result is None:
        raise _DependencyBlocked(source_id, "invalid_request", "Referenced stage has no completed result")
    if result.get("status") not in {"exact", "approximate"}:
        raise _DependencyBlocked(source_id, "insufficient_data", "Only exact or approximate numeric results can feed another operation")

    tool = definition["tool"]
    source_input = definition["input"]
    if tool == "calculation.evaluate" and field == "value":
        value, unit, domain = result.get("value"), result.get("unit", ""), source_input["domain"]
    elif tool == "calculation.convertUnits" and field == "convertedAmount":
        value, unit, domain = result.get("convertedAmount"), result.get("targetUnit", ""), "real"
    elif tool == "calculation.addQuantities" and field == "sum":
        value, unit, domain = result.get("sum"), result.get("unit", ""), "real"
    else:
        raise _DependencyBlocked(source_id, "invalid_request", "This result field is not a supported numeric value")
    if not isinstance(value, str) or _NUMERIC.fullmatch(value) is None:
        raise _DependencyBlocked(source_id, "domain_error", "Referenced result is not a scalar in the supported numeric grammar")
    return value, unit, domain


def _check_references(
    stage: dict[str, Any],
    resolved_input: dict[str, Any],
    definitions: dict[str, dict[str, Any]],
    results: dict[str, dict[str, Any]],
) -> None:
    for source_id, field, path in _references(stage["input"]):
        _, unit, domain = _numeric_source(source_id, field, definitions, results)
        tool = stage["tool"]
        if tool == "calculation.evaluate" and len(path) == 2 and path[0] == "operands" and isinstance(path[1], int):
            if unit:
                raise _DependencyBlocked(source_id, "unit_mismatch", "A unit-bearing result cannot enter a unitless arithmetic operation")
            if domain != stage["input"]["domain"]:
                raise _DependencyBlocked(source_id, "domain_error", "Source and destination arithmetic domains must match")
        elif tool == "calculation.convertUnits" and path == ("amount",):
            if not unit or resolved_input.get("sourceUnit") != unit:
                raise _DependencyBlocked(source_id, "unit_mismatch", "Source unit must exactly match the referenced value; convert explicitly first")
            if domain != "real":
                raise _DependencyBlocked(source_id, "domain_error", "Unit conversion accepts real values only")
        elif tool == "calculation.addQuantities" and len(path) == 3 and path[0] == "quantities" and isinstance(path[1], int) and path[2] == "amount":
            quantities = resolved_input.get("quantities", [])
            if path[1] >= len(quantities) or not unit or quantities[path[1]].get("unit") != unit:
                raise _DependencyBlocked(source_id, "unit_mismatch", "Quantity unit must exactly match the referenced value")
            if domain != "real":
                raise _DependencyBlocked(source_id, "domain_error", "Quantity operations accept real values only")
        else:
            raise _DependencyBlocked(source_id, "invalid_request", "This destination field cannot consume a calculated result")


def _stage_outcome(tool: str, result: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    missing_dependencies: list[str] = []
    missing_inputs: list[str] = []
    if "code" in result:
        if result["code"] in {"unavailable", "limit_exceeded"}:
            missing_dependencies.append(f"capacidade local ou limite disponível para {tool}")
            return "blocked", missing_dependencies, missing_inputs
        if result["code"] == "insufficient_data":
            missing_inputs.append(result["message"])
            return "needs_input", missing_dependencies, missing_inputs
        return "failed", missing_dependencies, missing_inputs
    if result.get("status") in {"insufficient_data", "ambiguous"}:
        prompts = result.get("conditions", result.get("assumptions", []))
        missing_inputs.extend(item for item in prompts if isinstance(item, str) and item.strip())
        if not missing_inputs:
            missing_inputs.append("Forneça os dados que faltam para executar esta operação matemática.")
        return "needs_input", missing_dependencies, missing_inputs
    return "completed", missing_dependencies, missing_inputs


def _resume_claims(
    checkpoint: dict[str, Any],
    definition_digest: str,
    definitions: dict[str, dict[str, Any]],
) -> dict[str, dict[str, str]]:
    if checkpoint["objectiveDigest"] != definition_digest:
        raise ContractViolation("Checkpoint belongs to a different task definition")
    claims: dict[str, dict[str, str]] = {}
    for item in checkpoint["completedStages"]:
        stage = definitions.get(item["id"])
        if item["id"] in claims or stage is None:
            raise ContractViolation("Checkpoint contains duplicate or unknown stage IDs")
        if item["tool"] != stage["tool"] or item["stageDigest"] != _stage_digest(stage):
            raise ContractViolation("Checkpoint stage does not match the task")
        claims[item["id"]] = item
    return claims


def run_task(
    payload: Any,
    *,
    execute_tool: _Runner | None = None,
    cancel_event: threading.Event | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    """Execute a bounded serial task; all tool calls are side-effect-free calculations."""
    try:
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
        if len(encoded) > 80_000:
            return error_result("limit_exceeded", "Task exceeds 80000 bytes.")
        validate(TASK_SCHEMA, payload)
        limits = dict(_DEFAULT_LIMITS)
        limits.update(payload.get("limits", {}))
        _graph(payload["stages"], limits)
        definition_digest = _digest(_definition(payload, limits))
        definitions = {stage["id"]: stage for stage in payload["stages"]}
        claims = _resume_claims(payload["resume"], definition_digest, definitions) if payload.get("resume") else {}
        task_id = str(uuid.UUID(payload.get("resume", {}).get("taskId", str(uuid.uuid4()))))
    except (ContractViolation, KeyError, TypeError, ValueError, RecursionError) as exc:
        return error_result("invalid_request", str(exc) or "Task contract is invalid")

    runner = execute_tool or (lambda tool, data, _event: execute(tool, data))
    started = clock()
    results: dict[str, dict[str, Any]] = {}
    states: dict[str, str] = {}
    output_stages: list[dict[str, Any]] = []
    missing_dependencies: list[str] = []
    missing_inputs: list[str] = []
    stop_status: str | None = None
    capability_ran = False

    for stage in payload["stages"]:
        if cancel_event is not None and cancel_event.is_set():
            stop_status = "cancelled"
            break
        if clock() - started >= limits["timeoutMs"] / 1000:
            stop_status = "timed_out"
            break
        stage_id, tool = stage["id"], stage["tool"]
        blocked_by = [dependency for dependency in stage.get("dependsOn", []) if states.get(dependency) != "completed"]
        if blocked_by:
            states[stage_id] = "blocked"
            output_stages.append(
                {"id": stage_id, "tool": tool, "status": "blocked", "mode": "deterministic", "attempts": 0, "blockedBy": blocked_by}
            )
            continue

        mode = "simulated" if execute_tool is not None else ("checkpoint_recomputed" if stage_id in claims else "deterministic")
        record: dict[str, Any] = {"id": stage_id, "tool": tool, "status": "failed", "mode": mode, "attempts": 0}
        refs = _references(stage["input"])
        try:
            resolved_input = _resolve(stage["input"], results)
            if not isinstance(resolved_input, dict):
                raise ContractViolation("Resolved stage input must be an object")
            _check_references(stage, resolved_input, definitions, results)
            try:
                validate_input(tool, resolved_input)
            except ContractViolation as exc:
                if refs:
                    raise _DependencyBlocked(refs[0][0], "invalid_request", "Referenced output does not match the destination input contract") from exc
                raise
        except _DependencyBlocked as exc:
            states[stage_id] = "blocked"
            output_stages.append(
                {
                    "id": stage_id,
                    "tool": tool,
                    "status": "blocked",
                    "mode": mode,
                    "attempts": 0,
                    "blockedBy": [exc.source_id],
                    "error": error_result(exc.code, str(exc)),
                }
            )
            continue
        except (ContractViolation, KeyError, TypeError, ValueError, RecursionError) as exc:
            states[stage_id] = "failed"
            output_stages.append(
                {"id": stage_id, "tool": tool, "status": "failed", "mode": mode, "attempts": 0, "error": error_result("invalid_request", str(exc) or "Stage input is invalid")}
            )
            continue

        for attempt in range(1, limits["maxAttempts"] + 1):
            if cancel_event is not None and cancel_event.is_set():
                stop_status = "cancelled"
                record["status"] = "cancelled"
                break
            if clock() - started >= limits["timeoutMs"] / 1000:
                stop_status = "timed_out"
                record["status"] = "timed_out"
                break
            record["attempts"] = attempt
            try:
                result = runner(tool, resolved_input, cancel_event)
            except KeyboardInterrupt:
                stop_status = "cancelled"
                record["status"] = "cancelled"
                break
            if not isinstance(result, dict):
                result = error_result("internal_error", "Calculation tool returned a non-object result")
            if "code" in result:
                try:
                    validate(ERROR_SCHEMA, result)
                except ContractViolation:
                    result = error_result("internal_error", "Calculation error failed its output contract")
                record["error"] = result
                outcome, absent, unanswered = _stage_outcome(tool, result)
                record["status"] = outcome
                if result.get("retryable") is True and attempt < limits["maxAttempts"]:
                    continue
                missing_dependencies.extend(absent)
                missing_inputs.extend(unanswered)
                break
            try:
                validate_result(tool, result)
            except ContractViolation:
                record["error"] = error_result("internal_error", "Calculation result failed its output contract")
                record["status"] = "failed"
                break
            capability_ran = True
            if cancel_event is not None and cancel_event.is_set():
                stop_status = "cancelled"
                record["status"] = "cancelled"
                break
            if clock() - started >= limits["timeoutMs"] / 1000:
                stop_status = "timed_out"
                record["status"] = "timed_out"
                break
            outcome, absent, unanswered = _stage_outcome(tool, result)
            record["status"] = outcome
            record["result"] = result
            missing_dependencies.extend(absent)
            missing_inputs.extend(unanswered)
            if outcome == "completed":
                results[stage_id] = result
                prior = claims.get(stage_id)
                if prior is not None and prior["resultDigest"] != _digest(result):
                    record["status"] = "failed"
                    record.pop("result", None)
                    record["error"] = error_result("invalid_request", "Checkpoint result changed; restart without this checkpoint")
                    results.pop(stage_id, None)
            break
        states[stage_id] = record["status"]
        output_stages.append(record)
        if stop_status:
            break

    if stop_status:
        for stage in payload["stages"][len(output_stages):]:
            output_stages.append({"id": stage["id"], "tool": stage["tool"], "status": stop_status, "mode": "deterministic", "attempts": 0})
    stage_states = [item["status"] for item in output_stages]
    has_failure = any(state in {"failed", "blocked"} for state in stage_states)
    has_completed = any(state == "completed" for state in stage_states)
    if stop_status:
        status = stop_status
    elif has_failure and has_completed:
        status = "partial"
    elif has_failure:
        status = "blocked" if all(state == "blocked" for state in stage_states) else "failed"
    elif any(state == "needs_input" for state in stage_states):
        status = "needs_input"
    else:
        status = "completed"

    completed = [
        {"id": stage["id"], "tool": stage["tool"], "stageDigest": _stage_digest(stage), "resultDigest": _digest(stage_result["result"])}
        for stage, stage_result in zip(payload["stages"], output_stages)
        if stage_result["status"] == "completed" and "result" in stage_result
    ]
    response = {
        "contractVersion": CONTRACT["contractVersion"],
        "taskId": task_id,
        "objective": payload["objective"],
        "status": status,
        "executed": capability_ran,
        "stages": output_stages,
        "missingDependencies": sorted(set(missing_dependencies)),
        "missingInputs": missing_inputs[:40],
        "limits": limits,
        "delegation": {"depthUsed": 0, "subagents": 0, "reason": "Todas as ferramentas matemáticas atuais são locais, determinísticas e sem efeitos colaterais."},
        "checkpoint": {"contractVersion": CONTRACT["contractVersion"], "taskId": task_id, "objectiveDigest": definition_digest, "completedStages": completed},
    }
    validate(TASK_RESULT_SCHEMA, response)
    output_size = len(json.dumps(response, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    if output_size > limits["maxOutputBytes"]:
        return error_result("limit_exceeded", "Task result exceeds maxOutputBytes; use a smaller operation or fewer stages.")
    return response
