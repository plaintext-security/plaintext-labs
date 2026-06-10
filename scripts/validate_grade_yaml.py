#!/usr/bin/env python3
"""Validate every lab's `grade.yaml` against the grader's schema.

`grade.py` trusts its manifests — it reads `manifest["lab"]`, iterates `checks`, and
dispatches on each check's `type`, pulling type-specific keys (`expects_sha256`, `file`,
`run`, …) with bare `c["..."]` lookups. A malformed manifest therefore fails late and
cryptically (a `KeyError` mid-grade) or, worse, silently grades nothing. This linter
catches those problems up front and runs in CI so a broken manifest never ships.

It checks, for each `*/grade.yaml`:
  - the file is valid YAML and parses to a mapping;
  - it has a non-empty `lab` (str) and a non-empty `checks` list;
  - every check is a mapping with a `name` (str) and a known `type`;
  - each check carries the fields its `type` requires (see REQUIRED_FIELDS), of the
    right shape — e.g. `flag` needs `expects_sha256`, `structural` needs `file`,
    `artifact_functional`/`target_state` need `run`, `ai_rubric` needs `file`.

Usage:
    python3 scripts/validate_grade_yaml.py                 # scan repo root (default)
    python3 scripts/validate_grade_yaml.py path/to/grade.yaml ...   # specific files
    python3 scripts/validate_grade_yaml.py --root some/dir  # scan a different tree

Exit 0 = every manifest is valid; 1 = at least one violation (all printed); 2 = bad args.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

# The check types the grader knows (must mirror grade.py's CHECKS dispatch table).
KNOWN_TYPES = {
    "flag",
    "structural",
    "artifact_functional",
    "target_state",
    "advisory",
    "ai_rubric",
}

# Per-type required keys. Each entry is (key, expected_python_type). These mirror the
# bare `c["..."]` lookups in grade.py's check_* functions — the keys that, if missing,
# raise a KeyError at grade time.
REQUIRED_FIELDS: dict[str, list[tuple[str, type]]] = {
    "flag": [("expects_sha256", str)],
    "structural": [("file", str)],
    "artifact_functional": [("run", str)],
    "target_state": [("run", str)],
    "advisory": [],
    "ai_rubric": [("file", str)],
}


def validate_check(check: object, idx: int) -> list[str]:
    """Return a list of human-readable problems with one check (empty == valid)."""
    where = f"checks[{idx}]"
    if not isinstance(check, dict):
        return [f"{where}: must be a mapping, got {type(check).__name__}"]

    errs: list[str] = []
    name = check.get("name")
    if not isinstance(name, str) or not name.strip():
        errs.append(f"{where}: missing non-empty string `name`")
    else:
        where = f"check {name!r}"

    ctype = check.get("type")
    if ctype is None:
        errs.append(f"{where}: missing `type`")
        return errs
    if ctype not in KNOWN_TYPES:
        errs.append(
            f"{where}: unknown type {ctype!r} "
            f"(known: {', '.join(sorted(KNOWN_TYPES))})"
        )
        return errs

    for key, expected_type in REQUIRED_FIELDS[ctype]:
        if key not in check:
            errs.append(f"{where}: type {ctype!r} requires `{key}`")
        elif not isinstance(check[key], expected_type):
            errs.append(
                f"{where}: `{key}` must be {expected_type.__name__}, "
                f"got {type(check[key]).__name__}"
            )

    # `required`, when present, must be a bool — the grader treats it as a gate flag.
    if "required" in check and not isinstance(check["required"], bool):
        errs.append(f"{where}: `required` must be true/false")

    return errs


def validate_manifest_data(data: object) -> list[str]:
    """Validate a parsed manifest (a Python object from yaml.safe_load)."""
    if not isinstance(data, dict):
        return [f"top level must be a mapping, got {type(data).__name__}"]

    errs: list[str] = []
    lab = data.get("lab")
    if not isinstance(lab, str) or not lab.strip():
        errs.append("missing non-empty string `lab`")

    checks = data.get("checks")
    if not isinstance(checks, list) or not checks:
        errs.append("missing non-empty `checks` list")
        return errs

    for i, check in enumerate(checks):
        errs.extend(validate_check(check, i))
    return errs


def validate_file(path: Path) -> list[str]:
    """Validate one grade.yaml file; returns a list of problems (empty == valid)."""
    try:
        text = path.read_text()
    except OSError as e:
        return [f"cannot read: {e}"]
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        return [f"invalid YAML: {e}"]
    if data is None:
        return ["file is empty"]
    return validate_manifest_data(data)


def discover(root: Path) -> list[Path]:
    """Find every grade.yaml under root (excluding common build/vendor dirs)."""
    skip = {".git", "node_modules", "site", "__pycache__"}
    return sorted(
        p for p in root.rglob("grade.yaml")
        if not any(part in skip for part in p.parts)
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("files", nargs="*", help="specific grade.yaml files (default: scan --root)")
    ap.add_argument("--root", default=".", help="tree to scan for */grade.yaml (default: .)")
    args = ap.parse_args(argv)

    if args.files:
        manifests = [Path(f) for f in args.files]
    else:
        root = Path(args.root)
        if not root.is_dir():
            print(f"error: --root {root} is not a directory", file=sys.stderr)
            return 2
        manifests = discover(root)

    if not manifests:
        print("error: no grade.yaml files found", file=sys.stderr)
        return 2

    total_errors = 0
    for path in manifests:
        errs = validate_file(path)
        if errs:
            total_errors += len(errs)
            print(f"FAIL {path}")
            for e in errs:
                print(f"       - {e}")
        else:
            print(f"ok   {path}")

    print()
    if total_errors:
        print(f"Validation FAILED: {total_errors} problem(s) across {len(manifests)} manifest(s).")
        return 1
    print(f"Validation passed: {len(manifests)} grade.yaml manifest(s) are well-formed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
