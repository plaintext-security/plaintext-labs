#!/usr/bin/env python3
"""Detection / telemetry drift harness — compare declared baseline vs. observed.

This is a TEACHING harness, not a SIEM health monitor. It implements the two
halves of drift detection so you can watch them fire against bundled data:

  1. TELEMETRY drift  — per-source heartbeat + volume check. A binary "is it up?"
     view misses a *degraded* source (still emitting, but a fraction of its
     baseline), so we check last-seen AND volume floor.
  2. DETECTION drift  — re-score a Sigma rule against a held-out LABELLED corpus
     and diff recall against the t=0 baseline. A field rename upstream leaves a
     rule that still parses and "runs" but whose recall has fallen to zero. That
     decay is invisible to a syntax check; only re-firing against ground truth
     catches it.

Then it prints a drift report (expected-vs-observed sources + rule recall
regression) and exits non-zero when any drift is present, so it can be a
scheduled control (see `make drift-check`).

  usage:
    drift_check.py --baseline baseline/sources.yml \\
                   --events <events.jsonl> --corpus <corpus.jsonl> \\
                   --rule rules/encoded_powershell.yml \\
                   [--baseline-recall 1.0]

In production you do not hand-roll this — your SIEM ships source-health and
detection-efficacy metrics. The point of the lab is the LOOP: declare a
baseline, observe, diff, reconcile.
"""
import argparse
import json
import sys
from datetime import datetime

import yaml

# --- shared Sigma matching subset (same semantics as module 08's detect.py) ---


def as_list(value):
    return value if isinstance(value, list) else [value]


def match_field(event_value, modifier, expected):
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
    for key, expected in selection.items():
        field, _, modifier = key.partition("|")
        if not match_field(event.get(field), modifier or None, expected):
            return False
    return True


def rule_matches(event, detection):
    condition = str(detection.get("condition", "selection")).strip()
    hit = match_selection(event, detection.get("selection", {}))
    if condition == "selection":
        return hit
    if condition == "selection and not filter":
        return hit and not match_selection(event, detection.get("filter", {}))
    sys.exit(f"unsupported condition: {condition!r}")


# --- telemetry drift: heartbeat + volume ------------------------------------


def parse_ts(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")


def telemetry_drift(baseline, events):
    """Return (rows, drifted) where rows is a per-source status table."""
    by_source = {}
    last_seen = {}
    for e in events:
        comp = str(e.get("Computer", "")).split(".")[0]  # short hostname
        by_source[comp] = by_source.get(comp, 0) + 1
        ts = e.get("UtcTime")
        if ts:
            t = parse_ts(ts)
            if comp not in last_seen or t > last_seen[comp]:
                last_seen[comp] = t

    # reference "now" = latest event seen anywhere in the window
    now = max(last_seen.values()) if last_seen else None

    rows = []
    drifted = False
    for src in baseline["sources"]:
        name = src["name"]
        seen = by_source.get(name, 0)
        ls = last_seen.get(name)
        decommissioned = bool(src.get("decommissioned", False))

        # overdue if never seen, or last-seen older than its interval
        overdue = ls is None or (
            now is not None and (now - ls).total_seconds() > src["heartbeat_interval_s"]
        )
        below_floor = seen < src["volume_floor"]

        if decommissioned:
            status = "OK (decommissioned, silence expected)"
            is_drift = False
        elif seen == 0:
            status = "DRIFT: DEAD (no events — source offline?)"
            is_drift = True
        elif below_floor:
            status = f"DRIFT: DEGRADED (volume {seen} < floor {src['volume_floor']})"
            is_drift = True
        elif overdue:
            status = "DRIFT: OVERDUE (last event older than heartbeat interval)"
            is_drift = True
        else:
            status = "OK"
            is_drift = False

        drifted = drifted or is_drift
        rows.append(
            {
                "name": name,
                "observed": seen,
                "floor": src["volume_floor"],
                "last_seen": ls.strftime("%Y-%m-%d %H:%M") if ls else "never",
                "status": status,
            }
        )
    return rows, drifted


# --- detection drift: re-score a rule against a labelled corpus --------------


def recall_against_corpus(detection, corpus):
    """recall = matched-malicious / total-malicious on the labelled corpus."""
    mal = mal_hit = 0
    fp = 0
    for e in corpus:
        label = e.get("_label")
        ev = {k: v for k, v in e.items() if k != "_label"}
        hit = rule_matches(ev, detection)
        if label == "malicious":
            mal += 1
            if hit:
                mal_hit += 1
        elif label == "benign" and hit:
            fp += 1
    recall = (mal_hit / mal) if mal else 0.0
    return recall, mal_hit, mal, fp


def load_jsonl(path):
    out = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def main():
    ap = argparse.ArgumentParser(description="Detection/telemetry drift check.")
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--events", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--rule", required=True)
    ap.add_argument(
        "--baseline-recall",
        type=float,
        default=1.0,
        help="t=0 recall for the rule on the corpus (snapshot at `make baseline`).",
    )
    args = ap.parse_args()

    with open(args.baseline) as fh:
        baseline = yaml.safe_load(fh)
    with open(args.rule) as fh:
        rule = yaml.safe_load(fh)
    detection = rule["detection"]
    events = load_jsonl(args.events)
    corpus = load_jsonl(args.corpus)

    print("=" * 70)
    print("DRIFT REPORT")
    print(f"  baseline : {args.baseline}")
    print(f"  events   : {args.events}")
    print(f"  corpus   : {args.corpus}")
    print("=" * 70)

    # 1. Telemetry drift
    rows, telem_drift = telemetry_drift(baseline, events)
    print("\n[1] TELEMETRY HEALTH (expected vs. observed)")
    print(f"  {'SOURCE':<14}{'OBSERVED':>9}{'FLOOR':>7}  {'LAST SEEN':<18}STATUS")
    for r in rows:
        print(
            f"  {r['name']:<14}{r['observed']:>9}{r['floor']:>7}  "
            f"{r['last_seen']:<18}{r['status']}"
        )

    # 2. Detection drift
    recall, hit, total, fp = recall_against_corpus(detection, corpus)
    rule_title = rule.get("title", "<untitled>")
    regressed = recall < args.baseline_recall
    print("\n[2] DETECTION EFFICACY (re-scored against held-out corpus)")
    print(f"  rule         : {rule_title}")
    print(f"  baseline recall (t=0) : {args.baseline_recall:.2f}")
    print(f"  observed recall       : {recall:.2f}  ({hit}/{total} malicious caught)")
    print(f"  false positives       : {fp}")
    if regressed:
        cause = (
            "rule still parses & runs but matches nothing — suspect a renamed/"
            "missing field upstream (schema drift)"
            if recall == 0.0
            else "partial recall loss"
        )
        print(f"  >>> DRIFT: recall regressed from baseline — {cause}")
    else:
        print("  recall holding at baseline — no detection drift.")

    # 3. Verdict
    any_drift = telem_drift or regressed
    print("\n" + "=" * 70)
    if any_drift:
        print("VERDICT: DRIFT DETECTED — reconcile before trusting coverage.")
    else:
        print("VERDICT: CLEAN — observed state matches the declared baseline.")
    print("=" * 70)
    sys.exit(1 if any_drift else 0)


if __name__ == "__main__":
    main()
