"""Verify the pinned C: runtime and exact third-party dependency lock."""

import argparse
import importlib.metadata
import json
import platform
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    raise SystemExit(f"environment check: FAIL: {message}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", type=Path, default=ROOT / "environment.lock.json")
    args = parser.parse_args()
    lock = json.loads(args.lock.read_text(encoding="utf-8"))

    if lock.get("lockVersion") != 1:
        fail("unsupported lockVersion")
    if platform.system() != lock.get("targetOs"):
        fail(f"expected {lock.get('targetOs')}, got {platform.system()}")

    runtime = lock["runtime"]
    version = ".".join(str(part) for part in sys.version_info[:3])
    if platform.python_implementation() != runtime["implementation"]:
        fail(f"expected {runtime['implementation']}, got {platform.python_implementation()}")
    if version != runtime["version"]:
        fail(f"expected Python {runtime['version']}, got {version}")

    base_executable = Path(getattr(sys, "_base_executable", sys.executable)).resolve()
    if not base_executable.is_file():
        fail(f"base interpreter is missing: {base_executable}")
    if Path(sys.prefix).drive.upper() != "C:" or Path(sys.base_prefix).drive.upper() != "C:":
        fail("virtual environment and base interpreter must both reside on C:")

    license_file = Path(sys.base_prefix) / runtime["licenseFile"]
    if not license_file.is_file():
        fail(f"runtime license file is missing: {license_file}")

    lock_path = ROOT / lock["requirementsLock"]
    if not lock_path.is_file():
        fail(f"requirements lock is missing: {lock_path}")
    entries = [
        line.strip()
        for line in lock_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if lock.get("thirdPartyDependencies") != entries:
        fail("environment.lock.json does not exactly match requirements.lock")

    for item in entries:
        match = re.fullmatch(
            r"([A-Za-z0-9][A-Za-z0-9_.-]*)==([A-Za-z0-9][A-Za-z0-9.!+_-]*)",
            item,
        )
        if match is None:
            fail(f"dependency must be pinned exactly: {item}")
        name, expected = match.groups()
        try:
            actual = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            fail(f"locked dependency is not installed: {name}")
        if actual != expected:
            fail(f"{name} version mismatch: expected {expected}, got {actual}")

    print(
        "environment check: PASS; "
        f"{platform.python_implementation()} {version}; "
        f"base={base_executable}; venv={Path(sys.prefix)}; "
        f"third-party dependencies={len(entries)}"
    )


if __name__ == "__main__":
    main()
