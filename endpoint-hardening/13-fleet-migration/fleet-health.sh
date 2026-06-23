#!/usr/bin/env bash
# Module 13 — the service-health harness (the success signal).
# Per host, asserts BOTH:
#   (a) SERVING  — the app's /health endpoint returns 200 (no outage), and
#   (b) HARDENED — the host is at its EXPECTED profile (full baseline, or the
#                  legacy host's relaxed profile).
# Exits non-zero on ANY failure. FAILS CLOSED: a timeout / unreachable endpoint
# counts as a FAILURE, never a silent pass — a harness that goes green because it
# merely couldn't reach the app is the exact compliant-but-down trap this lab
# exists to teach.
#
#   fleet-health.sh <ring|all> [expect_hardened]
#     expect_hardened: "no" (default, before any roll) | "yes"
set -uo pipefail

FLEET=/fleet
INV=/lab/data/inventory.ini
ring="${1:-all}"
expect_hardened="${2:-no}"

hosts_in_ring() {
  case "$1" in
    all) echo "host-01 host-02 host-03 host-04 host-05 host-06" ;;
    *)   awk -v R="[$1]" '
            $0==R {f=1; next}
            /^\[/ {f=0}
            f && NF {gsub(/#.*/,""); if($1!="") print $1}
         ' "$INV" ;;
  esac
}

port_for() { local n="${1##*-}"; echo $(( 18000 + 10#$n )); }

state_val() { # state_val HOST KEY
  grep -E "^$2=" "$FLEET/$1/state.env" 2>/dev/null | head -1 | cut -d= -f2
}

rc=0
echo "== service-health: ring='$ring' expect_hardened='$expect_hardened' =="
for h in $(hosts_in_ring "$ring"); do
  port=$(port_for "$h")

  # (a) SERVING — fail closed on timeout/unreachable.
  code=$(curl -s -o /dev/null -m 3 -w '%{http_code}' "http://127.0.0.1:$port/health" 2>/dev/null || echo "000")
  serving="DOWN"; [ "$code" = "200" ] && serving="UP"

  # (b) HARDENED for its expected profile.
  profile=$(state_val "$h" PROFILE)
  legacy=$(state_val "$h" LEGACY)
  hardened="no"
  if [ "$profile" = "full-baseline" ] || [ "$profile" = "relaxed-legacy" ]; then
    hardened="yes"
  fi

  expect_p="full-baseline"; [ "$legacy" = "1" ] && expect_p="relaxed-legacy"

  ok=1
  [ "$serving" != "UP" ] && ok=0
  if [ "$expect_hardened" = "yes" ]; then
    [ "$hardened" != "yes" ] && ok=0
    [ "$profile" != "$expect_p" ] && ok=0
  fi
  # if endpoint was unreachable (000), that's fail-closed
  [ "$code" = "000" ] && ok=0

  if [ "$ok" = "1" ]; then
    printf '  %-9s serving=%-4s(%s)  profile=%-14s -> PASS\n' "$h" "$serving" "$code" "$profile"
  else
    printf '  %-9s serving=%-4s(%s)  profile=%-14s -> FAIL\n' "$h" "$serving" "$code" "$profile"
    rc=1
  fi
done

if [ "$rc" -eq 0 ]; then echo "RESULT: all hosts healthy."; else echo "RESULT: FAILURE — at least one host failed (serving and/or hardened)."; fi
exit $rc
