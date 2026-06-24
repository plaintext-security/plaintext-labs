#!/usr/bin/env python3
"""check_summary.py — cross-reference an AI incident summary's claims to artifacts.

Given an AI-drafted summary (with a structured YAML-ish front-matter block) and a
directory of primary artifacts, this walks every MECHANICAL claim — each CVE, ATT&CK
ID + tactic, hash, and timeline timestamp — and reports which trace to a bundled
artifact and which do NOT.

WHAT THIS DOES NOT DO (this limit *is* the lesson):
  It verifies STRUCTURE and PRESENCE only. It does NOT — and cannot — validate the
  root-cause narrative or any causal story. A field-checker can catch a hallucinated
  hash; it cannot catch a confidently-wrong "brute force" conclusion that the
  timeline contradicts. That error is yours to catch by hand.

FAIL LOUD, NOT SILENT: an unparseable front-matter, an unreadable artifact, or a
claim it cannot recognise is reported as NEEDS-HUMAN-REVIEW, never quietly passed.
A well-formed CVE/ATT&CK ID that is absent from evidence is FLAGGED — format-valid
is not evidence-valid.

Usage: check_summary.py <summary.md> <artifacts_dir>
Stdlib only (runs in python:3.12-slim, offline).
"""
import json
import os
import re
import sys

# ATT&CK technique -> canonical tactic(s), for the IDs in scope (offline ground truth
# from the bundled pe_features.json case). Used to catch a real ID under the WRONG tactic.
ATTCK_TACTICS = {
    "T1071.001": ["Command and Control"],
    "T1036.004": ["Defense Evasion"],
    "T1547.001": ["Persistence"],
    "T1110": ["Credential Access"],
}

CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,7}$")
ATTCK_RE = re.compile(r"^T\d{4}(\.\d{3})?$")
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class Reviewer:
    def __init__(self, artifacts_dir):
        self.dir = artifacts_dir
        self.blob = ""          # concatenated raw text of all artifacts
        self.hashes = set()     # every sha256 seen in artifacts
        self.timestamps = set() # every time-of-day "HH:MM:SS" seen in artifacts
        self._load()

    def _load(self):
        if not os.path.isdir(self.dir):
            fail_loud(f"artifacts dir not found: {self.dir}")
        for name in sorted(os.listdir(self.dir)):
            path = os.path.join(self.dir, name)
            if not os.path.isfile(path):
                continue
            try:
                text = open(path, encoding="utf-8", errors="replace").read()
            except Exception as exc:  # noqa: BLE001 — fail loud
                fail_loud(f"could not read artifact {name}: {exc}")
            self.blob += "\n" + text
            for h in re.findall(r"\b[0-9a-fA-F]{64}\b", text):
                self.hashes.add(h.lower())
            # Normalise every time across heterogeneous log formats (syslog
            # "Mar 14 22:14:07", ISO "…T22:14:07Z") down to HH:MM:SS, the way an
            # analyst cross-references a time-of-day across sources.
            for hms in re.findall(r"(\d{2}:\d{2}:\d{2})", text):
                self.timestamps.add(hms)

    def mentions(self, token):
        return token.lower() in self.blob.lower()


# --- a tiny, forgiving front-matter parser (stdlib only) ---------------------

def parse_frontmatter(md_text):
    """Extract the leading --- ... --- block and parse the claims we score.

    Deliberately small: we only need cves / attck / hashes / timeline / root_cause.
    Any structure it cannot parse -> fail loud.
    """
    m = re.search(r"^---\n(.*?)\n---", md_text, re.DOTALL)
    if not m:
        fail_loud("no YAML front-matter block found in summary")
    body = m.group(1)

    claims = {"cves": [], "attck": [], "hashes": [], "timeline": [], "root_cause": None}
    section = None
    for raw in body.splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        # top-level key
        top = re.match(r"^(\w+):\s*(.*)$", line)
        if top and not raw.startswith((" ", "-")):
            key, val = top.group(1), top.group(2).strip()
            if key == "root_cause":
                claims["root_cause"] = strip_quotes(val)
                section = None
            elif key in claims:
                section = key
            else:
                section = None
            continue
        # list items
        item = line.strip()
        if item.startswith("- "):
            payload = item[2:].strip()
            if section == "cves":
                claims["cves"].append(strip_quotes(payload.split("#")[0].strip()))
            elif section == "hashes":
                claims["hashes"].append({})  # filled by following indented keys
            elif section == "attck":
                claims["attck"].append({})
            elif section == "timeline":
                claims["timeline"].append({})
            # inline "- id: X" style
            inline = re.match(r"^(\w+):\s*(.*)$", payload)
            if inline and section in ("attck", "hashes", "timeline"):
                claims[section][-1][inline.group(1)] = strip_quotes(inline.group(2).split("#")[0].strip())
            continue
        # indented key under the last list item
        kv = re.match(r"^\s+(\w+):\s*(.*)$", raw)
        if kv and section in ("attck", "hashes", "timeline") and claims[section]:
            claims[section][-1][kv.group(1)] = strip_quotes(kv.group(2).split("#")[0].strip())
    return claims


