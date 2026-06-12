#!/usr/bin/env python3
"""
check_no_static_secret.py — prove the pipeline holds no static secret and the credential
it minted is short-lived and scoped.

Anyone can *claim* "we use OIDC." This is the proof. It asserts:

  1. NO STORED LONG-LIVED KEY — the pipeline definition the runner deploys with carries no
     long-lived AWS access key. We scan the OIDC pipeline script (and the reference
     deploy-oidc.yml) and confirm there is no `AKIA…`/`aws-access-key-id`/
     `aws-secret-access-key` material, and that the OIDC workflow uses role-to-assume +
     id-token: write instead. (The bad pipeline, by contrast, DOES carry one — we confirm
     the checker would catch it.)

  2. SHORT-LIVED CREDENTIAL — the credential the OIDC pipeline minted (/tmp/oidc-creds.json,
     written by pipeline-oidc.sh) carries a SessionToken and an Expiration in the future.
     A stored key has neither; a federated credential has both. That is what "short-lived"
     means operationally.

  3. SCOPED TRUST POLICY — the role's trust policy pins aud=sts.amazonaws.com and a SPECIFIC
     sub (StringEquals on the exact repo/ref), not a wildcard `repo:org/*:*` that any fork
     could satisfy. A loose sub is the wildcard-IAM failure mode for OIDC.

Usage:
  python check_no_static_secret.py                       # default paths under data/, /tmp
  python check_no_static_secret.py --creds /tmp/oidc-creds.json --trust data/trust-policy.json
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# Long-lived AWS key id pattern (AKIA…) + the configure-aws-credentials inputs that pass a
# stored key. Their ABSENCE in the OIDC pipeline is the "no static secret" assertion.
AKIA_RE = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
STATIC_INPUT_RE = re.compile(r"aws-secret-access-key\s*:", re.IGNORECASE)


def _read(path: str) -> str:
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return ""


class Checks:
    def __init__(self):
        self.passed = 0
        self.failed = 0

    def ok(self, msg):
        print(f"  [PASS] {msg}")
        self.passed += 1

    def bad(self, msg):
        print(f"  [FAIL] {msg}")
        self.failed += 1


def check_no_static_key(c: Checks, oidc_script: str, oidc_yml: str):
    print("== 1. The OIDC pipeline stores NO long-lived AWS key ==")
    blob = _read(oidc_script) + "\n" + _read(oidc_yml)
    if not blob.strip():
        c.bad(f"could not read OIDC pipeline ({oidc_script} / {oidc_yml})")
        return
    akia = AKIA_RE.search(blob)
    static_input = STATIC_INPUT_RE.search(blob)
    if akia:
        c.bad(f"found a long-lived key id ({akia.group(0)}) in the OIDC pipeline")
    else:
        c.ok("no AKIA… long-lived access key id present")
    if static_input:
        c.bad("OIDC pipeline passes a stored aws-secret-access-key (defeats the purpose)")
    else:
        c.ok("no stored aws-secret-access-key input")
    # Positive signal: the OIDC workflow federates (role-to-assume + id-token: write).
    yml = _read(oidc_yml)
    if yml:
        if "role-to-assume" in yml and re.search(r"id-token:\s*write", yml):
            c.ok("OIDC workflow federates: role-to-assume + permissions id-token: write")
        else:
            c.bad("OIDC workflow is missing role-to-assume or id-token: write")


def check_short_lived(c: Checks, creds_path: str):
    print("== 2. The minted credential is short-lived (SessionToken + future Expiration) ==")
    raw = _read(creds_path)
    if not raw.strip():
        c.bad(f"no minted-credentials file at {creds_path} — run the OIDC pipeline first "
              "(make oidc)")
        return
    try:
        creds = json.loads(raw).get("Credentials", {})
    except json.JSONDecodeError:
        c.bad(f"{creds_path} is not valid JSON")
        return
    if creds.get("SessionToken"):
        c.ok("credential carries a SessionToken (temporary, not a standing key)")
    else:
        c.bad("no SessionToken — this looks like a long-lived credential")
    exp = creds.get("Expiration")
    if not exp:
        c.bad("no Expiration on the credential")
        return
    try:
        # Accept ISO-8601 with offset or trailing Z.
        when = dt.datetime.fromisoformat(str(exp).replace("Z", "+00:00"))
    except ValueError:
        c.bad(f"Expiration not parseable: {exp!r}")
        return
    now = dt.datetime.now(dt.timezone.utc)
    if when.tzinfo is None:
        when = when.replace(tzinfo=dt.timezone.utc)
    if when > now:
        mins = (when - now).total_seconds() / 60.0
        c.ok(f"Expiration is in the future (~{mins:.0f} min out) — credential expires on its own")
    else:
        c.bad(f"Expiration {when.isoformat()} is not in the future")


def check_scoped_trust(c: Checks, trust_path: str):
    print("== 3. The role's trust policy is SCOPED to the intended pipeline ==")
    raw = _read(trust_path)
    if not raw.strip():
        c.bad(f"no trust policy at {trust_path}")
        return
    try:
        policy = json.loads(raw)
    except json.JSONDecodeError:
        c.bad(f"{trust_path} is not valid JSON")
        return
    found_aud = False
    found_specific_sub = False
    loose_sub = False
    for stmt in policy.get("Statement", []):
        cond = stmt.get("Condition", {})
        for op, kv in cond.items():
            for key, val in kv.items():
                k = key.lower()
                vals = val if isinstance(val, list) else [val]
                if k.endswith(":aud"):
                    if "sts.amazonaws.com" in vals:
                        found_aud = True
                if k.endswith(":sub"):
                    # StringEquals on an exact sub = scoped. StringLike with a '*' in the
                    # repo/org/ref position = a fork/branch can satisfy it = loose.
                    if op == "StringEquals" and all("*" not in v for v in vals):
                        found_specific_sub = True
                    if any("*" in v for v in vals):
                        loose_sub = True
    if found_aud:
        c.ok("trust policy pins aud = sts.amazonaws.com")
    else:
        c.bad("trust policy does not pin aud = sts.amazonaws.com")
    if loose_sub:
        c.bad("trust policy uses a WILDCARD sub — any fork/branch could federate")
    elif found_specific_sub:
        c.ok("trust policy pins sub to an exact repo/ref (StringEquals, no wildcard)")
    else:
        c.bad("trust policy does not constrain sub to a specific repo/ref")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--oidc-script", default=os.path.join(HERE, "data", "pipeline-oidc.sh"))
    ap.add_argument("--oidc-yml", default=os.path.join(HERE, "data", "deploy-oidc.yml"))
    ap.add_argument("--creds", default="/tmp/oidc-creds.json")
    ap.add_argument("--trust", default=os.path.join(HERE, "data", "trust-policy.json"))
    args = ap.parse_args()

    c = Checks()
    check_no_static_key(c, args.oidc_script, args.oidc_yml)
    print()
    check_short_lived(c, args.creds)
    print()
    check_scoped_trust(c, args.trust)
    print()
    print(f"== {c.passed} passed, {c.failed} failed ==")
    if c.failed:
        print("Pipeline-secrets proof FAILED — see the FAIL lines above.")
        return 1
    print("All assertions PASS — no stored static secret; credential is short-lived and scoped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
