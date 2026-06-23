#!/usr/bin/env python3
"""
drift-detect.py — scheduled AD posture-drift detector. Diffs the OBSERVED security posture
against a committed, declared BASELINE and emits a per-FACT delta (never a score), mapping
each regression to its ATT&CK technique. Exits non-zero when drift is found so it can gate
a CI job or alert from cron.

THE LOOP: detect (collect observed facts) -> diff (observed vs baseline, normalized) ->
report (per-fact delta, ATT&CK-mapped). Reconcile is a HUMAN step (bless-or-enforce) — this
tool never auto-reverts; a blind revert of a sanctioned change is its own outage.

WHY DIFF FACTS, NOT A SCORE. A posture score ("87/100") hides WHICH control moved. The whole
point is to name the concrete regression — "new Kerberoastable SPN on svc-newdb", "GenericWrite
re-added on Finance-Managers", "mnguyen joined Domain Admins", "krbtgt 211d > 180d threshold" —
so it can be adjudicated. We diff sorted, normalized facts so the delta shows real change, not
JSON key/list-ordering noise.

SIMULATION NOTE. The OBSERVED posture is read from data/observed.json (a seed mutated by
bin/drift-introduce.sh). In a full Samba-DC build the same facts would be COLLECTED LIVE via
the ldap3 queries sketched in collect_observed_live() below — the diff/report/exit logic is
identical. No live DC ships here (see VALIDATION.md).

SCORING DIRECTION (the thing a model inverts — verify it):
  * a FRESH krbtgt (age <= threshold) is CLEAN; a STALE one (> threshold) is DRIFT.
  * an ABSENT dangerous ACE / empty Kerberoastable list is CLEAN, NOT a finding.
  * an EXTRA member in a privileged group is drift; a MISSING expected member is ALSO drift.

  python3 drift-detect.py                 # human report; exit 1 if drift
  python3 drift-detect.py --json          # machine-readable delta
  python3 drift-detect.py --out report.md # also write a dated-style markdown report
"""
import argparse
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# ATT&CK mapping per fact category.
ATTCK = {
    "kerberoastable": ("T1558.003", "Steal or Forge Kerberos Tickets: Kerberoasting"),
    "asrep": ("T1558.004", "Steal or Forge Kerberos Tickets: AS-REP Roasting"),
    "unconstrained": ("T1558.001", "Steal or Forge Kerberos Tickets: Golden Ticket (delegation TGT theft)"),
    "dangerous_ace": ("T1098", "Account Manipulation (ACL abuse -> T1484.001 Group Policy Modification)"),
    "priv_group": ("T1098", "Account Manipulation: privileged-group membership"),
    "krbtgt": ("T1558.001", "standing Golden Ticket risk from a stale krbtgt"),
}


