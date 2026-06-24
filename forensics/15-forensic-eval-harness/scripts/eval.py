#!/usr/bin/env python3
"""Forensic eval harness — score detectors on a held-out labelled corpus and gate.

This is the measurement layer Modules 11 and 12 were missing. It does three things:

  --detect   run the timestomp + YARA detectors over the bundled corpus and write
             per-file verdicts (a recorded result, not a vibe).
  --score    print the confusion matrix and precision / recall / F1 / FP-rate /
             accuracy for each detector, against the held-out answer key.
  --demo     run the gate on the GOOD detectors (passes, exit 0), then on the
             planted REGRESSION (fails) — and end with a single verdict line.

The detectors here are *honest stand-ins* so the loop runs offline and in CI: the
timestomp detector compares the bundled $SI/$FN metadata fixtures, and the YARA
detector runs the REAL `yara` binary over inert PE fixtures. In real use you drop
in your own Modules 11/12 rules; the corpus, eval, and gate are unchanged.

FAIL CLOSED: any unreadable fixture, unparseable config, missing label, or yara
error raises and exits non-zero. The gate never silently passes.
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

import yaml

DATA = "/data"
REGRESSED = "/regressed"


def die(msg):
    """Fail closed: print to stderr and exit non-zero."""
    print(f"ERROR (fail-closed): {msg}", file=sys.stderr)
    sys.exit(2)


def load_json(path):
    try:
        with open(path) as fh:
            return json.load(fh)
    except Exception as exc:  # noqa: BLE001 — fail closed on any load error
        die(f"could not load {path}: {exc}")


def load_yaml(path):
    try:
        with open(path) as fh:
            return yaml.safe_load(fh)
    except Exception as exc:  # noqa: BLE001
        die(f"could not load {path}: {exc}")


def parse_iso(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception as exc:  # noqa: BLE001
        die(f"unparseable timestamp {ts!r}: {exc}")


# --- detectors ---------------------------------------------------------------

def run_timestomp(divergence_seconds):
    """Return {file_id: 0|1}. 1 = flagged (suspected timestomp)."""
    corpus = load_json(os.path.join(DATA, "timestomp_corpus.json"))
    verdicts = {}
    for rec in corpus["files"]:
        si = parse_iso(rec["si_modified"])
        fn = parse_iso(rec["fn_modified"])
        gap = abs((si - fn).total_seconds())
        verdicts[rec["id"]] = 1 if gap > divergence_seconds else 0
    return verdicts


def ensure_pe_fixtures():
    """Generate the inert PE fixtures into /data/pe_fixtures if not present."""
    out = os.path.join(DATA, "pe_fixtures")
    if not os.path.isdir(out) or not os.listdir(out):
        gen = os.path.join(DATA, "make_pe_fixtures.py")
        rc = subprocess.run([sys.executable, gen, out]).returncode
        if rc != 0:
            die("PE fixture generation failed")
    return out


def run_yara(rule_file):
    """Return {filename: 0|1} by running the real yara binary over each fixture."""
    fixtures_dir = ensure_pe_fixtures()
    rule_path = rule_file if os.path.isabs(rule_file) else os.path.join(DATA, rule_file)
    if not os.path.isfile(rule_path):
        die(f"YARA rule not found: {rule_path}")
    verdicts = {}
    for name in sorted(os.listdir(fixtures_dir)):
        target = os.path.join(fixtures_dir, name)
        proc = subprocess.run(
            ["yara", rule_path, target], capture_output=True, text=True
        )
        if proc.returncode not in (0, 1):  # 0 = ran, may or may not match
            die(f"yara errored on {name}: {proc.stderr.strip()}")
        verdicts[name] = 1 if proc.stdout.strip() else 0
    return verdicts


# --- scoring -----------------------------------------------------------------

def confusion(verdicts, labels):
    tp = fp = tn = fn = 0
    for key, truth in labels.items():
        if key not in verdicts:
            die(f"detector produced no verdict for labelled item {key!r}")
        pred = verdicts[key]
        if pred and truth:
            tp += 1
        elif pred and not truth:
            fp += 1
        elif not pred and truth:
            fn += 1
        else:
            tn += 1
    return tp, fp, tn, fn


def metrics(tp, fp, tn, fn):
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    fp_rate = fp / (fp + tn) if (fp + tn) else 0.0
    accuracy = (tp + tn) / (tp + fp + tn + fn) if (tp + fp + tn + fn) else 0.0
    return precision, recall, f1, fp_rate, accuracy


def score_detector(name, verdicts, labels, the_metric):
    tp, fp, tn, fn = confusion(verdicts, labels)
    precision, recall, f1, fp_rate, accuracy = metrics(tp, fp, tn, fn)
    print(f"\n=== {name} ===")
    print(f"  confusion: TP={tp}  FP={fp}  TN={tn}  FN={fn}")
    print(f"  precision={precision:.3f}  recall={recall:.3f}  F1={f1:.3f}  "
          f"FP-rate={fp_rate:.3f}  accuracy={accuracy:.3f}")
    print(f"  >> the metric that matters here: {the_metric}")
    return {"precision": precision, "recall": recall, "f1": f1,
            "fp_rate": fp_rate, "accuracy": accuracy}


# --- gate --------------------------------------------------------------------

def run_pipeline(config_path, write_verdicts=False):
    cfg = load_yaml(config_path)
    if not cfg:
        die(f"empty/invalid detector config: {config_path}")
    labels = load_json(os.path.join(DATA, "labels.json"))

    ts_cfg = cfg.get("timestomp") or die("config missing 'timestomp'")
    yara_cfg = cfg.get("yara") or die("config missing 'yara'")

    ts_verdicts = run_timestomp(ts_cfg["divergence_seconds"])
    yara_verdicts = run_yara(yara_cfg["rule_file"])

    if write_verdicts:
        out = os.path.join(DATA, "verdicts.json")
        with open(out, "w") as fh:
            json.dump({"timestomp": ts_verdicts, "yara": yara_verdicts}, fh, indent=2)
        print(f"Wrote per-file verdicts to {out}")

    ts_scores = score_detector(
        "timestomp detector (hunting rule — favour RECALL)",
        ts_verdicts, labels["timestomp"],
        "recall — a missed timestomp is a host you never look at again; "
        "accuracy misleads (a 'flag nothing' detector scores high accuracy, zero recall).",
    )
    yara_scores = score_detector(
        "YARA dropper rule (auto-triage — favour PRECISION)",
        yara_verdicts, labels["yara"],
        "precision — every false positive is an analyst-hour drowning the triage queue.",
    )
    return cfg, ts_scores, yara_scores


def check_gate(cfg, ts_scores, yara_scores):
    gate = cfg.get("gate") or die("config missing 'gate'")
    failures = []

    min_recall = gate["timestomp"]["min_recall"]
    if ts_scores["recall"] < min_recall:
        failures.append(f"timestomp recall {ts_scores['recall']:.3f} < floor {min_recall}")

    min_precision = gate["yara"]["min_precision"]
    if yara_scores["precision"] < min_precision:
        failures.append(f"YARA precision {yara_scores['precision']:.3f} < floor {min_precision}")

    print("\n--- gate ---")
    if failures:
        for f in failures:
            print(f"  RED:  {f}")
        return False
    print(f"  GREEN: timestomp recall ≥ {min_recall} and YARA precision ≥ {min_precision}")
    return True


# --- entrypoints -------------------------------------------------------------

def cmd_detect():
    run_pipeline(os.path.join(DATA, "detectors.yml"), write_verdicts=True)


def cmd_score():
    run_pipeline(os.path.join(DATA, "detectors.yml"))


def cmd_demo():
    print("########################################################")
    print("# 1. GOOD detectors — the gate should be GREEN")
    print("########################################################")
    cfg, ts, ya = run_pipeline(os.path.join(DATA, "detectors.yml"))
    good_green = check_gate(cfg, ts, ya)

    print("\n\n########################################################")
    print("# 2. REGRESSED detectors — the gate should go RED")
    print("#    (YARA loosened to /update.bin alone; timestomp")
    print("#     threshold dropped to 2s so legit files trip it)")
    print("########################################################")
    cfg2, ts2, ya2 = run_pipeline(os.path.join(REGRESSED, "detectors_regressed.yml"))
    bad_green = check_gate(cfg2, ts2, ya2)

    print("\n========================================================")
    if good_green and not bad_green:
        print("PASS: gate is GREEN on the good detectors and RED on the regression")
        sys.exit(0)
    print("FAIL: expected GREEN-then-RED; "
          f"good_green={good_green} regression_green={bad_green}")
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--detect", action="store_true", help="write per-file verdicts")
    g.add_argument("--score", action="store_true", help="print the scorecard")
    g.add_argument("--demo", action="store_true", help="gate good (green) then regressed (red)")
    args = ap.parse_args()
    if args.detect:
        cmd_detect()
    elif args.score:
        cmd_score()
    else:
        cmd_demo()


if __name__ == "__main__":
    main()
