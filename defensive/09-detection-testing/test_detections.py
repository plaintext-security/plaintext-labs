#!/usr/bin/env python3
"""Purple-team detection test loop: fire atomics, check Sigma rules.

Detection engineering is a loop, not a one-shot task. For each technique:
  1. Simulate the attack (atomic)
  2. Check the detection (Sigma rule)
  3. Record FIRED / MISSED / FALSE-POSITIVE
  4. Tune and repeat

This script wires that loop for the rules in `rules/` and the atomics in
`atomics/`. Every atomic produces an event record; every rule is checked
against that record using a simple in-process matcher. No external SIEM needed.
"""
import glob
import importlib.util
import re
import sys
from pathlib import Path

import yaml

RULES_DIR   = Path(__file__).parent / "rules"
ATOMICS_DIR = Path(__file__).parent / "atomics"


# ── Sigma detection matcher ──────────────────────────────────────────────────

def _match_condition(event: dict, selection: dict) -> bool:
    """Evaluate one selection block against an event record."""
    for field_expr, value_spec in selection.items():
        # Parse field + modifiers (e.g. CommandLine|contains)
        parts = field_expr.split("|")
        field = parts[0]
        modifier = parts[1].lower() if len(parts) > 1 else "equals"

        field_val = str(event.get(field, ""))
        values = value_spec if isinstance(value_spec, list) else [value_spec]

        if modifier == "contains":
            if not any(str(v).lower() in field_val.lower() for v in values):
                return False
        elif modifier in ("startswith",):
            if not any(field_val.lower().startswith(str(v).lower()) for v in values):
                return False
        elif modifier in ("endswith",):
            if not any(field_val.lower().endswith(str(v).lower()) for v in values):
                return False
        else:
            if not any(str(v).lower() == field_val.lower() for v in values):
                return False
    return True


def rule_fires(rule: dict, event: dict) -> bool:
    detection = rule.get("detection", {})
    condition  = detection.get("condition", "")
    selections = {k: v for k, v in detection.items() if k != "condition"}

    # Evaluate all named selections
    results = {name: _match_condition(event, sel) for name, sel in selections.items()}

    # Evaluate the condition expression (simplified: handles "selection" and "all of *")
    if condition.strip() == "selection":
        return results.get("selection", False)
    if re.search(r"^all of \*$", condition.strip()):
        return all(results.values())
    # Fallback: any named selection matching → fire
    return any(results.values())


# ── Atomic loader ──────────────────────────────────────────────────────────

def load_atomic(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.run


def load_rules() -> list[dict]:
    rules = []
    for path in sorted(RULES_DIR.glob("*.yml")):
        data = yaml.safe_load(path.read_text())
        if data:
            data["_path"] = str(path.name)
            rules.append(data)
    return rules


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    rules   = load_rules()
    atomics = sorted(ATOMICS_DIR.glob("*.py"))

    print("=" * 62)
    print("Meridian Financial — Detection Test Loop")
    print(f"Rules: {len(rules)}   Atomics: {len(atomics)}")
    print("=" * 62)

    results = []

    for atomic_path in atomics:
        run_fn = load_atomic(atomic_path)
        event  = run_fn()

        tech     = event.get("technique") or "(benign)"
        is_benign = event.get("technique") is None
        print(f"\n{'─'*62}")
        print(f"[ATOMIC] {atomic_path.stem}")
        print(f"  technique: {tech}")
        print(f"  event:     EventID={event.get('EventID','?')}  "
              f"Image={event.get('Image','?')}")
        if "CommandLine" in event:
            cl = event["CommandLine"][:80]
            print(f"  cmdline:   {cl}")

        fired = []
        for rule in rules:
            if rule_fires(rule, event):
                fired.append(rule)

        if fired and is_benign:
            print(f"  result:    ⚠ FALSE POSITIVE — {len(fired)} rule(s) fired on benign activity")
            for r in fired:
                print(f"             → {r.get('title','?')}")
            results.append(("FP", atomic_path.stem, fired))
        elif fired and not is_benign:
            print(f"  result:    ✓ FIRED — {len(fired)} rule(s) matched")
            for r in fired:
                print(f"             → {r.get('title','?')}")
            results.append(("FIRED", atomic_path.stem, fired))
        else:
            label = "EXPECTED-CLEAN" if is_benign else "⚠ MISSED"
            print(f"  result:    {label}")
            results.append(("MISSED" if not is_benign else "CLEAN", atomic_path.stem, []))

    # Summary
    print(f"\n{'='*62}")
    print("Detection coverage summary:")
    fired_count  = sum(1 for r in results if r[0] == "FIRED")
    missed_count = sum(1 for r in results if r[0] == "MISSED")
    fp_count     = sum(1 for r in results if r[0] == "FP")
    clean_count  = sum(1 for r in results if r[0] == "CLEAN")
    print(f"  ✓ Fired:          {fired_count}")
    print(f"  ✗ Missed:         {missed_count}")
    print(f"  ⚠ False positive: {fp_count}")
    print(f"  ○ Clean (benign): {clean_count}")
    if fp_count:
        print("\n  False positives require rule tuning — add conditions to narrow scope.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