def load(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


def strip_comments(d):
    """Drop the _comment / _threshold annotation keys so they never appear in the diff."""
    if isinstance(d, dict):
        return {k: strip_comments(v) for k, v in d.items() if not k.startswith("_")}
    if isinstance(d, list):
        return [strip_comments(x) for x in d]
    return d


def collect_observed_live(host):  # pragma: no cover - documentation of the real-DC path
    """SKETCH of the live collector a Samba-DC build would use (ldap3). Not exercised in the
    simulation; here to make the gap explicit and to seed the learner's extension.

        from ldap3 import Server, Connection, ALL
        conn = Connection(Server(host, get_info=ALL), user=..., password=..., auto_bind=True)
        # kerberoastable: user objects with an SPN
        conn.search(base, '(&(objectClass=user)(servicePrincipalName=*)'
                          '(!(objectClass=computer)))', attributes=['sAMAccountName'])
        # asrep: uAC & 0x400000 ; unconstrained: uAC & 0x80000 (bit-and OID 1.2.840.113556.1.4.803)
        # priv group rosters: read member of CN=Domain Admins,... etc.
        # dangerous ACEs: parse nTSecurityDescriptor for non-default GenericWrite/WriteDacl/...
        # krbtgt age: now - pwdLastSet of CN=krbtgt
    The returned dict has the SAME shape as data/observed.json, so the diff below is reused
    verbatim."""
    raise NotImplementedError("live collector is the Samba-DC extension; see VALIDATION.md")


def diff_posture(baseline, observed, krbtgt_max):
    """Return an ordered list of per-fact drift items. Empty list == clean (no false drift)."""
    deltas = []

    def list_delta(category, key, label):
        b = sorted(json.dumps(x, sort_keys=True) for x in baseline.get(key, []))
        o = sorted(json.dumps(x, sort_keys=True) for x in observed.get(key, []))
        for added in [x for x in o if x not in b]:
            deltas.append({"category": category, "change": "added", "fact": json.loads(added),
                           "where": label, "attck": ATTCK[category]})
        for removed in [x for x in b if x not in o]:
            # An expected-but-now-absent hardened fact would appear here. For these lists the
            # hardened baseline is empty, so a removal is unusual but still surfaced (not hidden).
            deltas.append({"category": category, "change": "removed", "fact": json.loads(removed),
                           "where": label, "attck": ATTCK[category]})

    list_delta("kerberoastable", "kerberoastable_accounts", "kerberoastable_accounts")
    list_delta("asrep", "asrep_roastable_accounts", "asrep_roastable_accounts")
    list_delta("unconstrained", "unconstrained_delegation_principals", "unconstrained_delegation")
    list_delta("dangerous_ace", "dangerous_aces", "dangerous_aces")

    # Privileged-group rosters: diff membership sets per group (extra AND missing both drift).
    b_groups = baseline.get("privileged_group_rosters", {})
    o_groups = observed.get("privileged_group_rosters", {})
    for group in sorted(set(b_groups) | set(o_groups)):
        b_members = set(b_groups.get(group, []))
        o_members = set(o_groups.get(group, []))
        for extra in sorted(o_members - b_members):
            deltas.append({"category": "priv_group", "change": "added",
                           "fact": {"member": extra, "group": group},
                           "where": f"group:{group}", "attck": ATTCK["priv_group"]})
        for missing in sorted(b_members - o_members):
            deltas.append({"category": "priv_group", "change": "removed",
                           "fact": {"member": missing, "group": group},
                           "where": f"group:{group}", "attck": ATTCK["priv_group"]})

    # krbtgt age vs threshold. Fresh (<=) is CLEAN; stale (>) is drift. Verify the direction.
    age = observed.get("krbtgt", {}).get("age_days")
    if age is not None and age > krbtgt_max:
        deltas.append({"category": "krbtgt", "change": "stale",
                       "fact": {"age_days": age, "threshold_days": krbtgt_max},
                       "where": "krbtgt", "attck": ATTCK["krbtgt"]})

    return deltas


def render_markdown(deltas, krbtgt_max):
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [f"# Posture drift report — {now}", "",
             f"Baseline krbtgt threshold: {krbtgt_max} days.", ""]
    if not deltas:
        lines += ["**No drift.** Observed posture matches the declared baseline.", ""]
        return "\n".join(lines)
    lines += [f"**{len(deltas)} drift item(s) found.** Each must be adjudicated "
              "(bless into baseline OR re-enforce).", "",
              "| # | change | fact | where | ATT&CK |", "|--|--|--|--|--|"]
    for i, d in enumerate(deltas, 1):
        tid, tname = d["attck"]
        lines.append(f"| {i} | {d['change']} | `{json.dumps(d['fact'])}` | {d['where']} "
                     f"| {tid} ({tname}) |")
    lines += ["", "## Reconcile (fill in per item)", ""]
    for i, d in enumerate(deltas, 1):
        lines.append(f"- [ ] item {i}: bless (who/why, update baseline.json) OR re-enforce "
                     "(remediate, re-run detector, prove steady-state).")
    return "\n".join(lines) + "\n"


def print_human(deltas, krbtgt_max):
    print(f"\n=== AD posture-drift report (krbtgt threshold {krbtgt_max}d) ===")
    if not deltas:
        print("NO DRIFT — observed posture matches the declared baseline. Steady-state holds.\n")
        return
    print(f"{len(deltas)} DRIFT ITEM(S) — each needs adjudication (bless or re-enforce):\n")
    for i, d in enumerate(deltas, 1):
        tid, tname = d["attck"]
        print(f"  [{i}] {d['change'].upper():<7} {d['where']:<22} {json.dumps(d['fact'])}")
        print(f"        -> {tid}  {tname}")
    print()


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--baseline", default="baseline.json")
    p.add_argument("--observed", default="observed.json")
    p.add_argument("--json", action="store_true", help="machine-readable delta")
    p.add_argument("--out", help="also write a markdown report to this path")
    args = p.parse_args()

    baseline_raw = load(args.baseline)
    observed_raw = load(args.observed)
    krbtgt_max = baseline_raw.get("_thresholds", {}).get("krbtgt_max_age_days", 180)

    baseline = strip_comments(baseline_raw)
    observed = strip_comments(observed_raw)
    deltas = diff_posture(baseline, observed, krbtgt_max)

    if args.json:
        print(json.dumps({"drift": bool(deltas), "count": len(deltas), "deltas": deltas}, indent=2))
    else:
        print_human(deltas, krbtgt_max)

    if args.out:
        with open(args.out, "w") as f:
            f.write(render_markdown(deltas, krbtgt_max))
        if not args.json:
            print(f"(markdown report written to {args.out})")

    return 1 if deltas else 0


if __name__ == "__main__":
    sys.exit(main())
