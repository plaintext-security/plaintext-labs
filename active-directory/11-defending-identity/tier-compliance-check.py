#!/usr/bin/env python3
"""
tier-compliance-check.py — nightly tiered-admin compliance check against a LIVE Samba DC (ldap3).

This is the continuous-compliance counterpart to the tiered-admin DESIGN you author in this lab.
The design says "Tier 0 accounts are protected; service accounts never hold Tier 0 rights." This
script proves whether the running domain actually obeys that, by querying the DC directly:

  CHECK 1  Tier 0 accounts ARE in Protected Users.
           (Hardened target: tallen, Administrator should be members. Note: the DC that ships
            with this track is the FLAT pre-hardening domain, so this check is EXPECTED to FAIL
            until you remediate — that gap is the point. A green run means you fixed it.)
  CHECK 2  No service account (sAMAccountName starts 'svc-') is a member of Domain Admins.
  CHECK 3  No service account is a member of Backup Operators (DCSync-equivalent on the DC).

Exits non-zero if ANY check fails, so it can gate a CI job or alert from cron.

  python3 tier-compliance-check.py
  python3 tier-compliance-check.py --json
"""
import argparse
import json
import os
import sys

TIER0_ACCOUNTS = ["tallen", "Administrator"]  # the design's declared Tier 0 identities


def get_group_members(conn, base_dn, group_cn):
    """Return the set of sAMAccountNames that are direct members of group_cn."""
    from ldap3 import SUBTREE
    conn.search(base_dn, f"(&(objectClass=group)(cn={group_cn}))",
                search_scope=SUBTREE, attributes=["member"])
    members = set()
    if conn.entries:
        for dn in (conn.entries[0]["member"].values or []):
            conn.search(dn, "(objectClass=*)", search_scope="BASE",
                        attributes=["sAMAccountName"])
            if conn.entries and conn.entries[0]["sAMAccountName"].value:
                members.add(conn.entries[0]["sAMAccountName"].value)
    return members


def run_checks(host, base_dn, user, password):
    from ldap3 import Server, Connection, ALL
    conn = Connection(Server(host, get_info=ALL), user=user, password=password, auto_bind=True)

    protected = get_group_members(conn, base_dn, "Protected Users")
    domain_admins = get_group_members(conn, base_dn, "Domain Admins")
    backup_ops = get_group_members(conn, base_dn, "Backup Operators")
    conn.unbind()

    results = []

    # CHECK 1 — Tier 0 accounts in Protected Users.
    missing = [a for a in TIER0_ACCOUNTS if a not in protected]
    results.append({
        "check": "tier0_in_protected_users",
        "pass": not missing,
        "detail": f"Tier 0 accounts NOT in Protected Users: {missing}" if missing
                  else "all Tier 0 accounts are in Protected Users",
    })

    # CHECK 2 — no svc-* in Domain Admins.
    svc_da = sorted(m for m in domain_admins if m.lower().startswith("svc-"))
    results.append({
        "check": "no_service_account_in_domain_admins",
        "pass": not svc_da,
        "detail": f"service accounts in Domain Admins: {svc_da}" if svc_da
                  else "no service account is a Domain Admin",
    })

    # CHECK 3 — no svc-* in Backup Operators.
    svc_bo = sorted(m for m in backup_ops if m.lower().startswith("svc-"))
    results.append({
        "check": "no_service_account_in_backup_operators",
        "pass": not svc_bo,
        "detail": f"service accounts in Backup Operators: {svc_bo}" if svc_bo
                  else "no service account is a Backup Operator",
    })

    return results


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--host", default=os.environ.get("DC_HOST", "ldap://10.10.0.10"))
    p.add_argument("--base-dn", default=os.environ.get("BASE_DN", "DC=corp,DC=local"))
    p.add_argument("--user", default=os.environ.get("DC_USER", "jsmith@CORP.LOCAL"))
    p.add_argument("--password", default=os.environ.get("DC_PASSWORD", "Welcome1!"))
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    results = run_checks(args.host, args.base_dn, args.user, args.password)
    all_pass = all(r["pass"] for r in results)

    if args.json:
        print(json.dumps({"all_pass": all_pass, "checks": results}, indent=2))
    else:
        print("=== Tiered-admin compliance check (live DC) ===")
        for r in results:
            print(f"  [{'PASS' if r['pass'] else 'FAIL'}] {r['check']}: {r['detail']}")
        print("\n" + ("ALL CHECKS PASS — the running domain obeys the tiered-admin design."
                      if all_pass else
                      "COMPLIANCE FAIL — remediate the failures above (this is expected on the "
                      "flat pre-hardening DC; the failing checks ARE the work)."))

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
