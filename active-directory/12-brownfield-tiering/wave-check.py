#!/usr/bin/env python3
"""
wave-check.py — the per-wave two-part gate for a brownfield AD tiering migration.

WHAT IT DOES. Given the flat baseline (data/baseline.json), the attack path
(data/path-001.json) and a wave plan (data/waves.json), it applies one wave's
mutations to an in-memory copy of the domain state and then runs the TWO assertions
that every wave must satisfy:

  (a) NO ADMIN LOCKED OUT  — every account in the wave's no-lockout list can still
      log on to the host its real job requires (the "legitimate logon path" survives).
  (b) ATTACK PATH DEAD     — the PATH-001 hop the wave targets is now CLOSED, so the
      path no longer reaches Domain Admin.

It emits a clean pass/fail JSON per assertion and exits non-zero if EITHER half fails
(fails CLOSED). Run `--cumulative` to apply waves 1..N in order (the real migration is
cumulative); run a single `--wave wave-1` to check one wave against the flat baseline.

WHY THIS IS A SIMULATION, NOT A LIVE DC. Samba4 does not enforce client-side GPO
user-rights (SeDenyInteractiveLogonRight / SeDenyRemoteInteractiveLogonRight) — that
enforcement lives in the Windows LSA on a domain-joined CLIENT, which these labs do not
ship. So the "does the Deny-logon actually take effect" question cannot be answered by
querying Samba. We model the logon-rights state as a graph (baseline.json) and the attack
as a reachability check over it. A real-DC version would additionally (1) write the GPO
via samba-tool / RSAT, (2) join a Windows client, and (3) attempt the actual logon and the
actual secretsdump. See VALIDATION.md. The JUDGEMENT this script encodes — score a FAILED
attack as PASS and a STILL-WORKING attack as FAIL — is identical either way, and is exactly
the thing a model gets backwards.

  python3 wave-check.py --wave wave-1
  python3 wave-check.py --cumulative           # apply waves 1..N in order, gate each
  python3 wave-check.py --cumulative --json     # machine-readable result
"""
import argparse
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


