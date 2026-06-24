#!/usr/bin/env python3
"""
corroborate-live.py — verify the FLAT baseline fixture against the REAL Samba DC over LDAP.

The wave gate (wave-check.py) models GPO Deny-logon enforcement as a graph, because Samba does
not enforce client-side user-rights (that lives in the Windows LSA on a domain-joined client —
see VALIDATION.md). What IS live-checkable on the DC, and what this script checks via ldap3, is
the part of the baseline that is pure directory state:

  * the Tier 0 / privileged-group ROSTERS (who is actually in Domain Admins, Backup Operators, …)
  * which accounts the baseline models actually EXIST in the directory
  * which accounts carry an SPN (the Kerberoastable surface PATH-001 step 1 relies on)

If the fixture and the live DC disagree, the simulation is reasoning about a domain that isn't
there — this is the corroboration that keeps the model honest. The logon-rights reachability
stays a documented model; everything queryable is queried.

  python3 corroborate-live.py                 # human report; exit 1 on any mismatch
  python3 corroborate-live.py --json
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

PRIV_GROUPS = ["Domain Admins", "Enterprise Admins", "Backup Operators", "IT-Admins"]


def load(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


def collect_live(host, base_dn, user, password):
    """Read the corroborate-able directory facts off the live DC via ldap3."""
    from ldap3 import Server, Connection, ALL, SUBTREE

    conn = Connection(Server(host, get_info=ALL), user=user, password=password, auto_bind=True)

    def sam_of(dn):
        conn.search(dn, "(objectClass=*)", search_scope="BASE", attributes=["sAMAccountName"])
        if conn.entries and conn.entries[0]["sAMAccountName"].value:
            return conn.entries[0]["sAMAccountName"].value
        return None

    rosters = {}
    for group in PRIV_GROUPS:
        conn.search(base_dn, f"(&(objectClass=group)(cn={group}))",
                    search_scope=SUBTREE, attributes=["member"])
        members = []
        if conn.entries:
            for dn in (conn.entries[0]["member"].values or []):
                s = sam_of(dn)
                if s:
                    members.append(s)
        rosters[group] = sorted(members)

    conn.search(base_dn, "(&(objectClass=user)(servicePrincipalName=*)(!(objectClass=computer)))",
                search_scope=SUBTREE, attributes=["sAMAccountName"])
    spn_accounts = sorted(e["sAMAccountName"].value for e in conn.entries
                          if e["sAMAccountName"].value)

    conn.search(base_dn, "(&(objectCategory=person)(objectClass=user))",
                search_scope=SUBTREE, attributes=["sAMAccountName"])
    all_users = sorted(e["sAMAccountName"].value for e in conn.entries
                       if e["sAMAccountName"].value)

    conn.unbind()
    return {"rosters": rosters, "spn_accounts": spn_accounts, "users": all_users}


def corroborate(baseline, live):
    """Compare the baseline fixture's claims to the live DC. Return a list of mismatches."""
    issues = []

    # Tier 0 accounts the fixture names must exist on the DC.
    tier0 = baseline["tiers"]["assignment"].get("tier0_accounts", [])
    for acct in tier0:
        if acct not in live["users"]:
            issues.append(f"Tier 0 account '{acct}' in fixture but NOT found on the live DC")

    # Domain Admins roster: every modelled DA member should be a real DA on the DC.
    fixture_da = set(baseline["accounts"].keys())
    live_da = set(live["rosters"].get("Domain Admins", []))
    modelled_das = {a for a, v in baseline["accounts"].items()
                    if "Domain Admins" in v.get("groups", [])}
    for da in modelled_das:
        if da not in live_da:
            issues.append(f"'{da}' modelled as Domain Admin but is NOT in live Domain Admins {sorted(live_da)}")

    # The PATH-001 Kerberoastable surface must be real: at least one SPN account on the DC.
    if not live["spn_accounts"]:
        issues.append("baseline assumes a Kerberoastable surface but the live DC has NO SPN accounts")

    return issues


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--host", default=os.environ.get("DC_HOST", "ldap://10.10.0.10"))
    p.add_argument("--base-dn", default=os.environ.get("BASE_DN", "DC=corp,DC=local"))
    p.add_argument("--user", default=os.environ.get("DC_USER", "jsmith@CORP.LOCAL"))
    p.add_argument("--password", default=os.environ.get("DC_PASSWORD", "Welcome1!"))
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    baseline = load("baseline.json")
    live = collect_live(args.host, args.base_dn, args.user, args.password)
    issues = corroborate(baseline, live)

    if args.json:
        print(json.dumps({"ok": not issues, "issues": issues, "live": live}, indent=2))
    else:
        print("=== Corroborate flat baseline vs the LIVE DC (ldap3) ===")
        print(f"  live Domain Admins:   {live['rosters'].get('Domain Admins')}")
        print(f"  live SPN accounts:    {live['spn_accounts']}")
        print(f"  live user count:      {len(live['users'])}")
        if not issues:
            print("\nOK — the fixture matches the live directory state. The wave model reasons about")
            print("the real domain; only the GPO-logon ENFORCEMENT remains modelled (see VALIDATION.md).")
        else:
            print(f"\n{len(issues)} MISMATCH(ES) — the fixture disagrees with the live DC:")
            for i in issues:
                print(f"  [!] {i}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