def strip_quotes(s):
    s = s.strip()
    if len(s) >= 2 and s[0] in "\"'" and s[-1] == s[0]:
        return s[1:-1]
    return s


def fail_loud(msg):
    print(f"\n!! FAIL-LOUD: {msg}", file=sys.stderr)
    sys.exit(2)


# --- the checks --------------------------------------------------------------

def check_cves(claims, rev, findings):
    print("\n== CVEs ==")
    for cve in claims["cves"]:
        if not CVE_RE.match(cve):
            findings.append(("CVE", cve, "MALFORMED — needs human review"))
            print(f"  [REVIEW] {cve}: malformed CVE id")
            continue
        if rev.mentions(cve):
            print(f"  [ OK   ] {cve}: referenced in an artifact")
        else:
            findings.append(("CVE", cve, "well-formed but absent from all evidence"))
            print(f"  [FLAG  ] {cve}: well-formed but NOT in any artifact "
                  f"(format-valid != evidence-valid)")


def check_attck(claims, rev, findings):
    print("\n== ATT&CK techniques (id + tactic) ==")
    for entry in claims["attck"]:
        tid = entry.get("id", "")
        tactic = entry.get("tactic", "")
        if not ATTCK_RE.match(tid):
            findings.append(("ATT&CK", tid, "malformed id — needs human review"))
            print(f"  [REVIEW] {tid!r}: malformed technique id")
            continue
        valid = ATTCK_TACTICS.get(tid)
        if valid is None:
            findings.append(("ATT&CK", tid, "unknown id — needs human review"))
            print(f"  [REVIEW] {tid}: not in the case's known-technique set")
            continue
        if tactic in valid:
            print(f"  [ OK   ] {tid} under {tactic!r}")
        else:
            findings.append(("ATT&CK", tid, f"wrong tactic: claimed {tactic!r}, should be {valid}"))
            print(f"  [FLAG  ] {tid}: claimed tactic {tactic!r} but it belongs to {valid}")


def check_hashes(claims, rev, findings):
    print("\n== Hashes ==")
    for h in claims["hashes"]:
        sha = (h.get("sha256") or "").lower()
        art = h.get("artifact", "?")
        if not SHA256_RE.match(sha):
            findings.append(("hash", sha, "malformed — needs human review"))
            print(f"  [REVIEW] {art}: malformed sha256")
            continue
        if sha in rev.hashes:
            print(f"  [ OK   ] {art}: sha256 matches a bundled artifact")
        else:
            findings.append(("hash", f"{art}:{sha}", "does not match any artifact hash"))
            print(f"  [FLAG  ] {art}: sha256 {sha[:16]}… matches NO artifact")


def check_timeline(claims, rev, findings):
    print("\n== Timeline (timestamp present in artifacts?) ==")
    for entry in claims["timeline"]:
        ts = entry.get("time", "")
        ev = entry.get("event", "")
        if not ISO_RE.match(ts):
            findings.append(("timeline", ts, "malformed timestamp — needs human review"))
            print(f"  [REVIEW] {ts!r}: malformed timestamp")
            continue
        hms = ts[11:19]  # HH:MM:SS from the ISO claim
        if hms in rev.timestamps:
            print(f"  [ OK   ] {ts}: a log line bears this timestamp — {ev[:50]}")
        else:
            findings.append(("timeline", ts, f"no artifact at this time: {ev}"))
            print(f"  [FLAG  ] {ts}: NO artifact at this time — {ev[:50]}")


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: check_summary.py <summary.md> <artifacts_dir>")
    summary_path, artifacts_dir = sys.argv[1], sys.argv[2]

    try:
        md = open(summary_path, encoding="utf-8").read()
    except Exception as exc:  # noqa: BLE001
        fail_loud(f"could not read summary {summary_path}: {exc}")

    rev = Reviewer(artifacts_dir)
    claims = parse_frontmatter(md)
    findings = []

    check_cves(claims, rev, findings)
    check_attck(claims, rev, findings)
    check_hashes(claims, rev, findings)
    check_timeline(claims, rev, findings)

    print("\n" + "=" * 64)
    print(f"UNSUPPORTED / SUSPECT MECHANICAL CLAIMS: {len(findings)}")
    for kind, what, why in findings:
        print(f"  - [{kind}] {what}  ->  {why}")

    print("\n" + "-" * 64)
    print("LIMIT OF THIS TOOL (the lesson): it checked structure and presence only.")
    print("It did NOT validate the ROOT CAUSE. The summary asserts a brute-force")
    print("root cause — a field-checker cannot disprove that. You must trace the")
    print("causal chain against auth.log by hand (a single accepted login from a")
    print("new geography is NOT a brute force). That error is yours to catch.")
    print(f"\nClaimed root cause (UNVERIFIED by this tool): {claims['root_cause']}")

    # Exit non-zero if any mechanical claim is unsupported/suspect — fail closed so
    # this can gate a CI traceability check.
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
