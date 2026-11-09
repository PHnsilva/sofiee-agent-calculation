"""Validate public synthetic evaluation case structure and deterministic fixture rules."""
import json
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "evals" / "manifest.json"
PROJECT = "sofiee-agent-calculation"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message):
    raise SystemExit(f"eval-fixtures: FAIL: {message}")


def check_deterministic(case):
    check = case.get("deterministicCheck")
    if not check:
        return
    kind = check["kind"]
    if kind == "fraction":
        left, right = map(Fraction, check["operands"])
        operations = {
            "add": lambda: left + right,
            "subtract": lambda: left - right,
            "multiply": lambda: left * right,
            "divide": lambda: left / right,
        }
        if check["operation"] not in operations:
            fail(f"{case['id']}: unsupported exact operation")
        actual = operations[check["operation"]]()
    elif kind == "percent_of":
        actual = Fraction(check["percent"]) * Fraction(check["value"]) / 100
    elif kind == "scale":
        actual = Fraction(check["value"]) * Fraction(check["factor"])
    else:
        fail(f"{case['id']}: unsupported deterministic check {kind}")
    if actual != Fraction(check["expected"]):
        fail(f"{case['id']}: expected {check['expected']}, computed {actual}")


def filter_value(candidate, key):
    return candidate.get(key)


def check_search(case):
    if "expectedFilterResult" not in case:
        return
    accepted, unverified, rejected = [], [], []
    for candidate in case.get("candidates", []):
        statuses = []
        for key, expected in case["requiredFilters"].items():
            observed = filter_value(candidate, key)
            if observed is None:
                statuses.append("unverified")
            elif isinstance(expected, str):
                statuses.append("pass" if observed.casefold() == expected.casefold() else "fail")
            else:
                statuses.append("pass" if observed == expected else "fail")
        if "fail" in statuses:
            rejected.append(candidate["id"])
        elif "unverified" in statuses:
            unverified.append(candidate["id"])
        else:
            accepted.append(candidate["id"])
    got = {
        "accepted": sorted(accepted),
        "unverified": sorted(unverified),
        "rejected": sorted(rejected),
    }
    expected = {key: sorted(value) for key, value in case["expectedFilterResult"].items()}
    if got != expected:
        fail(f"{case['id']}: filter intersection mismatch {got} != {expected}")


def main():
    manifest = load_json(MANIFEST)
    if manifest["project"] != PROJECT or manifest["version"] != "1.0.0":
        fail("manifest project/version mismatch")
    reserve = manifest["reserve"]
    if reserve["policyVersion"] != "1.0.0" or reserve["status"] != "defined_not_populated":
        fail("reserve policy must be versioned and explicitly unpopulated")
    if reserve["custodian"] != "Pedro" or reserve["publiclyIncluded"] or reserve["agentAccessible"]:
        fail("reserve custody/privacy boundary mismatch")
    if reserve["caseIds"]:
        fail("private reserve case identifiers must not be published")

    contract = load_json(ROOT / "contracts" / "v1" / "contracts.json")
    contract_tools = {tool["name"] for tool in contract["tools"]}
    all_ids, covered_tools, count = set(), set(), 0
    for split in ("development", "regression"):
        dataset = manifest["datasets"][split]
        if dataset["version"] != "1.0.0" or dataset["public"] is not True:
            fail(f"{split}: expected a public version 1.0.0 set")
        data = load_json(ROOT / dataset["path"])
        if data["dataset"] != split or data["version"] != dataset["version"]:
            fail(f"{split}: dataset header mismatch")
        if data["caseIds"] != dataset["caseIds"]:
            fail(f"{split}: manifest case id mismatch")
        for case in data["cases"]:
            case_id = case["id"]
            if case_id in all_ids:
                fail(f"duplicate case id {case_id}")
            all_ids.add(case_id)
            if case["synthetic"] is not True or case["humanReviewRequired"] is not True:
                fail(f"{case_id}: public cases must be synthetic and reviewed by a human")
            if case["contractTool"] not in contract_tools:
                fail(f"{case_id}: unknown contract tool {case['contractTool']}")
            if not case["criteria"] or not case["criticalFailures"]:
                fail(f"{case_id}: missing observable criteria or critical failures")
            if "modelOutput" in case or "actualOutput" in case:
                fail(f"{case_id}: fixture must not claim a model result")
            covered_tools.add(case["contractTool"])
            check_deterministic(case)
            if PROJECT == "sofiee-agent-search":
                check_search(case)
            count += 1

    if all_ids != set(manifest["datasets"]["development"]["caseIds"] + manifest["datasets"]["regression"]["caseIds"]):
        fail("manifest must list exactly the public case IDs")
    required = set(manifest["requiredContractTools"])
    if required != covered_tools:
        fail(f"contract tool coverage mismatch; expected {sorted(required)}, got {sorted(covered_tools)}")

    if PROJECT == "sofiee-agent-search":
        camisa = [
            case for case in load_json(ROOT / manifest["datasets"]["development"]["path"])["cases"]
            if "camisa branca" in case["stimulus"].lower()
        ]
        if not camisa:
            fail("missing camisa branca synthetic case")
        filters = camisa[0]["requiredFilters"]
        if filters.get("category") != "camisa" or filters.get("color") != "branca":
            fail("camisa branca requires separate category and color filters")
        if any(case.get("sourceHints") for case in camisa):
            fail("example must not impose a global source allowlist")

    if PROJECT == "sofiee-agent-validation":
        cases = [
            case
            for split in ("development", "regression")
            for case in load_json(ROOT / manifest["datasets"][split]["path"])["cases"]
        ]
        if not any(case["expectedDisposition"] == "format_invalid_truth_unverified" for case in cases):
            fail("format validity must remain distinct from truth")
        if not any(case["contractTool"] == "validation.auditSearchResults" and case["expectedDisposition"] == "inconclusive" and not case["sourceReopenedIndependently"] for case in cases):
            fail("unreopened Search references must not become confirmed")

    print(f"eval-fixtures: PASS; project={PROJECT}; public_cases={count}; contract_tools={len(covered_tools)}; reserve_policy=v1.0.0/unpopulated; no model outputs")


if __name__ == "__main__":
    main()
