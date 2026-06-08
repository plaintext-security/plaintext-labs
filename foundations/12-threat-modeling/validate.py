#!/usr/bin/env python3
"""
Threat Modeling lab — STRIDE template guide + threat-model.md validator.

Usage:
    python3 validate.py             # demo: validate the template + print guide
    python3 validate.py my-model.md # validate a completed threat model
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DIVIDER = "─" * 64
STRIDE_LETTERS = list("STRIDE")


def check(text: str, pattern: str, label: str) -> bool:
    found = bool(re.search(pattern, text, re.IGNORECASE))
    print(f"  {'✓' if found else '✗'}  {label}")
    return found


def count_stride_coverage(text: str) -> int:
    covered = []
    patterns = {
        "S": r"\bspoofing\b",
        "T": r"\btampering\b",
        "R": r"\brepudiation\b",
        "I": r"\binformation.disclosure\b",
        "D": r"\bdenial.of.service\b",
        "E": r"\belevation.of.privilege\b",
    }
    for letter, pattern in patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            covered.append(letter)
    missing = [l for l in STRIDE_LETTERS if l not in covered]
    if missing:
        print(f"  ✗  STRIDE: missing letters — {', '.join(missing)}")
    else:
        print(f"  ✓  STRIDE: all 6 letters covered (S T R I D E)")
    return len(covered)


def validate_model(path: Path) -> int:
    text = path.read_text(errors="replace")
    print(f"\n[Threat Model] Validating: {path.name}\n")

    results = []
    results.append(check(text, r"trust.boundar",          "Trust boundaries marked (≥1)"))
    results.append(check(text, r"trust.boundar.*\n.*trust.boundar|boundary.+\n.+boundary",
                                                            "Two+ trust boundaries"))
    stride_count = count_stride_coverage(text)
    results.append(stride_count == 6)
    results.append(check(text, r"mitigation|control|fix",  "Mitigations provided"))
    results.append(check(text, r"cia|confidential|integrit|availab",
                                                            "CIA properties referenced"))
    results.append(check(text, r"data.flow|dfd|element|flow",
                                                            "Data flow described"))
    results.append(check(text, r"ai|model|claude|gpt|gemini",
                                                            "AI reconciliation step done"))

    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"\n  Score: {passed}/{total}")
    if passed == total:
        print("  ✓ Threat model passes all checks")
    else:
        print(f"  ✗ {total - passed} check(s) missing")
    return 0 if passed == total else 1


def print_guide() -> None:
    print("""
══════════════════════════════════════════════════════════════
Lab 12 — Threat Modeling with STRIDE
══════════════════════════════════════════════════════════════

STRIDE is a mnemonic for six categories of threats. Work through each
letter for every element and every flow in your data-flow diagram.

──────────────────────────────────────────────────────────────
S — Spoofing          Can an attacker impersonate a user or component?
T — Tampering         Can data be modified in transit or at rest?
R — Repudiation       Can an actor deny performing an action?
I — Information       Can sensitive data be read by the wrong party?
    Disclosure
D — Denial of service Can the system be made unavailable?
E — Elevation of      Can an attacker gain higher privilege than intended?
    Privilege
──────────────────────────────────────────────────────────────

WORKFLOW:
  1. Draw the data flow (elements + flows + trust boundaries)
  2. For each element/flow, apply every STRIDE letter
  3. Write a CONCRETE threat (not "bad auth" — "forged JWT bypasses admin check")
  4. Propose a specific mitigation and name the CIA property it protects
  5. Have a model do its own STRIDE pass; prune and annotate the diff

TRUST BOUNDARIES (mark at least 2):
  Examples: internet/DMZ, DMZ/internal, user/kernel, client/server,
  third-party/our-system, pre-auth/post-auth.

TIPS:
  • Every S threat pairs with an authentication control
  • Every T threat pairs with a MAC/signature or parameterized query
  • Every E threat pairs with a least-privilege control
  • Vague threats ("SQL injection") are less useful than concrete ones
    ("attacker sends ' OR 1=1-- in login field, dumps user table")

OPTIONAL: model a real app:
    docker run --rm -d -p 3000:3000 bkimminich/juice-shop
    Open http://localhost:3000 — document threats against /login, /api/users
""")


def demo() -> int:
    print("=" * 64)
    print("Threat Modeling — Lab Validator Demo")
    print("=" * 64)

    template = DATA_DIR / "threat-model-template.md"
    print(f"\n[Demo] Validating bundled template: {template.name}")
    validate_model(template)
    print()
    print(DIVIDER)
    print_guide()
    print(DIVIDER)
    print("Template in: data/threat-model-template.md")
    print("Validate your model: python3 validate.py threat-model.md")
    print(DIVIDER + "\n")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(validate_model(Path(sys.argv[1])))
    sys.exit(demo())
