#!/usr/bin/env python3
"""Teaching matcher: apply a (subset-of-)Sigma rule to JSONL events, offline.

This is a LEARNING harness, not a SIEM. It implements the common Sigma matching
subset so you can watch a rule fire against real-shaped telemetry without standing
up a backend:

  * field equality, and the |contains / |startswith / |endswith modifiers
  * a list of values under one key  -> OR
  * multiple keys in one selection  -> AND
  * condition: `selection`, or `selection and not filter`
  * matching is case-insensitive (as Sigma string matching is by default)

In production you do NOT hand-roll a matcher — you `sigma convert` the *same* rule
to your SIEM's query language (see `make convert`) and let the SIEM do this. The
point of the lab is that the rule is identical either way: that is detection-as-code.
"""
import json
import sys

import yaml


def as_list(value):
    return value if isinstance(value, list) else [value]


def match_field(event_value, modifier, expected):
    """True if event_value satisfies the modifier against any expected value (OR)."""
    if event_value is None:
        return False
    haystack = str(event_value).lower()
    for exp in as_list(expected):
        needle = str(exp).lower()
        if modifier is None and haystack == needle:
            return True
        if modifier == "contains" and needle in haystack:
            return True
        if modifier == "startswith" and haystack.startswith(needle):
            return True
        if modifier == "endswith" and haystack.endswith(needle):
            return True
    return False


def match_selection(event, selection):
    """Every key must match (AND). `field|modifier` splits the modifier off."""
    for key, expected in selection.items():
        field, _, modifier = key.partition("|")
        if not match_field(event.get(field), modifier or None, expected):
            return False
    return True


def evaluate(event, detection):
    condition = str(detection.get("condition", "selection")).strip()
    selection_hit = match_selection(event, detection.get("selection", {}))
    if condition == "selection":
        return selection_hit
    if condition == "selection and not filter":
        return selection_hit and not match_selection(event, detection.get("filter", {}))
    sys.exit(
        f"This teaching matcher supports `condition: selection` or "
        f"`selection and not filter` only (got: {condition!r}). "
        f"Real backends handle the full Sigma condition grammar."
    )


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: detect.py <rule.yml> <events.jsonl>")

    with open(sys.argv[1]) as fh:
        rule = yaml.safe_load(fh)
    detection = rule["detection"]
    title = rule.get("title", "<untitled>")
    tags = ", ".join(rule.get("tags", [])) or "-"

    hits = 0
    with open(sys.argv[2]) as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            event = json.loads(line)
            if evaluate(event, detection):
                hits += 1
                cmd = str(event.get("CommandLine", ""))[:80]
                print(f"  [HIT] line {lineno}: {event.get('Image', '?')}  {cmd}")

    print(f"\nRule: {title}   (ATT&CK: {tags})")
    print(f"Matched {hits} of the events in {sys.argv[2]}.")
    sys.exit(0 if hits else 1)


if __name__ == "__main__":
    main()
