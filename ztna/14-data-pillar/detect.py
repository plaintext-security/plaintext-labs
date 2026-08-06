#!/usr/bin/env python3
"""Teaching matcher: apply a Sigma rule to Zero Trust access log JSONL events, offline.

Same offline teaching harness as Module 09 (zt-monitoring-detection) — field equality
and the |contains / |startswith / |endswith modifiers, `condition: selection` and
`selection and not filter`, case-insensitive string matching. This copy adds exactly
one thing Module 09's matcher didn't need: a **count aggregation** condition, because
the Data pillar's exfil signal is volume in one session, not a single anomalous field.

  * field equality, and the |contains / |startswith / |endswith modifiers
  * a list of values under one key  -> OR
  * multiple keys in one selection  -> AND
  * condition: `selection`, `selection and not filter`, or
               `selection | count() by <field> > <N>`
  * matching is case-insensitive (as Sigma string matching is by default)

`selection | count() by <field> > <N>` groups the selection-matching events by
<field> (here, session_id) and fires only for groups whose count exceeds <N> — the
offline stand-in for a real backend's `stats count by session_id` / EQL sequence
aggregation. `sigma convert` compiles the same rule to a real backend's aggregation
syntax where the pipeline supports it; this matcher exists so you can iterate on the
rule without a SIEM.

Key Zero Trust note: the classification label on every restricted-data event is
itself the output of the access-control decision in ../data/policies/ — the Sigma
rule and the Rego policy are reading the SAME label for two different jobs. OPA
decides whether ONE request may proceed; this rule decides whether a SESSION'S total
restricted reads look like exfiltration. Neither one does the other's job.
"""
import json
import re
import sys
from collections import defaultdict

import yaml

COUNT_CONDITION = re.compile(
    r"^selection\s*\|\s*count\(\)\s*by\s+(\w+)\s*>\s*(\d+)$"
)


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


def evaluate_simple(events, detection, condition):
    """`selection` or `selection and not filter` — per-event, same as Module 09."""
    hits = []
    for lineno, event in events:
        selection_hit = match_selection(event, detection.get("selection", {}))
        if condition == "selection":
            fired = selection_hit
        elif condition == "selection and not filter":
            fired = selection_hit and not match_selection(event, detection.get("filter", {}))
        else:
            fired = False
        if fired:
            hits.append((lineno, event, None))
    return hits


def evaluate_count(events, detection, group_field, threshold):
    """`selection | count() by <field> > <N>` — aggregate, then flag whole groups."""
    groups = defaultdict(list)
    for lineno, event in events:
        if match_selection(event, detection.get("selection", {})):
            groups[event.get(group_field)].append((lineno, event))

    hits = []
    for group_key, members in groups.items():
        if len(members) > threshold:
            for lineno, event in members:
                hits.append((lineno, event, f"{group_field}={group_key} count={len(members)}"))
    return hits


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: detect.py <rule.yml> <events.jsonl>")

    with open(sys.argv[1]) as fh:
        rule = yaml.safe_load(fh)
    detection = rule["detection"]
    title = rule.get("title", "<untitled>")
    tags = ", ".join(rule.get("tags", [])) or "-"
    condition = str(detection.get("condition", "selection")).strip()

    events = []
    with open(sys.argv[2]) as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            events.append((lineno, json.loads(line)))

    count_match = COUNT_CONDITION.match(condition)
    if count_match:
        group_field, threshold = count_match.group(1), int(count_match.group(2))
        hits = evaluate_count(events, detection, group_field, threshold)
    elif condition in ("selection", "selection and not filter"):
        hits = evaluate_simple(events, detection, condition)
    else:
        sys.exit(
            f"This teaching matcher supports `condition: selection`, "
            f"`selection and not filter`, or `selection | count() by <field> > <N>` "
            f"only (got: {condition!r}). Real backends handle the full Sigma condition "
            f"grammar."
        )

    for lineno, event, note in hits:
        user = event.get("user", "?")
        record_id = event.get("record_id", "?")
        classification = event.get("classification", "?")
        event_type = event.get("event_type", "?")
        ts = event.get("timestamp", "?")
        suffix = f"  [{note}]" if note else ""
        print(
            f"  [HIT] line {lineno}: {ts}  user={user}  record={record_id}  "
            f"classification={classification}  type={event_type}{suffix}"
        )

    print(f"\nRule: {title}   (ATT&CK: {tags})")
    print(f"Matched {len(hits)} of the events in {sys.argv[2]}.")
    sys.exit(0 if hits else 1)


if __name__ == "__main__":
    main()