def load(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


# --- state mutation --------------------------------------------------------------------

def apply_mutation(state, m):
    """Mutate the in-memory domain state per one wave action. This is the simulation's
    stand-in for `samba-tool` / GPO writes against a live DC."""
    acct = state["accounts"].get(m["account"])
    if acct is None:
        # Account not modelled in baseline (e.g. a Tier 0 account beyond tallen). For the
        # worked example only tallen is fully modelled; create a thin record so the wave
        # still applies deterministically.
        acct = {"groups": [], "in_protected_users": False,
                "logon_rights": {"interactive": [], "remote_interactive": []},
                "legitimate_work": {"must_log_on_to": []}}
        state["accounts"][m["account"]] = acct

    if m["action"] == "deny_logon":
        rights = acct["logon_rights"]
        host = m["host"]
        if host in rights.get(m["right"], []):
            rights[m["right"]].remove(host)
        acct.setdefault("denied", {}).setdefault(m["right"], [])
        if host not in acct["denied"][m["right"]]:
            acct["denied"][m["right"]].append(host)
    elif m["action"] == "add_to_protected_users":
        acct["in_protected_users"] = True
    else:
        raise ValueError(f"unknown mutation action: {m['action']}")


# --- assertion (a): no admin locked out ------------------------------------------------

def check_no_lockout(state, assertions):
    """For each (account, host) the wave promises to preserve, confirm the account can
    STILL log on there. 'Can log on' = the host is in one of the account's logon-right
    lists AND not in its denied lists. A failure here is a LOCKOUT the wave caused."""
    results = []
    ok = True
    for a in assertions:
        acct = state["accounts"].get(a["account"], {})
        host = a["must_still_log_on_to"]
        rights = acct.get("logon_rights", {})
        denied = acct.get("denied", {})
        can = (host in rights.get("interactive", []) or host in rights.get("remote_interactive", [])) \
            and host not in denied.get("interactive", []) \
            and host not in denied.get("remote_interactive", [])
        if not can:
            ok = False
        results.append({"account": a["account"], "host": host,
                        "can_log_on": can,
                        "verdict": "ok" if can else "LOCKOUT"})
    return ok, results


# --- assertion (b): attack path dead ---------------------------------------------------

def hop_is_open(state, hop):
    """Evaluate one PATH-001 hop against the (mutated) state. Returns True if the hop's
    precondition still HOLDS (attacker can take it). The only tiering-closeable hop is the
    Tier-0-logon-on-Tier-2 credential-harvest hop; the rest are modelled as standing-open
    preconditions outside tiering's remit."""
    if not hop.get("closed_by_tiering"):
        # Hops tiering doesn't address: treat as open UNLESS gated on a prior hop.
        if hop.get("reachable_only_if"):
            return None  # resolved by path-level logic below
        return True

    # The credential-harvest hop. It is CLOSED when EITHER:
    #   - the Tier 0 account is denied BOTH interactive and remote_interactive on the host, OR
    #   - the Tier 0 account is in Protected Users (cached cred non-harvestable).
    closes = hop["closes_when"]
    cond = closes["all_of"]
    acct_name = cond[0]["account"]
    host = cond[0]["host"]
    acct = state["accounts"].get(acct_name, {})
    denied = acct.get("denied", {})
    denied_both = (host in denied.get("interactive", []) and
                   host in denied.get("remote_interactive", []))
    protected = acct.get("in_protected_users", False)
    closed = denied_both or protected
    return not closed


def check_attack_dead(state, path, targeted_hop):
    """Walk PATH-001. The path reaches Domain Admin only if EVERY hop is open. The wave's
    job is to close `targeted_hop`; we report that hop specifically AND whether the whole
    path still reaches the goal.

    CRITICAL SCORING (the thing a model inverts): a CLOSED targeted hop => attack DEAD =>
    PASS. An OPEN targeted hop => attack still works => FAIL."""
    hop_states = []
    path_reaches_da = True
    for hop in path["hops"]:
        open_ = hop_is_open(state, hop)
        if open_ is None:
            # reachable_only_if: open iff the referenced prior hop is open.
            # All our gated hops depend on the credential-harvest hop (step 3).
            prior = next((h for h in hop_states if h["step"] == 3), None)
            open_ = prior["open"] if prior else True
        hop_states.append({"step": hop["step"], "edge": hop["edge"], "open": open_})
        if not open_:
            path_reaches_da = False

    targeted = next(h for h in hop_states if h["step"] == targeted_hop)
    attack_dead = (not targeted["open"])  # targeted hop closed == attack dead at this wave's target
    return {
        "targeted_hop": targeted_hop,
        "targeted_hop_open": targeted["open"],
        "attack_dead": attack_dead,
        "path_reaches_domain_admin": path_reaches_da,
        "hops": hop_states,
        "verdict": "ATTACK DEAD (pass)" if attack_dead else "ATTACK STILL WORKS (fail)",
    }


# --- driver ----------------------------------------------------------------------------

def run_wave(state, path, wave):
    for m in wave["mutations"]:
        apply_mutation(state, m)
    lock_ok, lock_results = check_no_lockout(state, wave["no_lockout_assertions"])
    atk = check_attack_dead(state, path, wave["targets_path_hop"])
    wave_pass = lock_ok and atk["attack_dead"]
    return {
        "wave": wave["id"], "name": wave["name"],
        "assertion_a_no_lockout": {"pass": lock_ok, "results": lock_results},
        "assertion_b_attack_dead": {"pass": atk["attack_dead"], "detail": atk},
        "wave_pass": wave_pass,
    }


def print_result(r):
    print(f"\n=== {r['wave']} — {r['name']} ===")
    a = r["assertion_a_no_lockout"]
    print(f"  (a) no admin locked out: {'PASS' if a['pass'] else 'FAIL'}")
    for x in a["results"]:
        flag = "ok " if x["can_log_on"] else "LOCKOUT"
        print(f"        [{flag}] {x['account']} -> {x['host']}")
    b = r["assertion_b_attack_dead"]["detail"]
    print(f"  (b) attack path dead:    {'PASS' if r['assertion_b_attack_dead']['pass'] else 'FAIL'}  "
          f"({b['verdict']})")
    print(f"        targeted hop {b['targeted_hop']} open? {b['targeted_hop_open']}  |  "
          f"path reaches Domain Admin? {b['path_reaches_domain_admin']}")
    print(f"  WAVE VERDICT: {'PASS' if r['wave_pass'] else 'FAIL'}")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--wave", help="check a single wave id (e.g. wave-1) against the flat baseline")
    p.add_argument("--cumulative", action="store_true",
                   help="apply waves 1..N in order and gate each (the real migration)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    args = p.parse_args()

    baseline = load("baseline.json")
    path = load("path-001.json")
    waves = load("waves.json")["waves"]

    results = []
    all_pass = True

    if args.cumulative:
        state = copy.deepcopy(baseline)
        for w in waves:
            r = run_wave(state, path, w)   # state carries forward = cumulative
            results.append(r)
            all_pass = all_pass and r["wave_pass"]
    else:
        target = args.wave or waves[0]["id"]
        w = next((x for x in waves if x["id"] == target), None)
        if w is None:
            print(f"no such wave: {target}", file=sys.stderr)
            return 2
        state = copy.deepcopy(baseline)
        r = run_wave(state, path, w)
        results.append(r)
        all_pass = r["wave_pass"]

    if args.json:
        print(json.dumps({"all_pass": all_pass, "waves": results}, indent=2))
    else:
        for r in results:
            print_result(r)
        print("\n" + ("ALL WAVES PASS: every wave kept admins logged on AND killed its target hop."
                       if all_pass else
                       "GATE FAIL: at least one wave locked out an admin or left its target hop open."))

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
