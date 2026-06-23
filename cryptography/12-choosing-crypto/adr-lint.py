#!/usr/bin/env python3
"""adr-lint.py — fail the build when a crypto ADR skips its discipline.

Judgment-as-Code: this encodes "every crypto decision must cite a standard and
own its consequences" as a check that FAILS on bad input. It is intentionally
dependency-free (Python 3 stdlib only) so it drops into any CI.

An ADR file FAILS (non-zero exit, with the reason printed) if it:
  * is missing any of the five required sections
        Context / Options / Decision / Consequences / What would change this
  * cites no recognised standard (RFC <n>, SP 800-<n>, or OWASP), or
  * has an empty Consequences or "What would change this" section.

Sections are matched as Markdown headings (any level, e.g. `## Consequences`),
case-insensitively, tolerating a trailing colon and minor wording
("What would change this" / "What would change this decision").

Usage:
  adr-lint.py adr/*.md
  adr-lint.py data/sample-adr-good.md data/sample-adr-bad.md
Exit code: 0 if every file passes, 1 if any file fails.
"""
import re
import sys

# Required sections -> regex matching their heading text (after the # markers).
REQUIRED_SECTIONS = {
    "Context": r"context",
    "Options": r"options|considered options|decision drivers",
    "Decision": r"decision(?! drivers)|decision outcome",
    "Consequences": r"consequences",
    "What would change this": r"what would change this(?:\s+decision)?",
}

# A recognised standard citation: RFC NNNN, NIST SP 800-NN(D), or OWASP.
STANDARD_RE = re.compile(r"\bRFC\s*\d+\b|\bSP\s*800-\d+[A-Z]?\b|\bOWASP\b", re.IGNORECASE)

HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$")


def parse_sections(text):
    """Return {normalized_heading_line: body_text} for every Markdown heading."""
    sections = {}
    current = None
    buf = []
    for line in text.splitlines():
        m = HEADING_RE.match(line)
        if m:
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = m.group(1).strip().rstrip(":").lower()
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections


def find_section_body(sections, pattern):
    """Body of the first heading whose text fully matches `pattern`, else None."""
    rx = re.compile(rf"^(?:{pattern})$", re.IGNORECASE)
    for heading, body in sections.items():
        if rx.match(heading):
            return body
    return None


def lint_file(path):
    """Return a list of failure reasons (empty list == pass)."""
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        return [f"could not read file: {exc}"]

    failures = []
    sections = parse_sections(text)

    bodies = {}
    for name, pattern in REQUIRED_SECTIONS.items():
        body = find_section_body(sections, pattern)
        if body is None:
            failures.append(f"missing required section: '{name}'")
        bodies[name] = body

    # Empty-body checks for the two sections where emptiness defeats the point.
    for name in ("Consequences", "What would change this"):
        body = bodies.get(name)
        if body is not None and not body.strip():
            failures.append(f"section '{name}' is present but EMPTY")

    if not STANDARD_RE.search(text):
        failures.append(
            "no recognised standard cited (expected an RFC NNNN, SP 800-NN, or OWASP reference)"
        )

    return failures


def main(argv):
    paths = argv[1:]
    if not paths:
        sys.exit("usage: adr-lint.py <adr1.md> [adr2.md ...]")

    any_failed = False
    for path in paths:
        failures = lint_file(path)
        if failures:
            any_failed = True
            print(f"FAIL  {path}")
            for reason in failures:
                print(f"      - {reason}")
        else:
            print(f"PASS  {path}")

    print()
    if any_failed:
        print("adr-lint: at least one ADR failed the gate.")
        sys.exit(1)
    print("adr-lint: all ADRs passed.")
    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
